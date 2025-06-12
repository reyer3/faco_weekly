#!/usr/bin/env python3
"""
SCRIPT DE CONFIGURACIÓN AUTOMATIZADA - FACO Weekly
================================================

Script para configurar automáticamente el sistema FACO Weekly
con generación de reportes Excel y PowerPoint.

Uso:
    python setup.py [--mode MODO] [--skip-deps]

Modos:
    development - Configuración para desarrollo local
    production  - Configuración para producción  
    testing     - Configuración para pruebas
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
import shutil
from datetime import datetime

class FacoWeeklySetup:
    """Configurador automático del sistema FACO Weekly"""
    
    def __init__(self, mode="development"):
        self.mode = mode
        self.project_root = Path(__file__).parent
        self.config = self._load_config()
        
    def _load_config(self):
        """Cargar configuración según el modo"""
        configs = {
            "development": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": True,
                "log_level": "info",
                "workers": 1
            },
            "production": {
                "host": "0.0.0.0", 
                "port": 8000,
                "reload": False,
                "log_level": "warning",
                "workers": 4
            },
            "testing": {
                "host": "127.0.0.1",
                "port": 8001,
                "reload": True,
                "log_level": "debug",
                "workers": 1
            }
        }
        return configs.get(self.mode, configs["development"])
    
    def check_python_version(self):
        """Verificar versión de Python"""
        print("🐍 Verificando versión de Python...")
        
        if sys.version_info < (3, 8):
            print("❌ Error: Se requiere Python 3.8 o superior")
            print(f"   Versión actual: {sys.version}")
            return False
        
        print(f"✅ Python {sys.version.split()[0]} - Compatible")
        return True
    
    def install_dependencies(self, skip=False):
        """Instalar dependencias del proyecto"""
        if skip:
            print("⏭️ Saltando instalación de dependencias")
            return True
        
        print("📦 Instalando dependencias...")
        
        try:
            # Verificar si pip está disponible
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            
            # Instalar requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error instalando dependencias: {result.stderr}")
                return False
            
            print("✅ Dependencias instaladas correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en instalación: {str(e)}")
            return False
    
    def setup_environment(self):
        """Configurar variables de entorno"""
        print("🔧 Configurando variables de entorno...")
        
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"
        
        if not env_example.exists():
            print("⚠️ Archivo .env.example no encontrado")
            return False
        
        # Copiar .env.example a .env si no existe
        if not env_file.exists():
            shutil.copy(env_example, env_file)
            print("✅ Archivo .env creado desde .env.example")
        else:
            print("ℹ️ Archivo .env ya existe")
        
        # Verificar variables críticas
        env_vars = self._read_env_file(env_file)
        missing_vars = []
        
        critical_vars = [
            "BIGQUERY_PROJECT_ID",
            "BIGQUERY_DATASET"
        ]
        
        for var in critical_vars:
            if var not in env_vars or not env_vars[var]:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Variables faltantes en .env: {', '.join(missing_vars)}")
            print("   Por favor, configura estas variables antes de continuar")
        
        # Verificar credenciales Google Cloud
        google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds:
            print("⚠️ GOOGLE_APPLICATION_CREDENTIALS no configurado")
            print("   Ejecuta: export GOOGLE_APPLICATION_CREDENTIALS='path/to/key.json'")
        elif not os.path.exists(google_creds):
            print(f"⚠️ Archivo de credenciales no encontrado: {google_creds}")
        else:
            print("✅ Credenciales Google Cloud configuradas")
        
        return True
    
    def _read_env_file(self, env_file):
        """Leer archivo .env"""
        env_vars = {}
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value.strip('"\'')
        except Exception as e:
            print(f"Error leyendo .env: {e}")
        
        return env_vars
    
    def setup_directories(self):
        """Crear directorios necesarios"""
        print("📁 Configurando directorios...")
        
        directories = [
            "outputs",
            "logs", 
            "temp",
            "docs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            print(f"   ✅ {directory}/")
        
        return True
    
    def test_bigquery_connection(self):
        """Probar conexión con BigQuery"""
        print("🔌 Probando conexión con BigQuery...")
        
        try:
            from google.cloud import bigquery
            
            client = bigquery.Client(project="mibot-222814")
            
            # Query simple de prueba
            query = "SELECT 1 as test"
            result = client.query(query).result()
            
            # Verificar que la consulta funcione
            for row in result:
                if row.test == 1:
                    print("✅ Conexión BigQuery exitosa")
                    return True
            
            print("❌ Error en query de prueba BigQuery")
            return False
            
        except Exception as e:
            print(f"❌ Error conectando BigQuery: {str(e)}")
            print("   Verifica las credenciales y permisos")
            return False
    
    def test_api_startup(self):
        """Probar que la API puede iniciarse"""
        print("🚀 Probando inicio de API...")
        
        try:
            # Importar módulos principales
            import main
            from report_generator import TelefonicaReportGenerator
            
            print("✅ Módulos principales importados correctamente")
            
            # Verificar que FastAPI se puede crear
            app = main.app
            if app:
                print("✅ FastAPI app creada correctamente")
                return True
            else:
                print("❌ Error creando FastAPI app")
                return False
                
        except Exception as e:
            print(f"❌ Error en startup de API: {str(e)}")
            return False
    
    def create_startup_script(self):
        """Crear script de inicio personalizado"""
        print("📝 Creando script de inicio...")
        
        script_content = f"""#!/bin/bash
# Script de inicio generado automáticamente para FACO Weekly
# Modo: {self.mode}
# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e

echo "🚀 Iniciando FACO Weekly v2.2.0 - Modo: {self.mode}"

# Verificar variables de entorno
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️ GOOGLE_APPLICATION_CREDENTIALS no configurado"
    echo "   Ejecuta: export GOOGLE_APPLICATION_CREDENTIALS='path/to/key.json'"
    exit 1
