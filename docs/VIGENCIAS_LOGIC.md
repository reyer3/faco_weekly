# LÓGICA DE VIGENCIAS EN FACO WEEKLY

## 🎯 Respuesta a la Pregunta: "¿Los rangos de fechas están regidos por las vigencias del calendario?"

**SÍ**, el sistema **FACO Weekly v2.1.0** ya implementa correctamente la lógica donde los rangos de fechas están regidos por las vigencias del `calendario_v2`.

## 📋 ¿Cómo Funciona la Lógica de Vigencias?

### 1. **Tabla de Control: calendario_v2**
```sql
SELECT 
    archivo,                  -- Nombre de la campaña
    fecha_asignacion,        -- INICIO de vigencia
    fecha_cierre,            -- FIN de vigencia  
    vencimiento,             -- Días de vencimiento
    suma_lineas              -- Registros en la campaña
FROM calendario_v2
```

### 2. **Vigencias Específicas por Campaña**
Cada campaña tiene su propia vigencia independiente:

```
Campaña A: Temprana_20250520
├── Vigencia: 2025-05-20 → 2025-06-15
├── Gestiones válidas: Solo entre estas fechas
└── cod_lunas: Solo los asignados en esta campaña

Campaña B: AN_20250602  
├── Vigencia: 2025-06-02 → 2025-06-30
├── Gestiones válidas: Solo entre estas fechas
└── cod_lunas: Solo los asignados en esta campaña
```

### 3. **Filtrado de Gestiones por Vigencia**
El sistema NO usa rangos globales de fechas. En su lugar:

```sql
-- ❌ INCORRECTO (enfoque anterior)
WHERE DATE(gestiones.date) BETWEEN '2025-06-01' AND '2025-06-12'

-- ✅ CORRECTO (enfoque actual)
WHERE (
  (asignacion.archivo = 'Temprana_20250520' AND DATE(gestiones.date) BETWEEN '2025-05-20' AND '2025-06-15')
  OR
  (asignacion.archivo = 'AN_20250602' AND DATE(gestiones.date) BETWEEN '2025-06-02' AND '2025-06-30')
)
```

### 4. **Validación de cod_luna por Campaña**
Un `cod_luna` solo puede ser gestionado si:
- Está asignado en esa campaña específica
- La gestión ocurre dentro de la vigencia de esa campaña

## 🔍 Funciones Implementadas

### `get_unified_gestiones_by_vigencias(calendario_df)`
- ✅ Extrae gestiones respetando vigencias específicas
- ✅ Valida que `cod_luna` esté en la campaña correspondiente  
- ✅ Filtra por `fecha_asignacion` ≤ `fecha_gestion` ≤ `fecha_cierre`

### `analyze_vigencias_coverage(calendario_df, gestiones_df)`
- ✅ Analiza cobertura temporal por campaña
- ✅ Detecta gestiones fuera de vigencia (debería ser 0)
- ✅ Calcula % de cobertura por campaña

### `validate_vigencias_logic(calendario_df, gestiones_df)`
- ✅ Valida que NO haya gestiones fuera de vigencia
- ✅ Identifica problemas de consistencia
- ✅ Reporta estadísticas de validación

## 🎯 Casos de Uso Resueltos

### Caso 1: cod_luna en Múltiples Carteras
```
cod_luna: 123456
├── Campaña Temprana: vigencia 2025-05-20 → 2025-06-15
├── Campaña AN: vigencia 2025-06-02 → 2025-06-30
└── Gestiones válidas:
    ├── 2025-05-25 → Atribuida a Temprana ✅
    ├── 2025-06-05 → Ambas vigencias activas ✅
    └── 2025-06-20 → Solo AN activa ✅
```

### Caso 2: Atribución de Pagos
```
Pago: 2025-06-10, cod_luna: 123456
├── Buscar gestiones en ventana: 2025-05-11 → 2025-06-10
├── Filtrar por vigencias activas en esas fechas
└── Atribuir a la gestión más reciente que cumpla:
    ├── Está en vigencia ✅
    ├── cod_luna correcto ✅
    └── Tipo de contacto prioritario ✅
```

## 📊 Endpoints para Validar Vigencias

### `GET /vigencias-status`
Muestra estado actual de todas las vigencias:
```json
{
  "resumen": {
    "total_campañas": 15,
    "vigencias_activas": 8,
    "vigencias_cerradas": 7
  },
  "vigencias_recientes": [...]
}
```

### `POST /process-by-vigencias`
Procesa datos respetando vigencias específicas:
```bash
curl -X POST "http://localhost:8000/process-by-vigencias" \
  -H "Content-Type: application/json" \
  -d '{"incluir_cerradas": false}'
```

### `POST /validate-vigencias`
Valida que la lógica funcione correctamente:
```json
{
  "resultado_validacion": {
    "gestiones_fuera_vigencia": 0,    // ✅ Debe ser 0
    "gestiones_sin_campania": 0,      // ✅ Debe ser 0
    "pct_fuera_vigencia": 0.0         // ✅ Debe ser 0%
  },
  "conclusion": "VIGENCIAS CORRECTAS"
}
```

## 🚀 Ventajas de esta Implementación

### ✅ **Precisión Temporal**
- Cada gestión está vinculada a la vigencia exacta de su campaña
- No hay "contaminación" entre campañas diferentes
- Respeta los ciclos de gestión reales del negocio

### ✅ **Flexibilidad de Carteras**
- Maneja cod_lunas en múltiples carteras simultáneamente
- Respeta vigencias específicas de cada cartera
- Permite análisis granular por campaña

### ✅ **Atribución Precisa**
- Pagos se atribuyen considerando vigencias activas
- Evita atribuciones incorrectas a campañas cerradas
- Mantiene trazabilidad completa

### ✅ **Validación Automática**
- Sistema auto-valida que no haya gestiones fuera de vigencia
- Reporta problemas de consistencia
- Garantiza integridad de datos

## 🔧 Cómo Probar la Lógica

```bash
# 1. Verificar vigencias activas
curl http://localhost:8000/vigencias-status

# 2. Procesar datos con vigencias
curl -X POST http://localhost:8000/process-by-vigencias

# 3. Validar lógica de vigencias
curl -X POST http://localhost:8000/validate-vigencias

# 4. Verificar que gestiones_fuera_vigencia = 0
```

## 📝 Conclusión

**SÍ, los rangos de fechas están completamente regidos por las vigencias del calendario_v2.**

El sistema **FACO Weekly v2.1.0** implementa esta lógica correctamente:
- ✅ No usa fechas arbitrarias
- ✅ Respeta vigencias específicas por campaña  
- ✅ Valida consistencia automáticamente
- ✅ Maneja casos complejos (cod_luna en múltiples carteras)

La tabla `calendario_v2` es la **fuente de verdad** para determinar qué gestiones son válidas y en qué período.
