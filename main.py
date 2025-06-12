"""
FACO WEEKLY - Sistema de Reportes Automatizados (VERSIÓN EXTENDIDA)
====================================================================

Sistema completo con generación automática de reportes Excel y PowerPoint
integrando análisis de gestión de cobranza con vigencias corregidas.
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
import pandas as pd
from google.cloud import bigquery
import os
from datetime import datetime, date, timedelta
import tempfile
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from pptx import Presentation
from pptx.util import Inches, Pt
import logging
from typing import Optional, Dict, List
import re
import asyncio
import io
from contextlib import asynccontextmanager

# Importar el generador de reportes
from report_generator import TelefonicaReportGenerator

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FACO Weekly - Sistema Completo con Reportes",
    description="Sistema con vigencias corregidas + generación automática Excel/PPT",
    version="2.2.0"
)

class CorrectedBigQueryManager:
    """Gestor corregido con lógica de vigencias del calendario"""
    
    def __init__(self):
        self.client = bigquery.Client(project="mibot-222814")
        self.dataset = "BI_USA"
    
    def get_control_calendar_with_vigencias(self, fecha_corte: str = None) -> pd.DataFrame:
        """Extrae calendario con vigencias activas"""
        where_clause = "WHERE 1=1"
        if fecha_corte:
            where_clause += f" AND fecha_asignacion <= '{fecha_corte}'"
            
        query = f"""
        SELECT 
            archivo,
            suma_lineas,
            fecha_asignacion,
            fecha_cierre,
            vencimiento,
            -- Clasificar cartera por patrón de archivo
            CASE 
                WHEN archivo LIKE '%_AN_%' THEN 'Altas_Nuevas'
                WHEN archivo LIKE '%_Temprana_%' THEN 'Temprana'
                WHEN archivo LIKE '%_CF_ANN_%' THEN 'Fraccionamiento'
                ELSE 'Otro'
            END as tipo_cartera,
            -- Calcular días de vigencia
            DATE_DIFF(fecha_cierre, fecha_asignacion, DAY) as dias_vigencia,
            -- Estado de vigencia
            CASE 
                WHEN fecha_cierre >= CURRENT_DATE() THEN 'ACTIVA'
                ELSE 'CERRADA'
            END as estado_vigencia
        FROM `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_calendario_v2`
        {where_clause}
        ORDER BY fecha_asignacion DESC
        """
        return self.client.query(query).to_dataframe()
    
    def get_unified_gestiones_by_vigencias(self, calendario_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrae gestiones unificadas respetando vigencias del calendario
        CORREGIDO: Usa vigencias específicas por campaña
        """
        if calendario_df.empty:
            return pd.DataFrame()
        
        # Construir condiciones de vigencia por archivo
        vigencia_conditions = []
        for _, campaign in calendario_df.iterrows():
            archivo_base = campaign['archivo'].replace('.txt', '')  # Remover .txt si existe
            fecha_inicio = campaign['fecha_asignacion'].strftime('%Y-%m-%d')
            fecha_fin = campaign['fecha_cierre'].strftime('%Y-%m-%d')
            
            vigencia_conditions.append(f"""
            (a.archivo = '{archivo_base}' AND DATE(g.date) BETWEEN '{fecha_inicio}' AND '{fecha_fin}')
            """)
        
        # Unir todas las condiciones con OR
        vigencias_where = " OR ".join(vigencia_conditions)
        
        query = f"""
        WITH
        -- 1. Definir vigencias de campañas
        vigencias_campanias AS (
          SELECT 
            archivo,
            fecha_asignacion,
            fecha_cierre,
            CASE 
                WHEN archivo LIKE '%_AN_%' THEN 'Altas_Nuevas'
                WHEN archivo LIKE '%_Temprana_%' THEN 'Temprana'
                WHEN archivo LIKE '%_CF_ANN_%' THEN 'Fraccionamiento'
                ELSE 'Otro'
            END as tipo_cartera
          FROM `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_calendario_v2`
          WHERE archivo IN ({','.join([f"'{row['archivo']}'\" for _, row in calendario_df.iterrows()])})
        ),
        
        -- 2. Asignaciones con sus vigencias correspondientes
        asignaciones_con_vigencia AS (
          SELECT 
            a.cod_luna,
            a.cuenta,
            a.negocio,
            a.archivo,
            v.fecha_asignacion,
            v.fecha_cierre,
            v.tipo_cartera,
            -- Servicio normalizado: solo MOVIL es móvil
            CASE 
                WHEN UPPER(a.negocio) = 'MOVIL' THEN 'Movil'
                ELSE 'Fijo'
            END as servicio
          FROM `{self.dataset}.batch_P3fV4dWNeMkN5RJMhV8e_asignacion` a
          JOIN vigencias_campanias v ON REGEXP_REPLACE(a.archivo, r'\\.txt$', '') = v.archivo
          WHERE a.creado_el >= '2025-06-11'
            AND a.motivo_rechazo IS NULL
        ),
        
        -- 3. Unificar gestiones (CALL + VOICEBOT)
        gestiones_unificadas AS (
          -- Gestiones CALL
          SELECT
            mba.date,
            SAFE_CAST(mba.document AS INT64) AS cod_luna,
            'CALL' AS canal,
            COALESCE(u.nombre_apellidos, 'AGENTE NO IDENTIFICADO') AS ejecutivo_homologado,
            COALESCE(mba.nombre_agente, 'DISCADOR') AS ejecutivo,
            SAFE_CAST(u.dni AS STRING) AS dni_ejecutivo,
            mba.n1,
            mba.n2,
            mba.n3,
            mba.sub_management,
            NULL AS bot_management,
            NULL AS bot_compromiso,
            mba.duracion
          FROM `{self.dataset}.mibotair_P3fV4dWNeMkN5RJMhV8e` mba
          LEFT JOIN `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_usuarios` u
            ON mba.correo_agente = u.usuario

          UNION ALL

          -- Gestiones VOICEBOT
          SELECT
            vb.date,
            SAFE_CAST(vb.document AS INT64) AS cod_luna,
            'VOICEBOT' AS canal,
            'VOICEBOT' AS ejecutivo_homologado,
            'VOICEBOT' AS ejecutivo,
            '99999999' AS dni_ejecutivo,
            vb.management, NULL, NULL, NULL,
            vb.management AS bot_management,
            vb.compromiso AS bot_compromiso,
            NULL AS duracion
          FROM `{self.dataset}.voicebot_P3fV4dWNeMkN5RJMhV8e` vb
        ),
        
        -- 4. Filtrar gestiones por vigencias específicas de cada campaña
        gestiones_en_vigencia AS (
          SELECT 
            g.*,
            av.archivo,
            av.fecha_asignacion,
            av.fecha_cierre,
            av.tipo_cartera,
            av.servicio,
            -- Días desde asignación
            DATE_DIFF(DATE(g.date), av.fecha_asignacion, DAY) as dias_desde_asignacion
          FROM gestiones_unificadas g
          JOIN asignaciones_con_vigencia av ON g.cod_luna = av.cod_luna
          WHERE DATE(g.date) BETWEEN av.fecha_asignacion AND av.fecha_cierre
        ),

        -- 5. Homologar las gestiones en vigencia
        gestiones_homologadas AS (
          SELECT
            g.*,
            CASE
              WHEN g.canal = 'CALL' THEN COALESCE(SAFE_CAST(h_call.peso AS INT64), 0)
              WHEN g.canal = 'VOICEBOT' THEN COALESCE(SAFE_CAST(h_bot.peso_homologado AS INT64), 0)
              ELSE 0
            END AS peso,
            CASE
              WHEN g.canal = 'CALL' THEN COALESCE(h_call.contactabilidad, 'NO_HOMOLOGADO')
              WHEN g.canal = 'VOICEBOT' THEN COALESCE(h_bot.contactabilidad_homologada, 'NO_HOMOLOGADO')
            END AS contactabilidad,
            CASE
              WHEN g.canal = 'CALL' THEN COALESCE(h_call.pdp, 'NO')
              WHEN g.canal = 'VOICEBOT' THEN COALESCE(IF(h_bot.es_pdp_homologado = 1, 'SI', 'NO'), 'NO')
            END AS es_pdp,
            CASE
                WHEN g.canal = 'VOICEBOT' THEN h_bot.n1_homologado
                ELSE g.n1
            END AS n1_final,
            CASE
                WHEN g.canal = 'VOICEBOT' THEN h_bot.n2_homologado
                ELSE g.n2
            END AS n2_final,
            CASE
                WHEN g.canal = 'VOICEBOT' THEN h_bot.n3_homologado
                ELSE g.n3
            END AS n3_final,
            CASE
                WHEN g.canal = 'CALL' THEN g.sub_management
                ELSE g.bot_compromiso
            END AS compromiso
          FROM gestiones_en_vigencia g
          LEFT JOIN `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_v2` h_call
            ON g.canal = 'CALL' AND g.n1 = h_call.n_1 AND g.n2 = h_call.n_2 AND g.n3 = h_call.n_3
          LEFT JOIN `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_voicebot` h_bot
            ON g.canal = 'VOICEBOT' AND g.bot_management = h_bot.bot_management 
            AND COALESCE(g.sub_management, '') = h_bot.bot_sub_management 
            AND COALESCE(g.bot_compromiso, '') = h_bot.bot_compromiso
        )

        -- 6. Resultado final con monto de compromiso
        SELECT
          h.date,
          h.cod_luna,
          h.canal,
          h.ejecutivo,
          h.ejecutivo_homologado,
          h.dni_ejecutivo,
          h.duracion,
          h.n1_final AS n1,
          h.n2_final AS n2,
          h.n3_final AS n3,
          h.compromiso,
          h.contactabilidad,
          h.es_pdp,
          h.peso,
          h.archivo,
          h.fecha_asignacion,
          h.fecha_cierre,
          h.tipo_cartera,
          h.servicio,
          h.dias_desde_asignacion,
          -- Lógica de monto de compromiso desde fact_asignacion
          CASE
            WHEN h.es_pdp = 'SI' THEN COALESCE(fa.monto_exigible, 0)
            ELSE 0
          END AS monto_compromiso,
          fa.monto_exigible
        FROM gestiones_homologadas h
        LEFT JOIN `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_fact_asignacion` fa
          ON h.cod_luna = fa.cod_luna
        WHERE h.contactabilidad != 'NO_HOMOLOGADO'
        ORDER BY h.date DESC, h.archivo, h.cod_luna
        """
        
        logger.info(f"Ejecutando query con vigencias para {len(calendario_df)} campañas")
        result = self.client.query(query).to_dataframe()
        logger.info(f"Gestiones en vigencia extraídas: {len(result)}")
        
        return result
    
    def get_asignacion_summary_by_vigencias(self, calendario_df: pd.DataFrame) -> pd.DataFrame:
        """Resumen de asignaciones por vigencias"""
        if calendario_df.empty:
            return pd.DataFrame()
        
        archivos = [row['archivo'] for _, row in calendario_df.iterrows()]
        archivos_str = "', '".join(archivos)
        
        query = f"""
        WITH asignaciones_vigentes AS (
          SELECT 
            a.*,
            c.fecha_asignacion,
            c.fecha_cierre,
            c.tipo_cartera,
            DATE_DIFF(c.fecha_cierre, c.fecha_asignacion, DAY) as dias_vigencia,
            CASE 
                WHEN UPPER(a.negocio) = 'MOVIL' THEN 'Movil'
                ELSE 'Fijo'
            END as servicio_normalizado
          FROM `{self.dataset}.batch_P3fV4dWNeMkN5RJMhV8e_asignacion` a
          JOIN (
            SELECT archivo, fecha_asignacion, fecha_cierre,
                   CASE 
                     WHEN archivo LIKE '%_AN_%' THEN 'Altas_Nuevas'
                     WHEN archivo LIKE '%_Temprana_%' THEN 'Temprana'
                     WHEN archivo LIKE '%_CF_ANN_%' THEN 'Fraccionamiento'
                     ELSE 'Otro'
                   END as tipo_cartera
            FROM `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_calendario_v2`
            WHERE archivo IN ('{archivos_str}')
          ) c ON REGEXP_REPLACE(a.archivo, r'\\.txt$', '') = c.archivo
          WHERE a.creado_el >= '2025-06-11'
            AND a.motivo_rechazo IS NULL
        )
        
        SELECT 
          archivo,
          fecha_asignacion,
          fecha_cierre,
          tipo_cartera,
          servicio_normalizado,
          dias_vigencia,
          COUNT(DISTINCT cod_luna) as clientes_asignados,
          COUNT(DISTINCT cuenta) as cuentas_asignadas,
          COUNT(*) as registros_totales
        FROM asignaciones_vigentes
        GROUP BY 1,2,3,4,5,6
        ORDER BY fecha_asignacion DESC, tipo_cartera
        """
        
        return self.client.query(query).to_dataframe()
    
    def get_pagos_by_vigencias(self, calendario_df: pd.DataFrame) -> pd.DataFrame:
        """Extrae pagos considerando las vigencias extendidas"""
        if calendario_df.empty:
            return pd.DataFrame()
        
        # Extender vigencias para capturar pagos post-gestión
        fecha_min = calendario_df['fecha_asignacion'].min().strftime('%Y-%m-%d')
        fecha_max = (calendario_df['fecha_cierre'].max() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        query = f"""
        SELECT 
            cod_sistema,
            nro_documento,
            monto_cancelado,
            fecha_pago,
            archivo
        FROM `{self.dataset}.batch_P3fV4dWNeMkN5RJMhV8e_pagos`
        WHERE fecha_pago BETWEEN '{fecha_min}' AND '{fecha_max}'
            AND motivo_rechazo IS NULL
            AND monto_cancelado > 0
        """
        return self.client.query(query).to_dataframe()

class VigenciaBusinessProcessor:
    """Procesador que respeta vigencias del calendario"""
    
    def __init__(self):
        pass
    
    def analyze_vigencias_coverage(self, calendario_df: pd.DataFrame, gestiones_df: pd.DataFrame) -> Dict:
        """Analiza cobertura de gestiones por vigencias"""
        if calendario_df.empty or gestiones_df.empty:
            return {}
        
        coverage_by_campaign = []
        
        for _, campaign in calendario_df.iterrows():
            archivo = campaign['archivo']
            fecha_inicio = campaign['fecha_asignacion']
            fecha_fin = campaign['fecha_cierre']
            
            # Gestiones en esta campaña específica
            gestiones_campaign = gestiones_df[gestiones_df['archivo'] == archivo]
            
            # Análisis temporal de gestiones
            if not gestiones_campaign.empty:
                gestiones_por_dia = gestiones_campaign.groupby(
                    gestiones_campaign['date'].dt.date
                ).size()
                
                cobertura = {
                    'archivo': archivo,
                    'tipo_cartera': campaign['tipo_cartera'],
                    'fecha_asignacion': fecha_inicio,
                    'fecha_cierre': fecha_fin,
                    'dias_vigencia': (fecha_fin - fecha_inicio).days,
                    'total_gestiones': len(gestiones_campaign),
                    'clientes_gestionados': gestiones_campaign['cod_luna'].nunique(),
                    'dias_con_gestion': len(gestiones_por_dia),
                    'gestion_promedio_por_dia': gestiones_por_dia.mean(),
                    'primer_gestion': gestiones_campaign['date'].min().date(),
                    'ultima_gestion': gestiones_campaign['date'].max().date()
                }
                
                # Calcular distribución temporal
                cobertura['cobertura_temporal'] = len(gestiones_por_dia) / max((fecha_fin - fecha_inicio).days, 1) * 100
                
            else:
                cobertura = {
                    'archivo': archivo,
                    'tipo_cartera': campaign['tipo_cartera'],
                    'fecha_asignacion': fecha_inicio,
                    'fecha_cierre': fecha_fin,
                    'dias_vigencia': (fecha_fin - fecha_inicio).days,
                    'total_gestiones': 0,
                    'clientes_gestionados': 0,
                    'dias_con_gestion': 0,
                    'gestion_promedio_por_dia': 0,
                    'primer_gestion': None,
                    'ultima_gestion': None,
                    'cobertura_temporal': 0
                }
            
            coverage_by_campaign.append(cobertura)
        
        return {
            'cobertura_por_campania': coverage_by_campaign,
            'resumen': {
                'campañas_analizadas': len(coverage_by_campaign),
                'campañas_con_gestion': len([c for c in coverage_by_campaign if c['total_gestiones'] > 0]),
                'cobertura_temporal_promedio': round(
                    sum(c['cobertura_temporal'] for c in coverage_by_campaign) / len(coverage_by_campaign), 2
                )
            }
        }
    
    def validate_vigencias_logic(self, calendario_df: pd.DataFrame, gestiones_df: pd.DataFrame) -> Dict:
        """Valida que la lógica de vigencias esté funcionando correctamente"""
        validation = {
            'total_campañas': len(calendario_df),
            'gestiones_fuera_vigencia': 0,
            'gestiones_sin_campania': 0,
            'problems': []
        }
        
        if gestiones_df.empty:
            validation['problems'].append("No hay gestiones para validar")
            return validation
        
        # Verificar gestiones fuera de vigencia (no debería haber ninguna)
        for _, gestion in gestiones_df.iterrows():
            fecha_gestion = gestion['date'].date() if hasattr(gestion['date'], 'date') else gestion['date']
            archivo = gestion['archivo']
            
            # Buscar la campaña correspondiente
            campaign = calendario_df[calendario_df['archivo'] == archivo]
            
            if campaign.empty:
                validation['gestiones_sin_campania'] += 1
                continue
            
            fecha_inicio = campaign.iloc[0]['fecha_asignacion']
            fecha_fin = campaign.iloc[0]['fecha_cierre']
            
            if not (fecha_inicio <= fecha_gestion <= fecha_fin):
                validation['gestiones_fuera_vigencia'] += 1
        
        # Calcular porcentajes
        total_gestiones = len(gestiones_df)
        if total_gestiones > 0:
            validation['pct_fuera_vigencia'] = round(
                validation['gestiones_fuera_vigencia'] / total_gestiones * 100, 2
            )
            validation['pct_sin_campania'] = round(
                validation['gestiones_sin_campania'] / total_gestiones * 100, 2
            )
        
        return validation

# Inicializar managers corregidos
bq_manager = CorrectedBigQueryManager()
vigencia_processor = VigenciaBusinessProcessor()

@app.get("/")
async def root():
    return {
        "message": "FACO Weekly - Sistema Completo con Reportes Automatizados",
        "version": "2.2.0",
        "features": [
            "Gestiones filtradas por vigencias específicas del calendario_v2",
            "Generación automática de reportes Excel y PowerPoint",
            "Análisis consolidado por canales CALL y VOICEBOT",
            "KPIs y métricas ejecutivas automatizadas"
        ],
        "endpoints": {
            "/process-by-vigencias": "Procesamiento respetando vigencias del calendario",
            "/generate-reports": "🆕 Generar reportes Excel y PowerPoint automáticamente",
            "/download-excel/{filename}": "🆕 Descargar archivo Excel generado",
            "/download-powerpoint/{filename}": "🆕 Descargar archivo PowerPoint generado",
            "/validate-vigencias": "Validar lógica de vigencias",
            "/vigencias-status": "Estado de vigencias activas",
            "/health": "Estado del sistema"
        }
    }

@app.get("/vigencias-status")
async def get_vigencias_status():
    """Estado actual de vigencias del calendario"""
    try:
        calendario_df = bq_manager.get_control_calendar_with_vigencias()
        
        if calendario_df.empty:
            return {"status": "no_data", "message": "No hay campañas en calendario"}
        
        # Análisis de vigencias
        total_campañas = len(calendario_df)
        activas = len(calendario_df[calendario_df['estado_vigencia'] == 'ACTIVA'])
        cerradas = len(calendario_df[calendario_df['estado_vigencia'] == 'CERRADA'])
        
        # Distribución por cartera
        dist_cartera = calendario_df['tipo_cartera'].value_counts().to_dict()
        
        # Vigencias más recientes
        vigencias_recientes = calendario_df.head(10)[
            ['archivo', 'fecha_asignacion', 'fecha_cierre', 'tipo_cartera', 'dias_vigencia', 'estado_vigencia']
        ].to_dict('records')
        
        return {
            "status": "success",
            "resumen": {
                "total_campañas": total_campañas,
                "vigencias_activas": activas,
                "vigencias_cerradas": cerradas,
                "distribucion_cartera": dist_cartera
            },
            "vigencias_recientes": vigencias_recientes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo vigencias: {str(e)}")

@app.post("/process-by-vigencias")
async def process_by_vigencias(
    incluir_cerradas: bool = False,
    fecha_corte: Optional[str] = None
):
    """
    Procesamiento respetando vigencias específicas del calendario_v2
    CORREGIDO: No usa rangos globales, sino vigencias por campaña
    """
    try:
        logger.info("Iniciando procesamiento por vigencias específicas")
        
        # 1. Obtener calendario con vigencias
        calendario_df = bq_manager.get_control_calendar_with_vigencias(fecha_corte)
        
        if calendario_df.empty:
            raise HTTPException(status_code=404, detail="No hay campañas en calendario")
        
        # 2. Filtrar por estado de vigencia si se solicita
        if not incluir_cerradas:
            calendario_df = calendario_df[calendario_df['estado_vigencia'] == 'ACTIVA']
        
        logger.info(f"Procesando {len(calendario_df)} campañas")
        
        # 3. Extraer gestiones respetando vigencias específicas
        gestiones_df = bq_manager.get_unified_gestiones_by_vigencias(calendario_df)
        
        # 4. Obtener resumen de asignaciones por vigencias
        asignacion_df = bq_manager.get_asignacion_summary_by_vigencias(calendario_df)
        
        # 5. Extraer pagos considerando vigencias extendidas
        pagos_df = bq_manager.get_pagos_by_vigencias(calendario_df)
        
        # 6. Análisis de cobertura por vigencias
        cobertura_analysis = vigencia_processor.analyze_vigencias_coverage(calendario_df, gestiones_df)
        
        # 7. Validar lógica de vigencias
        validation = vigencia_processor.validate_vigencias_logic(calendario_df, gestiones_df)
        
        # 8. KPIs por campaña
        kpis_por_campania = []
        if not gestiones_df.empty:
            for archivo in calendario_df['archivo'].unique():
                gestiones_camp = gestiones_df[gestiones_df['archivo'] == archivo]
                if not gestiones_camp.empty:
                    kpi = {
                        'archivo': archivo,
                        'total_gestiones': len(gestiones_camp),
                        'clientes_gestionados': gestiones_camp['cod_luna'].nunique(),
                        'contactos_efectivos': len(gestiones_camp[gestiones_camp['contactabilidad'] == 'CONTACTO_EFECTIVO']),
                        'pdps': len(gestiones_camp[gestiones_camp['es_pdp'] == 'SI']),
                        'monto_compromisos': gestiones_camp['monto_compromiso'].sum()
                    }
                    kpi['tasa_contactabilidad'] = round(kpi['contactos_efectivos'] / kpi['total_gestiones'] * 100, 2)
                    kpi['tasa_pdp'] = round(kpi['pdps'] / kpi['contactos_efectivos'] * 100, 2) if kpi['contactos_efectivos'] > 0 else 0
                    kpis_por_campania.append(kpi)
        
        return {
            "status": "success",
            "version": "2.2.0",
            "vigencias_procesadas": len(calendario_df),
            "configuracion": {
                "incluir_cerradas": incluir_cerradas,
                "fecha_corte": fecha_corte
            },
            "datos_procesados": {
                "campañas_calendario": len(calendario_df),
                "gestiones_en_vigencia": len(gestiones_df),
                "asignaciones_resumen": len(asignacion_df),
                "pagos_periodo": len(pagos_df)
            },
            "validacion_vigencias": validation,
            "cobertura_vigencias": cobertura_analysis,
            "kpis_por_campania": kpis_por_campania[:10],  # Top 10
            "resumen_campañas": asignacion_df.to_dict('records') if not asignacion_df.empty else []
        }
        
    except Exception as e:
        logger.error(f"Error en procesamiento por vigencias: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en procesamiento por vigencias: {str(e)}")

@app.post("/generate-reports")
async def generate_reports(
    fecha_inicio: str,
    fecha_fin: str,
    incluir_cerradas: bool = False,
    formato: str = "ambos"  # "excel", "powerpoint", "ambos"
):
    """
    🆕 NUEVO: Generar reportes automatizados Excel y/o PowerPoint
    
    Args:
        fecha_inicio: Fecha inicio período (YYYY-MM-DD)
        fecha_fin: Fecha fin período (YYYY-MM-DD)
        incluir_cerradas: Incluir campañas cerradas
        formato: Tipo de reporte ("excel", "powerpoint", "ambos")
    
    Returns:
        Información de archivos generados y enlaces de descarga
    """
    try:
        logger.info(f"🚀 Iniciando generación de reportes: {fecha_inicio} a {fecha_fin}")
        
        # 1. Validar formato
        if formato not in ["excel", "powerpoint", "ambos"]:
            raise HTTPException(status_code=400, detail="Formato debe ser: excel, powerpoint o ambos")
        
        # 2. Obtener datos usando el sistema existente
        calendario_df = bq_manager.get_control_calendar_with_vigencias(fecha_fin)
        
        if calendario_df.empty:
            raise HTTPException(status_code=404, detail="No hay campañas en calendario para el período")
        
        # Filtrar por vigencias si necesario
        if not incluir_cerradas:
            calendario_df = calendario_df[calendario_df['estado_vigencia'] == 'ACTIVA']
        
        # 3. Extraer datos para reportes
        gestiones_df = bq_manager.get_unified_gestiones_by_vigencias(calendario_df)
        asignacion_df = bq_manager.get_asignacion_summary_by_vigencias(calendario_df)
        pagos_df = bq_manager.get_pagos_by_vigencias(calendario_df)
        
        # 4. Calcular KPIs por campaña
        kpis_por_campania = []
        if not gestiones_df.empty:
            for archivo in calendario_df['archivo'].unique():
                gestiones_camp = gestiones_df[gestiones_df['archivo'] == archivo]
                if not gestiones_camp.empty:
                    kpi = {
                        'archivo': archivo,
                        'total_gestiones': len(gestiones_camp),
                        'clientes_gestionados': gestiones_camp['cod_luna'].nunique(),
                        'contactos_efectivos': len(gestiones_camp[gestiones_camp['contactabilidad'] == 'CONTACTO_EFECTIVO']),
                        'pdps': len(gestiones_camp[gestiones_camp['es_pdp'] == 'SI']),
                        'monto_compromisos': gestiones_camp['monto_compromiso'].sum()
                    }
                    kpi['tasa_contactabilidad'] = round(kpi['contactos_efectivos'] / kpi['total_gestiones'] * 100, 2)
                    kpi['tasa_pdp'] = round(kpi['pdps'] / kpi['contactos_efectivos'] * 100, 2) if kpi['contactos_efectivos'] > 0 else 0
                    kpis_por_campania.append(kpi)
        
        # 5. Inicializar generador de reportes
        report_generator = TelefonicaReportGenerator(fecha_inicio, fecha_fin)
        
        # 6. Cargar datos al generador
        report_generator.load_data_from_processing(
            gestiones_df=gestiones_df,
            calendario_df=calendario_df,
            asignacion_df=asignacion_df,
            pagos_df=pagos_df,
            kpis_campania=kpis_por_campania
        )
        
        # 7. Crear directorio temporal para archivos
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        archivos_generados = {}
        
        # 8. Generar archivos según formato solicitado
        if formato in ["excel", "ambos"]:
            excel_path = os.path.join(temp_dir, f"Informe_Semanal_Telefonica_{timestamp}.xlsx")
            excel_file = report_generator.generate_excel_report(excel_path)
            archivos_generados['excel'] = {
                'filename': os.path.basename(excel_file),
                'path': excel_file,
                'size_mb': round(os.path.getsize(excel_file) / 1024 / 1024, 2)
            }
            logger.info(f"✅ Excel generado: {archivos_generados['excel']['filename']}")
        
        if formato in ["powerpoint", "ambos"]:
            ppt_path = os.path.join(temp_dir, f"Presentacion_Semanal_Telefonica_{timestamp}.pptx")
            ppt_file = report_generator.generate_powerpoint_report(ppt_path)
            archivos_generados['powerpoint'] = {
                'filename': os.path.basename(ppt_file),
                'path': ppt_file,
                'size_mb': round(os.path.getsize(ppt_file) / 1024 / 1024, 2)
            }
            logger.info(f"✅ PowerPoint generado: {archivos_generados['powerpoint']['filename']}")
        
        # 9. Preparar respuesta con información de archivos
        response_data = {
            "status": "success",
            "message": "Reportes generados exitosamente",
            "periodo": f"{fecha_inicio} a {fecha_fin}",
            "timestamp": timestamp,
            "formato_solicitado": formato,
            "datos_procesados": {
                "campañas": len(calendario_df),
                "gestiones": len(gestiones_df),
                "pagos": len(pagos_df),
                "kpis_campania": len(kpis_por_campania)
            },
            "archivos_generados": archivos_generados,
            "enlaces_descarga": {}
        }
        
        # 10. Crear enlaces de descarga
        if "excel" in archivos_generados:
            response_data["enlaces_descarga"]["excel"] = f"/download-excel/{archivos_generados['excel']['filename']}"
        
        if "powerpoint" in archivos_generados:
            response_data["enlaces_descarga"]["powerpoint"] = f"/download-powerpoint/{archivos_generados['powerpoint']['filename']}"
        
        # 11. Agregar resumen ejecutivo para referencia
        resumen_ejecutivo = report_generator.data['resumen_ejecutivo']
        response_data["resumen_ejecutivo"] = {
            "total_gestiones": resumen_ejecutivo.get('total_gestiones', 0),
            "contactos_efectivos": resumen_ejecutivo.get('total_contactos_efectivos', 0),
            "tasa_contactabilidad": resumen_ejecutivo.get('tasa_contactabilidad_global', 0),
            "compromisos": resumen_ejecutivo.get('total_compromisos', 0),
            "monto_compromisos": resumen_ejecutivo.get('monto_compromisos_call', 0)
        }
        
        logger.info(f"🎉 Reportes generados exitosamente en: {temp_dir}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error generando reportes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando reportes: {str(e)}")

@app.get("/download-excel/{filename}")
async def download_excel(filename: str):
    """🆕 Descargar archivo Excel generado"""
    try:
        # Buscar archivo en directorio temporal
        temp_dir = tempfile.gettempdir()
        
        # Buscar el archivo en subdirectorios temporales
        file_path = None
        for root, dirs, files in os.walk(temp_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo Excel no encontrado: {filename}")
        
        logger.info(f"📊 Descargando Excel: {filename}")
        
        return FileResponse(
            path=file_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error descargando Excel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

@app.get("/download-powerpoint/{filename}")
async def download_powerpoint(filename: str):
    """🆕 Descargar archivo PowerPoint generado"""
    try:
        # Buscar archivo en directorio temporal
        temp_dir = tempfile.gettempdir()
        
        # Buscar el archivo en subdirectorios temporales
        file_path = None
        for root, dirs, files in os.walk(temp_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo PowerPoint no encontrado: {filename}")
        
        logger.info(f"📈 Descargando PowerPoint: {filename}")
        
        return FileResponse(
            path=file_path,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error descargando PowerPoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

@app.post("/validate-vigencias")
async def validate_vigencias_logic():
    """Endpoint específico para validar que la lógica de vigencias funciona correctamente"""
    try:
        calendario_df = bq_manager.get_control_calendar_with_vigencias()
        gestiones_df = bq_manager.get_unified_gestiones_by_vigencias(calendario_df)
        
        validation = vigencia_processor.validate_vigencias_logic(calendario_df, gestiones_df)
        
        # Análisis adicional
        if not gestiones_df.empty:
            validation['analisis_detallado'] = {
                'gestiones_por_campania': gestiones_df.groupby('archivo').size().to_dict(),
                'distribucion_temporal': gestiones_df.groupby('tipo_cartera')['dias_desde_asignacion'].describe().to_dict()
            }
        
        return {
            "status": "validation_complete",
            "resultado_validacion": validation,
            "conclusion": "VIGENCIAS CORRECTAS" if validation['gestiones_fuera_vigencia'] == 0 else "HAY PROBLEMAS DE VIGENCIA"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando vigencias: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        test_query = "SELECT 1 as test"
        bq_manager.client.query(test_query).result()
        
        # Test rápido de calendario
        calendario_df = bq_manager.get_control_calendar_with_vigencias()
        
        return {
            "status": "healthy", 
            "bigquery": "connected",
            "calendario_vigencias": len(calendario_df),
            "version": "2.2.0 - Sistema completo con reportes",
            "features": [
                "Vigencias corregidas",
                "Generación Excel automática",
                "Generación PowerPoint automática", 
                "Descarga de archivos"
            ]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
