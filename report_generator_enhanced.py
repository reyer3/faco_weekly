"""
ENHANCED REPORT GENERATOR - Telefónica del Perú
==============================================

Versión mejorada del generador de reportes con análisis específicos,
métricas avanzadas y formato ejecutivo optimizado.

Características:
- Análisis consolidado CALL vs VOICEBOT
- Métricas de efectividad por tipo de cartera
- Comparativas temporales automáticas
- Recomendaciones basadas en datos
- Formato ejecutivo con colores corporativos

Autor: Sistema Automatizado FACO Weekly Enhanced
Fecha: Junio 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import tempfile
import os
from typing import Dict, List, Optional, Tuple
import logging

# Excel libraries
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, LineChart, Reference, PieChart
from openpyxl.chart.marker import DataPoint
from openpyxl.drawing.colors import ColorChoice
from openpyxl.worksheet.table import Table, TableStyleInfo

# PowerPoint libraries
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

logger = logging.getLogger(__name__)

class EnhancedTelefonicaReportGenerator:
    """
    Generador mejorado de reportes semanales para Telefónica del Perú
    
    Mejoras específicas:
    - Análisis comparativo detallado entre canales
    - Métricas de efectividad por tipo de cartera
    - Análisis de patrones temporales
    - Recomendaciones automáticas basadas en datos
    - Formato ejecutivo optimizado para stakeholders
    """
    
    # Colores corporativos Telefónica (mejorados)
    COLORS = {
        'telefonica_blue': '0019A5',
        'telefonica_light_blue': '4B9CD3', 
        'telefonica_green': '00A651',
        'telefonica_orange': 'FF6600',
        'telefonica_red': 'E60026',
        'telefonica_gray': '666666',
        'telefonica_dark_gray': '333333',
        'white': 'FFFFFF',
        'light_gray': 'F5F5F5',
        'success_green': '28A745',
        'warning_yellow': 'FFC107',
        'danger_red': 'DC3545'
    }
    
    # Métricas objetivo (benchmarks)
    BENCHMARKS = {
        'tasa_contactabilidad_call': 5.0,      # 5% objetivo CALL
        'tasa_contactabilidad_voicebot': 1.5,   # 1.5% objetivo VOICEBOT
        'tasa_compromiso': 35.0,                # 35% de compromisos sobre contactos
        'ticket_promedio_compromiso': 75.0,     # $75 promedio por compromiso
        'intensidad_gestion_diaria': 1.2        # 1.2 gestiones por cliente/día
    }
    
    def __init__(self, fecha_inicio: str, fecha_fin: str):
        """
        Inicializar generador mejorado
        
        Args:
            fecha_inicio: Fecha inicio período (YYYY-MM-DD)
            fecha_fin: Fecha fin período (YYYY-MM-DD)
        """
        self.fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        self.fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        self.periodo_str = f"{fecha_inicio} a {fecha_fin}"
        self.fecha_generacion = datetime.now()
        self.dias_periodo = (self.fecha_fin - self.fecha_inicio).days + 1
        
        # Estructura de datos mejorada
        self.data = {
            'resumen_ejecutivo': {},
            'analisis_canales': {
                'call': {},
                'voicebot': {},
                'comparativo': {}
            },
            'metricas_por_cartera': [],
            'evolucion_diaria': [],
            'carteras_activas': [],
            'analisis_efectividad': {},
            'patrones_temporales': {},
            'recomendaciones_prioritarias': [],
            'benchmarks_cumplimiento': {}
        }
    
    def load_enhanced_data(self, 
                          gestiones_df: pd.DataFrame,
                          calendario_df: pd.DataFrame,
                          asignacion_df: pd.DataFrame,
                          pagos_df: pd.DataFrame,
                          kpis_campania: List[Dict]) -> None:
        """
        Cargar y procesar datos con análisis mejorado
        
        Args:
            gestiones_df: DataFrame con gestiones procesadas
            calendario_df: DataFrame con calendario de vigencias
            asignacion_df: DataFrame con resumen de asignaciones
            pagos_df: DataFrame con pagos del período
            kpis_campania: Lista de KPIs por campaña
        """
        logger.info("🚀 Iniciando carga de datos con análisis mejorado")
        
        # Procesar datos principales
        self._process_enhanced_gestiones(gestiones_df)
        self._process_enhanced_carteras(calendario_df, asignacion_df)
        self._process_enhanced_pagos(pagos_df)
        self._process_kpis_por_cartera(kpis_campania)
        
        # Análisis avanzados
        self._calculate_efectividad_metrics()
        self._analyze_temporal_patterns()
        self._benchmark_performance()
        self._generate_enhanced_recommendations()
        self._build_executive_summary()
        
        logger.info("✅ Datos cargados y análisis completado")
    
    def _process_enhanced_gestiones(self, gestiones_df: pd.DataFrame) -> None:
        """Procesamiento mejorado de gestiones con análisis comparativo"""
        if gestiones_df.empty:
            logger.warning("No hay datos de gestiones para procesar")
            return
        
        # Separar por canal
        call_data = gestiones_df[gestiones_df['canal'] == 'CALL'].copy()
        voicebot_data = gestiones_df[gestiones_df['canal'] == 'VOICEBOT'].copy()
        
        # Análisis CALL (mejorado)
        call_analysis = self._analyze_channel_performance(call_data, 'CALL')
        
        # Análisis VOICEBOT (mejorado)
        voicebot_analysis = self._analyze_channel_performance(voicebot_data, 'VOICEBOT')
        
        # Análisis comparativo
        comparativo = self._create_channel_comparison(call_analysis, voicebot_analysis)
        
        # Guardar análisis
        self.data['analisis_canales'] = {
            'call': call_analysis,
            'voicebot': voicebot_analysis,
            'comparativo': comparativo
        }
        
        # Evolución diaria mejorada
        self._process_daily_evolution(gestiones_df)
    
    def _analyze_channel_performance(self, channel_data: pd.DataFrame, channel_name: str) -> Dict:
        """Análisis detallado de rendimiento por canal"""
        if channel_data.empty:
            return self._empty_channel_analysis()
        
        # Métricas básicas
        total_gestiones = len(channel_data)
        contactos_efectivos = len(channel_data[channel_data['contactabilidad'] == 'CONTACTO_EFECTIVO'])
        contactos_no_efectivos = len(channel_data[channel_data['contactabilidad'] == 'CONTACTO_NO_EFECTIVO'])
        no_contactos = len(channel_data[channel_data['contactabilidad'] == 'NO_CONTACTO'])
        compromisos = len(channel_data[channel_data['es_pdp'] == 'SI'])
        
        # Métricas financieras
        monto_compromisos = channel_data['monto_compromiso'].sum()
        ticket_promedio = monto_compromisos / max(compromisos, 1)
        
        # Métricas de eficiencia
        clientes_unicos = channel_data['cod_luna'].nunique()
        intensidad_gestion = total_gestiones / max(clientes_unicos, 1)
        
        # Duración promedio (solo para CALL)
        duracion_promedio = 0
        if channel_name == 'CALL' and 'duracion' in channel_data.columns:
            duracion_promedio = channel_data['duracion'].mean()
        
        # Tasas calculadas
        tasa_contactabilidad = round(contactos_efectivos / max(total_gestiones, 1) * 100, 2)
        tasa_compromiso = round(compromisos / max(contactos_efectivos, 1) * 100, 2)
        tasa_no_contacto = round(no_contactos / max(total_gestiones, 1) * 100, 2)
        
        # Análisis por tipo de cartera
        cartera_performance = {}
        if 'tipo_cartera' in channel_data.columns:
            for cartera in channel_data['tipo_cartera'].unique():
                cartera_data = channel_data[channel_data['tipo_cartera'] == cartera]
                cartera_contactos = len(cartera_data[cartera_data['contactabilidad'] == 'CONTACTO_EFECTIVO'])
                cartera_total = len(cartera_data)
                
                cartera_performance[cartera] = {
                    'gestiones': cartera_total,
                    'contactos_efectivos': cartera_contactos,
                    'tasa_contactabilidad': round(cartera_contactos / max(cartera_total, 1) * 100, 2),
                    'clientes_unicos': cartera_data['cod_luna'].nunique()
                }
        
        # Evaluación vs benchmarks
        benchmark_contactabilidad = self.BENCHMARKS[f'tasa_contactabilidad_{channel_name.lower()}']
        benchmark_compromiso = self.BENCHMARKS['tasa_compromiso']
        
        cumple_benchmark_contactabilidad = tasa_contactabilidad >= benchmark_contactabilidad
        cumple_benchmark_compromiso = tasa_compromiso >= benchmark_compromiso
        
        return {
            'canal': channel_name,
            'metricas_basicas': {
                'total_gestiones': total_gestiones,
                'contactos_efectivos': contactos_efectivos,
                'contactos_no_efectivos': contactos_no_efectivos,
                'no_contactos': no_contactos,
                'compromisos': compromisos,
                'clientes_unicos': clientes_unicos
            },
            'metricas_financieras': {
                'monto_compromisos': monto_compromisos,
                'ticket_promedio': ticket_promedio
            },
            'metricas_eficiencia': {
                'tasa_contactabilidad': tasa_contactabilidad,
                'tasa_compromiso': tasa_compromiso,
                'tasa_no_contacto': tasa_no_contacto,
                'intensidad_gestion': round(intensidad_gestion, 2),
                'duracion_promedio': round(duracion_promedio, 1)
            },
            'performance_por_cartera': cartera_performance,
            'benchmark_evaluation': {
                'contactabilidad_objetivo': benchmark_contactabilidad,
                'compromiso_objetivo': benchmark_compromiso,
                'cumple_contactabilidad': cumple_benchmark_contactabilidad,
                'cumple_compromiso': cumple_benchmark_compromiso,
                'gap_contactabilidad': round(tasa_contactabilidad - benchmark_contactabilidad, 2),
                'gap_compromiso': round(tasa_compromiso - benchmark_compromiso, 2)
            }
        }
    
    def _empty_channel_analysis(self) -> Dict:
        """Retorna estructura vacía para canales sin datos"""
        return {
            'canal': 'UNKNOWN',
            'metricas_basicas': {k: 0 for k in ['total_gestiones', 'contactos_efectivos', 'contactos_no_efectivos', 'no_contactos', 'compromisos', 'clientes_unicos']},
            'metricas_financieras': {'monto_compromisos': 0, 'ticket_promedio': 0},
            'metricas_eficiencia': {k: 0 for k in ['tasa_contactabilidad', 'tasa_compromiso', 'tasa_no_contacto', 'intensidad_gestion', 'duracion_promedio']},
            'performance_por_cartera': {},
            'benchmark_evaluation': {k: 0 for k in ['contactabilidad_objetivo', 'compromiso_objetivo', 'cumple_contactabilidad', 'cumple_compromiso', 'gap_contactabilidad', 'gap_compromiso'