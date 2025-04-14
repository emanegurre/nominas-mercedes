"""
Módulo de Comparación de Nóminas, Saldos y Tiempos

Este módulo implementa la funcionalidad principal para extraer datos de archivos PDF y Excel,
procesarlos y realizar comparaciones para detectar desviaciones.
"""

import os
import re
import sqlite3
import pandas as pd
import numpy as np
import PyPDF2
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Any, Optional, Union

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class ExtractorDatos:
    """Clase para extraer datos de diferentes formatos de archivo."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el extractor de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._inicializar_bd()
    
    def _inicializar_bd(self):
        """Inicializa la base de datos con las tablas necesarias si no existen."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Crear tablas si no existen
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Empleados (
            id_empleado INTEGER PRIMARY KEY,
            numero_empleado TEXT,
            nombre TEXT,
            apellidos TEXT,
            centro_coste TEXT,
            nivel_salarial TEXT,
            grupo_profesional TEXT,
            fecha_antiguedad TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Nominas (
            id_nomina INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            periodo_inicio TEXT,
            periodo_fin TEXT,
            fecha_emision TEXT,
            total_devengos REAL,
            total_deducciones REAL,
            liquido REAL,
            fecha_importacion TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConceptosNomina (
            id_concepto INTEGER PRIMARY KEY,
            id_nomina INTEGER,
            tipo TEXT,
            concepto TEXT,
            unidades REAL,
            tarifa REAL,
            importe REAL,
            es_retroactivo INTEGER,
            FOREIGN KEY (id_nomina) REFERENCES Nominas(id_nomina)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Saldos (
            id_saldo INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha_evaluacion TEXT,
            tipo_saldo TEXT,
            anio INTEGER,
            derecho REAL,
            disfrutado REAL,
            pendiente REAL,
            unidad TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TiemposNomina (
            id_tiempo INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha TEXT,
            tipo_tiempo TEXT,
            horas REAL,
            dias_nomina REAL,
            es_recalculo INTEGER,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS CalendarioLaboral (
            id_calendario INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha TEXT,
            tipo_dia TEXT,
            horas_teoricas REAL,
            turno TEXT,
            descripcion TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        self.conn.commit()
    
    def extraer_texto_pdf(self, pdf_path: str) -> str:
        """Extrae el texto completo de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        texto = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    texto += page.extract_text() + "\n\n"
            return texto
        except Exception as e:
            print(f"Error al procesar el PDF {pdf_path}: {str(e)}")
            return ""
    
    def extraer_datos_excel(self, excel_path: str) -> Dict[str, pd.DataFrame]:
        """Extrae datos de un archivo Excel.
        
        Args:
            excel_path: Ruta al archivo Excel
            
        Returns:
            Diccionario con DataFrames para cada hoja del Excel
        """
        try:
            # Leer todas las hojas del Excel
            excel_data = pd.read_excel(excel_path, sheet_name=None)
            return excel_data
        except Exception as e:
            print(f"Error al procesar el Excel {excel_path}: {str(e)}")
            return {}
    
    def procesar_nomina_pdf(self, pdf_path: str) -> Tuple[Dict, List[Dict]]:
        """Procesa un archivo PDF de nómina y extrae la información relevante.
        
        Args:
            pdf_path: Ruta al archivo PDF de nómina
            
        Returns:
            Tupla con información de la nómina y lista de conceptos
        """
        texto = self.extraer_texto_pdf(pdf_path)
        
        # Extraer información general de la nómina
        nomina_info = {}
        
        # Buscar periodo de liquidación
        periodo_match = re.search(r'Periodo de liquidación del (\d{2}/\d{2}/\d{4}) al (\d{2}/\d{2}/\d{4})', texto)
        if periodo_match:
            nomina_info['periodo_inicio'] = periodo_match.group(1)
            nomina_info['periodo_fin'] = periodo_match.group(2)
        
        # Buscar número de empleado
        empleado_match = re.search(r'Nº empleado\s+(\d+)', texto)
        if empleado_match:
            nomina_info['numero_empleado'] = empleado_match.group(1)
        
        # Buscar centro de coste
        coste_match = re.search(r'C. coste\s*:\s*(\d+)', texto)
        if coste_match:
            nomina_info['centro_coste'] = coste_match.group(1)
        
        # Buscar nivel salarial y grupo profesional
        nivel_match = re.search(r'Nivel salarial\s*:\s*([^\s]+)\s+Grupo profesional\s*:\s*([^\s]+)', texto)
        if nivel_match:
            nomina_info['nivel_salarial'] = nivel_match.group(1)
            nomina_info['grupo_profesional'] = nivel_match.group(2)
        
        # Buscar fecha de antigüedad
        antiguedad_match = re.search(r'Fecha antigüedad\s*:\s*(\d{2}/\d{2}/\d{4})', texto)
        if antiguedad_match:
            nomina_info['fecha_antiguedad'] = antiguedad_match.group(1)
        
        # Buscar totales
        totales_match = re.search(r'TOTALES\s+([0-9.,]+)\s+([0-9.,]+)', texto)
        if totales_match:
            nomina_info['total_devengos'] = float(totales_match.group(1).replace('.', '').replace(',', '.'))
            nomina_info['total_deducciones'] = float(totales_match.group(2).replace('.', '').replace(',', '.'))
        
        # Buscar líquido
        liquido_match = re.search(r'LIQUIDO\s+([0-9.,]+)', texto)
        if liquido_match:
            nomina_info['liquido'] = float(liquido_match.group(1).replace('.', '').replace(',', '.'))
        
        # Extraer conceptos de nómina
        conceptos = []
        
        # Patrón para conceptos de devengo
        devengo_pattern = r'([A-Za-zÀ-ÿ\s]+)\s+XXX\s+(\d+[.,]?\d*)\s+(\d+[.,]?\d*)\s+(\d+[.,]?\d*)'
        for match in re.finditer(devengo_pattern, texto):
            concepto = {
                'tipo': 'devengo',
                'concepto': match.group(1).strip(),
                'unidades': float(match.group(2).replace(',', '.')),
                'tarifa': float(match.group(3).replace(',', '.')),
                'importe': float(match.group(4).replace('.', '').replace(',', '.')),
                'es_retroactivo': 'retroactividad' in texto[:match.start()].split('\n')[-5:],
            }
            conceptos.append(concepto)
        
        # Patrón para conceptos de deducción
        deduccion_pattern = r'([A-Za-zÀ-ÿ\s]+)\s+(\d+[.,]?\d*)\s*%\s+(\d+[.,]?\d*)\s+(\d+[.,]?\d*)'
        for match in re.finditer(deduccion_pattern, texto):
            concepto = {
                'tipo': 'deduccion',
                'concepto': match.group(1).strip(),
                'unidades': float(match.group(2).replace(',', '.')),  # Porcentaje
                'tarifa': float(match.group(3).replace('.', '').replace(',', '.')),  # Base
                'importe': float(match.group(4).replace(',', '.')),
                'es_retroactivo': 'retroactividad' in texto[:match.start()].split('\n')[-5:],
            }
            conceptos.append(concepto)
        
        return nomina_info, conceptos
    
    def procesar_saldos_pdf(self, pdf_path: str) -> List[Dict]:
        """Procesa un archivo PDF de saldos y extrae la información relevante.
        
        Args:
            pdf_path: Ruta al archivo PDF de saldos
            
        Returns:
            Lista de diccionarios con información de saldos
        """
        texto = self.extraer_texto_pdf(pdf_path)
        saldos = []
        
        # Dividir por secciones de "RESUMEN DE SALDOS"
        secciones = texto.split("RESUMEN DE SALDOS")
        
        for seccion in secciones[1:]:  # Ignorar la primera parte antes del primer "RESUMEN DE SALDOS"
            # Extraer número de personal
            num_personal_match = re.search(r'Número de personal\s+(\d+)', seccion)
            if not num_personal_match:
                continue
                
            numero_empleado = num_personal_match.group(1)
            
            # Extraer fecha de evaluación
            fecha_match = re.search(r'Los saldos corresponden a su último día evaluado:\s+(\d{2}/\d{2}/\d{4})', seccion)
            fecha_evaluacion = fecha_match.group(1) if fecha_match else None
            
            # Extraer centro de coste
            centro_match = re.search(r'Centro de coste\s+([^-\n]+)-(\d+)', seccion)
            centro_coste = centro_match.group(2) if centro_match else None
            
            # Extraer vacaciones
            vacaciones_pattern = r'Vacaciones\s+Año\s+Derecho\s+Disfrutado\s+Pendientes de disfrutar\s+Unidad\s+(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+([^\n]+)'
            for match in re.finditer(vacaciones_pattern, seccion):
                saldo = {
                    'numero_empleado': numero_empleado,
                    'centro_coste': centro_coste,
                    'fecha_evaluacion': fecha_evaluacion,
                    'tipo_saldo': 'Vacaciones',
                    'anio': int(match.group(1)),
                    'derecho': float(match.group(2)),
                    'disfrutado': float(match.group(3)),
                    'pendiente': float(match.group(4)),
                    'unidad': match.group(5).strip()
                }
                saldos.append(saldo)
            
            # Extraer activables de producción
            activables_pattern = r'Activables de Producción\s+Año\s+Derecho\s+Disfrutado\s+Pendiente de disfrutar\s+Unidad\s+(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+([^\n]+)'
            for match in re.finditer(activables_pattern, seccion):
                saldo = {
                    'numero_empleado': numero_empleado,
                    'centro_coste': centro_coste,
                    'fecha_evaluacion': fecha_evaluacion,
                    'tipo_saldo': 'Activables de Producción',
                    'anio': int(match.group(1)),
                    'derecho': float(match.group(2)),
                    'disfrutado': float(match.group(3)),
                    'pendiente': float(match.group(4)),
                    'unidad': match.group(5).strip()
                }
                saldos.append(saldo)
            
            # Extraer cuentas de tiempos
            cuentas_pattern = r'Cuentas de tiempos\s+Denominación\s+Cantidad\s+Unidad\s+([^\n]+)\s+(-?\s*\d+[.,]?\d*)\s+([^\n]+)'
            for match in re.finditer(cuentas_pattern, seccion):
                saldo = {
                    'numero_empleado': numero_empleado,
                    'centro_coste': centro_coste,
                    'fecha_evaluacion': fecha_evaluacion,
                    'tipo_saldo': match.group(1).strip(),
                    'anio': datetime.strptime(fecha_evaluacion, '%d/%m/%Y').year if fecha_evaluacion else None,
                    'derecho': None,
                    'disfrutado': None,
                    'pendiente': float(match.group(2).replace(' ', '').replace(',', '.')),
                    'unidad': match.group(3).strip()
                }
                saldos.append(saldo)
        
        return saldos
    
    def procesar_tiempos_pdf(self, pdf_path: str) -> List[Dict]:
        """Procesa un archivo PDF de tiempos de nómina y extrae la información relevante.
        
        Args:
            pdf_path: Ruta al archivo PDF de tiempos
            
        Returns:
            Lista de diccionarios con información de tiempos
        """
        texto = self.extraer_texto_pdf(pdf_path)
        tiempos = []
        
        # Dividir por secciones de "Datos de Tiempos utilizados en el cálculo de la nómina"
        secciones = texto.split("Datos de Tiempos utilizados en el cálculo de la nómina")
        
        for seccion in secciones[1:]:  # Ignorar la primera parte antes del primer título
            # Extraer número de personal
            num_personal_match = re.search(r'Número de personal\s+(\d+)', seccion)
            if not num_personal_match:
                continue
                
            numero_empleado = num_personal_match.group(1)
            
            # Extraer centro de coste
            centro_match = re.search(r'Centro de coste\s+(\d+)\s+-\s+([^\n]+)', seccion)
            centro_coste = centro_match.group(1) if centro_match else None
            
            # Extraer periodo
            periodo_match = re.search(r'Periodo: Desde (\d{2}-\w{3}-\d{2}) Hasta (\d{2}-\w{3}-\d{2})', seccion)
            periodo_inicio = periodo_match.group(1) if periodo_match else None
            periodo_fin = periodo_match.group(2) if periodo_match else None
            
            # Extraer datos de tiempos recálculos
            recalculos_section = seccion.split("Datos de Tiempos - Re-cálculos de meses anteriores")
            if len(recalculos_section) > 1:
                recalculos_text = recalculos_section[1].split("Datos de Tiempos")[0]
                
                # Patrón para absentismos/presencias en recálculos
                recalculo_pattern = r'([^\n]+)\s+(\d{2}-\w{3}-\d{2})\s+(\d{2}-\w{3}-\d{2})\s+(\d+)\s+(\d+)\s+(\d+)\s+([^\n]+)'
                for match in re.finditer(recalculo_pattern, recalculos_text):
                    tiempo = {
                        'numero_empleado': numero_empleado,
                        'centro_coste': centro_coste,
                        'tipo_tiempo': match.group(1).strip(),
                        'fecha_inicio': match.group(2),
                        'fecha_fin': match.group(3),
                        'horas': float(match.group(4)),
                        'dias': float(match.group(5)),
                        'dias_nomina': float(match.group(6)),
                        'situacion': match.group(7).strip(),
                        'es_recalculo': True
                    }
                    tiempos.append(tiempo)
            
            # Extraer datos de tiempos normales
            tiempos_pattern = r'Datos de Tiempos\s+Fecha\s+Nº Horas\s+Días/Horas Nómina\s+([^\n]+)\s+(\d{2}-\w{3}-\d{2})\s+(\d+)\s+(\d+)'
            for match in re.finditer(tiempos_pattern, seccion):
                tiempo = {
                    'numero_empleado': numero_empleado,
                    'centro_coste': centro_coste,
   
(Content truncated due to size limit. Use line ranges to read in chunks)