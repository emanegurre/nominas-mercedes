# Comparador de Nóminas

## Descripción
Software para Windows 11 que permite comparar nóminas, saldos y tiempos de nómina. Facilita la detección de errores, análisis de desviaciones y predicción de nóminas futuras.

## Características Principales
- Comparación automática de nóminas, saldos y tiempos
- Calendario laboral personalizable
- Cálculo de precio por hora y desglose de pluses
- Predicción de nóminas basada en el calendario laboral
- Gestión de incrementos salariales y pagas extras
- Comparación entre nóminas de diferentes empleados
- Visualizaciones gráficas y generación de informes
- Entrada manual de datos para simulaciones

## Requisitos del Sistema
- Sistema Operativo: Windows 11
- Python 3.8 o superior
- Bibliotecas Python: PyQt5, pandas, numpy, matplotlib, PyPDF2, openpyxl

## Instalación

### Opción 1: Ejecutar directamente desde Python
1. Instalar Python 3.8 o superior desde [python.org](https://www.python.org/downloads/)
2. Instalar las bibliotecas requeridas:
   ```
   pip install PyQt5 pandas numpy matplotlib PyPDF2 openpyxl
   ```
3. Ejecutar el programa:
   ```
   python interfaz_usuario.py
   ```

### Opción 2: Crear un ejecutable con PyInstaller
1. Instalar PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Crear el ejecutable:
   ```
   pyinstaller --onefile --windowed --icon=icon.ico interfaz_usuario.py
   ```
3. Alternativamente puede ejecutar:
   ```
   python build_exe.py
   ```
   Este script utiliza el archivo `interfaz_usuario.spec` incluido para
   generar el ejecutable automáticamente.
4. El ejecutable se creará en la carpeta `dist`

### Opción 3: Crear un instalador con Inno Setup
1. Crear el ejecutable con PyInstaller (ver Opción 2)
2. Descargar e instalar [Inno Setup](https://jrsoftware.org/isdl.php)
3. Abrir el archivo `inno_setup_script.iss` con Inno Setup
4. Compilar el script para generar el instalador `ComparadorNominas_Setup.exe`

## Estructura de Archivos
- `interfaz_usuario.py`: Punto de entrada principal del programa
- `implementacion_comparacion.py`: Módulo de comparación de nóminas, saldos y tiempos
- `implementacion_precio_hora.py`: Cálculo de precio por hora y desglose de pluses
- `implementacion_prediccion_nomina.py`: Sistema de predicción de nóminas
- `implementacion_calendario_laboral.py`: Gestión del calendario laboral
- `implementacion_incrementos_salariales.py`: Gestión de incrementos salariales
- `implementacion_pagas_extras.py`: Gestión de pagas extras
- `implementacion_comparacion_nominas_empleados.py`: Comparación entre empleados
- `implementacion_visualizaciones_graficas.py`: Visualizaciones gráficas
- `implementacion_entrada_manual_datos.py`: Entrada manual de datos
- `implementacion_informes_personalizados.py`: Generación de informes
- `docs/`: Documentación del software
  - `guia_usuario.md`: Guía detallada para usuarios
  - `documentacion_tecnica.md`: Documentación técnica para desarrolladores
- `ejemplos/`: Archivos de ejemplo para pruebas

## Uso Básico
1. Importar archivos PDF o Excel de nóminas, saldos y tiempos
2. Configurar el calendario laboral con días festivos, vacaciones, etc.
3. Comparar nóminas entre diferentes periodos o con otros empleados
4. Generar predicciones de nóminas futuras
5. Crear informes personalizados con las comparaciones y desviaciones

## Personalización
El software es completamente editable, permitiendo:
- Modificar manualmente cualquier dato
- Configurar parámetros de cálculo
- Personalizar visualizaciones gráficas
- Adaptar informes a necesidades específicas

## Documentación
Para información detallada sobre el uso del software, consulte la Guía de Usuario en `docs/guia_usuario.md`.
Para información técnica sobre la arquitectura y componentes, consulte la Documentación Técnica en `docs/documentacion_tecnica.md`.

## Soporte
Para cualquier consulta o problema, contacte con el desarrollador.
