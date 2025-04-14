# Análisis de Archivos PDF de Nóminas, Saldos y Tiempos

## Resumen General
He analizado los tres archivos PDF proporcionados:
1. **nominas all_redacted.pdf** (76 páginas)
2. **saldos all_redacted.pdf** (38 páginas)
3. **tiempos nominas all_redacted.pdf** (79 páginas)

## Estructura de los Archivos

### Archivo de Nóminas
- Contiene información detallada sobre salarios, deducciones y pagos
- Incluye conceptos como:
  - Salario base
  - Antigüedad
  - Primas (Directa, Calidad)
  - Nocturnidad
  - Plus por trabajo en días festivos
  - Deducciones (IRPF, Seguridad Social, etc.)
  - Pagos en especie
- Muestra periodos de liquidación mensuales
- Incluye información del empleado (número, nivel salarial, centro de coste)

### Archivo de Saldos
- Muestra resúmenes de saldos de tiempo por empleado
- Incluye información sobre:
  - Vacaciones (derecho, disfrutado, pendiente)
  - Activables de producción
  - Cuentas de tiempos (horas acumuladas)
- Los saldos están referenciados a fechas específicas (último día evaluado)
- Organizado por centro de coste

### Archivo de Tiempos de Nóminas
- Detalla los tiempos utilizados en el cálculo de la nómina
- Incluye:
  - Periodos específicos (mensual)
  - Datos de tiempos (nocturnidad, reducción de tiempo)
  - Recálculos de meses anteriores
  - Horas trabajadas por periodo
  - Nivel de rendimiento y grado de ocupación
- Organizado por centro de coste y empleado

## Relaciones entre los Archivos
- Los tres archivos comparten información del empleado y centro de coste
- El archivo de tiempos proporciona datos que se reflejan en conceptos de la nómina
- Los saldos muestran acumulados que se relacionan con los tiempos trabajados

## Posibles Funcionalidades para el Software
1. Comparación de nóminas entre periodos
2. Verificación de cálculos (horas trabajadas vs pagadas)
3. Seguimiento de saldos de vacaciones y tiempo
4. Detección de desviaciones en conceptos salariales
5. Gestión del calendario laboral personalizado
6. Visualizaciones gráficas para análisis de tendencias
7. Resúmenes por meses y años
