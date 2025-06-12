"""
FACO WEEKLY - Sistema de Reportes Automatizados
===============================================

Sistema para generar reportes semanales de gestión de cobranza 
basado en calendario_v2 como tabla de control principal.

Reglas de Negocio:
- Solo negocio "MOVIL" = servicio Móvil, resto = Fijo
- Asignaciones desde 2025-06-11 en adelante
- Gestiones filtradas según calendario de gestión
- cod_luna como unidad de gestión
- Atribución de pagos con ventana de 30 días
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
    title="FACO Weekly - Reportes Telefónica",
    description="Sistema automatizado de reportes semanales de cobranza",
    version="1.0.0"
)

class BigQueryManager:
    """Gestor de extracción de datos desde BigQuery"""
    
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
    
    def get_asignacion_data(self, archivos_control: List[str]) -> pd.DataFrame:
        """Extrae asignaciones basado en archivos del calendario"""
        archivos_str = "', '".join([f"{arch}.txt" for arch in archivos_control])
        
        query = f"""
        SELECT 
            cliente,
            cuenta,
            cod_luna,
            negocio,
            min_vto,
            tramo_gestion,
            zona,
            decil_contacto,
            decil_pago,
            tipo_linea,
            cod_sistema,
            archivo,
            DATE(creado_el) as fecha_carga,
            -- Servicio: solo MOVIL es móvil, resto fijo
            CASE 
                WHEN UPPER(negocio) = 'MOVIL' THEN 'Movil'
                ELSE 'Fijo'
            END as servicio
        FROM `{self.dataset}.batch_P3fV4dWNeMkN5RJMhV8e_asignacion`
        WHERE creado_el >= '2025-06-11'
            AND archivo IN ('{archivos_str}')
            AND motivo_rechazo IS NULL
        """
        return self.client.query(query).to_dataframe()
    
    def get_deuda_vigente(self, fecha_asignacion: str) -> pd.DataFrame:
        """Extrae deuda vigente a la fecha de asignación"""
        query = f"""
        WITH deuda_ranked AS (
            SELECT 
                cod_cuenta,
                nro_documento,
                fecha_vencimiento,
                monto_exigible,
                archivo,
                DATE(creado_el) as fecha_carga,
                ROW_NUMBER() OVER (
                    PARTITION BY nro_documento 
                    ORDER BY DATE(creado_el) DESC
                ) as rn
            FROM `{self.dataset}.batch_P3fV4dWNeMkN5RJMhV8e_tran_deuda`
            WHERE DATE(creado_el) <= '{fecha_asignacion}'
                AND motivo_rechazo IS NULL
                AND monto_exigible > 0
        )
        SELECT 
            cod_cuenta,
            nro_documento,
            fecha_vencimiento,
            monto_exigible,
            archivo,
            fecha_carga
        FROM deuda_ranked
        WHERE rn = 1
        """
        return self.client.query(query).to_dataframe()
    
    def get_gestiones_periodo(self, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        """Extrae gestiones del período según calendario"""
        # Gestiones CALL
        query_call = f"""
        SELECT 
            'CALL' as canal,
            document as cod_documento,
            DATE(date) as fecha_gestion,
            EXTRACT(HOUR FROM date) as hora_gestion,
            COALESCE(nombre_agente, 'DISCADOR') as ejecutivo,
            correo_agente,
            management as tipificacion,
            sub_management as subtipificacion,
            duracion,
            monto_compromiso,
            fecha_compromiso,
            -- Homologación de contactabilidad
            CASE 
                WHEN UPPER(management) LIKE '%CONTACTO%' 
                     OR UPPER(management) LIKE '%COMPROMISO%'
                     OR UPPER(management) LIKE '%PROMESA%'
                     OR UPPER(management) LIKE '%ACEPTA%' THEN 'CONTACTO_EFECTIVO'
                WHEN UPPER(management) LIKE '%NO CONTESTA%'
                     OR UPPER(management) LIKE '%OCUPADO%'
                     OR UPPER(management) LIKE '%APAGADO%'
                     OR UPPER(management) LIKE '%BUZÓN%' THEN 'NO_CONTACTO'
                ELSE 'CONTACTO_NO_EFECTIVO'
            END as tipo_contacto
        FROM `{self.dataset}.mibotair_P3fV4dWNeMkN5RJMhV8e`
        WHERE DATE(date) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        
        UNION ALL
        
        SELECT 
            'VOICEBOT' as canal,
            document as cod_documento,
            DATE(date) as fecha_gestion,
            EXTRACT(HOUR FROM date) as hora_gestion,
            'VOICEBOT' as ejecutivo,
            NULL as correo_agente,
            management as tipificacion,
            sub_management as subtipificacion,
            duracion,
            CAST(NULL AS FLOAT64) as monto_compromiso,
            CAST(fecha_compromiso AS DATE) as fecha_compromiso,
            CASE 
                WHEN UPPER(management) LIKE '%CONTACTO%' 
                     OR UPPER(management) LIKE '%COMPROMISO%'
                     OR UPPER(compromiso) = 'SI' THEN 'CONTACTO_EFECTIVO'
                WHEN UPPER(management) LIKE '%NO CONTESTA%'
                     OR UPPER(management) LIKE '%OCUPADO%'
                     OR UPPER(management) LIKE '%APAGADO%' THEN 'NO_CONTACTO'
                ELSE 'CONTACTO_NO_EFECTIVO'
            END as tipo_contacto
        FROM `{self.dataset}.voicebot_P3fV4dWNeMkN5RJMhV8e`
        WHERE DATE(date) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        """
        
        return self.client.query(query_call).to_dataframe()
    
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

class BusinessLogicProcessor:
    """Procesador de lógica de negocio"""
    
    def __init__(self):
        pass
    
    def resolve_duplicated_cod_lunas(self, asignacion_df: pd.DataFrame) -> pd.DataFrame:
        """
        Resuelve duplicidades de cod_luna en múltiples carteras.
        Regla: Si está en 2 carteras, vale ambas para gestión y atribución.
        """
        logger.info(f"Procesando {len(asignacion_df)} asignaciones...")
        
        # Marcar cod_lunas duplicados
        duplicated_mask = asignacion_df.duplicated(subset=['cod_luna'], keep=False)
        asignacion_df['es_duplicado'] = duplicated_mask
        
        # Estadísticas de duplicidad
        total_cod_lunas = asignacion_df['cod_luna'].nunique()
        cod_lunas_duplicados = asignacion_df[duplicated_mask]['cod_luna'].nunique()
        
        logger.info(f"Total cod_lunas: {total_cod_lunas}")
        logger.info(f"cod_lunas en múltiples carteras: {cod_lunas_duplicados}")
        
        return asignacion_df
    
    def create_universo_gestionable(self, asignacion_df: pd.DataFrame, 
                                   deuda_df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea universo gestionable: solo casos con deuda vigente a fecha de asignación.
        """
        # Mapear cod_cuenta a cod_luna a través de la asignación
        cuenta_luna_map = asignacion_df[['cuenta', 'cod_luna']].drop_duplicates()
        
        # Unir deuda con asignación por cuenta
        universo = deuda_df.merge(
            cuenta_luna_map,
            left_on='cod_cuenta',
            right_on='cuenta',
            how='inner'
        )
        
        # Estadísticas
        total_asignaciones = len(asignacion_df)
        con_deuda = len(universo)
        
        logger.info(f"Asignaciones totales: {total_asignaciones}")
        logger.info(f"Con deuda vigente: {con_deuda}")
        logger.info(f"% Universo gestionable: {(con_deuda/total_asignaciones)*100:.1f}%")
        
        return universo
    
    def attribute_payments(self, gestiones_df: pd.DataFrame, 
                          pagos_df: pd.DataFrame, 
                          universo_df: pd.DataFrame) -> pd.DataFrame:
        """
        Atribuye pagos a la última gestión efectiva en ventana de 30 días.
        """
        if gestiones_df.empty or pagos_df.empty:
            return pd.DataFrame()
        
        # Mapear documento a cod_luna
        doc_luna_map = universo_df[['nro_documento', 'cod_luna']].drop_duplicates()
        
        # Agregar cod_luna a gestiones
        gestiones_with_luna = gestiones_df.merge(
            doc_luna_map,
            left_on='cod_documento',
            right_on='nro_documento',
            how='inner'
        )
        
        # Agregar cod_luna a pagos
        pagos_with_luna = pagos_df.merge(
            doc_luna_map,
            left_on='nro_documento',
            right_on='nro_documento',
            how='inner'
        )
        
        # Atribuir última gestión antes del pago (ventana 30 días)
        atribuciones = []
        
        for _, pago in pagos_with_luna.iterrows():
            # Filtrar gestiones del mismo cod_luna en ventana de 30 días
            gestiones_candidatas = gestiones_with_luna[
                (gestiones_with_luna['cod_luna'] == pago['cod_luna']) &
                (gestiones_with_luna['fecha_gestion'] <= pago['fecha_pago']) &
                (gestiones_with_luna['fecha_gestion'] >= pago['fecha_pago'] - timedelta(days=30))
            ]
            
            if not gestiones_candidatas.empty:
                # Priorizar por tipo de contacto y fecha
                gestiones_candidatas = gestiones_candidatas.sort_values([
                    'tipo_contacto',  # CONTACTO_EFECTIVO primero
                    'fecha_gestion'   # Más reciente
                ], ascending=[True, False])
                
                ultima_gestion = gestiones_candidatas.iloc[0]
                
                atribuciones.append({
                    'nro_documento': pago['nro_documento'],
                    'cod_luna': pago['cod_luna'],
                    'fecha_pago': pago['fecha_pago'],
                    'monto_pagado': pago['monto_cancelado'],
                    'ejecutivo_atribuido': ultima_gestion['ejecutivo'],
                    'canal_atribuido': ultima_gestion['canal'],
                    'fecha_gestion_atribuida': ultima_gestion['fecha_gestion'],
                    'tipo_contacto_atribuido': ultima_gestion['tipo_contacto'],
                    'dias_desde_gestion': (pago['fecha_pago'] - ultima_gestion['fecha_gestion']).days
                })
            else:
                # Pago sin gestión atribuible
                atribuciones.append({
                    'nro_documento': pago['nro_documento'],
                    'cod_luna': pago['cod_luna'],
                    'fecha_pago': pago['fecha_pago'],
                    'monto_pagado': pago['monto_cancelado'],
                    'ejecutivo_atribuido': None,
                    'canal_atribuido': None,
                    'fecha_gestion_atribuida': None,
                    'tipo_contacto_atribuido': 'SIN_GESTION',
                    'dias_desde_gestion': None
                })
        
        return pd.DataFrame(atribuciones)

