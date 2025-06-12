# 📊 FACO Weekly - Sistema de Reportes Automatizados

## 🚀 Nuevas Funcionalidades v2.2.0

El sistema FACO Weekly ahora incluye **generación automática de reportes Excel y PowerPoint** para análisis ejecutivo de gestión de cobranza de Telefónica del Perú.

### ✨ Características Principales

- 📈 **Generación automática de Excel** con múltiples hojas y análisis detallado
- 🎯 **Presentaciones PowerPoint ejecutivas** listas para dirección
- 🔄 **Integración completa** con pipeline de datos BigQuery existente
- 📊 **KPIs automáticos** y tendencias temporales
- 🎨 **Branding Telefónica** aplicado a todos los reportes
- ⚡ **API RESTful** para automatización completa

---

## 🛠️ Instalación y Configuración

### Dependencias Actualizadas

```bash
# Instalar nuevas dependencias
pip install -r requirements.txt

# Dependencias clave añadidas:
# - xlsxwriter: Formateo avanzado Excel
# - matplotlib/seaborn: Gráficos
# - jinja2: Templates
# - aiofiles: Operaciones async
```

### Variables de Entorno

```bash
# Copiar configuración base
cp .env.example .env

# Configurar credenciales Google Cloud
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

---

## 📋 Endpoints Nuevos

### 🆕 `/generate-reports` (POST)

Endpoint principal para generar reportes automatizados.

**Parámetros:**
- `fecha_inicio` (str): Fecha inicio período (YYYY-MM-DD)
- `fecha_fin` (str): Fecha fin período (YYYY-MM-DD) 
- `formato` (str): Tipo de reporte ("excel", "powerpoint", "ambos")
- `incluir_cerradas` (bool): Incluir campañas cerradas

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/generate-reports" \
  -d "fecha_inicio=2025-06-01" \
  -d "fecha_fin=2025-06-12" \
  -d "formato=ambos" \
  -d "incluir_cerradas=false"
```

**Respuesta:**
```json
{
  "status": "success",
  "periodo": "2025-06-01 a 2025-06-12",
  "timestamp": "20250612_143022",
  "archivos_generados": {
    "excel": {
      "filename": "Informe_Semanal_Telefonica_20250612_143022.xlsx",
      "size_mb": 2.1
    },
    "powerpoint": {
      "filename": "Presentacion_Semanal_Telefonica_20250612_143022.pptx", 
      "size_mb": 1.8
    }
  },
  "enlaces_descarga": {
    "excel": "/download-excel/Informe_Semanal_Telefonica_20250612_143022.xlsx",
    "powerpoint": "/download-powerpoint/Presentacion_Semanal_Telefonica_20250612_143022.pptx"
  },
  "resumen_ejecutivo": {
    "total_gestiones": 759118,
    "contactos_efectivos": 12440,
    "tasa_contactabilidad": 1.64,
    "compromisos": 4502,
    "monto_compromisos": 175998
  }
}
```

### 🆕 `/download-excel/{filename}` (GET)

Descargar archivo Excel generado.

### 🆕 `/download-powerpoint/{filename}` (GET)

Descargar archivo PowerPoint generado.

---

## 📊 Estructura de Reportes

### 📈 Archivo Excel

El Excel generado contiene **6 hojas especializadas**:

1. **Resumen Ejecutivo**
   - KPIs consolidados del período
   - Métricas de contactabilidad y compromisos
   - Información de pagos procesados

2. **Análisis por Canal**
   - Comparativa CALL vs VOICEBOT
   - Tasas de contactabilidad por canal
   - Distribución de gestiones

3. **Evolución Diaria** 
   - Tendencias día a día
   - Contactos efectivos por fecha
   - Patrones de efectividad

4. **Carteras Activas**
   - Estado de vigencias
   - Clientes asignados por cartera
   - Información de asignaciones

5. **KPIs por Campaña**
   - Métricas detalladas por archivo
   - Performance individual de campañas
   - Montos de compromiso

6. **Recomendaciones**
   - Insights automáticos
   - Acciones sugeridas por prioridad
   - Análisis de oportunidades

