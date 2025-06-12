"""
REPORT GENERATOR - Telefónica del Perú
=====================================

Módulo para generar reportes semanales automatizados en Excel y PowerPoint
integrando con el sistema de gestión de cobranza existente.

Autor: Sistema Automatizado FACO Weekly
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
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, LineChart, Reference
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

class TelefonicaReportGenerator:
    """
    Generador de reportes semanales para Telefónica del Perú
    Crea archivos Excel y PowerPoint con datos de gestión de cobranza
    """
    
    # Colores corporativos Telefónica
    COLORS = {
        'telefonica_blue': '0019A5',
        'telefonica_light_blue': '5BB4E5', 
        'telefonica_green': '00A651',
        'telefonica_orange': 'FF6600',
        'telefonica_gray': '666666',
        'white': 'FFFFFF',
        'light_gray': 'F2F2F2'
    }
    
    def __init__(self, fecha_inicio: str, fecha_fin: str):
        """
        Inicializar generador de reportes
        
        Args:
            fecha_inicio: Fecha inicio período (YYYY-MM-DD)
            fecha_fin: Fecha fin período (YYYY-MM-DD)
        """
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.periodo_str = f"{fecha_inicio} a {fecha_fin}"
        self.fecha_generacion = datetime.now()
        
        # Estructura de datos que se llenará con información procesada
        self.data = {
            'resumen_ejecutivo': {},
            'canal_call': {},
            'canal_voicebot': {},
            'evolucion_diaria': [],
            'carteras_activas': [],
            'kpis_consolidados': {},
            'comparativas': {},
            'recomendaciones': []
        }
    
    def load_data_from_processing(self, 
                                gestiones_df: pd.DataFrame,
                                calendario_df: pd.DataFrame,
                                asignacion_df: pd.DataFrame,
                                pagos_df: pd.DataFrame,
                                kpis_campania: List[Dict]) -> None:
        """
        Cargar datos desde el procesamiento principal
        
        Args:
            gestiones_df: DataFrame con gestiones procesadas
            calendario_df: DataFrame con calendario de vigencias
            asignacion_df: DataFrame con resumen de asignaciones
            pagos_df: DataFrame con pagos del período
            kpis_campania: Lista de KPIs por campaña
        """
        logger.info("Cargando datos para generación de reportes")
        
        # Procesar datos de gestiones
        self._process_gestiones_data(gestiones_df)
        
        # Procesar datos de calendario y asignaciones
        self._process_calendario_data(calendario_df, asignacion_df)
        
        # Procesar datos de pagos
        self._process_pagos_data(pagos_df)
        
        # Procesar KPIs por campaña
        self._process_kpis_campania(kpis_campania)
        
        # Calcular métricas consolidadas
        self._calculate_consolidated_metrics()
        
        # Generar recomendaciones automáticas
        self._generate_recommendations()
        
        logger.info("Datos cargados y procesados exitosamente")
    
    def _process_gestiones_data(self, gestiones_df: pd.DataFrame) -> None:
        """Procesar datos de gestiones por canal"""
        if gestiones_df.empty:
            logger.warning("No hay datos de gestiones para procesar")
            return
        
        # Separar por canal
        call_data = gestiones_df[gestiones_df['canal'] == 'CALL']
        voicebot_data = gestiones_df[gestiones_df['canal'] == 'VOICEBOT']
        
        # Métricas CALL
        self.data['canal_call'] = {
            'total_gestiones': len(call_data),
            'contactos_efectivos': len(call_data[call_data['contactabilidad'] == 'CONTACTO_EFECTIVO']),
            'contactos_no_efectivos': len(call_data[call_data['contactabilidad'] == 'CONTACTO_NO_EFECTIVO']),
            'no_contactos': len(call_data[call_data['contactabilidad'] == 'NO_CONTACTO']),
            'compromisos': len(call_data[call_data['es_pdp'] == 'SI']),
            'monto_compromisos': call_data['monto_compromiso'].sum(),
            'clientes_unicos': call_data['cod_luna'].nunique(),
            'duracion_promedio': call_data['duracion'].mean() if 'duracion' in call_data.columns else 0
        }
        
        # Calcular tasas CALL
        if self.data['canal_call']['total_gestiones'] > 0:
            self.data['canal_call']['tasa_contactabilidad'] = round(
                self.data['canal_call']['contactos_efectivos'] / self.data['canal_call']['total_gestiones'] * 100, 2
            )
            if self.data['canal_call']['contactos_efectivos'] > 0:
                self.data['canal_call']['tasa_compromiso'] = round(
                    self.data['canal_call']['compromisos'] / self.data['canal_call']['contactos_efectivos'] * 100, 2
                )
        
        # Métricas VOICEBOT
        self.data['canal_voicebot'] = {
            'total_gestiones': len(voicebot_data),
            'contactos_efectivos': len(voicebot_data[voicebot_data['contactabilidad'] == 'CONTACTO_EFECTIVO']),
            'compromisos': len(voicebot_data[voicebot_data['es_pdp'] == 'SI']),
            'clientes_unicos': voicebot_data['cod_luna'].nunique()
        }
        
        # Calcular tasas VOICEBOT
        if self.data['canal_voicebot']['total_gestiones'] > 0:
            self.data['canal_voicebot']['tasa_contactabilidad'] = round(
                self.data['canal_voicebot']['contactos_efectivos'] / self.data['canal_voicebot']['total_gestiones'] * 100, 2
            )
            if self.data['canal_voicebot']['contactos_efectivos'] > 0:
                self.data['canal_voicebot']['tasa_compromiso'] = round(
                    self.data['canal_voicebot']['compromisos'] / self.data['canal_voicebot']['contactos_efectivos'] * 100, 2
                )
        
        # Evolución diaria
        gestiones_df['fecha'] = pd.to_datetime(gestiones_df['date']).dt.date
        evolucion_call = call_data.groupby('fecha').agg({
            'cod_luna': 'count',
            'contactabilidad': lambda x: (x == 'CONTACTO_EFECTIVO').sum()
        }).rename(columns={'cod_luna': 'gestiones_call', 'contactabilidad': 'contactos_call'})
        
        evolucion_voicebot = voicebot_data.groupby('fecha').agg({
            'cod_luna': 'count',
            'contactabilidad': lambda x: (x == 'CONTACTO_EFECTIVO').sum()
        }).rename(columns={'cod_luna': 'gestiones_voicebot', 'contactabilidad': 'contactos_voicebot'})
        
        # Combinar evolución diaria
        evolucion_completa = evolucion_call.join(evolucion_voicebot, how='outer').fillna(0)
        evolucion_completa['total_gestiones'] = evolucion_completa['gestiones_call'] + evolucion_completa['gestiones_voicebot']
        evolucion_completa['total_contactos'] = evolucion_completa['contactos_call'] + evolucion_completa['contactos_voicebot']
        
        self.data['evolucion_diaria'] = [
            {
                'fecha': fecha.strftime('%Y-%m-%d'),
                'call_gestiones': int(row['gestiones_call']),
                'call_contactos': int(row['contactos_call']),
                'voicebot_gestiones': int(row['gestiones_voicebot']),
                'voicebot_contactos': int(row['contactos_voicebot']),
                'total_gestiones': int(row['total_gestiones']),
                'total_contactos': int(row['total_contactos']),
                'tasa_contactabilidad': round(row['total_contactos'] / row['total_gestiones'] * 100, 2) if row['total_gestiones'] > 0 else 0
            }
            for fecha, row in evolucion_completa.iterrows()
        ]
    
    def _process_calendario_data(self, calendario_df: pd.DataFrame, asignacion_df: pd.DataFrame) -> None:
        """Procesar datos de calendario y asignaciones"""
        if not calendario_df.empty:
            self.data['carteras_activas'] = [
                {
                    'archivo': row['archivo'],
                    'tipo_cartera': row['tipo_cartera'],
                    'fecha_asignacion': row['fecha_asignacion'].strftime('%Y-%m-%d'),
                    'fecha_cierre': row['fecha_cierre'].strftime('%Y-%m-%d'),
                    'suma_lineas': row['suma_lineas'] if 'suma_lineas' in row else 0,
                    'dias_vigencia': row['dias_vigencia'] if 'dias_vigencia' in row else 0,
                    'estado': row['estado_vigencia'] if 'estado_vigencia' in row else 'ACTIVA'
                }
                for _, row in calendario_df.iterrows()
            ]
        
        if not asignacion_df.empty:
            # Agregar información de asignaciones a carteras activas
            for cartera in self.data['carteras_activas']:
                asig_data = asignacion_df[asignacion_df['archivo'] == cartera['archivo']]
                if not asig_data.empty:
                    cartera.update({
                        'clientes_asignados': int(asig_data.iloc[0]['clientes_asignados']),
                        'cuentas_asignadas': int(asig_data.iloc[0]['cuentas_asignadas'])
                    })
    
    def _process_pagos_data(self, pagos_df: pd.DataFrame) -> None:
        """Procesar datos de pagos"""
        if not pagos_df.empty:
            self.data['pagos'] = {
                'total_pagos': len(pagos_df),
                'clientes_con_pago': pagos_df['nro_documento'].nunique(),
                'monto_total': pagos_df['monto_cancelado'].sum(),
                'ticket_promedio': pagos_df['monto_cancelado'].mean(),
                'monto_min': pagos_df['monto_cancelado'].min(),
                'monto_max': pagos_df['monto_cancelado'].max()
            }
        else:
            self.data['pagos'] = {
                'total_pagos': 0,
                'clientes_con_pago': 0,
                'monto_total': 0,
                'ticket_promedio': 0,
                'monto_min': 0,
                'monto_max': 0
            }
    
    def _process_kpis_campania(self, kpis_campania: List[Dict]) -> None:
        """Procesar KPIs por campaña"""
        self.data['kpis_por_campania'] = kpis_campania
    
    def _calculate_consolidated_metrics(self) -> None:
        """Calcular métricas consolidadas"""
        call = self.data['canal_call']
        voicebot = self.data['canal_voicebot']
        
        total_gestiones = call.get('total_gestiones', 0) + voicebot.get('total_gestiones', 0)
        total_contactos = call.get('contactos_efectivos', 0) + voicebot.get('contactos_efectivos', 0)
        total_compromisos = call.get('compromisos', 0) + voicebot.get('compromisos', 0)
        
        self.data['resumen_ejecutivo'] = {
            'total_gestiones': total_gestiones,
            'total_contactos_efectivos': total_contactos,
            'total_compromisos': total_compromisos,
            'tasa_contactabilidad_global': round(total_contactos / total_gestiones * 100, 2) if total_gestiones > 0 else 0,
            'tasa_compromiso_global': round(total_compromisos / total_contactos * 100, 2) if total_contactos > 0 else 0,
            'monto_compromisos_call': call.get('monto_compromisos', 0),
            'clientes_unicos_total': call.get('clientes_unicos', 0) + voicebot.get('clientes_unicos', 0)
        }
    
    def _generate_recommendations(self) -> None:
        """Generar recomendaciones automáticas basadas en datos"""
        recomendaciones = []
        
        # Analizar contactabilidad por canal
        call_contactabilidad = self.data['canal_call'].get('tasa_contactabilidad', 0)
        voicebot_contactabilidad = self.data['canal_voicebot'].get('tasa_contactabilidad', 0)
        
        if voicebot_contactabilidad < 2.0:
            recomendaciones.append({
                'categoria': 'Optimización VOICEBOT',
                'prioridad': 'Alta',
                'descripcion': f'Mejorar scripts VOICEBOT - actual: {voicebot_contactabilidad}%, meta: 2%+',
                'accion': 'Revisar y optimizar scripts de contacto automatizado'
            })
        
        if call_contactabilidad > voicebot_contactabilidad * 3:
            recomendaciones.append({
                'categoria': 'Balanceo de Canales',
                'prioridad': 'Media',
                'descripcion': f'CALL ({call_contactabilidad}%) vs VOICEBOT ({voicebot_contactabilidad}%) - gran diferencia',
                'accion': 'Redistribuir cartera para optimizar efectividad'
            })
        
        # Analizar evolución diaria
        if self.data['evolucion_diaria']:
            contactabilidad_diaria = [dia['tasa_contactabilidad'] for dia in self.data['evolucion_diaria']]
            if max(contactabilidad_diaria) - min(contactabilidad_diaria) > 2.0:
                recomendaciones.append({
                    'categoria': 'Consistencia Operativa',
                    'prioridad': 'Media',
                    'descripcion': 'Alta variabilidad en contactabilidad diaria',
                    'accion': 'Estandarizar procesos y horarios de gestión'
                })
        
        # Analizar compromisos
        monto_compromisos = self.data['canal_call'].get('monto_compromisos', 0)
        if monto_compromisos > 100000:
            recomendaciones.append({
                'categoria': 'Seguimiento Compromisos',
                'prioridad': 'Alta',
                'descripcion': f'${monto_compromisos:,.0f} en compromisos requiere seguimiento intensivo',
                'accion': 'Implementar sistema de tracking de cumplimiento'
            })
        
        self.data['recomendaciones'] = recomendaciones
    
    def generate_excel_report(self, output_path: str = None) -> str:
        """
        Generar reporte Excel completo
        
        Args:
            output_path: Ruta del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo Excel generado
        """
        if output_path is None:
            timestamp = self.fecha_generacion.strftime('%Y%m%d_%H%M%S')
            output_path = f"Informe_Semanal_Telefonica_{timestamp}.xlsx"
        
        logger.info(f"Generando reporte Excel: {output_path}")
        
        # Crear workbook
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remover hoja por defecto
        
        # Generar hojas
        self._create_excel_resumen_ejecutivo(wb)
        self._create_excel_analisis_canales(wb)
        self._create_excel_evolucion_diaria(wb)
        self._create_excel_carteras_activas(wb)
        self._create_excel_kpis_campanias(wb)
        self._create_excel_recomendaciones(wb)
        
        # Guardar archivo
        wb.save(output_path)
        logger.info(f"Reporte Excel generado exitosamente: {output_path}")
        
        return output_path
    
    def _create_excel_resumen_ejecutivo(self, wb: openpyxl.Workbook) -> None:
        """Crear hoja de resumen ejecutivo"""
        ws = wb.create_sheet("Resumen Ejecutivo")
        
        # Título principal
        ws['A1'] = "INFORME SEMANAL DE GESTIÓN DE COBRANZA"
        ws['A2'] = f"Telefónica del Perú - Período: {self.periodo_str}"
        ws['A3'] = f"Generado: {self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}"
        
        # Formatear títulos
        for row in range(1, 4):
            cell = ws[f'A{row}']
            cell.font = Font(bold=True, size=14 if row == 1 else 12, color=self.COLORS['white'])
            cell.fill = PatternFill(start_color=self.COLORS['telefonica_blue'], 
                                  end_color=self.COLORS['telefonica_blue'], fill_type="solid")
            ws.merge_cells(f'A{row}:D{row}')
        
        # Datos principales
        resumen = self.data['resumen_ejecutivo']
        data_rows = [
            ['INDICADOR CLAVE', 'VALOR', 'MÉTRICA', 'OBSERVACIONES'],
            ['Total Gestiones', f"{resumen.get('total_gestiones', 0):,}", '100%', 'CALL + VOICEBOT'],
            ['Contactos Efectivos', f"{resumen.get('total_contactos_efectivos', 0):,}", 
             f"{resumen.get('tasa_contactabilidad_global', 0)}%", 'Tasa de contactabilidad global'],
            ['Compromisos Obtenidos', f"{resumen.get('total_compromisos', 0):,}", 
             f"{resumen.get('tasa_compromiso_global', 0)}%", 'De contactos efectivos'],
            ['Monto Compromisos CALL', f"${resumen.get('monto_compromisos_call', 0):,.0f}", '-', 
             f"Promedio: ${resumen.get('monto_compromisos_call', 0) / max(resumen.get('total_compromisos', 1), 1):.0f}"],
            ['Clientes Únicos', f"{resumen.get('clientes_unicos_total', 0):,}", '-', 'Total gestionados'],
        ]
        
        # Agregar datos de pagos si están disponibles
        if 'pagos' in self.data:
            pagos = self.data['pagos']
            data_rows.extend([
                ['Clientes con Pago', f"{pagos.get('clientes_con_pago', 0):,}", '-', 
                 f"Total: ${pagos.get('monto_total', 0):,.0f}"],
                ['Ticket Promedio Pago', f"${pagos.get('ticket_promedio', 0):.2f}", '-', 
                 f"Rango: ${pagos.get('monto_min', 0):.2f} - ${pagos.get('monto_max', 0):,.0f}"]
            ])
        
        # Escribir datos
        for i, row_data in enumerate(data_rows, start=5):
            for j, value in enumerate(row_data, start=1):
                cell = ws.cell(row=i, column=j, value=value)
                if i == 5:  # Encabezados
                    cell.font = Font(bold=True, color=self.COLORS['white'])
                    cell.fill = PatternFill(start_color=self.COLORS['telefonica_light_blue'], 
                                          end_color=self.COLORS['telefonica_light_blue'], fill_type="solid")
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 40
    
    def _create_excel_analisis_canales(self, wb: openpyxl.Workbook) -> None:
        """Crear hoja de análisis por canales"""
        ws = wb.create_sheet("Análisis por Canal")
        
        # Título
        ws['A1'] = "ANÁLISIS DETALLADO POR CANAL"
        ws['A1'].font = Font(bold=True, size=14, color=self.COLORS['white'])
        ws['A1'].fill = PatternFill(start_color=self.COLORS['telefonica_blue'], 
                                   end_color=self.COLORS['telefonica_blue'], fill_type="solid")
        ws.merge_cells('A1:C1')
        
        # Canal CALL
        call_data = self.data['canal_call']
        call_rows = [
            ['CANAL CALL', 'VALOR', 'PORCENTAJE'],
            ['Gestiones Totales', f"{call_data.get('total_gestiones', 0):,}", '-'],
            ['Contactos Efectivos', f"{call_data.get('contactos_efectivos', 0):,}", 
             f"{call_data.get('tasa_contactabilidad', 0)}%"],
            ['Contactos No Efectivos', f"{call_data.get('contactos_no_efectivos', 0):,}", '-'],
            ['No Contactos', f"{call_data.get('no_contactos', 0):,}", '-'],
            ['Compromisos', f"{call_data.get('compromisos', 0):,}", 
             f"{call_data.get('tasa_compromiso', 0)}%"],
            ['Monto Compromisos', f"${call_data.get('monto_compromisos', 0):,.0f}", '-'],
            ['Duración Promedio', f"{call_data.get('duracion_promedio', 0):.1f} seg", '-']
        ]
        
        # Escribir datos CALL
        for i, row_data in enumerate(call_rows, start=3):
            for j, value in enumerate(row_data, start=1):
                cell = ws.cell(row=i, column=j, value=value)
                if i == 3:  # Encabezado
                    cell.font = Font(bold=True, color=self.COLORS['white'])
                    cell.fill = PatternFill(start_color=self.COLORS['telefonica_green'], 
                                          end_color=self.COLORS['telefonica_green'], fill_type="solid")
        
        # Canal VOICEBOT
        voicebot_data = self.data['canal_voicebot']
        voicebot_rows = [
            ['CANAL VOICEBOT', 'VALOR', 'PORCENTAJE'],
            ['Gestiones Totales', f"{voicebot_data.get('total_gestiones', 0):,}", '-'],
            ['Contactos Efectivos', f"{voicebot_data.get('contactos_efectivos', 0):,}", 
             f"{voicebot_data.get('tasa_contactabilidad', 0)}%"],
            ['Compromisos', f"{voicebot_data.get('compromisos', 0):,}", 
             f"{voicebot_data.get('tasa_compromiso', 0)}%"],
        ]
        
        # Escribir datos VOICEBOT
        start_row = len(call_rows) + 5
        for i, row_data in enumerate(voicebot_rows, start=start_row):
            for j, value in enumerate(row_data, start=1):
                cell = ws.cell(row=i, column=j, value=value)
                if i == start_row:  # Encabezado
                    cell.font = Font(bold=True, color=self.COLORS['white'])
                    cell.fill = PatternFill(start_color=self.COLORS['telefonica_orange'], 
                                          end_color=self.COLORS['telefonica_orange'], fill_type="solid")
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
    
    def _create_excel_evolucion_diaria(self, wb: openpyxl.Workbook) -> None:
        """Crear hoja de evolución diaria"""
        ws = wb.create_sheet("Evolución Diaria")
        
        # Título
        ws['A1'] = "EVOLUCIÓN DIARIA - CONTACTOS EFECTIVOS"
        ws['A1'].font = Font(bold=True, size=14, color=self.COLORS['white'])
        ws['A1'].fill = PatternFill(start_color=self.COLORS['telefonica_blue'], 
                                   end_color=self.COLORS['telefonica_blue'], fill_type="solid")
        ws.merge_cells('A1:H1')
        
        # Encabezados
        headers = ['Fecha', 'CALL Gestiones', 'CALL Contactos', 'VOICEBOT Gestiones', 
                  'VOICEBOT Contactos', 'Total Gestiones', 'Total Contactos', 'Tasa Contactabilidad']
        
        for j, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=j, value=header)
            cell.font = Font(bold=True, color=self.COLORS['white'])
            cell.fill = PatternFill(start_color=self.COLORS['telefonica_light_blue'], 
                                   end_color=self.COLORS['telefonica_light_blue'], fill_type="solid")
        
        # Datos diarios
        for i, dia in enumerate(self.data['evolucion_diaria'], start=4):
            row_data = [
                dia['fecha'],
                dia['call_gestiones'],
                dia['call_contactos'],
                dia['voicebot_gestiones'],
                dia['voicebot_contactos'],
                dia['total_gestiones'],
                dia['total_contactos'],
                f"{dia['tasa_contactabilidad']}%"
            ]
            
            for j, value in enumerate(row_data, start=1):
                ws.cell(row=i, column=j, value=value)
        
        # Ajustar anchos
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 15
    
    def _create_excel_carteras_activas(self, wb: openpyxl.Workbook) -> None:
        """Crear hoja de carteras activas"""
        ws = wb.create_sheet("Carteras Activas")
        
        # Título
        ws['A1'] = "CARTERAS ACTIVAS - PERÍODO ANALIZADO"
        ws['A1'].font = Font(bold=True, size=14, color=self.COLORS['white'])
        ws['A1'].fill = PatternFill(start_color=self.COLORS['telefonica_blue'], 
                                   end_color=self.COLORS['telefonica_blue'], fill_type="solid")
        ws.merge_cells('A1:H1')
        
        # Encabezados
        headers = ['Archivo', 'Tipo Cartera', 'Fecha Asignación', 'Fecha Cierre', 
                  'Clientes Asignados', 'Cuentas', 'Días Vigencia', 'Estado']
        
        for j, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=j, value=header)
            cell.font = Font(bold=True, color=self.COLORS['white'])
            cell.fill = PatternFill(start_color=self.COLORS['telefonica_light_blue'], 
                                   end_color=self.COLORS['telefonica_light_blue'], fill_type="solid")
        
        # Datos de carteras
        for i, cartera in enumerate(self.data['carteras_activas'], start=4):
            row_data = [
                cartera['archivo'],
                cartera['tipo_cartera'],
                cartera['fecha_asignacion'],
                cartera['fecha_cierre'],
                cartera.get('clientes_asignados', 0),
                cartera.get('cuentas_asignadas', 0),
                cartera['dias_vigencia'],
                cartera['estado']
            ]
            
            for j, value in enumerate(row_data, start=1):
                cell = ws.cell(row=i, column=j, value=value)
                # Colorear estado
                if j == 8:  # Columna Estado
                    if value == 'ACTIVA':
                        cell.fill = PatternFill(start_color=self.COLORS['telefonica_green'], 
                                              end_color=self.COLORS['telefonica_green'], fill_type="solid")
                        cell.font = Font(color=self.COLORS['white'])
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 30
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 15
    
    def _create_excel_kpis_campanias(self, wb: openpyxl.Workbook) -> None:
        """Crear hoja de KPIs por campaña"""
        ws = wb.create_sheet("KPIs por Campaña")
        
        # Título
        ws['A1'] = "KPIS DETALLADOS POR CAMPAÑA"
        ws['A1'].font = Font(bold=True, size=14, color=self.COLORS['white'])
        ws['A1'].fill = PatternFill(start_color=self.COLORS['telefonica_blue'], 
                                   end_color=self.COLORS['telefonica_blue'], fill_type="solid")
        ws.merge_cells('A1:H1')
        
        if not self.data['kpis_por_campania']:
            ws['A3'] = "No hay datos de KPIs por campaña disponibles"
            return
        
        # Encabezados
        headers = ['Archivo', 'Total Gestiones', 'Clientes Gestionados', 'Contactos Efectivos', 
                  'PDPs', 'Monto Compromisos', 'Tasa Contactabilidad', 'Tasa PDP']
        
        for j, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=j, value=header)
            cell.font = Font(bold=True, color=self.COLORS['white'])
            cell.fill = PatternFill(start_color=self.COLORS['telefonica_light_blue'], 
                                   end_color=self.COLORS['telefonica_light_blue'], fill_type="solid")
        
        # Datos de KPIs
        for i, kpi in enumerate(self.data['kpis_por_campania'], start=4):
            row_data = [
                kpi.get('archivo', ''),
                kpi.get('total_gestiones', 0),
                kpi.get('clientes_gestionados', 0),
                kpi.get('contactos_efectivos', 0),
                kpi.get('pdps', 0),
                f"${kpi.get('monto_compromisos', 0):,.0f}",
                f"{kpi.get('tasa_contactabilidad', 0)}%",
                f"{kpi.get('tasa_pdp', 0)}%"
            ]
            
            for j, value in enumerate(row_data, start=1):
                ws.cell(row=i, column=j, value=value)
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 30
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 15
    
    def _create_excel_recomendaciones(self, wb: openpyxl.Workbook) -> None:
        """Crear hoja de recomendaciones"""
        ws = wb.create_sheet("Recomendaciones")
        
        # Título
        ws['A1'] = "RECOMENDACIONES ESTRATÉGICAS"
        ws['A1'].font = Font(bold=True, size=14, color=self.COLORS['white'])
        ws['A1'].fill = PatternFill(start_color=self.COLORS['telefonica_blue'], 
                                   end_color=self.COLORS['telefonica_blue'], fill_type="solid")
        ws.merge_cells('A1:D1')
        
        if not self.data['recomendaciones']:
            ws['A3'] = "No hay recomendaciones específicas para este período"
            return
        
        # Encabezados
        headers = ['Categoría', 'Prioridad', 'Descripción', 'Acción Recomendada']
        
        for j, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=j, value=header)
            cell.font = Font(bold=True, color=self.COLORS['white'])
            cell.fill = PatternFill(start_color=self.COLORS['telefonica_light_blue'], 
                                   end_color=self.COLORS['telefonica_light_blue'], fill_type="solid")
        
        # Datos de recomendaciones
        for i, rec in enumerate(self.data['recomendaciones'], start=4):
            row_data = [
                rec.get('categoria', ''),
                rec.get('prioridad', ''),
                rec.get('descripcion', ''),
                rec.get('accion', '')
            ]
            
            for j, value in enumerate(row_data, start=1):
                cell = ws.cell(row=i, column=j, value=value)
                # Colorear por prioridad
                if j == 2:  # Columna Prioridad
                    if value == 'Alta':
                        cell.fill = PatternFill(start_color='FF6B6B', end_color='FF6B6B', fill_type="solid")
                        cell.font = Font(color=self.COLORS['white'])
                    elif value == 'Media':
                        cell.fill = PatternFill(start_color='FFE66D', end_color='FFE66D', fill_type="solid")
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 50
    
    def generate_powerpoint_report(self, output_path: str = None) -> str:
        """
        Generar presentación PowerPoint ejecutiva
        
        Args:
            output_path: Ruta del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo PowerPoint generado
        """
        if output_path is None:
            timestamp = self.fecha_generacion.strftime('%Y%m%d_%H%M%S')
            output_path = f"Presentacion_Semanal_Telefonica_{timestamp}.pptx"
        
        logger.info(f"Generando presentación PowerPoint: {output_path}")
        
        # Crear presentación
        prs = Presentation()
        
        # Generar slides
        self._create_ppt_portada(prs)
        self._create_ppt_resumen_ejecutivo(prs)
        self._create_ppt_analisis_canales(prs)
        self._create_ppt_evolucion_temporal(prs)
        self._create_ppt_carteras_activas(prs)
        self._create_ppt_recomendaciones(prs)
        
        # Guardar presentación
        prs.save(output_path)
        logger.info(f"Presentación PowerPoint generada exitosamente: {output_path}")
        
        return output_path
    
    def _create_ppt_portada(self, prs: Presentation) -> None:
        """Crear slide de portada"""
        slide = prs.slides.add_slide(prs.slide_layouts[0])  # Title slide
        
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        
        title.text = "INFORME SEMANAL DE GESTIÓN"
        title.text_frame.paragraphs[0].font.size = Pt(32)
        title.text_frame.paragraphs[0].font.bold = True
        
        subtitle.text = f"Telefónica del Perú\n{self.periodo_str}\nSistema de Cobranza Automatizado"
        subtitle.text_frame.paragraphs[0].font.size = Pt(18)
    
    def _create_ppt_resumen_ejecutivo(self, prs: Presentation) -> None:
        """Crear slide de resumen ejecutivo"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title and content
        
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "RESUMEN EJECUTIVO"
        
        resumen = self.data['resumen_ejecutivo']
        tf = content.text_frame
        tf.text = f"• {resumen.get('total_gestiones', 0):,} gestiones totales realizadas"
        
        # Agregar párrafos adicionales
        paragraphs_data = [
            f"• {resumen.get('total_contactos_efectivos', 0):,} contactos efectivos ({resumen.get('tasa_contactabilidad_global', 0)}%)",
            f"• {resumen.get('total_compromisos', 0):,} compromisos obtenidos ({resumen.get('tasa_compromiso_global', 0)}%)",
            f"• ${resumen.get('monto_compromisos_call', 0):,.0f} en compromisos CALL",
            f"• {resumen.get('clientes_unicos_total', 0):,} clientes únicos gestionados"
        ]
        
        # Agregar información de pagos si disponible
        if 'pagos' in self.data:
            pagos = self.data['pagos']
            paragraphs_data.append(f"• ${pagos.get('monto_total', 0):,.0f} en pagos procesados")
        
        for para_text in paragraphs_data:
            p = tf.add_paragraph()
            p.text = para_text
            p.font.size = Pt(16)
    
    def _create_ppt_analisis_canales(self, prs: Presentation) -> None:
        """Crear slide de análisis por canales"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
        
        # Título
        left = Inches(0.5)
        top = Inches(0.5)
        width = Inches(9)
        height = Inches(1)
        title_box = slide.shapes.add_textbox(left, top, width, height)
        tf = title_box.text_frame
        tf.text = "ANÁLISIS POR CANAL"
        tf.paragraphs[0].font.size = Pt(28)
        tf.paragraphs[0].font.bold = True
        
        # Canal CALL
        call_data = self.data['canal_call']
        left = Inches(0.5)
        top = Inches(2)
        width = Inches(4)
        height = Inches(3.5)
        call_box = slide.shapes.add_textbox(left, top, width, height)
        tf_call = call_box.text_frame
        tf_call.text = "📞 CANAL CALL"
        tf_call.paragraphs[0].font.size = Pt(20)
        tf_call.paragraphs[0].font.bold = True
        
        call_bullets = [
            f"• {call_data.get('total_gestiones', 0):,} gestiones",
            f"• {call_data.get('tasa_contactabilidad', 0)}% contactabilidad",
            f"• {call_data.get('compromisos', 0):,} compromisos",
            f"• ${call_data.get('monto_compromisos', 0):,.0f} monto"
        ]
        
        for bullet in call_bullets:
            p = tf_call.add_paragraph()
            p.text = bullet
            p.font.size = Pt(14)
        
        # Canal VOICEBOT
        voicebot_data = self.data['canal_voicebot']
        left = Inches(5)
        top = Inches(2)
        width = Inches(4)
        height = Inches(3.5)
        vb_box = slide.shapes.add_textbox(left, top, width, height)
        tf_vb = vb_box.text_frame
        tf_vb.text = "🤖 CANAL VOICEBOT"
        tf_vb.paragraphs[0].font.size = Pt(20)
        tf_vb.paragraphs[0].font.bold = True
        
        vb_bullets = [
            f"• {voicebot_data.get('total_gestiones', 0):,} gestiones",
            f"• {voicebot_data.get('tasa_contactabilidad', 0)}% contactabilidad",
            f"• {voicebot_data.get('compromisos', 0):,} compromisos"
        ]
        
        for bullet in vb_bullets:
            p = tf_vb.add_paragraph()
            p.text = bullet
            p.font.size = Pt(14)
    
    def _create_ppt_evolucion_temporal(self, prs: Presentation) -> None:
        """Crear slide de evolución temporal"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "EVOLUCIÓN TEMPORAL"
        
        tf = content.text_frame
        tf.text = "Tendencias de Contactabilidad por Día:"
        tf.paragraphs[0].font.size = Pt(18)
        tf.paragraphs[0].font.bold = True
        
        # Encontrar mejor y peor día
        if self.data['evolucion_diaria']:
            mejor_dia = max(self.data['evolucion_diaria'], key=lambda x: x['tasa_contactabilidad'])
            peor_dia = min(self.data['evolucion_diaria'], key=lambda x: x['tasa_contactabilidad'])
            
            insights = [
                f"• Mejor día: {mejor_dia['fecha']} ({mejor_dia['tasa_contactabilidad']}% contactabilidad)",
                f"• Menor día: {peor_dia['fecha']} ({peor_dia['tasa_contactabilidad']}% contactabilidad)",
                f"• Total días analizados: {len(self.data['evolucion_diaria'])}",
                f"• Promedio contactabilidad: {sum(d['tasa_contactabilidad'] for d in self.data['evolucion_diaria']) / len(self.data['evolucion_diaria']):.1f}%"
            ]
            
            for insight in insights:
                p = tf.add_paragraph()
                p.text = insight
                p.font.size = Pt(14)
    
    def _create_ppt_carteras_activas(self, prs: Presentation) -> None:
        """Crear slide de carteras activas"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "CARTERAS ACTIVAS"
        
        tf = content.text_frame
        total_clientes = sum(c.get('clientes_asignados', 0) for c in self.data['carteras_activas'])
        tf.text = f"• {total_clientes:,} clientes asignados total"
        tf.paragraphs[0].font.size = Pt(16)
        
        # Resumen por tipo de cartera
        cartera_summary = {}
        for cartera in self.data['carteras_activas']:
            tipo = cartera['tipo_cartera']
            clientes = cartera.get('clientes_asignados', 0)
            if tipo in cartera_summary:
                cartera_summary[tipo] += clientes
            else:
                cartera_summary[tipo] = clientes
        
        for tipo, clientes in cartera_summary.items():
            p = tf.add_paragraph()
            p.text = f"• {tipo}: {clientes:,} clientes"
            p.font.size = Pt(14)
        
        # Información de vigencias
        activas = len([c for c in self.data['carteras_activas'] if c['estado'] == 'ACTIVA'])
        p = tf.add_paragraph()
        p.text = f"• {activas} carteras activas de {len(self.data['carteras_activas'])} total"
        p.font.size = Pt(14)
    
    def _create_ppt_recomendaciones(self, prs: Presentation) -> None:
        """Crear slide de recomendaciones"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "RECOMENDACIONES ESTRATÉGICAS"
        
        tf = content.text_frame
        
        if not self.data['recomendaciones']:
            tf.text = "• No hay recomendaciones específicas para este período"
            tf.paragraphs[0].font.size = Pt(16)
        else:
            # Tomar las 5 recomendaciones más importantes
            top_recommendations = self.data['recomendaciones'][:5]
            
            for i, rec in enumerate(top_recommendations):
                if i == 0:
                    tf.text = f"• {rec['descripcion']}"
                    tf.paragraphs[0].font.size = Pt(14)
                else:
                    p = tf.add_paragraph()
                    p.text = f"• {rec['descripcion']}"
                    p.font.size = Pt(14)
        
        # Agregar recomendaciones generales si no hay específicas
        if not self.data['recomendaciones']:
            general_recs = [
                "• Mantener monitoreo continuo de KPIs",
                "• Optimizar distribución de cartera entre canales",
                "• Implementar mejoras continuas en procesos"
            ]
            
            for rec in general_recs:
                p = tf.add_paragraph()
                p.text = rec
                p.font.size = Pt(14)
    
    def generate_complete_report(self, output_dir: str = None) -> Tuple[str, str]:
        """
        Generar reporte completo (Excel + PowerPoint)
        
        Args:
            output_dir: Directorio de salida (opcional)
            
        Returns:
            Tupla con rutas de archivos (excel_path, ppt_path)
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        
        timestamp = self.fecha_generacion.strftime('%Y%m%d_%H%M%S')
        
        excel_path = os.path.join(output_dir, f"Informe_Semanal_Telefonica_{timestamp}.xlsx")
        ppt_path = os.path.join(output_dir, f"Presentacion_Semanal_Telefonica_{timestamp}.pptx")
        
        # Generar ambos reportes
        excel_file = self.generate_excel_report(excel_path)
        ppt_file = self.generate_powerpoint_report(ppt_path)
        
        logger.info(f"Reportes completos generados en: {output_dir}")
        
        return excel_file, ppt_file