class KPICalculator:
    """Calculadora de KPIs para reportes"""
    
    def __init__(self, asignacion_df, gestiones_df, pagos_df, atribuciones_df):
        self.asignacion = asignacion_df
        self.gestiones = gestiones_df
        self.pagos = pagos_df
        self.atribuciones = atribuciones_df
    
    def calculate_summary_metrics(self) -> Dict:
        """Calcula métricas resumen para el período"""
        # Universo asignado
        total_asignados = self.asignacion['cod_luna'].nunique()
        total_cuentas = self.asignacion['cuenta'].nunique()
        
        # Gestiones
        total_gestiones = len(self.gestiones)
        clientes_gestionados = self.gestiones['cod_documento'].nunique() if not self.gestiones.empty else 0
        
        # Contactabilidad
        contactos_efectivos = len(self.gestiones[self.gestiones['tipo_contacto'] == 'CONTACTO_EFECTIVO']) if not self.gestiones.empty else 0
        tasa_contactabilidad = (contactos_efectivos / total_gestiones * 100) if total_gestiones > 0 else 0
        
        # Pagos
        total_pagos = len(self.pagos) if not self.pagos.empty else 0
        monto_total_pagos = self.pagos['monto_cancelado'].sum() if not self.pagos.empty else 0
        
        # Atribuciones
        pagos_atribuidos = len(self.atribuciones[self.atribuciones['ejecutivo_atribuido'].notna()]) if not self.atribuciones.empty else 0
        tasa_atribucion = (pagos_atribuidos / total_pagos * 100) if total_pagos > 0 else 0
        
        return {
            'periodo_analisis': {
                'total_asignados': total_asignados,
                'total_cuentas': total_cuentas,
                'total_gestiones': total_gestiones,
                'clientes_gestionados': clientes_gestionados,
                'total_pagos': total_pagos,
                'monto_total_pagos': float(monto_total_pagos)
            },
            'kpis': {
                'tasa_contactabilidad': round(tasa_contactabilidad, 2),
                'tasa_atribucion': round(tasa_atribucion, 2),
                'intensidad_gestion': round(total_gestiones / clientes_gestionados, 2) if clientes_gestionados > 0 else 0,
                'ticket_promedio_pago': round(monto_total_pagos / total_pagos, 2) if total_pagos > 0 else 0
            }
        }
    
    def get_ranking_agentes(self, top_n: int = 20) -> pd.DataFrame:
        """Genera ranking de agentes por performance"""
        if self.gestiones.empty:
            return pd.DataFrame()
        
        # Agrupar por ejecutivo (excluir VOICEBOT para ranking)
        agentes = self.gestiones[
            self.gestiones['ejecutivo'] != 'VOICEBOT'
        ].groupby('ejecutivo').agg({
            'cod_documento': 'count',
            'tipo_contacto': [
                lambda x: (x == 'CONTACTO_EFECTIVO').sum(),
                lambda x: (x == 'NO_CONTACTO').sum()
            ],
            'duracion': 'sum',
            'monto_compromiso': ['sum', 'count']
        }).reset_index()
        
        # Aplanar columnas
        agentes.columns = [
            'ejecutivo', 'total_gestiones', 'contactos_efectivos', 
            'no_contactos', 'duracion_total', 'monto_comprometido', 'num_compromisos'
        ]
        
        # Calcular KPIs
        agentes['tasa_contactabilidad'] = (agentes['contactos_efectivos'] / agentes['total_gestiones'] * 100).round(2)
        agentes['intensidad'] = (agentes['duracion_total'] / agentes['total_gestiones'] / 60).round(2)
        
        # Agregar pagos atribuidos
        if not self.atribuciones.empty:
            pagos_por_agente = self.atribuciones.groupby('ejecutivo_atribuido').agg({
                'monto_pagado': 'sum',
                'cod_luna': 'nunique'
            }).reset_index()
            pagos_por_agente.columns = ['ejecutivo', 'monto_pagado_atribuido', 'clientes_pagaron']
            
            agentes = agentes.merge(pagos_por_agente, on='ejecutivo', how='left')
            agentes['monto_pagado_atribuido'] = agentes['monto_pagado_atribuido'].fillna(0)
            agentes['clientes_pagaron'] = agentes['clientes_pagaron'].fillna(0)
        else:
            agentes['monto_pagado_atribuido'] = 0
            agentes['clientes_pagaron'] = 0
        
        # Ordenar por criterios múltiples
        agentes = agentes.sort_values([
            'monto_pagado_atribuido', 'tasa_contactabilidad', 'total_gestiones'
        ], ascending=[False, False, False])
        
        return agentes.head(top_n)

