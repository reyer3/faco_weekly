# 📊 FACO Weekly - Sistema de Reportes Automatizados

**Sistema para generar reportes semanales de gestión de cobranza Telefónica Perú** con generación automática de Excel y PowerPoint.

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/reyer3/faco_weekly)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![BigQuery](https://img.shields.io/badge/BigQuery-enabled-orange.svg)](https://cloud.google.com/bigquery)

## 🚀 Nuevas Funcionalidades v2.2.0

- **📈 Generación automática de Excel** con 6 hojas especializadas
- **🎯 Presentaciones PowerPoint ejecutivas** con branding Telefónica
- **🔄 API REST completa** para automatización total
- **📊 KPIs automáticos** y análisis de tendencias
- **⚡ Procesamiento optimizado** con vigencias corregidas

---

## 🎯 Características Principales

### 📋 Gestión de Datos
- **Tabla de Control**: `calendario_v2` gobierna todo el proceso
- **Universo Gestionable**: Solo casos con deuda vigente a fecha de asignación
- **Gestión por cod_luna**: Unidad principal de gestión  
- **Atribución Inteligente**: Pagos atribuidos a última gestión en ventana de 30 días
- **Manejo de Duplicidades**: cod_luna puede estar en múltiples carteras

### 🔄 Canales de Gestión
- **CALL**: Gestiones con agentes humanos
- **VOICEBOT**: Gestiones automatizadas
- **Integración completa**: Homologación unificada de resultados

### 📊 Tipos de Cartera
- **Móvil**: Solo negocio "MOVIL"
- **Fijo**: Todo lo demás (FIJA, MT, otros)
- **Altas Nuevas**: `*_AN_*`
- **Temprana**: `*_Temprana_*`  
- **Fraccionamiento**: `*_CF_ANN_*`

### 🎯 Métricas Clave
- **CONTACTO_EFECTIVO**: CONTACTO, COMPROMISO, PROMESA, ACEPTA
- **NO_CONTACTO**: NO CONTESTA, OCUPADO, APAGADO, BUZÓN  
- **CONTACTO_NO_EFECTIVO**: NO ACEPTA, RECHAZA, NO INTERESADO

---

## ⚡ Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/reyer3/faco_weekly.git
cd faco_weekly

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
cp .env.example .env
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"

# Iniciar servidor
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🚀 Uso Rápido

### Verificar Estado
```bash
curl http://localhost:8000/health
```

### Generar Reportes Automáticamente
```bash
# Generar Excel + PowerPoint de la última semana
curl -X POST "http://localhost:8000/generate-reports" \
  -d "fecha_inicio=2025-06-01" \
  -d "fecha_fin=2025-06-12" \
  -d "formato=ambos"
```

### Script de Prueba
```bash
# Probar funcionalidad completa
python test_reports.py --periodo semanal --formato ambos
```

---

## 📋 Endpoints Principales

### 🆕 **Generación de Reportes**
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/generate-reports` | POST | 🆕 Generar reportes Excel/PowerPoint |
| `/download-excel/{filename}` | GET | 🆕 Descargar archivo Excel |
| `/download-powerpoint/{filename}` | GET | 🆕 Descargar archivo PowerPoint |

### 📊 **Procesamiento de Datos**
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/process-by-vigencias` | POST | Procesamiento con vigencias corregidas |
| `/validate-vigencias` | GET | Validar lógica de vigencias |
| `/vigencias-status` | GET | Estado de vigencias activas |

### 🔍 **Monitoreo**
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del sistema |
| `/` | GET | Información general y versión |

---

## 📊 Estructura de Reportes

### 📈 **Archivo Excel** (6 Hojas)
1. **Resumen Ejecutivo** - KPIs consolidados y métricas clave
2. **Análisis por Canal** - Comparativa CALL vs VOICEBOT  
3. **Evolución Diaria** - Tendencias temporales y patrones
4. **Carteras Activas** - Estado de vigencias y asignaciones
5. **KPIs por Campaña** - Performance detallada por archivo
6. **Recomendaciones** - Insights automáticos y acciones sugeridas

### 🎯 **Presentación PowerPoint** (6 Slides)
1. **Portada** - Información del período y branding
2. **Resumen Ejecutivo** - KPIs clave consolidados
3. **Análisis por Canal** - Distribución y comparativas
4. **Evolución Temporal** - Tendencias y mejores días
5. **Carteras Activas** - Resumen de asignaciones
6. **Recomendaciones** - Acciones estratégicas prioritarias

---

## 🎯 KPIs Incluidos

### 📊 **Indicadores Consolidados**
- Total Gestiones (CALL + VOICEBOT)
- Contactabilidad Global (% efectiva)
- Tasa de Compromiso (% PDPs)
- Monto Compromisos Totales
- Clientes Únicos Gestionados

### 📞 **Por Canal**
- Gestiones por canal
- Contactabilidad específica
- Compromisos obtenidos
- Duración promedio (CALL)
- Distribución temporal

### 💰 **Financieros**
- Pagos procesados
- Ticket promedio
- Rangos de montos
- Atribución a gestiones

---

## 🧪 Ejemplos de Uso

### Reporte Semanal Completo
```python
import requests

response = requests.post("http://localhost:8000/generate-reports", params={
    "fecha_inicio": "2025-06-01",
    "fecha_fin": "2025-06-12", 
    "formato": "ambos"
})

result = response.json()
print(f"Excel: {result['enlaces_descarga']['excel']}")
print(f"PowerPoint: {result['enlaces_descarga']['powerpoint']}")
```

### Solo Presentación Ejecutiva
```python
response = requests.post("http://localhost:8000/generate-reports", params={
    "fecha_inicio": "2025-06-01",
    "fecha_fin": "2025-06-12",
    "formato": "powerpoint"
})
```

### Análisis Detallado con Campañas Cerradas
```python
response = requests.post("http://localhost:8000/generate-reports", params={
    "fecha_inicio": "2025-06-01", 
    "fecha_fin": "2025-06-12",
    "formato": "excel",
    "incluir_cerradas": True
})
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# BigQuery
GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
BIGQUERY_PROJECT_ID="mibot-222814"
BIGQUERY_DATASET="BI_USA"

# Reportes (Opcional)
TELEFONICA_LOGO_PATH="/path/to/logo.png"
REPORT_OUTPUT_DIR="/shared/reports"
MAX_REPORT_RETENTION_DAYS=30
```

### Personalización de Colores
```python
# En report_generator.py
COLORS = {
    'telefonica_blue': '0019A5',
    'telefonica_light_blue': '5BB4E5', 
    'telefonica_green': '00A651',
    'telefonica_orange': 'FF6600'
}
```

---

## 🔄 Automatización

### Scheduler Semanal
```python
import schedule
import requests
from datetime import datetime, timedelta

def reporte_automatico():
    # Calcular semana anterior
    fin = datetime.now() - timedelta(days=1)
    inicio = fin - timedelta(days=7)
    
    requests.post("http://localhost:8000/generate-reports", params={
        "fecha_inicio": inicio.strftime('%Y-%m-%d'),
        "fecha_fin": fin.strftime('%Y-%m-%d'),
        "formato": "ambos"
    })

# Ejecutar todos los lunes a las 8 AM
schedule.every().monday.at("08:00").do(reporte_automatico)
```

### Integración con Teams/Slack
```python
import requests

def notificar_reporte_generado(webhook_url, archivos):
    payload = {
        "text": f"📊 Nuevo reporte semanal generado",
        "attachments": [{
            "color": "good",
            "fields": [
                {"title": "Excel", "value": archivos['excel']['filename']},
                {"title": "PowerPoint", "value": archivos['powerpoint']['filename']}
            ]
        }]
    }
    requests.post(webhook_url, json=payload)
```

---

## 📖 Documentación Completa

- 📊 **[Generación de Reportes](docs/AUTOMATED_REPORTS.md)** - Guía completa de reportes automatizados
- 🔄 **[API Reference](docs/API.md)** - Documentación de endpoints
- 🧪 **[Testing Guide](docs/TESTING.md)** - Guías de prueba y validación
- 🔧 **[Configuration](docs/CONFIG.md)** - Configuración avanzada

---

## 🛠️ Desarrollo

### Estructura del Proyecto
```
faco_weekly/
├── main.py                 # API principal con endpoints
├── report_generator.py     # 🆕 Generador de reportes
├── test_reports.py        # 🆕 Script de pruebas
├── requirements.txt       # Dependencias actualizadas
├── .env.example          # Configuración de ejemplo
├── start.sh             # Script de inicio
├── docs/                # 📚 Documentación
│   └── AUTOMATED_REPORTS.md
└── outputs/             # 📁 Archivos generados
```

### Ejecutar Tests
```bash
# Test completo del sistema
python test_reports.py --periodo semanal --formato ambos

# Test solo API
python test_api.py

# Health check
curl http://localhost:8000/health
```

---

## 🔍 Datos y Tablas

### Tablas BigQuery Principales
- `dash_P3fV4dWNeMkN5RJMhV8e_calendario_v2` - **Control de vigencias**
- `batch_P3fV4dWNeMkN5RJMhV8e_asignacion` - **Asignaciones**
- `mibotair_P3fV4dWNeMkN5RJMhV8e` - **Gestiones CALL**
- `voicebot_P3fV4dWNeMkN5RJMhV8e` - **Gestiones VOICEBOT**
- `batch_P3fV4dWNeMkN5RJMhV8e_pagos` - **Pagos procesados**

### Reglas de Negocio
- **Asignaciones**: Desde 2025-06-11 en adelante
- **Gestiones**: Según calendario de gestión activo
- **Deuda**: Solo vigente a fecha de asignación
- **Vigencias**: Cada campaña tiene su propia ventana temporal
- **Atribución**: Ventana de 30 días para vincular pagos

---

## 🤝 Contribución

Para mejoras o nuevas funcionalidades:

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Add nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/reyer3/faco_weekly/issues)
- **Documentación**: [docs/](docs/)
- **Email**: Contactar al equipo de desarrollo

