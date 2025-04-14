# Documentación Técnica - Software de Comparación de Nóminas

## Arquitectura del Sistema

El Software de Comparación de Nóminas está desarrollado con una arquitectura de tres capas:

1. **Capa de Presentación**: Interfaz gráfica desarrollada con PyQt5
2. **Capa de Lógica de Negocio**: Módulos Python para procesamiento y análisis
3. **Capa de Datos**: Sistema de almacenamiento basado en SQLite

### Diagrama de Componentes

```
+----------------------------------+
|        Interfaz de Usuario       |
|  (PyQt5, Matplotlib, QtCharts)   |
+----------------------------------+
                 |
+----------------------------------+
|       Lógica de Negocio          |
|                                  |
| +------------+ +---------------+ |
| | Extracción | | Comparación   | |
| | de Datos   | | de Nóminas    | |
| +------------+ +---------------+ |
|                                  |
| +------------+ +---------------+ |
| | Predicción | | Calendario    | |
| | de Nóminas | | Laboral       | |
| +------------+ +---------------+ |
|                                  |
| +------------+ +---------------+ |
| | Gestión de | | Generación de | |
| | Incrementos| | Informes      | |
| +------------+ +---------------+ |
+----------------------------------+
                 |
+----------------------------------+
|         Capa de Datos            |
|        (SQLite, JSON)            |
+----------------------------------+
```

## Requisitos del Sistema

### Requisitos de Hardware
- Procesador: 1.6 GHz o superior
- Memoria RAM: 4GB mínimo (8GB recomendado)
- Espacio en disco: 500MB
- Resolución de pantalla: 1366x768 o superior

### Requisitos de Software
- Sistema Operativo: Windows 11
- Python 3.8 o superior (incluido en el instalador)
- Bibliotecas Python (incluidas en el instalador):
  - PyQt5
  - Pandas
  - NumPy
  - Matplotlib
  - PyPDF2
  - openpyxl
  - SQLite3

## Estructura de la Base de Datos

El software utiliza una base de datos SQLite con la siguiente estructura:

### Tabla: Empleados
```sql
CREATE TABLE Empleados (
    id_empleado INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    categoria TEXT,
    fecha_alta DATE,
    configuracion TEXT
);
```

