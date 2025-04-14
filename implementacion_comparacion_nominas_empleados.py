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
                datos_nomina['i
(Content truncated due to size limit. Use line ranges to read in chunks)