---

## 📄 Licencia

MIT License - Ver archivo [LICENSE](LICENSE) para detalles.

---

**🎯 Desarrollado para Telefónica del Perú - Sistema de Gestión de Cobranza**  
*Versión 2.2.0 - Junio 2025*

---

## 🏆 Changelog v2.2.0

### ✨ Nuevas Funcionalidades
- ➕ Generación automática de reportes Excel y PowerPoint
- ➕ Endpoint `/generate-reports` con múltiples formatos
- ➕ Endpoints de descarga `/download-excel` y `/download-powerpoint`
- ➕ KPIs automáticos y recomendaciones inteligentes
- ➕ Script de pruebas comprehensivo `test_reports.py`

### 🔧 Mejoras
- ⚡ Optimización de queries BigQuery para reportes
- 🎨 Branding Telefónica aplicado a todos los archivos
- 📊 Métricas consolidadas por canal y campaña
- 🔄 Integración completa con pipeline existente

### 🐛 Correcciones
- ✅ Lógica de vigencias corregida por campaña específica
- ✅ Homologación unificada CALL + VOICEBOT
- ✅ Atribución mejorada de pagos a gestiones
- ✅ Manejo robusto de errores y validaciones

---

*¡Sistema listo para automatizar completamente los reportes semanales! 🚀*
