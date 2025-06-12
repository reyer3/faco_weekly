#!/bin/bash

# ===========================================
# FACO WEEKLY - SETUP Y EJECUCIÓN RÁPIDA
# ===========================================

echo "🚀 FACO WEEKLY - Sistema de Reportes Telefónica"
echo "==============================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "📥 Instálalo desde: https://python.org"
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "🐍 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip e instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar configuración
echo "🔍 Verificando configuración..."

if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "📋 Copiando archivo de ejemplo..."
    cp .env.example .env
    echo "✏️  Edita .env con tus credenciales de Google Cloud"
fi

# Verificar credenciales de Google Cloud
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  Variable GOOGLE_APPLICATION_CREDENTIALS no configurada"
    echo "🔑 Configura las credenciales:"
    echo "   export GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account-key.json'"
else
    echo "✅ Credenciales de Google Cloud configuradas"
fi

# Función para iniciar el API
start_api() {
    echo "🚀 Iniciando API FACO Weekly..."
    echo "🌐 Servidor: http://localhost:8000"
    echo "📚 Documentación: http://localhost:8000/docs"
    echo "🛑 Presiona Ctrl+C para detener"
    echo ""
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# Función para ejecutar tests
run_tests() {
    echo "🧪 Ejecutando tests del sistema..."
    python test_api.py
}

# Función para procesamiento rápido
quick_process() {
    echo "⚡ Procesamiento rápido de datos semanales..."
    echo "📊 Usando fechas por defecto (última semana)"
    
    # Iniciar API en background
    uvicorn main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    
    # Esperar que el API esté listo
    echo "⏳ Esperando que el API esté listo..."
    sleep 5
    
    # Ejecutar procesamiento
    python test_api.py process
    
    # Detener API
    kill $API_PID 2>/dev/null
    echo "✅ Procesamiento completado"
}

# Menú principal
echo ""
echo "🎯 ¿Qué deseas hacer?"
echo "1) Iniciar API (modo interactivo)"
echo "2) Ejecutar tests"
echo "3) Procesamiento rápido" 
echo "4) Mostrar ayuda"
echo "5) Salir"
echo ""

read -p "Selecciona una opción [1-5]: " choice

case $choice in
    1)
        start_api
        ;;
    2)
        run_tests
        ;;
    3)
        quick_process
        ;;
    4)
        echo ""
        echo "📖 AYUDA FACO WEEKLY"
        echo "==================="
        echo ""
        echo "🔧 Configuración inicial:"
        echo "   1. Configurar credenciales Google Cloud en .env"
        echo "   2. export GOOGLE_APPLICATION_CREDENTIALS='path/to/key.json'"
        echo ""
        echo "🚀 Uso básico:"
        echo "   ./start.sh                    # Menú interactivo"
        echo "   uvicorn main:app --reload     # Iniciar API manualmente"
        echo "   python test_api.py            # Ejecutar todos los tests"
        echo ""
        echo "📊 API Endpoints:"
        echo "   GET  /                        # Info del sistema"
        echo "   GET  /health                  # Estado de salud"
        echo "   POST /process-weekly          # Procesar datos semanales"
        echo ""
        echo "🧪 Testing:"
        echo "   python test_api.py health     # Solo health check"
        echo "   python test_api.py process    # Solo procesamiento"
        echo ""
        echo "📁 Estructura del proyecto:"
        echo "   main.py                       # API principal"
        echo "   test_api.py                   # Script de pruebas"
        echo "   requirements.txt              # Dependencias"
        echo "   .env                          # Configuración"
        echo ""
        ;;
    5)
        echo "👋 ¡Hasta luego!"
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "✅ Operación completada"
echo "📞 Para soporte, consulta README.md o crea un issue en GitHub"
