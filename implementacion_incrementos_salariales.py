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
            Diccionario con información de la retroactividad
        """
        cursor = self.conn.cursor()
        
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Calcular diferencia mensual
        diferencia_mensual = salario_nuevo - salario_anterior
        
        # Calcular número de meses entre las fechas
        meses = (fecha_fin_dt.year - fecha_inicio_dt.year) * 12 + fecha_fin_dt.month - fecha_inicio_dt.month
        if fecha_fin_dt.day < fecha_inicio_dt.day:
            meses -= 1
        
        # Ajustar si es menos de un mes
        if meses < 1:
            dias = (fecha_fin_dt - fecha_inicio_dt).days
            meses = dias / 30.0  # Aproximación
        
        # Calcular importe total de retroactividad
        importe_retroactividad = diferencia_mensual * meses
        
        # Registrar retroactividad
        cursor.execute('''
        INSERT INTO HistoricoSalarios
        (id_empleado, fecha, concepto, valor_anterior, valor_nuevo, porcentaje_incremento, motivo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            fecha_fin,
            f"Retroactividad {concepto}",
            0,
            importe_retroactividad,
            0,
            f"Retroactividad de {fecha_inicio_dt.strftime('%d/%m/%Y')} a {fecha_fin_dt.strftime('%d/%m/%Y')}"
        ))
        
        self.conn.commit()
        
        return {
            'meses': meses,
            'diferencia_mensual': diferencia_mensual,
            'importe_total': importe_retroactividad,
            'fecha_inicio': fecha_inicio_dt.strftime('%d/%m/%Y'),
            'fecha_fin': fecha_fin_dt.strftime('%d/%m/%Y')
        }
    
    def aplicar_incremento_todos_empleados(self, id_incremento: int) -> Dict:
        """Aplica un incremento salarial a todos los empleados.
        
        Args:
            id_incremento: ID del incremento
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener todos los empleados
        cursor.execute('SELECT id_empleado FROM Empleados')
        
        empleados = cursor.fetchall()
        resultados = []
        
        for empleado in empleados:
            resultado = self.aplicar_incremento_empleado(id_incremento, empleado['id_empleado'])
            if resultado['resultado'] == 'éxito':
                resultados.append({
                    'id_empleado': empleado['id_empleado'],
                    'salario_anterior': resultado['salario_anterior'],
                    'salario_nuevo': resultado['salario_nuevo'],
                    'diferencia': resultado['diferencia']
                })
        
        return {
            'resultado': 'éxito',
            'empleados_actualizados': len(resultados),
            'detalles': resultados
        }
    
    def obtener_incrementos_convenio(self, id_convenio: int) -> List[Dict]:
        """Obtiene los incrementos salariales de un convenio.
        
        Args:
            id_convenio: ID del convenio
            
        Returns:
            Lista de diccionarios con información de incrementos
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_incremento, concepto, porcentaje, cantidad_fija, fecha_aplicacion, 
               fecha_fin, es_retroactivo, fecha_retroactividad, descripcion
        FROM IncrementosSalariales
        WHERE id_convenio = ?
        ORDER BY fecha_aplicacion
        ''', (id_convenio,))
        
        incrementos = []
        for row in cursor.fetchall():
            fecha_aplicacion = datetime.strptime(row['fecha_aplicacion'], '%Y-%m-%d')
            fecha_fin = datetime.strptime(row['fecha_fin'], '%Y-%m-%d') if row['fecha_fin'] else None
            fecha_retroactividad = datetime.strptime(row['fecha_retroactividad'], '%Y-%m-%d') if row['fecha_retroactividad'] else None
            
            incrementos.append({
                'id': row['id_incremento'],
                'concepto': row['concepto'],
                'porcentaje': row['porcentaje'],
                'cantidad_fija': row['cantidad_fija'],
                'fecha_aplicacion': fecha_aplicacion.strftime('%d/%m/%Y'),
                'fecha_fin': fecha_fin.strftime('%d/%m/%Y') if fecha_fin else None,
                'es_retroactivo': bool(row['es_retroactivo']),
                'fecha_retroactividad': fecha_retroactividad.strftime('%d/%m/%Y') if fecha_retroactividad else None,
                'descripcion': row['descripcion']
            })
        
        return incrementos
    
    def obtener_convenios_activos(self) -> List[Dict]:
        """Obtiene los convenios colectivos activos.
        
        Returns:
            Lista de diccionarios con información de convenios
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_convenio, nombre, descripcion, fecha_inicio, fecha_fin, ambito
        FROM ConveniosColectivos
        WHERE es_activo = 1
        ORDER BY fecha_inicio DESC
        ''')
        
        convenios = []
        for row in cursor.fetchall():
            fecha_inicio = datetime.strptime(row['fecha_inicio'], '%Y-%m-%d')
            fecha_fin = datetime.strptime(row['fecha_fin'], '%Y-%m-%d')
            
            convenios.append({
                'id': row['id_convenio'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin': fecha_fin.strftime('%d/%m/%Y'),
                'ambito': row['ambito']
            })
        
        return convenios
    
    def obtener_historico_salarios_empleado(self, id_empleado: int, 
                                          concepto: str = None) -> List[Dict]:
        """Obtiene el histórico de salarios de un empleado.
        
        Args:
            id_empleado: ID del empleado
            concepto: Concepto salarial específico (opcional)
            
        Returns:
            Lista de diccionarios con información de histórico salarial
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT fecha, concepto, valor_anterior, valor_nuevo, porcentaje_incremento, motivo
        FROM HistoricoSalarios
        WHERE id_empleado = ?
        '''
        params = [id_empleado]
        
        # Añadir filtro de concepto si se proporciona
        if concepto:
            query += ' AND concepto = ?'
            params.append(concepto)
        
        # Ordenar por fecha
        query += ' ORDER BY fecha DESC'
        
        cursor.execute(query, params)
        
        historico = []
        for row in cursor.fetchall():
            fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
            
            historico.append({
                'fecha': fecha.strftime('%d/%m/%Y'),
                'concepto': row['concepto'],
                'valor_anterior': row['valor_anterior'],
                'valor_nuevo': row['valor_nuevo'],
                'porcentaje_incremento': row['porcentaje_incremento'],
                'motivo': row['motivo']
            })
        
        return historico
    
    def obtener_incrementos_pendientes(self, id_empleado: int = None) -> List[Dict]:
        """Obtiene los incrementos salariales pendientes de aplicar.
        
        Args:
            id_empleado: ID del empleado específico (opcional)
            
        Returns:
            Lista de diccionarios con información de incrementos pendientes
        """
        cursor = self.conn.cursor()
        
        # Obtener fecha actual
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        
        # Obtener incrementos con fecha de aplicación futura
        cursor.execute('''
        SELECT i.id_incremento, i.concepto, i.porcentaje, i.cantidad_fija, i.fecha_aplicacion,
               i.es_retroactivo, i.fecha_retroactividad, i.descripcion, c.nombre as convenio
        FROM IncrementosSalariales i
        JOIN ConveniosColectivos c ON i.id_convenio = c.id_convenio
        WHERE i.fecha_aplicacion > ? AND c.es_activo = 1
        ORDER BY i.fecha_aplicacion
        ''', (fecha_actual,))
        
        incrementos = []
        for row in cursor.fetchall():
            fecha_aplicacion = datetime.strptime(row['fecha_aplicacion'], '%Y-%m-%d')
            fecha_retroactividad = datetime.strptime(row['fecha_retroactividad'], '%Y-%m-%d') if row['fecha_retroactividad'] else None
            
            # Si se especifica un empleado, verificar si ya se le aplicó
            if id_empleado:
                cursor.execute('''
                SELECT COUNT(*) as count
                FROM IncrementosEmpleados
                WHERE id_incremento = ? AND id_empleado = ?
                ''', (row['id_incremento'], id_empleado))
                
                if cursor.fetchone()['count'] > 0:
                    continue  # Ya se aplicó a este empleado
            
            incrementos.append({
                'id': row['id_incremento'],
                'concepto': row['concepto'],
                'porcentaje': row['porcentaje'],
                'cantidad_fija': row['cantidad_fija'],
                'fecha_aplicacion': fecha_aplicacion.strftime('%d/%m/%Y'),
                'es_retroactivo': bool(row['es_retroactivo']),
                'fecha_retroactividad': fecha_retroactividad.strftime('%d/%m/%Y') if fecha_retroactividad else None,
                'descripcion': row['descripcion'],
                'convenio': row['convenio']
            })
        
        return incrementos
    
    def simular_incremento(self, id_empleado: int, porcentaje: float = None, 
                          cantidad_fija: float = None, concepto: str = 'Salario Base') -> Dict:
        """Simula un incremento salarial para un empleado.
        
        Args:
            id_empleado: ID del empleado
            porcentaje: Porcentaje de incremento (opcional)
            cantidad_fija: Cantidad fija de incremento (opcional)
            concepto: Concepto salarial (por defecto 'Salario Base')
            
        Returns:
            Diccionario con resultado de la simulación
        """
        # Verificar que se proporciona al menos un tipo de incremento
        if porcentaje is None and cantidad_fija is None:
            return {
                'resultado': 'error',
                'mensaje': 'Debe proporcionar un porcentaje o una cantidad fija'
            }
        
        # Obtener salario actual
        salario_actual = self._obtener_salario_concepto(id_empleado, concepto)
        
        if salario_actual is None:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró información salarial para el concepto {concepto}'
            }
        
        # Calcular nuevo salario
        nuevo_salario = salario_actual
        
        if porcentaje is not None:
            nuevo_salario += salario_actual * (porcentaje / 100)
        
        if cantidad_fija is not None:
            nuevo_salario += cantidad_fija
        
        # Calcular diferencia
        diferencia = nuevo_salario - salario_actual
        porcentaje_real = (diferencia / salario_actual * 100) if salario_actual > 0 else 0
        
        return {
            'resultado': 'éxito',
            'concepto': concepto,
            'salario_actual': salario_actual,
            'salario_simulado': nuevo_salario,
            'diferencia': diferencia,
            'porcentaje_real': porcentaje_real,
            'incremento_mensual': diferencia,
            'incremento_anual': diferencia * 12
        }
    
    def simular_incrementos_futuros(self, id_empleado: int, anio: int) -> Dict:
        """Simula los incrementos futuros para un empleado en un año específico.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para la simulación
            
        Returns:
            Diccionario con resultado de la simulación
        """
        cursor = self.conn.cursor()
        
        # Obtener fecha de inicio y fin del año
        fecha_inicio = date(anio, 1, 1).strftime('%Y-%m-%d')
        fecha_fin = date(anio, 12, 31).strftime('%Y-%m-%d')
        
        # Obtener incrementos programados para el año
        cursor.execute('''
        SELECT i.id_incremento, i.concepto, i.porcentaje, i.cantidad_fija, i.fecha_aplicacion,
               i.es_retroactivo, i.fecha_retroactividad, i.descripcion, c.nombre as convenio
        FROM IncrementosSalariales i
        JOIN ConveniosColectivos c ON i.id_convenio = c.id_convenio
        WHERE i.fecha_aplicacion BETWEEN ? AND ? AND c.es_activo = 1
        ORDER BY i.fecha_aplicacion
        ''', (fecha_inicio, fecha_fin))
        
        incrementos = cursor.fetchall()
        
        # Obtener salario base actual
        salario_base = self._obtener_salario_concepto(id_empleado, 'Salario Base')
        
        if salario_base is None:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró información salarial para el empleado'
            }
        
        # Simular aplicación de incrementos
        simulaciones = []
        salario_actual = salario_base
        
        for incremento in incrementos:
            fecha_aplicacion = datetime.strptime(incremento['fecha_aplicacion'], '%Y-%m-%d')
            
            # Verificar si aplica al concepto correcto
            if incremento['concepto'] != 'Salario Base' and incremento['concepto'] != 'Todos':
                continue
            
            # Calcular nuevo salario
            nuevo_salario = salario_actual
            
            if incremento['porcentaje'] is not None:
                nuevo_salario += salario_actual * (incremento['porcentaje'] / 100)
            
            if incremento['cantidad_fija'] is not None:
                nuevo_salario += incremento['cantidad_fija']
            
            # Calcular diferencia
            diferencia = nuevo_salario - salario_actual
            porcentaje_real = (diferencia / salario_actual * 100) if salario_actual > 0 else 0
            
            # Calcular retroactividad si aplica
            retroactividad = None
            if incremento['es_retroactivo'] and incremento['fecha_retroactividad']:
                fecha_retroactividad = datetime.strptime(incremento['fecha_retroactividad'], '%Y-%m-%d')
                meses_retro = (fecha_aplicacion.year - fecha_retroactividad.year) * 12 + fecha_aplicacion.month - fecha_retroactividad.month
                if meses_retro < 0:
                    meses_retro = 0
                retroactividad = diferencia * meses_retro
            
            simulacion = {
                'fecha': fecha_aplicacion.strftime('%d/%m/%Y'),
                'concepto': incremento['concepto'],
                'convenio': incremento['convenio'],
                'porcentaje': incremento['porcentaje'],
                'cantidad_fija': incremento['cantidad_fija'],
                'salario_anterior': salario_actual,
                'salario_nuevo': nuevo_salario,
                'diferencia': diferencia,
                'porcentaje_real': porcentaje_real,
                'retroactividad': retroactividad,
                'descripcion': incremento['descripcion']
            }
            
            simulaciones.append(simulacion)
            
            # Actualizar salario actual para la siguiente simulación
            salario_actual = nuevo_salario
        
        # Calcular impacto anual
        impacto_anual = salario_actual - salario_base
        
        return {
            'resultado': 'éxito',
            'anio': anio,
            'salario_inicial': salario_base,
            'salario_final': salario_actual,
            'incremento_total': impacto_anual,
            'porcentaje_total': (impacto_anual / salario_base * 100) if salario_base > 0 else 0,
            'simulaciones': simulaciones
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del gestor de incrementos salariales
    gestor = GestorIncrementosSalariales()
    
    # Ejemplo de creación de convenio
    resultado = gestor.crear_convenio(
        nombre="Convenio Colectivo 2023-2025",
        descripcion="Convenio colectivo para el periodo 2023-2025",
        fecha_inicio="01/01/2023",
        fecha_fin="31/12/2025",
        ambito="Empresa"
    )
    print(f"Convenio creado: {resultado}")
    
    # Registrar incremento salarial
    id_convenio = resultado['id_convenio']
    resultado = gestor.registrar_incremento(
        id_convenio=id_convenio,
        concepto="Salario Base",
        porcentaje=2.5,
        fecha_aplicacion="01/01/2023",
        descripcion="Incremento anual 2023"
    )
    print(f"Incremento registrado: {resultado}")
    
    # Simular incremento para un empleado
    id_empleado = 1  # Ajustar según la base de datos
    simulacion = gestor.simular_incremento(
        id_empleado=id_empleado,
        porcentaje=2.5,
        concepto="Salario Base"
    )
    print(f"Simulación de incremento: {simulacion}")
    
    print("\nProceso completado.")
