# FACO Weekly v2.0 - Lógica Avanzada Implementada

## 🆕 Actualización Mayor: Homologación Completa

Sistema actualizado con la lógica avanzada de gestiones unificadas y homologación completa según el query proporcionado.

---

## 🔄 Cambios Principales

### 1. **Gestiones Unificadas (CALL + VOICEBOT)**
- **Antes**: Queries separados para mibotair y voicebot
- **Ahora**: Query unificado con lógica CTE avanzada
- **Beneficio**: Homologación consistente entre canales

```sql
-- Nueva estructura unificada
WITH gestiones_unificadas AS (
  SELECT date, cod_luna, canal, ejecutivo, dni_ejecutivo, ...
  FROM mibotair + usuarios UNION ALL voicebot
)
```

### 2. **Tablas de Homologación Integradas**
- ✅ `homologacion_P3fV4dWNeMkN5RJMhV8e_usuarios` - Mapeo correo → nombre/DNI
- ✅ `homologacion_P3fV4dWNeMkN5RJMhV8e_v2` - Tipificaciones CALL (n1,n2,n3)
- ✅ `homologacion_P3fV4dWNeMkN5RJMhV8e_voicebot` - Tipificaciones VOICEBOT
- ✅ `dash_P3fV4dWNeMkN5RJMhV8e_fact_asignacion` - Fact con monto_exigible

### 3. **DNI de Ejecutivos**
- **CALL**: DNI real desde tabla de usuarios
- **VOICEBOT**: DNI ficticio '99999999'
- **Mapeo**: correo_agente → usuario → dni + nombre_apellidos

### 4. **Lógica de Monto Compromiso**
```sql
-- Nueva regla implementada
CASE
  WHEN es_pdp = 'SI' THEN monto_exigible
  ELSE 0
END AS monto_compromiso
```

### 5. **Homologación Robusta**
- **Contactabilidad**: Homologada por tabla específica de cada canal
- **PDP**: Lógica unificada (SI/NO)
- **Peso**: Desde tablas de homologación
- **n1,n2,n3**: Homologados para VOICEBOT

---

## 🚀 Nuevos Endpoints

### GET `/homologation-status`
Verifica estado de todas las tablas de homologación
```json
{
  "tablas_homologacion": {
    "usuarios": 150,
    "call_homolog": 45,
    "bot_homolog": 12,
    "fact_asignacion": 58654
  }
}
```

### POST `/process-advanced`
Procesamiento con lógica completa de homologación
- Gestiones unificadas
- Análisis de problemas de homologación
- KPIs avanzados por canal
- Ranking con DNI y scores

---

## 📊 Nuevas Métricas y Análisis

### **Problemas de Homologación Detectados**
- Gestiones NO_HOMOLOGADO
- Ejecutivos sin DNI
- Agentes no identificados
- Gestiones con peso cero

### **KPIs Avanzados**
- Tasa contactabilidad efectiva por canal
- Tasa PDP (Promesa de Pago)
- Monto total compromisos
- Ticket promedio compromiso
- Cobertura de gestión vs universo asignado

### **Ranking de Ejecutivos Mejorado**
- DNI real de ejecutivos
- Score de productividad compuesto
- Métricas por canal
- Intensidad en minutos
- Peso promedio de gestiones

---

## 🔧 Uso del Sistema Actualizado

### **Instalación y Setup**
```bash
git clone https://github.com/reyer3/faco_weekly.git
cd faco_weekly
./start.sh
```

### **Comandos de Prueba Actualizados**
```bash
# Verificar homologación
python test_api.py homolog

# Procesamiento avanzado
python test_api.py advanced 2025-06-01 2025-06-12

# Suite completa de tests
python test_api.py full
```

### **API Calls Nuevos**
```bash
# Estado de homologación
curl http://localhost:8000/homologation-status

# Procesamiento avanzado
curl -X POST "http://localhost:8000/process-advanced" \
  -H "Content-Type: application/json" \
  -d '{"fecha_inicio": "2025-06-01", "fecha_fin": "2025-06-12"}'
```

---

## 📈 Salida del Sistema Avanzado

### **Ejemplo de Respuesta**
```json
{
  "version": "2.0.0",
  "homologacion": {
    "problemas_detectados": {
      "total_gestiones": 45230,
      "no_homologadas": 120,
      "no_homologadas_pct": 0.27,
      "sin_dni": 15,
      "ejecutivos_sin_identificar": 8
    }
  },
  "kpis_avanzados": {
    "kpis_generales": {
      "tasa_contactabilidad_efectiva": 45.2,
      "tasa_pdp": 32.1,
      "monto_total_compromisos": 2450000.50,
      "cobertura_gestion": 78.5
    }
  },
  "ranking_ejecutivos": [
    {
      "ejecutivo": "JUAN PEREZ LOPEZ",
      "dni_ejecutivo": "12345678",
      "canal": "CALL",
      "productividad_score": 87.5,
      "monto_comprometido": 150000.00
    }
  ]
}
```

---

## 🎯 Beneficios de la Actualización

### **Para Analistas**
- Datos completamente homologados
- Métricas consistentes entre canales
- Identificación clara de problemas

### **Para Gerentes**
- Ranking preciso de ejecutivos
- Scores de productividad compuestos
- Cobertura real de gestión

### **Para TI**
- Lógica centralizada en SQL
- Detección automática de issues
- Fácil debugging con endpoints dedicados

---

## ⚠️ Consideraciones Importantes

### **Dependencias**
- Todas las tablas de homologación deben existir
- Mapeo usuarios actualizado
- fact_asignacion con monto_exigible válido

### **Performance**
- Query más complejo (CTE con múltiples JOINs)
- Timeout aumentado a 3 minutos
- Caching recomendado para producción

### **Validaciones**
- Sistema detecta automáticamente problemas
- Reporta % de gestiones no homologadas
- Alertas de ejecutivos sin identificar

---

## 🔄 Migración desde v1.0

### **Endpoints Mantenidos**
- `/health` - Actualizado con estado de homologación
- `/` - Info actualizada con nuevas características

### **Endpoints Nuevos**
- `/homologation-status` - Estado de tablas
- `/process-advanced` - Procesamiento completo

### **Compatibilidad**
- Tests antiguos siguen funcionando
- Estructura de respuesta expandida
- Nuevos campos agregados sin romper existentes

---

## 📞 Próximos Pasos

1. **Probar sistema avanzado**: `python test_api.py full`
2. **Verificar homologación**: Revisar % de gestiones no homologadas
3. **Validar ejecutivos**: Confirmar mapeo DNI correcto
4. **Generar reportes**: Usar KPIs avanzados para reportes ejecutivos

---

**🎉 Sistema FACO Weekly v2.0 listo para producción con lógica completa de homologación**
