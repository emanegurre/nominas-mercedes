"""
Interfaz de Usuario para el Comparador de Nóminas

Este módulo implementa la interfaz gráfica de usuario para el software de comparación
de nóminas, saldos y tiempos, integrando todas las funcionalidades desarrolladas.
"""

import sys
import os
import sqlite3
from datetime import datetime, date
import calendar
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, 
                            QTableWidget, QTableWidgetItem, QLineEdit, QDateEdit, 
                            QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QFormLayout, 
                            QMessageBox, QCalendarWidget, QSplitter, QFrame, QScrollArea,
                            QRadioButton, QButtonGroup, QProgressBar, QTextEdit, QListWidget,
                            QListWidgetItem, QMenu, QAction, QToolBar, QStatusBar, QDialog,
                            QDialogButtonBox, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QDate, QDateTime, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QBrush, QCursor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Importar módulos de funcionalidad
# Nota: En una implementación real, estos imports serían de los módulos reales
# Para esta demostración, usaremos clases simuladas
class ExtractorPDF:
    """Clase simulada para extracción de datos de PDFs."""
    def extraer_datos(self, ruta_pdf):
        return {"estado": "éxito", "datos": {"conceptos": [], "importes": []}}

class ComparadorNominas:
    """Clase simulada para comparación de nóminas."""
    def comparar(self, nomina1, nomina2):
        return {"diferencias": [], "porcentaje_total": 0}

class CalculadorPrecioHora:
    """Clase simulada para cálculo de precio por hora."""
    def calcular(self, nomina, horas):
        return 15.75  # Valor simulado

class PredictorNomina:
    """Clase simulada para predicción de nóminas."""
    def predecir(self, datos_historicos, calendario):
        return {"prediccion": {"bruto": 2000, "neto": 1600}}

class GestorCalendario:
    """Clase simulada para gestión del calendario laboral."""
    def obtener_calendario(self, anio, mes):
        return {"dias": []}

class GeneradorInformes:
    """Clase simulada para generación de informes."""
    def generar_informe_nomina(self, id_nomina):
        return "/ruta/simulada/informe.pdf"

