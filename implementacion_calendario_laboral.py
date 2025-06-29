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
            (id_empleado, fecha, id_tipo_dia, id_turno, horas_teoricas, descripcion, es_manual)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_empleado,
                dia_actual.strftime('%Y-%m-%d'),
                id_tipo_dia,
                id_turno,
                horas_teoricas,
                descripcion,
                0  # No es manual
            ))
            
            dias_creados += 1
            dia_actual += timedelta(days=1)
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'anio': anio,
            'dias_creados': dias_creados,
            'mensaje': f'Calendario creado para el año {anio}'
        }
    
    def establecer_dia(self, id_empleado: int, fecha: str, id_tipo_dia: int, 
                      id_turno: int = None, horas_teoricas: float = None, 
                      descripcion: str = None) -> Dict:
        """Establece o modifica un día específico en el calendario.
        
        Args:
            id_empleado: ID del empleado
            fecha: Fecha en formato 'DD/MM/YYYY'
            id_tipo_dia: ID del tipo de día
            id_turno: ID del turno (opcional)
            horas_teoricas: Horas teóricas (opcional)
            descripcion: Descripción adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        
        # Si no se proporcionan horas teóricas, obtener del tipo de día
        if horas_teoricas is None:
            cursor.execute('''
            SELECT horas_computables
            FROM TiposDia
            WHERE id_tipo_dia = ?
            ''', (id_tipo_dia,))
            
            tipo_dia_row = cursor.fetchone()
            horas_teoricas = tipo_dia_row['horas_computables'] if tipo_dia_row else 0.0
        
        # Verificar si ya existe este día en el calendario
        cursor.execute('''
        SELECT id_calendario
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha = ?
        ''', (id_empleado, fecha_dt.strftime('%Y-%m-%d')))
        
        dia_existente = cursor.fetchone()
        
        if dia_existente:
            # Actualizar día existente
            cursor.execute('''
            UPDATE CalendarioLaboral
            SET id_tipo_dia = ?, id_turno = ?, horas_teoricas = ?, descripcion = ?, es_manual = 1
            WHERE id_calendario = ?
            ''', (
                id_tipo_dia,
                id_turno,
                horas_teoricas,
                descripcion if descripcion is not None else "Modificado manualmente",
                dia_existente['id_calendario']
            ))
        else:
            # Insertar nuevo día
            cursor.execute('''
            INSERT INTO CalendarioLaboral
            (id_empleado, fecha, id_tipo_dia, id_turno, horas_teoricas, descripcion, es_manual)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (
                id_empleado,
                fecha_dt.strftime('%Y-%m-%d'),
                id_tipo_dia,
                id_turno,
                horas_teoricas,
                descripcion if descripcion is not None else "Creado manualmente"
            ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'fecha': fecha,
            'id_tipo_dia': id_tipo_dia,
            'id_turno': id_turno,
            'horas_teoricas': horas_teoricas
        }
    
    def establecer_periodo(self, id_empleado: int, fecha_inicio: str, fecha_fin: str, 
                          id_tipo_dia: int, id_turno: int = None, 
                          horas_teoricas: float = None, descripcion: str = None) -> Dict:
        """Establece o modifica un periodo de días en el calendario.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            id_tipo_dia: ID del tipo de día
            id_turno: ID del turno (opcional)
            horas_teoricas: Horas teóricas (opcional)
            descripcion: Descripción adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        # Verificar que la fecha de inicio es anterior o igual a la fecha de fin
        if fecha_inicio_dt > fecha_fin_dt:
            return {
                'resultado': 'error',
                'mensaje': 'La fecha de inicio debe ser anterior o igual a la fecha de fin'
            }
        
        # Establecer cada día del periodo
        dia_actual = fecha_inicio_dt
        dias_modificados = 0
        
        while dia_actual <= fecha_fin_dt:
            resultado = self.establecer_dia(
                id_empleado=id_empleado,
                fecha=dia_actual.strftime('%d/%m/%Y'),
                id_tipo_dia=id_tipo_dia,
                id_turno=id_turno,
                horas_teoricas=horas_teoricas,
                descripcion=descripcion
            )
            
            if resultado['resultado'] == 'éxito':
                dias_modificados += 1
            
            dia_actual += timedelta(days=1)
        
        return {
            'resultado': 'éxito',
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'dias_modificados': dias_modificados,
            'id_tipo_dia': id_tipo_dia,
            'id_turno': id_turno
        }
    
    def establecer_vacaciones(self, id_empleado: int, fecha_inicio: str, 
                             fecha_fin: str, descripcion: str = None) -> Dict:
        """Establece un periodo de vacaciones en el calendario.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            descripcion: Descripción adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener tipo de día de vacaciones
        cursor.execute('''
        SELECT id_tipo_dia
        FROM TiposDia
        WHERE codigo = 'VAC'
        LIMIT 1
        ''')
        
        tipo_dia_row = cursor.fetchone()
        if not tipo_dia_row:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró un tipo de día para vacaciones'
            }
        
        id_tipo_dia_vacaciones = tipo_dia_row['id_tipo_dia']
        
        # Establecer periodo de vacaciones
        return self.establecer_periodo(
            id_empleado=id_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_tipo_dia=id_tipo_dia_vacaciones,
            id_turno=None,
            horas_teoricas=0.0,
            descripcion=descripcion if descripcion is not None else "Vacaciones"
        )
    
    def establecer_festivos(self, id_empleado: int, anio: int, 
                           festivos_adicionales: List[str] = None) -> Dict:
        """Establece los días festivos en el calendario.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            festivos_adicionales: Lista de fechas festivas adicionales en formato 'DD/MM/YYYY' (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener tipo de día festivo
        cursor.execute('''
        SELECT id_tipo_dia
        FROM TiposDia
        WHERE codigo = 'FES'
        LIMIT 1
        ''')
        
        tipo_dia_row = cursor.fetchone()
        if not tipo_dia_row:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró un tipo de día festivo'
            }
        
        id_tipo_dia_festivo = tipo_dia_row['id_tipo_dia']
        
        # Obtener festivos nacionales para España (o el país correspondiente)
        festivos = holidays.Spain(years=anio)
        
        # Convertir festivos a formato 'DD/MM/YYYY'
        festivos_nacionales = [fecha.strftime('%d/%m/%Y') for fecha in festivos.keys()]
        
        # Combinar con festivos adicionales
        todos_festivos = festivos_nacionales
        if festivos_adicionales:
            todos_festivos.extend(festivos_adicionales)
        
        # Establecer cada festivo
        festivos_establecidos = 0
        
        for festivo in todos_festivos:
            fecha_dt = datetime.strptime(festivo, '%d/%m/%Y')
            
            # Solo procesar festivos del año especificado
            if fecha_dt.year == anio:
                descripcion = f"Festivo: {festivos.get(fecha_dt.date(), 'Festivo adicional')}" if fecha_dt.date() in festivos else "Festivo adicional"
                
                resultado = self.establecer_dia(
                    id_empleado=id_empleado,
                    fecha=festivo,
                    id_tipo_dia=id_tipo_dia_festivo,
                    id_turno=None,
                    horas_teoricas=0.0,
                    descripcion=descripcion
                )
                
                if resultado['resultado'] == 'éxito':
                    festivos_establecidos += 1
        
        return {
            'resultado': 'éxito',
            'anio': anio,
            'festivos_establecidos': festivos_establecidos
        }
    
    def establecer_patron_semanal(self, id_empleado: int, fecha_inicio: str, 
                                 fecha_fin: str, patron: Dict[int, Dict]) -> Dict:
        """Establece un patrón semanal en el calendario.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            patron: Diccionario con patrón semanal {dia_semana: {id_tipo_dia, id_turno, horas_teoricas}}
                   donde dia_semana es 0 (lunes) a 6 (domingo)
            
        Returns:
            Diccionario con resultado de la operación
        """
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        # Verificar que la fecha de inicio es anterior o igual a la fecha de fin
        if fecha_inicio_dt > fecha_fin_dt:
            return {
                'resultado': 'error',
                'mensaje': 'La fecha de inicio debe ser anterior o igual a la fecha de fin'
            }
        
        # Establecer cada día según el patrón
        dia_actual = fecha_inicio_dt
        dias_modificados = 0
        
        while dia_actual <= fecha_fin_dt:
            # Obtener día de la semana (0 = lunes, 6 = domingo)
            dia_semana = dia_actual.weekday()
            
            # Verificar si hay configuración para este día de la semana
            if dia_semana in patron:
                config_dia = patron[dia_semana]
                
                resultado = self.establecer_dia(
                    id_empleado=id_empleado,
                    fecha=dia_actual.strftime('%d/%m/%Y'),
                    id_tipo_dia=config_dia.get('id_tipo_dia'),
                    id_turno=config_dia.get('id_turno'),
                    horas_teoricas=config_dia.get('horas_teoricas'),
                    descripcion=config_dia.get('descripcion', f"Patrón semanal - Día {dia_semana}")
                )
                
                if resultado['resultado'] == 'éxito':
                    dias_modificados += 1
            
            dia_actual += timedelta(days=1)
        
        return {
            'resultado': 'éxito',
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'dias_modificados': dias_modificados
        }
    
    def guardar_patron(self, nombre: str, descripcion: str, 
                      dias_semana: List[int], id_tipo_dia: int, 
                      id_turno: int = None) -> Dict:
        """Guarda un patrón de calendario para uso futuro.
        
        Args:
            nombre: Nombre del patrón
            descripcion: Descripción del patrón
            dias_semana: Lista de días de la semana (0-6)
            id_tipo_dia: ID del tipo de día
            id_turno: ID del turno (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Convertir lista de días a string
        dias_semana_str = ','.join(map(str, dias_semana))
        
        cursor.execute('''
        INSERT INTO PatronesCalendario
        (nombre, descripcion, dias_semana, id_tipo_dia, id_turno)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            nombre,
            descripcion,
            dias_semana_str,
            id_tipo_dia,
            id_turno
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_patron': cursor.lastrowid,
            'nombre': nombre
        }
    
    def aplicar_patron(self, id_empleado: int, id_patron: int, 
                      fecha_inicio: str, fecha_fin: str) -> Dict:
        """Aplica un patrón guardado al calendario.
        
        Args:
            id_empleado: ID del empleado
            id_patron: ID del patrón
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener información del patrón
        cursor.execute('''
        SELECT nombre, descripcion, dias_semana, id_tipo_dia, id_turno
        FROM PatronesCalendario
        WHERE id_patron = ?
        ''', (id_patron,))
        
        patron_row = cursor.fetchone()
        if not patron_row:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró el patrón especificado'
            }
        
        # Convertir string de días a lista
        dias_semana = [int(dia) for dia in patron_row['dias_semana'].split(',')]
        
        # Crear patrón
        patron = {}
        for dia in dias_semana:
            patron[dia] = {
                'id_tipo_dia': patron_row['id_tipo_dia'],
                'id_turno': patron_row['id_turno'],
                'descripcion': f"Patrón: {patron_row['nombre']}"
            }
        
        # Aplicar patrón
        return self.establecer_patron_semanal(
            id_empleado=id_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            patron=patron
        )
    
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
        fecha_inicio = date(anio, mes, 1)
        if mes == 12:
            fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
        else:
            fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
        
        # Obtener días del calendario
        cursor.execute('''
        SELECT c.fecha, c.horas_teoricas, c.descripcion, c.es_manual,
               t.id_tipo_dia, t.codigo as tipo_codigo, t.nombre as tipo_nombre, t.color as tipo_color,
               tu.id_turno, tu.codigo as turno_codigo, tu.nombre as turno_nombre, tu.color as turno_color
        FROM CalendarioLaboral c
        LEFT JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        LEFT JOIN Turnos tu ON c.id_turno = tu.id_turno
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ?
        ORDER BY c.fecha
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        calendario = []
        for row in cursor.fetchall():
            fecha_db = datetime.strptime(row['fecha'], '%Y-%m-%d')
            
            dia = {
                'fecha': fecha_db.strftime('%d/%m/%Y'),
                'dia_semana': fecha_db.strftime('%A'),
                'dia_mes': fecha_db.day,
                'tipo_dia': {
                    'id': row['id_tipo_dia'],
                    'codigo': row['tipo_codigo'],
                    'nombre': row['tipo_nombre'],
                    'color': row['tipo_color']
                },
                'turno': None,
                'horas_teoricas': row['horas_teoricas'],
                'descripcion': row['descripcion'],
                'es_manual': bool(row['es_manual'])
            }
            
            if row['id_turno']:
                dia['turno'] = {
                    'id': row['id_turno'],
                    'codigo': row['turno_codigo'],
                    'nombre': row['turno_nombre'],
                    'color': row['turno_color']
                }
            
            calendario.append(dia)
        
        return calendario
    
    def obtener_calendario_anual(self, id_empleado: int, anio: int) -> Dict[int, List[Dict]]:
        """Obtiene el calendario laboral de un año completo.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            
        Returns:
            Diccionario con meses como claves y listas de días como valores
        """
        calendario_anual = {}
        
        for mes in range(1, 13):
            calendario_anual[mes] = self.obtener_calendario_mensual(id_empleado, anio, mes)
        
        return calendario_anual
    
    def obtener_resumen_anual(self, id_empleado: int, anio: int) -> Dict:
        """Obtiene un resumen del calendario anual.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            
        Returns:
            Diccionario con resumen del calendario anual
        """
        cursor = self.conn.cursor()
        
        # Fechas de inicio y fin del año
        fecha_inicio = date(anio, 1, 1)
        fecha_fin = date(anio, 12, 31)
        
        # Obtener resumen por tipo de día
        cursor.execute('''
        SELECT t.codigo, t.nombre, COUNT(*) as dias
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ?
        GROUP BY t.id_tipo_dia
        ORDER BY dias DESC
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        resumen_tipos = []
        for row in cursor.fetchall():
            resumen_tipos.append({
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'dias': row['dias']
            })
        
        # Obtener resumen por turno
        cursor.execute('''
        SELECT tu.codigo, tu.nombre, COUNT(*) as dias
        FROM CalendarioLaboral c
        JOIN Turnos tu ON c.id_turno = tu.id_turno
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ?
        GROUP BY tu.id_turno
        ORDER BY dias DESC
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        resumen_turnos = []
        for row in cursor.fetchall():
            resumen_turnos.append({
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'dias': row['dias']
            })
        
        # Obtener total de horas teóricas
        cursor.execute('''
        SELECT SUM(horas_teoricas) as total_horas
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ?
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        total_horas = cursor.fetchone()['total_horas'] or 0
        
        # Obtener días laborables
        cursor.execute('''
        SELECT COUNT(*) as dias_laborables
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ? AND t.es_laboral = 1
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        dias_laborables = cursor.fetchone()['dias_laborables'] or 0
        
        # Obtener días festivos
        cursor.execute('''
        SELECT COUNT(*) as dias_festivos
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ? AND t.es_festivo = 1
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        dias_festivos = cursor.fetchone()['dias_festivos'] or 0
        
        # Obtener días de vacaciones
        cursor.execute('''
        SELECT COUNT(*) as dias_vacaciones
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ? AND t.es_vacaciones = 1
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        dias_vacaciones = cursor.fetchone()['dias_vacaciones'] or 0
        
        return {
            'anio': anio,
            'total_dias': (fecha_fin - fecha_inicio).days + 1,
            'dias_laborables': dias_laborables,
            'dias_festivos': dias_festivos,
            'dias_vacaciones': dias_vacaciones,
            'total_horas_teoricas': total_horas,
            'resumen_tipos': resumen_tipos,
            'resumen_turnos': resumen_turnos
        }
    
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
                    return {
                        'resultado': 'error',
                        'mensaje': f'Falta la columna {col} en el archivo Excel'
                    }
            
            cursor = self.conn.cursor()
            
            # Mapeo de tipos de día
            cursor.execute('SELECT codigo, id_tipo_dia FROM TiposDia')
            tipos_dia = {row['codigo']: row['id_tipo_dia'] for row in cursor.fetchall()}
            
            # Mapeo de turnos
            cursor.execute('SELECT codigo, id_turno FROM Turnos')
            turnos = {row['codigo']: row['id_turno'] for row in cursor.fetchall()}
            
            # Procesar cada fila
            filas_procesadas = 0
            filas_error = 0
            
            for _, row in df.iterrows():
                try:
                    fecha = row['Fecha']
                    tipo_codigo = row['Tipo']
                    
                    # Convertir fecha si es necesario
                    if isinstance(fecha, str):
                        try:
                            fecha = datetime.strptime(fecha, '%d/%m/%Y')
                        except ValueError:
                            filas_error += 1
                            continue
                    elif isinstance(fecha, pd.Timestamp):
                        fecha = fecha.to_pydatetime()
                    
                    # Obtener ID del tipo de día
                    id_tipo_dia = tipos_dia.get(tipo_codigo)
                    if id_tipo_dia is None:
                        filas_error += 1
                        continue
                    
                    # Obtener ID del turno si existe
                    id_turno = None
                    if 'Turno' in row and row['Turno'] in turnos:
                        id_turno = turnos[row['Turno']]
                    
                    # Obtener horas teóricas si existen
                    horas_teoricas = None
                    if 'Horas' in row:
                        horas_teoricas = row['Horas']
                    
                    # Obtener descripción si existe
                    descripcion = None
                    if 'Descripcion' in row:
                        descripcion = row['Descripcion']
                    
                    # Establecer día en el calendario
                    resultado = self.establecer_dia(
                        id_empleado=id_empleado,
                        fecha=fecha.strftime('%d/%m/%Y'),
                        id_tipo_dia=id_tipo_dia,
                        id_turno=id_turno,
                        horas_teoricas=horas_teoricas,
                        descripcion=descripcion
                    )
                    
                    if resultado['resultado'] == 'éxito':
                        filas_procesadas += 1
                    else:
                        filas_error += 1
                
                except Exception:
                    filas_error += 1
            
            return {
                'resultado': 'éxito',
                'filas_procesadas': filas_procesadas,
                'filas_error': filas_error
            }
            
        except Exception as e:
            return {
                'resultado': 'error',
                'mensaje': f'Error al importar calendario: {str(e)}'
            }
    
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
            SELECT c.fecha, c.horas_teoricas, c.descripcion, c.es_manual,
                   t.codigo as tipo_codigo, t.nombre as tipo_nombre,
                   tu.codigo as turno_codigo, tu.nombre as turno_nombre
            FROM CalendarioLaboral c
            LEFT JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
            LEFT JOIN Turnos tu ON c.id_turno = tu.id_turno
            WHERE c.id_empleado = ? AND strftime('%Y', c.fecha) = ?
            ORDER BY c.fecha
            ''', (id_empleado, str(anio)))
            
            # Crear DataFrame
            datos = []
            for row in cursor.fetchall():
                fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
                
                datos.append({
                    'Fecha': fecha.strftime('%d/%m/%Y'),
                    'Día': fecha.strftime('%A'),
                    'Tipo': row['tipo_codigo'],
                    'Tipo Nombre': row['tipo_nombre'],
                    'Turno': row['turno_codigo'] if row['turno_codigo'] else '',
                    'Turno Nombre': row['turno_nombre'] if row['turno_nombre'] else '',
                    'Horas': row['horas_teoricas'],
                    'Descripción': row['descripcion'],
                    'Manual': 'Sí' if row['es_manual'] else 'No'
                })
            
            df = pd.DataFrame(datos)
            
            # Guardar a Excel
            df.to_excel(excel_path, index=False)
            
            return {
                'resultado': 'éxito',
                'ruta': excel_path,
                'filas': len(datos)
            }
            
        except Exception as e:
            return {
                'resultado': 'error',
                'mensaje': f'Error al exportar calendario: {str(e)}'
            }
    
    def obtener_dias_tipo(self, id_empleado: int, id_tipo_dia: int, 
                         fecha_inicio: str, fecha_fin: str) -> List[Dict]:
        """Obtiene los días de un tipo específico en un periodo.
        
        Args:
            id_empleado: ID del empleado
            id_tipo_dia: ID del tipo de día
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            
        Returns:
            Lista de diccionarios con información de los días
        """
        cursor = self.conn.cursor()
        
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        # Obtener días del tipo especificado
        cursor.execute('''
        SELECT c.fecha, c.horas_teoricas, c.descripcion,
               t.codigo as tipo_codigo, t.nombre as tipo_nombre,
               tu.codigo as turno_codigo, tu.nombre as turno_nombre
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        LEFT JOIN Turnos tu ON c.id_turno = tu.id_turno
        WHERE c.id_empleado = ? AND c.id_tipo_dia = ? AND c.fecha BETWEEN ? AND ?
        ORDER BY c.fecha
        ''', (
            id_empleado,
            id_tipo_dia,
            fecha_inicio_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d')
        ))
        
        dias = []
        for row in cursor.fetchall():
            fecha_db = datetime.strptime(row['fecha'], '%Y-%m-%d')
            
            dia = {
                'fecha': fecha_db.strftime('%d/%m/%Y'),
                'dia_semana': fecha_db.strftime('%A'),
                'tipo': {
                    'codigo': row['tipo_codigo'],
                    'nombre': row['tipo_nombre']
                },
                'turno': None,
                'horas_teoricas': row['horas_teoricas'],
                'descripcion': row['descripcion']
            }
            
            if row['turno_codigo']:
                dia['turno'] = {
                    'codigo': row['turno_codigo'],
                    'nombre': row['turno_nombre']
                }
            
            dias.append(dia)
        
        return dias
    
    def calcular_horas_periodo(self, id_empleado: int, fecha_inicio: str, 
                              fecha_fin: str) -> Dict:
        """Calcula las horas teóricas en un periodo.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY'
            
        Returns:
            Diccionario con información de horas
        """
        cursor = self.conn.cursor()
        
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        # Calcular total de horas teóricas
        cursor.execute('''
        SELECT SUM(horas_teoricas) as total_horas
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ?
        ''', (
            id_empleado,
            fecha_inicio_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d')
        ))
        
        total_horas = cursor.fetchone()['total_horas'] or 0
        
        # Calcular horas por tipo de día
        cursor.execute('''
        SELECT t.codigo, t.nombre, SUM(c.horas_teoricas) as horas
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ?
        GROUP BY t.id_tipo_dia
        ORDER BY horas DESC
        ''', (
            id_empleado,
            fecha_inicio_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d')
        ))
        
        horas_por_tipo = []
        for row in cursor.fetchall():
            horas_por_tipo.append({
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'horas': row['horas']
            })
        
        # Calcular horas por turno
        cursor.execute('''
        SELECT tu.codigo, tu.nombre, SUM(c.horas_teoricas) as horas
        FROM CalendarioLaboral c
        JOIN Turnos tu ON c.id_turno = tu.id_turno
        WHERE c.id_empleado = ? AND c.fecha BETWEEN ? AND ?
        GROUP BY tu.id_turno
        ORDER BY horas DESC
        ''', (
            id_empleado,
            fecha_inicio_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d')
        ))
        
        horas_por_turno = []
        for row in cursor.fetchall():
            horas_por_turno.append({
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'horas': row['horas']
            })
        
        # Calcular días totales
        dias_totales = (fecha_fin_dt - fecha_inicio_dt).days + 1
        
        return {
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin,
                'dias_totales': dias_totales
            },
            'total_horas': total_horas,
            'horas_por_tipo': horas_por_tipo,
            'horas_por_turno': horas_por_turno,
            'promedio_diario': total_horas / dias_totales if dias_totales > 0 else 0
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del calendario laboral
    calendario = CalendarioLaboral()
    
    # Ejemplo de creación de calendario anual
    id_empleado = 1  # Ajustar según la base de datos
    anio_actual = datetime.now().year
    
    resultado = calendario.crear_calendario_anual(id_empleado, anio_actual)
    print(f"Calendario anual creado: {resultado}")
    
    # Establecer vacaciones
    resultado = calendario.establecer_vacaciones(
        id_empleado=id_empleado,
        fecha_inicio="01/08/2023",
        fecha_fin="15/08/2023",
        descripcion="Vacaciones de verano"
    )
    print(f"Vacaciones establecidas: {resultado}")
    
    # Obtener resumen anual
    resumen = calendario.obtener_resumen_anual(id_empleado, anio_actual)
    print(f"Resumen anual:")
    print(f"Días laborables: {resumen['dias_laborables']}")
    print(f"Días festivos: {resumen['dias_festivos']}")
    print(f"Días de vacaciones: {resumen['dias_vacaciones']}")
    print(f"Total horas teóricas: {resumen['total_horas_teoricas']}")
    
    print("\nProceso completado.")
