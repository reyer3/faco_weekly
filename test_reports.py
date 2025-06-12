#!/usr/bin/env python3
"""
SCRIPT DE PRUEBA - Generación Automática de Reportes
===================================================

Script para probar y demostrar la funcionalidad de generación automática
de reportes Excel y PowerPoint del sistema FACO Weekly.

Uso:
    python test_reports.py [--periodo PERIODO] [--formato FORMATO]

Ejemplos:
    python test_reports.py --periodo semanal --formato ambos
    python test_reports.py --periodo custom --inicio 2025-06-01 --fin 2025-06-12
    python test_reports.py --formato excel
"""

import requests
import json
import argparse
import sys
import os
from datetime import datetime, timedelta
import time
from typing import Optional

class FacoReportsTester:
    """Tester para el sistema de reportes FACO Weekly"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def check_health(self) -> bool:
        """Verificar que el sistema esté funcionando"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Sistema FACO Weekly funcionando correctamente")
                print(f"   📊 Versión: {health_data.get('version', 'Unknown')}")
                print(f"   🔌 BigQuery: {health_data.get('bigquery', 'Unknown')}")
                print(f"   📋 Campañas en calendario: {health_data.get('calendario_vigencias', 0)}")
                return True
            else:
                print(f"❌ Error en health check: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ No se puede conectar al sistema: {str(e)}")
            print("   💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:8000")
            return False
    
    def get_vigencias_status(self) -> dict:
        """Obtener estado de vigencias del calendario"""
        try:
            response = self.session.get(f"{self.base_url}/vigencias-status")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Error obteniendo vigencias: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error consultando vigencias: {str(e)}")
            return {}
    
    def generate_reports(self, 
                        fecha_inicio: str, 
                        fecha_fin: str, 
                        formato: str = "ambos",
                        incluir_cerradas: bool = False) -> dict:
        """Generar reportes usando la API"""
        
        print(f"🚀 Iniciando generación de reportes...")
        print(f"   📅 Período: {fecha_inicio} a {fecha_fin}")
        print(f"   📊 Formato: {formato}")
        print(f"   🗂️ Incluir cerradas: {incluir_cerradas}")
        
        payload = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "formato": formato,
            "incluir_cerradas": incluir_cerradas
        }
        
        try:
            # Enviar solicitud
            print("\n⏳ Procesando datos y generando archivos...")
            start_time = time.time()
            
            response = self.session.post(
                f"{self.base_url}/generate-reports",
                params=payload
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Reportes generados exitosamente en {elapsed_time:.2f} segundos")
                return result
            else:
                print(f"❌ Error generando reportes: {response.status_code}")
                print(f"   📄 Detalle: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error en solicitud: {str(e)}")
            return {}
    
    def download_file(self, download_url: str, filename: str, tipo: str) -> bool:
        """Descargar archivo generado"""
        try:
            print(f"📥 Descargando {tipo}: {filename}")
            
            response = self.session.get(f"{self.base_url}{download_url}")
            
            if response.status_code == 200:
                # Guardar archivo localmente
                output_path = os.path.join("outputs", filename)
                os.makedirs("outputs", exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
                print(f"✅ {tipo} descargado: {output_path} ({file_size:.2f} MB)")
                return True
            else:
                print(f"❌ Error descargando {tipo}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error descargando {filename}: {str(e)}")
            return False
    
    def print_report_summary(self, result: dict) -> None:
        """Imprimir resumen del reporte generado"""
        if not result:
            return
        
        print("\n" + "="*60)
        print("📊 RESUMEN DEL REPORTE GENERADO")
        print("="*60)
        
        # Información general
        print(f"📅 Período: {result.get('periodo', 'N/A')}")
        print(f"🕐 Timestamp: {result.get('timestamp', 'N/A')}")
        print(f"📋 Formato: {result.get('formato_solicitado', 'N/A')}")
        
        # Datos procesados
        datos = result.get('datos_procesados', {})
        print(f"\n📈 DATOS PROCESADOS:")
        print(f"   • Campañas: {datos.get('campañas', 0):,}")
        print(f"   • Gestiones: {datos.get('gestiones', 0):,}")
        print(f"   • Pagos: {datos.get('pagos', 0):,}")
        print(f"   • KPIs por campaña: {datos.get('kpis_campania', 0)}")
        
        # Resumen ejecutivo
        resumen = result.get('resumen_ejecutivo', {})
        if resumen:
            print(f"\n🎯 RESUMEN EJECUTIVO:")
            print(f"   • Total gestiones: {resumen.get('total_gestiones', 0):,}")
            print(f"   • Contactos efectivos: {resumen.get('contactos_efectivos', 0):,}")
            print(f"   • Tasa contactabilidad: {resumen.get('tasa_contactabilidad', 0):.2f}%")
            print(f"   • Compromisos: {resumen.get('compromisos', 0):,}")
            print(f"   • Monto compromisos: ${resumen.get('monto_compromisos', 0):,.0f}")
        
        # Archivos generados
        archivos = result.get('archivos_generados', {})
        if archivos:
            print(f"\n📁 ARCHIVOS GENERADOS:")
            for tipo, info in archivos.items():
                print(f"   • {tipo.upper()}: {info['filename']} ({info['size_mb']} MB)")
        
        # Enlaces de descarga
        enlaces = result.get('enlaces_descarga', {})
        if enlaces:
            print(f"\n🔗 ENLACES DE DESCARGA:")
            for tipo, url in enlaces.items():
                print(f"   • {tipo.upper()}: {url}")
    
    def run_test_suite(self, 
                      fecha_inicio: Optional[str] = None,
                      fecha_fin: Optional[str] = None,
                      formato: str = "ambos") -> bool:
        """Ejecutar suite completa de pruebas"""
        
        print("🧪 INICIANDO SUITE DE PRUEBAS FACO WEEKLY")
        print("="*50)
        
        # 1. Verificar salud del sistema
        if not self.check_health():
            return False
        
        # 2. Obtener estado de vigencias
        print(f"\n📋 Verificando estado de vigencias...")
        vigencias = self.get_vigencias_status()
        if vigencias:
            resumen = vigencias.get('resumen', {})
            print(f"   • Total campañas: {resumen.get('total_campañas', 0)}")
            print(f"   • Vigencias activas: {resumen.get('vigencias_activas', 0)}")
            print(f"   • Vigencias cerradas: {resumen.get('vigencias_cerradas', 0)}")
        
        # 3. Definir período de prueba si no se proporciona
        if not fecha_inicio or not fecha_fin:
            # Usar última semana como período por defecto
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            fecha_inicio = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            print(f"\n📅 Usando período por defecto: {fecha_inicio} a {fecha_fin}")
        
        # 4. Generar reportes
        result = self.generate_reports(fecha_inicio, fecha_fin, formato)
        
        if not result:
            print("❌ Error generando reportes")
            return False
        
        # 5. Mostrar resumen
        self.print_report_summary(result)
        
        # 6. Descargar archivos
        enlaces = result.get('enlaces_descarga', {})
        archivos = result.get('archivos_generados', {})
        
        success_downloads = 0
        total_downloads = len(enlaces)
        
        if enlaces:
            print(f"\n📥 Descargando {total_downloads} archivo(s)...")
            
            for tipo, url in enlaces.items():
                filename = archivos[tipo]['filename']
                if self.download_file(url, filename, tipo):
                    success_downloads += 1
        
        # 7. Resumen final
        print(f"\n🎉 PRUEBAS COMPLETADAS")
        print(f"   ✅ Archivos descargados: {success_downloads}/{total_downloads}")
        print(f"   📁 Ubicación: ./outputs/")
        
        if success_downloads == total_downloads:
            print(f"   🎯 ¡Todas las pruebas pasaron exitosamente!")
            return True
        else:
            print(f"   ⚠️ Algunas pruebas fallaron")
            return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Script de prueba para generación de reportes FACO Weekly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
    python test_reports.py --periodo semanal
    python test_reports.py --inicio 2025-06-01 --fin 2025-06-12 --formato excel
    python test_reports.py --url http://prod-server:8000 --formato powerpoint
        """
    )
    
    parser.add_argument('--url', default='http://localhost:8000',
                       help='URL base del servidor FACO Weekly')
    parser.add_argument('--periodo', choices=['semanal', 'custom'], default='custom',
                       help='Tipo de período (semanal usa últimos 10 días)')
    parser.add_argument('--inicio', type=str,
                       help='Fecha inicio período (YYYY-MM-DD)')
    parser.add_argument('--fin', type=str,
                       help='Fecha fin período (YYYY-MM-DD)')
    parser.add_argument('--formato', choices=['excel', 'powerpoint', 'ambos'], 
                       default='ambos', help='Formato de reporte a generar')
    parser.add_argument('--incluir-cerradas', action='store_true',
                       help='Incluir campañas cerradas')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    # Configurar fechas según período
    if args.periodo == 'semanal':
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        fecha_inicio = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    else:
        fecha_inicio = args.inicio
        fecha_fin = args.fin
        
        if not fecha_inicio or not fecha_fin:
            print("❌ Para período 'custom' debes especificar --inicio y --fin")
            sys.exit(1)
    
    # Inicializar tester
    tester = FacoReportsTester(base_url=args.url)
    
    # Ejecutar pruebas
    success = tester.run_test_suite(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        formato=args.formato
    )
    
    # Resultado final
    if success:
        print("\n🎊 ¡Éxito! El sistema de reportes funciona correctamente")
        sys.exit(0)
    else:
        print("\n💥 Error: Algunas pruebas fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main()
