"""
Módulo de Cálculo de Precio por Hora y Desglose de Pluses

Este módulo implementa la funcionalidad para calcular el precio por hora,
desglosar los diferentes pluses y permitir la edición manual de estos valores.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class CalculadoraPrecioHora:
    """Clase para calcular el precio por hora y desglosar pluses."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa la calculadora de precio por hora.
        
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
        """Inicializa las tablas necesarias para el cálculo de precio por hora y pluses."""
        cursor = self.conn.cursor()
        
        # Tabla para configuración de tarifas y pluses
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConfiguracionTarifas (
            id_configuracion INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            concepto TEXT,
            valor REAL,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            descripcion TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Tabla para histórico de precios por hora
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS HistoricoPrecioHora (
            id_historico INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha TEXT,
            precio_hora_base REAL,
            precio_hora_efectivo REAL,
            horas_teoricas REAL,
            horas_efectivas REAL,
            salario_base REAL,
            comentario TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Tabla para desglose de pluses
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS DesglosePluses (
            id_desglose INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            fecha TEXT,
            tipo_plus TEXT,
            cantidad REAL,
            valor_unitario REAL,
            valor_total REAL,
            es_manual INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        self.conn.commit()
    
    def calcular_precio_hora_base(self, id_empleado: int, fecha: str) -> Dict:
        """Calcula el precio por hora base para un empleado en una fecha específica.
        
        Args:
            id_empleado: ID del empleado
            fecha: Fecha en formato 'DD/MM/YYYY'
            
        Returns:
            Diccionario con información del precio por hora
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        anio = fecha_dt.year
        mes = fecha_dt.month
        
        # Obtener el primer y último día del mes
        primer_dia = datetime(anio, mes, 1).strftime('%d/%m/%Y')
        if mes == 12:
            ultimo_dia = datetime(anio + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(anio, mes + 1, 1) - timedelta(days=1)
        ultimo_dia = ultimo_dia.strftime('%d/%m/%Y')
        
        # Buscar nómina del mes correspondiente
        cursor.execute('''
        SELECT id_nomina, total_devengos, liquido
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio <= ? AND periodo_fin >= ?
        ORDER BY fecha_importacion DESC
        LIMIT 1
        ''', (id_empleado, ultimo_dia, primer_dia))
        
        nomina = cursor.fetchone()
        if not nomina:
            # Si no hay nómina, buscar configuración manual
            cursor.execute('''
            SELECT valor
            FROM ConfiguracionTarifas
            WHERE id_empleado = ? AND concepto = 'precio_hora_base' AND fecha_inicio <= ? AND (fecha_fin >= ? OR fecha_fin IS NULL)
            ORDER BY fecha_inicio DESC
            LIMIT 1
            ''', (id_empleado, fecha_dt.strftime('%Y-%m-%d'), fecha_dt.strftime('%Y-%m-%d')))
            
            config = cursor.fetchone()
            if config:
                return {
                    'precio_hora_base': config['valor'],
                    'fuente': 'configuracion_manual',
                    'fecha': fecha
                }
            else:
                return {
                    'error': 'No se encontró información para calcular el precio por hora',
                    'fecha': fecha
                }
        
        # Obtener salario base y otros conceptos fijos
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ? AND concepto IN ('Salario', 'Antigüedad', 'Complemento Personal')
        ''', (nomina['id_nomina'],))
        
        conceptos_fijos = cursor.fetchall()
        salario_base = sum(c['importe'] for c in conceptos_fijos)
        
        # Obtener días laborables del mes
        cursor.execute('''
        SELECT COUNT(*) as dias_laborables
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Laboral'
        ''', (id_empleado, datetime(anio, mes, 1).strftime('%Y-%m-%d'), ultimo_dia.replace('/', '-')))
        
        dias_result = cursor.fetchone()
        dias_laborables = dias_result['dias_laborables'] if dias_result else 21  # Valor por defecto
        
        # Obtener horas teóricas por día
        cursor.execute('''
        SELECT AVG(horas_teoricas) as horas_por_dia
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Laboral'
        ''', (id_empleado, datetime(anio, mes, 1).strftime('%Y-%m-%d'), ultimo_dia.replace('/', '-')))
        
        horas_result = cursor.fetchone()
        horas_por_dia = horas_result['horas_por_dia'] if horas_result and horas_result['horas_por_dia'] else 8.0  # Valor por defecto
        
        # Calcular horas teóricas totales
        horas_teoricas = dias_laborables * horas_por_dia
        
        # Calcular precio por hora base
        precio_hora_base = salario_base / horas_teoricas if horas_teoricas > 0 else 0
        
        # Guardar en histórico
        cursor.execute('''
        INSERT INTO HistoricoPrecioHora
        (id_empleado, fecha, precio_hora_base, precio_hora_efectivo, horas_teoricas, horas_efectivas, salario_base, comentario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            fecha_dt.strftime('%Y-%m-%d'),
            precio_hora_base,
            precio_hora_base,  # Inicialmente igual al base
            horas_teoricas,
            horas_teoricas,  # Inicialmente igual a las teóricas
            salario_base,
            f"Calculado automáticamente a partir de la nómina de {mes}/{anio}"
        ))
        
        self.conn.commit()
        
        return {
            'precio_hora_base': precio_hora_base,
            'salario_base': salario_base,
            'dias_laborables': dias_laborables,
            'horas_por_dia': horas_por_dia,
            'horas_teoricas': horas_teoricas,
            'fuente': 'nomina',
            'fecha': fecha
        }
    
    def calcular_precio_hora_efectivo(self, id_empleado: int, fecha: str) -> Dict:
        """Calcula el precio por hora efectivo incluyendo todos los conceptos variables.
        
        Args:
            id_empleado: ID del empleado
            fecha: Fecha en formato 'DD/MM/YYYY'
            
        Returns:
            Diccionario con información del precio por hora efectivo
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        anio = fecha_dt.year
        mes = fecha_dt.month
        
        # Obtener el primer y último día del mes
        primer_dia = datetime(anio, mes, 1).strftime('%d/%m/%Y')
        if mes == 12:
            ultimo_dia = datetime(anio + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(anio, mes + 1, 1) - timedelta(days=1)
        ultimo_dia = ultimo_dia.strftime('%d/%m/%Y')
        
        # Buscar nómina del mes correspondiente
        cursor.execute('''
        SELECT id_nomina, total_devengos, liquido
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio <= ? AND periodo_fin >= ?
        ORDER BY fecha_importacion DESC
        LIMIT 1
        ''', (id_empleado, ultimo_dia, primer_dia))
        
        nomina = cursor.fetchone()
        if not nomina:
            # Si no hay nómina, buscar configuración manual
            cursor.execute('''
            SELECT valor
            FROM ConfiguracionTarifas
            WHERE id_empleado = ? AND concepto = 'precio_hora_efectivo' AND fecha_inicio <= ? AND (fecha_fin >= ? OR fecha_fin IS NULL)
            ORDER BY fecha_inicio DESC
            LIMIT 1
            ''', (id_empleado, fecha_dt.strftime('%Y-%m-%d'), fecha_dt.strftime('%Y-%m-%d')))
            
            config = cursor.fetchone()
            if config:
                return {
                    'precio_hora_efectivo': config['valor'],
                    'fuente': 'configuracion_manual',
                    'fecha': fecha
                }
            else:
                return {
                    'error': 'No se encontró información para calcular el precio por hora efectivo',
                    'fecha': fecha
                }
        
        # Obtener todos los conceptos de devengo (excepto retroactivos)
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ? AND tipo = 'devengo' AND es_retroactivo = 0
        ''', (nomina['id_nomina'],))
        
        conceptos = cursor.fetchall()
        total_devengos = sum(c['importe'] for c in conceptos)
        
        # Obtener horas efectivas trabajadas
        cursor.execute('''
        SELECT SUM(horas) as horas_efectivas
        FROM TiemposNomina
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ?
        ''', (id_empleado, datetime(anio, mes, 1).strftime('%d-%b-%y'), ultimo_dia.replace('/', '-')))
        
        horas_result = cursor.fetchone()
        horas_efectivas = horas_result['horas_efectivas'] if horas_result and horas_result['horas_efectivas'] else 0
        
        # Si no hay horas efectivas registradas, usar horas teóricas
        if horas_efectivas == 0:
            cursor.execute('''
            SELECT COUNT(*) as dias_laborables
            FROM CalendarioLaboral
            WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Laboral'
            ''', (id_empleado, datetime(anio, mes, 1).strftime('%Y-%m-%d'), ultimo_dia.replace('/', '-')))
            
            dias_result = cursor.fetchone()
            dias_laborables = dias_result['dias_laborables'] if dias_result else 21  # Valor por defecto
            
            cursor.execute('''
            SELECT AVG(horas_teoricas) as horas_por_dia
            FROM CalendarioLaboral
            WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Laboral'
            ''', (id_empleado, datetime(anio, mes, 1).strftime('%Y-%m-%d'), ultimo_dia.replace('/', '-')))
            
            horas_dia_result = cursor.fetchone()
            horas_por_dia = horas_dia_result['horas_por_dia'] if horas_dia_result and horas_dia_result['horas_por_dia'] else 8.0
            
            horas_efectivas = dias_laborables * horas_por_dia
        
        # Calcular precio por hora efectivo
        precio_hora_efectivo = total_devengos / horas_efectivas if horas_efectivas > 0 else 0
        
        # Actualizar histórico
        cursor.execute('''
        UPDATE HistoricoPrecioHora
        SET precio_hora_efectivo = ?, horas_efectivas = ?
        WHERE id_empleado = ? AND fecha = ?
        ''', (
            precio_hora_efectivo,
            horas_efectivas,
            id_empleado,
            fecha_dt.strftime('%Y-%m-%d')
        ))
        
        # Si no se actualizó ninguna fila, insertar nuevo registro
        if cursor.rowcount == 0:
            cursor.execute('''
            INSERT INTO HistoricoPrecioHora
            (id_empleado, fecha, precio_hora_base, precio_hora_efectivo, horas_teoricas, horas_efectivas, salario_base, comentario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_empleado,
                fecha_dt.strftime('%Y-%m-%d'),
                0,  # Se calculará después
                precio_hora_efectivo,
                0,  # Se calculará después
                horas_efectivas,
                0,  # Se calculará después
                f"Calculado automáticamente a partir de la nómina de {mes}/{anio}"
            ))
        
        self.conn.commit()
        
        return {
            'precio_hora_efectivo': precio_hora_efectivo,
            'total_devengos': total_devengos,
            'horas_efectivas': horas_efectivas,
            'fuente': 'nomina',
            'fecha': fecha
        }
    
    def desglosar_pluses(self, id_empleado: int, fecha: str) -> Dict:
        """Desglosa los diferentes pluses para un empleado en una fecha específica.
        
        Args:
            id_empleado: ID del empleado
            fecha: Fecha en formato 'DD/MM/YYYY'
            
        Returns:
            Diccionario con información de los pluses
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        anio = fecha_dt.year
        mes = fecha_dt.month
        
        # Obtener el primer y último día del mes
        primer_dia = datetime(anio, mes, 1).strftime('%d/%m/%Y')
        if mes == 12:
            ultimo_dia = datetime(anio + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(anio, mes + 1, 1) - timedelta(days=1)
        ultimo_dia = ultimo_dia.strftime('%d/%m/%Y')
        
        # Buscar nómina del mes correspondiente
        cursor.execute('''
        SELECT id_nomina
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio <= ? AND periodo_fin >= ?
        ORDER BY fecha_importacion DESC
        LIMIT 1
        ''', (id_empleado, ultimo_dia, primer_dia))
        
        nomina = cursor.fetchone()
        
        pluses = {}
        
        if nomina:
            # Obtener conceptos de plus de la nómina
            cursor.execute('''
            SELECT concepto, unidades, tarifa, importe
            FROM ConceptosNomina
            WHERE id_nomina = ? AND concepto LIKE '%Plus%' OR concepto LIKE '%Prima%' OR concepto = 'Nocturnidad'
            ''', (nomina['id_nomina'],))
            
            conceptos_plus = cursor.fetchall()
            
            for plus in conceptos_plus:
                pluses[plus['concepto']] = {
                    'cantidad': plus['unidades'],
                    'valor_unitario': plus['tarifa'],
                    'valor_total': plus['importe'],
                    'fuente': 'nomina'
                }
        
        # Buscar pluses manuales
        cursor.execute('''
        SELECT tipo_plus, cantidad, valor_unitario, valor_total
        FROM DesglosePluses
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND es_manual = 1
        ''', (id_empleado, datetime(anio, mes, 1).strftime('%Y-%m-%d'), ultimo_dia.replace('/', '-')))
        
        pluses_manuales 
(Content truncated due to size limit. Use line ranges to read in chunks)