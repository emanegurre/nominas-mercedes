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
        self.combo_mes.current
(Content truncated due to size limit. Use line ranges to read in chunks)