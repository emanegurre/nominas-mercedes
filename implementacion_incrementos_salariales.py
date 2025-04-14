"""
Módulo de Gestión de Incrementos Salariales

Este módulo implementa la funcionalidad para gestionar los incrementos salariales
pactados en convenio, permitiendo su configuración, aplicación y visualización.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class GestorIncrementosSalariales:
    """Clase para gestionar los incrementos salariales pactados en convenio."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el gestor de incrementos salariales.
        
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
        """Inicializa las tablas necesarias para la gestión de incrementos salariales."""
        cursor = self.conn.cursor()
        
        # Tabla para convenios colectivos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConveniosColectivos (
            id_convenio INTEGER PRIMARY KEY,
            nombre TEXT,
            descripcion TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            ambito TEXT,
            es_activo INTEGER
        )
        ''')
        
        # Tabla para incrementos salariales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS IncrementosSalariales (
            id_incremento INTEGER PRIMARY KEY,
            id_convenio INTEGER,
            concepto TEXT,
            porcentaje REAL,
            cantidad_fija REAL,
            fecha_aplicacion TEXT,
            fecha_fin TEXT,
            es_retroactivo INTEGER,
            fecha_retroactividad TEXT,
            descripcion TEXT,
            FOREIGN KEY (id_convenio) REFERENCES ConveniosColectivos(id_convenio)
        )
        ''')
        
        # Tabla para aplicación de incrementos a empleados
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS IncrementosEmpleados (
            id_incremento_empleado INTEGER PRIMARY KEY,
            id_incremento INTEGER,
            id_empleado INTEGER,
            fecha_aplicacion TEXT,
            salario_anterior REAL,
            salario_nuevo REAL,
            diferencia REAL,
            es_aplicado INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_incremento) REFERENCES IncrementosSalariales(id_incremento),
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Tabla para histórico de salarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS HistoricoSalarios (
            id_historico INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha TEXT,
            concepto TEXT,
            valor_anterior REAL,
            valor_nuevo REAL,
            porcentaje_incremento REAL,
            motivo TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        self.conn.commit()
    
    def crear_convenio(self, nombre: str, descripcion: str, fecha_inicio: str, 
                      fecha_fin: str, ambito: str) -> Dict:
        """Crea un nuevo convenio colectivo.
        
        Args:
            nombre: Nombre del convenio
            descripcion: Descripción del convenio
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            ambito: Ámbito de aplicación (ej. 'Empresa', 'Sectorial')
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        # Desactivar convenios activos en el mismo ámbito
        cursor.execute('''
        UPDATE ConveniosColectivos
        SET es_activo = 0
        WHERE ambito = ? AND es_activo = 1
        ''', (ambito,))
        
        # Insertar nuevo convenio
        cursor.execute('''
        INSERT INTO ConveniosColectivos
        (nombre, descripcion, fecha_inicio, fecha_fin, ambito, es_activo)
        VALUES (?, ?, ?, ?, ?, 1)
        ''', (
            nombre,
            descripcion,
            fecha_inicio_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d'),
            ambito
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_convenio': cursor.lastrowid,
            'nombre': nombre,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    
    def registrar_incremento(self, id_convenio: int, concepto: str, porcentaje: float = None, 
                            cantidad_fija: float = None, fecha_aplicacion: str = None, 
                            fecha_fin: str = None, es_retroactivo: bool = False, 
                            fecha_retroactividad: str = None, descripcion: str = None) -> Dict:
        """Registra un incremento salarial en un convenio.
        
        Args:
            id_convenio: ID del convenio
            concepto: Concepto al que aplica el incremento (ej. 'Salario Base', 'Todos')
            porcentaje: Porcentaje de incremento (opcional)
            cantidad_fija: Cantidad fija de incremento (opcional)
            fecha_aplicacion: Fecha de aplicación en formato 'DD/MM/YYYY' (opcional)
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY' (opcional)
            es_retroactivo: Si el incremento es retroactivo
            fecha_retroactividad: Fecha desde la que aplica retroactivamente (opcional)
            descripcion: Descripción adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que se proporciona al menos un tipo de incremento
        if porcentaje is None and cantidad_fija is None:
            return {
                'resultado': 'error',
                'mensaje': 'Debe proporcionar un porcentaje o una cantidad fija'
            }
        
        # Obtener información del convenio
        cursor.execute('''
        SELECT fecha_inicio, fecha_fin
        FROM ConveniosColectivos
        WHERE id_convenio = ?
        ''', (id_convenio,))
        
        convenio = cursor.fetchone()
        if not convenio:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró el convenio especificado'
            }
        
        # Si no se proporciona fecha de aplicación, usar la fecha actual
        if fecha_aplicacion is None:
            fecha_aplicacion = datetime.now().strftime('%d/%m/%Y')
        
        # Convertir fechas a formato de base de datos
        fecha_aplicacion_dt = datetime.strptime(fecha_aplicacion, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y') if fecha_fin else None
        fecha_retroactividad_dt = datetime.strptime(fecha_retroactividad, '%d/%m/%Y') if fecha_retroactividad else None
        
        # Insertar incremento
        cursor.execute('''
        INSERT INTO IncrementosSalariales
        (id_convenio, concepto, porcentaje, cantidad_fija, fecha_aplicacion, fecha_fin, 
         es_retroactivo, fecha_retroactividad, descripcion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_convenio,
            concepto,
            porcentaje,
            cantidad_fija,
            fecha_aplicacion_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d') if fecha_fin_dt else None,
            1 if es_retroactivo else 0,
            fecha_retroactividad_dt.strftime('%Y-%m-%d') if fecha_retroactividad_dt else None,
            descripcion if descripcion else f"Incremento {concepto} - {fecha_aplicacion}"
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_incremento': cursor.lastrowid,
            'concepto': concepto,
            'porcentaje': porcentaje,
            'cantidad_fija': cantidad_fija,
            'fecha_aplicacion': fecha_aplicacion
        }
    
    def aplicar_incremento_empleado(self, id_incremento: int, id_empleado: int) -> Dict:
        """Aplica un incremento salarial a un empleado específico.
        
        Args:
            id_incremento: ID del incremento
            id_empleado: ID del empleado
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener información del incremento
        cursor.execute('''
        SELECT concepto, porcentaje, cantidad_fija, fecha_aplicacion, es_retroactivo, fecha_retroactividad
        FROM IncrementosSalariales
        WHERE id_incremento = ?
        ''', (id_incremento,))
        
        incremento = cursor.fetchone()
        if not incremento:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró el incremento especificado'
            }
        
        # Obtener salario actual del empleado para el concepto
        salario_actual = self._obtener_salario_concepto(id_empleado, incremento['concepto'])
        
        if salario_actual is None:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró información salarial para el concepto {incremento["concepto"]}'
            }
        
        # Calcular nuevo salario
        nuevo_salario = salario_actual
        
        if incremento['porcentaje'] is not None:
            nuevo_salario += salario_actual * (incremento['porcentaje'] / 100)
        
        if incremento['cantidad_fija'] is not None:
            nuevo_salario += incremento['cantidad_fija']
        
        # Registrar aplicación del incremento
        cursor.execute('''
        INSERT INTO IncrementosEmpleados
        (id_incremento, id_empleado, fecha_aplicacion, salario_anterior, salario_nuevo, 
         diferencia, es_aplicado, comentario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_incremento,
            id_empleado,
            incremento['fecha_aplicacion'],
            salario_actual,
            nuevo_salario,
            nuevo_salario - salario_actual,
            1,
            f"Incremento aplicado el {datetime.now().strftime('%d/%m/%Y')}"
        ))
        
        # Registrar en histórico de salarios
        cursor.execute('''
        INSERT INTO HistoricoSalarios
        (id_empleado, fecha, concepto, valor_anterior, valor_nuevo, porcentaje_incremento, motivo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            incremento['fecha_aplicacion'],
            incremento['concepto'],
            salario_actual,
            nuevo_salario,
            incremento['porcentaje'] if incremento['porcentaje'] else 
            ((nuevo_salario - salario_actual) / salario_actual * 100 if salario_actual > 0 else 0),
            f"Incremento por convenio - {incremento['concepto']}"
        ))
        
        # Actualizar configuración de predicción
        if incremento['concepto'] == 'Salario Base' or incremento['concepto'] == 'Todos':
            cursor.execute('''
            INSERT INTO ConfiguracionPrediccion
            (id_empleado, concepto, valor, fecha_inicio, fecha_fin, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                id_empleado,
                'salario_base',
                nuevo_salario,
                incremento['fecha_aplicacion'],
                None,
                f"Actualizado por incremento salarial"
            ))
        
        self.conn.commit()
        
        # Calcular retroactividad si aplica
        retroactividad = None
        if incremento['es_retroactivo'] and incremento['fecha_retroactividad']:
            retroactividad = self._calcular_retroactividad(
                id_empleado, 
                incremento['concepto'], 
                incremento['fecha_retroactividad'], 
                incremento['fecha_aplicacion'], 
                salario_actual, 
                nuevo_salario
            )
        
        return {
            'resultado': 'éxito',
            'id_empleado': id_empleado,
            'concepto': incremento['concepto'],
            'salario_anterior': salario_actual,
            'salario_nuevo': nuevo_salario,
            'diferencia': nuevo_salario - salario_actual,
            'retroactividad': retroactividad
        }
    
    def _obtener_salario_concepto(self, id_empleado: int, concepto: str) -> float:
        """Obtiene el salario actual de un empleado para un concepto específico.
        
        Args:
            id_empleado: ID del empleado
            concepto: Concepto salarial
            
        Returns:
            Salario actual o None si no se encuentra
        """
        cursor = self.conn.cursor()
        
        # Si el concepto es 'Todos', obtener el salario base
        if concepto == 'Todos':
            concepto = 'Salario Base'
        
        # Buscar en histórico de salarios
        cursor.execute('''
        SELECT valor_nuevo
        FROM HistoricoSalarios
        WHERE id_empleado = ? AND concepto = ?
        ORDER BY fecha DESC
        LIMIT 1
        ''', (id_empleado, concepto))
        
        historico = cursor.fetchone()
        if historico:
            return historico['valor_nuevo']
        
        # Si no hay histórico, buscar en nóminas
        if concepto == 'Salario Base':
            # Buscar en nóminas
            cursor.execute('''
            SELECT n.id_nomina
            FROM Nominas n
            WHERE n.id_empleado = ?
            ORDER BY n.periodo_fin DESC
            LIMIT 1
            ''', (id_empleado,))
            
            nomina = cursor.fetchone()
            if nomina:
                cursor.execute('''
                SELECT importe
                FROM ConceptosNomina
                WHERE id_nomina = ? AND concepto = 'Salario'
                LIMIT 1
                ''', (nomina['id_nomina'],))
                
                concepto_nomina = cursor.fetchone()
                if concepto_nomina:
                    return concepto_nomina['importe']
        
        # Si no se encuentra, buscar en configuración de predicción
        if concepto == 'Salario Base':
            cursor.execute('''
            SELECT valor
            FROM ConfiguracionPrediccion
            WHERE id_empleado = ? AND concepto = 'salario_base'
            ORDER BY fecha_inicio DESC
            LIMIT 1
            ''', (id_empleado,))
            
            config = cursor.fetchone()
            if config:
                return config['valor']
        
        # Si no se encuentra en ninguna parte, devolver None
        return None
    
    def _calcular_retroactividad(self, id_empleado: int, concepto: str, 
                               fecha_inicio: str, fecha_fin: str, 
                               salario_anterior: float, salario_nuevo: float) -> Dict:
        """Calcula la retroactividad de un incremento salarial.
        
        Args:
            id_empleado: ID del empleado
            concepto: Concepto salarial
            fecha_inicio: Fecha de inicio de la retroactividad
            fecha_fin: Fecha de fin de la retroactividad
            salario_anterior: Salario anterior
            salario_nuevo: Salario nuevo
            
        Returns:
         
(Content truncated due to size limit. Use line ranges to read in chunks)