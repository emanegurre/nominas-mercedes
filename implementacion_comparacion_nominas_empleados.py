"""
Módulo de Comparación de Nóminas entre Empleados

Este módulo implementa la funcionalidad para comparar nóminas entre diferentes empleados,
permitiendo detectar desviaciones y diferencias según categorías profesionales.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union
import os
import re

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class ComparadorNominasEmpleados:
    """Clase para comparar nóminas entre diferentes empleados."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el comparador de nóminas entre empleados.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._conectar_bd()
        self._inicializar_tablas()
    
    def _conectar_bd(self):
        """Conecta a la base de datos."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    
    def _inicializar_tablas(self):
        """Inicializa las tablas necesarias para la comparación de nóminas."""
        cursor = self.conn.cursor()
        
        # Tabla para categorías profesionales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS CategoriasProfesionales (
            id_categoria INTEGER PRIMARY KEY,
            codigo TEXT UNIQUE,
            nombre TEXT,
            descripcion TEXT,
            salario_base_recomendado REAL,
            nivel INTEGER
        )
        ''')
        
        # Tabla para pluses por categoría
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS PlusesPorCategoria (
            id_plus_categoria INTEGER PRIMARY KEY,
            id_categoria INTEGER,
            nombre_plus TEXT,
            importe_recomendado REAL,
            es_porcentaje INTEGER,
            porcentaje REAL,
            es_obligatorio INTEGER,
            descripcion TEXT,
            FOREIGN KEY (id_categoria) REFERENCES CategoriasProfesionales(id_categoria)
        )
        ''')
        
        # Tabla para empleados de referencia (compañeros)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmpleadosReferencia (
            id_empleado_ref INTEGER PRIMARY KEY,
            nombre TEXT,
            id_categoria INTEGER,
            fecha_alta TEXT,
            es_anonimo INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_categoria) REFERENCES CategoriasProfesionales(id_categoria)
        )
        ''')
        
        # Tabla para nóminas de referencia
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS NominasReferencia (
            id_nomina_ref INTEGER PRIMARY KEY,
            id_empleado_ref INTEGER,
            periodo_inicio TEXT,
            periodo_fin TEXT,
            fecha_pago TEXT,
            importe_bruto REAL,
            importe_neto REAL,
            ruta_archivo TEXT,
            comentario TEXT,
            FOREIGN KEY (id_empleado_ref) REFERENCES EmpleadosReferencia(id_empleado_ref)
        )
        ''')
        
        # Tabla para conceptos de nóminas de referencia
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConceptosNominaReferencia (
            id_concepto_ref INTEGER PRIMARY KEY,
            id_nomina_ref INTEGER,
            concepto TEXT,
            importe REAL,
            es_devengo INTEGER,
            es_plus INTEGER,
            es_retencion INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_nomina_ref) REFERENCES NominasReferencia(id_nomina_ref)
        )
        ''')
        
        # Tabla para comparaciones de nóminas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ComparacionesNominas (
            id_comparacion INTEGER PRIMARY KEY,
            id_nomina INTEGER,
            id_nomina_ref INTEGER,
            fecha_comparacion TEXT,
            descripcion TEXT,
            FOREIGN KEY (id_nomina) REFERENCES Nominas(id_nomina),
            FOREIGN KEY (id_nomina_ref) REFERENCES NominasReferencia(id_nomina_ref)
        )
        ''')
        
        # Tabla para resultados de comparaciones
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ResultadosComparacion (
            id_resultado INTEGER PRIMARY KEY,
            id_comparacion INTEGER,
            concepto TEXT,
            importe_nomina REAL,
            importe_nomina_ref REAL,
            diferencia REAL,
            porcentaje_diferencia REAL,
            es_significativa INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_comparacion) REFERENCES ComparacionesNominas(id_comparacion)
        )
        ''')
        
        # Insertar categorías profesionales predeterminadas si no existen
        cursor.execute('SELECT COUNT(*) as count FROM CategoriasProfesionales')
        if cursor.fetchone()['count'] == 0:
            categorias_default = [
                ('AUX', 'Auxiliar', 'Auxiliar administrativo', 1200.0, 1),
                ('OFI', 'Oficial', 'Oficial administrativo', 1500.0, 2),
                ('TEC', 'Técnico', 'Técnico especialista', 1800.0, 3),
                ('RES', 'Responsable', 'Responsable de área', 2200.0, 4),
                ('DIR', 'Director', 'Director de departamento', 2800.0, 5)
            ]
            
            for categoria in categorias_default:
                cursor.execute('''
                INSERT INTO CategoriasProfesionales 
                (codigo, nombre, descripcion, salario_base_recomendado, nivel)
                VALUES (?, ?, ?, ?, ?)
                ''', categoria)
        
        # Insertar pluses por categoría predeterminados si no existen
        cursor.execute('SELECT COUNT(*) as count FROM PlusesPorCategoria')
        if cursor.fetchone()['count'] == 0:
            # Obtener IDs de categorías
            cursor.execute('SELECT id_categoria, codigo FROM CategoriasProfesionales')
            categorias = {row['codigo']: row['id_categoria'] for row in cursor.fetchall()}
            
            pluses_default = [
                # Auxiliar
                (categorias['AUX'], 'Plus Transporte', 100.0, 0, None, 1, 'Plus de transporte mensual'),
                (categorias['AUX'], 'Plus Asistencia', 50.0, 0, None, 0, 'Plus por asistencia perfecta'),
                
                # Oficial
                (categorias['OFI'], 'Plus Transporte', 100.0, 0, None, 1, 'Plus de transporte mensual'),
                (categorias['OFI'], 'Plus Asistencia', 75.0, 0, None, 0, 'Plus por asistencia perfecta'),
                (categorias['OFI'], 'Plus Responsabilidad', 100.0, 0, None, 0, 'Plus por responsabilidad adicional'),
                
                # Técnico
                (categorias['TEC'], 'Plus Transporte', 120.0, 0, None, 1, 'Plus de transporte mensual'),
                (categorias['TEC'], 'Plus Especialización', 150.0, 0, None, 1, 'Plus por especialización técnica'),
                (categorias['TEC'], 'Plus Disponibilidad', 200.0, 0, None, 0, 'Plus por disponibilidad horaria'),
                
                # Responsable
                (categorias['RES'], 'Plus Transporte', 150.0, 0, None, 1, 'Plus de transporte mensual'),
                (categorias['RES'], 'Plus Responsabilidad', 300.0, 0, None, 1, 'Plus por responsabilidad de área'),
                (categorias['RES'], 'Plus Objetivos', None, 1, 10.0, 0, 'Plus por cumplimiento de objetivos (% sobre salario)'),
                
                # Director
                (categorias['DIR'], 'Plus Transporte', 200.0, 0, None, 1, 'Plus de transporte mensual'),
                (categorias['DIR'], 'Plus Responsabilidad', 500.0, 0, None, 1, 'Plus por responsabilidad directiva'),
                (categorias['DIR'], 'Plus Objetivos', None, 1, 15.0, 1, 'Plus por cumplimiento de objetivos (% sobre salario)')
            ]
            
            for plus in pluses_default:
                cursor.execute('''
                INSERT INTO PlusesPorCategoria 
                (id_categoria, nombre_plus, importe_recomendado, es_porcentaje, porcentaje, es_obligatorio, descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', plus)
        
        self.conn.commit()
    
    def crear_categoria_profesional(self, codigo: str, nombre: str, descripcion: str, 
                                   salario_base_recomendado: float, nivel: int) -> Dict:
        """Crea una nueva categoría profesional.
        
        Args:
            codigo: Código único de la categoría
            nombre: Nombre de la categoría
            descripcion: Descripción de la categoría
            salario_base_recomendado: Salario base recomendado
            nivel: Nivel jerárquico (1-5)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO CategoriasProfesionales 
            (codigo, nombre, descripcion, salario_base_recomendado, nivel)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                codigo,
                nombre,
                descripcion,
                salario_base_recomendado,
                nivel
            ))
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_categoria': cursor.lastrowid,
                'codigo': codigo,
                'nombre': nombre
            }
        except sqlite3.IntegrityError:
            return {
                'resultado': 'error',
                'mensaje': f'Ya existe una categoría con el código {codigo}'
            }
    
    def crear_plus_categoria(self, id_categoria: int, nombre_plus: str, 
                            importe_recomendado: float = None, es_porcentaje: bool = False, 
                            porcentaje: float = None, es_obligatorio: bool = False, 
                            descripcion: str = None) -> Dict:
        """Crea un nuevo plus para una categoría profesional.
        
        Args:
            id_categoria: ID de la categoría
            nombre_plus: Nombre del plus
            importe_recomendado: Importe recomendado (opcional)
            es_porcentaje: Si el plus es un porcentaje del salario
            porcentaje: Porcentaje sobre el salario (opcional)
            es_obligatorio: Si el plus es obligatorio
            descripcion: Descripción del plus (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que se proporciona importe o porcentaje
        if importe_recomendado is None and (not es_porcentaje or porcentaje is None):
            return {
                'resultado': 'error',
                'mensaje': 'Debe proporcionar un importe recomendado o un porcentaje'
            }
        
        try:
            cursor.execute('''
            INSERT INTO PlusesPorCategoria 
            (id_categoria, nombre_plus, importe_recomendado, es_porcentaje, porcentaje, es_obligatorio, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_categoria,
                nombre_plus,
                importe_recomendado,
                1 if es_porcentaje else 0,
                porcentaje,
                1 if es_obligatorio else 0,
                descripcion
            ))
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_plus_categoria': cursor.lastrowid,
                'nombre_plus': nombre_plus
            }
        except sqlite3.IntegrityError:
            return {
                'resultado': 'error',
                'mensaje': 'Error al crear el plus para la categoría'
            }
    
    def registrar_empleado_referencia(self, nombre: str, id_categoria: int, 
                                     fecha_alta: str = None, es_anonimo: bool = False, 
                                     comentario: str = None) -> Dict:
        """Registra un nuevo empleado de referencia (compañero).
        
        Args:
            nombre: Nombre del empleado
            id_categoria: ID de la categoría profesional
            fecha_alta: Fecha de alta en formato 'DD/MM/YYYY' (opcional)
            es_anonimo: Si se debe anonimizar la información
            comentario: Comentario adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Si no se proporciona fecha de alta, usar la fecha actual
        if fecha_alta is None:
            fecha_alta = datetime.now().strftime('%d/%m/%Y')
        
        # Convertir fecha a formato de base de datos
        fecha_alta_dt = datetime.strptime(fecha_alta, '%d/%m/%Y')
        
        cursor.execute('''
        INSERT INTO EmpleadosReferencia 
        (nombre, id_categoria, fecha_alta, es_anonimo, comentario)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            nombre,
            id_categoria,
            fecha_alta_dt.strftime('%Y-%m-%d'),
            1 if es_anonimo else 0,
            comentario
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_empleado_ref': cursor.lastrowid,
            'nombre': nombre if not es_anonimo else f"Anónimo_{cursor.lastrowid}"
        }
    
    def importar_nomina_referencia(self, id_empleado_ref: int, ruta_archivo: str, 
                                  periodo_inicio: str, periodo_fin: str, 
                                  fecha_pago: str = None, comentario: str = None) -> Dict:
        """Importa una nómina de referencia desde un archivo.
        
        Args:
            id_empleado_ref: ID del empleado de referencia
            ruta_archivo: Ruta al archivo de nómina
            periodo_inicio: Fecha de inicio del periodo en formato 'DD/MM/YYYY'
            periodo_fin: Fecha de fin del periodo en formato 'DD/MM/YYYY'
            fecha_pago: Fecha de pago en formato 'DD/MM/YYYY' (opcional)
            comentario: Comentario adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_archivo):
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró el archivo en la ruta {ruta_archivo}'
            }
        
        # Convertir fechas a formato de base de datos
        periodo_inicio_dt = datetime.strptime(periodo_inicio, '%d/%m/%Y')
        periodo_fin_dt = datetime.strptime(periodo_fin, '%d/%m/%Y')
        
        # Si no se proporciona fecha de pago, usar la fecha de fin del periodo
        if fecha_pago is None:
            fecha_pago_dt = periodo_fin_dt
        else:
            fecha_pago_dt = datetime.strptime(fecha_pago, '%d/%m/%Y')
        
        # Extraer datos de la nómina
        try:
            datos_nomina = self._extraer_datos_nomina(ruta_archivo)
            
            if datos_nomina['resultado'] == 'error':
                return datos_nomina
            
            # Registrar nómina de referencia
            cursor.execute('''
            INSERT INTO NominasReferencia 
            (id_empleado_ref, periodo_inicio, periodo_fin, fecha_pago, 
             importe_bruto, importe_neto, ruta_archivo, comentario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_empleado_ref,
                periodo_inicio_dt.strftime('%Y-%m-%d'),
                periodo_fin_dt.strftime('%Y-%m-%d'),
                fecha_pago_dt.strftime('%Y-%m-%d'),
                datos_nomina['importe_bruto'],
                datos_nomina['importe_neto'],
                ruta_archivo,
                comentario if comentario else f"Importada el {datetime.now().strftime('%d/%m/%Y')}"
            ))
            
            id_nomina_ref = cursor.lastrowid
            
            # Registrar conceptos de la nómina
            for concepto in datos_nomina['conceptos']:
                cursor.execute('''
                INSERT INTO ConceptosNominaReferencia 
                (id_nomina_ref, concepto, importe, es_devengo, es_plus, es_retencion, comentario)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    id_nomina_ref,
                    concepto['concepto'],
                    concepto['importe'],
                    1 if concepto['es_devengo'] else 0,
                    1 if concepto['es_plus'] else 0,
                    1 if concepto['es_retencion'] else 0,
                    concepto.get('comentario', '')
                ))
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_nomina_ref': id_nomina_ref,
                'conceptos_importados': len(datos_nomina['conceptos']),
                'importe_bruto': datos_nomina['importe_bruto'],
                'importe_neto': datos_nomina['importe_neto']
            }
            
        except Exception as e:
            return {
                'resultado': 'error',
                'mensaje': f'Error al importar la nómina: {str(e)}'
            }
    
    def _extraer_datos_nomina(self, ruta_archivo: str) -> Dict:
        """Extrae datos de un archivo de nómina.
        
        Args:
            ruta_archivo: Ruta al archivo de nómina
            
        Returns:
            Diccionario con datos extraídos
        """
        # Determinar tipo de archivo
        extension = os.path.splitext(ruta_archivo)[1].lower()
        
        if extension == '.pdf':
            return self._extraer_datos_nomina_pdf(ruta_archivo)
        elif extension in ['.xlsx', '.xls']:
            return self._extraer_datos_nomina_excel(ruta_archivo)
        else:
            return {
                'resultado': 'error',
                'mensaje': f'Formato de archivo no soportado: {extension}'
            }
    
    def _extraer_datos_nomina_pdf(self, ruta_archivo: str) -> Dict:
        """Extrae datos de un archivo PDF de nómina.
        
        Args:
            ruta_archivo: Ruta al archivo PDF
            
        Returns:
            Diccionario con datos extraídos
        """
        try:
            # Aquí iría el código para extraer texto del PDF
            # Por simplicidad, asumimos que ya tenemos un extractor implementado
            # y simulamos el resultado
            
            # En una implementación real, se usaría PyPDF2, pdfplumber o similar
            # para extraer el texto y luego procesarlo
            
            # Simulación de datos extraídos
            conceptos = [
                {'concepto': 'Salario Base', 'importe': 1500.0, 'es_devengo': True, 'es_plus': False, 'es_retencion': False},
                {'concepto': 'Plus Transporte', 'importe': 100.0, 'es_devengo': True, 'es_plus': True, 'es_retencion': False},
                {'concepto': 'Plus Asistencia', 'importe': 75.0, 'es_devengo': True, 'es_plus': True, 'es_retencion': False},
                {'concepto': 'IRPF', 'importe': 225.0, 'es_devengo': False, 'es_plus': False, 'es_retencion': True},
                {'concepto': 'Seguridad Social', 'importe': 95.0, 'es_devengo': False, 'es_plus': False, 'es_retencion': True}
            ]
            
            # Calcular importes totales
            importe_bruto = sum(c['importe'] for c in conceptos if c['es_devengo'])
            importe_retenciones = sum(c['importe'] for c in conceptos if c['es_retencion'])
            importe_neto = importe_bruto - importe_retenciones
            
            return {
                'resultado': 'éxito',
                'conceptos': conceptos,
                'importe_bruto': importe_bruto,
                'importe_neto': importe_neto
            }
            
        except Exception as e:
            return {
                'resultado': 'error',
                'mensaje': f'Error al extraer datos del PDF: {str(e)}'
            }
    
    def _extraer_datos_nomina_excel(self, ruta_archivo: str) -> Dict:
        """Extrae datos de un archivo Excel de nómina.
        
        Args:
            ruta_archivo: Ruta al archivo Excel
            
        Returns:
            Diccionario con datos extraídos
        """
        try:
            # Leer archivo Excel
            df = pd.read_excel(ruta_archivo)
            
            # Verificar columnas necesarias
            columnas_requeridas = ['Concepto', 'Importe']
            for col in columnas_requeridas:
                if col not in df.columns:
                    return {
                        'resultado': 'error',
                        'mensaje': f'Falta la columna {col} en el archivo Excel'
                    }
            
            # Procesar conceptos
            conceptos = []
            
            for _, row in df.iterrows():
                concepto = row['Concepto']
                importe = float(row['Importe'])
                
                # Determinar tipo de concepto
                es_devengo = True
                es_plus = False
                es_retencion = False
                
                # Verificar si es un plus
                if 'plus' in concepto.lower() or 'complemento' in concepto.lower():
                    es_plus = True
                
                # Verificar si es una retención
                if ('irpf' in concepto.lower() or 
                    'seguridad social' in concepto.lower() or 
                    'retención' in concepto.lower() or
                    importe < 0):
                    es_devengo = False
                    es_retencion = True
                    # Convertir importe negativo a positivo para retenciones
                    if importe < 0:
                        importe = abs(importe)
                
                conceptos.append({
                    'concepto': concepto,
                    'importe': importe,
                    'es_devengo': es_devengo,
                    'es_plus': es_plus,
                    'es_retencion': es_retencion
                })
            
            # Calcular importes totales
            importe_bruto = sum(c['importe'] for c in conceptos if c['es_devengo'])
            importe_retenciones = sum(c['importe'] for c in conceptos if c['es_retencion'])
            importe_neto = importe_bruto - importe_retenciones
            
            return {
                'resultado': 'éxito',
                'conceptos': conceptos,
                'importe_bruto': importe_bruto,
                'importe_neto': importe_neto
            }
            
        except Exception as e:
            return {
                'resultado': 'error',
                'mensaje': f'Error al extraer datos del Excel: {str(e)}'
            }
    
    def comparar_nominas(self, id_nomina: int, id_nomina_ref: int, 
                        descripcion: str = None) -> Dict:
        """Compara una nómina propia con una nómina de referencia.
        
        Args:
            id_nomina: ID de la nómina propia
            id_nomina_ref: ID de la nómina de referencia
            descripcion: Descripción de la comparación (opcional)
            
        Returns:
            Diccionario con resultado de la comparación
        """
        cursor = self.conn.cursor()
        
        # Verificar que ambas nóminas existen
        cursor.execute('SELECT id_nomina FROM Nominas WHERE id_nomina = ?', (id_nomina,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la nómina propia especificada'
            }
        
        cursor.execute('SELECT id_nomina_ref FROM NominasReferencia WHERE id_nomina_ref = ?', (id_nomina_ref,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la nómina de referencia especificada'
            }
        
        # Registrar comparación
        cursor.execute('''
        INSERT INTO ComparacionesNominas 
        (id_nomina, id_nomina_ref, fecha_comparacion, descripcion)
        VALUES (?, ?, ?, ?)
        ''', (
            id_nomina,
            id_nomina_ref,
            datetime.now().strftime('%Y-%m-%d'),
            descripcion if descripcion else f"Comparación realizada el {datetime.now().strftime('%d/%m/%Y')}"
        ))
        
        id_comparacion = cursor.lastrowid
        
        # Obtener conceptos de la nómina propia
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ?
        ''', (id_nomina,))
        
        conceptos_nomina = {row['concepto']: row['importe'] for row in cursor.fetchall()}
        
        # Obtener conceptos de la nómina de referencia
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNominaReferencia
        WHERE id_nomina_ref = ?
        ''', (id_nomina_ref,))
        
        conceptos_nomina_ref = {row['concepto']: row['importe'] for row in cursor.fetchall()}
        
        # Comparar conceptos
        resultados = []
        
        # Todos los conceptos únicos
        todos_conceptos = set(list(conceptos_nomina.keys()) + list(conceptos_nomina_ref.keys()))
        
        for concepto in todos_conceptos:
            importe_nomina = conceptos_nomina.get(concepto, 0)
            importe_nomina_ref = conceptos_nomina_ref.get(concepto, 0)
            
            # Calcular diferencia
            diferencia = importe_nomina - importe_nomina_ref
            
            # Calcular porcentaje de diferencia
            if importe_nomina_ref > 0:
                porcentaje_diferencia = (diferencia / importe_nomina_ref) * 100
            elif importe_nomina > 0:
                porcentaje_diferencia = 100  # Si el concepto no existe en la nómina de referencia
            else:
                porcentaje_diferencia = 0
            
            # Determinar si la diferencia es significativa (más del 5%)
            es_significativa = abs(porcentaje_diferencia) > 5
            
            # Generar comentario
            if diferencia == 0:
                comentario = "Sin diferencias"
            elif diferencia > 0:
                comentario = f"Tu nómina tiene un {abs(porcentaje_diferencia):.2f}% más en este concepto"
            else:
                comentario = f"Tu nómina tiene un {abs(porcentaje_diferencia):.2f}% menos en este concepto"
            
            # Registrar resultado
            cursor.execute('''
            INSERT INTO ResultadosComparacion 
            (id_comparacion, concepto, importe_nomina, importe_nomina_ref, 
             diferencia, porcentaje_diferencia, es_significativa, comentario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_comparacion,
                concepto,
                importe_nomina,
                importe_nomina_ref,
                diferencia,
                porcentaje_diferencia,
                1 if es_significativa else 0,
                comentario
            ))
            
            resultados.append({
                'concepto': concepto,
                'importe_nomina': importe_nomina,
                'importe_nomina_ref': importe_nomina_ref,
                'diferencia': diferencia,
                'porcentaje_diferencia': porcentaje_diferencia,
                'es_significativa': es_significativa,
                'comentario': comentario
            })
        
        self.conn.commit()
        
        # Calcular totales
        total_nomina = sum(conceptos_nomina.values())
        total_nomina_ref = sum(conceptos_nomina_ref.values())
        diferencia_total = total_nomina - total_nomina_ref
        
        if total_nomina_ref > 0:
            porcentaje_diferencia_total = (diferencia_total / total_nomina_ref) * 100
        else:
            porcentaje_diferencia_total = 0
        
        return {
            'resultado': 'éxito',
            'id_comparacion': id_comparacion,
            'resultados': resultados,
            'total_nomina': total_nomina,
            'total_nomina_ref': total_nomina_ref,
            'diferencia_total': diferencia_total,
            'porcentaje_diferencia_total': porcentaje_diferencia_total
        }
    
    def comparar_nomina_con_categoria(self, id_nomina: int, id_categoria: int) -> Dict:
        """Compara una nómina con los valores recomendados para una categoría profesional.
        
        Args:
            id_nomina: ID de la nómina
            id_categoria: ID de la categoría profesional
            
        Returns:
            Diccionario con resultado de la comparación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la nómina existe
        cursor.execute('SELECT id_nomina FROM Nominas WHERE id_nomina = ?', (id_nomina,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la nómina especificada'
            }
        
        # Verificar que la categoría existe
        cursor.execute('''
        SELECT codigo, nombre, salario_base_recomendado
        FROM CategoriasProfesionales
        WHERE id_categoria = ?
        ''', (id_categoria,))
        
        categoria = cursor.fetchone()
        if not categoria:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la categoría profesional especificada'
            }
        
        # Obtener pluses recomendados para la categoría
        cursor.execute('''
        SELECT nombre_plus, importe_recomendado, es_porcentaje, porcentaje, es_obligatorio
        FROM PlusesPorCategoria
        WHERE id_categoria = ?
        ''', (id_categoria,))
        
        pluses_recomendados = {}
        for row in cursor.fetchall():
            if row['es_porcentaje'] and row['porcentaje'] is not None:
                # Calcular importe basado en porcentaje del salario base
                importe = categoria['salario_base_recomendado'] * (row['porcentaje'] / 100)
            else:
                importe = row['importe_recomendado']
            
            pluses_recomendados[row['nombre_plus']] = {
                'importe': importe,
                'es_obligatorio': bool(row['es_obligatorio'])
            }
        
        # Obtener conceptos de la nómina
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ?
        ''', (id_nomina,))
        
        conceptos_nomina = {}
        for row in cursor.fetchall():
            conceptos_nomina[row['concepto']] = row['importe']
        
        # Comparar salario base
        salario_base_nomina = conceptos_nomina.get('Salario Base', 0)
        if salario_base_nomina == 0:
            # Buscar concepto similar a salario base
            for concepto, importe in conceptos_nomina.items():
                if 'salario' in concepto.lower() or 'sueldo' in concepto.lower():
                    salario_base_nomina = importe
                    break
        
        diferencia_salario = salario_base_nomina - categoria['salario_base_recomendado']
        if categoria['salario_base_recomendado'] > 0:
            porcentaje_diferencia_salario = (diferencia_salario / categoria['salario_base_recomendado']) * 100
        else:
            porcentaje_diferencia_salario = 0
        
        # Comparar pluses
        resultados_pluses = []
        
        for nombre_plus, datos_plus in pluses_recomendados.items():
            # Buscar el plus en la nómina
            importe_plus_nomina = 0
            for concepto, importe in conceptos_nomina.items():
                if nombre_plus.lower() in concepto.lower():
                    importe_plus_nomina = importe
                    break
            
            diferencia_plus = importe_plus_nomina - datos_plus['importe']
            if datos_plus['importe'] > 0:
                porcentaje_diferencia_plus = (diferencia_plus / datos_plus['importe']) * 100
            elif importe_plus_nomina > 0:
                porcentaje_diferencia_plus = 100
            else:
                porcentaje_diferencia_plus = 0
            
            # Determinar si la diferencia es significativa
            es_significativa = abs(porcentaje_diferencia_plus) > 5
            
            # Generar comentario
            if importe_plus_nomina == 0 and datos_plus['es_obligatorio']:
                comentario = f"Falta el plus obligatorio: {nombre_plus}"
            elif diferencia_plus == 0:
                comentario = "Sin diferencias"
            elif diferencia_plus > 0:
                comentario = f"Tu nómina tiene un {abs(porcentaje_diferencia_plus):.2f}% más en este plus"
            else:
                comentario = f"Tu nómina tiene un {abs(porcentaje_diferencia_plus):.2f}% menos en este plus"
            
            resultados_pluses.append({
                'plus': nombre_plus,
                'importe_nomina': importe_plus_nomina,
                'importe_recomendado': datos_plus['importe'],
                'diferencia': diferencia_plus,
                'porcentaje_diferencia': porcentaje_diferencia_plus,
                'es_obligatorio': datos_plus['es_obligatorio'],
                'es_significativa': es_significativa,
                'comentario': comentario
            })
        
        # Buscar pluses en la nómina que no están en los recomendados
        for concepto, importe in conceptos_nomina.items():
            if ('plus' in concepto.lower() or 'complemento' in concepto.lower()) and concepto not in pluses_recomendados:
                resultados_pluses.append({
                    'plus': concepto,
                    'importe_nomina': importe,
                    'importe_recomendado': 0,
                    'diferencia': importe,
                    'porcentaje_diferencia': 100,
                    'es_obligatorio': False,
                    'es_significativa': True,
                    'comentario': "Plus adicional no contemplado en la categoría"
                })
        
        return {
            'resultado': 'éxito',
            'categoria': {
                'codigo': categoria['codigo'],
                'nombre': categoria['nombre'],
                'salario_base_recomendado': categoria['salario_base_recomendado']
            },
            'salario_base': {
                'importe_nomina': salario_base_nomina,
                'importe_recomendado': categoria['salario_base_recomendado'],
                'diferencia': diferencia_salario,
                'porcentaje_diferencia': porcentaje_diferencia_salario
            },
            'pluses': resultados_pluses
        }
    
    def obtener_categorias_profesionales(self) -> List[Dict]:
        """Obtiene todas las categorías profesionales disponibles.
        
        Returns:
            Lista de diccionarios con información de categorías
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_categoria, codigo, nombre, descripcion, salario_base_recomendado, nivel
        FROM CategoriasProfesionales
        ORDER BY nivel
        ''')
        
        categorias = []
        for row in cursor.fetchall():
            categorias.append({
                'id': row['id_categoria'],
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'salario_base_recomendado': row['salario_base_recomendado'],
                'nivel': row['nivel']
            })
        
        return categorias
    
    def obtener_pluses_categoria(self, id_categoria: int) -> List[Dict]:
        """Obtiene los pluses recomendados para una categoría profesional.
        
        Args:
            id_categoria: ID de la categoría profesional
            
        Returns:
            Lista de diccionarios con información de pluses
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_plus_categoria, nombre_plus, importe_recomendado, 
               es_porcentaje, porcentaje, es_obligatorio, descripcion
        FROM PlusesPorCategoria
        WHERE id_categoria = ?
        ORDER BY nombre_plus
        ''', (id_categoria,))
        
        pluses = []
        for row in cursor.fetchall():
            pluses.append({
                'id': row['id_plus_categoria'],
                'nombre': row['nombre_plus'],
                'importe_recomendado': row['importe_recomendado'],
                'es_porcentaje': bool(row['es_porcentaje']),
                'porcentaje': row['porcentaje'],
                'es_obligatorio': bool(row['es_obligatorio']),
                'descripcion': row['descripcion']
            })
        
        return pluses
    
    def obtener_empleados_referencia(self) -> List[Dict]:
        """Obtiene todos los empleados de referencia registrados.
        
        Returns:
            Lista de diccionarios con información de empleados
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT e.id_empleado_ref, e.nombre, e.fecha_alta, e.es_anonimo, e.comentario,
               c.id_categoria, c.codigo as categoria_codigo, c.nombre as categoria_nombre
        FROM EmpleadosReferencia e
        JOIN CategoriasProfesionales c ON e.id_categoria = c.id_categoria
        ORDER BY e.nombre
        ''')
        
        empleados = []
        for row in cursor.fetchall():
            fecha_alta = datetime.strptime(row['fecha_alta'], '%Y-%m-%d')
            
            nombre_mostrar = row['nombre']
            if row['es_anonimo']:
                nombre_mostrar = f"Anónimo_{row['id_empleado_ref']}"
            
            empleados.append({
                'id': row['id_empleado_ref'],
                'nombre': nombre_mostrar,
                'fecha_alta': fecha_alta.strftime('%d/%m/%Y'),
                'categoria': {
                    'id': row['id_categoria'],
                    'codigo': row['categoria_codigo'],
                    'nombre': row['categoria_nombre']
                },
                'es_anonimo': bool(row['es_anonimo']),
                'comentario': row['comentario']
            })
        
        return empleados
    
    def obtener_nominas_referencia(self, id_empleado_ref: int = None) -> List[Dict]:
        """Obtiene las nóminas de referencia registradas.
        
        Args:
            id_empleado_ref: ID del empleado de referencia (opcional)
            
        Returns:
            Lista de diccionarios con información de nóminas
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT n.id_nomina_ref, n.periodo_inicio, n.periodo_fin, n.fecha_pago, 
               n.importe_bruto, n.importe_neto, n.comentario,
               e.id_empleado_ref, e.nombre, e.es_anonimo
        FROM NominasReferencia n
        JOIN EmpleadosReferencia e ON n.id_empleado_ref = e.id_empleado_ref
        '''
        params = []
        
        # Añadir filtro de empleado si se proporciona
        if id_empleado_ref:
            query += ' WHERE n.id_empleado_ref = ?'
            params.append(id_empleado_ref)
        
        # Ordenar por fecha
        query += ' ORDER BY n.periodo_fin DESC'
        
        cursor.execute(query, params)
        
        nominas = []
        for row in cursor.fetchall():
            periodo_inicio = datetime.strptime(row['periodo_inicio'], '%Y-%m-%d')
            periodo_fin = datetime.strptime(row['periodo_fin'], '%Y-%m-%d')
            fecha_pago = datetime.strptime(row['fecha_pago'], '%Y-%m-%d')
            
            nombre_mostrar = row['nombre']
            if row['es_anonimo']:
                nombre_mostrar = f"Anónimo_{row['id_empleado_ref']}"
            
            nominas.append({
                'id': row['id_nomina_ref'],
                'empleado': {
                    'id': row['id_empleado_ref'],
                    'nombre': nombre_mostrar
                },
                'periodo': {
                    'inicio': periodo_inicio.strftime('%d/%m/%Y'),
                    'fin': periodo_fin.strftime('%d/%m/%Y')
                },
                'fecha_pago': fecha_pago.strftime('%d/%m/%Y'),
                'importe_bruto': row['importe_bruto'],
                'importe_neto': row['importe_neto'],
                'comentario': row['comentario']
            })
        
        return nominas
    
    def obtener_conceptos_nomina_referencia(self, id_nomina_ref: int) -> List[Dict]:
        """Obtiene los conceptos de una nómina de referencia.
        
        Args:
            id_nomina_ref: ID de la nómina de referencia
            
        Returns:
            Lista de diccionarios con información de conceptos
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_concepto_ref, concepto, importe, es_devengo, es_plus, es_retencion, comentario
        FROM ConceptosNominaReferencia
        WHERE id_nomina_ref = ?
        ORDER BY concepto
        ''', (id_nomina_ref,))
        
        conceptos = []
        for row in cursor.fetchall():
            conceptos.append({
                'id': row['id_concepto_ref'],
                'concepto': row['concepto'],
                'importe': row['importe'],
                'es_devengo': bool(row['es_devengo']),
                'es_plus': bool(row['es_plus']),
                'es_retencion': bool(row['es_retencion']),
                'comentario': row['comentario']
            })
        
        return conceptos
    
    def obtener_comparaciones(self, id_nomina: int = None) -> List[Dict]:
        """Obtiene las comparaciones de nóminas realizadas.
        
        Args:
            id_nomina: ID de la nómina propia (opcional)
            
        Returns:
            Lista de diccionarios con información de comparaciones
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT c.id_comparacion, c.fecha_comparacion, c.descripcion,
               n.id_nomina, n.periodo_inicio as n_periodo_inicio, n.periodo_fin as n_periodo_fin,
               nr.id_nomina_ref, nr.periodo_inicio as nr_periodo_inicio, nr.periodo_fin as nr_periodo_fin,
               e.nombre, e.es_anonimo, e.id_empleado_ref
        FROM ComparacionesNominas c
        JOIN Nominas n ON c.id_nomina = n.id_nomina
        JOIN NominasReferencia nr ON c.id_nomina_ref = nr.id_nomina_ref
        JOIN EmpleadosReferencia e ON nr.id_empleado_ref = e.id_empleado_ref
        '''
        params = []
        
        # Añadir filtro de nómina si se proporciona
        if id_nomina:
            query += ' WHERE c.id_nomina = ?'
            params.append(id_nomina)
        
        # Ordenar por fecha
        query += ' ORDER BY c.fecha_comparacion DESC'
        
        cursor.execute(query, params)
        
        comparaciones = []
        for row in cursor.fetchall():
            fecha_comparacion = datetime.strptime(row['fecha_comparacion'], '%Y-%m-%d')
            n_periodo_inicio = datetime.strptime(row['n_periodo_inicio'], '%Y-%m-%d')
            n_periodo_fin = datetime.strptime(row['n_periodo_fin'], '%Y-%m-%d')
            nr_periodo_inicio = datetime.strptime(row['nr_periodo_inicio'], '%Y-%m-%d')
            nr_periodo_fin = datetime.strptime(row['nr_periodo_fin'], '%Y-%m-%d')
            
            nombre_mostrar = row['nombre']
            if row['es_anonimo']:
                nombre_mostrar = f"Anónimo_{row['id_empleado_ref']}"
            
            comparaciones.append({
                'id': row['id_comparacion'],
                'fecha': fecha_comparacion.strftime('%d/%m/%Y'),
                'descripcion': row['descripcion'],
                'nomina_propia': {
                    'id': row['id_nomina'],
                    'periodo': {
                        'inicio': n_periodo_inicio.strftime('%d/%m/%Y'),
                        'fin': n_periodo_fin.strftime('%d/%m/%Y')
                    }
                },
                'nomina_referencia': {
                    'id': row['id_nomina_ref'],
                    'periodo': {
                        'inicio': nr_periodo_inicio.strftime('%d/%m/%Y'),
                        'fin': nr_periodo_fin.strftime('%d/%m/%Y')
                    },
                    'empleado': nombre_mostrar
                }
            })
        
        return comparaciones
    
    def obtener_resultados_comparacion(self, id_comparacion: int) -> Dict:
        """Obtiene los resultados de una comparación de nóminas.
        
        Args:
            id_comparacion: ID de la comparación
            
        Returns:
            Diccionario con resultados de la comparación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la comparación existe
        cursor.execute('SELECT id_comparacion FROM ComparacionesNominas WHERE id_comparacion = ?', (id_comparacion,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la comparación especificada'
            }
        
        # Obtener información de la comparación
        cursor.execute('''
        SELECT c.fecha_comparacion, c.descripcion,
               n.id_nomina, n.periodo_inicio as n_periodo_inicio, n.periodo_fin as n_periodo_fin,
               nr.id_nomina_ref, nr.periodo_inicio as nr_periodo_inicio, nr.periodo_fin as nr_periodo_fin,
               e.nombre, e.es_anonimo, e.id_empleado_ref
        FROM ComparacionesNominas c
        JOIN Nominas n ON c.id_nomina = n.id_nomina
        JOIN NominasReferencia nr ON c.id_nomina_ref = nr.id_nomina_ref
        JOIN EmpleadosReferencia e ON nr.id_empleado_ref = e.id_empleado_ref
        WHERE c.id_comparacion = ?
        ''', (id_comparacion,))
        
        info_comparacion = cursor.fetchone()
        fecha_comparacion = datetime.strptime(info_comparacion['fecha_comparacion'], '%Y-%m-%d')
        n_periodo_inicio = datetime.strptime(info_comparacion['n_periodo_inicio'], '%Y-%m-%d')
        n_periodo_fin = datetime.strptime(info_comparacion['n_periodo_fin'], '%Y-%m-%d')
        nr_periodo_inicio = datetime.strptime(info_comparacion['nr_periodo_inicio'], '%Y-%m-%d')
        nr_periodo_fin = datetime.strptime(info_comparacion['nr_periodo_fin'], '%Y-%m-%d')
        
        nombre_mostrar = info_comparacion['nombre']
        if info_comparacion['es_anonimo']:
            nombre_mostrar = f"Anónimo_{info_comparacion['id_empleado_ref']}"
        
        # Obtener resultados de la comparación
        cursor.execute('''
        SELECT concepto, importe_nomina, importe_nomina_ref, diferencia, 
               porcentaje_diferencia, es_significativa, comentario
        FROM ResultadosComparacion
        WHERE id_comparacion = ?
        ORDER BY ABS(porcentaje_diferencia) DESC
        ''', (id_comparacion,))
        
        resultados = []
        for row in cursor.fetchall():
            resultados.append({
                'concepto': row['concepto'],
                'importe_nomina': row['importe_nomina'],
                'importe_nomina_ref': row['importe_nomina_ref'],
                'diferencia': row['diferencia'],
                'porcentaje_diferencia': row['porcentaje_diferencia'],
                'es_significativa': bool(row['es_significativa']),
                'comentario': row['comentario']
            })
        
        # Calcular totales
        total_nomina = sum(r['importe_nomina'] for r in resultados)
        total_nomina_ref = sum(r['importe_nomina_ref'] for r in resultados)
        diferencia_total = total_nomina - total_nomina_ref
        
        if total_nomina_ref > 0:
            porcentaje_diferencia_total = (diferencia_total / total_nomina_ref) * 100
        else:
            porcentaje_diferencia_total = 0
        
        return {
            'resultado': 'éxito',
            'id_comparacion': id_comparacion,
            'fecha': fecha_comparacion.strftime('%d/%m/%Y'),
            'descripcion': info_comparacion['descripcion'],
            'nomina_propia': {
                'id': info_comparacion['id_nomina'],
                'periodo': {
                    'inicio': n_periodo_inicio.strftime('%d/%m/%Y'),
                    'fin': n_periodo_fin.strftime('%d/%m/%Y')
                }
            },
            'nomina_referencia': {
                'id': info_comparacion['id_nomina_ref'],
                'periodo': {
                    'inicio': nr_periodo_inicio.strftime('%d/%m/%Y'),
                    'fin': nr_periodo_fin.strftime('%d/%m/%Y')
                },
                'empleado': nombre_mostrar
            },
            'resultados': resultados,
            'totales': {
                'nomina': total_nomina,
                'nomina_ref': total_nomina_ref,
                'diferencia': diferencia_total,
                'porcentaje_diferencia': porcentaje_diferencia_total
            }
        }
    
    def editar_concepto_nomina_referencia(self, id_concepto_ref: int, 
                                         nuevo_importe: float = None, 
                                         nuevo_comentario: str = None) -> Dict:
        """Edita un concepto de una nómina de referencia.
        
        Args:
            id_concepto_ref: ID del concepto de la nómina de referencia
            nuevo_importe: Nuevo importe (opcional)
            nuevo_comentario: Nuevo comentario (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que el concepto existe
        cursor.execute('''
        SELECT c.id_concepto_ref, c.concepto, c.importe, c.comentario, n.id_nomina_ref
        FROM ConceptosNominaReferencia c
        JOIN NominasReferencia n ON c.id_nomina_ref = n.id_nomina_ref
        WHERE c.id_concepto_ref = ?
        ''', (id_concepto_ref,))
        
        concepto = cursor.fetchone()
        if not concepto:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró el concepto especificado'
            }
        
        # Preparar valores a actualizar
        valores = []
        campos = []
        
        if nuevo_importe is not None:
            campos.append('importe = ?')
            valores.append(nuevo_importe)
        
        if nuevo_comentario is not None:
            campos.append('comentario = ?')
            valores.append(nuevo_comentario)
        
        if not campos:
            return {
                'resultado': 'error',
                'mensaje': 'No se proporcionaron valores para actualizar'
            }
        
        # Actualizar concepto
        query = f"UPDATE ConceptosNominaReferencia SET {', '.join(campos)} WHERE id_concepto_ref = ?"
        valores.append(id_concepto_ref)
        
        cursor.execute(query, valores)
        
        # Actualizar importes totales de la nómina
        self._actualizar_totales_nomina_referencia(concepto['id_nomina_ref'])
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_concepto_ref': id_concepto_ref,
            'concepto': concepto['concepto'],
            'importe_anterior': concepto['importe'],
            'importe_nuevo': nuevo_importe if nuevo_importe is not None else concepto['importe']
        }
    
    def _actualizar_totales_nomina_referencia(self, id_nomina_ref: int):
        """Actualiza los importes totales de una nómina de referencia.
        
        Args:
            id_nomina_ref: ID de la nómina de referencia
        """
        cursor = self.conn.cursor()
        
        # Calcular importe bruto (suma de devengos)
        cursor.execute('''
        SELECT SUM(importe) as total_bruto
        FROM ConceptosNominaReferencia
        WHERE id_nomina_ref = ? AND es_devengo = 1
        ''', (id_nomina_ref,))
        
        total_bruto = cursor.fetchone()['total_bruto'] or 0
        
        # Calcular retenciones (suma de retenciones)
        cursor.execute('''
        SELECT SUM(importe) as total_retenciones
        FROM ConceptosNominaReferencia
        WHERE id_nomina_ref = ? AND es_retencion = 1
        ''', (id_nomina_ref,))
        
        total_retenciones = cursor.fetchone()['total_retenciones'] or 0
        
        # Calcular importe neto
        total_neto = total_bruto - total_retenciones
        
        # Actualizar nómina
        cursor.execute('''
        UPDATE NominasReferencia
        SET importe_bruto = ?, importe_neto = ?
        WHERE id_nomina_ref = ?
        ''', (total_bruto, total_neto, id_nomina_ref))


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del comparador de nóminas
    comparador = ComparadorNominasEmpleados()
    
    # Registrar un empleado de referencia
    id_categoria = 2  # Ajustar según la base de datos
    resultado = comparador.registrar_empleado_referencia(
        nombre="Compañero de Trabajo",
        id_categoria=id_categoria,
        es_anonimo=True,
        comentario="Mismo departamento, misma categoría"
    )
    print(f"Empleado de referencia registrado: {resultado}")
    
    # Importar nómina de referencia
    id_empleado_ref = resultado['id_empleado_ref']
    ruta_archivo = "/ruta/a/nomina_ejemplo.xlsx"  # Ajustar según el entorno
    
    # Simulación de importación (en un entorno real se usaría un archivo existente)
    print("Simulando importación de nómina de referencia...")
    
    # Comparar nóminas
    id_nomina = 1  # Ajustar según la base de datos
    id_nomina_ref = 1  # Ajustar según la base de datos
    
    print("Simulando comparación de nóminas...")
    
    print("\nProceso completado.")
