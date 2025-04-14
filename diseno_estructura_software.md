# Diseño de la Estructura del Software para Comparación de Nóminas

## 1. Arquitectura General

### 1.1 Patrón de Arquitectura
El software seguirá una arquitectura de tres capas:

1. **Capa de Presentación**
   - Interfaz gráfica de usuario (GUI)
   - Componentes de visualización de datos y gráficos
   - Formularios de entrada y configuración

2. **Capa de Lógica de Negocio**
   - Módulo de extracción y procesamiento de datos
   - Módulo de comparación y análisis
   - Módulo de gestión del calendario laboral
   - Módulo de generación de reportes y visualizaciones

3. **Capa de Datos**
   - Gestión de archivos (PDF, Excel, etc.)
   - Base de datos local (SQLite)
   - Exportación e importación de datos

### 1.2 Tecnologías Propuestas

- **Lenguaje de Programación**: Python 3.x
  - Amplio soporte para procesamiento de datos
  - Excelentes bibliotecas para GUI, análisis de datos y visualización
  - Facilidad para crear aplicaciones portables

- **Interfaz Gráfica**: PyQt6 o PySide6
  - Interfaces modernas y responsivas
  - Soporte para temas y personalización
  - Componentes avanzados para visualización de datos

- **Procesamiento de Datos**:
  - PyPDF2/pdfplumber para extracción de datos de PDF
  - pandas para manipulación y análisis de datos
  - openpyxl/xlrd para manejo de archivos Excel

- **Visualización**:
  - matplotlib para gráficos estáticos
  - plotly para gráficos interactivos
  - QCustomPlot (a través de PyQt) para integración nativa

- **Base de Datos**:
  - SQLite para almacenamiento local sin necesidad de servidor
  - SQLAlchemy como ORM para abstracción de la base de datos

- **Empaquetado**:
  - PyInstaller para crear ejecutables portables
  - cx_Freeze como alternativa para la distribución

## 2. Estructura de la Base de Datos

### 2.1 Modelo de Datos

#### Tabla: Empleados
- id_empleado (PK)
- numero_empleado
- nombre
- apellidos
- centro_coste
- nivel_salarial
- grupo_profesional
- fecha_antiguedad

#### Tabla: Nominas
- id_nomina (PK)
- id_empleado (FK)
- periodo_inicio
- periodo_fin
- fecha_emision
- total_devengos
- total_deducciones
- liquido
- fecha_importacion

#### Tabla: ConceptosNomina
- id_concepto (PK)
- id_nomina (FK)
- tipo (devengo/deducción)
- concepto
- unidades
- tarifa
- importe
- es_retroactivo

#### Tabla: Saldos
- id_saldo (PK)
- id_empleado (FK)
- fecha_evaluacion
- tipo_saldo (vacaciones, activables, etc.)
- anio
- derecho
- disfrutado
- pendiente
- unidad

#### Tabla: TiemposNomina
- id_tiempo (PK)
- id_empleado (FK)
- fecha
- tipo_tiempo
- horas
- dias_nomina
- es_recalculo

#### Tabla: CalendarioLaboral
- id_calendario (PK)
- id_empleado (FK)
- fecha
- tipo_dia (laboral, festivo, vacaciones, etc.)
- horas_teoricas
- turno
- descripcion

#### Tabla: Configuracion
- id_configuracion (PK)
- clave
- valor
- descripcion

### 2.2 Relaciones
- Un Empleado tiene muchas Nominas
- Una Nomina tiene muchos ConceptosNomina
- Un Empleado tiene muchos Saldos
- Un Empleado tiene muchos TiemposNomina
- Un Empleado tiene muchas entradas en CalendarioLaboral

## 3. Flujo de Trabajo para Comparación de Datos

### 3.1 Proceso General
1. **Importación de Datos**
   - Selección de archivos (PDF, Excel)
   - Extracción y procesamiento de datos
   - Almacenamiento en la base de datos

2. **Configuración de Parámetros**
   - Selección de periodos a comparar
   - Configuración de umbrales de desviación
   - Selección de conceptos específicos a monitorear

3. **Ejecución de Comparaciones**
   - Comparación de nóminas entre periodos
   - Verificación de correspondencia entre tiempos y conceptos de nómina
   - Validación de saldos contra registros de tiempo
   - Detección automática de desviaciones

4. **Visualización de Resultados**
   - Presentación de desviaciones detectadas
   - Generación de gráficos comparativos
   - Resúmenes por periodos (mensual, anual)

5. **Generación de Informes**
   - Exportación de resultados
   - Creación de reportes detallados
   - Guardado de configuraciones para futuras comparaciones

### 3.2 Algoritmos de Comparación

#### Comparación de Nóminas
- Comparación de conceptos individuales entre periodos
- Detección de variaciones porcentuales significativas
- Identificación de conceptos faltantes o nuevos
- Análisis de retroactividad y su impacto

#### Verificación de Tiempos
- Correlación entre horas registradas y pagadas
- Validación de nocturnidad, festivos y otros conceptos especiales
- Comprobación de recálculos de periodos anteriores

#### Validación de Saldos
- Verificación de acumulados contra registros individuales
- Seguimiento de evolución de saldos (vacaciones, horas, etc.)
- Detección de inconsistencias en derechos y disfrutes

## 4. Interfaz de Usuario

### 4.1 Componentes Principales

#### Pantalla Principal
- Barra de herramientas con acciones principales
- Panel de navegación entre módulos
- Área de trabajo principal
- Barra de estado con información contextual

#### Módulo de Importación
- Selector de archivos
- Visualizador de contenido
- Opciones de mapeo de datos
- Progreso de importación

#### Módulo de Calendario
- Vista de calendario mensual/anual
- Editor de tipos de día
- Importador de calendarios externos
- Configuración de patrones (turnos, etc.)

#### Módulo de Comparación
- Selector de periodos y empleados
- Configuración de parámetros de comparación
- Visualización de resultados
- Filtros de desviaciones

#### Módulo de Visualización
- Selector de tipo de gráfico
- Configuración de métricas y dimensiones
- Área de visualización interactiva
- Opciones de exportación

### 4.2 Flujo de Navegación
- Diseño intuitivo con flujo lineal para tareas comunes
- Acceso rápido a funciones frecuentes
- Asistentes guiados para operaciones complejas
- Sistema de pestañas para trabajar con múltiples vistas

## 5. Consideraciones Técnicas

### 5.1 Rendimiento
- Optimización para archivos PDF grandes
- Indexación eficiente de la base de datos
- Procesamiento por lotes para operaciones masivas
- Caché de resultados frecuentes

### 5.2 Portabilidad
- Empaquetado completo con todas las dependencias
- Minimización de requisitos externos
- Configuración automática en primer uso
- Gestión de rutas relativas

### 5.3 Seguridad
- Encriptación de datos sensibles
- Sin transmisión de datos a servidores externos
- Protección básica con contraseña (opcional)
- Respaldo y restauración de datos

### 5.4 Extensibilidad
- Arquitectura modular para facilitar extensiones
- Sistema de plugins para funcionalidades adicionales
- Configuración personalizable de reglas de comparación
- Soporte para formatos adicionales en el futuro
