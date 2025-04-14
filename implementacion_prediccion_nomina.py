"""
Módulo de Predicción de Nómina

Este módulo implementa la funcionalidad para predecir nóminas futuras basadas en
el calendario laboral, pluses configurados y datos históricos.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class PredictorNomina:
    """Clase para predecir nóminas futuras basadas en calendario laboral y configuración."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa el predictor de nómina.
        
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
        """Inicializa las tablas necesarias para la predicción de nóminas."""
        cursor = self.conn.cursor()
        
        # Tabla para configuración de predicción
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConfiguracionPrediccion (
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
        
        # Tabla para nóminas predichas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS NominasPredecidas (
            id_nomina_predicha INTEGER PRIMARY KEY,
            id_empleado INTEGER,
            periodo_inicio TEXT,
            periodo_fin TEXT,
            fecha_prediccion TEXT,
            total_devengos REAL,
            total_deducciones REAL,
            liquido REAL,
            comentario TEXT,
            FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
        )
        ''')
        
        # Tabla para conceptos de nóminas predichas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConceptosNominaPredecida (
            id_concepto INTEGER PRIMARY KEY,
            id_nomina_predicha INTEGER,
            tipo TEXT,
            concepto TEXT,
            unidades REAL,
            tarifa REAL,
            importe REAL,
            es_retroactivo INTEGER,
            FOREIGN KEY (id_nomina_predicha) REFERENCES NominasPredecidas(id_nomina_predicha)
        )
        ''')
        
        self.conn.commit()
    
    def obtener_configuracion_prediccion(self, id_empleado: int, concepto: str, 
                                        fecha: str = None) -> Dict:
        """Obtiene la configuración de predicción para un concepto específico.
        
        Args:
            id_empleado: ID del empleado
            concepto: Concepto de predicción
            fecha: Fecha en formato 'DD/MM/YYYY' (opcional, por defecto fecha actual)
            
        Returns:
            Diccionario con información de la configuración
        """
        cursor = self.conn.cursor()
        
        # Si no se proporciona fecha, usar la fecha actual
        if not fecha:
            fecha = datetime.now().strftime('%d/%m/%Y')
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        
        # Buscar configuración
        cursor.execute('''
        SELECT valor, descripcion
        FROM ConfiguracionPrediccion
        WHERE id_empleado = ? AND concepto = ? AND fecha_inicio <= ? AND (fecha_fin >= ? OR fecha_fin IS NULL)
        ORDER BY fecha_inicio DESC
        LIMIT 1
        ''', (id_empleado, concepto, fecha_dt.strftime('%Y-%m-%d'), fecha_dt.strftime('%Y-%m-%d')))
        
        config = cursor.fetchone()
        if config:
            return {
                'concepto': concepto,
                'valor': config['valor'],
                'descripcion': config['descripcion'],
                'fecha': fecha
            }
        
        # Si no hay configuración específica, buscar valores por defecto
        valores_defecto = {
            'salario_base': self._obtener_salario_base_defecto(id_empleado, fecha),
            'porcentaje_irpf': 16.0,  # Valor por defecto
            'porcentaje_ss_trabajador': 6.35,  # Valor por defecto (4.7% + 1.55% + 0.1%)
            'porcentaje_antiguedad': 1.0,  # Valor por defecto
            'dias_laborables_mes': 21,  # Valor por defecto
            'horas_jornada': 8.0,  # Valor por defecto
        }
        
        if concepto in valores_defecto:
            return {
                'concepto': concepto,
                'valor': valores_defecto[concepto],
                'descripcion': 'Valor por defecto',
                'fecha': fecha
            }
        
        # Si no se encuentra, devolver valor cero
        return {
            'concepto': concepto,
            'valor': 0,
            'descripcion': 'No se encontró configuración',
            'fecha': fecha
        }
    
    def _obtener_salario_base_defecto(self, id_empleado: int, fecha: str) -> float:
        """Obtiene el salario base por defecto basado en nóminas anteriores.
        
        Args:
            id_empleado: ID del empleado
            fecha: Fecha en formato 'DD/MM/YYYY'
            
        Returns:
            Salario base por defecto
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        
        # Buscar en nóminas anteriores
        cursor.execute('''
        SELECT n.id_nomina
        FROM Nominas n
        WHERE n.id_empleado = ?
        ORDER BY n.periodo_fin DESC
        LIMIT 1
        ''', (id_empleado,))
        
        nomina = cursor.fetchone()
        if nomina:
            # Obtener salario base de la última nómina
            cursor.execute('''
            SELECT importe
            FROM ConceptosNomina
            WHERE id_nomina = ? AND concepto = 'Salario'
            LIMIT 1
            ''', (nomina['id_nomina'],))
            
            concepto = cursor.fetchone()
            if concepto:
                return concepto['importe']
        
        # Si no se encuentra, devolver valor por defecto
        return 1500.0  # Valor por defecto
    
    def establecer_configuracion_prediccion(self, id_empleado: int, concepto: str, 
                                          valor: float, fecha_inicio: str, 
                                          fecha_fin: str = None, descripcion: str = "") -> Dict:
        """Establece la configuración de predicción para un concepto específico.
        
        Args:
            id_empleado: ID del empleado
            concepto: Concepto de predicción
            valor: Valor del concepto
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY'
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY' (opcional)
            descripcion: Descripción adicional (opcional)
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Convertir fechas a formato de base de datos
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y') if fecha_fin else None
        
        # Insertar en configuración de predicción
        cursor.execute('''
        INSERT INTO ConfiguracionPrediccion
        (id_empleado, concepto, valor, fecha_inicio, fecha_fin, descripcion)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            concepto,
            valor,
            fecha_inicio_dt.strftime('%Y-%m-%d'),
            fecha_fin_dt.strftime('%Y-%m-%d') if fecha_fin_dt else None,
            descripcion
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'concepto': concepto,
            'valor': valor,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    
    def predecir_nomina_mes(self, id_empleado: int, anio: int, mes: int) -> Dict:
        """Predice la nómina para un mes específico basada en el calendario laboral.
        
        Args:
            id_empleado: ID del empleado
            anio: Año de la predicción
            mes: Mes de la predicción (1-12)
            
        Returns:
            Diccionario con la nómina predicha
        """
        cursor = self.conn.cursor()
        
        # Obtener primer y último día del mes
        primer_dia = date(anio, mes, 1)
        if mes == 12:
            ultimo_dia = date(anio + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(anio, mes + 1, 1) - timedelta(days=1)
        
        # Formatear fechas
        periodo_inicio = primer_dia.strftime('%d/%m/%Y')
        periodo_fin = ultimo_dia.strftime('%d/%m/%Y')
        
        # Obtener días laborables del mes desde el calendario
        cursor.execute('''
        SELECT COUNT(*) as dias_laborables
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Laboral'
        ''', (id_empleado, primer_dia.strftime('%Y-%m-%d'), ultimo_dia.strftime('%Y-%m-%d')))
        
        dias_result = cursor.fetchone()
        dias_laborables = dias_result['dias_laborables'] if dias_result else 0
        
        # Si no hay días laborables en el calendario, usar valor por defecto
        if dias_laborables == 0:
            config_dias = self.obtener_configuracion_prediccion(id_empleado, 'dias_laborables_mes')
            dias_laborables = config_dias['valor']
        
        # Obtener configuración básica
        salario_base_config = self.obtener_configuracion_prediccion(id_empleado, 'salario_base', periodo_inicio)
        salario_base = salario_base_config['valor']
        
        porcentaje_irpf_config = self.obtener_configuracion_prediccion(id_empleado, 'porcentaje_irpf', periodo_inicio)
        porcentaje_irpf = porcentaje_irpf_config['valor']
        
        porcentaje_ss_config = self.obtener_configuracion_prediccion(id_empleado, 'porcentaje_ss_trabajador', periodo_inicio)
        porcentaje_ss = porcentaje_ss_config['valor']
        
        porcentaje_antiguedad_config = self.obtener_configuracion_prediccion(id_empleado, 'porcentaje_antiguedad', periodo_inicio)
        porcentaje_antiguedad = porcentaje_antiguedad_config['valor']
        
        # Calcular conceptos básicos
        antiguedad = salario_base * (porcentaje_antiguedad / 100)
        
        # Inicializar listas para conceptos
        conceptos_devengo = []
        conceptos_deduccion = []
        
        # Añadir conceptos fijos
        conceptos_devengo.append({
            'concepto': 'Salario',
            'unidades': dias_laborables,
            'tarifa': salario_base / dias_laborables if dias_laborables > 0 else 0,
            'importe': salario_base,
            'es_retroactivo': 0
        })
        
        conceptos_devengo.append({
            'concepto': 'Antigüedad',
            'unidades': dias_laborables,
            'tarifa': antiguedad / dias_laborables if dias_laborables > 0 else 0,
            'importe': antiguedad,
            'es_retroactivo': 0
        })
        
        # Calcular pluses basados en el calendario
        pluses = self._calcular_pluses_calendario(id_empleado, primer_dia, ultimo_dia)
        
        # Añadir pluses a conceptos de devengo
        for plus, datos in pluses.items():
            conceptos_devengo.append({
                'concepto': plus,
                'unidades': datos['cantidad'],
                'tarifa': datos['valor_unitario'],
                'importe': datos['valor_total'],
                'es_retroactivo': 0
            })
        
        # Calcular total de devengos
        total_devengos = sum(c['importe'] for c in conceptos_devengo)
        
        # Calcular deducciones
        base_ss = total_devengos
        retencion_ss = base_ss * (porcentaje_ss / 100)
        
        base_irpf = total_devengos
        retencion_irpf = base_irpf * (porcentaje_irpf / 100)
        
        # Añadir deducciones
        conceptos_deduccion.append({
            'concepto': 'Retención a cta. IRPF',
            'unidades': porcentaje_irpf,
            'tarifa': base_irpf,
            'importe': retencion_irpf,
            'es_retroactivo': 0
        })
        
        conceptos_deduccion.append({
            'concepto': 'Trab.cont.comunes',
            'unidades': 4.70,  # Porcentaje fijo
            'tarifa': base_ss,
            'importe': base_ss * 0.047,
            'es_retroactivo': 0
        })
        
        conceptos_deduccion.append({
            'concepto': 'Trab.desempleo',
            'unidades': 1.55,  # Porcentaje fijo
            'tarifa': base_ss,
            'importe': base_ss * 0.0155,
            'es_retroactivo': 0
        })
        
        conceptos_deduccion.append({
            'concepto': 'Trab.formac.profesional',
            'unidades': 0.10,  # Porcentaje fijo
            'tarifa': base_ss,
            'importe': base_ss * 0.001,
            'es_retroactivo': 0
        })
        
        # Calcular total de deducciones
        total_deducciones = sum(c['importe'] for c in conceptos_deduccion)
        
        # Calcular líquido
        liquido = total_devengos - total_deducciones
        
        # Guardar nómina predicha en la base de datos
        cursor.execute('''
        INSERT INTO NominasPredecidas
        (id_empleado, periodo_inicio, periodo_fin, fecha_prediccion, total_devengos, total_deducciones, liquido, comentario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_empleado,
            periodo_inicio,
            periodo_fin,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_devengos,
            total_deducciones,
            liquido,
            f"Predicción para {mes}/{anio}"
        ))
        
        id_nomina_predicha = cursor.lastrowid
        
        # Guardar conceptos
        for concepto in conceptos_devengo:
            cursor.execute('''
            INSERT INTO ConceptosNominaPredecida
            (id_nomina_predicha, tipo, concepto, unidades, tarifa, importe, es_retroactivo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_nomina_predicha,
                'devengo',
                concepto['concepto'],
                concepto['unidades'],
                concepto['tarifa'],
                concepto['importe'],
                concepto['es_retroactivo']
            ))
        
        for concepto in conceptos_deduccion:
            cursor.execute('''
            INSERT INTO ConceptosNominaPredecida
            (id_nomina_predicha, tipo, concepto, unidades, tarifa, importe, es_retroactivo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_nomina_predicha,
                'deduccion',
                concepto['concepto'],
                concepto['unidades'],
                concepto['tarifa'],
                concepto['importe'],
                concepto['es_retroactivo']
            ))
        
        self.conn.commit()
        
        # Preparar resultado
        resultado = {
            'id_nomina_predicha': id_nomina_predicha,
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'total_devengos': total_devengos,
            'total_deducciones': total_deducciones,
            'liquido': liquido,
            'conceptos_devengo': conceptos_devengo,
            'conceptos_deduccion': conceptos_deduccion,
            'dias_laborables': dias_laborab
(Content truncated due to size limit. Use line ranges to read in chunks)