### 🎯 Presentación PowerPoint

La presentación ejecutiva incluye **6 slides profesionales**:

1. **Portada** - Información del período y branding
2. **Resumen Ejecutivo** - KPIs clave del período
3. **Análisis por Canal** - Comparativa CALL vs VOICEBOT
4. **Evolución Temporal** - Tendencias y patrones
5. **Carteras Activas** - Estado de asignaciones
6. **Recomendaciones** - Acciones estratégicas

---

## 🧪 Pruebas y Validación

### Script de Prueba Incluido

```bash
# Probar generación completa (Excel + PowerPoint)
python test_reports.py --periodo semanal --formato ambos

# Probar solo Excel para período específico
python test_reports.py --inicio 2025-06-01 --fin 2025-06-12 --formato excel

# Probar con servidor remoto
python test_reports.py --url http://prod-server:8000 --formato powerpoint
```

### Validaciones Automáticas

El script de prueba verifica:
- ✅ Conectividad con BigQuery
- ✅ Estado de vigencias del calendario
- ✅ Generación exitosa de archivos
- ✅ Descarga y validación de contenido
- ✅ Integridad de datos procesados

---

## 🔄 Casos de Uso

### 1. Reporte Semanal Automatizado

```python
import requests

# Generar reporte de la semana pasada
response = requests.post("http://localhost:8000/generate-reports", params={
    "fecha_inicio": "2025-06-03",
    "fecha_fin": "2025-06-10", 
    "formato": "ambos"
})

result = response.json()
print(f"Archivos: {result['archivos_generados']}")
```

### 2. Dashboard Ejecutivo (Solo PowerPoint)

```python
# Solo presentación para reunión de dirección
response = requests.post("http://localhost:8000/generate-reports", params={
    "fecha_inicio": "2025-06-01",
    "fecha_fin": "2025-06-12",
    "formato": "powerpoint"
})
```

### 3. Análisis Detallado (Solo Excel)

```python
# Excel completo para análisis profundo
response = requests.post("http://localhost:8000/generate-reports", params={
    "fecha_inicio": "2025-06-01", 
    "fecha_fin": "2025-06-12",
    "formato": "excel",
    "incluir_cerradas": True  # Incluir todas las campañas
})
```

---

## 🎯 Métricas y KPIs Incluidos

### Indicadores Consolidados
- **Total Gestiones**: CALL + VOICEBOT
- **Contactabilidad Global**: % de contactos efectivos
- **Tasa de Compromiso**: % de PDPs vs contactos
- **Monto Compromisos**: Total comprometido en período
- **Clientes Únicos**: Alcance de gestión

### Por Canal (CALL vs VOICEBOT)
- Gestiones realizadas por canal
- Contactabilidad específica por canal  
- Compromisos obtenidos
- Duración promedio (CALL)
- Distribución temporal

### Por Campaña
- Performance individual por archivo
- Clientes gestionados vs asignados
- Tasas de contactabilidad por cartera
- Montos de compromiso por campaña
- Cobertura temporal de gestión

### Financieros
- Pagos procesados en período
- Ticket promedio de pagos
- Rangos de montos (min/max)
- Atribución de pagos a gestiones

---

## ⚡ Automatización Avanzada

### Scheduler Automático (Ejemplo)

