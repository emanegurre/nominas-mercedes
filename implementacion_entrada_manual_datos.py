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
            periodo_fin_dt.strftime('%Y-%m-%d'),
            0.0,  # importe_bruto inicial
            0.0,  # importe_neto inicial
            0     # no guardada inicialmente
        ))
        
        id_simulacion = cursor.lastrowid
        
        # Copiar conceptos de la plantilla
        cursor.execute('''
        SELECT concepto, importe_defecto, es_devengo, es_plus, es_retencion
        FROM ConceptosPlantilla
        WHERE id_plantilla = ?
        ORDER BY orden
        ''', (id_plantilla,))
        
        for row in cursor.fetchall():
            cursor.execute('''
            INSERT INTO ConceptosSimulacion 
            (id_simulacion, concepto, importe, es_devengo, es_plus, es_retencion, comentario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_simulacion,
                row['concepto'],
                row['importe_defecto'],
                row['es_devengo'],
                row['es_plus'],
                row['es_retencion'],
                'Valor inicial de plantilla'
            ))
        
        # Actualizar importes totales
        self._actualizar_totales_simulacion(id_simulacion)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion': id_simulacion,
            'nombre': nombre,
            'periodo': {
                'inicio': periodo_inicio,
                'fin': periodo_fin
            }
        }
    
    def editar_concepto_simulacion(self, id_simulacion: int, concepto: str, 
                                  nuevo_importe: float, comentario: str = None) -> Dict:
        """Edita un concepto en una simulación de nómina.
        
        Args:
            id_simulacion: ID de la simulación
            concepto: Nombre del concepto a editar
            nuevo_importe: Nuevo importe para el concepto
            comentario: Comentario sobre la edición (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('SELECT id_simulacion FROM SimulacionesNomina WHERE id_simulacion = ?', (id_simulacion,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación especificada'
            }
        
        # Verificar que el concepto existe en la simulación
        cursor.execute('''
        SELECT id_concepto_simulacion, importe
        FROM ConceptosSimulacion
        WHERE id_simulacion = ? AND concepto = ?
        ''', (id_simulacion, concepto))
        
        concepto_existente = cursor.fetchone()
        if not concepto_existente:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró el concepto "{concepto}" en la simulación'
            }
        
        importe_anterior = concepto_existente['importe']
        
        # Actualizar concepto
        cursor.execute('''
        UPDATE ConceptosSimulacion
        SET importe = ?, comentario = ?
        WHERE id_concepto_simulacion = ?
        ''', (
            nuevo_importe,
            comentario if comentario else f"Editado manualmente el {datetime.now().strftime('%d/%m/%Y')}",
            concepto_existente['id_concepto_simulacion']
        ))
        
        # Actualizar importes totales
        self._actualizar_totales_simulacion(id_simulacion)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'concepto': concepto,
            'importe_anterior': importe_anterior,
            'importe_nuevo': nuevo_importe
        }
    
    def agregar_concepto_simulacion(self, id_simulacion: int, concepto: str, 
                                   importe: float, es_devengo: bool = True, 
                                   es_plus: bool = False, es_retencion: bool = False, 
                                   comentario: str = None) -> Dict:
        """Agrega un nuevo concepto a una simulación de nómina.
        
        Args:
            id_simulacion: ID de la simulación
            concepto: Nombre del concepto
            importe: Importe del concepto
            es_devengo: Si es un concepto de devengo
            es_plus: Si es un plus
            es_retencion: Si es una retención
            comentario: Comentario sobre el concepto (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('SELECT id_simulacion FROM SimulacionesNomina WHERE id_simulacion = ?', (id_simulacion,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación especificada'
            }
        
        # Verificar que el concepto no existe ya en la simulación
        cursor.execute('''
        SELECT id_concepto_simulacion
        FROM ConceptosSimulacion
        WHERE id_simulacion = ? AND concepto = ?
        ''', (id_simulacion, concepto))
        
        if cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': f'El concepto "{concepto}" ya existe en la simulación'
            }
        
        # Agregar concepto
        cursor.execute('''
        INSERT INTO ConceptosSimulacion 
        (id_simulacion, concepto, importe, es_devengo, es_plus, es_retencion, comentario)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_simulacion,
            concepto,
            importe,
            1 if es_devengo else 0,
            1 if es_plus else 0,
            1 if es_retencion else 0,
            comentario if comentario else f"Agregado manualmente el {datetime.now().strftime('%d/%m/%Y')}"
        ))
        
        id_concepto_simulacion = cursor.lastrowid
        
        # Actualizar importes totales
        self._actualizar_totales_simulacion(id_simulacion)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_concepto_simulacion': id_concepto_simulacion,
            'concepto': concepto,
            'importe': importe
        }
    
    def eliminar_concepto_simulacion(self, id_simulacion: int, concepto: str) -> Dict:
        """Elimina un concepto de una simulación de nómina.
        
        Args:
            id_simulacion: ID de la simulación
            concepto: Nombre del concepto a eliminar
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('SELECT id_simulacion FROM SimulacionesNomina WHERE id_simulacion = ?', (id_simulacion,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación especificada'
            }
        
        # Verificar que el concepto existe en la simulación
        cursor.execute('''
        SELECT id_concepto_simulacion, importe
        FROM ConceptosSimulacion
        WHERE id_simulacion = ? AND concepto = ?
        ''', (id_simulacion, concepto))
        
        concepto_existente = cursor.fetchone()
        if not concepto_existente:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró el concepto "{concepto}" en la simulación'
            }
        
        # Eliminar concepto
        cursor.execute('''
        DELETE FROM ConceptosSimulacion
        WHERE id_concepto_simulacion = ?
        ''', (concepto_existente['id_concepto_simulacion'],))
        
        # Actualizar importes totales
        self._actualizar_totales_simulacion(id_simulacion)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'concepto': concepto,
            'importe_eliminado': concepto_existente['importe']
        }
    
    def guardar_simulacion_nomina(self, id_simulacion: int) -> Dict:
        """Marca una simulación de nómina como guardada.
        
        Args:
            id_simulacion: ID de la simulación
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('SELECT id_simulacion FROM SimulacionesNomina WHERE id_simulacion = ?', (id_simulacion,))
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación especificada'
            }
        
        # Marcar como guardada
        cursor.execute('''
        UPDATE SimulacionesNomina
        SET es_guardada = 1
        WHERE id_simulacion = ?
        ''', (id_simulacion,))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion': id_simulacion,
            'mensaje': 'Simulación guardada correctamente'
        }
    
    def obtener_simulaciones_nomina(self, id_empleado: int = None, 
                                   solo_guardadas: bool = False) -> List[Dict]:
        """Obtiene las simulaciones de nómina disponibles.
        
        Args:
            id_empleado: ID del empleado (opcional)
            solo_guardadas: Si solo se deben obtener simulaciones guardadas
            
        Returns:
            Lista de diccionarios con información de simulaciones
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT s.id_simulacion, s.id_empleado, s.nombre, s.descripcion, 
               s.fecha_creacion, s.periodo_inicio, s.periodo_fin, 
               s.importe_bruto, s.importe_neto, s.es_guardada,
               e.nombre as nombre_empleado
        FROM SimulacionesNomina s
        JOIN Empleados e ON s.id_empleado = e.id_empleado
        '''
        params = []
        
        # Añadir filtros
        where_clauses = []
        
        if id_empleado:
            where_clauses.append('s.id_empleado = ?')
            params.append(id_empleado)
        
        if solo_guardadas:
            where_clauses.append('s.es_guardada = 1')
        
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        # Ordenar por fecha de creación
        query += ' ORDER BY s.fecha_creacion DESC'
        
        cursor.execute(query, params)
        
        simulaciones = []
        for row in cursor.fetchall():
            fecha_creacion = datetime.strptime(row['fecha_creacion'], '%Y-%m-%d')
            periodo_inicio = datetime.strptime(row['periodo_inicio'], '%Y-%m-%d')
            periodo_fin = datetime.strptime(row['periodo_fin'], '%Y-%m-%d')
            
            simulaciones.append({
                'id': row['id_simulacion'],
                'empleado': {
                    'id': row['id_empleado'],
                    'nombre': row['nombre_empleado']
                },
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'fecha_creacion': fecha_creacion.strftime('%d/%m/%Y'),
                'periodo': {
                    'inicio': periodo_inicio.strftime('%d/%m/%Y'),
                    'fin': periodo_fin.strftime('%d/%m/%Y')
                },
                'importe_bruto': row['importe_bruto'],
                'importe_neto': row['importe_neto'],
                'es_guardada': bool(row['es_guardada'])
            })
        
        return simulaciones
    
    def obtener_conceptos_simulacion(self, id_simulacion: int) -> List[Dict]:
        """Obtiene los conceptos de una simulación de nómina.
        
        Args:
            id_simulacion: ID de la simulación
            
        Returns:
            Lista de diccionarios con información de conceptos
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_concepto_simulacion, concepto, importe, es_devengo, 
               es_plus, es_retencion, comentario
        FROM ConceptosSimulacion
        WHERE id_simulacion = ?
        ORDER BY es_devengo DESC, es_retencion, concepto
        ''', (id_simulacion,))
        
        conceptos = []
        for row in cursor.fetchall():
            conceptos.append({
                'id': row['id_concepto_simulacion'],
                'concepto': row['concepto'],
                'importe': row['importe'],
                'es_devengo': bool(row['es_devengo']),
                'es_plus': bool(row['es_plus']),
                'es_retencion': bool(row['es_retencion']),
                'comentario': row['comentario']
            })
        
        return conceptos
    
    def _actualizar_totales_simulacion(self, id_simulacion: int):
        """Actualiza los importes totales de una simulación de nómina.
        
        Args:
            id_simulacion: ID de la simulación
        """
        cursor = self.conn.cursor()
        
        # Calcular importe bruto (suma de devengos)
        cursor.execute('''
        SELECT SUM(importe) as total_bruto
        FROM ConceptosSimulacion
        WHERE id_simulacion = ? AND es_devengo = 1
        ''', (id_simulacion,))
        
        total_bruto = cursor.fetchone()['total_bruto'] or 0
        
        # Calcular retenciones (suma de retenciones)
        cursor.execute('''
        SELECT SUM(importe) as total_retenciones
        FROM ConceptosSimulacion
        WHERE id_simulacion = ? AND es_retencion = 1
        ''', (id_simulacion,))
        
        total_retenciones = cursor.fetchone()['total_retenciones'] or 0
        
        # Calcular importe neto
        total_neto = total_bruto - total_retenciones
        
        # Actualizar simulación
        cursor.execute('''
        UPDATE SimulacionesNomina
        SET importe_bruto = ?, importe_neto = ?
        WHERE id_simulacion = ?
        ''', (total_bruto, total_neto, id_simulacion))
    
    def crear_simulacion_calendario(self, id_empleado: int, nombre: str, 
                                   anio: int, mes: int = None, 
                                   descripcion: str = None) -> Dict:
        """Crea una nueva simulación de calendario laboral.
        
        Args:
            id_empleado: ID del empleado
            nombre: Nombre de la simulación
            anio: Año del calendario
            mes: Mes específico (1-12) (opcional)
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
        
        # Si no se proporciona mes, usar el mes actual
        if mes is None:
            mes = date.today().month
        
        cursor.execute('''
        INSERT INTO SimulacionesCalendario 
        (id_empleado, nombre, descripcion, fecha_creacion, anio, mes, es_guardada)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            nombre,
            descripcion if descripcion else f"Simulación creada el {datetime.now().strftime('%d/%m/%Y')}",
            datetime.now().strftime('%Y-%m-%d'),
            anio,
            mes,
            0  # no guardada inicialmente
        ))
        
        id_simulacion_calendario = cursor.lastrowid
        
        # Crear días del mes
        self._crear_dias_simulacion_calendario(id_simulacion_calendario, anio, mes)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion_calendario': id_simulacion_calendario,
            'nombre': nombre,
            'anio': anio,
            'mes': mes
        }
    
    def _crear_dias_simulacion_calendario(self, id_simulacion_calendario: int, anio: int, mes: int):
        """Crea los días para una simulación de calendario.
        
        Args:
            id_simulacion_calendario: ID de la simulación de calendario
            anio: Año del calendario
            mes: Mes del calendario (1-12)
        """
        cursor = self.conn.cursor()
        
        # Obtener tipos de día y turnos predeterminados
        cursor.execute('SELECT id_tipo_dia FROM TiposDia WHERE codigo = ?', ('LAB',))  # Laborable
        tipo_dia_laborable = cursor.fetchone()
        id_tipo_dia_default = tipo_dia_laborable['id_tipo_dia'] if tipo_dia_laborable else 1
        
        cursor.execute('SELECT id_turno FROM Turnos WHERE codigo = ?', ('M',))  # Mañana
        turno_manana = cursor.fetchone()
        id_turno_default = turno_manana['id_turno'] if turno_manana else 1
        
        # Determinar primer y último día del mes
        primer_dia = date(anio, mes, 1)
        if mes == 12:
            ultimo_dia = date(anio + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(anio, mes + 1, 1) - timedelta(days=1)
        
        # Crear días
        dia_actual = primer_dia
        while dia_actual <= ultimo_dia:
            # Determinar si es fin de semana
            es_fin_semana = dia_actual.weekday() >= 5  # 5=sábado, 6=domingo
            
            # Si es fin de semana, buscar tipo de día para festivo
            if es_fin_semana:
                cursor.execute('SELECT id_tipo_dia FROM TiposDia WHERE codigo = ?', ('FES',))  # Festivo
                tipo_dia_festivo = cursor.fetchone()
                id_tipo_dia = tipo_dia_festivo['id_tipo_dia'] if tipo_dia_festivo else id_tipo_dia_default
            else:
                id_tipo_dia = id_tipo_dia_default
            
            cursor.execute('''
            INSERT INTO DiasSimulacionCalendario 
            (id_simulacion_calendario, fecha, id_tipo_dia, id_turno, horas_teoricas, comentario)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                id_simulacion_calendario,
                dia_actual.strftime('%Y-%m-%d'),
                id_tipo_dia,
                id_turno_default,
                8.0 if not es_fin_semana else 0.0,  # 8 horas para días laborables, 0 para fines de semana
                'Día generado automáticamente'
            ))
            
            # Avanzar al siguiente día
            dia_actual += timedelta(days=1)
    
    def editar_dia_simulacion_calendario(self, id_simulacion_calendario: int, 
                                        fecha: str, id_tipo_dia: int = None, 
                                        id_turno: int = None, horas_teoricas: float = None, 
                                        comentario: str = None) -> Dict:
        """Edita un día en una simulación de calendario.
        
        Args:
            id_simulacion_calendario: ID de la simulación de calendario
            fecha: Fecha del día en formato 'DD/MM/YYYY'
            id_tipo_dia: ID del tipo de día (opcional)
            id_turno: ID del turno (opcional)
            horas_teoricas: Horas teóricas (opcional)
            comentario: Comentario sobre el día (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT id_simulacion_calendario 
        FROM SimulacionesCalendario 
        WHERE id_simulacion_calendario = ?
        ''', (id_simulacion_calendario,))
        
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación de calendario especificada'
            }
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        fecha_db = fecha_dt.strftime('%Y-%m-%d')
        
        # Verificar que el día existe en la simulación
        cursor.execute('''
        SELECT id_dia_simulacion, id_tipo_dia, id_turno, horas_teoricas, comentario
        FROM DiasSimulacionCalendario
        WHERE id_simulacion_calendario = ? AND fecha = ?
        ''', (id_simulacion_calendario, fecha_db))
        
        dia_existente = cursor.fetchone()
        if not dia_existente:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró el día {fecha} en la simulación de calendario'
            }
        
        # Preparar valores a actualizar
        valores = []
        campos = []
        
        if id_tipo_dia is not None:
            campos.append('id_tipo_dia = ?')
            valores.append(id_tipo_dia)
        
        if id_turno is not None:
            campos.append('id_turno = ?')
            valores.append(id_turno)
        
        if horas_teoricas is not None:
            campos.append('horas_teoricas = ?')
            valores.append(horas_teoricas)
        
        if comentario is not None:
            campos.append('comentario = ?')
            valores.append(comentario)
        
        if not campos:
            return {
                'resultado': 'error',
                'mensaje': 'No se proporcionaron valores para actualizar'
            }
        
        # Actualizar día
        query = f"UPDATE DiasSimulacionCalendario SET {', '.join(campos)} WHERE id_dia_simulacion = ?"
        valores.append(dia_existente['id_dia_simulacion'])
        
        cursor.execute(query, valores)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'fecha': fecha,
            'mensaje': 'Día actualizado correctamente'
        }
    
    def guardar_simulacion_calendario(self, id_simulacion_calendario: int) -> Dict:
        """Marca una simulación de calendario como guardada.
        
        Args:
            id_simulacion_calendario: ID de la simulación de calendario
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT id_simulacion_calendario 
        FROM SimulacionesCalendario 
        WHERE id_simulacion_calendario = ?
        ''', (id_simulacion_calendario,))
        
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación de calendario especificada'
            }
        
        # Marcar como guardada
        cursor.execute('''
        UPDATE SimulacionesCalendario
        SET es_guardada = 1
        WHERE id_simulacion_calendario = ?
        ''', (id_simulacion_calendario,))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion_calendario': id_simulacion_calendario,
            'mensaje': 'Simulación de calendario guardada correctamente'
        }
    
    def obtener_simulaciones_calendario(self, id_empleado: int = None, 
                                       solo_guardadas: bool = False) -> List[Dict]:
        """Obtiene las simulaciones de calendario disponibles.
        
        Args:
            id_empleado: ID del empleado (opcional)
            solo_guardadas: Si solo se deben obtener simulaciones guardadas
            
        Returns:
            Lista de diccionarios con información de simulaciones
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT s.id_simulacion_calendario, s.id_empleado, s.nombre, s.descripcion, 
               s.fecha_creacion, s.anio, s.mes, s.es_guardada,
               e.nombre as nombre_empleado
        FROM SimulacionesCalendario s
        JOIN Empleados e ON s.id_empleado = e.id_empleado
        '''
        params = []
        
        # Añadir filtros
        where_clauses = []
        
        if id_empleado:
            where_clauses.append('s.id_empleado = ?')
            params.append(id_empleado)
        
        if solo_guardadas:
            where_clauses.append('s.es_guardada = 1')
        
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        # Ordenar por fecha de creación
        query += ' ORDER BY s.fecha_creacion DESC'
        
        cursor.execute(query, params)
        
        simulaciones = []
        for row in cursor.fetchall():
            fecha_creacion = datetime.strptime(row['fecha_creacion'], '%Y-%m-%d')
            
            simulaciones.append({
                'id': row['id_simulacion_calendario'],
                'empleado': {
                    'id': row['id_empleado'],
                    'nombre': row['nombre_empleado']
                },
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'fecha_creacion': fecha_creacion.strftime('%d/%m/%Y'),
                'anio': row['anio'],
                'mes': row['mes'],
                'mes_nombre': calendar.month_name[row['mes']],
                'es_guardada': bool(row['es_guardada'])
            })
        
        return simulaciones
    
    def obtener_dias_simulacion_calendario(self, id_simulacion_calendario: int) -> List[Dict]:
        """Obtiene los días de una simulación de calendario.
        
        Args:
            id_simulacion_calendario: ID de la simulación de calendario
            
        Returns:
            Lista de diccionarios con información de días
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT d.id_dia_simulacion, d.fecha, d.id_tipo_dia, d.id_turno, 
               d.horas_teoricas, d.comentario,
               t.codigo as tipo_codigo, t.nombre as tipo_nombre, t.color as tipo_color,
               tu.codigo as turno_codigo, tu.nombre as turno_nombre
        FROM DiasSimulacionCalendario d
        JOIN TiposDia t ON d.id_tipo_dia = t.id_tipo_dia
        JOIN Turnos tu ON d.id_turno = tu.id_turno
        WHERE d.id_simulacion_calendario = ?
        ORDER BY d.fecha
        ''', (id_simulacion_calendario,))
        
        dias = []
        for row in cursor.fetchall():
            fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
            
            dias.append({
                'id': row['id_dia_simulacion'],
                'fecha': fecha.strftime('%d/%m/%Y'),
                'dia_semana': calendar.day_name[fecha.weekday()],
                'tipo_dia': {
                    'id': row['id_tipo_dia'],
                    'codigo': row['tipo_codigo'],
                    'nombre': row['tipo_nombre'],
                    'color': row['tipo_color']
                },
                'turno': {
                    'id': row['id_turno'],
                    'codigo': row['turno_codigo'],
                    'nombre': row['turno_nombre']
                },
                'horas_teoricas': row['horas_teoricas'],
                'comentario': row['comentario']
            })
        
        return dias
    
    def crear_simulacion_incremento(self, id_empleado: int, nombre: str, 
                                   concepto: str, valor_anterior: float, 
                                   valor_nuevo: float, fecha_aplicacion: str = None, 
                                   descripcion: str = None) -> Dict:
        """Crea una nueva simulación de incremento salarial.
        
        Args:
            id_empleado: ID del empleado
            nombre: Nombre de la simulación
            concepto: Concepto salarial a incrementar
            valor_anterior: Valor anterior del concepto
            valor_nuevo: Valor nuevo del concepto
            fecha_aplicacion: Fecha de aplicación en formato 'DD/MM/YYYY' (opcional)
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
        
        # Si no se proporciona fecha de aplicación, usar la fecha actual
        if fecha_aplicacion is None:
            fecha_aplicacion = date.today().strftime('%d/%m/%Y')
        
        # Convertir fecha a formato de base de datos
        fecha_aplicacion_dt = datetime.strptime(fecha_aplicacion, '%d/%m/%Y')
        
        # Calcular porcentaje de incremento
        if valor_anterior > 0:
            porcentaje_incremento = ((valor_nuevo - valor_anterior) / valor_anterior) * 100
        else:
            porcentaje_incremento = 100  # Si el valor anterior es 0, el incremento es del 100%
        
        cursor.execute('''
        INSERT INTO SimulacionesIncremento 
        (id_empleado, nombre, descripcion, fecha_creacion, fecha_aplicacion, 
         concepto, valor_anterior, valor_nuevo, porcentaje_incremento, es_guardada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            nombre,
            descripcion if descripcion else f"Simulación creada el {datetime.now().strftime('%d/%m/%Y')}",
            datetime.now().strftime('%Y-%m-%d'),
            fecha_aplicacion_dt.strftime('%Y-%m-%d'),
            concepto,
            valor_anterior,
            valor_nuevo,
            porcentaje_incremento,
            0  # no guardada inicialmente
        ))
        
        id_simulacion_incremento = cursor.lastrowid
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion_incremento': id_simulacion_incremento,
            'nombre': nombre,
            'concepto': concepto,
            'porcentaje_incremento': porcentaje_incremento
        }
    
    def guardar_simulacion_incremento(self, id_simulacion_incremento: int) -> Dict:
        """Marca una simulación de incremento como guardada.
        
        Args:
            id_simulacion_incremento: ID de la simulación de incremento
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT id_simulacion_incremento 
        FROM SimulacionesIncremento 
        WHERE id_simulacion_incremento = ?
        ''', (id_simulacion_incremento,))
        
        if not cursor.fetchone():
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación de incremento especificada'
            }
        
        # Marcar como guardada
        cursor.execute('''
        UPDATE SimulacionesIncremento
        SET es_guardada = 1
        WHERE id_simulacion_incremento = ?
        ''', (id_simulacion_incremento,))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion_incremento': id_simulacion_incremento,
            'mensaje': 'Simulación de incremento guardada correctamente'
        }
    
    def obtener_simulaciones_incremento(self, id_empleado: int = None, 
                                       solo_guardadas: bool = False) -> List[Dict]:
        """Obtiene las simulaciones de incremento disponibles.
        
        Args:
            id_empleado: ID del empleado (opcional)
            solo_guardadas: Si solo se deben obtener simulaciones guardadas
            
        Returns:
            Lista de diccionarios con información de simulaciones
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT s.id_simulacion_incremento, s.id_empleado, s.nombre, s.descripcion, 
               s.fecha_creacion, s.fecha_aplicacion, s.concepto, s.valor_anterior, 
               s.valor_nuevo, s.porcentaje_incremento, s.es_guardada,
               e.nombre as nombre_empleado
        FROM SimulacionesIncremento s
        JOIN Empleados e ON s.id_empleado = e.id_empleado
        '''
        params = []
        
        # Añadir filtros
        where_clauses = []
        
        if id_empleado:
            where_clauses.append('s.id_empleado = ?')
            params.append(id_empleado)
        
        if solo_guardadas:
            where_clauses.append('s.es_guardada = 1')
        
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        # Ordenar por fecha de creación
        query += ' ORDER BY s.fecha_creacion DESC'
        
        cursor.execute(query, params)
        
        simulaciones = []
        for row in cursor.fetchall():
            fecha_creacion = datetime.strptime(row['fecha_creacion'], '%Y-%m-%d')
            fecha_aplicacion = datetime.strptime(row['fecha_aplicacion'], '%Y-%m-%d')
            
            simulaciones.append({
                'id': row['id_simulacion_incremento'],
                'empleado': {
                    'id': row['id_empleado'],
                    'nombre': row['nombre_empleado']
                },
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'fecha_creacion': fecha_creacion.strftime('%d/%m/%Y'),
                'fecha_aplicacion': fecha_aplicacion.strftime('%d/%m/%Y'),
                'concepto': row['concepto'],
                'valor_anterior': row['valor_anterior'],
                'valor_nuevo': row['valor_nuevo'],
                'porcentaje_incremento': row['porcentaje_incremento'],
                'es_guardada': bool(row['es_guardada'])
            })
        
        return simulaciones
    
    def aplicar_simulacion_a_nomina(self, id_simulacion: int) -> Dict:
        """Aplica una simulación de nómina a una nómina real.
        
        Args:
            id_simulacion: ID de la simulación
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT s.id_simulacion, s.id_empleado, s.periodo_inicio, s.periodo_fin, 
               s.importe_bruto, s.importe_neto
        FROM SimulacionesNomina s
        WHERE s.id_simulacion = ?
        ''', (id_simulacion,))
        
        simulacion = cursor.fetchone()
        if not simulacion:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación especificada'
            }
        
        # Crear nómina real a partir de la simulación
        cursor.execute('''
        INSERT INTO Nominas 
        (id_empleado, periodo_inicio, periodo_fin, fecha_pago, 
         importe_bruto, importe_neto, comentario)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            simulacion['id_empleado'],
            simulacion['periodo_inicio'],
            simulacion['periodo_fin'],
            datetime.now().strftime('%Y-%m-%d'),  # fecha de pago = hoy
            simulacion['importe_bruto'],
            simulacion['importe_neto'],
            f"Creada a partir de simulación #{simulacion['id_simulacion']}"
        ))
        
        id_nomina = cursor.lastrowid
        
        # Copiar conceptos de la simulación a la nómina
        cursor.execute('''
        SELECT concepto, importe, es_devengo, es_plus, es_retencion, comentario
        FROM ConceptosSimulacion
        WHERE id_simulacion = ?
        ''', (id_simulacion,))
        
        for row in cursor.fetchall():
            cursor.execute('''
            INSERT INTO ConceptosNomina 
            (id_nomina, concepto, importe, es_devengo, es_plus, es_retencion, comentario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_nomina,
                row['concepto'],
                row['importe'],
                row['es_devengo'],
                row['es_plus'],
                row['es_retencion'],
                row['comentario']
            ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_nomina': id_nomina,
            'id_simulacion': id_simulacion,
            'mensaje': 'Simulación aplicada correctamente a una nueva nómina'
        }
    
    def aplicar_simulacion_a_calendario(self, id_simulacion_calendario: int) -> Dict:
        """Aplica una simulación de calendario al calendario real.
        
        Args:
            id_simulacion_calendario: ID de la simulación de calendario
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT s.id_simulacion_calendario, s.id_empleado, s.anio, s.mes
        FROM SimulacionesCalendario s
        WHERE s.id_simulacion_calendario = ?
        ''', (id_simulacion_calendario,))
        
        simulacion = cursor.fetchone()
        if not simulacion:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación de calendario especificada'
            }
        
        # Obtener días de la simulación
        cursor.execute('''
        SELECT fecha, id_tipo_dia, id_turno, horas_teoricas, comentario
        FROM DiasSimulacionCalendario
        WHERE id_simulacion_calendario = ?
        ''', (id_simulacion_calendario,))
        
        dias_simulacion = cursor.fetchall()
        
        # Para cada día de la simulación, actualizar o crear en el calendario real
        for dia in dias_simulacion:
            # Verificar si el día ya existe en el calendario real
            cursor.execute('''
            SELECT id_calendario
            FROM CalendarioLaboral
            WHERE id_empleado = ? AND fecha = ?
            ''', (simulacion['id_empleado'], dia['fecha']))
            
            dia_existente = cursor.fetchone()
            
            if dia_existente:
                # Actualizar día existente
                cursor.execute('''
                UPDATE CalendarioLaboral
                SET id_tipo_dia = ?, id_turno = ?, horas_teoricas = ?
                WHERE id_calendario = ?
                ''', (
                    dia['id_tipo_dia'],
                    dia['id_turno'],
                    dia['horas_teoricas'],
                    dia_existente['id_calendario']
                ))
            else:
                # Crear nuevo día
                cursor.execute('''
                INSERT INTO CalendarioLaboral 
                (id_empleado, fecha, id_tipo_dia, id_turno, horas_teoricas)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    simulacion['id_empleado'],
                    dia['fecha'],
                    dia['id_tipo_dia'],
                    dia['id_turno'],
                    dia['horas_teoricas']
                ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_simulacion_calendario': id_simulacion_calendario,
            'dias_actualizados': len(dias_simulacion),
            'mensaje': 'Simulación aplicada correctamente al calendario real'
        }
    
    def aplicar_simulacion_a_incremento(self, id_simulacion_incremento: int) -> Dict:
        """Aplica una simulación de incremento al histórico de salarios.
        
        Args:
            id_simulacion_incremento: ID de la simulación de incremento
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT s.id_simulacion_incremento, s.id_empleado, s.fecha_aplicacion, 
               s.concepto, s.valor_anterior, s.valor_nuevo, s.porcentaje_incremento
        FROM SimulacionesIncremento s
        WHERE s.id_simulacion_incremento = ?
        ''', (id_simulacion_incremento,))
        
        simulacion = cursor.fetchone()
        if not simulacion:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación de incremento especificada'
            }
        
        # Registrar incremento en el histórico de salarios
        cursor.execute('''
        INSERT INTO HistoricoSalarios 
        (id_empleado, fecha, concepto, valor_anterior, valor_nuevo, 
         porcentaje_incremento, motivo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            simulacion['id_empleado'],
            simulacion['fecha_aplicacion'],
            simulacion['concepto'],
            simulacion['valor_anterior'],
            simulacion['valor_nuevo'],
            simulacion['porcentaje_incremento'],
            f"Aplicado desde simulación #{simulacion['id_simulacion_incremento']}"
        ))
        
        id_historico = cursor.lastrowid
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_historico': id_historico,
            'id_simulacion_incremento': id_simulacion_incremento,
            'mensaje': 'Simulación aplicada correctamente al histórico de salarios'
        }
    
    def exportar_simulacion_a_json(self, id_simulacion: int) -> Dict:
        """Exporta una simulación de nómina a formato JSON.
        
        Args:
            id_simulacion: ID de la simulación
            
        Returns:
            Diccionario con resultado de la operación y datos JSON
        """
        cursor = self.conn.cursor()
        
        # Verificar que la simulación existe
        cursor.execute('''
        SELECT s.id_simulacion, s.id_empleado, s.nombre, s.descripcion, 
               s.fecha_creacion, s.periodo_inicio, s.periodo_fin, 
               s.importe_bruto, s.importe_neto, s.es_guardada,
               e.nombre as nombre_empleado
        FROM SimulacionesNomina s
        JOIN Empleados e ON s.id_empleado = e.id_empleado
        WHERE s.id_simulacion = ?
        ''', (id_simulacion,))
        
        simulacion = cursor.fetchone()
        if not simulacion:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la simulación especificada'
            }
        
        # Obtener conceptos de la simulación
        cursor.execute('''
        SELECT concepto, importe, es_devengo, es_plus, es_retencion, comentario
        FROM ConceptosSimulacion
        WHERE id_simulacion = ?
        ORDER BY es_devengo DESC, es_retencion, concepto
        ''', (id_simulacion,))
        
        conceptos = []
        for row in cursor.fetchall():
            conceptos.append({
                'concepto': row['concepto'],
                'importe': row['importe'],
                'es_devengo': bool(row['es_devengo']),
                'es_plus': bool(row['es_plus']),
                'es_retencion': bool(row['es_retencion']),
                'comentario': row['comentario']
            })
        
        # Crear estructura JSON
        fecha_creacion = datetime.strptime(simulacion['fecha_creacion'], '%Y-%m-%d')
        periodo_inicio = datetime.strptime(simulacion['periodo_inicio'], '%Y-%m-%d')
        periodo_fin = datetime.strptime(simulacion['periodo_fin'], '%Y-%m-%d')
        
        datos_json = {
            'id_simulacion': simulacion['id_simulacion'],
            'nombre': simulacion['nombre'],
            'descripcion': simulacion['descripcion'],
            'fecha_creacion': fecha_creacion.strftime('%d/%m/%Y'),
            'empleado': {
                'id': simulacion['id_empleado'],
                'nombre': simulacion['nombre_empleado']
            },
            'periodo': {
                'inicio': periodo_inicio.strftime('%d/%m/%Y'),
                'fin': periodo_fin.strftime('%d/%m/%Y')
            },
            'importe_bruto': simulacion['importe_bruto'],
            'importe_neto': simulacion['importe_neto'],
            'conceptos': conceptos
        }
        
        # Convertir a cadena JSON
        json_str = json.dumps(datos_json, indent=2, ensure_ascii=False)
        
        return {
            'resultado': 'éxito',
            'id_simulacion': id_simulacion,
            'json': json_str
        }
    
    def importar_simulacion_desde_json(self, json_str: str, id_empleado: int = None) -> Dict:
        """Importa una simulación de nómina desde formato JSON.
        
        Args:
            json_str: Cadena JSON con los datos de la simulación
            id_empleado: ID del empleado al que asignar la simulación (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Parsear JSON
            datos = json.loads(json_str)
            
            # Verificar estructura mínima
            if 'nombre' not in datos or 'conceptos' not in datos:
                return {
                    'resultado': 'error',
                    'mensaje': 'El JSON no tiene la estructura requerida'
                }
            
            # Usar id_empleado proporcionado o el del JSON
            if id_empleado is None:
                if 'empleado' in datos and 'id' in datos['empleado']:
                    id_empleado = datos['empleado']['id']
                else:
                    return {
                        'resultado': 'error',
                        'mensaje': 'No se proporcionó ID de empleado y no se encontró en el JSON'
                    }
            
            # Verificar que el empleado existe
            cursor = self.conn.cursor()
            cursor.execute('SELECT id_empleado FROM Empleados WHERE id_empleado = ?', (id_empleado,))
            if not cursor.fetchone():
                return {
                    'resultado': 'error',
                    'mensaje': 'No se encontró el empleado especificado'
                }
            
            # Obtener periodo
            periodo_inicio = None
            periodo_fin = None
            
            if 'periodo' in datos:
                if 'inicio' in datos['periodo']:
                    periodo_inicio = datos['periodo']['inicio']
                if 'fin' in datos['periodo']:
                    periodo_fin = datos['periodo']['fin']
            
            # Crear simulación
            resultado = self.crear_simulacion_nomina(
                id_empleado=id_empleado,
                nombre=datos['nombre'],
                descripcion=datos.get('descripcion', f"Importada el {datetime.now().strftime('%d/%m/%Y')}"),
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin
            )
            
            if resultado['resultado'] != 'éxito':
                return resultado
            
            id_simulacion = resultado['id_simulacion']
            
            # Eliminar conceptos predeterminados
            cursor.execute('DELETE FROM ConceptosSimulacion WHERE id_simulacion = ?', (id_simulacion,))
            
            # Importar conceptos
            for concepto_datos in datos['conceptos']:
                self.agregar_concepto_simulacion(
                    id_simulacion=id_simulacion,
                    concepto=concepto_datos['concepto'],
                    importe=concepto_datos['importe'],
                    es_devengo=concepto_datos.get('es_devengo', True),
                    es_plus=concepto_datos.get('es_plus', False),
                    es_retencion=concepto_datos.get('es_retencion', False),
                    comentario=concepto_datos.get('comentario', 'Importado desde JSON')
                )
            
            # Actualizar importes totales
            self._actualizar_totales_simulacion(id_simulacion)
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_simulacion': id_simulacion,
                'nombre': datos['nombre'],
                'conceptos_importados': len(datos['conceptos'])
            }
            
        except json.JSONDecodeError:
            return {
                'resultado': 'error',
                'mensaje': 'El JSON proporcionado no es válido'
            }
        except Exception as e:
            return {
                'resultado': 'error',
                'mensaje': f'Error al importar la simulación: {str(e)}'
            }


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del gestor de entrada manual
    entrada_manual = EntradaManualDatos()
    
    # Crear una plantilla personalizada
    resultado = entrada_manual.crear_plantilla_nomina(
        nombre="Plantilla Personalizada",
        descripcion="Plantilla con conceptos personalizados",
        es_predeterminada=False
    )
    print(f"Plantilla creada: {resultado}")
    
    id_plantilla = resultado['id_plantilla']
    
    # Agregar conceptos a la plantilla
    entrada_manual.agregar_concepto_plantilla(
        id_plantilla=id_plantilla,
        concepto="Salario Base",
        importe_defecto=1500.0,
        es_devengo=True,
        es_plus=False,
        es_retencion=False,
        es_editable=True,
        orden=1
    )
    
    entrada_manual.agregar_concepto_plantilla(
        id_plantilla=id_plantilla,
        concepto="Plus Productividad",
        importe_defecto=200.0,
        es_devengo=True,
        es_plus=True,
        es_retencion=False,
        es_editable=True,
        orden=2
    )
    
    # Crear una simulación de nómina
    id_empleado = 1  # Ajustar según la base de datos
    
    resultado = entrada_manual.crear_simulacion_nomina(
        id_empleado=id_empleado,
        nombre="Simulación de prueba",
        id_plantilla=id_plantilla
    )
    print(f"Simulación creada: {resultado}")
    
    id_simulacion = resultado['id_simulacion']
    
    # Editar un concepto en la simulación
    entrada_manual.editar_concepto_simulacion(
        id_simulacion=id_simulacion,
        concepto="Salario Base",
        nuevo_importe=1600.0,
        comentario="Ajustado por simulación"
    )
    
    # Exportar simulación a JSON
    resultado = entrada_manual.exportar_simulacion_a_json(id_simulacion)
    print(f"Simulación exportada a JSON: {resultado['resultado']}")
    
    print("\nProceso completado.")
