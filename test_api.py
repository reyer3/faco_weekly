#!/usr/bin/env python3
"""
Test Script Avanzado para FACO Weekly API v2.0
===============================================

Script actualizado para probar la funcionalidad avanzada con homologación.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuración
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test de conectividad y salud del sistema avanzado"""
    print("🔍 Verificando estado del sistema avanzado...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sistema: {data['status']}")
            print(f"📊 BigQuery: {data['bigquery']}")
            
            # Mostrar estado de tablas de homologación
            if 'homologacion_tables' in data:
                print("🔗 Tablas de Homologación:")
                for table, count in data['homologacion_tables'].items():
                    if isinstance(count, int):
                        print(f"   📋 {table}: {count:,} registros")
                    else:
                        print(f"   ❌ {table}: {count}")
            
            return True
        else:
            print(f"❌ Error de salud: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al API. ¿Está ejecutándose en puerto 8000?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_homologation_status():
    """Test específico del estado de homologación"""
    print("\n🔗 Verificando estado de homologación...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/homologation-status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estado: {data['status']}")
            
            print("\n📊 Tablas de Homologación:")
            for table, count in data['tablas_homologacion'].items():
                if isinstance(count, int):
                    status_icon = "✅" if count > 0 else "⚠️"
                    print(f"   {status_icon} {table}: {count:,} registros")
                else:
                    print(f"   ❌ {table}: {count}")
            
            print("\n📝 Observaciones:")
            for table, desc in data['observaciones'].items():
                print(f"   • {table}: {desc}")
            
            return True
        else:
            print(f"❌ Error verificando homologación: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_info():
    """Test de información general del API avanzado"""
    print("\nℹ️ Información del API Avanzado...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📡 {data['message']}")
            print(f"🔢 Versión: {data['version']}")
            
            print("🚀 Características:")
            for feature in data.get('features', []):
                print(f"   • {feature}")
            
            print("📋 Endpoints disponibles:")
            for endpoint, desc in data['endpoints'].items():
                print(f"   {endpoint}: {desc}")
            return True
        else:
            print(f"❌ Error obteniendo info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_advanced_processing(fecha_inicio=None, fecha_fin=None):
    """Test de procesamiento avanzado con homologación"""
    print("\n🧠 Probando procesamiento avanzado...")
    
    # Configurar fechas por defecto
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"📅 Período: {fecha_inicio} a {fecha_fin}")
    
    payload = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/process-advanced",
            json=payload,
            timeout=180  # 3 minutos para procesamiento avanzado
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Procesamiento avanzado exitoso!")
            print(f"📋 Estado: {data['status']}")
            print(f"🔢 Versión: {data['version']}")
            
            # Mostrar estado de homologación
            homolog = data.get('homologacion', {})
            if 'problemas_detectados' in homolog:
                issues = homolog['problemas_detectados']
                print(f"\n🔍 Análisis de Homologación:")
                print(f"   📊 Total gestiones: {issues.get('total_gestiones', 0):,}")
                print(f"   ❌ No homologadas: {issues.get('no_homologadas', 0)} ({issues.get('no_homologadas_pct', 0)}%)")
                print(f"   👤 Sin DNI: {issues.get('sin_dni', 0)} ({issues.get('sin_dni_pct', 0)}%)")
                print(f"   🆔 Sin identificar: {issues.get('ejecutivos_sin_identificar', 0)} ({issues.get('ejecutivos_sin_identificar_pct', 0)}%)")
                print(f"   ⚖️ Peso cero: {issues.get('peso_cero', 0)} ({issues.get('peso_cero_pct', 0)}%)")
            
            # Mostrar datos procesados
            datos = data.get('datos_procesados', {})
            print(f"\n📊 Datos Procesados:")
            print(f"   📅 Campañas calendario: {datos.get('campañas_calendario', 0)}")
            print(f"   🎯 Gestiones unificadas: {datos.get('gestiones_unificadas', 0):,}")
            print(f"   👥 Asignaciones fact: {datos.get('asignaciones_fact', 0):,}")
            print(f"   💰 Pagos: {datos.get('pagos', 0):,}")
            
            # Mostrar KPIs avanzados
            kpis = data.get('kpis_avanzados', {})
            if 'kpis_generales' in kpis:
                kpis_gen = kpis['kpis_generales']
                print(f"\n📈 KPIs Avanzados:")
                print(f"   👥 Clientes gestionados: {kpis_gen.get('clientes_gestionados', 0):,}")
                print(f"   📞 Contactabilidad efectiva: {kpis_gen.get('tasa_contactabilidad_efectiva', 0)}%")
                print(f"   🎯 Tasa PDP: {kpis_gen.get('tasa_pdp', 0)}%")
                print(f"   💰 Monto compromisos: S/ {kpis_gen.get('monto_total_compromisos', 0):,.2f}")
                print(f"   🎫 Ticket promedio: S/ {kpis_gen.get('ticket_promedio_compromiso', 0):,.2f}")
                print(f"   📊 Cobertura gestión: {kpis_gen.get('cobertura_gestion', 0)}%")
            
            # Mostrar análisis de contactabilidad
            contact_analysis = data.get('analisis_contactabilidad', {})
            if 'contactabilidad_distribucion' in contact_analysis:
                print(f"\n📊 Distribución Contactabilidad:")
                for tipo, cantidad in contact_analysis['contactabilidad_distribucion'].items():
                    print(f"   📋 {tipo}: {cantidad}")
            
            # Mostrar top ejecutivos
            ranking = data.get('ranking_ejecutivos', [])
            if ranking:
                print(f"\n🏆 Top {len(ranking)} Ejecutivos:")
                for i, exec_data in enumerate(ranking, 1):
                    print(f"   {i}. {exec_data.get('ejecutivo', 'N/A')} ({exec_data.get('canal', 'N/A')})")
                    print(f"      💼 DNI: {exec_data.get('dni_ejecutivo', 'N/A')}")
                    print(f"      📞 Gestiones: {exec_data.get('total_gestiones', 0)}")
                    print(f"      📈 Contactabilidad: {exec_data.get('tasa_contactabilidad_efectiva', 0)}%")
                    print(f"      💰 Monto: S/ {exec_data.get('monto_comprometido', 0):,.2f}")
                    print(f"      🏅 Score: {exec_data.get('productividad_score', 0)}")
                    print()
            
            # Mostrar resumen de campañas
            campaigns = data.get('resumen_campañas', [])
            if campaigns:
                print(f"📋 Resumen por Cartera:")
                for campaign in campaigns:
                    print(f"   🎯 {campaign.get('cartera', 'N/A')}: {campaign.get('clientes_asignados', 0)} asignados")
            
            return True
            
        else:
            print(f"❌ Error en procesamiento: {response.status_code}")
            try:
                error_data = response.json()
                print(f"💬 Detalle: {error_data.get('detail', 'Sin detalles')}")
            except:
                print(f"💬 Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: El procesamiento tomó más de 3 minutos")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Ejecuta todos los tests avanzados en secuencia"""
    print("🚀 INICIANDO TESTS FACO WEEKLY v2.0 (AVANZADO)")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Tests abortados: Sistema no disponible")
        return False
    
    # Test 2: Estado de homologación
    if not test_homologation_status():
        print("\n⚠️ Advertencia: Problemas con tablas de homologación")
    
    # Test 3: Info del API
    if not test_api_info():
        print("\n⚠️ Advertencia: No se pudo obtener info del API")
    
    # Test 4: Procesamiento avanzado
    print("\n" + "=" * 60)
    if not test_advanced_processing():
        print("\n❌ Test de procesamiento avanzado falló")
        return False
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS AVANZADOS COMPLETADOS EXITOSAMENTE")
    print("🎉 Sistema con homologación funcionando correctamente")
    return True

def main():
    """Función principal con opciones avanzadas"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "health":
            test_health()
        elif command == "homolog":
            test_homologation_status()
        elif command == "info":
            test_api_info()
        elif command == "advanced":
            # Permitir fechas customizadas
            fecha_inicio = sys.argv[2] if len(sys.argv) > 2 else None
            fecha_fin = sys.argv[3] if len(sys.argv) > 3 else None
            test_advanced_processing(fecha_inicio, fecha_fin)
        elif command == "full":
            run_all_tests()
        else:
            print("Uso: python test_api.py [health|homolog|info|advanced|full] [fecha_inicio] [fecha_fin]")
            print("")
            print("Comandos disponibles:")
            print("  health    - Solo health check")
            print("  homolog   - Estado de homologación")
            print("  info      - Información del API")
            print("  advanced  - Procesamiento avanzado")
            print("  full      - Todos los tests")
            print("")
            print("Ejemplos:")
            print("  python test_api.py advanced 2025-06-01 2025-06-12")
            print("  python test_api.py full")
    else:
        # Ejecutar todos los tests por defecto
        run_all_tests()

if __name__ == "__main__":
    main()