```python
import schedule
import time
import requests
from datetime import datetime, timedelta

def generar_reporte_semanal():
    """Generar reporte automático todos los lunes"""
    
    # Calcular semana anterior
    hoy = datetime.now()
    fin_semana = hoy - timedelta(days=hoy.weekday() + 1)  # Domingo anterior
    inicio_semana = fin_semana - timedelta(days=6)  # Lunes anterior
    
    # Generar reporte
    response = requests.post("http://localhost:8000/generate-reports", params={
        "fecha_inicio": inicio_semana.strftime('%Y-%m-%d'),
        "fecha_fin": fin_semana.strftime('%Y-%m-%d'),
        "formato": "ambos"
    })
    
    if response.status_code == 200:
        print(f"✅ Reporte semanal generado: {inicio_semana} - {fin_semana}")
    else:
        print(f"❌ Error generando reporte: {response.status_code}")

# Programar ejecución todos los lunes a las 8 AM
schedule.every().monday.at("08:00").do(generar_reporte_semanal)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Integración con Email

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def enviar_reporte_por_email(excel_path, ppt_path, destinatarios):
    """Enviar reportes por email automáticamente"""
    
    msg = MIMEMultipart()
    msg['Subject'] = f"Reporte Semanal Telefónica - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = "sistema@telefonica.pe"
    msg['To'] = ", ".join(destinatarios)
    
    # Adjuntar Excel
    with open(excel_path, 'rb') as f:
        excel_attachment = MIMEApplication(f.read(), Name=os.path.basename(excel_path))
        excel_attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(excel_path)}"'
        msg.attach(excel_attachment)
    
    # Adjuntar PowerPoint
    with open(ppt_path, 'rb') as f:
        ppt_attachment = MIMEApplication(f.read(), Name=os.path.basename(ppt_path))
        ppt_attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(ppt_path)}"'
        msg.attach(ppt_attachment)
    
    # Enviar email
    with smtplib.SMTP('smtp.telefonica.pe', 587) as server:
        server.send_message(msg)
```

---

## 🔧 Configuración Avanzada

### Personalización de Reportes

```python
# En report_generator.py, puedes personalizar:

# Colores corporativos
COLORS = {
    'telefonica_blue': '0019A5',
    'telefonica_light_blue': '5BB4E5', 
    'telefonica_green': '00A651',
    'telefonica_orange': 'FF6600'
}

# Métricas incluidas
def _calculate_custom_metrics(self):
    # Agregar métricas específicas de negocio
    pass

# Templates de slides
def _create_custom_slide(self, prs):
    # Personalizar diseño de slides
    pass
```

### Variables de Entorno Adicionales

```bash
# .env
TELEFONICA_LOGO_PATH="/path/to/logo.png"
REPORT_OUTPUT_DIR="/shared/reports"
EMAIL_SMTP_SERVER="smtp.telefonica.pe"
NOTIFICATION_WEBHOOK="https://teams.webhook.url"
MAX_REPORT_RETENTION_DAYS=30
```

---

## 📞 Troubleshooting

### Problemas Comunes

1. **Error de Conexión BigQuery**
   ```bash
   # Verificar credenciales
   gcloud auth application-default login
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

2. **Archivos No Se Generan**
   ```bash
   # Verificar permisos de escritura
   chmod 755 /tmp
   
   # Verificar espacio en disco
   df -h
   ```

3. **Error en Descarga**
   ```bash
   # Verificar que el archivo existe
   curl http://localhost:8000/health
   
   # Comprobar logs del servidor
   tail -f logs/faco_weekly.log
   ```

### Logs y Monitoreo

```python
# Configurar logging detallado
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('faco_weekly.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🎉 Resumen de Beneficios

### Para el Equipo de Gestión
- ⏰ **Ahorro de tiempo**: Reportes automáticos vs manual
- 📊 **Consistencia**: Formato estandarizado y métricas uniformes
- 🎯 **Insights**: Recomendaciones automáticas basadas en datos
- 📈 **Tendencias**: Evolución temporal visualizada

### Para Dirección
- 🚀 **Agilidad**: Reportes ejecutivos en minutos
- 💼 **Profesionalismo**: Presentaciones listas para reuniones
- 📋 **Completitud**: Visión 360° de gestión de cobranza
- 🔍 **Profundidad**: Drill-down por canal y campaña

### Para IT/Sistemas
- 🔄 **Automatización**: Pipeline completo sin intervención manual
- 🛠️ **Escalabilidad**: API REST para integración con otros sistemas
- 📊 **Trazabilidad**: Logs completos y validación de datos
- 🔧 **Mantenibilidad**: Código modular y documentado

---

*Sistema desarrollado para Telefónica del Perú - Gestión de Cobranza*  
*Versión 2.2.0 - Junio 2025*
