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
                    'tipo_tiempo': match.group(1).strip(),
                    'fecha': match.group(2),
                    'horas': float(match.group(3)),
                    'dias_nomina': float(match.group(4)),
                    'es_recalculo': False
                }
                tiempos.append(tiempo)
            
            # Extraer datos de ocupación
            ocupacion_pattern = r'Fecha Inicio\s+Fecha Fin\s+Días laborables\s*NºHoras\s+Trabajadas\s*Gr. Ocupación \(s/modelo\s+trabajo\)\s*Gr. Ocupación promedio\s+(\d{2}-\w{3}-\d{2})\s+(\d{2}-\w{3}-\d{2})\s+(\d+)\s+(\d+)\s+(\d+[.,]?\d*%)\s+(\d+[.,]?\d*%)'
            for match in re.finditer(ocupacion_pattern, seccion):
                tiempo = {
                    'numero_empleado': numero_empleado,
                    'centro_coste': centro_coste,
                    'tipo_tiempo': 'Ocupación',
                    'fecha_inicio': match.group(1),
                    'fecha_fin': match.group(2),
                    'dias_laborables': float(match.group(3)),
                    'horas_trabajadas': float(match.group(4)),
                    'ocupacion_modelo': match.group(5),
                    'ocupacion_promedio': match.group(6),
                    'es_recalculo': False
                }
                tiempos.append(tiempo)
        
        return tiempos
    
    def guardar_datos_en_bd(self, nominas: List[Dict], conceptos: List[Dict], 
                           saldos: List[Dict], tiempos: List[Dict]) -> None:
        """Guarda los datos procesados en la base de datos.
        
        Args:
            nominas: Lista de diccionarios con información de nóminas
            conceptos: Lista de diccionarios con información de conceptos de nómina
            saldos: Lista de diccionarios con información de saldos
            tiempos: Lista de diccionarios con información de tiempos
        """
        cursor = self.conn.cursor()
        
        # Guardar empleados (extraídos de las nóminas)
        for nomina in nominas:
            if 'numero_empleado' in nomina:
                cursor.execute('''
                INSERT OR IGNORE INTO Empleados 
                (numero_empleado, centro_coste, nivel_salarial, grupo_profesional, fecha_antiguedad)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    nomina.get('numero_empleado'),
                    nomina.get('centro_coste'),
                    nomina.get('nivel_salarial'),
                    nomina.get('grupo_profesional'),
                    nomina.get('fecha_antiguedad')
                ))
        
        # Guardar nóminas
        for nomina in nominas:
            if 'numero_empleado' in nomina:
                # Obtener id_empleado
                cursor.execute('SELECT id_empleado FROM Empleados WHERE numero_empleado = ?', 
                              (nomina.get('numero_empleado'),))
                empleado_row = cursor.fetchone()
                if empleado_row:
                    id_empleado = empleado_row[0]
                    
                    cursor.execute('''
                    INSERT INTO Nominas 
                    (id_empleado, periodo_inicio, periodo_fin, total_devengos, total_deducciones, liquido, fecha_importacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        id_empleado,
                        nomina.get('periodo_inicio'),
                        nomina.get('periodo_fin'),
                        nomina.get('total_devengos'),
                        nomina.get('total_deducciones'),
                        nomina.get('liquido'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    # Obtener id_nomina del último registro insertado
                    id_nomina = cursor.lastrowid
                    
                    # Guardar conceptos asociados a esta nómina
                    for concepto in conceptos:
                        if concepto.get('id_nomina') == id_nomina:
                            cursor.execute('''
                            INSERT INTO ConceptosNomina 
                            (id_nomina, tipo, concepto, unidades, tarifa, importe, es_retroactivo)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                id_nomina,
                                concepto.get('tipo'),
                                concepto.get('concepto'),
                                concepto.get('unidades'),
                                concepto.get('tarifa'),
                                concepto.get('importe'),
                                1 if concepto.get('es_retroactivo') else 0
                            ))
        
        # Guardar saldos
        for saldo in saldos:
            if 'numero_empleado' in saldo:
                # Obtener id_empleado
                cursor.execute('SELECT id_empleado FROM Empleados WHERE numero_empleado = ?', 
                              (saldo.get('numero_empleado'),))
                empleado_row = cursor.fetchone()
                if empleado_row:
                    id_empleado = empleado_row[0]
                    
                    cursor.execute('''
                    INSERT INTO Saldos 
                    (id_empleado, fecha_evaluacion, tipo_saldo, anio, derecho, disfrutado, pendiente, unidad)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        id_empleado,
                        saldo.get('fecha_evaluacion'),
                        saldo.get('tipo_saldo'),
                        saldo.get('anio'),
                        saldo.get('derecho'),
                        saldo.get('disfrutado'),
                        saldo.get('pendiente'),
                        saldo.get('unidad')
                    ))
        
        # Guardar tiempos
        for tiempo in tiempos:
            if 'numero_empleado' in tiempo:
                # Obtener id_empleado
                cursor.execute('SELECT id_empleado FROM Empleados WHERE numero_empleado = ?', 
                              (tiempo.get('numero_empleado'),))
                empleado_row = cursor.fetchone()
                if empleado_row:
                    id_empleado = empleado_row[0]
                    
                    # Determinar qué campos guardar según el tipo de tiempo
                    fecha = tiempo.get('fecha', tiempo.get('fecha_inicio'))
                    horas = tiempo.get('horas', tiempo.get('horas_trabajadas'))
                    dias_nomina = tiempo.get('dias_nomina', tiempo.get('dias_laborables'))
                    
                    cursor.execute('''
                    INSERT INTO TiemposNomina 
                    (id_empleado, fecha, tipo_tiempo, horas, dias_nomina, es_recalculo)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        id_empleado,
                        fecha,
                        tiempo.get('tipo_tiempo'),
                        horas,
                        dias_nomina,
                        1 if tiempo.get('es_recalculo') else 0
                    ))
        
        self.conn.commit()


class ComparadorNominas:
    """Clase para realizar comparaciones entre nóminas, saldos y tiempos."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el comparador de nóminas.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._conectar_bd()
    
    def _conectar_bd(self):
        """Conecta a la base de datos."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    
    def obtener_periodos_disponibles(self) -> List[Dict]:
        """Obtiene los periodos de nómina disponibles en la base de datos.
        
        Returns:
            Lista de diccionarios con información de periodos
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT DISTINCT periodo_inicio, periodo_fin 
        FROM Nominas 
        ORDER BY periodo_inicio
        ''')
        
        periodos = []
        for row in cursor.fetchall():
            periodos.append({
                'inicio': row['periodo_inicio'],
                'fin': row['periodo_fin']
            })
        
        return periodos
    
    def obtener_empleados_disponibles(self) -> List[Dict]:
        """Obtiene los empleados disponibles en la base de datos.
        
        Returns:
            Lista de diccionarios con información de empleados
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id_empleado, numero_empleado, nombre, apellidos, centro_coste 
        FROM Empleados 
        ORDER BY numero_empleado
        ''')
        
        empleados = []
        for row in cursor.fetchall():
            empleados.append({
                'id': row['id_empleado'],
                'numero': row['numero_empleado'],
                'nombre': row['nombre'],
                'apellidos': row['apellidos'],
                'centro_coste': row['centro_coste']
            })
        
        return empleados
    
    def comparar_nominas_periodos(self, id_empleado: int, periodo1: str, periodo2: str) -> Dict:
        """Compara las nóminas de un empleado entre dos periodos.
        
        Args:
            id_empleado: ID del empleado
            periodo1: Periodo inicial (formato: 'DD/MM/YYYY-DD/MM/YYYY')
            periodo2: Periodo final (formato: 'DD/MM/YYYY-DD/MM/YYYY')
            
        Returns:
            Diccionario con resultados de la comparación
        """
        cursor = self.conn.cursor()
        
        # Separar periodos en inicio y fin
        periodo1_inicio, periodo1_fin = periodo1.split('-')
        periodo2_inicio, periodo2_fin = periodo2.split('-')
        
        # Obtener nóminas para ambos periodos
        cursor.execute('''
        SELECT id_nomina, periodo_inicio, periodo_fin, total_devengos, total_deducciones, liquido
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio = ? AND periodo_fin = ?
        ''', (id_empleado, periodo1_inicio, periodo1_fin))
        nomina1 = cursor.fetchone()
        
        cursor.execute('''
        SELECT id_nomina, periodo_inicio, periodo_fin, total_devengos, total_deducciones, liquido
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio = ? AND periodo_fin = ?
        ''', (id_empleado, periodo2_inicio, periodo2_fin))
        nomina2 = cursor.fetchone()
        
        if not nomina1 or not nomina2:
            return {'error': 'No se encontraron nóminas para los periodos especificados'}
        
        # Obtener conceptos para ambas nóminas
        cursor.execute('''
        SELECT tipo, concepto, unidades, tarifa, importe, es_retroactivo
        FROM ConceptosNomina
        WHERE id_nomina = ?
        ''', (nomina1['id_nomina'],))
        conceptos1 = cursor.fetchall()
        
        cursor.execute('''
        SELECT tipo, concepto, unidades, tarifa, importe, es_retroactivo
        FROM ConceptosNomina
        WHERE id_nomina = ?
        ''', (nomina2['id_nomina'],))
        conceptos2 = cursor.fetchall()
        
        # Convertir a diccionarios para facilitar la comparación
        conceptos1_dict = {f"{row['concepto']}_{row['es_retroactivo']}": dict(row) for row in conceptos1}
        conceptos2_dict = {f"{row['concepto']}_{row['es_retroactivo']}": dict(row) for row in conceptos2}
        
        # Comparar totales
        comparacion_totales = {
            'total_devengos': {
                'periodo1': nomina1['total_devengos'],
                'periodo2': nomina2['total_devengos'],
                'diferencia': nomina2['total_devengos'] - nomina1['total_devengos'],
                'porcentaje': (nomina2['total_devengos'] - nomina1['total_devengos']) / nomina1['total_devengos'] * 100 if nomina1['total_devengos'] else 0
            },
            'total_deducciones': {
                'periodo1': nomina1['total_deducciones'],
                'periodo2': nomina2['total_deducciones'],
                'diferencia': nomina2['total_deducciones'] - nomina1['total_deducciones'],
                'porcentaje': (nomina2['total_deducciones'] - nomina1['total_deducciones']) / nomina1['total_deducciones'] * 100 if nomina1['total_deducciones'] else 0
            },
            'liquido': {
                'periodo1': nomina1['liquido'],
                'periodo2': nomina2['liquido'],
                'diferencia': nomina2['liquido'] - nomina1['liquido'],
                'porcentaje': (nomina2['liquido'] - nomina1['liquido']) / nomina1['liquido'] * 100 if nomina1['liquido'] else 0
            }
        }
        
        # Comparar conceptos
        comparacion_conceptos = []
        todos_conceptos = set(conceptos1_dict.keys()) | set(conceptos2_dict.keys())
        
        for concepto_key in todos_conceptos:
            concepto1 = conceptos1_dict.get(concepto_key, {'importe': 0, 'unidades': 0})
            concepto2 = conceptos2_dict.get(concepto_key, {'importe': 0, 'unidades': 0})
            
            # Extraer el nombre del concepto sin el sufijo de retroactividad
            nombre_concepto = concepto_key.split('_')[0]
            es_retroactivo = '_1' in concepto_key
            
            comparacion = {
                'concepto': nombre_concepto,
                'es_retroactivo': es_retroactivo,
                'importe_periodo1': concepto1.get('importe', 0),
                'importe_periodo2': concepto2.get('importe', 0),
                'diferencia_importe': concepto2.get('importe', 0) - concepto1.get('importe', 0),
                'unidades_periodo1': concepto1.get('unidades', 0),
                'unidades_periodo2': concepto2.get('unidades', 0),
                'diferencia_unidades': concepto2.get('unidades', 0) - concepto1.get('unidades', 0),
            }
            
            # Calcular porcentaje de variación si el importe del periodo 1 no es cero
            if concepto1.get('importe', 0) != 0:
                comparacion['porcentaje_variacion'] = (comparacion['diferencia_importe'] / concepto1.get('importe', 0)) * 100
            else:
                comparacion['porcentaje_variacion'] = float('inf') if comparacion['diferencia_importe'] > 0 else 0
            
            # Determinar si hay desviación significativa (más del 5% o concepto nuevo/eliminado)
            comparacion['desviacion_significativa'] = (
                abs(comparacion['porcentaje_variacion']) > 5 if 'porcentaje_variacion' in comparacion else True
            )
            
            comparacion_conceptos.append(comparacion)
        
        # Ordenar por magnitud de desviación
        comparacion_conceptos.sort(key=lambda x: abs(x.get('porcentaje_variacion', 0)), reverse=True)
        
        return {
            'info_periodos': {
                'periodo1': f"{periodo1_inicio} - {periodo1_fin}",
                'periodo2': f"{periodo2_inicio} - {periodo2_fin}"
            },
            'comparacion_totales': comparacion_totales,
            'comparacion_conceptos': comparacion_conceptos,
            'desviaciones_significativas': [c for c in comparacion_conceptos if c['desviacion_significativa']]
        }
    
    def comparar_tiempos_nomina(self, id_empleado: int, periodo: str) -> Dict:
        """Compara los tiempos registrados con los conceptos de nómina para un periodo.
        
        Args:
            id_empleado: ID del empleado
            periodo: Periodo (formato: 'DD/MM/YYYY-DD/MM/YYYY')
            
        Returns:
            Diccionario con resultados de la comparación
        """
        cursor = self.conn.cursor()
        
        # Separar periodo en inicio y fin
        periodo_inicio, periodo_fin = periodo.split('-')
        
        # Convertir fechas a formato de base de datos
        fecha_inicio = datetime.strptime(periodo_inicio, '%d/%m/%Y')
        fecha_fin = datetime.strptime(periodo_fin, '%d/%m/%Y')
        
        # Obtener nómina para el periodo
        cursor.execute('''
        SELECT id_nomina
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio = ? AND periodo_fin = ?
        ''', (id_empleado, periodo_inicio, periodo_fin))
        nomina = cursor.fetchone()
        
        if not nomina:
            return {'error': 'No se encontró nómina para el periodo especificado'}
        
        # Obtener conceptos de nómina relacionados con tiempos
        cursor.execute('''
        SELECT concepto, unidades, importe
        FROM ConceptosNomina
        WHERE id_nomina = ? AND concepto IN ('Nocturnidad', 'Plus trab.días Festivos', 'Horas Extras')
        ''', (nomina['id_nomina'],))
        conceptos_tiempo = cursor.fetchall()
        
        # Obtener tiempos registrados para el periodo
        cursor.execute('''
        SELECT tipo_tiempo, SUM(horas) as total_horas, SUM(dias_nomina) as total_dias
        FROM TiemposNomina
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND es_recalculo = 0
        GROUP BY tipo_tiempo
        ''', (id_empleado, fecha_inicio.strftime('%d-%b-%y'), fecha_fin.strftime('%d-%b-%y')))
        tiempos = cursor.fetchall()
        
        # Mapear tipos de tiempo a conceptos de nómina
        mapeo_tiempo_concepto = {
            'Nocturnidad': 'Nocturnidad',
            'Festivo': 'Plus trab.días Festivos',
            'Horas Extras': 'Horas Extras'
        }
        
        # Convertir a diccionarios para facilitar la comparación
        conceptos_dict = {row['concepto']: dict(row) for row in conceptos_tiempo}
        tiempos_dict = {}
        
        for tiempo in tiempos:
            tipo = tiempo['tipo_tiempo']
            if tipo in mapeo_tiempo_concepto:
                concepto_asociado = mapeo_tiempo_concepto[tipo]
                tiempos_dict[concepto_asociado] = {
                    'horas': tiempo['total_horas'],
                    'dias': tiempo['total_dias']
                }
        
        # Realizar comparación
        comparaciones = []
        
        for concepto, datos_concepto in conceptos_dict.items():
            datos_tiempo = tiempos_dict.get(concepto, {'horas': 0, 'dias': 0})
            
            comparacion = {
                'concepto': concepto,
                'unidades_nomina': datos_concepto['unidades'],
                'horas_registradas': datos_tiempo['horas'],
                'diferencia': datos_concepto['unidades'] - datos_tiempo['horas'],
                'importe_nomina': datos_concepto['importe']
            }
            
            # Determinar si hay desviación
            comparacion['hay_desviacion'] = abs(comparacion['diferencia']) > 0.5  # Tolerancia de media hora
            
            comparaciones.append(comparacion)
        
        return {
            'periodo': f"{periodo_inicio} - {periodo_fin}",
            'comparaciones': comparaciones,
            'desviaciones': [c for c in comparaciones if c['hay_desviacion']]
        }
    
    def comparar_saldos_tiempos(self, id_empleado: int, fecha_evaluacion: str) -> Dict:
        """Compara los saldos con los tiempos acumulados hasta una fecha.
        
        Args:
            id_empleado: ID del empleado
            fecha_evaluacion: Fecha de evaluación (formato: 'DD/MM/YYYY')
            
        Returns:
            Diccionario con resultados de la comparación
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha = datetime.strptime(fecha_evaluacion, '%d/%m/%Y')
        anio = fecha.year
        
        # Obtener saldos para la fecha de evaluación
        cursor.execute('''
        SELECT tipo_saldo, derecho, disfrutado, pendiente, unidad
        FROM Saldos
        WHERE id_empleado = ? AND fecha_evaluacion = ? AND anio = ?
        ''', (id_empleado, fecha_evaluacion, anio))
        saldos = cursor.fetchall()
        
        if not saldos:
            return {'error': 'No se encontraron saldos para la fecha especificada'}
        
        # Obtener tiempos acumulados hasta la fecha
        inicio_anio = f"01-01-{anio}"
        cursor.execute('''
        SELECT tipo_tiempo, SUM(horas) as total_horas, SUM(dias_nomina) as total_dias
        FROM TiemposNomina
        WHERE id_empleado = ? AND fecha <= ? AND strftime('%Y', fecha) = ?
        GROUP BY tipo_tiempo
        ''', (id_empleado, fecha.strftime('%d-%b-%y'), str(anio)))
        tiempos = cursor.fetchall()
        
        # Convertir a diccionarios para facilitar la comparación
        saldos_dict = {row['tipo_saldo']: dict(row) for row in saldos}
        tiempos_dict = {row['tipo_tiempo']: dict(row) for row in tiempos}
        
        # Mapeo de tipos de tiempo a tipos de saldo (simplificado)
        mapeo_tiempo_saldo = {
            'Vacaciones': ['Vacaciones'],
            'Activables de Producción': ['Activables'],
            'Cta.Unica F. año ant.acum': ['Horas Extras', 'Nocturnidad']
        }
        
        # Realizar comparación
        comparaciones = []
        
        for tipo_saldo, tipos_tiempo in mapeo_tiempo_saldo.items():
            if tipo_saldo in saldos_dict:
                saldo = saldos_dict[tipo_saldo]
                
                # Sumar tiempos relacionados
                horas_acumuladas = 0
                dias_acumulados = 0
                
                for tipo_tiempo in tipos_tiempo:
                    if tipo_tiempo in tiempos_dict:
                        tiempo = tiempos_dict[tipo_tiempo]
                        horas_acumuladas += tiempo.get('total_horas', 0)
                        dias_acumulados += tiempo.get('total_dias', 0)
                
                # Determinar qué comparar según la unidad del saldo
                valor_comparar = dias_acumulados if saldo['unidad'] == 'Días laborables' else horas_acumuladas
                
                comparacion = {
                    'tipo_saldo': tipo_saldo,
                    'derecho': saldo.get('derecho'),
                    'disfrutado': saldo.get('disfrutado'),
                    'pendiente': saldo.get('pendiente'),
                    'acumulado_calculado': valor_comparar,
                    'unidad': saldo['unidad']
                }
                
                # Calcular diferencia si es posible
                if saldo.get('disfrutado') is not None:
                    comparacion['diferencia'] = saldo.get('disfrutado') - valor_comparar
                    comparacion['hay_desviacion'] = abs(comparacion['diferencia']) > 0.5  # Tolerancia
                
                comparaciones.append(comparacion)
        
        return {
            'fecha_evaluacion': fecha_evaluacion,
            'comparaciones': comparaciones,
            'desviaciones': [c for c in comparaciones if c.get('hay_desviacion', False)]
        }
    
    def generar_visualizacion_evolucion_nomina(self, id_empleado: int, 
                                              concepto: Optional[str] = None) -> Dict:
        """Genera datos para visualizar la evolución de la nómina a lo largo del tiempo.
        
        Args:
            id_empleado: ID del empleado
            concepto: Concepto específico a visualizar (opcional)
            
        Returns:
            Diccionario con datos para visualización
        """
        cursor = self.conn.cursor()
        
        if concepto:
            # Obtener evolución de un concepto específico
            cursor.execute('''
            SELECT n.periodo_inicio, n.periodo_fin, c.concepto, c.importe
            FROM Nominas n
            JOIN ConceptosNomina c ON n.id_nomina = c.id_nomina
            WHERE n.id_empleado = ? AND c.concepto = ?
            ORDER BY n.periodo_inicio
            ''', (id_empleado, concepto))
            
            rows = cursor.fetchall()
            
            periodos = []
            importes = []
            
            for row in rows:
                # Usar el mes y año del periodo de inicio como etiqueta
                fecha = datetime.strptime(row['periodo_inicio'], '%d/%m/%Y')
                periodo_label = fecha.strftime('%m/%Y')
                
                periodos.append(periodo_label)
                importes.append(row['importe'])
            
            return {
                'tipo': 'concepto',
                'concepto': concepto,
                'periodos': periodos,
                'valores': importes
            }
        else:
            # Obtener evolución del líquido total
            cursor.execute('''
            SELECT periodo_inicio, periodo_fin, liquido
            FROM Nominas
            WHERE id_empleado = ?
            ORDER BY periodo_inicio
            ''', (id_empleado,))
            
            rows = cursor.fetchall()
            
            periodos = []
            liquidos = []
            
            for row in rows:
                # Usar el mes y año del periodo de inicio como etiqueta
                fecha = datetime.strptime(row['periodo_inicio'], '%d/%m/%Y')
                periodo_label = fecha.strftime('%m/%Y')
                
                periodos.append(periodo_label)
                liquidos.append(row['liquido'])
            
            return {
                'tipo': 'liquido',
                'periodos': periodos,
                'valores': liquidos
            }
    
    def generar_visualizacion_distribucion_nomina(self, id_empleado: int, 
                                                 periodo: str) -> Dict:
        """Genera datos para visualizar la distribución de conceptos en una nómina.
        
        Args:
            id_empleado: ID del empleado
            periodo: Periodo (formato: 'DD/MM/YYYY-DD/MM/YYYY')
            
        Returns:
            Diccionario con datos para visualización
        """
        cursor = self.conn.cursor()
        
        # Separar periodo en inicio y fin
        periodo_inicio, periodo_fin = periodo.split('-')
        
        # Obtener nómina para el periodo
        cursor.execute('''
        SELECT id_nomina
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio = ? AND periodo_fin = ?
        ''', (id_empleado, periodo_inicio, periodo_fin))
        nomina = cursor.fetchone()
        
        if not nomina:
            return {'error': 'No se encontró nómina para el periodo especificado'}
        
        # Obtener conceptos de devengo
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ? AND tipo = 'devengo' AND importe > 0
        ORDER BY importe DESC
        ''', (nomina['id_nomina'],))
        devengos = cursor.fetchall()
        
        # Obtener conceptos de deducción
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ? AND tipo = 'deduccion' AND importe > 0
        ORDER BY importe DESC
        ''', (nomina['id_nomina'],))
        deducciones = cursor.fetchall()
        
        # Preparar datos para visualización
        conceptos_devengo = [row['concepto'] for row in devengos]
        importes_devengo = [row['importe'] for row in devengos]
        
        conceptos_deduccion = [row['concepto'] for row in deducciones]
        importes_deduccion = [row['importe'] for row in deducciones]
        
        return {
            'periodo': f"{periodo_inicio} - {periodo_fin}",
            'devengos': {
                'conceptos': conceptos_devengo,
                'importes': importes_devengo
            },
            'deducciones': {
                'conceptos': conceptos_deduccion,
                'importes': importes_deduccion
            }
        }
    
    def generar_visualizacion_saldos(self, id_empleado: int, tipo_saldo: str) -> Dict:
        """Genera datos para visualizar la evolución de saldos a lo largo del tiempo.
        
        Args:
            id_empleado: ID del empleado
            tipo_saldo: Tipo de saldo a visualizar
            
        Returns:
            Diccionario con datos para visualización
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT fecha_evaluacion, derecho, disfrutado, pendiente
        FROM Saldos
        WHERE id_empleado = ? AND tipo_saldo = ?
        ORDER BY fecha_evaluacion
        ''', (id_empleado, tipo_saldo))
        
        rows = cursor.fetchall()
        
        fechas = []
        derechos = []
        disfrutados = []
        pendientes = []
        
        for row in rows:
            fechas.append(row['fecha_evaluacion'])
            
            if row['derecho'] is not None:
                derechos.append(row['derecho'])
            
            if row['disfrutado'] is not None:
                disfrutados.append(row['disfrutado'])
            
            if row['pendiente'] is not None:
                pendientes.append(row['pendiente'])
        
        return {
            'tipo_saldo': tipo_saldo,
            'fechas': fechas,
            'series': [
                {'nombre': 'Derecho', 'valores': derechos} if derechos else None,
                {'nombre': 'Disfrutado', 'valores': disfrutados} if disfrutados else None,
                {'nombre': 'Pendiente', 'valores': pendientes} if pendientes else None
            ]
        }


class VisualizadorDatos:
    """Clase para generar visualizaciones gráficas de los datos."""
    
    @staticmethod
    def crear_grafico_evolucion_nomina(datos: Dict, ruta_salida: str) -> None:
        """Crea un gráfico de línea para mostrar la evolución de la nómina.
        
        Args:
            datos: Diccionario con datos para visualización
            ruta_salida: Ruta donde guardar el gráfico
        """
        plt.figure(figsize=(10, 6))
        
        plt.plot(datos['periodos'], datos['valores'], marker='o', linestyle='-', linewidth=2)
        
        if datos['tipo'] == 'concepto':
            titulo = f"Evolución del concepto '{datos['concepto']}'"
        else:
            titulo = "Evolución del líquido de la nómina"
        
        plt.title(titulo)
        plt.xlabel('Periodo')
        plt.ylabel('Importe (€)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(ruta_salida)
        plt.close()
    
    @staticmethod
    def crear_grafico_distribucion_nomina(datos: Dict, ruta_salida: str) -> None:
        """Crea un gráfico de barras para mostrar la distribución de conceptos en una nómina.
        
        Args:
            datos: Diccionario con datos para visualización
            ruta_salida: Ruta donde guardar el gráfico
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
        
        # Gráfico de devengos
        if datos['devengos']['importes']:
            ax1.barh(datos['devengos']['conceptos'], datos['devengos']['importes'], color='green', alpha=0.7)
            ax1.set_title('Conceptos de Devengo')
            ax1.set_xlabel('Importe (€)')
            ax1.grid(True, linestyle='--', alpha=0.7, axis='x')
        else:
            ax1.text(0.5, 0.5, 'No hay datos de devengos', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax1.transAxes)
        
        # Gráfico de deducciones
        if datos['deducciones']['importes']:
            ax2.barh(datos['deducciones']['conceptos'], datos['deducciones']['importes'], color='red', alpha=0.7)
            ax2.set_title('Conceptos de Deducción')
            ax2.set_xlabel('Importe (€)')
            ax2.grid(True, linestyle='--', alpha=0.7, axis='x')
        else:
            ax2.text(0.5, 0.5, 'No hay datos de deducciones', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax2.transAxes)
        
        plt.suptitle(f"Distribución de conceptos en nómina - Periodo: {datos['periodo']}")
        plt.tight_layout()
        
        plt.savefig(ruta_salida)
        plt.close()
    
    @staticmethod
    def crear_grafico_saldos(datos: Dict, ruta_salida: str) -> None:
        """Crea un gráfico de línea para mostrar la evolución de saldos.
        
        Args:
            datos: Diccionario con datos para visualización
            ruta_salida: Ruta donde guardar el gráfico
        """
        plt.figure(figsize=(10, 6))
        
        for serie in datos['series']:
            if serie:
                plt.plot(datos['fechas'], serie['valores'], marker='o', linestyle='-', label=serie['nombre'])
        
        plt.title(f"Evolución de {datos['tipo_saldo']}")
        plt.xlabel('Fecha de evaluación')
        plt.ylabel('Valor')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(ruta_salida)
        plt.close()
    
    @staticmethod
    def crear_grafico_comparacion_nominas(datos: Dict, ruta_salida: str) -> None:
        """Crea un gráfico de barras para comparar nóminas entre periodos.
        
        Args:
            datos: Diccionario con datos de comparación
            ruta_salida: Ruta donde guardar el gráfico
        """
        # Extraer datos de totales
        categorias = ['Total Devengos', 'Total Deducciones', 'Líquido']
        valores_periodo1 = [
            datos['comparacion_totales']['total_devengos']['periodo1'],
            datos['comparacion_totales']['total_deducciones']['periodo1'],
            datos['comparacion_totales']['liquido']['periodo1']
        ]
        valores_periodo2 = [
            datos['comparacion_totales']['total_devengos']['periodo2'],
            datos['comparacion_totales']['total_deducciones']['periodo2'],
            datos['comparacion_totales']['liquido']['periodo2']
        ]
        
        # Crear gráfico de barras
        x = np.arange(len(categorias))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar(x - width/2, valores_periodo1, width, label=f"Periodo 1: {datos['info_periodos']['periodo1']}")
        rects2 = ax.bar(x + width/2, valores_periodo2, width, label=f"Periodo 2: {datos['info_periodos']['periodo2']}")
        
        ax.set_title('Comparación de Totales entre Periodos')
        ax.set_ylabel('Importe (€)')
        ax.set_xticks(x)
        ax.set_xticklabels(categorias)
        ax.legend()
        
        # Añadir etiquetas con valores
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.2f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 puntos de desplazamiento vertical
                            textcoords="offset points",
                            ha='center', va='bottom', rotation=0)
        
        autolabel(rects1)
        autolabel(rects2)
        
        plt.tight_layout()
        plt.savefig(ruta_salida)
        plt.close()
        
        # Crear gráfico adicional para conceptos con desviaciones significativas
        if datos['desviaciones_significativas']:
            # Limitar a los 10 conceptos con mayor desviación
            top_desviaciones = datos['desviaciones_significativas'][:10]
            
            conceptos = [d['concepto'] for d in top_desviaciones]
            valores_periodo1 = [d['importe_periodo1'] for d in top_desviaciones]
            valores_periodo2 = [d['importe_periodo2'] for d in top_desviaciones]
            
            # Crear gráfico de barras
            x = np.arange(len(conceptos))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(12, 8))
            rects1 = ax.bar(x - width/2, valores_periodo1, width, label=f"Periodo 1: {datos['info_periodos']['periodo1']}")
            rects2 = ax.bar(x + width/2, valores_periodo2, width, label=f"Periodo 2: {datos['info_periodos']['periodo2']}")
            
            ax.set_title('Conceptos con Desviaciones Significativas')
            ax.set_ylabel('Importe (€)')
            ax.set_xticks(x)
            ax.set_xticklabels(conceptos, rotation=45, ha='right')
            ax.legend()
            
            autolabel(rects1)
            autolabel(rects2)
            
            plt.tight_layout()
            plt.savefig(ruta_salida.replace('.png', '_desviaciones.png'))
            plt.close()