# Clase principal de la aplicación
class ComparadorNominasApp(QMainWindow):
    """Aplicación principal para comparación de nóminas."""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.setWindowTitle("Comparador de Nóminas")
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializar componentes
        self.init_ui()
        
        # Conectar a la base de datos (simulado)
        self.conectar_bd()
        
        # Inicializar módulos de funcionalidad
        self.extractor_pdf = ExtractorPDF()
        self.comparador_nominas = ComparadorNominas()
        self.calculador_precio_hora = CalculadorPrecioHora()
        self.predictor_nomina = PredictorNomina()
        self.gestor_calendario = GestorCalendario()
        self.generador_informes = GeneradorInformes()
        
        # Mostrar mensaje de bienvenida
        self.mostrar_mensaje_bienvenida()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        # Crear barra de menú
        self.crear_menu()
        
        # Crear barra de herramientas
        self.crear_toolbar()
        
        # Crear barra de estado
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Listo")
        
        # Widget central con pestañas
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Crear pestañas
        self.crear_tab_importacion()
        self.crear_tab_comparacion()
        self.crear_tab_calendario()
        self.crear_tab_prediccion()
        self.crear_tab_informes()
        self.crear_tab_configuracion()
    
    def crear_menu(self):
        """Crea la barra de menú de la aplicación."""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('Archivo')
        
        # Acciones del menú Archivo
        import_action = QAction('Importar PDF', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.importar_pdf)
        file_menu.addAction(import_action)
        
        export_action = QAction('Exportar Datos', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.exportar_datos)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Salir', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Editar
        edit_menu = menubar.addMenu('Editar')
        
        # Acciones del menú Editar
        preferences_action = QAction('Preferencias', self)
        preferences_action.triggered.connect(self.mostrar_preferencias)
        edit_menu.addAction(preferences_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('Herramientas')
        
        # Acciones del menú Herramientas
        calculator_action = QAction('Calculadora de Precio/Hora', self)
        calculator_action.triggered.connect(self.mostrar_calculadora_precio_hora)
        tools_menu.addAction(calculator_action)
        
        compare_action = QAction('Comparar Nóminas', self)
        compare_action.triggered.connect(self.comparar_nominas)
        tools_menu.addAction(compare_action)
        
        predict_action = QAction('Predecir Nómina', self)
        predict_action.triggered.connect(self.predecir_nomina)
        tools_menu.addAction(predict_action)
        
        # Menú Informes
        reports_menu = menubar.addMenu('Informes')
        
        # Acciones del menú Informes
        report_nomina_action = QAction('Informe de Nómina', self)
        report_nomina_action.triggered.connect(self.generar_informe_nomina)
        reports_menu.addAction(report_nomina_action)
        
        report_comparison_action = QAction('Informe de Comparación', self)
        report_comparison_action.triggered.connect(self.generar_informe_comparacion)
        reports_menu.addAction(report_comparison_action)
        
        report_deviations_action = QAction('Informe de Desviaciones', self)
        report_deviations_action.triggered.connect(self.generar_informe_desviaciones)
        reports_menu.addAction(report_deviations_action)
        
        report_calendar_action = QAction('Informe de Calendario', self)
        report_calendar_action.triggered.connect(self.generar_informe_calendario)
        reports_menu.addAction(report_calendar_action)
        
        report_prediction_action = QAction('Informe de Predicción', self)
        report_prediction_action.triggered.connect(self.generar_informe_prediccion)
        reports_menu.addAction(report_prediction_action)
        
        report_complete_action = QAction('Informe Completo', self)
        report_complete_action.triggered.connect(self.generar_informe_completo)
        reports_menu.addAction(report_complete_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('Ayuda')
        
        # Acciones del menú Ayuda
        help_action = QAction('Manual de Usuario', self)
        help_action.triggered.connect(self.mostrar_ayuda)
        help_menu.addAction(help_action)
        
        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.mostrar_acerca_de)
        help_menu.addAction(about_action)
    
    def crear_toolbar(self):
        """Crea la barra de herramientas de la aplicación."""
        toolbar = QToolBar("Barra de Herramientas Principal")
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Acciones de la barra de herramientas
        import_action = QAction('Importar', self)
        import_action.triggered.connect(self.importar_pdf)
        toolbar.addAction(import_action)
        
        compare_action = QAction('Comparar', self)
        compare_action.triggered.connect(self.comparar_nominas)
        toolbar.addAction(compare_action)
        
        calendar_action = QAction('Calendario', self)
        calendar_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addAction(calendar_action)
        
        predict_action = QAction('Predecir', self)
        predict_action.triggered.connect(self.predecir_nomina)
        toolbar.addAction(predict_action)
        
        report_action = QAction('Informes', self)
        report_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        toolbar.addAction(report_action)
    
    def crear_tab_importacion(self):
        """Crea la pestaña de importación de datos."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Importación de Datos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Sección de importación de PDFs
        grupo_importacion = QGroupBox("Importar archivos PDF")
        grupo_layout = QVBoxLayout()
        
        # Botones de importación
        btn_layout = QHBoxLayout()
        
        btn_importar_nomina = QPushButton("Importar Nómina")
        btn_importar_nomina.clicked.connect(lambda: self.importar_pdf("nomina"))
        btn_layout.addWidget(btn_importar_nomina)
        
        btn_importar_saldos = QPushButton("Importar Saldos")
        btn_importar_saldos.clicked.connect(lambda: self.importar_pdf("saldos"))
        btn_layout.addWidget(btn_importar_saldos)
        
        btn_importar_tiempos = QPushButton("Importar Tiempos")
        btn_importar_tiempos.clicked.connect(lambda: self.importar_pdf("tiempos"))
        btn_layout.addWidget(btn_importar_tiempos)
        
        grupo_layout.addLayout(btn_layout)
        
        # Lista de archivos importados
        self.lista_archivos = QListWidget()
        grupo_layout.addWidget(self.lista_archivos)
        
        grupo_importacion.setLayout(grupo_layout)
        layout.addWidget(grupo_importacion)
        
        # Sección de entrada manual
        grupo_manual = QGroupBox("Entrada Manual de Datos")
        grupo_manual_layout = QVBoxLayout()
        
        btn_entrada_manual = QPushButton("Abrir Editor de Datos")
        btn_entrada_manual.clicked.connect(self.abrir_editor_datos)
        grupo_manual_layout.addWidget(btn_entrada_manual)
        
        grupo_manual.setLayout(grupo_manual_layout)
        layout.addWidget(grupo_manual)
        
        # Botón de procesar
        btn_procesar = QPushButton("Procesar Datos")
        btn_procesar.clicked.connect(self.procesar_datos)
        layout.addWidget(btn_procesar)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Importación")
    
    def crear_tab_comparacion(self):
        """Crea la pestaña de comparación de datos."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Comparación de Datos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Sección de selección de nóminas
        grupo_seleccion = QGroupBox("Seleccionar Nóminas para Comparar")
        grupo_layout = QFormLayout()
        
        # Primera nómina
        self.combo_nomina1 = QComboBox()
        self.combo_nomina1.addItem("Seleccione una nómina...")
        grupo_layout.addRow("Nómina 1:", self.combo_nomina1)
        
        # Segunda nómina
        self.combo_nomina2 = QComboBox()
        self.combo_nomina2.addItem("Seleccione una nómina...")
        grupo_layout.addRow("Nómina 2:", self.combo_nomina2)
        
        # Opciones de comparación
        self.check_mostrar_todos = QCheckBox("Mostrar todos los conceptos")
        self.check_mostrar_todos.setChecked(True)
        grupo_layout.addRow("Opciones:", self.check_mostrar_todos)
        
        self.check_destacar_diferencias = QCheckBox("Destacar diferencias significativas")
        self.check_destacar_diferencias.setChecked(True)
        grupo_layout.addRow("", self.check_destacar_diferencias)
        
        # Botón de comparar
        btn_comparar = QPushButton("Comparar")
        btn_comparar.clicked.connect(self.comparar_nominas)
        grupo_layout.addRow("", btn_comparar)
        
        grupo_seleccion.setLayout(grupo_layout)
        layout.addWidget(grupo_seleccion)
        
        # Sección de resultados
        grupo_resultados = QGroupBox("Resultados de la Comparación")
        grupo_resultados_layout = QVBoxLayout()
        
        # Tabla de resultados
        self.tabla_comparacion = QTableWidget(0, 4)
        self.tabla_comparacion.setHorizontalHeaderLabels(["Concepto", "Nómina 1", "Nómina 2", "Diferencia"])
        self.tabla_comparacion.horizontalHeader().setStretchLastSection(True)
        grupo_resultados_layout.addWidget(self.tabla_comparacion)
        
        # Área para gráfico
        self.frame_grafico_comparacion = QFrame()
        self.frame_grafico_comparacion.setFrameShape(QFrame.StyledPanel)
        self.frame_grafico_comparacion.setMinimumHeight(300)
        grupo_resultados_layout.addWidget(self.frame_grafico_comparacion)
        
        # Layout para el gráfico
        grafico_layout = QVBoxLayout(self.frame_grafico_comparacion)
        
        # Canvas para matplotlib
        self.figura_comparacion = Figure(figsize=(5, 4), dpi=100)
        self.canvas_comparacion = FigureCanvas(self.figura_comparacion)
        grafico_layout.addWidget(self.canvas_comparacion)
        
        grupo_resultados.setLayout(grupo_resultados_layout)
        layout.addWidget(grupo_resultados)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        btn_exportar = QPushButton("Exportar Resultados")
        btn_exportar.clicked.connect(self.exportar_resultados_comparacion)
        btn_layout.addWidget(btn_exportar)
        
        btn_informe = QPushButton("Generar Informe")
        btn_informe.clicked.connect(self.generar_informe_comparacion)
        btn_layout.addWidget(btn_informe)
        
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Comparación")
    
    def crear_tab_calendario(self):
        """Crea la pestaña de calendario laboral."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Calendario Laboral")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Sección de selección de año y mes
        seleccion_layout = QHBoxLayout()
        
        # Selector de año
        seleccion_layout.addWidget(QLabel("Año:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2020, 2050)
        self.spin_anio.setValue(datetime.now().year)
        self.spin_anio.valueChanged.connect(self.actualizar_calendario)
        seleccion_layout.addWidget(self.spin_anio)
        
        # Selector de mes
        seleccion_layout.addWidget(QLabel("Mes:"))
        self.combo_mes = QComboBox()
        for i in range(1, 13):
            self.combo_mes.addItem(calendar.month_name[i], i)
        self.combo_mes.setCurrentIndex(datetime.now().month - 1)
        self.combo_mes.currentIndexChanged.connect(self.actualizar_calendario)
        seleccion_layout.addWidget(self.combo_mes)
        
        # Botón de hoy
        btn_hoy = QPushButton("Hoy")
        btn_hoy.clicked.connect(self.ir_a_hoy)
        seleccion_layout.addWidget(btn_hoy)
        
        seleccion_layout.addStretch()
        
        layout.addLayout(seleccion_layout)
        
        # Splitter para dividir el calendario y los detalles
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Calendario
        panel_calendario = QWidget()
        panel_calendario_layout = QVBoxLayout(panel_calendario)
        
        self.calendario_widget = QCalendarWidget()
        self.calendario_widget.selectionChanged.connect(self.actualizar_detalles_dia)
        panel_calendario_layout.addWidget(self.calendario_widget)
        
        # Leyenda de tipos de día
        grupo_leyenda = QGroupBox("Leyenda")
        grupo_leyenda_layout = QGridLayout()
        
        tipos_dia = [
            ("Laborable", "#FFFFFF"),
            ("Festivo", "#FFD0D0"),
            ("Vacaciones", "#D0FFD0"),
            ("Licencia", "#D0D0FF"),
            ("Baja", "#FFFFD0")
        ]
        
        for i, (tipo, color) in enumerate(tipos_dia):
            label_color = QLabel()
            label_color.setFixedSize(20, 20)
            label_color.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
            grupo_leyenda_layout.addWidget(label_color, i // 3, (i % 3) * 2)
            
            label_texto = QLabel(tipo)
            grupo_leyenda_layout.addWidget(label_texto, i // 3, (i % 3) * 2 + 1)
        
        grupo_leyenda.setLayout(grupo_leyenda_layout)
        panel_calendario_layout.addWidget(grupo_leyenda)
        
        splitter.addWidget(panel_calendario)
        
        # Panel derecho: Detalles del día
        panel_detalles = QWidget()
        panel_detalles_layout = QVBoxLayout(panel_detalles)
        
        grupo_detalles = QGroupBox("Detalles del Día")
        grupo_detalles_layout = QFormLayout()
        
        self.label_fecha = QLabel()
        grupo_detalles_layout.addRow("Fecha:", self.label_fecha)
        
        self.combo_tipo_dia = QComboBox()
        self.combo_tipo_dia.addItems(["Laborable", "Festivo", "Vacaciones", "Licencia", "Baja"])
        grupo_detalles_layout.addRow("Tipo de día:", self.combo_tipo_dia)
        
        self.combo_turno = QComboBox()
        self.combo_turno.addItems(["Mañana", "Tarde", "Noche", "Partido", "Libre"])
        grupo_detalles_layout.addRow("Turno:", self.combo_turno)
        
        self.spin_horas = QDoubleSpinBox()
        self.spin_horas.setRange(0, 24)
        self.spin_horas.setValue(8)
        self.spin_horas.setSingleStep(0.5)
        grupo_detalles_layout.addRow("Horas:", self.spin_horas)
        
        self.text_comentario = QTextEdit()
        self.text_comentario.setMaximumHeight(100)
        grupo_detalles_layout.addRow("Comentario:", self.text_comentario)
        
        grupo_detalles.setLayout(grupo_detalles_layout)
        panel_detalles_layout.addWidget(grupo_detalles)
        
        # Botones de acción para el día
        btn_detalles_layout = QHBoxLayout()
        
        btn_guardar_dia = QPushButton("Guardar Cambios")
        btn_guardar_dia.clicked.connect(self.guardar_detalles_dia)
        btn_detalles_layout.addWidget(btn_guardar_dia)
        
        btn_aplicar_patron = QPushButton("Aplicar Patrón")
        btn_aplicar_patron.clicked.connect(self.aplicar_patron)
        btn_detalles_layout.addWidget(btn_aplicar_patron)
        
        panel_detalles_layout.addLayout(btn_detalles_layout)
        
        # Resumen mensual
        grupo_resumen = QGroupBox("Resumen Mensual")
        grupo_resumen_layout = QFormLayout()
        
        self.label_dias_laborables = QLabel("0")
        grupo_resumen_layout.addRow("Días laborables:", self.label_dias_laborables)
        
        self.label_dias_festivos = QLabel("0")
        grupo_resumen_layout.addRow("Días festivos:", self.label_dias_festivos)
        
        self.label_dias_vacaciones = QLabel("0")
        grupo_resumen_layout.addRow("Días vacaciones:", self.label_dias_vacaciones)
        
        self.label_total_horas = QLabel("0")
        grupo_resumen_layout.addRow("Total horas:", self.label_total_horas)
        
        grupo_resumen.setLayout(grupo_resumen_layout)
        panel_detalles_layout.addWidget(grupo_resumen)
        
        # Botones de acción para el mes
        btn_mes_layout = QHBoxLayout()
        
        btn_importar_calendario = QPushButton("Importar Calendario")
        btn_importar_calendario.clicked.connect(self.importar_calendario)
        btn_mes_layout.addWidget(btn_importar_calendario)
        
        btn_exportar_calendario = QPushButton("Exportar Calendario")
        btn_exportar_calendario.clicked.connect(self.exportar_calendario)
        btn_mes_layout.addWidget(btn_exportar_calendario)
        
        panel_detalles_layout.addLayout(btn_mes_layout)
        
        panel_detalles_layout.addStretch()
        
        splitter.addWidget(panel_detalles)
        
        # Establecer tamaños iniciales del splitter
        splitter.setSizes([500, 300])
        
        layout.addWidget(splitter)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Calendario")
    
    def crear_tab_prediccion(self):
        """Crea la pestaña de predicción de nóminas."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Predicción de Nóminas")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Sección de parámetros de predicción
        grupo_parametros = QGroupBox("Parámetros de Predicción")
        grupo_parametros_layout = QFormLayout()
        
        # Selector de año
        self.spin_anio_prediccion = QSpinBox()
        self.spin_anio_prediccion.setRange(2020, 2050)
        self.spin_anio_prediccion.setValue(datetime.now().year)
        grupo_parametros_layout.addRow("Año:", self.spin_anio_prediccion)
        
        # Selector de mes
        self.combo_mes_prediccion = QComboBox()
        self.combo_mes_prediccion.addItem("Todos los meses")
        for i in range(1, 13):
            self.combo_mes_prediccion.addItem(calendar.month_name[i], i)
        grupo_parametros_layout.addRow("Mes:", self.combo_mes_prediccion)
        
        # Opciones de predicción
        self.check_usar_calendario = QCheckBox("Usar calendario laboral")
        self.check_usar_calendario.setChecked(True)
        grupo_parametros_layout.addRow("Opciones:", self.check_usar_calendario)
        
        self.check_incluir_incrementos = QCheckBox("Incluir incrementos salariales")
        self.check_incluir_incrementos.setChecked(True)
        grupo_parametros_layout.addRow("", self.check_incluir_incrementos)
        
        self.check_incluir_pagas_extras = QCheckBox("Incluir pagas extras")
        self.check_incluir_pagas_extras.setChecked(True)
        grupo_parametros_layout.addRow("", self.check_incluir_pagas_extras)
        
        # Botón de predecir
        btn_predecir = QPushButton("Generar Predicción")
        btn_predecir.clicked.connect(self.predecir_nomina)
        grupo_parametros_layout.addRow("", btn_predecir)
        
        grupo_parametros.setLayout(grupo_parametros_layout)
        layout.addWidget(grupo_parametros)
        
        # Sección de resultados
        grupo_resultados = QGroupBox("Resultados de la Predicción")
        grupo_resultados_layout = QVBoxLayout()
        
        # Tabla de resultados
        self.tabla_prediccion = QTableWidget(0, 3)
        self.tabla_prediccion.setHorizontalHeaderLabels(["Mes", "Importe Bruto", "Importe Neto"])
        self.tabla_prediccion.horizontalHeader().setStretchLastSection(True)
        grupo_resultados_layout.addWidget(self.tabla_prediccion)
        
        # Área para gráfico
        self.frame_grafico_prediccion = QFrame()
        self.frame_grafico_prediccion.setFrameShape(QFrame.StyledPanel)
        self.frame_grafico_prediccion.setMinimumHeight(300)
        grupo_resultados_layout.addWidget(self.frame_grafico_prediccion)
        
        # Layout para el gráfico
        grafico_layout = QVBoxLayout(self.frame_grafico_prediccion)
        
        # Canvas para matplotlib
        self.figura_prediccion = Figure(figsize=(5, 4), dpi=100)
        self.canvas_prediccion = FigureCanvas(self.figura_prediccion)
        grafico_layout.addWidget(self.canvas_prediccion)
        
        grupo_resultados.setLayout(grupo_resultados_layout)
        layout.addWidget(grupo_resultados)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        btn_exportar = QPushButton("Exportar Predicción")
        btn_exportar.clicked.connect(self.exportar_prediccion)
        btn_layout.addWidget(btn_exportar)
        
        btn_informe = QPushButton("Generar Informe")
        btn_informe.clicked.connect(self.generar_informe_prediccion)
        btn_layout.addWidget(btn_informe)
        
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Predicción")
    
    def crear_tab_informes(self):
        """Crea la pestaña de generación de informes."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Generación de Informes")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Sección de selección de tipo de informe
        grupo_tipo = QGroupBox("Tipo de Informe")
        grupo_tipo_layout = QVBoxLayout()
        
        # Opciones de tipo de informe
        self.radio_informe_nomina = QRadioButton("Informe de Nómina")
        self.radio_informe_nomina.setChecked(True)
        grupo_tipo_layout.addWidget(self.radio_informe_nomina)
        
        self.radio_informe_comparacion = QRadioButton("Informe de Comparación")
        grupo_tipo_layout.addWidget(self.radio_informe_comparacion)
        
        self.radio_informe_desviaciones = QRadioButton("Informe de Desviaciones")
        grupo_tipo_layout.addWidget(self.radio_informe_desviaciones)
        
        self.radio_informe_calendario = QRadioButton("Informe de Calendario")
        grupo_tipo_layout.addWidget(self.radio_informe_calendario)
        
        self.radio_informe_prediccion = QRadioButton("Informe de Predicción")
        grupo_tipo_layout.addWidget(self.radio_informe_prediccion)
        
        self.radio_informe_completo = QRadioButton("Informe Completo")
        grupo_tipo_layout.addWidget(self.radio_informe_completo)
        
        # Grupo de botones para selección única
        self.grupo_radio_informes = QButtonGroup()
        self.grupo_radio_informes.addButton(self.radio_informe_nomina)
        self.grupo_radio_informes.addButton(self.radio_informe_comparacion)
        self.grupo_radio_informes.addButton(self.radio_informe_desviaciones)
        self.grupo_radio_informes.addButton(self.radio_informe_calendario)
        self.grupo_radio_informes.addButton(self.radio_informe_prediccion)
        self.grupo_radio_informes.addButton(self.radio_informe_completo)
        
        grupo_tipo.setLayout(grupo_tipo_layout)
        layout.addWidget(grupo_tipo)
        
        # Sección de parámetros del informe
        self.grupo_parametros_informe = QGroupBox("Parámetros del Informe")
        self.grupo_parametros_layout = QFormLayout()
        
        # Parámetros comunes
        self.check_incluir_graficas = QCheckBox("Incluir gráficas")
        self.check_incluir_graficas.setChecked(True)
        self.grupo_parametros_layout.addRow("Opciones:", self.check_incluir_graficas)
        
        # Parámetros específicos para cada tipo de informe
        # (Se actualizarán dinámicamente según el tipo seleccionado)
        self.actualizar_parametros_informe()
        
        # Conectar cambios en el tipo de informe
        self.grupo_radio_informes.buttonClicked.connect(self.actualizar_parametros_informe)
        
        self.grupo_parametros_informe.setLayout(self.grupo_parametros_layout)
        layout.addWidget(self.grupo_parametros_informe)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        btn_generar = QPushButton("Generar Informe")
        btn_generar.clicked.connect(self.generar_informe)
        btn_layout.addWidget(btn_generar)
        
        btn_abrir = QPushButton("Abrir Último Informe")
        btn_abrir.clicked.connect(self.abrir_ultimo_informe)
        btn_layout.addWidget(btn_abrir)
        
        layout.addLayout(btn_layout)
        
        # Lista de informes generados
        grupo_historial = QGroupBox("Historial de Informes")
        grupo_historial_layout = QVBoxLayout()
        
        self.lista_informes = QListWidget()
        grupo_historial_layout.addWidget(self.lista_informes)
        
        # Botones para gestionar informes
        btn_historial_layout = QHBoxLayout()
        
        btn_abrir_seleccionado = QPushButton("Abrir Seleccionado")
        btn_abrir_seleccionado.clicked.connect(self.abrir_informe_seleccionado)
        btn_historial_layout.addWidget(btn_abrir_seleccionado)
        
        btn_eliminar_informe = QPushButton("Eliminar")
        btn_eliminar_informe.clicked.connect(self.eliminar_informe)
        btn_historial_layout.addWidget(btn_eliminar_informe)
        
        grupo_historial_layout.addLayout(btn_historial_layout)
        
        grupo_historial.setLayout(grupo_historial_layout)
        layout.addWidget(grupo_historial)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Informes")
    
    def crear_tab_configuracion(self):
        """Crea la pestaña de configuración."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Configuración")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Sección de datos personales
        grupo_personal = QGroupBox("Datos Personales")
        grupo_personal_layout = QFormLayout()
        
        self.input_nombre = QLineEdit()
        grupo_personal_layout.addRow("Nombre:", self.input_nombre)
        
        self.input_apellidos = QLineEdit()
        grupo_personal_layout.addRow("Apellidos:", self.input_apellidos)
        
        self.input_nif = QLineEdit()
        grupo_personal_layout.addRow("NIF:", self.input_nif)
        
        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems(["Seleccione una categoría...", "Auxiliar", "Técnico", "Especialista", "Jefe de Equipo", "Supervisor"])
        grupo_personal_layout.addRow("Categoría:", self.combo_categoria)
        
        self.date_fecha_alta = QDateEdit()
        self.date_fecha_alta.setCalendarPopup(True)
        self.date_fecha_alta.setDate(QDate.currentDate())
        grupo_personal_layout.addRow("Fecha de alta:", self.date_fecha_alta)
        
        grupo_personal.setLayout(grupo_personal_layout)
        layout.addWidget(grupo_personal)
        
        # Sección de configuración de conceptos salariales
        grupo_conceptos = QGroupBox("Conceptos Salariales")
        grupo_conceptos_layout = QVBoxLayout()
        
        # Tabla de conceptos
        self.tabla_conceptos = QTableWidget(0, 3)
        self.tabla_conceptos.setHorizontalHeaderLabels(["Concepto", "Tipo", "Valor"])
        self.tabla_conceptos.horizontalHeader().setStretchLastSection(True)
        grupo_conceptos_layout.addWidget(self.tabla_conceptos)
        
        # Botones para gestionar conceptos
        btn_conceptos_layout = QHBoxLayout()
        
        btn_agregar_concepto = QPushButton("Agregar")
        btn_agregar_concepto.clicked.connect(self.agregar_concepto)
        btn_conceptos_layout.addWidget(btn_agregar_concepto)
        
        btn_editar_concepto = QPushButton("Editar")
        btn_editar_concepto.clicked.connect(self.editar_concepto)
        btn_conceptos_layout.addWidget(btn_editar_concepto)
        
        btn_eliminar_concepto = QPushButton("Eliminar")
        btn_eliminar_concepto.clicked.connect(self.eliminar_concepto)
        btn_conceptos_layout.addWidget(btn_eliminar_concepto)
        
        grupo_conceptos_layout.addLayout(btn_conceptos_layout)
        
        grupo_conceptos.setLayout(grupo_conceptos_layout)
        layout.addWidget(grupo_conceptos)
        
        # Sección de configuración de la aplicación
        grupo_app = QGroupBox("Configuración de la Aplicación")
        grupo_app_layout = QFormLayout()
        
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Claro", "Oscuro", "Sistema"])
        grupo_app_layout.addRow("Tema:", self.combo_tema)
        
        self.check_autoguardado = QCheckBox()
        self.check_autoguardado.setChecked(True)
        grupo_app_layout.addRow("Autoguardado:", self.check_autoguardado)
        
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 60)
        self.spin_intervalo.setValue(5)
        self.spin_intervalo.setSuffix(" minutos")
        grupo_app_layout.addRow("Intervalo:", self.spin_intervalo)
        
        grupo_app.setLayout(grupo_app_layout)
        layout.addWidget(grupo_app)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        btn_guardar = QPushButton("Guardar Configuración")
        btn_guardar.clicked.connect(self.guardar_configuracion)
        btn_layout.addWidget(btn_guardar)
        
        btn_restaurar = QPushButton("Restaurar Valores Predeterminados")
        btn_restaurar.clicked.connect(self.restaurar_configuracion)
        btn_layout.addWidget(btn_restaurar)
        
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Configuración")
    
    def conectar_bd(self):
        """Conecta a la base de datos SQLite."""
        # Simulación de conexión a la base de datos
        self.statusBar.showMessage("Conectando a la base de datos...")
        
        # En una implementación real, aquí se conectaría a la base de datos
        # y se cargarían los datos iniciales
        
        # Simular carga de datos
        QTimer.singleShot(500, lambda: self.statusBar.showMessage("Conexión establecida", 2000))
        
        # Cargar datos de ejemplo en los combos
        self.cargar_datos_ejemplo()
    
    def cargar_datos_ejemplo(self):
        """Carga datos de ejemplo en la interfaz."""
        # Cargar nóminas de ejemplo
        self.combo_nomina1.clear()
        self.combo_nomina1.addItem("Seleccione una nómina...")
        self.combo_nomina1.addItem("Enero 2025 - Juan Pérez")
        self.combo_nomina1.addItem("Febrero 2025 - Juan Pérez")
        self.combo_nomina1.addItem("Marzo 2025 - Juan Pérez")
        
        self.combo_nomina2.clear()
        self.combo_nomina2.addItem("Seleccione una nómina...")
        self.combo_nomina2.addItem("Enero 2025 - Juan Pérez")
        self.combo_nomina2.addItem("Febrero 2025 - Juan Pérez")
        self.combo_nomina2.addItem("Marzo 2025 - Juan Pérez")
        
        # Cargar archivos de ejemplo
        self.lista_archivos.clear()
        self.lista_archivos.addItem("nominas_enero_2025.pdf")
        self.lista_archivos.addItem("saldos_enero_2025.pdf")
        self.lista_archivos.addItem("tiempos_enero_2025.pdf")
        
        # Cargar informes de ejemplo
        self.lista_informes.clear()
        self.lista_informes.addItem("informe_nomina_enero_2025.pdf")
        self.lista_informes.addItem("informe_comparacion_enero_febrero_2025.pdf")
        self.lista_informes.addItem("informe_desviaciones_2025.pdf")
        
        # Cargar conceptos de ejemplo
        self.tabla_conceptos.setRowCount(0)
        conceptos_ejemplo = [
            ("Salario Base", "Devengo", "1200.00"),
            ("Plus Nocturnidad", "Devengo", "150.00"),
            ("Plus Calidad", "Devengo", "100.00"),
            ("IRPF", "Retención", "15%"),
            ("Seguridad Social", "Retención", "6.35%")
        ]
        
        for concepto, tipo, valor in conceptos_ejemplo:
            row = self.tabla_conceptos.rowCount()
            self.tabla_conceptos.insertRow(row)
            self.tabla_conceptos.setItem(row, 0, QTableWidgetItem(concepto))
            self.tabla_conceptos.setItem(row, 1, QTableWidgetItem(tipo))
            self.tabla_conceptos.setItem(row, 2, QTableWidgetItem(valor))
    
    def mostrar_mensaje_bienvenida(self):
        """Muestra un mensaje de bienvenida al iniciar la aplicación."""
        QMessageBox.information(self, "Bienvenido", 
                               "Bienvenido al Comparador de Nóminas\n\n"
                               "Esta aplicación le permitirá comparar nóminas, saldos y tiempos, "
                               "detectar desviaciones, predecir nóminas futuras y generar informes detallados.\n\n"
                               "Para comenzar, importe sus archivos PDF o introduzca datos manualmente.")
    
    # Métodos para la pestaña de importación
    def importar_pdf(self, tipo=None):
        """Importa un archivo PDF."""
        if not tipo:
            tipo = "archivo"
        
        # Abrir diálogo de selección de archivo
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getOpenFileName(self, f"Importar {tipo}", "", 
                                               "Archivos PDF (*.pdf);;Todos los archivos (*)", 
                                               options=opciones)
        
        if archivo:
            # Añadir a la lista de archivos
            self.lista_archivos.addItem(os.path.basename(archivo))
            self.statusBar.showMessage(f"Archivo {os.path.basename(archivo)} importado correctamente", 3000)
            
            # En una implementación real, aquí se procesaría el PDF
            # utilizando el módulo ExtractorPDF
    
    def abrir_editor_datos(self):
        """Abre el editor de datos manual."""
        # En una implementación real, aquí se abriría un diálogo
        # para la entrada manual de datos
        QMessageBox.information(self, "Editor de Datos", 
                               "El editor de datos manual le permite introducir información "
                               "directamente sin necesidad de importar archivos PDF.")
    
    def procesar_datos(self):
        """Procesa los datos importados."""
        if self.lista_archivos.count() == 0:
            QMessageBox.warning(self, "Sin datos", "No hay archivos para procesar.")
            return
        
        # Simular procesamiento
        self.statusBar.showMessage("Procesando datos...")
        
        # En una implementación real, aquí se procesarían los datos
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Datos procesados correctamente", 3000))
        QMessageBox.information(self, "Procesamiento Completado", 
                               "Los datos han sido procesados correctamente y están listos para su análisis.")
    
    # Métodos para la pestaña de comparación
    def comparar_nominas(self):
        """Compara las nóminas seleccionadas."""
        # Verificar selección
        if self.combo_nomina1.currentIndex() == 0 or self.combo_nomina2.currentIndex() == 0:
            QMessageBox.warning(self, "Selección incompleta", 
                               "Por favor, seleccione dos nóminas para comparar.")
            return
        
        # Simular comparación
        self.statusBar.showMessage("Comparando nóminas...")
        
        # En una implementación real, aquí se compararían las nóminas
        # utilizando el módulo ComparadorNominas
        
        # Mostrar resultados de ejemplo
        self.mostrar_resultados_comparacion()
    
    def mostrar_resultados_comparacion(self):
        """Muestra los resultados de la comparación en la tabla y el gráfico."""
        # Limpiar tabla
        self.tabla_comparacion.setRowCount(0)
        
        # Datos de ejemplo
        conceptos = [
            ("Salario Base", 1200.00, 1200.00, 0.00),
            ("Plus Nocturnidad", 150.00, 180.00, 30.00),
            ("Plus Calidad", 100.00, 100.00, 0.00),
            ("Horas Extra", 75.00, 0.00, -75.00),
            ("IRPF", -180.00, -185.00, -5.00),
            ("Seguridad Social", -76.20, -76.20, 0.00),
            ("Total Bruto", 1525.00, 1480.00, -45.00),
            ("Total Neto", 1268.80, 1218.80, -50.00)
        ]
        
        # Llenar tabla
        for concepto, valor1, valor2, diferencia in conceptos:
            row = self.tabla_comparacion.rowCount()
            self.tabla_comparacion.insertRow(row)
            
            self.tabla_comparacion.setItem(row, 0, QTableWidgetItem(concepto))
            self.tabla_comparacion.setItem(row, 1, QTableWidgetItem(f"{valor1:.2f} €"))
            self.tabla_comparacion.setItem(row, 2, QTableWidgetItem(f"{valor2:.2f} €"))
            
            item_diferencia = QTableWidgetItem(f"{diferencia:.2f} €")
            
            # Colorear diferencias si está activada la opción
            if self.check_destacar_diferencias.isChecked() and diferencia != 0:
                if diferencia > 0:
                    item_diferencia.setForeground(QBrush(QColor("green")))
                else:
                    item_diferencia.setForeground(QBrush(QColor("red")))
            
            self.tabla_comparacion.setItem(row, 3, item_diferencia)
        
        # Crear gráfico de comparación
        self.crear_grafico_comparacion(conceptos)
        
        # Actualizar estado
        self.statusBar.showMessage("Comparación completada", 3000)
    
    def crear_grafico_comparacion(self, conceptos):
        """Crea un gráfico de comparación con matplotlib."""
        # Limpiar figura
        self.figura_comparacion.clear()
        
        # Crear nuevo subplot
        ax = self.figura_comparacion.add_subplot(111)
        
        # Filtrar conceptos para el gráfico (excluir totales)
        conceptos_grafico = [c for c in conceptos if "Total" not in c[0]]
        
        # Preparar datos
        labels = [c[0] for c in conceptos_grafico]
        valores1 = [c[1] for c in conceptos_grafico]
        valores2 = [c[2] for c in conceptos_grafico]
        
        # Crear gráfico de barras
        x = range(len(labels))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], valores1, width, label='Nómina 1')
        ax.bar([i + width/2 for i in x], valores2, width, label='Nómina 2')
        
        # Configurar gráfico
        ax.set_ylabel('Importe (€)')
        ax.set_title('Comparación de Conceptos')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        
        # Ajustar layout
        self.figura_comparacion.tight_layout()
        
        # Actualizar canvas
        self.canvas_comparacion.draw()
    
    def exportar_resultados_comparacion(self):
        """Exporta los resultados de la comparación a un archivo."""
        if self.tabla_comparacion.rowCount() == 0:
            QMessageBox.warning(self, "Sin datos", "No hay resultados para exportar.")
            return
        
        # Abrir diálogo de selección de archivo
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getSaveFileName(self, "Exportar Resultados", "", 
                                               "Archivos CSV (*.csv);;Archivos Excel (*.xlsx)", 
                                               options=opciones)
        
        if archivo:
            # Simular exportación
            self.statusBar.showMessage("Exportando resultados...")
            
            # En una implementación real, aquí se exportarían los datos
            
            # Simular finalización
            QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Resultados exportados correctamente", 3000))
            QMessageBox.information(self, "Exportación Completada", 
                                   f"Los resultados han sido exportados a {archivo}.")
    
    # Métodos para la pestaña de calendario
    def actualizar_calendario(self):
        """Actualiza la visualización del calendario."""
        # En una implementación real, aquí se cargarían los datos del calendario
        # desde la base de datos para el año y mes seleccionados
        
        # Actualizar resumen mensual (datos de ejemplo)
        self.label_dias_laborables.setText("21")
        self.label_dias_festivos.setText("8")
        self.label_dias_vacaciones.setText("1")
        self.label_total_horas.setText("168")
        
        # Actualizar estado
        anio = self.spin_anio.value()
        mes = self.combo_mes.currentText()
        self.statusBar.showMessage(f"Calendario actualizado: {mes} {anio}", 3000)
    
    def ir_a_hoy(self):
        """Establece el calendario en la fecha actual."""
        hoy = QDate.currentDate()
        self.calendario_widget.setSelectedDate(hoy)
        self.spin_anio.setValue(hoy.year())
        self.combo_mes.setCurrentIndex(hoy.month() - 1)
        self.actualizar_calendario()
        self.actualizar_detalles_dia()
    
    def actualizar_detalles_dia(self):
        """Actualiza los detalles del día seleccionado."""
        fecha = self.calendario_widget.selectedDate()
        self.label_fecha.setText(fecha.toString("dd/MM/yyyy"))
        
        # En una implementación real, aquí se cargarían los detalles del día
        # desde la base de datos
        
        # Establecer valores de ejemplo
        if fecha.dayOfWeek() >= 6:  # Sábado o domingo
            self.combo_tipo_dia.setCurrentText("Festivo")
            self.combo_turno.setCurrentText("Libre")
            self.spin_horas.setValue(0)
        else:
            self.combo_tipo_dia.setCurrentText("Laborable")
            self.combo_turno.setCurrentText("Mañana")
            self.spin_horas.setValue(8)
        
        self.text_comentario.clear()
    
    def guardar_detalles_dia(self):
        """Guarda los detalles del día seleccionado."""
        fecha = self.calendario_widget.selectedDate()
        tipo_dia = self.combo_tipo_dia.currentText()
        turno = self.combo_turno.currentText()
        horas = self.spin_horas.value()
        comentario = self.text_comentario.toPlainText()
        
        # En una implementación real, aquí se guardarían los detalles en la base de datos
        
        # Actualizar estado
        self.statusBar.showMessage(f"Detalles guardados para {fecha.toString('dd/MM/yyyy')}", 3000)
        
        # Actualizar resumen mensual
        self.actualizar_calendario()
    
    def aplicar_patron(self):
        """Aplica un patrón de calendario a un rango de fechas."""
        # En una implementación real, aquí se abriría un diálogo para seleccionar
        # el patrón y el rango de fechas
        
        QMessageBox.information(self, "Aplicar Patrón", 
                               "Esta función le permite aplicar un patrón de calendario "
                               "a un rango de fechas, facilitando la configuración de turnos rotativos.")
    
    def importar_calendario(self):
        """Importa un calendario desde un archivo."""
        # Abrir diálogo de selección de archivo
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getOpenFileName(self, "Importar Calendario", "", 
                                               "Archivos Excel (*.xlsx);;Archivos CSV (*.csv);;Todos los archivos (*)", 
                                               options=opciones)
        
        if archivo:
            # Simular importación
            self.statusBar.showMessage("Importando calendario...")
            
            # En una implementación real, aquí se importaría el calendario
            
            # Simular finalización
            QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Calendario importado correctamente", 3000))
            QMessageBox.information(self, "Importación Completada", 
                                   "El calendario ha sido importado correctamente.")
            
            # Actualizar visualización
            self.actualizar_calendario()
    
    def exportar_calendario(self):
        """Exporta el calendario a un archivo."""
        # Abrir diálogo de selección de archivo
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getSaveFileName(self, "Exportar Calendario", "", 
                                               "Archivos Excel (*.xlsx);;Archivos CSV (*.csv)", 
                                               options=opciones)
        
        if archivo:
            # Simular exportación
            self.statusBar.showMessage("Exportando calendario...")
            
            # En una implementación real, aquí se exportaría el calendario
            
            # Simular finalización
            QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Calendario exportado correctamente", 3000))
            QMessageBox.information(self, "Exportación Completada", 
                                   f"El calendario ha sido exportado a {archivo}.")
    
    # Métodos para la pestaña de predicción
    def predecir_nomina(self):
        """Genera una predicción de nómina."""
        # Obtener parámetros
        anio = self.spin_anio_prediccion.value()
        mes_idx = self.combo_mes_prediccion.currentIndex()
        
        # Simular predicción
        self.statusBar.showMessage("Generando predicción...")
        
        # En una implementación real, aquí se generaría la predicción
        # utilizando el módulo PredictorNomina
        
        # Mostrar resultados de ejemplo
        self.mostrar_resultados_prediccion(anio, mes_idx)
    
    def mostrar_resultados_prediccion(self, anio, mes_idx):
        """Muestra los resultados de la predicción en la tabla y el gráfico."""
        # Limpiar tabla
        self.tabla_prediccion.setRowCount(0)
        
        # Datos de ejemplo
        if mes_idx == 0:  # Todos los meses
            meses = [calendar.month_name[i] for i in range(1, 13)]
            brutos = [1500, 1500, 1500, 1500, 1500, 1500, 2250, 1500, 2250, 1500, 1500, 2250]  # Pagas extras en julio, septiembre y diciembre
            netos = [1200, 1200, 1200, 1200, 1200, 1200, 1800, 1200, 1800, 1200, 1200, 1800]
        else:
            meses = [calendar.month_name[mes_idx]]
            brutos = [1500]
            netos = [1200]
            
            # Ajustar para pagas extras
            if mes_idx == 7:  # Julio
                brutos = [2250]
                netos = [1800]
            elif mes_idx == 9:  # Septiembre
                brutos = [2250]
                netos = [1800]
            elif mes_idx == 12:  # Diciembre
                brutos = [2250]
                netos = [1800]
        
        # Llenar tabla
        for i, mes in enumerate(meses):
            row = self.tabla_prediccion.rowCount()
            self.tabla_prediccion.insertRow(row)
            
            self.tabla_prediccion.setItem(row, 0, QTableWidgetItem(mes))
            self.tabla_prediccion.setItem(row, 1, QTableWidgetItem(f"{brutos[i]:.2f} €"))
            self.tabla_prediccion.setItem(row, 2, QTableWidgetItem(f"{netos[i]:.2f} €"))
        
        # Añadir fila de totales si es anual
        if mes_idx == 0:
            row = self.tabla_prediccion.rowCount()
            self.tabla_prediccion.insertRow(row)
            
            self.tabla_prediccion.setItem(row, 0, QTableWidgetItem("TOTAL"))
            self.tabla_prediccion.setItem(row, 1, QTableWidgetItem(f"{sum(brutos):.2f} €"))
            self.tabla_prediccion.setItem(row, 2, QTableWidgetItem(f"{sum(netos):.2f} €"))
        
        # Crear gráfico de predicción
        self.crear_grafico_prediccion(meses, brutos, netos)
        
        # Actualizar estado
        self.statusBar.showMessage("Predicción completada", 3000)
    
    def crear_grafico_prediccion(self, meses, brutos, netos):
        """Crea un gráfico de predicción con matplotlib."""
        # Limpiar figura
        self.figura_prediccion.clear()
        
        # Crear nuevo subplot
        ax = self.figura_prediccion.add_subplot(111)
        
        # Crear gráfico de líneas
        x = range(len(meses))
        
        ax.plot(x, brutos, 'o-', label='Bruto')
        ax.plot(x, netos, 's-', label='Neto')
        
        # Configurar gráfico
        ax.set_ylabel('Importe (€)')
        ax.set_title('Predicción de Nómina')
        ax.set_xticks(x)
        ax.set_xticklabels(meses, rotation=45, ha='right')
        ax.legend()
        
        # Añadir grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Ajustar layout
        self.figura_prediccion.tight_layout()
        
        # Actualizar canvas
        self.canvas_prediccion.draw()
    
    def exportar_prediccion(self):
        """Exporta los resultados de la predicción a un archivo."""
        if self.tabla_prediccion.rowCount() == 0:
            QMessageBox.warning(self, "Sin datos", "No hay resultados para exportar.")
            return
        
        # Abrir diálogo de selección de archivo
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getSaveFileName(self, "Exportar Predicción", "", 
                                               "Archivos CSV (*.csv);;Archivos Excel (*.xlsx)", 
                                               options=opciones)
        
        if archivo:
            # Simular exportación
            self.statusBar.showMessage("Exportando predicción...")
            
            # En una implementación real, aquí se exportarían los datos
            
            # Simular finalización
            QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Predicción exportada correctamente", 3000))
            QMessageBox.information(self, "Exportación Completada", 
                                   f"La predicción ha sido exportada a {archivo}.")
    
    # Métodos para la pestaña de informes
    def actualizar_parametros_informe(self):
        """Actualiza los parámetros del informe según el tipo seleccionado."""
        # Limpiar parámetros específicos
        for i in reversed(range(self.grupo_parametros_layout.count())):
            item = self.grupo_parametros_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None and widget != self.check_incluir_graficas:
                    widget.setParent(None)
        
        # Añadir parámetros específicos según el tipo de informe
        if self.radio_informe_nomina.isChecked():
            # Parámetros para informe de nómina
            self.combo_nomina_informe = QComboBox()
            self.combo_nomina_informe.addItems(["Enero 2025", "Febrero 2025", "Marzo 2025"])
            self.grupo_parametros_layout.addRow("Nómina:", self.combo_nomina_informe)
            
        elif self.radio_informe_comparacion.isChecked():
            # Parámetros para informe de comparación
            self.combo_nomina1_informe = QComboBox()
            self.combo_nomina1_informe.addItems(["Enero 2025", "Febrero 2025", "Marzo 2025"])
            self.grupo_parametros_layout.addRow("Nómina 1:", self.combo_nomina1_informe)
            
            self.combo_nomina2_informe = QComboBox()
            self.combo_nomina2_informe.addItems(["Enero 2025", "Febrero 2025", "Marzo 2025"])
            self.grupo_parametros_layout.addRow("Nómina 2:", self.combo_nomina2_informe)
            
        elif self.radio_informe_desviaciones.isChecked():
            # Parámetros para informe de desviaciones
            self.spin_anio_informe = QSpinBox()
            self.spin_anio_informe.setRange(2020, 2050)
            self.spin_anio_informe.setValue(datetime.now().year)
            self.grupo_parametros_layout.addRow("Año:", self.spin_anio_informe)
            
            self.spin_umbral = QDoubleSpinBox()
            self.spin_umbral.setRange(0, 100)
            self.spin_umbral.setValue(5)
            self.spin_umbral.setSuffix(" %")
            self.grupo_parametros_layout.addRow("Umbral de desviación:", self.spin_umbral)
            
        elif self.radio_informe_calendario.isChecked():
            # Parámetros para informe de calendario
            self.spin_anio_cal_informe = QSpinBox()
            self.spin_anio_cal_informe.setRange(2020, 2050)
            self.spin_anio_cal_informe.setValue(datetime.now().year)
            self.grupo_parametros_layout.addRow("Año:", self.spin_anio_cal_informe)
            
            self.combo_mes_cal_informe = QComboBox()
            self.combo_mes_cal_informe.addItem("Todos los meses")
            for i in range(1, 13):
                self.combo_mes_cal_informe.addItem(calendar.month_name[i], i)
            self.grupo_parametros_layout.addRow("Mes:", self.combo_mes_cal_informe)
            
        elif self.radio_informe_prediccion.isChecked():
            # Parámetros para informe de predicción
            self.spin_anio_pred_informe = QSpinBox()
            self.spin_anio_pred_informe.setRange(2020, 2050)
            self.spin_anio_pred_informe.setValue(datetime.now().year)
            self.grupo_parametros_layout.addRow("Año:", self.spin_anio_pred_informe)
            
        elif self.radio_informe_completo.isChecked():
            # Parámetros para informe completo
            self.spin_anio_comp_informe = QSpinBox()
            self.spin_anio_comp_informe.setRange(2020, 2050)
            self.spin_anio_comp_informe.setValue(datetime.now().year)
            self.grupo_parametros_layout.addRow("Año:", self.spin_anio_comp_informe)
    
    def generar_informe(self):
        """Genera un informe según los parámetros seleccionados."""
        # Determinar tipo de informe
        if self.radio_informe_nomina.isChecked():
            self.generar_informe_nomina()
        elif self.radio_informe_comparacion.isChecked():
            self.generar_informe_comparacion()
        elif self.radio_informe_desviaciones.isChecked():
            self.generar_informe_desviaciones()
        elif self.radio_informe_calendario.isChecked():
            self.generar_informe_calendario()
        elif self.radio_informe_prediccion.isChecked():
            self.generar_informe_prediccion()
        elif self.radio_informe_completo.isChecked():
            self.generar_informe_completo()
    
    def generar_informe_nomina(self):
        """Genera un informe de nómina."""
        # En una implementación real, aquí se generaría el informe
        # utilizando el módulo GeneradorInformes
        
        # Simular generación
        self.statusBar.showMessage("Generando informe de nómina...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe generado correctamente", 3000))
        
        # Añadir a la lista de informes
        self.lista_informes.addItem(f"informe_nomina_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        QMessageBox.information(self, "Informe Generado", 
                               "El informe de nómina ha sido generado correctamente.")
    
    def generar_informe_comparacion(self):
        """Genera un informe de comparación de nóminas."""
        # En una implementación real, aquí se generaría el informe
        # utilizando el módulo GeneradorInformes
        
        # Simular generación
        self.statusBar.showMessage("Generando informe de comparación...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe generado correctamente", 3000))
        
        # Añadir a la lista de informes
        self.lista_informes.addItem(f"informe_comparacion_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        QMessageBox.information(self, "Informe Generado", 
                               "El informe de comparación ha sido generado correctamente.")
    
    def generar_informe_desviaciones(self):
        """Genera un informe de desviaciones."""
        # En una implementación real, aquí se generaría el informe
        # utilizando el módulo GeneradorInformes
        
        # Simular generación
        self.statusBar.showMessage("Generando informe de desviaciones...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe generado correctamente", 3000))
        
        # Añadir a la lista de informes
        self.lista_informes.addItem(f"informe_desviaciones_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        QMessageBox.information(self, "Informe Generado", 
                               "El informe de desviaciones ha sido generado correctamente.")
    
    def generar_informe_calendario(self):
        """Genera un informe de calendario laboral."""
        # En una implementación real, aquí se generaría el informe
        # utilizando el módulo GeneradorInformes
        
        # Simular generación
        self.statusBar.showMessage("Generando informe de calendario...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe generado correctamente", 3000))
        
        # Añadir a la lista de informes
        self.lista_informes.addItem(f"informe_calendario_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        QMessageBox.information(self, "Informe Generado", 
                               "El informe de calendario ha sido generado correctamente.")
    
    def generar_informe_prediccion(self):
        """Genera un informe de predicción de nómina."""
        # En una implementación real, aquí se generaría el informe
        # utilizando el módulo GeneradorInformes
        
        # Simular generación
        self.statusBar.showMessage("Generando informe de predicción...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe generado correctamente", 3000))
        
        # Añadir a la lista de informes
        self.lista_informes.addItem(f"informe_prediccion_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        QMessageBox.information(self, "Informe Generado", 
                               "El informe de predicción ha sido generado correctamente.")
    
    def generar_informe_completo(self):
        """Genera un informe completo."""
        # En una implementación real, aquí se generaría el informe
        # utilizando el módulo GeneradorInformes
        
        # Simular generación
        self.statusBar.showMessage("Generando informe completo...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe generado correctamente", 3000))
        
        # Añadir a la lista de informes
        self.lista_informes.addItem(f"informe_completo_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        QMessageBox.information(self, "Informe Generado", 
                               "El informe completo ha sido generado correctamente.")
    
    def abrir_ultimo_informe(self):
        """Abre el último informe generado."""
        if self.lista_informes.count() == 0:
            QMessageBox.warning(self, "Sin informes", "No hay informes para abrir.")
            return
        
        # Obtener último informe
        ultimo_informe = self.lista_informes.item(self.lista_informes.count() - 1).text()
        
        # Simular apertura
        self.statusBar.showMessage(f"Abriendo {ultimo_informe}...")
        
        # En una implementación real, aquí se abriría el archivo PDF
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe abierto", 3000))
        
        QMessageBox.information(self, "Informe Abierto", 
                               f"El informe {ultimo_informe} ha sido abierto.")
    
    def abrir_informe_seleccionado(self):
        """Abre el informe seleccionado en la lista."""
        if not self.lista_informes.currentItem():
            QMessageBox.warning(self, "Sin selección", "Por favor, seleccione un informe para abrir.")
            return
        
        # Obtener informe seleccionado
        informe = self.lista_informes.currentItem().text()
        
        # Simular apertura
        self.statusBar.showMessage(f"Abriendo {informe}...")
        
        # En una implementación real, aquí se abriría el archivo PDF
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Informe abierto", 3000))
        
        QMessageBox.information(self, "Informe Abierto", 
                               f"El informe {informe} ha sido abierto.")
    
    def eliminar_informe(self):
        """Elimina el informe seleccionado de la lista."""
        if not self.lista_informes.currentItem():
            QMessageBox.warning(self, "Sin selección", "Por favor, seleccione un informe para eliminar.")
            return
        
        # Confirmar eliminación
        informe = self.lista_informes.currentItem().text()
        respuesta = QMessageBox.question(self, "Confirmar Eliminación", 
                                       f"¿Está seguro de que desea eliminar el informe {informe}?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if respuesta == QMessageBox.Yes:
            # Eliminar de la lista
            self.lista_informes.takeItem(self.lista_informes.currentRow())
            
            # En una implementación real, aquí se eliminaría el archivo
            
            self.statusBar.showMessage(f"Informe {informe} eliminado", 3000)
    
    # Métodos para la pestaña de configuración
    def agregar_concepto(self):
        """Agrega un nuevo concepto salarial."""
        # En una implementación real, aquí se abriría un diálogo para
        # introducir los datos del nuevo concepto
        
        # Simular adición
        row = self.tabla_conceptos.rowCount()
        self.tabla_conceptos.insertRow(row)
        self.tabla_conceptos.setItem(row, 0, QTableWidgetItem("Nuevo Concepto"))
        self.tabla_conceptos.setItem(row, 1, QTableWidgetItem("Devengo"))
        self.tabla_conceptos.setItem(row, 2, QTableWidgetItem("0.00"))
        
        self.statusBar.showMessage("Concepto agregado", 3000)
    
    def editar_concepto(self):
        """Edita el concepto seleccionado."""
        if not self.tabla_conceptos.currentItem():
            QMessageBox.warning(self, "Sin selección", "Por favor, seleccione un concepto para editar.")
            return
        
        # En una implementación real, aquí se abriría un diálogo para
        # editar los datos del concepto
        
        # Simular edición
        row = self.tabla_conceptos.currentRow()
        self.tabla_conceptos.setItem(row, 2, QTableWidgetItem("100.00"))
        
        self.statusBar.showMessage("Concepto editado", 3000)
    
    def eliminar_concepto(self):
        """Elimina el concepto seleccionado."""
        if not self.tabla_conceptos.currentItem():
            QMessageBox.warning(self, "Sin selección", "Por favor, seleccione un concepto para eliminar.")
            return
        
        # Confirmar eliminación
        row = self.tabla_conceptos.currentRow()
        concepto = self.tabla_conceptos.item(row, 0).text()
        respuesta = QMessageBox.question(self, "Confirmar Eliminación", 
                                       f"¿Está seguro de que desea eliminar el concepto {concepto}?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if respuesta == QMessageBox.Yes:
            # Eliminar de la tabla
            self.tabla_conceptos.removeRow(row)
            
            self.statusBar.showMessage(f"Concepto {concepto} eliminado", 3000)
    
    def guardar_configuracion(self):
        """Guarda la configuración actual."""
        # En una implementación real, aquí se guardarían los datos en la base de datos
        
        # Simular guardado
        self.statusBar.showMessage("Guardando configuración...")
        
        # Simular finalización
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Configuración guardada correctamente", 3000))
        
        QMessageBox.information(self, "Configuración Guardada", 
                               "La configuración ha sido guardada correctamente.")
    
    def restaurar_configuracion(self):
        """Restaura la configuración a los valores predeterminados."""
        # Confirmar restauración
        respuesta = QMessageBox.question(self, "Confirmar Restauración", 
                                       "¿Está seguro de que desea restaurar la configuración a los valores predeterminados?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if respuesta == QMessageBox.Yes:
            # En una implementación real, aquí se restaurarían los valores predeterminados
            
            # Simular restauración
            self.combo_tema.setCurrentText("Claro")
            self.check_autoguardado.setChecked(True)
            self.spin_intervalo.setValue(5)
            
            self.statusBar.showMessage("Configuración restaurada a valores predeterminados", 3000)
    
    # Métodos para el menú
    def exportar_datos(self):
        """Exporta los datos a un archivo."""
        # Abrir diálogo de selección de archivo
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getSaveFileName(self, "Exportar Datos", "", 
                                               "Archivos JSON (*.json);;Archivos Excel (*.xlsx)", 
                                               options=opciones)
        
        if archivo:
            # Simular exportación
            self.statusBar.showMessage("Exportando datos...")
            
            # En una implementación real, aquí se exportarían los datos
            
            # Simular finalización
            QTimer.singleShot(1000, lambda: self.statusBar.showMessage("Datos exportados correctamente", 3000))
            QMessageBox.information(self, "Exportación Completada", 
                                   f"Los datos han sido exportados a {archivo}.")
    
    def mostrar_preferencias(self):
        """Muestra el diálogo de preferencias."""
        # En una implementación real, aquí se abriría un diálogo de preferencias
        
        # Simular apertura de preferencias
        self.tab_widget.setCurrentIndex(5)  # Ir a la pestaña de configuración
    
    def mostrar_calculadora_precio_hora(self):
        """Muestra la calculadora de precio por hora."""
        # En una implementación real, aquí se abriría un diálogo con la calculadora
        
        QMessageBox.information(self, "Calculadora de Precio/Hora", 
                               "Esta herramienta le permite calcular el precio por hora "
                               "basado en el salario y las horas trabajadas.")
    
    def mostrar_ayuda(self):
        """Muestra el manual de usuario."""
        # En una implementación real, aquí se abriría el manual de usuario
        
        QMessageBox.information(self, "Manual de Usuario", 
                               "El manual de usuario contiene información detallada "
                               "sobre cómo utilizar todas las funciones de la aplicación.")
    
    def mostrar_acerca_de(self):
        """Muestra información sobre la aplicación."""
        QMessageBox.about(self, "Acerca de Comparador de Nóminas", 
                         "Comparador de Nóminas v1.0\n\n"
                         "Esta aplicación permite comparar nóminas, saldos y tiempos, "
                         "detectar desviaciones, predecir nóminas futuras y generar informes detallados.\n\n"
                         "Desarrollado para facilitar la gestión y verificación de nóminas.")


# Función principal
def main():
    app = QApplication(sys.argv)
    window = ComparadorNominasApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