fi

# Verificar que el archivo de credenciales existe
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Archivo de credenciales no encontrado: $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

# Crear directorios si no existen
mkdir -p outputs logs temp

# Iniciar servidor
echo "🔧 Configuración:"
echo "   Host: {self.config['host']}"
echo "   Puerto: {self.config['port']}"
echo "   Reload: {self.config['reload']}"
echo "   Workers: {self.config['workers']}"
echo "   Log Level: {self.config['log_level']}"

echo ""
echo "📊 Endpoints principales:"
echo "   Health: http://{self.config['host']}:{self.config['port']}/health"
echo "   Docs: http://{self.config['host']}:{self.config['port']}/docs"
echo "   Reportes: http://{self.config['host']}:{self.config['port']}/generate-reports"

echo ""
echo "🎯 Iniciando servidor..."

uvicorn main:app \\
    --host {self.config['host']} \\
    --port {self.config['port']} \\
    {"--reload" if self.config['reload'] else ""} \\
    --log-level {self.config['log_level']} \\
    --workers {self.config['workers']}
"""
        
        script_path = self.project_root / f"start_{self.mode}.sh"
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Hacer ejecutable
        os.chmod(script_path, 0o755)
        
        print(f"✅ Script creado: {script_path}")
        return True
    
    def create_test_config(self):
        """Crear configuración de pruebas"""
        print("🧪 Configurando entorno de pruebas...")
        
        test_config = {
            "base_url": f"http://{self.config['host']}:{self.config['port']}",
            "test_period": {
                "fecha_inicio": "2025-06-01",
                "fecha_fin": "2025-06-12"
            },
            "formatos": ["excel", "powerpoint", "ambos"],
            "timeout": 300,
            "output_dir": "outputs"
        }
        
        config_path = self.project_root / "test_config.json"
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        print(f"✅ Configuración de pruebas: {config_path}")
        return True
    
    def show_next_steps(self):
        """Mostrar próximos pasos"""
        print("\n" + "="*60)
        print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("="*60)
        
        print(f"\n🚀 Para iniciar el servidor ({self.mode}):")
        print(f"   ./start_{self.mode}.sh")
        print(f"   # o manualmente:")
        print(f"   uvicorn main:app --host {self.config['host']} --port {self.config['port']}")
        
        print(f"\n🔍 URLs importantes:")
        print(f"   • Health Check: http://{self.config['host']}:{self.config['port']}/health")
        print(f"   • Documentación: http://{self.config['host']}:{self.config['port']}/docs")
        print(f"   • Generación de Reportes: http://{self.config['host']}:{self.config['port']}/generate-reports")
        
        print(f"\n🧪 Probar el sistema:")
        print(f"   python test_reports.py --url http://{self.config['host']}:{self.config['port']} --periodo semanal")
        
        print(f"\n📊 Generar reporte de ejemplo:")
        print(f"""   curl -X POST "http://{self.config['host']}:{self.config['port']}/generate-reports" \\
     -d "fecha_inicio=2025-06-01" \\
     -d "fecha_fin=2025-06-12" \\
     -d "formato=ambos\"""")
        
        print(f"\n📚 Documentación:")
        print(f"   • README.md - Guía principal")
        print(f"   • docs/AUTOMATED_REPORTS.md - Reportes automatizados")
        
        print(f"\n⚠️ Recordatorios:")
        if self.mode == "production":
            print(f"   • Configurar firewall para puerto {self.config['port']}")
            print(f"   • Configurar SSL/HTTPS si es necesario")
            print(f"   • Configurar logs rotation")
            print(f"   • Configurar monitoreo de sistema")
        
        print(f"   • Configurar GOOGLE_APPLICATION_CREDENTIALS si no está hecho")
        print(f"   • Revisar variables en .env")
        print(f"   • Configurar backup automático de reportes")
        
        print(f"\n🎯 ¡Sistema listo para generar reportes automatizados!")
    
    def run_setup(self, skip_deps=False):
        """Ejecutar configuración completa"""
        print("🔧 CONFIGURACIÓN AUTOMATIZADA FACO WEEKLY v2.2.0")
        print("="*50)
        print(f"📋 Modo: {self.mode}")
        print(f"📁 Directorio: {self.project_root}")
        print("")
        
        steps = [
            ("Verificar Python", self.check_python_version),
            ("Instalar dependencias", lambda: self.install_dependencies(skip_deps)),
            ("Configurar entorno", self.setup_environment),
            ("Crear directorios", self.setup_directories),
            ("Probar BigQuery", self.test_bigquery_connection),
            ("Probar API", self.test_api_startup),
            ("Crear script inicio", self.create_startup_script),
            ("Configurar pruebas", self.create_test_config)
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except Exception as e:
                print(f"❌ Error en {step_name}: {str(e)}")
                failed_steps.append(step_name)
        
        print("\n" + "="*50)
        
        if failed_steps:
            print(f"⚠️ Pasos con problemas: {', '.join(failed_steps)}")
            print("   Revisa los errores y vuelve a ejecutar el setup")
            return False
        else:
            print("✅ Todos los pasos completados exitosamente")
            self.show_next_steps()
            return True

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Configuración automatizada de FACO Weekly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python setup.py --mode development
    python setup.py --mode production --skip-deps
    python setup.py --mode testing
        """
    )
    
    parser.add_argument('--mode', choices=['development', 'production', 'testing'],
                       default='development', help='Modo de configuración')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Saltar instalación de dependencias')
    
    args = parser.parse_args()
    
    # Ejecutar configuración
    setup = FacoWeeklySetup(mode=args.mode)
    success = setup.run_setup(skip_deps=args.skip_deps)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
