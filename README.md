# 🚀 FACO Weekly - Reportes Automatizados Telefónica del Perú

## ✅ VERSIÓN CORREGIDA SIN ERRORES DE COMPILACIÓN

Sistema automatizado para generar reportes semanales Excel y PowerPoint de gestión de cobranza para Telefónica del Perú, **sin dependencias problemáticas** que requieren compilación C.

### 🔧 INSTALACIÓN SEGURA

#### Opción 1: Script de Instalación Automática (Recomendado)
```bash
# Clonar repositorio
git clone https://github.com/reyer3/faco_weekly.git
cd faco_weekly

# Hacer ejecutable el script de instalación
chmod +x install_safe.sh

# Ejecutar instalación segura
./install_safe.sh
```

#### Opción 2: Instalación Manual
```bash
# Limpiar caché para evitar problemas
pip cache purge

# Configurar variables de entorno (importante)
export MATPLOTLIB_BACKEND=Agg
export NO_MATPLOTLIB=1

# Instalar dependencias una por una
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pandas==2.1.3
pip install google-cloud-bigquery==3.13.0
pip install openpyxl==3.1.2
pip install python-pptx==0.6.23
pip install python-multipart==0.0.6
pip install pyyaml==6.0.1
pip install python-dotenv==1.0.0
pip install xlsxwriter==3.1.9
pip install jinja2==3.1.2
pip install requests==2.31.0
pip install aiofiles==23.2.0
pip install pillow==10.1.0
pip install numpy==1.24.4
pip install pytz==2023.3
```

### 🛠️ CONFIGURACIÓN

1. **Configurar credenciales de Google Cloud:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

2. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 🚀 EJECUCIÓN

#### Iniciar Servidor
```bash
# Opción 1: Python directo
python3 main.py

# Opción 2: Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Verificar Estado
```bash
curl http://localhost:8000/health
```

### 📊 GENERAR REPORTES

#### Via API REST
```bash
# Generar reportes Excel y PowerPoint
curl -X POST "http://localhost:8000/generate-reports" \\
  -H "Content-Type: application/json" \\
  -d '{
    "fecha_inicio": "2025-06-01",
    "fecha_fin": "2025-06-12",
    "formato": "ambos"
  }'
```

#### Parámetros de Generación
- `fecha_inicio`: Fecha inicio período (YYYY-MM-DD)
- `fecha_fin`: Fecha fin período (YYYY-MM-DD)
- `incluir_cerradas`: Incluir campañas cerradas (true/false)
- `formato`: Tipo de reporte ("excel", "powerpoint", "ambos")

#### Descargar Archivos Generados
```bash
# Descargar Excel
curl -O http://localhost:8000/download-excel/Informe_Semanal_Telefonica_TIMESTAMP.xlsx

# Descargar PowerPoint
curl -O http://localhost:8000/download-powerpoint/Presentacion_Semanal_Telefonica_TIMESTAMP.pptx
```

### 📋 ENDPOINTS DISPONIBLES

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Información del sistema |
| `/health` | GET | Estado del sistema |
| `/vigencias-status` | GET | Estado de vigencias activas |
| `/process-by-vigencias` | POST | Procesamiento por vigencias |
| `/generate-reports` | POST | **🆕 Generar reportes automatizados** |
| `/download-excel/{filename}` | GET | **🆕 Descargar archivo Excel** |
| `/download-powerpoint/{filename}` | GET | **🆕 Descargar archivo PowerPoint** |
| `/validate-vigencias` | POST | Validar lógica de vigencias |

### 📊 CARACTERÍSTICAS DE LOS REPORTES

#### 📈 Archivo Excel (Base Maestra)
- **Resumen Ejecutivo**: KPIs principales y métricas clave
- **Análisis por Canal**: Comparativa detallada CALL vs VOICEBOT
- **Evolución Diaria**: Tendencias temporales de contactabilidad
- **Carteras Activas**: Estado y configuración de campañas
- **KPIs por Campaña**: Métricas específicas por archivo
- **Recomendaciones**: Insights automáticos basados en datos

#### 🎯 Presentación PowerPoint (Ejecutiva)
- **Portada**: Información del período y sistema
- **Resumen Ejecutivo**: Métricas clave visualizadas
- **Análisis por Canal**: Comparativa visual CALL vs VOICEBOT
- **Evolución Temporal**: Patrones y tendencias identificadas
- **Carteras Activas**: Resumen de asignaciones y vigencias
- **Recomendaciones**: Acciones prioritarias sugeridas

### 🔍 MÉTRICAS INCLUIDAS

#### 📞 Canal CALL
- Total gestiones realizadas
- Contactos efectivos y tasas de contactabilidad
- Compromisos obtenidos y montos
- Duración promedio de llamadas
- Intensidad de gestión por cliente

#### 🤖 Canal VOICEBOT
- Volumen de gestiones automatizadas
- Contactos efectivos por bot
- Compromisos automatizados
- Eficiencia operativa

#### 📈 Análisis Consolidado
- Tasa de contactabilidad global
- Efectividad comparativa entre canales
- Evolución temporal de métricas
- Identificación de patrones operativos

### ⚠️ SOLUCIÓN DE PROBLEMAS

#### Error de Compilación matplotlib
```bash
# Si aparecen errores de compilación:
export MATPLOTLIB_BACKEND=Agg
export NO_MATPLOTLIB=1
pip cache purge
pip install --no-cache-dir --upgrade pip
```

#### Error de memoria durante instalación
```bash
# Instalar dependencias una por una en lugar de requirements.txt
pip install fastapi uvicorn pandas google-cloud-bigquery
pip install openpyxl python-pptx xlsxwriter
```

#### Error de permisos BigQuery
```bash
# Verificar credenciales
echo $GOOGLE_APPLICATION_CREDENTIALS
gcloud auth application-default login
```

### 📁 ESTRUCTURA DE ARCHIVOS GENERADOS

```
📂 Archivos Generados/
├── 📊 Informe_Semanal_Telefonica_YYYYMMDD_HHMMSS.xlsx
│   ├── 📄 Resumen Ejecutivo
│   ├── 📄 Análisis por Canal
│   ├── 📄 Evolución Diaria
│   ├── 📄 Carteras Activas
│   ├── 📄 KPIs por Campaña
│   └── 📄 Recomendaciones
│
└── 🎯 Presentacion_Semanal_Telefonica_YYYYMMDD_HHMMSS.pptx
    ├── 🏠 Portada
    ├── 📊 Resumen Ejecutivo
    ├── 📞🤖 Análisis por Canal
    ├── 📈 Evolución Temporal
    ├── 📋 Carteras Activas
    └── 💡 Recomendaciones
