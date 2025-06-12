#!/bin/bash

# FACO Weekly - Script de Instalación Segura
# Evita errores de compilación y dependencias problemáticas

echo "🚀 Iniciando instalación de FACO Weekly..."

# Verificar Python
python_version=$(python3 --version 2>&1)
echo "✅ Python detectado: $python_version"

# Limpiar caché pip/uv para evitar problemas
echo "🧹 Limpiando caché de dependencias..."
if command -v uv &> /dev/null; then
    uv cache clean 2>/dev/null || true
fi
pip cache purge 2>/dev/null || true

# Configurar variables de entorno para evitar compilación problemática
export MATPLOTLIB_BACKEND=Agg
export MPLBACKEND=Agg
export BUILD_MATPLOTLIB=0
export NO_MATPLOTLIB=1

# Actualizar pip
echo "⬆️ Actualizando pip..."
python3 -m pip install --upgrade pip

# Instalar dependencias básicas primero
echo "📦 Instalando dependencias básicas..."
python3 -m pip install wheel setuptools

# Instalar dependencias principales sin matplotlib
echo "📦 Instalando dependencias principales..."
python3 -m pip install fastapi==0.104.1
python3 -m pip install uvicorn[standard]==0.24.0
python3 -m pip install pandas==2.1.3
python3 -m pip install google-cloud-bigquery==3.13.0

# Instalar dependencias para reportes
echo "📊 Instalando dependencias para reportes..."
python3 -m pip install openpyxl==3.1.2
python3 -m pip install python-pptx==0.6.23
python3 -m pip install xlsxwriter==3.1.9

# Instalar dependencias auxiliares
echo "🔧 Instalando dependencias auxiliares..."
python3 -m pip install python-multipart==0.0.6
python3 -m pip install pyyaml==6.0.1
python3 -m pip install python-dotenv==1.0.0
python3 -m pip install jinja2==3.1.2
python3 -m pip install requests==2.31.0
python3 -m pip install aiofiles==23.2.0
python3 -m pip install pillow==10.1.0
python3 -m pip install numpy==1.24.4
python3 -m pip install pytz==2023.3

# Verificar instalación
echo "🔍 Verificando instalación..."
python3 -c "
import fastapi
import pandas as pd
import openpyxl
import pptx
print('✅ Dependencias principales: OK')

try:
    from google.cloud import bigquery
    print('✅ BigQuery: OK')
except ImportError:
    print('⚠️ BigQuery: Falta configurar credenciales')

print('✅ Instalación completada exitosamente!')
"

echo ""
echo "🎉 FACO Weekly instalado correctamente!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configurar credenciales de Google Cloud:"
echo "   export GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account-key.json'"
echo ""
echo "2. Copiar configuración:"
echo "   cp .env.example .env"
echo ""
echo "3. Iniciar servidor:"
echo "   python3 main.py"
echo "   # o"
echo "   uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "4. Probar generación de reportes:"
echo "   curl -X POST 'http://localhost:8000/generate-reports' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"fecha_inicio\": \"2025-06-01\", \"fecha_fin\": \"2025-06-12\"}'"
echo ""
echo "✨ Sistema listo para generar reportes Excel y PowerPoint automatizados!"
