"""
Módulo de Entrada Manual de Datos

Este módulo implementa la funcionalidad para introducir y editar datos manualmente
en el sistema, permitiendo realizar simulaciones y análisis personalizados.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union
import os
import re
import json

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class EntradaManualDatos:
    """Clase para gestionar la entrada manual de datos en el sistema."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el gestor de entrada manual de datos.
        
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
        """Inicializa las tablas necesarias para la entrada manual de datos."""
        cursor = self.conn.cursor()
        
        # Tabla para plantillas de nóminas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS PlantillasNomina (
            id_plantilla INTEGER PRIMARY KEY,
            nombre TEXT,
            descripcion TEXT,
            fecha_creacion TEXT,
            es_predeterminada INTEGER
        )
        ''')
        
        # Tabla para conceptos de plantillas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConceptosPlantilla (
            id_concepto_plantilla INTEGER PRIMARY KEY,
            id_plantilla INTEGER,
            concepto TEXT,
            importe_defecto REAL,
            es_devengo INTEGER,
            es_plus INTEGER,
            es_retencion INTEGER,
            es_editable INTEGER,
            orden INTEGER,
            FOREIGN KEY (id_plantilla) REFERENCES PlantillasNomina(id_plantilla)
        )
        ''')
        
        # Tabla para simulaciones de nóminas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SimulacionesNomina (
            id_simulacion INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            nombre TEXT,
            descripcion TEXT,
            fecha_creacion TEXT,
            periodo_inicio TEXT,
            periodo_fin TEXT,
            importe_bruto REAL,
            importe_neto REAL,
            es_guardada INTEGER,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Tabla para conceptos de simulaciones
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConceptosSimulacion (
            id_concepto_simulacion INTEGER PRIMARY KEY,
            id_simulacion INTEGER,
            concepto TEXT,
            importe REAL,
            es_devengo INTEGER,
            es_plus INTEGER,
            es_retencion INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_simulacion) REFERENCES SimulacionesNomina(id_simulacion)
        )
        ''')
        
        # Tabla para simulaciones de calendario
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SimulacionesCalendario (
            id_simulacion_calendario INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            nombre TEXT,
            descripcion TEXT,
            fecha_creacion TEXT,
            anio INTEGER,
            mes INTEGER,
            es_guardada INTEGER,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Tabla para días de simulaciones de calendario
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS DiasSimulacionCalendario (
            id_dia_simulacion INTEGER PRIMARY KEY,
            id_simulacion_calendario INTEGER,
            fecha TEXT,
            id_tipo_dia INTEGER,
            id_turno INTEGER,
            horas_teoricas REAL,
            comentario TEXT,
            FOREIGN KEY (id_simulacion_calendario) REFERENCES SimulacionesCalendario(id_simulacion_calendario),
            FOREIGN KEY (id_tipo_dia) REFERENCES TiposDia(id_tipo_dia),
            FOREIGN KEY (id_turno) REFERENCES Turnos(id_turno)
        )
        ''')
        
        # Tabla para simulaciones de incrementos salariales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SimulacionesIncremento (
            id_simulacion_incremento INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            nombre TEXT,
            descripcion TEXT,
            fecha_creacion TEXT,
            fecha_aplicacion TEXT,
            concepto TEXT,
            valor_anterior REAL,
            valor_nuevo REAL,
            porcentaje_incremento REAL,
            es_guardada INTEGER,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Insertar plantilla predeterminada si no existe
        cursor.execute('SELECT COUNT(*) as count FROM PlantillasNomina WHERE es_predeterminada = 1')
        if cursor.fetchone()['count'] == 0:
            cursor.execute('''
            INSERT INTO PlantillasNomina 
            (nombre, descripcion, fecha_creacion, es_predeterminada)
            VALUES (?, ?, ?, ?)
            ''', (
                'Plantilla Estándar',
                'Plantilla predeterminada con conceptos comunes',
                datetime.now().strftime('%Y-%m-%d'),
                1
            ))
            
            id_plantilla = cursor.lastrowid
            
            # Insertar conceptos predeterminados
            conceptos_default = [
                # Devengos
                ('Salario Base', 1200.0, 1, 0, 0, 1, 1),
                ('Plus Transporte', 100.0, 1, 1, 0, 1, 2),
                ('Plus Asistencia', 50.0, 1, 1, 0, 1, 3),
                ('Horas Extras', 0.0, 1, 0, 0, 1, 4),
                ('Paga Extra Prorrateada', 200.0, 1, 0, 0, 1, 5),
                ('Complemento Personal', 0.0, 1, 0, 0, 1, 6),
                ('Plus Nocturnidad', 0.0, 1, 1, 0, 1, 7),
                ('Plus Festivo', 0.0, 1, 1, 0, 1, 8),
                
                # Retenciones
                ('IRPF', 0.0, 0, 0, 1, 1, 9),
                ('Seguridad Social', 0.0, 0, 0, 1, 1, 10),
                ('Otros Descuentos', 0.0, 0, 0, 1, 1, 11)
            ]
            
            for concepto in conceptos_default:
                cursor.execute('''
                INSERT INTO ConceptosPlantilla 
                (id_plantilla, concepto, importe_defecto, es_devengo, es_plus, es_retencion, es_editable, orden)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (id_plantilla,) + concepto)
        
        self.conn.commit()
    
    def crear_plantilla_nomina(self, nombre: str, descripcion: str = None, 
                              es_predeterminada: bool = False) -> Dict:
        """Crea una nueva plantilla de nómina.
        
        Args:
            nombre: Nombre de la plantilla
            descripcion: Descripción de la plantilla (opcional)
            es_predeterminada: Si la plantilla debe ser la predeterminada
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Si es predeterminada, quitar marca de predeterminada a otras plantillas
        if es_predeterminada:
            cursor.execute('''
            UPDATE PlantillasNomina
            SET es_predeterminada = 0
            WHERE es_predeterminada = 1
            ''')
        
        cursor.execute('''
        INSERT INTO PlantillasNomina 
        (nombre, descripcion, fecha_creacion, es_predeterminada)
        VALUES (?, ?, ?, ?)
        ''', (
            nombre,
            descripcion if descripcion else f"Creada el {datetime.now().strftime('%d/%m/%Y')}",
            datetime.now().strftime('%Y-%m-%d'),
            1 if es_predeterminada else 0
        ))
        
        id_plantilla = cursor.lastrowid
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_plantilla': id_plantilla,
            'nombre': nombre,
            'es_predeterminada': es_predeterminada
        }
    
    def agregar_concepto_plantilla(self, id_plantilla: int, concepto: str, 
                                  importe_defecto: float = 0.0, es_devengo: bool = True, 
                                  es_plus: bool = False, es_retencion: bool = False, 
                                  es_editable: bool = True, orden: int = None) -> Dict:
        """Agrega un concepto a una plantilla de nómina.
        
        Args:
            id_plantilla: ID de la plantilla
            concepto: Nombre del concepto
            importe_defecto: Importe por defecto
            es_devengo: Si es un concepto de devengo
            es_plus: Si es un plus
            es_retencion: Si es una retención
            es_editable: Si el concepto es editable
            orden: Orden de aparición (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la plantilla existe
        cursor.execute('SELECT id_plantilla FROM PlantillasNomina WHERE id_plantilla = ?', (id_plantilla,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la plantilla especificada'
            }
        
        # Si no se proporciona orden, asignar el siguiente
        if orden is None:
            cursor.execute('''
            SELECT MAX(orden) as max_orden
            FROM ConceptosPlantilla
            WHERE id_plantilla = ?
            ''', (id_plantilla,))
            
            max_orden = cursor.fetchone()['max_orden']
            orden = 1 if max_orden is None else max_orden + 1
        
        cursor.execute('''
        INSERT INTO ConceptosPlantilla 
        (id_plantilla, concepto, importe_defecto, es_devengo, es_plus, es_retencion, es_editable, orden)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_plantilla,
            concepto,
            importe_defecto,
            1 if es_devengo else 0,
            1 if es_plus else 0,
            1 if es_retencion else 0,
            1 if es_editable else 0,
            orden
        ))
        
        id_concepto_plantilla = cursor.lastrowid
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_concepto_plantilla': id_concepto_plantilla,
            'concepto': concepto,
            'orden': orden
        }
    
    def obtener_plantillas_nomina(self) -> List[Dict]:
        """Obtiene todas las plantillas de nómina disponibles.
        
        Returns:
            Lista de diccionarios con información de plantillas
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_plantilla, nombre, descripcion, fecha_creacion, es_predeterminada
        FROM PlantillasNomina
        ORDER BY es_predeterminada DESC, nombre
        ''')
        
        plantillas = []
        for row in cursor.fetchall():
            fecha_creacion = datetime.strptime(row['fecha_creacion'], '%Y-%m-%d')
            
            plantillas.append({
                'id': row['id_plantilla'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'fecha_creacion': fecha_creacion.strftime('%d/%m/%Y'),
                'es_predeterminada': bool(row['es_predeterminada'])
            })
        
        return plantillas
    
    def obtener_conceptos_plantilla(self, id_plantilla: int) -> List[Dict]:
        """Obtiene los conceptos de una plantilla de nómina.
        
        Args:
            id_plantilla: ID de la plantilla
            
        Returns:
            Lista de diccionarios con información de conceptos
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_concepto_plantilla, concepto, importe_defecto, es_devengo, 
               es_plus, es_retencion, es_editable, orden
        FROM ConceptosPlantilla
        WHERE id_plantilla = ?
        ORDER BY orden
        ''', (id_plantilla,))
        
        conceptos = []
        for row in cursor.fetchall():
            conceptos.append({
                'id': row['id_concepto_plantilla'],
                'concepto': row['concepto'],
                'importe_defecto': row['importe_defecto'],
                'es_devengo': bool(row['es_devengo']),
                'es_plus': bool(row['es_plus']),
                'es_retencion': bool(row['es_retencion']),
                'es_editable': bool(row['es_editable']),
                'orden': row['orden']
            })
        
        return conceptos
    
    def crear_simulacion_nomina(self, id_empleado: int, nombre: str, 
                               id_plantilla: int = None, periodo_inicio: str = None, 
                               periodo_fin: str = None, descripcion: str = None) -> Dict:
        """Crea una nueva simulación de nómina.
        
        Args:
            id_empleado: ID del empleado
            nombre: Nombre de la simulación
            id_plantilla: ID de la plantilla a utilizar (opcional)
            periodo_inicio: Fecha de inicio del periodo en formato 'DD/MM/YYYY' (opcional)
            periodo_fin: Fecha de fin del periodo en formato 'DD/MM/YYYY' (opcional)
            descripcion: Descripción de la simulación (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que el empleado existe
        cursor.execute('SELECT id_empleado FROM Empleados WHERE id_empleado = ?', (id_empleado,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró el empleado especificado'
            }
        
        # Si no se proporciona plantilla, usar la predeterminada
        if id_plantilla is None:
            cursor.execute('SELECT id_plantilla FROM PlantillasNomina WHERE es_predeterminada = 1')
            plantilla = cursor.fetchone()
            if plantilla:
                id_plantilla = plantilla['id_plantilla']
            else:
                return {
                    'resultado': 'error',
                    'mensaje': 'No se encontró una plantilla predeterminada'
                }
        
        # Si no se proporcionan fechas, usar el mes actual
        hoy = date.today()
        if periodo_inicio is None:
            primer_dia_mes = date(hoy.year, hoy.month, 1)
            periodo_inicio = primer_dia_mes.strftime('%d/%m/%Y')
        
        if periodo_fin is None:
            if hoy.month == 12:
                ultimo_dia_mes = date(hoy.year + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia_mes = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            periodo_fin = ultimo_dia_mes.strftime('%d/%m/%Y')
        
        # Convertir fechas a formato de base de datos
        periodo_inicio_dt = datetime.strptime(periodo_inicio, '%d/%m/%Y')
        periodo_fin_dt = datetime.strptime(periodo_fin, '%d/%m/%Y')
        
        cursor.execute('''
        INSERT INTO SimulacionesNomina 
        (id_empleado, nombre, descripcion, fecha_creacion, periodo_inicio, periodo_fin, 
         importe_bruto, importe_neto, es_guardada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            nombre,
            descripcion if descripcion else f"Simulación creada el {datetime.now().strftime('%d/%m/%Y')}",
            datetime.now().strftime('%Y-%m-%d'),
            periodo_inicio_dt.strftime('%Y-%m-%d'),
(Content truncated due to size limit. Use line ranges to read in chunks)