### Tabla: Nominas
```sql
CREATE TABLE Nominas (
    id_nomina INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    periodo TEXT NOT NULL,
    fecha_nomina DATE,
    bruto REAL,
    neto REAL,
    datos_json TEXT,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### Tabla: Conceptos
```sql
CREATE TABLE Conceptos (
    id_concepto INTEGER PRIMARY KEY,
    id_nomina INTEGER,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    valor REAL,
    FOREIGN KEY (id_nomina) REFERENCES Nominas(id_nomina)
);
```

### Tabla: Saldos
```sql
CREATE TABLE Saldos (
    id_saldo INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    fecha DATE NOT NULL,
    valor REAL,
    tipo TEXT,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### Tabla: Tiempos
```sql
CREATE TABLE Tiempos (
    id_tiempo INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    fecha DATE NOT NULL,
    horas REAL,
    tipo TEXT,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### Tabla: Calendario
```sql
CREATE TABLE Calendario (
    id_dia INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    fecha DATE NOT NULL,
    tipo TEXT NOT NULL,
    turno TEXT,
    horas REAL,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### Tabla: Incrementos
```sql
CREATE TABLE Incrementos (
    id_incremento INTEGER PRIMARY KEY,
    concepto TEXT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    porcentaje REAL NOT NULL,
    retroactivo BOOLEAN
);
```

### Tabla: PagasExtras
```sql
CREATE TABLE PagasExtras (
    id_paga INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    tipo TEXT NOT NULL,
    fecha DATE NOT NULL,
    bruto REAL,
    neto REAL,
    datos_json TEXT,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### Tabla: Predicciones
```sql
CREATE TABLE Predicciones (
    id_prediccion INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    periodo TEXT NOT NULL,
    fecha_creacion DATE,
    bruto REAL,
    neto REAL,
    datos_json TEXT,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### Tabla: Informes
```sql
CREATE TABLE Informes (
    id_informe INTEGER PRIMARY KEY,
    id_empleado INTEGER,
    tipo TEXT NOT NULL,
    fecha_creacion DATE,
    parametros TEXT,
    ruta_archivo TEXT,
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

## Módulos Principales

### 1. Extracción de Datos
Este módulo se encarga de extraer información de archivos PDF y Excel.

#### Clases Principales:
- `PDFExtractor`: Extrae datos de archivos PDF
- `ExcelExtractor`: Extrae datos de archivos Excel
- `DataMapper`: Mapea los datos extraídos a la estructura interna

### 2. Comparación de Nóminas
Este módulo implementa la lógica para comparar nóminas, saldos y tiempos.

#### Clases Principales:
- `NominaComparator`: Compara nóminas entre diferentes periodos
- `SaldoComparator`: Compara saldos entre diferentes periodos
- `TiempoComparator`: Compara tiempos entre diferentes periodos
- `EmpleadoComparator`: Compara nóminas entre diferentes empleados

### 3. Precio por Hora y Pluses
Este módulo calcula el precio por hora y desglosa los pluses.

#### Clases Principales:
- `PrecioHoraCalculator`: Calcula el precio por hora base y efectivo
- `PlusAnalyzer`: Analiza y desglosa los diferentes pluses

### 4. Predicción de Nóminas
Este módulo implementa la lógica para predecir nóminas futuras.

#### Clases Principales:
- `NominaPredictor`: Predice nóminas basándose en datos históricos
- `ScenarioSimulator`: Simula diferentes escenarios de nóminas

### 5. Calendario Laboral
Este módulo gestiona el calendario laboral personalizable.

#### Clases Principales:
- `CalendarioManager`: Gestiona la creación y edición de calendarios
- `TurnoManager`: Gestiona los diferentes turnos
- `PatronManager`: Gestiona los patrones de turnos

### 6. Incrementos Salariales
Este módulo gestiona los incrementos salariales.

#### Clases Principales:
- `IncrementoManager`: Gestiona los incrementos salariales
- `RetroactivoCalculator`: Calcula los importes retroactivos

### 7. Pagas Extras
Este módulo gestiona las pagas extras.

#### Clases Principales:
- `PagaExtraManager`: Gestiona las diferentes pagas extras
- `PagaExtraCalculator`: Calcula los importes de las pagas extras

### 8. Visualizaciones Gráficas
Este módulo implementa las diferentes visualizaciones gráficas.

#### Clases Principales:
- `EvolucionChart`: Genera gráficas de evolución temporal
- `DistribucionChart`: Genera gráficas de distribución
- `ComparacionChart`: Genera gráficas de comparación

### 9. Generación de Informes
Este módulo implementa la generación de informes personalizados.

#### Clases Principales:
- `InformeGenerator`: Genera diferentes tipos de informes
- `PDFExporter`: Exporta informes a formato PDF
- `ExcelExporter`: Exporta informes a formato Excel

### 10. Interfaz de Usuario
Este módulo implementa la interfaz gráfica de usuario.

#### Clases Principales:
- `MainWindow`: Ventana principal de la aplicación
- `ImportTab`: Pestaña de importación de datos
- `CalendarioTab`: Pestaña de gestión del calendario
- `ComparacionTab`: Pestaña de comparación de nóminas
- `PrediccionTab`: Pestaña de predicción de nóminas
- `InformeTab`: Pestaña de generación de informes
- `ConfiguracionTab`: Pestaña de configuración

## Flujos de Trabajo Principales

### 1. Importación de Datos
```
1. Usuario selecciona archivo (PDF/Excel)
2. PDFExtractor/ExcelExtractor extrae datos
3. DataMapper mapea datos a estructura interna
4. Datos se almacenan en la base de datos
```

### 2. Comparación de Nóminas
```
1. Usuario selecciona nóminas a comparar
2. NominaComparator compara conceptos
3. Se identifican diferencias y desviaciones
4. Se generan visualizaciones con ComparacionChart
5. Se muestra resultado al usuario
```

### 3. Predicción de Nóminas
```
1. Usuario configura parámetros de predicción
2. NominaPredictor obtiene datos históricos
3. Se aplican incrementos y ajustes del calendario
4. Se genera predicción de nómina
5. Se muestra resultado al usuario
```

### 4. Generación de Informes
```
1. Usuario selecciona tipo de informe
2. InformeGenerator recopila datos necesarios
3. Se generan visualizaciones con módulo de gráficas
4. PDFExporter/ExcelExporter crea archivo de informe
5. Se guarda informe y se muestra al usuario
```

## Extensibilidad

El software está diseñado para ser fácilmente extensible:

### Nuevos Tipos de Documentos
Para añadir soporte para nuevos tipos de documentos:
1. Crear nueva clase de extractor que implemente la interfaz `IExtractor`
2. Registrar el nuevo extractor en el `ExtractorFactory`

### Nuevos Tipos de Informes
Para añadir nuevos tipos de informes:
1. Crear nueva clase de generador que implemente la interfaz `IInformeGenerator`
2. Registrar el nuevo generador en el `InformeGeneratorFactory`

### Nuevas Visualizaciones
Para añadir nuevas visualizaciones:
1. Crear nueva clase de gráfica que implemente la interfaz `IChart`
2. Registrar la nueva gráfica en el `ChartFactory`

## Seguridad

El software implementa las siguientes medidas de seguridad:

1. **Protección de Datos**: Los datos sensibles se almacenan cifrados en la base de datos
2. **Validación de Entrada**: Todas las entradas de usuario son validadas para prevenir inyecciones SQL
3. **Control de Acceso**: Sistema de perfiles de usuario con diferentes niveles de acceso
4. **Auditoría**: Registro de todas las operaciones críticas para facilitar la trazabilidad

## Rendimiento

El software está optimizado para ofrecer un buen rendimiento:

1. **Indexación**: Las tablas de la base de datos están correctamente indexadas
2. **Caché**: Se implementa un sistema de caché para operaciones frecuentes
3. **Procesamiento Asíncrono**: Las operaciones largas se ejecutan en hilos separados
4. **Carga Diferida**: Los datos se cargan solo cuando son necesarios

## Mantenimiento

Para facilitar el mantenimiento del software:

1. **Logs**: Sistema completo de logs para facilitar la depuración
2. **Modularidad**: Código organizado en módulos independientes
3. **Pruebas Unitarias**: Cobertura completa de pruebas unitarias
4. **Documentación**: Código documentado siguiendo estándares

## Instalación y Despliegue

### Proceso de Instalación
1. Ejecutar el instalador `ComparadorNominas_Setup.exe`
2. Seguir las instrucciones del asistente
3. El instalador configurará automáticamente:
   - Python y bibliotecas necesarias
   - Base de datos SQLite
   - Accesos directos

### Actualización
1. El software comprueba automáticamente si hay actualizaciones disponibles
2. Si hay una actualización, se descarga e instala automáticamente
3. Se realiza una copia de seguridad de los datos antes de la actualización

## Soporte y Contacto

Para soporte técnico o consultas sobre el desarrollo:

- Correo electrónico: desarrollo@comparadornominas.com
- Teléfono: +34 900 123 456
- Horario de atención: Lunes a Viernes, 9:00 - 18:00

---

Esta documentación técnica está destinada a desarrolladores y personal técnico. Para información sobre el uso del software, consulte la Guía de Usuario.
