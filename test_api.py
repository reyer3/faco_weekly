#!/usr/bin/env python3
"""
Test Script para FACO Weekly API
================================

Script simple para probar la funcionalidad del sistema.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuración
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test de conectividad y salud del sistema"""
    print("🔍 Verificando estado del sistema...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sistema: {data['status']}")
            print(f"📊 BigQuery: {data['bigquery']}")
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

def test_api_info():
    """Test de información general del API"""
    print("\nℹ️ Obteniendo información del API...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📡 {data['message']}")
            print(f"🔢 Versión: {data['version']}")
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

def test_process_weekly(fecha_inicio=None, fecha_fin=None):
    """Test de procesamiento semanal"""
    print("\n📊 Probando procesamiento semanal...")
    
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
            f"{API_BASE_URL}/process-weekly",
            json=payload,
            timeout=120  # 2 minutos para procesamiento
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Procesamiento exitoso!")
            print(f"📋 Estado: {data['status']}")
            
            # Mostrar estadísticas del calendario
            calendario = data.get('calendario', {})
            print(f"📅 Campañas activas: {calendario.get('campañas_activas', 0)}")
            print(f"📁 Archivos procesados: {calendario.get('archivos_procesados', 0)}")
            
            # Mostrar datos procesados
            datos = data.get('datos_procesados', {})
            print(f"👥 Asignaciones: {datos.get('asignaciones', 0):,}")
            print(f"🎯 Universo gestionable: {datos.get('universo_gestionable', 0):,}")
            print(f"📞 Gestiones: {datos.get('gestiones', 0):,}")
            print(f"💰 Pagos: {datos.get('pagos', 0):,}")
            print(f"🔗 Atribuciones: {datos.get('atribuciones', 0):,}")
            
            # Mostrar KPIs
            metricas = data.get('metricas', {})
            if 'kpis' in metricas:
                kpis = metricas['kpis']
                print(f"📈 Contactabilidad: {kpis.get('tasa_contactabilidad', 0)}%")
                print(f"🎯 Atribución: {kpis.get('tasa_atribucion', 0)}%")
                print(f"⚡ Intensidad: {kpis.get('intensidad_gestion', 0)}")
                print(f"💵 Ticket promedio: S/ {kpis.get('ticket_promedio_pago', 0):,.2f}")
            
            # Mostrar top agentes
            top_agentes = data.get('top_agentes', [])
            if top_agentes:
                print(f"\n🏆 Top {len(top_agentes)} Agentes:")
                for i, agente in enumerate(top_agentes, 1):
                    print(f"   {i}. {agente.get('ejecutivo', 'N/A')} - "
                          f"Gestiones: {agente.get('total_gestiones', 0)}, "
                          f"Contactabilidad: {agente.get('tasa_contactabilidad', 0)}%")
            
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
        print("⏰ Timeout: El procesamiento tomó más de 2 minutos")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Ejecuta todos los tests en secuencia"""
    print("🚀 INICIANDO TESTS FACO WEEKLY")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Tests abortados: Sistema no disponible")
        return False
    
    # Test 2: Info del API
    if not test_api_info():
        print("\n⚠️ Advertencia: No se pudo obtener info del API")
    
    # Test 3: Procesamiento semanal
    print("\n" + "=" * 50)
    if not test_process_weekly():
        print("\n❌ Test de procesamiento falló")
        return False
    
    print("\n" + "=" * 50)
    print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
    return True

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "health":
            test_health()
        elif sys.argv[1] == "info":
            test_api_info()
        elif sys.argv[1] == "process":
            # Permitir fechas customizadas
            fecha_inicio = sys.argv[2] if len(sys.argv) > 2 else None
            fecha_fin = sys.argv[3] if len(sys.argv) > 3 else None
            test_process_weekly(fecha_inicio, fecha_fin)
        else:
            print("Uso: python test_api.py [health|info|process] [fecha_inicio] [fecha_fin]")
    else:
        # Ejecutar todos los tests
        run_all_tests()

if __name__ == "__main__":
    main()
