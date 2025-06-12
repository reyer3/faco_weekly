"""
FACO WEEKLY - Sistema de Reportes Automatizados (VERSIÓN AVANZADA)
==================================================================

Versión actualizada con lógica completa de homologación y gestiones unificadas.
Incluye tablas de homologación para tipificaciones y usuarios.
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

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FACO Weekly - Reportes Telefónica (Avanzado)",
    description="Sistema automatizado con lógica completa de homologación",
    version="2.0.0"
)

class AdvancedBigQueryManager:
    """Gestor avanzado con lógica de homologación completa"""
    
    def __init__(self):
        self.client = bigquery.Client(project="mibot-222814")
        self.dataset = "BI_USA"
    
    def get_control_calendar(self, fecha_inicio: str = None) -> pd.DataFrame:
        """Extrae tabla de control calendario_v2"""
        where_clause = ""
        if fecha_inicio:
            where_clause = f"WHERE fecha_asignacion >= '{fecha_inicio}'"
            
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
            END as tipo_cartera
        FROM `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_calendario_v2`
        {where_clause}
        ORDER BY fecha_asignacion DESC
        """
        return self.client.query(query).to_dataframe()
    
    def get_unified_gestiones(self, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        """
        Extrae gestiones unificadas con homologación completa
        Basado en la lógica avanzada proporcionada
        """
        query = f"""
        WITH
        -- 1. Unificar las gestiones de ambos canales, ahora incluyendo el DNI del ejecutivo
        gestiones_unificadas AS (
          -- Lógica de gestiones_call
          SELECT
            mba.date,
            SAFE_CAST(mba.document AS INT64) AS cod_luna,
            'CALL' AS canal,
            COALESCE(u.nombre_apellidos, 'AGENTE NO IDENTIFICADO') AS ejecutivo_homologado,
            COALESCE(mba.nombre_agente, 'DISCADOR') AS ejecutivo,
            -- DNI del agente humano
            SAFE_CAST(u.dni AS STRING) AS dni_ejecutivo,
            -- Campos para la lógica de JOIN de homologación
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
          WHERE DATE(mba.date) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'

          UNION ALL

          -- Lógica de gestiones_bot
          SELECT
            vb.date,
            SAFE_CAST(vb.document AS INT64) AS cod_luna,
            'VOICEBOT' AS canal,
            'VOICEBOT' AS ejecutivo_homologado,
            'VOICEBOT' AS ejecutivo,
            -- >>> DNI FICTICIO PARA EL BOT <<<
            '99999999' AS dni_ejecutivo,
            -- Campos para la lógica de JOIN de homologación
            vb.management, NULL, NULL, NULL,
            vb.management AS bot_management,
            vb.compromiso AS bot_compromiso,
            NULL AS duracion
          FROM `{self.dataset}.voicebot_P3fV4dWNeMkN5RJMhV8e` vb
          WHERE DATE(vb.date) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        ),

        -- 2. Homologar las gestiones unificadas
        gestiones_homologadas AS (
          SELECT
            g.*,
            CASE
              WHEN g.canal = 'CALL' THEN COALESCE(SAFE_CAST(h_call.peso AS INT64), 0)
              WHEN g.canal = 'VOICEBOT' THEN COALESCE(SAFE_CAST(h_bot.peso_homologado AS INT64), 0)
              ELSE 0 -- Valor por defecto si el canal no es reconocido
            END AS peso,
            -- Lógica de homologación unificada con valores corregidos
            CASE
              WHEN g.canal = 'CALL' THEN COALESCE(h_call.contactabilidad, 'NO_HOMOLOGADO')
              WHEN g.canal = 'VOICEBOT' THEN COALESCE(h_bot.contactabilidad_homologada, 'NO_HOMOLOGADO')
            END AS contactabilidad,
            CASE
              WHEN g.canal = 'CALL' THEN COALESCE(h_call.pdp, 'NO')
              WHEN g.canal = 'VOICEBOT' THEN COALESCE(IF(h_bot.es_pdp_homologado = 1, 'SI', 'NO'), 'NO')
            END AS es_pdp,
            -- Traemos los n1,n2,n3 homologados del bot para estandarizar
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
            -- Estandarizamos el campo 'compromiso'
            CASE
                WHEN g.canal = 'CALL' THEN g.sub_management
                ELSE g.bot_compromiso
            END AS compromiso
          FROM gestiones_unificadas g
          LEFT JOIN `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_v2` h_call
            ON g.canal = 'CALL' AND g.n1 = h_call.n_1 AND g.n2 = h_call.n_2 AND g.n3 = h_call.n_3
          LEFT JOIN `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_voicebot` h_bot
            ON g.canal = 'VOICEBOT' AND g.bot_management = h_bot.bot_management 
            AND COALESCE(g.sub_management, '') = h_bot.bot_sub_management 
            AND COALESCE(g.bot_compromiso, '') = h_bot.bot_compromiso
        )

        -- 3. Unir con la asignación para obtener el monto exigible
        SELECT
          -- Dimensiones y hechos base de la gestión
          h.date,
          h.cod_luna,
          h.canal,
          h.ejecutivo,
          h.ejecutivo_homologado,
          h.dni_ejecutivo,
          h.duracion,
          -- Detalle de tipificación final
          h.n1_final AS n1,
          h.n2_final AS n2,
          h.n3_final AS n3,
          h.compromiso,
          -- Homologación final
          h.contactabilidad,
          h.es_pdp,
          -- Lógica del monto de compromiso
          h.peso,
          CASE
            WHEN h.es_pdp = 'SI' THEN COALESCE(a.monto_exigible, 0)
            ELSE 0
          END AS monto_compromiso,
          -- Campos adicionales de asignación
          a.monto_exigible,
          a.servicio,
          a.tipo_cartera
        FROM gestiones_homologadas h
        LEFT JOIN `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_fact_asignacion` a
          ON h.cod_luna = a.cod_luna
        WHERE h.contactabilidad != 'NO_HOMOLOGADO'  -- Excluir no homologados
        ORDER BY h.date DESC
        """
        
        logger.info(f"Ejecutando query de gestiones unificadas para período {fecha_inicio} a {fecha_fin}")
        result = self.client.query(query).to_dataframe()
        logger.info(f"Gestiones unificadas extraídas: {len(result)}")
        
        return result
    
    def get_asignacion_fact(self, archivos_control: List[str] = None) -> pd.DataFrame:
        """Extrae fact_asignacion con filtros de calendario"""
        where_clause = "WHERE 1=1"
        
        if archivos_control:
            archivos_str = "', '".join(archivos_control)
            where_clause += f" AND archivo IN ('{archivos_str}')"
        
        query = f"""
        SELECT 
            cod_luna,
            monto_exigible,
            servicio,
            tipo_cartera,
            archivo,
            fecha_asignacion,
            -- Calcular servicios según regla: solo MOVIL es móvil
            CASE 
                WHEN UPPER(servicio) = 'MOVIL' THEN 'Movil'
                ELSE 'Fijo'
            END as servicio_normalizado
        FROM `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_fact_asignacion`
        {where_clause}
        ORDER BY fecha_asignacion DESC
        """
        
        return self.client.query(query).to_dataframe()
    
    def get_pagos_periodo(self, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        """Extrae pagos del período"""
        query = f"""
        SELECT 
            cod_sistema,
            nro_documento,
            monto_cancelado,
            fecha_pago,
            archivo
        FROM `{self.dataset}.batch_P3fV4dWNeMkN5RJMhV8e_pagos`
        WHERE fecha_pago BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
            AND motivo_rechazo IS NULL
            AND monto_cancelado > 0
        """
        return self.client.query(query).to_dataframe()
    
    def get_homologation_status(self) -> Dict:
        """Verifica estado de las homologaciones"""
        queries = {
            'usuarios': f"SELECT COUNT(*) as total FROM `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_usuarios`",
            'call_homolog': f"SELECT COUNT(*) as total FROM `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_v2`",
            'bot_homolog': f"SELECT COUNT(*) as total FROM `{self.dataset}.homologacion_P3fV4dWNeMkN5RJMhV8e_voicebot`",
            'fact_asignacion': f"SELECT COUNT(*) as total FROM `{self.dataset}.dash_P3fV4dWNeMkN5RJMhV8e_fact_asignacion`"
        }
        
        status = {}
        for name, query in queries.items():
            try:
                result = self.client.query(query).to_dataframe()
                status[name] = int(result.iloc[0]['total'])
            except Exception as e:
                status[name] = f"Error: {str(e)}"
        
        return status

class AdvancedBusinessProcessor:
    """Procesador de lógica de negocio avanzada"""
    
    def __init__(self):
        pass
    
    def analyze_contactability_distribution(self, gestiones_df: pd.DataFrame) -> Dict:
        """Analiza distribución de contactabilidad homologada"""
        if gestiones_df.empty:
            return {}
        
        # Distribución por contactabilidad
        contactability_dist = gestiones_df['contactabilidad'].value_counts().to_dict()
        
        # Distribución por canal
        canal_dist = gestiones_df.groupby(['canal', 'contactabilidad']).size().unstack(fill_value=0)
        
        # PDP por canal
        pdp_dist = gestiones_df.groupby(['canal', 'es_pdp']).size().unstack(fill_value=0)
        
        # Ejecutivos con más gestiones
        top_ejecutivos = gestiones_df.groupby(['ejecutivo_homologado', 'canal']).agg({
            'cod_luna': 'count',
            'monto_compromiso': 'sum',
            'contactabilidad': lambda x: (x == 'CONTACTO_EFECTIVO').sum()
        }).reset_index()
        
        top_ejecutivos.columns = ['ejecutivo', 'canal', 'total_gestiones', 'monto_compromiso', 'contactos_efectivos']
        top_ejecutivos['tasa_efectividad'] = (
            top_ejecutivos['contactos_efectivos'] / top_ejecutivos['total_gestiones'] * 100
        ).round(2)
        
        return {
            'contactabilidad_distribucion': contactability_dist,
            'canal_contactabilidad': canal_dist.to_dict() if not canal_dist.empty else {},
            'pdp_distribucion': pdp_dist.to_dict() if not pdp_dist.empty else {},
            'top_ejecutivos': top_ejecutivos.sort_values('monto_compromiso', ascending=False).head(10).to_dict('records')
        }
    
    def calculate_advanced_kpis(self, gestiones_df: pd.DataFrame, asignacion_df: pd.DataFrame) -> Dict:
        """Calcula KPIs avanzados con la nueva lógica"""
        if gestiones_df.empty:
            return {}
        
        # KPIs base
        total_gestiones = len(gestiones_df)
        contactos_efectivos = len(gestiones_df[gestiones_df['contactabilidad'] == 'CONTACTO_EFECTIVO'])
        pdps_totales = len(gestiones_df[gestiones_df['es_pdp'] == 'SI'])
        monto_total_compromisos = gestiones_df['monto_compromiso'].sum()
        
        # Clientes únicos gestionados
        clientes_gestionados = gestiones_df['cod_luna'].nunique()
        
        # KPIs por canal
        kpis_por_canal = gestiones_df.groupby('canal').agg({
            'cod_luna': ['count', 'nunique'],
            'contactabilidad': lambda x: (x == 'CONTACTO_EFECTIVO').sum(),
            'es_pdp': lambda x: (x == 'SI').sum(),
            'monto_compromiso': 'sum',
            'duracion': 'mean'
        }).round(2)
        
        # Universo asignado vs gestionado
        universo_asignado = asignacion_df['cod_luna'].nunique() if not asignacion_df.empty else 0
        cobertura_gestion = (clientes_gestionados / universo_asignado * 100) if universo_asignado > 0 else 0
        
        return {
            'kpis_generales': {
                'total_gestiones': total_gestiones,
                'clientes_gestionados': clientes_gestionados,
                'contactos_efectivos': contactos_efectivos,
                'tasa_contactabilidad_efectiva': round((contactos_efectivos / total_gestiones * 100), 2),
                'pdps_totales': pdps_totales,
                'tasa_pdp': round((pdps_totales / contactos_efectivos * 100), 2) if contactos_efectivos > 0 else 0,
                'monto_total_compromisos': float(monto_total_compromisos),
                'ticket_promedio_compromiso': round((monto_total_compromisos / pdps_totales), 2) if pdps_totales > 0 else 0,
                'universo_asignado': universo_asignado,
                'cobertura_gestion': round(cobertura_gestion, 2)
            },
            'kpis_por_canal': kpis_por_canal.to_dict() if not kpis_por_canal.empty else {}
        }
    
    def detect_homologation_issues(self, gestiones_df: pd.DataFrame) -> Dict:
        """Detecta problemas de homologación"""
        issues = {
            'total_gestiones': len(gestiones_df),
            'no_homologadas': 0,
            'sin_dni': 0,
            'ejecutivos_sin_identificar': 0,
            'peso_cero': 0
        }
        
        if not gestiones_df.empty:
            issues['no_homologadas'] = len(gestiones_df[gestiones_df['contactabilidad'] == 'NO_HOMOLOGADO'])
            issues['sin_dni'] = len(gestiones_df[gestiones_df['dni_ejecutivo'].isna()])
            issues['ejecutivos_sin_identificar'] = len(gestiones_df[gestiones_df['ejecutivo_homologado'] == 'AGENTE NO IDENTIFICADO'])
            issues['peso_cero'] = len(gestiones_df[gestiones_df['peso'] == 0])
        
        # Calcular porcentajes
        total = issues['total_gestiones']
        if total > 0:
            for key in ['no_homologadas', 'sin_dni', 'ejecutivos_sin_identificar', 'peso_cero']:
                issues[f'{key}_pct'] = round((issues[key] / total * 100), 2)
        
        return issues

class AdvancedKPICalculator:
    """Calculadora avanzada de KPIs"""
    
    def __init__(self, gestiones_df, asignacion_df, pagos_df):
        self.gestiones = gestiones_df
        self.asignacion = asignacion_df
        self.pagos = pagos_df
    
    def get_executive_ranking(self, top_n: int = 20, exclude_voicebot: bool = True) -> pd.DataFrame:
        """Genera ranking de ejecutivos con lógica avanzada"""
        if self.gestiones.empty:
            return pd.DataFrame()
        
        # Filtrar gestiones
        gestiones_filtered = self.gestiones.copy()
        if exclude_voicebot:
            gestiones_filtered = gestiones_filtered[gestiones_filtered['canal'] != 'VOICEBOT']
        
        # Agrupar por ejecutivo
        ranking = gestiones_filtered.groupby(['ejecutivo_homologado', 'dni_ejecutivo', 'canal']).agg({
            'cod_luna': ['count', 'nunique'],
            'contactabilidad': [
                lambda x: (x == 'CONTACTO_EFECTIVO').sum(),
                lambda x: (x == 'NO_CONTACTO').sum(),
                lambda x: (x == 'CONTACTO_NO_EFECTIVO').sum()
            ],
            'es_pdp': lambda x: (x == 'SI').sum(),
            'monto_compromiso': 'sum',
            'duracion': ['sum', 'mean'],
            'peso': 'mean'
        }).reset_index()
        
        # Aplanar columnas
        ranking.columns = [
            'ejecutivo', 'dni_ejecutivo', 'canal', 'total_gestiones', 'clientes_unicos',
            'contactos_efectivos', 'no_contactos', 'contactos_no_efectivos',
            'pdps', 'monto_comprometido', 'duracion_total', 'duracion_promedio', 'peso_promedio'
        ]
        
        # Calcular métricas derivadas
        ranking['tasa_contactabilidad_efectiva'] = (
            ranking['contactos_efectivos'] / ranking['total_gestiones'] * 100
        ).round(2)
        
        ranking['tasa_pdp'] = (
            ranking['pdps'] / ranking['contactos_efectivos'] * 100
        ).fillna(0).round(2)
        
        ranking['intensidad_minutos'] = (ranking['duracion_promedio'] / 60).round(2)
        
        ranking['productividad_score'] = (
            ranking['monto_comprometido'] * 0.4 +
            ranking['tasa_contactabilidad_efectiva'] * 0.3 +
            ranking['tasa_pdp'] * 0.2 +
            ranking['peso_promedio'] * 0.1
        ).round(2)
        
        # Ordenar por productividad
        ranking = ranking.sort_values([
            'productividad_score', 'monto_comprometido', 'tasa_contactabilidad_efectiva'
        ], ascending=[False, False, False])
        
        return ranking.head(top_n)
    
    def get_campaign_summary(self) -> Dict:
        """Resumen por campaña/cartera"""
        if self.asignacion.empty:
            return {}
        
        # Resumen por cartera
        summary_cartera = self.asignacion.groupby('tipo_cartera').agg({
            'cod_luna': 'nunique',
            'monto_exigible': 'sum'
        }).reset_index()
        
        summary_cartera.columns = ['cartera', 'clientes_asignados', 'monto_exigible_total']
        
        # Agregar gestiones por cartera si hay join posible
        if not self.gestiones.empty and 'tipo_cartera' in self.gestiones.columns:
            gestiones_cartera = self.gestiones.groupby('tipo_cartera').agg({
                'cod_luna': 'nunique',
                'contactabilidad': lambda x: (x == 'CONTACTO_EFECTIVO').sum(),
                'monto_compromiso': 'sum'
            }).reset_index()
            
            gestiones_cartera.columns = ['cartera', 'clientes_gestionados', 'contactos_efectivos', 'monto_comprometido']
            
            summary_cartera = summary_cartera.merge(gestiones_cartera, on='cartera', how='left')
            summary_cartera = summary_cartera.fillna(0)
            
            # Calcular tasas
            summary_cartera['tasa_cobertura'] = (
                summary_cartera['clientes_gestionados'] / summary_cartera['clientes_asignados'] * 100
            ).round(2)
        
        return summary_cartera.to_dict('records')

# Inicializar managers avanzados
bq_manager = AdvancedBigQueryManager()
business_processor = AdvancedBusinessProcessor()

@app.get("/")
async def root():
    return {
        "message": "FACO Weekly - Sistema Avanzado con Homologación",
        "version": "2.0.0",
        "features": [
            "Gestiones unificadas CALL + VOICEBOT",
            "Homologación completa de tipificaciones",
            "DNI de ejecutivos y mapping de usuarios",
            "Lógica de monto_compromiso basada en PDP",
            "KPIs avanzados por canal y ejecutivo"
        ],
        "endpoints": {
            "/process-advanced": "Procesamiento con lógica avanzada",
            "/homologation-status": "Estado de tablas de homologación",
            "/health": "Estado del sistema"
        }
    }

@app.get("/homologation-status")
async def get_homologation_status():
    """Verifica estado de todas las tablas de homologación"""
    try:
        status = bq_manager.get_homologation_status()
        return {
            "status": "success",
            "tablas_homologacion": status,
            "observaciones": {
                "usuarios": "Mapeo correo → nombre/dni",
                "call_homolog": "Homologación tipificaciones CALL (n1,n2,n3)",
                "bot_homolog": "Homologación tipificaciones VOICEBOT",
                "fact_asignacion": "Tabla fact con monto_exigible"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando homologación: {str(e)}")

@app.post("/process-advanced")
async def process_advanced_weekly(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
):
    """
    Procesamiento avanzado con lógica completa de homologación
    """
    try:
        # Configurar fechas
        if not fecha_fin:
            fecha_fin = date.today().strftime('%Y-%m-%d')
        if not fecha_inicio:
            fecha_inicio = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        logger.info(f"Iniciando procesamiento avanzado: {fecha_inicio} a {fecha_fin}")
        
        # 1. Verificar estado de homologación
        homolog_status = bq_manager.get_homologation_status()
        logger.info(f"Estado homologación: {homolog_status}")
        
        # 2. Obtener calendario de control
        calendar_df = bq_manager.get_control_calendar('2025-06-11')
        
        # 3. Extraer gestiones unificadas con homologación
        gestiones_df = bq_manager.get_unified_gestiones(fecha_inicio, fecha_fin)
        logger.info(f"Gestiones unificadas extraídas: {len(gestiones_df)}")
        
        # 4. Extraer fact_asignacion
        archivos_control = calendar_df['archivo'].tolist() if not calendar_df.empty else []
        asignacion_df = bq_manager.get_asignacion_fact(archivos_control)
        
        # 5. Extraer pagos
        pagos_df = bq_manager.get_pagos_periodo(fecha_inicio, fecha_fin)
        
        # 6. Análisis de contactabilidad
        contactability_analysis = business_processor.analyze_contactability_distribution(gestiones_df)
        
        # 7. KPIs avanzados
        advanced_kpis = business_processor.calculate_advanced_kpis(gestiones_df, asignacion_df)
        
        # 8. Detectar problemas de homologación
        homolog_issues = business_processor.detect_homologation_issues(gestiones_df)
        
        # 9. Ranking de ejecutivos
        kpi_calc = AdvancedKPICalculator(gestiones_df, asignacion_df, pagos_df)
        executive_ranking = kpi_calc.get_executive_ranking()
        campaign_summary = kpi_calc.get_campaign_summary()
        
        return {
            "status": "success",
            "version": "2.0.0",
            "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
            "homologacion": {
                "tablas_disponibles": homolog_status,
                "problemas_detectados": homolog_issues
            },
            "datos_procesados": {
                "campañas_calendario": len(calendar_df),
                "gestiones_unificadas": len(gestiones_df),
                "asignaciones_fact": len(asignacion_df),
                "pagos": len(pagos_df)
            },
            "analisis_contactabilidad": contactability_analysis,
            "kpis_avanzados": advanced_kpis,
            "ranking_ejecutivos": executive_ranking.head(10).to_dict('records') if not executive_ranking.empty else [],
            "resumen_campañas": campaign_summary
        }
        
    except Exception as e:
        logger.error(f"Error en procesamiento avanzado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en procesamiento avanzado: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        # Test BigQuery básico
        test_query = "SELECT 1 as test"
        bq_manager.client.query(test_query).result()
        
        # Test tablas de homologación
        homolog_status = bq_manager.get_homologation_status()
        
        return {
            "status": "healthy", 
            "bigquery": "connected",
            "homologacion_tables": homolog_status
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
