# FACO Weekly - Sistema Automatizado de Reportes

Sistema para generar reportes semanales de gestión de cobranza Telefónica Perú basado en calendario_v2 como tabla de control principal.

## 🎯 Características Principales

- **Tabla de Control**: Uso de `calendario_v2` para gobernar todo el proceso
- **Universo Gestionable**: Solo casos con deuda vigente a fecha de asignación  
- **Gestión por cod_luna**: Unidad principal de gestión
- **Atribución Inteligente**: Pagos atribuidos a última gestión en ventana de 30 días
- **Manejo de Duplicidades**: cod_luna puede estar en múltiples carteras

## 📋 Reglas de Negocio Implementadas

### Clasificación de Servicios
- **Móvil**: Solo negocio "MOVIL" 
- **Fijo**: Todo lo demás (FIJA, MT, otros)

### Clasificación de Carteras (por patrón de archivo)
- **Altas Nuevas**: `*_AN_*`
- **Temprana**: `*_Temprana_*` 
- **Fraccionamiento**: `*_CF_ANN_*`

### Filtros de Datos
- **Asignaciones**: Desde 2025-06-11 en adelante
- **Gestiones**: Según calendario de gestión activo
- **Deuda**: Solo vigente a fecha de asignación

### Tipificaciones Homologadas
- **CONTACTO_EFECTIVO**: CONTACTO, COMPROMISO, PROMESA, ACEPTA
- **NO_CONTACTO**: NO CONTESTA, OCUPADO, APAGADO, BUZÓN
- **CONTACTO_NO_EFECTIVO**: NO ACEPTA, RECHAZA, NO INTERESADO

## 🚀 Instalación y Uso

### 1. Clonar Repositorio
```bash
git clone https://github.com/reyer3/faco_weekly.git
cd faco_weekly
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Credenciales
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Configurar credenciales de Google Cloud
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 4. Ejecutar API
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Probar Funcionalidad
```bash
# Health check
curl http://localhost:8000/health

# Procesar datos semanales
curl -X POST "http://localhost:8000/process-weekly" \
  -H "Content-Type: application/json" \
  -d '{"fecha_inicio": "2025-06-01", "fecha_fin": "2025-06-12"}'
```

## 📊 Endpoints Principales

### GET /
Información general del API

### GET /health  
Verificación de estado y conexión a BigQuery

### POST /process-weekly
Procesa datos semanales según calendario_v2
- Extrae campañas activas del calendario
- Procesa asignaciones con reglas de duplicidad
- Calcula universo gestionable con deuda vigente
- Atribuye pagos a gestiones
- Genera KPIs y ranking de agentes

## 🏗️ Arquitectura

```
faco_weekly/
├── main.py              # API principal con lógica de negocio
├── requirements.txt     # Dependencias
├── .env.example        # Configuración de ejemplo
├── README.md           # Documentación
└── test_api.py         # Script de pruebas
```

## 📈 Lógica de Atribución de Pagos

1. **Ventana**: Buscar gestiones en últimos 30 días antes del pago
2. **Mapeo**: Relacionar documento → cuenta → cod_luna
3. **Prioridad**: CONTACTO_EFECTIVO > CONTACTO_NO_EFECTIVO > NO_CONTACTO
4. **Temporal**: Gestión más reciente dentro de la ventana
5. **Sin Atribución**: Pagos sin gestión en ventana = "SIN_GESTION"

## 🔍 Manejo de Duplicidades

- **Identificación**: cod_luna en múltiples carteras se marca como duplicado
- **Gestión**: Válido para gestionar desde cualquier cartera
- **Atribución**: Pago se atribuye según cuenta específica del documento

## 📊 KPIs Calculados

- **Tasa Contactabilidad**: Contactos efectivos / Total gestiones
- **Tasa Atribución**: Pagos atribuidos / Total pagos  
- **Intensidad Gestión**: Gestiones / Clientes gestionados
- **Ticket Promedio**: Monto total / Número pagos

## 🛠️ Configuración

### Variables de Entorno
```bash
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
BIGQUERY_PROJECT_ID=mibot-222814
BIGQUERY_DATASET=BI_USA
```

### Tablas BigQuery Utilizadas
- `dash_P3fV4dWNeMkN5RJMhV8e_calendario_v2` (control)
- `batch_P3fV4dWNeMkN5RJMhV8e_asignacion`
- `batch_P3fV4dWNeMkN5RJMhV8e_tran_deuda`
- `batch_P3fV4dWNeMkN5RJMhV8e_pagos`
- `mibotair_P3fV4dWNeMkN5RJMhV8e` (gestiones CALL)
- `voicebot_P3fV4dWNeMkN5RJMhV8e` (gestiones VOICEBOT)

## 🧪 Testing

```bash
# Ejecutar script de pruebas
python test_api.py
```

## 📝 Logs

El sistema genera logs detallados incluyendo:
- Estadísticas de procesamiento
- Identificación de duplicidades
- Métricas de atribución
- Errores y warnings

## 🔄 Flujo de Procesamiento

1. **Control**: Leer calendario_v2 para campañas activas
2. **Extracción**: Obtener asignaciones basadas en archivos de calendario
3. **Deduplicación**: Procesar cod_lunas en múltiples carteras
4. **Universo**: Crear base gestionable con deuda vigente
5. **Gestiones**: Extraer actividad del período según calendario
6. **Atribución**: Vincular pagos con gestiones
7. **KPIs**: Calcular métricas de performance
8. **Ranking**: Generar ranking de agentes

## 📞 Soporte

Para problemas o mejoras, crear issue en GitHub o contactar al equipo de desarrollo.

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.