class CalendarioLaboral:
    """Clase para gestionar el calendario laboral."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el gestor de calendario laboral.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._conectar_bd()
    
    def _conectar_bd(self):
        """Conecta a la base de datos."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    
    def crear_calendario_anual(self, anio: int, id_empleado: int) -> None:
        """Crea un calendario laboral anual para un empleado.
        
        Args:
            anio: Año del calendario
            id_empleado: ID del empleado
        """
        cursor = self.conn.cursor()
        
        # Verificar si ya existe un calendario para este empleado y año
        cursor.execute('''
        SELECT COUNT(*) as count
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
        ''', (id_empleado, str(anio)))
        
        if cursor.fetchone()['count'] > 0:
            # Eliminar calendario existente
            cursor.execute('''
            DELETE FROM CalendarioLaboral
            WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
            ''', (id_empleado, str(anio)))
        
        # Crear calendario con días laborables por defecto
        fecha_inicio = datetime(anio, 1, 1)
        fecha_fin = datetime(anio, 12, 31)
        
        dia_actual = fecha_inicio
        while dia_actual <= fecha_fin:
            # Por defecto, lunes a viernes son laborables, sábado y domingo son festivos
            if dia_actual.weekday() < 5:  # 0-4 son lunes a viernes
                tipo_dia = 'Laboral'
                horas_teoricas = 8.0
            else:
                tipo_dia = 'Festivo'
                horas_teoricas = 0.0
            
            cursor.execute('''
            INSERT INTO CalendarioLaboral
            (id_empleado, fecha, tipo_dia, horas_teoricas, turno, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                id_empleado,
                dia_actual.strftime('%Y-%m-%d'),
                tipo_dia,
                horas_teoricas,
                'Diurno' if tipo_dia == 'Laboral' else '',
                ''
            ))
            
            dia_actual += timedelta(days=1)
        
        self.conn.commit()
    
    def establecer_festivos(self, id_empleado: int, anio: int, festivos: List[str]) -> None:
        """Establece días festivos en el calendario.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            festivos: Lista de fechas festivas en formato 'DD/MM/YYYY'
        """
        cursor = self.conn.cursor()
        
        for festivo in festivos:
            fecha = datetime.strptime(festivo, '%d/%m/%Y')
            
            cursor.execute('''
            UPDATE CalendarioLaboral
            SET tipo_dia = 'Festivo', horas_teoricas = 0.0, descripcion = 'Festivo'
            WHERE id_empleado = ? AND fecha = ?
            ''', (id_empleado, fecha.strftime('%Y-%m-%d')))
        
        self.conn.commit()
    
    def establecer_vacaciones(self, id_empleado: int, fecha_inicio: str, fecha_fin: str) -> None:
        """Establece un periodo de vacaciones en el calendario.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
        """
        cursor = self.conn.cursor()
        
        inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        dia_actual = inicio
        while dia_actual <= fin:
            cursor.execute('''
            UPDATE CalendarioLaboral
            SET tipo_dia = 'Vacaciones', horas_teoricas = 0.0, descripcion = 'Vacaciones'
            WHERE id_empleado = ? AND fecha = ?
            ''', (id_empleado, dia_actual.strftime('%Y-%m-%d')))
            
            dia_actual += timedelta(days=1)
        
        self.conn.commit()
    
    def establecer_licencia(self, id_empleado: int, fecha_inicio: str, fecha_fin: str, 
                           tipo_licencia: str) -> None:
        """Establece un periodo de licencia en el calendario.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            tipo_licencia: Tipo de licencia (ej. 'Permiso retribuido', 'Baja médica')
        """
        cursor = self.conn.cursor()
        
        inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        dia_actual = inicio
        while dia_actual <= fin:
            cursor.execute('''
            UPDATE CalendarioLaboral
            SET tipo_dia = ?, horas_teoricas = 0.0, descripcion = ?
            WHERE id_empleado = ? AND fecha = ?
            ''', (tipo_licencia, tipo_licencia, id_empleado, dia_actual.strftime('%Y-%m-%d')))
            
            dia_actual += timedelta(days=1)
        
        self.conn.commit()
    
    def establecer_turno(self, id_empleado: int, fecha_inicio: str, fecha_fin: str, 
                        turno: str, horas: float) -> None:
        """Establece un turno específico para un periodo.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            turno: Tipo de turno (ej. 'Diurno', 'Nocturno', 'Mixto')
            horas: Horas teóricas del turno
        """
        cursor = self.conn.cursor()
        
        inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        dia_actual = inicio
        while dia_actual <= fin:
            # Solo modificar días laborables
            cursor.execute('''
            UPDATE CalendarioLaboral
            SET turno = ?, horas_teoricas = ?
            WHERE id_empleado = ? AND fecha = ? AND tipo_dia = 'Laboral'
            ''', (turno, horas, id_empleado, dia_actual.strftime('%Y-%m-%d')))
            
            dia_actual += timedelta(days=1)
        
        self.conn.commit()
    
    def obtener_calendario_mensual(self, id_empleado: int, anio: int, mes: int) -> List[Dict]:
        """Obtiene el calendario laboral de un mes específico.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            mes: Mes del calendario (1-12)
            
        Returns:
            Lista de diccionarios con información de cada día
        """
        cursor = self.conn.cursor()
        
        # Construir fechas de inicio y fin del mes
        fecha_inicio = f"{anio}-{mes:02d}-01"
        
        # Determinar último día del mes
        if mes == 12:
            siguiente_anio = anio + 1
            siguiente_mes = 1
        else:
            siguiente_anio = anio
            siguiente_mes = mes + 1
        
        fecha_fin = datetime(siguiente_anio, siguiente_mes, 1) - timedelta(days=1)
        fecha_fin = fecha_fin.strftime('%Y-%m-%d')
        
        cursor.execute('''
        SELECT fecha, tipo_dia, horas_teoricas, turno, descripcion
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ?
        ORDER BY fecha
        ''', (id_empleado, fecha_inicio, fecha_fin))
        
        calendario = []
        for row in cursor.fetchall():
            fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
            
            dia = {
                'fecha': fecha.strftime('%d/%m/%Y'),
                'dia_semana': fecha.strftime('%A'),
                'tipo_dia': row['tipo_dia'],
                'horas_teoricas': row['horas_teoricas'],
                'turno': row['turno'],
                'descripcion': row['descripcion']
            }
            
            calendario.append(dia)
        
        return calendario
    
    def importar_calendario_excel(self, id_empleado: int, excel_path: str) -> Dict:
        """Importa un calendario laboral desde un archivo Excel.
        
        Args:
            id_empleado: ID del empleado
            excel_path: Ruta al archivo Excel
            
        Returns:
            Diccionario con resultado de la importación
        """
        try:
            # Leer Excel
            df = pd.read_excel(excel_path)
            
            # Verificar columnas necesarias
            columnas_requeridas = ['Fecha', 'Tipo']
            for col in columnas_requeridas:
                if col not in df.columns:
                    return {'error': f'Falta la columna {col} en el archivo Excel'}
            
            # Conectar a la base de datos
            cursor = self.conn.cursor()
            
            # Procesar cada fila
            filas_procesadas = 0
            for _, row in df.iterrows():
                fecha = row['Fecha']
                tipo_dia = row['Tipo']
                
                # Convertir fecha si es necesario
                if isinstance(fecha, str):
                    try:
                        fecha = datetime.strptime(fecha, '%d/%m/%Y')
                    except ValueError:
                        continue
                
                # Obtener valores adicionales si existen
                horas_teoricas = row.get('Horas', 8.0 if tipo_dia == 'Laboral' else 0.0)
                turno = row.get('Turno', 'Diurno' if tipo_dia == 'Laboral' else '')
                descripcion = row.get('Descripcion', '')
                
                # Actualizar o insertar en la base de datos
                cursor.execute('''
                UPDATE CalendarioLaboral
                SET tipo_dia = ?, horas_teoricas = ?, turno = ?, descripcion = ?
                WHERE id_empleado = ? AND fecha = ?
                ''', (tipo_dia, horas_teoricas, turno, descripcion, id_empleado, fecha.strftime('%Y-%m-%d')))
                
                # Si no se actualizó ninguna fila, insertar
                if cursor.rowcount == 0:
                    cursor.execute('''
                    INSERT INTO CalendarioLaboral
                    (id_empleado, fecha, tipo_dia, horas_teoricas, turno, descripcion)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (id_empleado, fecha.strftime('%Y-%m-%d'), tipo_dia, horas_teoricas, turno, descripcion))
                
                filas_procesadas += 1
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'filas_procesadas': filas_procesadas
            }
            
        except Exception as e:
            return {'error': f'Error al importar calendario: {str(e)}'}
    
    def exportar_calendario_excel(self, id_empleado: int, anio: int, excel_path: str) -> Dict:
        """Exporta el calendario laboral a un archivo Excel.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            excel_path: Ruta donde guardar el archivo Excel
            
        Returns:
            Diccionario con resultado de la exportación
        """
        try:
            cursor = self.conn.cursor()
            
            # Obtener datos del calendario
            cursor.execute('''
            SELECT fecha, tipo_dia, horas_teoricas, turno, descripcion
            FROM CalendarioLaboral
            WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
            ORDER BY fecha
            ''', (id_empleado, str(anio)))
            
            # Crear DataFrame
            datos = []
            for row in cursor.fetchall():
                fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
                
                datos.append({
                    'Fecha': fecha.strftime('%d/%m/%Y'),
                    'Día': fecha.strftime('%A'),
                    'Tipo': row['tipo_dia'],
                    'Horas': row['horas_teoricas'],
                    'Turno': row['turno'],
                    'Descripción': row['descripcion']
                })
            
            df = pd.DataFrame(datos)
            
            # Guardar a Excel
            df.to_excel(excel_path, index=False)
            
            return {
                'resultado': 'éxito',
                'ruta': excel_path
            }
            
        except Exception as e:
            return {'error': f'Error al exportar calendario: {str(e)}'}


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del extractor
    extractor = ExtractorDatos()
    
    # Procesar archivos PDF
    pdf_nominas = "/home/ubuntu/upload/nominas all_redacted.pdf"
    pdf_saldos = "/home/ubuntu/upload/saldos all_redacted.pdf"
    pdf_tiempos = "/home/ubuntu/upload/tiempos nominas all_redacted.pdf"
    
    # Extraer y procesar datos
    print("Procesando nóminas...")
    nomina_info, conceptos = extractor.procesar_nomina_pdf(pdf_nominas)
    print(f"Información de nómina extraída: {nomina_info}")
    print(f"Conceptos extraídos: {len(conceptos)}")
    
    print("\nProcesando saldos...")
    saldos = extractor.procesar_saldos_pdf(pdf_saldos)
    print(f"Saldos extraídos: {len(saldos)}")
    
    print("\nProcesando tiempos...")
    tiempos = extractor.procesar_tiempos_pdf(pdf_tiempos)
    print(f"Tiempos extraídos: {len(tiempos)}")
    
    # Guardar en base de datos
    print("\nGuardando datos en la base de datos...")
    extractor.guardar_datos_en_bd([nomina_info], conceptos, saldos, tiempos)
    
    print("\nProceso completado.")
