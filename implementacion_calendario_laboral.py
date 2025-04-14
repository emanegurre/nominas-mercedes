"""
Módulo de Calendario Laboral Personalizable

Este módulo implementa la funcionalidad para gestionar un calendario laboral
completamente personalizable, permitiendo configurar diferentes tipos de días,
turnos, festivos, vacaciones y otros eventos relevantes.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union
import holidays

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class CalendarioLaboral:
    """Clase para gestionar el calendario laboral personalizable."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el gestor de calendario laboral.
        
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
        """Inicializa las tablas necesarias para el calendario laboral."""
        cursor = self.conn.cursor()
        
        # Tabla para tipos de día
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TiposDia (
            id_tipo_dia INTEGER PRIMARY KEY,
            codigo TEXT UNIQUE,
            nombre TEXT,
            descripcion TEXT,
            color TEXT,
            horas_computables REAL,
            es_laboral INTEGER,
            es_festivo INTEGER,
            es_vacaciones INTEGER,
            es_licencia INTEGER
        )
        ''')
        
        # Tabla para turnos de trabajo
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Turnos (
            id_turno INTEGER PRIMARY KEY,
            codigo TEXT UNIQUE,
            nombre TEXT,
            descripcion TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            horas_jornada REAL,
            es_nocturno INTEGER,
            es_rotativo INTEGER,
            color TEXT
        )
        ''')
        
        # Tabla para el calendario laboral
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS CalendarioLaboral (
            id_calendario INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha TEXT,
            id_tipo_dia INTEGER,
            id_turno INTEGER,
            horas_teoricas REAL,
            descripcion TEXT,
            es_manual INTEGER,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado),
            FOREIGN KEY (id_tipo_dia) REFERENCES TiposDia(id_tipo_dia),
            FOREIGN KEY (id_turno) REFERENCES Turnos(id_turno)
        )
        ''')
        
        # Tabla para patrones de calendario
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS PatronesCalendario (
            id_patron INTEGER PRIMARY KEY,
            nombre TEXT,
            descripcion TEXT,
            dias_semana TEXT,
            id_tipo_dia INTEGER,
            id_turno INTEGER,
            FOREIGN KEY (id_tipo_dia) REFERENCES TiposDia(id_tipo_dia),
            FOREIGN KEY (id_turno) REFERENCES Turnos(id_turno)
        )
        ''')
        
        # Insertar tipos de día predeterminados si no existen
        cursor.execute('SELECT COUNT(*) as count FROM TiposDia')
        if cursor.fetchone()['count'] == 0:
            tipos_dia_default = [
                ('LAB', 'Laboral', 'Día laboral normal', '#FFFFFF', 8.0, 1, 0, 0, 0),
                ('FES', 'Festivo', 'Día festivo', '#FF9999', 0.0, 0, 1, 0, 0),
                ('VAC', 'Vacaciones', 'Día de vacaciones', '#99CCFF', 0.0, 0, 0, 1, 0),
                ('LIC', 'Licencia', 'Día de licencia retribuida', '#FFCC99', 0.0, 0, 0, 0, 1),
                ('BAJ', 'Baja', 'Día de baja médica', '#CC99FF', 0.0, 0, 0, 0, 1),
                ('FTR', 'Festivo Trabajado', 'Día festivo trabajado', '#FF6666', 8.0, 1, 1, 0, 0),
                ('DIS', 'Disfrute', 'Día de disfrute de horas acumuladas', '#99FF99', 0.0, 0, 0, 0, 1)
            ]
            
            for tipo in tipos_dia_default:
                cursor.execute('''
                INSERT INTO TiposDia 
                (codigo, nombre, descripcion, color, horas_computables, es_laboral, es_festivo, es_vacaciones, es_licencia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tipo)
        
        # Insertar turnos predeterminados si no existen
        cursor.execute('SELECT COUNT(*) as count FROM Turnos')
        if cursor.fetchone()['count'] == 0:
            turnos_default = [
                ('M', 'Mañana', 'Turno de mañana', '06:00', '14:00', 8.0, 0, 0, '#FFFF99'),
                ('T', 'Tarde', 'Turno de tarde', '14:00', '22:00', 8.0, 0, 0, '#FFCC66'),
                ('N', 'Noche', 'Turno de noche', '22:00', '06:00', 8.0, 1, 0, '#9999FF'),
                ('P', 'Partido', 'Turno partido', '09:00', '18:00', 8.0, 0, 0, '#99FFCC'),
                ('R', 'Rotativo', 'Turno rotativo', '00:00', '00:00', 8.0, 0, 1, '#CC99CC')
            ]
            
            for turno in turnos_default:
                cursor.execute('''
                INSERT INTO Turnos 
                (codigo, nombre, descripcion, hora_inicio, hora_fin, horas_jornada, es_nocturno, es_rotativo, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', turno)
        
        self.conn.commit()
    
    def crear_tipo_dia(self, codigo: str, nombre: str, descripcion: str, color: str, 
                      horas_computables: float, es_laboral: bool, es_festivo: bool, 
                      es_vacaciones: bool, es_licencia: bool) -> Dict:
        """Crea un nuevo tipo de día.
        
        Args:
            codigo: Código único del tipo de día
            nombre: Nombre del tipo de día
            descripcion: Descripción del tipo de día
            color: Color en formato hexadecimal
            horas_computables: Horas computables para este tipo de día
            es_laboral: Si es un día laboral
            es_festivo: Si es un día festivo
            es_vacaciones: Si es un día de vacaciones
            es_licencia: Si es un día de licencia
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO TiposDia 
            (codigo, nombre, descripcion, color, horas_computables, es_laboral, es_festivo, es_vacaciones, es_licencia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                codigo,
                nombre,
                descripcion,
                color,
                horas_computables,
                1 if es_laboral else 0,
                1 if es_festivo else 0,
                1 if es_vacaciones else 0,
                1 if es_licencia else 0
            ))
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_tipo_dia': cursor.lastrowid,
                'codigo': codigo,
                'nombre': nombre
            }
        except sqlite3.IntegrityError:
            return {
                'resultado': 'error',
                'mensaje': f'Ya existe un tipo de día con el código {codigo}'
            }
    
    def crear_turno(self, codigo: str, nombre: str, descripcion: str, hora_inicio: str, 
                   hora_fin: str, horas_jornada: float, es_nocturno: bool, 
                   es_rotativo: bool, color: str) -> Dict:
        """Crea un nuevo turno de trabajo.
        
        Args:
            codigo: Código único del turno
            nombre: Nombre del turno
            descripcion: Descripción del turno
            hora_inicio: Hora de inicio (formato HH:MM)
            hora_fin: Hora de fin (formato HH:MM)
            horas_jornada: Horas de la jornada
            es_nocturno: Si es un turno nocturno
            es_rotativo: Si es un turno rotativo
            color: Color en formato hexadecimal
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO Turnos 
            (codigo, nombre, descripcion, hora_inicio, hora_fin, horas_jornada, es_nocturno, es_rotativo, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                codigo,
                nombre,
                descripcion,
                hora_inicio,
                hora_fin,
                horas_jornada,
                1 if es_nocturno else 0,
                1 if es_rotativo else 0,
                color
            ))
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_turno': cursor.lastrowid,
                'codigo': codigo,
                'nombre': nombre
            }
        except sqlite3.IntegrityError:
            return {
                'resultado': 'error',
                'mensaje': f'Ya existe un turno con el código {codigo}'
            }
    
    def obtener_tipos_dia(self) -> List[Dict]:
        """Obtiene todos los tipos de día disponibles.
        
        Returns:
            Lista de diccionarios con información de tipos de día
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_tipo_dia, codigo, nombre, descripcion, color, horas_computables, 
               es_laboral, es_festivo, es_vacaciones, es_licencia
        FROM TiposDia
        ORDER BY codigo
        ''')
        
        tipos_dia = []
        for row in cursor.fetchall():
            tipos_dia.append({
                'id': row['id_tipo_dia'],
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'color': row['color'],
                'horas_computables': row['horas_computables'],
                'es_laboral': bool(row['es_laboral']),
                'es_festivo': bool(row['es_festivo']),
                'es_vacaciones': bool(row['es_vacaciones']),
                'es_licencia': bool(row['es_licencia'])
            })
        
        return tipos_dia
    
    def obtener_turnos(self) -> List[Dict]:
        """Obtiene todos los turnos disponibles.
        
        Returns:
            Lista de diccionarios con información de turnos
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_turno, codigo, nombre, descripcion, hora_inicio, hora_fin, 
               horas_jornada, es_nocturno, es_rotativo, color
        FROM Turnos
        ORDER BY codigo
        ''')
        
        turnos = []
        for row in cursor.fetchall():
            turnos.append({
                'id': row['id_turno'],
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'hora_inicio': row['hora_inicio'],
                'hora_fin': row['hora_fin'],
                'horas_jornada': row['horas_jornada'],
                'es_nocturno': bool(row['es_nocturno']),
                'es_rotativo': bool(row['es_rotativo']),
                'color': row['color']
            })
        
        return turnos
    
    def crear_calendario_anual(self, id_empleado: int, anio: int, 
                              id_tipo_dia_laboral: int = None, 
                              id_turno_default: int = None) -> Dict:
        """Crea un calendario laboral anual para un empleado.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            id_tipo_dia_laboral: ID del tipo de día para días laborables (opcional)
            id_turno_default: ID del turno por defecto (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener tipo de día laboral si no se proporciona
        if id_tipo_dia_laboral is None:
            cursor.execute('''
            SELECT id_tipo_dia
            FROM TiposDia
            WHERE codigo = 'LAB'
            LIMIT 1
            ''')
            
            tipo_dia_row = cursor.fetchone()
            if tipo_dia_row:
                id_tipo_dia_laboral = tipo_dia_row['id_tipo_dia']
            else:
                return {
                    'resultado': 'error',
                    'mensaje': 'No se encontró un tipo de día laboral'
                }
        
        # Obtener tipo de día festivo
        cursor.execute('''
        SELECT id_tipo_dia
        FROM TiposDia
        WHERE codigo = 'FES'
        LIMIT 1
        ''')
        
        tipo_dia_festivo_row = cursor.fetchone()
        id_tipo_dia_festivo = tipo_dia_festivo_row['id_tipo_dia'] if tipo_dia_festivo_row else None
        
        if id_tipo_dia_festivo is None:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró un tipo de día festivo'
            }
        
        # Obtener turno por defecto si no se proporciona
        if id_turno_default is None:
            cursor.execute('''
            SELECT id_turno
            FROM Turnos
            WHERE codigo = 'M'
            LIMIT 1
            ''')
            
            turno_row = cursor.fetchone()
            if turno_row:
                id_turno_default = turno_row['id_turno']
        
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
        fecha_inicio = date(anio, 1, 1)
        fecha_fin = date(anio, 12, 31)
        
        # Obtener festivos nacionales para España (o el país correspondiente)
        festivos = holidays.Spain(years=anio)
        
        # Crear cada día del año
        dia_actual = fecha_inicio
        dias_creados = 0
        
        while dia_actual <= fecha_fin:
            # Determinar tipo de día
            if dia_actual in festivos:
                # Festivo nacional
                id_tipo_dia = id_tipo_dia_festivo
                id_turno = None
                horas_teoricas = 0.0
                descripcion = f"Festivo: {festivos[dia_actual]}"
            elif dia_actual.weekday() >= 5:  # 5 y 6 son sábado y domingo
                # Fin de semana
                id_tipo_dia = id_tipo_dia_festivo
                id_turno = None
                horas_teoricas = 0.0
                descripcion = "Fin de semana"
            else:
                # Día laboral
                id_tipo_dia = id_tipo_dia_laboral
                id_turno = id_turno_default
                
                # Obtener horas computables del tipo de día
                cursor.execute('''
                SELECT horas_computables
                FROM TiposDia
                WHERE id_tipo_dia = ?
                ''', (id_tipo_dia,))
                
                tipo_dia_row = cursor.fetchone()
                horas_teoricas = tipo_dia_row['horas_computables'] if tipo_dia_row else 8.0
                
                descripcion = "Día laboral"
            
            # Insertar día en el calendario
            cursor.execute('''
            INSERT INTO CalendarioLaboral
            (id_empl
(Content truncated due to size limit. Use line ranges to read in chunks)