```

### 🔄 AUTOMATIZACIÓN

#### Cron Job para Reportes Semanales
```bash
# Agregar a crontab para ejecución automática los lunes a las 8 AM
0 8 * * 1 cd /path/to/faco_weekly && python3 -c "
import requests
from datetime import datetime, timedelta

# Calcular fechas de la semana anterior
fin = datetime.now().date()
inicio = fin - timedelta(days=7)

# Generar reporte
response = requests.post('http://localhost:8000/generate-reports', json={
    'fecha_inicio': inicio.strftime('%Y-%m-%d'),
    'fecha_fin': fin.strftime('%Y-%m-%d'),
    'formato': 'ambos'
})

print('Reporte semanal generado:', response.json())
"
```

### 📧 INTEGRACIÓN CON EMAIL

```python
# Ejemplo de integración para envío automático por email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def enviar_reporte_email(excel_path, ppt_path, destinatarios):
    msg = MIMEMultipart()
    msg['From'] = "sistema@telefonica.pe"
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"Informe Semanal Automatizado - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Adjuntar archivos
    for archivo in [excel_path, ppt_path]:
        with open(archivo, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(archivo)}'
            )
            msg.attach(part)
    
    # Enviar email
    server = smtplib.SMTP('smtp.telefonica.pe', 587)
    server.starttls()
    server.login("usuario", "password")
    server.send_message(msg)
    server.quit()
```

### 🛡️ CARACTERÍSTICAS DE SEGURIDAD

- **Sin dependencias problemáticas**: Eliminadas matplotlib y librerías que requieren compilación C
- **Manejo robusto de errores**: Try/catch en todas las operaciones críticas
- **Validación de datos**: Verificación de integridad antes de procesamiento
- **Logs detallados**: Trazabilidad completa de operaciones
- **Modo fail-safe**: El sistema continúa operando aunque falten algunos datos

### ✨ BENEFICIOS

#### 🕒 Eficiencia Temporal
- **Automatización completa**: De 4 horas manuales a 15 minutos automatizados
- **Generación dual**: Excel + PowerPoint en una sola ejecución
- **Actualización en tiempo real**: Datos frescos desde BigQuery

#### 📊 Calidad de Datos
- **Consistencia**: Misma fuente de verdad para todos los reportes
- **Precisión**: Cálculos automáticos sin errores manuales
- **Completitud**: Cobertura total de métricas relevantes

#### 🎯 Valor Ejecutivo
- **Insights automáticos**: Recomendaciones basadas en patterns
- **Formato profesional**: Listo para presentación directiva
- **Comparativas temporales**: Evolución y tendencias identificadas

### 🆘 SOPORTE

Para problemas o mejoras:
1. **Issues GitHub**: [Crear issue](https://github.com/reyer3/faco_weekly/issues)
2. **Logs del sistema**: Revisar `/var/log/faco_weekly.log`
3. **Estado del servicio**: `curl http://localhost:8000/health`

### 📜 LICENCIA

MIT License - Ver archivo LICENSE para detalles.

---

**🎉 Sistema listo para generar reportes ejecutivos automatizados sin errores de compilación!**
