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
            es_beneficios=bool(tipo_paga['es_beneficios']),
            anio=anio
        )
        
        if importe_bruto is None:
            return {
                'resultado': 'error',
                'mensaje': 'No se pudo calcular el importe bruto de la paga'
            }
        
        # Calcular retenciones
        porcentaje_irpf = config['porcentaje_irpf'] if config['porcentaje_irpf'] is not None else 0
        porcentaje_ss = config['porcentaje_ss'] if config['porcentaje_ss'] is not None else 0
        otros_descuentos = config['otros_descuentos'] if config['otros_descuentos'] is not None else 0
        
        importe_irpf = importe_bruto * (porcentaje_irpf / 100)
        importe_ss = importe_bruto * (porcentaje_ss / 100)
        
        # Calcular importe neto
        importe_neto = importe_bruto - importe_irpf - importe_ss - otros_descuentos
        
        # Convertir fecha a formato de base de datos
        fecha_pago_dt = datetime.strptime(fecha_pago, '%d/%m/%Y')
        
        # Verificar si ya existe esta paga para el empleado
        cursor.execute('''
        SELECT id_paga_empleado
        FROM PagasExtrasEmpleados
        WHERE id_empleado = ? AND id_tipo_paga = ? AND anio = ?
        ''', (id_empleado, id_tipo_paga, anio))
        
        paga_existente = cursor.fetchone()
        
        if paga_existente:
            # Actualizar paga existente
            cursor.execute('''
            UPDATE PagasExtrasEmpleados
            SET fecha_pago = ?, importe_bruto = ?, porcentaje_irpf = ?, importe_irpf = ?,
                porcentaje_ss = ?, importe_ss = ?, otros_descuentos = ?, importe_neto = ?,
                comentario = ?
            WHERE id_paga_empleado = ?
            ''', (
                fecha_pago_dt.strftime('%Y-%m-%d'),
                importe_bruto,
                porcentaje_irpf,
                importe_irpf,
                porcentaje_ss,
                importe_ss,
                otros_descuentos,
                importe_neto,
                f"Actualizado el {datetime.now().strftime('%d/%m/%Y')}",
                paga_existente['id_paga_empleado']
            ))
            
            id_paga_empleado = paga_existente['id_paga_empleado']
        else:
            # Crear nueva paga
            cursor.execute('''
            INSERT INTO PagasExtrasEmpleados
            (id_empleado, id_tipo_paga, anio, fecha_pago, importe_bruto, porcentaje_irpf, 
             importe_irpf, porcentaje_ss, importe_ss, otros_descuentos, importe_neto, 
             es_pagada, comentario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            ''', (
                id_empleado,
                id_tipo_paga,
                anio,
                fecha_pago_dt.strftime('%Y-%m-%d'),
                importe_bruto,
                porcentaje_irpf,
                importe_irpf,
                porcentaje_ss,
                importe_ss,
                otros_descuentos,
                importe_neto,
                f"Calculado el {datetime.now().strftime('%d/%m/%Y')}"
            ))
            
            id_paga_empleado = cursor.lastrowid
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_paga_empleado': id_paga_empleado,
            'tipo_paga': tipo_paga['nombre'],
            'anio': anio,
            'fecha_pago': fecha_pago,
            'importe_bruto': importe_bruto,
            'retenciones': {
                'irpf': {
                    'porcentaje': porcentaje_irpf,
                    'importe': importe_irpf
                },
                'seguridad_social': {
                    'porcentaje': porcentaje_ss,
                    'importe': importe_ss
                },
                'otros': otros_descuentos
            },
            'importe_neto': importe_neto
        }
    
    def _calcular_importe_bruto(self, id_empleado: int, formula: str, 
                              importe_base: float, es_beneficios: bool, anio: int) -> float:
        """Calcula el importe bruto de una paga extra.
        
        Args:
            id_empleado: ID del empleado
            formula: Fórmula para calcular el importe
            importe_base: Importe base configurado
            es_beneficios: Si la paga depende de los beneficios
            anio: Año de la paga
            
        Returns:
            Importe bruto calculado o None si hay error
        """
        cursor = self.conn.cursor()
        
        # Si hay un importe base configurado, usarlo directamente
        if importe_base is not None:
            return importe_base
        
        # Obtener salario base del empleado
        salario_base = self._obtener_salario_base(id_empleado)
        
        if salario_base is None:
            return None
        
        # Variables para la fórmula
        variables = {
            'salario_base': salario_base,
            'porcentaje_beneficios': 0,
            'factor_convenio': 1
        }
        
        # Si es paga de beneficios, obtener porcentaje de beneficios
        if es_beneficios:
            variables['porcentaje_beneficios'] = self._obtener_porcentaje_beneficios(anio)
        
        # Evaluar fórmula
        try:
            # Reemplazar variables en la fórmula
            formula_eval = formula
            for var, valor in variables.items():
                formula_eval = formula_eval.replace(var, str(valor))
            
            # Evaluar fórmula
            importe = eval(formula_eval)
            return importe
        except Exception:
            return None
    
    def _obtener_salario_base(self, id_empleado: int) -> float:
        """Obtiene el salario base de un empleado.
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Salario base o None si no se encuentra
        """
        cursor = self.conn.cursor()
        
        # Buscar en histórico de salarios
        cursor.execute('''
        SELECT valor_nuevo
        FROM HistoricoSalarios
        WHERE id_empleado = ? AND concepto = 'Salario Base'
        ORDER BY fecha DESC
        LIMIT 1
        ''', (id_empleado,))
        
        historico = cursor.fetchone()
        if historico:
            return historico['valor_nuevo']
        
        # Si no hay histórico, buscar en nóminas
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
    
    def _obtener_porcentaje_beneficios(self, anio: int) -> float:
        """Obtiene el porcentaje de beneficios para un año específico.
        
        Args:
            anio: Año para el que se quiere obtener el porcentaje
            
        Returns:
            Porcentaje de beneficios o 0 si no se encuentra
        """
        cursor = self.conn.cursor()
        
        # Buscar en configuración de empresa
        cursor.execute('''
        SELECT valor
        FROM ConfiguracionEmpresa
        WHERE concepto = 'porcentaje_beneficios' AND anio = ?
        ''', (anio,))
        
        config = cursor.fetchone()
        if config:
            return float(config['valor'])
        
        # Si no se encuentra, devolver 0
        return 0
    
    def marcar_paga_como_pagada(self, id_paga_empleado: int) -> Dict:
        """Marca una paga extra como pagada.
        
        Args:
            id_paga_empleado: ID de la paga del empleado
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        UPDATE PagasExtrasEmpleados
        SET es_pagada = 1, comentario = ?
        WHERE id_paga_empleado = ?
        ''', (
            f"Marcada como pagada el {datetime.now().strftime('%d/%m/%Y')}",
            id_paga_empleado
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_paga_empleado': id_paga_empleado,
            'mensaje': 'Paga marcada como pagada'
        }
    
    def obtener_pagas_empleado(self, id_empleado: int, anio: int = None) -> List[Dict]:
        """Obtiene las pagas extras de un empleado.
        
        Args:
            id_empleado: ID del empleado
            anio: Año específico (opcional)
            
        Returns:
            Lista de diccionarios con información de pagas
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT p.id_paga_empleado, p.anio, p.fecha_pago, p.importe_bruto, 
               p.porcentaje_irpf, p.importe_irpf, p.porcentaje_ss, p.importe_ss, 
               p.otros_descuentos, p.importe_neto, p.es_pagada, p.comentario,
               t.codigo, t.nombre, t.mes_pago, t.dia_pago
        FROM PagasExtrasEmpleados p
        JOIN TiposPagaExtra t ON p.id_tipo_paga = t.id_tipo_paga
        WHERE p.id_empleado = ?
        '''
        params = [id_empleado]
        
        # Añadir filtro de año si se proporciona
        if anio:
            query += ' AND p.anio = ?'
            params.append(anio)
        
        # Ordenar por fecha
        query += ' ORDER BY p.fecha_pago'
        
        cursor.execute(query, params)
        
        pagas = []
        for row in cursor.fetchall():
            fecha_pago = datetime.strptime(row['fecha_pago'], '%Y-%m-%d')
            
            pagas.append({
                'id': row['id_paga_empleado'],
                'tipo': {
                    'codigo': row['codigo'],
                    'nombre': row['nombre']
                },
                'anio': row['anio'],
                'fecha_pago': fecha_pago.strftime('%d/%m/%Y'),
                'importe_bruto': row['importe_bruto'],
                'retenciones': {
                    'irpf': {
                        'porcentaje': row['porcentaje_irpf'],
                        'importe': row['importe_irpf']
                    },
                    'seguridad_social': {
                        'porcentaje': row['porcentaje_ss'],
                        'importe': row['importe_ss']
                    },
                    'otros': row['otros_descuentos']
                },
                'importe_neto': row['importe_neto'],
                'es_pagada': bool(row['es_pagada']),
                'comentario': row['comentario']
            })
        
        return pagas
    
    def calcular_todas_pagas_anio(self, id_empleado: int, anio: int) -> Dict:
        """Calcula todas las pagas extras de un empleado para un año específico.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para el que se quieren calcular las pagas
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener todos los tipos de paga
        cursor.execute('''
        SELECT id_tipo_paga, nombre
        FROM TiposPagaExtra
        ''')
        
        tipos_paga = cursor.fetchall()
        
        resultados = []
        
        for tipo_paga in tipos_paga:
            # Calcular cada paga
            resultado = self.calcular_paga_extra(
                id_empleado=id_empleado,
                id_tipo_paga=tipo_paga['id_tipo_paga'],
                anio=anio
            )
            
            if resultado['resultado'] == 'éxito':
                resultados.append({
                    'tipo_paga': tipo_paga['nombre'],
                    'importe_bruto': resultado['importe_bruto'],
                    'importe_neto': resultado['importe_neto'],
                    'fecha_pago': resultado['fecha_pago']
                })
        
        # Calcular totales
        total_bruto = sum(r['importe_bruto'] for r in resultados)
        total_neto = sum(r['importe_neto'] for r in resultados)
        
        return {
            'resultado': 'éxito',
            'anio': anio,
            'pagas_calculadas': len(resultados),
            'pagas': resultados,
            'total_bruto': total_bruto,
            'total_neto': total_neto
        }
    
    def comparar_pagas_anios(self, id_empleado: int, anio1: int, anio2: int) -> Dict:
        """Compara las pagas extras de un empleado entre dos años.
        
        Args:
            id_empleado: ID del empleado
            anio1: Primer año para comparar
            anio2: Segundo año para comparar
            
        Returns:
            Diccionario con resultado de la comparación
        """
        # Obtener pagas del primer año
        pagas_anio1 = self.obtener_pagas_empleado(id_empleado, anio1)
        
        # Obtener pagas del segundo año
        pagas_anio2 = self.obtener_pagas_empleado(id_empleado, anio2)
        
        # Organizar pagas por tipo
        pagas_por_tipo_anio1 = {p['tipo']['codigo']: p for p in pagas_anio1}
        pagas_por_tipo_anio2 = {p['tipo']['codigo']: p for p in pagas_anio2}
        
        # Comparar pagas
        comparaciones = []
        
        # Obtener todos los tipos de paga únicos
        todos_tipos = set(list(pagas_por_tipo_anio1.keys()) + list(pagas_por_tipo_anio2.keys()))
        
        for tipo in todos_tipos:
            paga_anio1 = pagas_por_tipo_anio1.get(tipo)
            paga_anio2 = pagas_por_tipo_anio2.get(tipo)
            
            if paga_anio1 and paga_anio2:
                # Calcular diferencias
                dif_bruto = paga_anio2['importe_bruto'] - paga_anio1['importe_bruto']
                dif_neto = paga_anio2['importe_neto'] - paga_anio1['importe_neto']
                
                porc_bruto = (dif_bruto / paga_anio1['importe_bruto'] * 100) if paga_anio1['importe_bruto'] > 0 else 0
                porc_neto = (dif_neto / paga_anio1['importe_neto'] * 100) if paga_anio1['importe_neto'] > 0 else 0
                
                comparacion = {
                    'tipo': tipo,
                    'nombre': paga_anio1['tipo']['nombre'],
                    'anio1': {
                        'importe_bruto': paga_anio1['importe_bruto'],
                        'importe_neto': paga_anio1['importe_neto']
                    },
                    'anio2': {
                        'importe_bruto': paga_anio2['importe_bruto'],
                        'importe_neto': paga_anio2['importe_neto']
                    },
                    'diferencia': {
                        'bruto': dif_bruto,
                        'neto': dif_neto,
                        'porcentaje_bruto': porc_bruto,
                        'porcentaje_neto': porc_neto
                    }
                }
            elif paga_anio1:
                comparacion = {
                    'tipo': tipo,
                    'nombre': paga_anio1['tipo']['nombre'],
                    'anio1': {
                        'importe_bruto': paga_anio1['importe_bruto'],
                        'importe_neto': paga_anio1['importe_neto']
                    },
                    'anio2': {
                        'importe_bruto': 0,
                        'importe_neto': 0
                    },
                    'diferencia': {
                        'bruto': -paga_anio1['importe_bruto'],
                        'neto': -paga_anio1['importe_neto'],
                        'porcentaje_bruto': -100,
                        'porcentaje_neto': -100
                    }
                }
            else:  # paga_anio2
                comparacion = {
                    'tipo': tipo,
                    'nombre': paga_anio2['tipo']['nombre'],
                    'anio1': {
                        'importe_bruto': 0,
                        'importe_neto': 0
                    },
                    'anio2': {
                        'importe_bruto': paga_anio2['importe_bruto'],
                        'importe_neto': paga_anio2['importe_neto']
                    },
                    'diferencia': {
                        'bruto': paga_anio2['importe_bruto'],
                        'neto': paga_anio2['importe_neto'],
                        'porcentaje_bruto': 100,
                        'porcentaje_neto': 100
                    }
                }
            
            comparaciones.append(comparacion)
        
        # Calcular totales
        total_bruto_anio1 = sum(p['importe_bruto'] for p in pagas_anio1)
        total_neto_anio1 = sum(p['importe_neto'] for p in pagas_anio1)
        
        total_bruto_anio2 = sum(p['importe_bruto'] for p in pagas_anio2)
        total_neto_anio2 = sum(p['importe_neto'] for p in pagas_anio2)
        
        dif_total_bruto = total_bruto_anio2 - total_bruto_anio1
        dif_total_neto = total_neto_anio2 - total_neto_anio1
        
        porc_total_bruto = (dif_total_bruto / total_bruto_anio1 * 100) if total_bruto_anio1 > 0 else 0
        porc_total_neto = (dif_total_neto / total_neto_anio1 * 100) if total_neto_anio1 > 0 else 0
        
        return {
            'resultado': 'éxito',
            'anio1': anio1,
            'anio2': anio2,
            'comparaciones': comparaciones,
            'totales': {
                'anio1': {
                    'bruto': total_bruto_anio1,
                    'neto': total_neto_anio1
                },
                'anio2': {
                    'bruto': total_bruto_anio2,
                    'neto': total_neto_anio2
                },
                'diferencia': {
                    'bruto': dif_total_bruto,
                    'neto': dif_total_neto,
                    'porcentaje_bruto': porc_total_bruto,
                    'porcentaje_neto': porc_total_neto
                }
            }
        }
    
    def simular_cambio_retencion(self, id_paga_empleado: int, 
                                nuevo_porcentaje_irpf: float = None, 
                                nuevo_porcentaje_ss: float = None, 
                                nuevos_otros_descuentos: float = None) -> Dict:
        """Simula un cambio en las retenciones de una paga extra.
        
        Args:
            id_paga_empleado: ID de la paga del empleado
            nuevo_porcentaje_irpf: Nuevo porcentaje de IRPF (opcional)
            nuevo_porcentaje_ss: Nuevo porcentaje de Seguridad Social (opcional)
            nuevos_otros_descuentos: Nuevos otros descuentos (opcional)
            
        Returns:
            Diccionario con resultado de la simulación
        """
        cursor = self.conn.cursor()
        
        # Obtener información de la paga
        cursor.execute('''
        SELECT importe_bruto, porcentaje_irpf, importe_irpf, porcentaje_ss, 
               importe_ss, otros_descuentos, importe_neto
        FROM PagasExtrasEmpleados
        WHERE id_paga_empleado = ?
        ''', (id_paga_empleado,))
        
        paga = cursor.fetchone()
        if not paga:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la paga especificada'
            }
        
        # Calcular nuevos importes
        importe_bruto = paga['importe_bruto']
        
        # IRPF
        porcentaje_irpf = nuevo_porcentaje_irpf if nuevo_porcentaje_irpf is not None else paga['porcentaje_irpf']
        importe_irpf = importe_bruto * (porcentaje_irpf / 100)
        
        # Seguridad Social
        porcentaje_ss = nuevo_porcentaje_ss if nuevo_porcentaje_ss is not None else paga['porcentaje_ss']
        importe_ss = importe_bruto * (porcentaje_ss / 100)
        
        # Otros descuentos
        otros_descuentos = nuevos_otros_descuentos if nuevos_otros_descuentos is not None else paga['otros_descuentos']
        
        # Importe neto
        nuevo_importe_neto = importe_bruto - importe_irpf - importe_ss - otros_descuentos
        
        # Calcular diferencias
        dif_neto = nuevo_importe_neto - paga['importe_neto']
        porc_dif = (dif_neto / paga['importe_neto'] * 100) if paga['importe_neto'] > 0 else 0
        
        return {
            'resultado': 'éxito',
            'id_paga_empleado': id_paga_empleado,
            'importe_bruto': importe_bruto,
            'retenciones_actuales': {
                'irpf': {
                    'porcentaje': paga['porcentaje_irpf'],
                    'importe': paga['importe_irpf']
                },
                'seguridad_social': {
                    'porcentaje': paga['porcentaje_ss'],
                    'importe': paga['importe_ss']
                },
                'otros': paga['otros_descuentos'],
                'importe_neto': paga['importe_neto']
            },
            'retenciones_simuladas': {
                'irpf': {
                    'porcentaje': porcentaje_irpf,
                    'importe': importe_irpf
                },
                'seguridad_social': {
                    'porcentaje': porcentaje_ss,
                    'importe': importe_ss
                },
                'otros': otros_descuentos,
                'importe_neto': nuevo_importe_neto
            },
            'diferencia': {
                'importe': dif_neto,
                'porcentaje': porc_dif
            }
        }
    
    def aplicar_cambio_retencion(self, id_paga_empleado: int, 
                               nuevo_porcentaje_irpf: float = None, 
                               nuevo_porcentaje_ss: float = None, 
                               nuevos_otros_descuentos: float = None) -> Dict:
        """Aplica un cambio en las retenciones de una paga extra.
        
        Args:
            id_paga_empleado: ID de la paga del empleado
            nuevo_porcentaje_irpf: Nuevo porcentaje de IRPF (opcional)
            nuevo_porcentaje_ss: Nuevo porcentaje de Seguridad Social (opcional)
            nuevos_otros_descuentos: Nuevos otros descuentos (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Obtener información de la paga
        cursor.execute('''
        SELECT importe_bruto, porcentaje_irpf, porcentaje_ss, otros_descuentos
        FROM PagasExtrasEmpleados
        WHERE id_paga_empleado = ?
        ''', (id_paga_empleado,))
        
        paga = cursor.fetchone()
        if not paga:
            return {
                'resultado': 'error',
                'mensaje': 'No se encontró la paga especificada'
            }
        
        # Determinar nuevos valores
        porcentaje_irpf = nuevo_porcentaje_irpf if nuevo_porcentaje_irpf is not None else paga['porcentaje_irpf']
        porcentaje_ss = nuevo_porcentaje_ss if nuevo_porcentaje_ss is not None else paga['porcentaje_ss']
        otros_descuentos = nuevos_otros_descuentos if nuevos_otros_descuentos is not None else paga['otros_descuentos']
        
        # Calcular nuevos importes
        importe_bruto = paga['importe_bruto']
        importe_irpf = importe_bruto * (porcentaje_irpf / 100)
        importe_ss = importe_bruto * (porcentaje_ss / 100)
        importe_neto = importe_bruto - importe_irpf - importe_ss - otros_descuentos
        
        # Actualizar paga
        cursor.execute('''
        UPDATE PagasExtrasEmpleados
        SET porcentaje_irpf = ?, importe_irpf = ?, porcentaje_ss = ?, importe_ss = ?,
            otros_descuentos = ?, importe_neto = ?, comentario = ?
        WHERE id_paga_empleado = ?
        ''', (
            porcentaje_irpf,
            importe_irpf,
            porcentaje_ss,
            importe_ss,
            otros_descuentos,
            importe_neto,
            f"Retenciones modificadas el {datetime.now().strftime('%d/%m/%Y')}",
            id_paga_empleado
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_paga_empleado': id_paga_empleado,
            'nuevas_retenciones': {
                'irpf': {
                    'porcentaje': porcentaje_irpf,
                    'importe': importe_irpf
                },
                'seguridad_social': {
                    'porcentaje': porcentaje_ss,
                    'importe': importe_ss
                },
                'otros': otros_descuentos
            },
            'nuevo_importe_neto': importe_neto
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del gestor de pagas extras
    gestor = GestorPagasExtras()
    
    # Configurar paga extra
    id_tipo_paga = 1  # Ajustar según la base de datos
    anio_actual = datetime.now().year
    
    resultado = gestor.configurar_paga_extra(
        id_tipo_paga=id_tipo_paga,
        anio=anio_actual,
        porcentaje_irpf=15,
        porcentaje_ss=6.35
    )
    print(f"Paga extra configurada: {resultado}")
    
    # Calcular paga extra para un empleado
    id_empleado = 1  # Ajustar según la base de datos
    resultado = gestor.calcular_paga_extra(
        id_empleado=id_empleado,
        id_tipo_paga=id_tipo_paga,
        anio=anio_actual
    )
    print(f"Paga extra calculada: {resultado}")
    
    # Obtener pagas del empleado
    pagas = gestor.obtener_pagas_empleado(id_empleado, anio_actual)
    print(f"Pagas del empleado: {len(pagas)}")
    
    print("\nProceso completado.")