# Inicializar managers
bq_manager = BigQueryManager()
business_processor = BusinessLogicProcessor()

@app.get("/")
async def root():
    return {
        "message": "FACO Weekly - Sistema de Reportes Telefónica",
        "version": "1.0.0",
        "endpoints": {
            "/process-weekly": "Procesa datos semanales según calendario",
            "/generate-report": "Genera reportes Excel/PowerPoint",
            "/health": "Estado del sistema"
        }
    }

@app.get("/health")
async def health_check():
    try:
        # Test BigQuery
        test_query = "SELECT 1 as test"
        bq_manager.client.query(test_query).result()
        return {"status": "healthy", "bigquery": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/process-weekly")
async def process_weekly_data(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
):
    """
    Procesa datos semanales basado en calendario_v2
    """
    try:
        # Configurar fechas
        if not fecha_fin:
            fecha_fin = date.today().strftime('%Y-%m-%d')
        if not fecha_inicio:
            fecha_inicio = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        logger.info(f"Procesando período: {fecha_inicio} a {fecha_fin}")
        
        # 1. Obtener calendario de control
        calendar_df = bq_manager.get_control_calendar('2025-06-11')
        if calendar_df.empty:
            raise HTTPException(status_code=404, detail="No hay campañas en calendario")
        
        # 2. Extraer asignaciones basadas en calendario
        archivos_control = calendar_df['archivo'].tolist()
        asignacion_df = bq_manager.get_asignacion_data(archivos_control)
        
        # 3. Procesar duplicidades
        asignacion_df = business_processor.resolve_duplicated_cod_lunas(asignacion_df)
        
        # 4. Obtener deuda vigente
        deuda_df = bq_manager.get_deuda_vigente(fecha_fin)
        
        # 5. Crear universo gestionable
        universo_df = business_processor.create_universo_gestionable(asignacion_df, deuda_df)
        
        # 6. Extraer gestiones del período
        gestiones_df = bq_manager.get_gestiones_periodo(fecha_inicio, fecha_fin)
        
        # 7. Extraer pagos
        pagos_df = bq_manager.get_pagos_periodo(fecha_inicio, fecha_fin)
        
        # 8. Atribuir pagos
        atribuciones_df = business_processor.attribute_payments(gestiones_df, pagos_df, universo_df)
        
        # 9. Calcular KPIs
        kpi_calc = KPICalculator(asignacion_df, gestiones_df, pagos_df, atribuciones_df)
        summary_metrics = kpi_calc.calculate_summary_metrics()
        ranking_agentes = kpi_calc.get_ranking_agentes()
        
        return {
            "status": "success",
            "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
            "calendario": {
                "campañas_activas": len(calendar_df),
                "archivos_procesados": len(archivos_control)
            },
            "datos_procesados": {
                "asignaciones": len(asignacion_df),
                "universo_gestionable": len(universo_df),
                "gestiones": len(gestiones_df),
                "pagos": len(pagos_df),
                "atribuciones": len(atribuciones_df)
            },
            "metricas": summary_metrics,
            "top_agentes": ranking_agentes.head(5).to_dict('records') if not ranking_agentes.empty else []
        }
        
    except Exception as e:
        logger.error(f"Error procesando datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando datos: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
