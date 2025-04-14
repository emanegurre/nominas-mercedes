"""
Módulo de Gestión de Pagas Extras

Este módulo implementa la funcionalidad para gestionar las pagas extras,
incluyendo las cuatro pagas anuales (enero, marzo, julio y septiembre)
con sus características específicas, y calculando tanto importes brutos como netos.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class GestorPagasExtras:
    """Clase para gestionar las pagas extras."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el gestor de pagas extras.
        
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
        """Inicializa las tablas necesarias para la gestión de pagas extras."""
        cursor = self.conn.cursor()
        
        # Tabla para tipos de pagas extras
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TiposPagaExtra (
            id_tipo_paga INTEGER PRIMARY KEY,
            codigo TEXT UNIQUE,
            nombre TEXT,
            descripcion TEXT,
            mes_pago INTEGER,
            dia_pago INTEGER,
            es_prorrateada INTEGER,
            es_beneficios INTEGER,
            es_convenio INTEGER,
            id_convenio INTEGER,
            formula_calculo TEXT,
            FOREIGN KEY (id_convenio) REFERENCES ConveniosColectivos(id_convenio)
        )
        ''')
        
        # Tabla para configuración de pagas extras
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConfiguracionPagasExtras (
            id_configuracion INTEGER PRIMARY KEY,
            id_tipo_paga INTEGER,
            anio INTEGER,
            importe_base REAL,
            porcentaje_irpf REAL,
            porcentaje_ss REAL,
            otros_descuentos REAL,
            descripcion_otros TEXT,
            es_activa INTEGER,
            FOREIGN KEY (id_tipo_paga) REFERENCES TiposPagaExtra(id_tipo_paga)
        )
        ''')
        
        # Tabla para pagas extras de empleados
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS PagasExtrasEmpleados (
            id_paga_empleado INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            id_tipo_paga INTEGER,
            anio INTEGER,
            fecha_pago TEXT,
            importe_bruto REAL,
            porcentaje_irpf REAL,
            importe_irpf REAL,
            porcentaje_ss REAL,
            importe_ss REAL,
            otros_descuentos REAL,
            importe_neto REAL,
            es_pagada INTEGER,
            comentario TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado),
            FOREIGN KEY (id_tipo_paga) REFERENCES TiposPagaExtra(id_tipo_paga)
        )
        ''')
        
        # Insertar tipos de pagas extras predeterminados si no existen
        cursor.execute('SELECT COUNT(*) as count FROM TiposPagaExtra')
        if cursor.fetchone()['count'] == 0:
            tipos_paga_default = [
                ('ENERO', 'Paga Extra Enero', 'Paga extra estándar de enero', 1, 15, 0, 0, 0, None, 'salario_base'),
                ('MARZO', 'Paga Beneficios', 'Paga de beneficios de la empresa de marzo', 3, 15, 0, 1, 0, None, 'salario_base * (1 + porcentaje_beneficios)'),
                ('JULIO', 'Paga Extra Julio', 'Paga extra estándar de julio', 7, 15, 0, 0, 0, None, 'salario_base'),
                ('SEPT', 'Paga Convenio', 'Paga pactada en convenio de septiembre', 9, 15, 0, 0, 1, None, 'salario_base * factor_convenio')
            ]
            
            for tipo in tipos_paga_default:
                cursor.execute('''
                INSERT INTO TiposPagaExtra 
                (codigo, nombre, descripcion, mes_pago, dia_pago, es_prorrateada, 
                 es_beneficios, es_convenio, id_convenio, formula_calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tipo)
        
        self.conn.commit()
    
    def crear_tipo_paga(self, codigo: str, nombre: str, descripcion: str, 
                       mes_pago: int, dia_pago: int, es_prorrateada: bool, 
                       es_beneficios: bool, es_convenio: bool, 
                       id_convenio: int = None, formula_calculo: str = None) -> Dict:
        """Crea un nuevo tipo de paga extra.
        
        Args:
            codigo: Código único del tipo de paga
            nombre: Nombre del tipo de paga
            descripcion: Descripción del tipo de paga
            mes_pago: Mes de pago (1-12)
            dia_pago: Día de pago (1-31)
            es_prorrateada: Si la paga se prorratea mensualmente
            es_beneficios: Si la paga depende de los beneficios de la empresa
            es_convenio: Si la paga está vinculada a un convenio
            id_convenio: ID del convenio (opcional)
            formula_calculo: Fórmula para calcular el importe (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO TiposPagaExtra 
            (codigo, nombre, descripcion, mes_pago, dia_pago, es_prorrateada, 
             es_beneficios, es_convenio, id_convenio, formula_calculo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                codigo,
                nombre,
                descripcion,
                mes_pago,
                dia_pago,
                1 if es_prorrateada else 0,
                1 if es_beneficios else 0,
                1 if es_convenio else 0,
                id_convenio,
                formula_calculo if formula_calculo else 'salario_base'
            ))
            
            self.conn.commit()
            
            return {
                'resultado': 'éxito',
                'id_tipo_paga': cursor.lastrowid,
                'codigo': codigo,
                'nombre': nombre
            }
        except sqlite3.IntegrityError:
            return {
                'resultado': 'error',
                'mensaje': f'Ya existe un tipo de paga con el código {codigo}'
            }
    
    def configurar_paga_extra(self, id_tipo_paga: int, anio: int, 
                             importe_base: float = None, porcentaje_irpf: float = None, 
                             porcentaje_ss: float = None, otros_descuentos: float = None, 
                             descripcion_otros: str = None) -> Dict:
        """Configura una paga extra para un año específico.
        
        Args:
            id_tipo_paga: ID del tipo de paga
            anio: Año de la configuración
            importe_base: Importe base de la paga (opcional)
            porcentaje_irpf: Porcentaje de IRPF (opcional)
            porcentaje_ss: Porcentaje de Seguridad Social (opcional)
            otros_descuentos: Otros descuentos (opcional)
            descripcion_otros: Descripción de otros descuentos (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar si ya existe configuración para este tipo de paga y año
        cursor.execute('''
        SELECT id_configuracion
        FROM ConfiguracionPagasExtras
        WHERE id_tipo_paga = ? AND anio = ?
        ''', (id_tipo_paga, anio))
        
        config_existente = cursor.fetchone()
        
        if config_existente:
            # Actualizar configuración existente
            cursor.execute('''
            UPDATE ConfiguracionPagasExtras
            SET importe_base = ?, porcentaje_irpf = ?, porcentaje_ss = ?, 
                otros_descuentos = ?, descripcion_otros = ?, es_activa = 1
            WHERE id_configuracion = ?
            ''', (
                importe_base,
                porcentaje_irpf,
                porcentaje_ss,
                otros_descuentos,
                descripcion_otros,
                config_existente['id_configuracion']
            ))
            
            id_configuracion = config_existente['id_configuracion']
        else:
            # Crear nueva configuración
            cursor.execute('''
            INSERT INTO ConfiguracionPagasExtras
            (id_tipo_paga, anio, importe_base, porcentaje_irpf, porcentaje_ss, 
             otros_descuentos, descripcion_otros, es_activa)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                id_tipo_paga,
                anio,
                importe_base,
                porcentaje_irpf,
                porcentaje_ss,
                otros_descuentos,
                descripcion_otros
            ))
            
            id_configuracion = cursor.lastrowid
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_configuracion': id_configuracion,
            'id_tipo_paga': id_tipo_paga,
            'anio': anio
        }
    
    def obtener_tipos_paga(self) -> List[Dict]:
        """Obtiene todos los tipos de paga extra disponibles.
        
        Returns:
            Lista de diccionarios con información de tipos de paga
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id_tipo_paga, codigo, nombre, descripcion, mes_pago, dia_pago, 
               es_prorrateada, es_beneficios, es_convenio, id_convenio, formula_calculo
        FROM TiposPagaExtra
        ORDER BY mes_pago
        ''')
        
        tipos_paga = []
        for row in cursor.fetchall():
            tipos_paga.append({
                'id': row['id_tipo_paga'],
                'codigo': row['codigo'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'mes_pago': row['mes_pago'],
                'dia_pago': row['dia_pago'],
                'es_prorrateada': bool(row['es_prorrateada']),
                'es_beneficios': bool(row['es_beneficios']),
                'es_convenio': bool(row['es_convenio']),
                'id_convenio': row['id_convenio'],
                'formula_calculo': row['formula_calculo']
            })
        
        return tipos_paga
    
    def obtener_configuracion_paga(self, id_tipo_paga: int, anio: int) -> Dict:
        """Obtiene la configuración de una paga extra para un año específico.
        
        Args:
            id_tipo_paga: ID del tipo de paga
            anio: Año de la configuración
            
        Returns:
            Diccionario con información de la configuración
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT c.id_configuracion, c.importe_base, c.porcentaje_irpf, c.porcentaje_ss, 
               c.otros_descuentos, c.descripcion_otros, c.es_activa,
               t.codigo, t.nombre, t.mes_pago, t.dia_pago, t.formula_calculo
        FROM ConfiguracionPagasExtras c
        JOIN TiposPagaExtra t ON c.id_tipo_paga = t.id_tipo_paga
        WHERE c.id_tipo_paga = ? AND c.anio = ?
        ''', (id_tipo_paga, anio))
        
        row = cursor.fetchone()
        
        if not row:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró configuración para el tipo de paga {id_tipo_paga} y año {anio}'
            }
        
        return {
            'resultado': 'éxito',
            'id_configuracion': row['id_configuracion'],
            'id_tipo_paga': id_tipo_paga,
            'codigo': row['codigo'],
            'nombre': row['nombre'],
            'anio': anio,
            'mes_pago': row['mes_pago'],
            'dia_pago': row['dia_pago'],
            'importe_base': row['importe_base'],
            'porcentaje_irpf': row['porcentaje_irpf'],
            'porcentaje_ss': row['porcentaje_ss'],
            'otros_descuentos': row['otros_descuentos'],
            'descripcion_otros': row['descripcion_otros'],
            'es_activa': bool(row['es_activa']),
            'formula_calculo': row['formula_calculo']
        }
    
    def calcular_paga_extra(self, id_empleado: int, id_tipo_paga: int, 
                           anio: int, fecha_pago: str = None) -> Dict:
        """Calcula una paga extra para un empleado.
        
        Args:
            id_empleado: ID del empleado
            id_tipo_paga: ID del tipo de paga
            anio: Año de la paga
            fecha_pago: Fecha de pago en formato 'DD/MM/YYYY' (opcional)
            
        Returns:
            Diccionario con resultado del cálculo
        """
        cursor = self.conn.cursor()
        
        # Obtener información del tipo de paga
        cursor.execute('''
        SELECT id_tipo_paga, codigo, nombre, mes_pago, dia_pago, 
               es_prorrateada, es_beneficios, es_convenio, id_convenio, formula_calculo
        FROM TiposPagaExtra
        WHERE id_tipo_paga = ?
        ''', (id_tipo_paga,))
        
        tipo_paga = cursor.fetchone()
        if not tipo_paga:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró el tipo de paga especificado'
            }
        
        # Verificar si la paga está vinculada a un convenio y si este sigue vigente
        if tipo_paga['es_convenio'] and tipo_paga['id_convenio']:
            cursor.execute('''
            SELECT es_activo, fecha_fin
            FROM ConveniosColectivos
            WHERE id_convenio = ?
            ''', (tipo_paga['id_convenio'],))
            
            convenio = cursor.fetchone()
            if not convenio or not convenio['es_activo']:
                return {
                    'resultado': 'error',
                    'mensaje': 'El convenio asociado a esta paga no está activo'
                }
            
            # Verificar si el convenio ha expirado
            fecha_fin = datetime.strptime(convenio['fecha_fin'], '%Y-%m-%d')
            if fecha_fin < datetime.now():
                return {
                    'resultado': 'error',
                    'mensaje': 'El convenio asociado a esta paga ha expirado'
                }
        
        # Obtener configuración de la paga para el año especificado
        cursor.execute('''
        SELECT importe_base, porcentaje_irpf, porcentaje_ss, otros_descuentos
        FROM ConfiguracionPagasExtras
        WHERE id_tipo_paga = ? AND anio = ? AND es_activa = 1
        ''', (id_tipo_paga, anio))
        
        config = cursor.fetchone()
        if not config:
            return {
                'resultado': 'error',
                'mensaje': f'No se encontró configuración activa para la paga {tipo_paga["nombre"]} en el año {anio}'
            }
        
        # Determinar fecha de pago si no se proporciona
        if not fecha_pago:
            # Usar mes y día configurados
            try:
                fecha_pago_dt = date(anio, tipo_paga['mes_pago'], tipo_paga['dia_pago'])
                fecha_pago = fecha_pago_dt.strftime('%d/%m/%Y')
            except ValueError:
                # Si el día no es válido para el mes (ej. 31 de febrero), usar el último día del mes
                ultimo_dia = calendar.monthrange(anio, tipo_paga['mes_pago'])[1]
                fecha_pago_dt = date(anio, tipo_paga['mes_pago'], ultimo_dia)
                fecha_pago = fecha_pago_dt.strftime('%d/%m/%Y')
        
        # Calcular importe bruto
        importe_bruto = self._calcular_importe_bruto(
            id_empleado=id_empleado,
            formula=tipo_paga['formula_calculo'],
            importe_base=config['importe_base'],
          
(Content truncated due to size limit. Use line ranges to read in chunks)