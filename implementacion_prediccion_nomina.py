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
            'dias_laborables': dias_laborables
        }
        
        return resultado
    
    def _calcular_pluses_calendario(self, id_empleado: int, fecha_inicio: date, 
                                   fecha_fin: date) -> Dict[str, Dict]:
        """Calcula los pluses basados en el calendario laboral.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            Diccionario con información de pluses
        """
        cursor = self.conn.cursor()
        
        # Inicializar diccionario de pluses
        pluses = {}
        
        # Obtener días con nocturnidad
        cursor.execute('''
        SELECT COUNT(*) as dias_nocturnidad
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND turno = 'Nocturno'
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        dias_nocturnidad = cursor.fetchone()['dias_nocturnidad']
        
        if dias_nocturnidad > 0:
            # Obtener valor unitario de nocturnidad
            valor_nocturnidad = self._obtener_valor_plus(id_empleado, 'Nocturnidad', fecha_inicio.strftime('%d/%m/%Y'))
            
            # Calcular horas de nocturnidad (8 horas por día)
            horas_nocturnidad = dias_nocturnidad * 8
            
            pluses['Nocturnidad'] = {
                'cantidad': horas_nocturnidad,
                'valor_unitario': valor_nocturnidad,
                'valor_total': horas_nocturnidad * valor_nocturnidad
            }
        
        # Obtener días festivos trabajados
        cursor.execute('''
        SELECT COUNT(*) as dias_festivos
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Festivo' AND descripcion LIKE '%Trabajado%'
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        dias_festivos = cursor.fetchone()['dias_festivos']
        
        if dias_festivos > 0:
            # Obtener valor unitario de plus festivo
            valor_festivo = self._obtener_valor_plus(id_empleado, 'Plus trab.días Festivos', fecha_inicio.strftime('%d/%m/%Y'))
            
            pluses['Plus trab.días Festivos'] = {
                'cantidad': dias_festivos,
                'valor_unitario': valor_festivo,
                'valor_total': dias_festivos * valor_festivo
            }
        
        # Obtener días con prima de calidad
        cursor.execute('''
        SELECT COUNT(*) as dias_calidad
        FROM CalendarioLaboral
        WHERE id_empleado = ? AND fecha BETWEEN ? AND ? AND tipo_dia = 'Laboral'
        ''', (id_empleado, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
        
        dias_calidad = cursor.fetchone()['dias_calidad']
        
        if dias_calidad > 0:
            # Obtener valor unitario de prima de calidad
            valor_calidad = self._obtener_valor_plus(id_empleado, 'Plus Prima Calidad', fecha_inicio.strftime('%d/%m/%Y'))
            
            pluses['Plus Prima Calidad'] = {
                'cantidad': dias_calidad,
                'valor_unitario': valor_calidad,
                'valor_total': dias_calidad * valor_calidad
            }
        
        # Obtener días con prima directa
        if dias_calidad > 0:
            # Obtener valor unitario de prima directa
            valor_directa = self._obtener_valor_plus(id_empleado, 'Prima Directa', fecha_inicio.strftime('%d/%m/%Y'))
            
            pluses['Prima Directa'] = {
                'cantidad': dias_calidad,
                'valor_unitario': valor_directa,
                'valor_total': dias_calidad * valor_directa
            }
        
        return pluses
    
    def _obtener_valor_plus(self, id_empleado: int, tipo_plus: str, fecha: str) -> float:
        """Obtiene el valor unitario de un plus específico.
        
        Args:
            id_empleado: ID del empleado
            tipo_plus: Tipo de plus
            fecha: Fecha en formato 'DD/MM/YYYY'
            
        Returns:
            Valor unitario del plus
        """
        cursor = self.conn.cursor()
        
        # Convertir fecha a formato de base de datos
        fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
        
        # Buscar en configuración de tarifas
        cursor.execute('''
        SELECT valor
        FROM ConfiguracionTarifas
        WHERE id_empleado = ? AND concepto = ? AND fecha_inicio <= ? AND (fecha_fin >= ? OR fecha_fin IS NULL)
        ORDER BY fecha_inicio DESC
        LIMIT 1
        ''', (id_empleado, tipo_plus, fecha_dt.strftime('%Y-%m-%d'), fecha_dt.strftime('%Y-%m-%d')))
        
        config = cursor.fetchone()
        if config:
            return config['valor']
        
        # Si no hay configuración, buscar en histórico de nóminas
        anio = fecha_dt.year
        mes = fecha_dt.month
        
        # Obtener el primer y último día del mes
        primer_dia = datetime(anio, mes, 1).strftime('%d/%m/%Y')
        if mes == 12:
            ultimo_dia = datetime(anio + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(anio, mes + 1, 1) - timedelta(days=1)
        ultimo_dia = ultimo_dia.strftime('%d/%m/%Y')
        
        # Buscar nómina del mes correspondiente o anterior
        cursor.execute('''
        SELECT id_nomina
        FROM Nominas
        WHERE id_empleado = ?
        ORDER BY periodo_fin DESC
        LIMIT 1
        ''', (id_empleado,))
        
        nomina = cursor.fetchone()
        if nomina:
            cursor.execute('''
            SELECT tarifa
            FROM ConceptosNomina
            WHERE id_nomina = ? AND concepto = ?
            LIMIT 1
            ''', (nomina['id_nomina'], tipo_plus))
            
            concepto = cursor.fetchone()
            if concepto:
                return concepto['tarifa']
        
        # Valores por defecto si no se encuentra información
        valores_defecto = {
            'Nocturnidad': 3.38,
            'Plus trab.días Festivos': 17.70,
            'Plus Prima Calidad': 2.23,
            'Prima Directa': 12.63
        }
        
        return valores_defecto.get(tipo_plus, 0)
    
    def obtener_nomina_predicha(self, id_nomina_predicha: int) -> Dict:
        """Obtiene una nómina predicha específica.
        
        Args:
            id_nomina_predicha: ID de la nómina predicha
            
        Returns:
            Diccionario con información de la nómina predicha
        """
        cursor = self.conn.cursor()
        
        # Obtener información general de la nómina
        cursor.execute('''
        SELECT id_empleado, periodo_inicio, periodo_fin, fecha_prediccion, total_devengos, total_deducciones, liquido, comentario
        FROM NominasPredecidas
        WHERE id_nomina_predicha = ?
        ''', (id_nomina_predicha,))
        
        nomina = cursor.fetchone()
        if not nomina:
            return {'error': 'No se encontró la nómina predicha'}
        
        # Obtener conceptos de devengo
        cursor.execute('''
        SELECT concepto, unidades, tarifa, importe, es_retroactivo
        FROM ConceptosNominaPredecida
        WHERE id_nomina_predicha = ? AND tipo = 'devengo'
        ''', (id_nomina_predicha,))
        
        conceptos_devengo = []
        for row in cursor.fetchall():
            conceptos_devengo.append({
                'concepto': row['concepto'],
                'unidades': row['unidades'],
                'tarifa': row['tarifa'],
                'importe': row['importe'],
                'es_retroactivo': bool(row['es_retroactivo'])
            })
        
        # Obtener conceptos de deducción
        cursor.execute('''
        SELECT concepto, unidades, tarifa, importe, es_retroactivo
        FROM ConceptosNominaPredecida
        WHERE id_nomina_predicha = ? AND tipo = 'deduccion'
        ''', (id_nomina_predicha,))
        
        conceptos_deduccion = []
        for row in cursor.fetchall():
            conceptos_deduccion.append({
                'concepto': row['concepto'],
                'unidades': row['unidades'],
                'tarifa': row['tarifa'],
                'importe': row['importe'],
                'es_retroactivo': bool(row['es_retroactivo'])
            })
        
        # Preparar resultado
        resultado = {
            'id_nomina_predicha': id_nomina_predicha,
            'id_empleado': nomina['id_empleado'],
            'periodo_inicio': nomina['periodo_inicio'],
            'periodo_fin': nomina['periodo_fin'],
            'fecha_prediccion': nomina['fecha_prediccion'],
            'total_devengos': nomina['total_devengos'],
            'total_deducciones': nomina['total_deducciones'],
            'liquido': nomina['liquido'],
            'comentario': nomina['comentario'],
            'conceptos_devengo': conceptos_devengo,
            'conceptos_deduccion': conceptos_deduccion
        }
        
        return resultado
    
    def listar_nominas_predichas(self, id_empleado: int, fecha_inicio: str = None, 
                               fecha_fin: str = None) -> List[Dict]:
        """Lista las nóminas predichas para un empleado.
        
        Args:
            id_empleado: ID del empleado
            fecha_inicio: Fecha de inicio en formato 'DD/MM/YYYY' (opcional)
            fecha_fin: Fecha de fin en formato 'DD/MM/YYYY' (opcional)
            
        Returns:
            Lista de diccionarios con información resumida de nóminas predichas
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta base
        query = '''
        SELECT id_nomina_predicha, periodo_inicio, periodo_fin, fecha_prediccion, total_devengos, total_deducciones, liquido, comentario
        FROM NominasPredecidas
        WHERE id_empleado = ?
        '''
        params = [id_empleado]
        
        # Añadir filtros de fecha si se proporcionan
        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%d/%m/%Y')
            query += ' AND periodo_inicio >= ?'
            params.append(fecha_inicio_dt.strftime('%d/%m/%Y'))
        
        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%d/%m/%Y')
            query += ' AND periodo_fin <= ?'
            params.append(fecha_fin_dt.strftime('%d/%m/%Y'))
        
        # Ordenar por periodo
        query += ' ORDER BY periodo_inicio DESC'
        
        cursor.execute(query, params)
        
        nominas = []
        for row in cursor.fetchall():
            nominas.append({
                'id_nomina_predicha': row['id_nomina_predicha'],
                'periodo_inicio': row['periodo_inicio'],
                'periodo_fin': row['periodo_fin'],
                'fecha_prediccion': row['fecha_prediccion'],
                'total_devengos': row['total_devengos'],
                'total_deducciones': row['total_deducciones'],
                'liquido': row['liquido'],
                'comentario': row['comentario']
            })
        
        return nominas
    
    def comparar_nomina_real_predicha(self, id_empleado: int, periodo: str) -> Dict:
        """Compara una nómina real con su predicción.
        
        Args:
            id_empleado: ID del empleado
            periodo: Periodo en formato 'DD/MM/YYYY-DD/MM/YYYY'
            
        Returns:
            Diccionario con resultados de la comparación
        """
        cursor = self.conn.cursor()
        
        # Separar periodo en inicio y fin
        periodo_inicio, periodo_fin = periodo.split('-')
        
        # Obtener nómina real
        cursor.execute('''
        SELECT id_nomina, total_devengos, total_deducciones, liquido
        FROM Nominas
        WHERE id_empleado = ? AND periodo_inicio = ? AND periodo_fin = ?
        ''', (id_empleado, periodo_inicio, periodo_fin))
        
        nomina_real = cursor.fetchone()
        if not nomina_real:
            return {'error': 'No se encontró la nómina real para el periodo especificado'}
        
        # Obtener nómina predicha
        cursor.execute('''
        SELECT id_nomina_predicha, total_devengos, total_deducciones, liquido
        FROM NominasPredecidas
        WHERE id_empleado = ? AND periodo_inicio = ? AND periodo_fin = ?
        ORDER BY fecha_prediccion DESC
        LIMIT 1
        ''', (id_empleado, periodo_inicio, periodo_fin))
        
        nomina_predicha = cursor.fetchone()
        if not nomina_predicha:
            return {'error': 'No se encontró una predicción para el periodo especificado'}
        
        # Obtener conceptos de la nómina real
        cursor.execute('''
        SELECT tipo, concepto, unidades, tarifa, importe
        FROM ConceptosNomina
        WHERE id_nomina = ?
        ''', (nomina_real['id_nomina'],))
        
        conceptos_real = {}
        for row in cursor.fetchall():
            conceptos_real[f"{row['tipo']}_{row['concepto']}"] = {
                'tipo': row['tipo'],
                'concepto': row['concepto'],
                'unidades': row['unidades'],
                'tarifa': row['tarifa'],
                'importe': row['importe']
            }
        
        # Obtener conceptos de la nómina predicha
        cursor.execute('''
        SELECT tipo, concepto, unidades, tarifa, importe
        FROM ConceptosNominaPredecida
        WHERE id_nomina_predicha = ?
        ''', (nomina_predicha['id_nomina_predicha'],))
        
        conceptos_predicha = {}
        for row in cursor.fetchall():
            conceptos_predicha[f"{row['tipo']}_{row['concepto']}"] = {
                'tipo': row['tipo'],
                'concepto': row['concepto'],
                'unidades': row['unidades'],
                'tarifa': row['tarifa'],
                'importe': row['importe']
            }
        
        # Comparar totales
        comparacion_totales = {
            'total_devengos': {
                'real': nomina_real['total_devengos'],
                'predicha': nomina_predicha['total_devengos'],
                'diferencia': nomina_real['total_devengos'] - nomina_predicha['total_devengos'],
                'porcentaje': (nomina_real['total_devengos'] - nomina_predicha['total_devengos']) / nomina_predicha['total_devengos'] * 100 if nomina_predicha['total_devengos'] else 0
            },
            'total_deducciones': {
                'real': nomina_real['total_deducciones'],
                'predicha': nomina_predicha['total_deducciones'],
                'diferencia': nomina_real['total_deducciones'] - nomina_predicha['total_deducciones'],
                'porcentaje': (nomina_real['total_deducciones'] - nomina_predicha['total_deducciones']) / nomina_predicha['total_deducciones'] * 100 if nomina_predicha['total_deducciones'] else 0
            },
            'liquido': {
                'real': nomina_real['liquido'],
                'predicha': nomina_predicha['liquido'],
                'diferencia': nomina_real['liquido'] - nomina_predicha['liquido'],
                'porcentaje': (nomina_real['liquido'] - nomina_predicha['liquido']) / nomina_predicha['liquido'] * 100 if nomina_predicha['liquido'] else 0
            }
        }
        
        # Comparar conceptos
        comparacion_conceptos = []
        todos_conceptos = set(conceptos_real.keys()) | set(conceptos_predicha.keys())
        
        for clave in todos_conceptos:
            concepto_real = conceptos_real.get(clave, {'importe': 0, 'unidades': 0, 'tarifa': 0})
            concepto_predicha = conceptos_predicha.get(clave, {'importe': 0, 'unidades': 0, 'tarifa': 0})
            
            # Extraer tipo y nombre del concepto
            if '_' in clave:
                tipo, nombre = clave.split('_', 1)
            else:
                tipo = ''
                nombre = clave
            
            comparacion = {
                'tipo': tipo,
                'concepto': nombre,
                'importe_real': concepto_real.get('importe', 0),
                'importe_predicha': concepto_predicha.get('importe', 0),
                'diferencia_importe': concepto_real.get('importe', 0) - concepto_predicha.get('importe', 0),
                'unidades_real': concepto_real.get('unidades', 0),
                'unidades_predicha': concepto_predicha.get('unidades', 0),
                'diferencia_unidades': concepto_real.get('unidades', 0) - concepto_predicha.get('unidades', 0),
                'tarifa_real': concepto_real.get('tarifa', 0),
                'tarifa_predicha': concepto_predicha.get('tarifa', 0),
                'diferencia_tarifa': concepto_real.get('tarifa', 0) - concepto_predicha.get('tarifa', 0)
            }
            
            # Calcular porcentaje de variación si el importe predicho no es cero
            if concepto_predicha.get('importe', 0) != 0:
                comparacion['porcentaje_variacion'] = (comparacion['diferencia_importe'] / concepto_predicha.get('importe', 0)) * 100
            else:
                comparacion['porcentaje_variacion'] = float('inf') if comparacion['diferencia_importe'] > 0 else 0
            
            # Determinar si hay desviación significativa (más del 5% o concepto nuevo/eliminado)
            comparacion['desviacion_significativa'] = (
                abs(comparacion.get('porcentaje_variacion', 0)) > 5 if 'porcentaje_variacion' in comparacion else True
            )
            
            comparacion_conceptos.append(comparacion)
        
        # Ordenar por magnitud de desviación
        comparacion_conceptos.sort(key=lambda x: abs(x.get('porcentaje_variacion', 0)), reverse=True)
        
        return {
            'periodo': periodo,
            'comparacion_totales': comparacion_totales,
            'comparacion_conceptos': comparacion_conceptos,
            'desviaciones_significativas': [c for c in comparacion_conceptos if c['desviacion_significativa']]
        }
    
    def predecir_nomina_anual(self, id_empleado: int, anio: int) -> Dict:
        """Predice las nóminas para todo un año.
        
        Args:
            id_empleado: ID del empleado
            anio: Año de la predicción
            
        Returns:
            Diccionario con resumen de las predicciones anuales
        """
        # Predecir nómina para cada mes
        predicciones_mensuales = []
        total_anual_devengos = 0
        total_anual_deducciones = 0
        total_anual_liquido = 0
        
        for mes in range(1, 13):
            prediccion = self.predecir_nomina_mes(id_empleado, anio, mes)
            
            predicciones_mensuales.append({
                'mes': mes,
                'periodo_inicio': prediccion['periodo_inicio'],
                'periodo_fin': prediccion['periodo_fin'],
                'total_devengos': prediccion['total_devengos'],
                'total_deducciones': prediccion['total_deducciones'],
                'liquido': prediccion['liquido'],
                'id_nomina_predicha': prediccion['id_nomina_predicha']
            })
            
            total_anual_devengos += prediccion['total_devengos']
            total_anual_deducciones += prediccion['total_deducciones']
            total_anual_liquido += prediccion['liquido']
        
        # Calcular promedios
        promedio_devengos = total_anual_devengos / 12
        promedio_deducciones = total_anual_deducciones / 12
        promedio_liquido = total_anual_liquido / 12
        
        return {
            'anio': anio,
            'predicciones_mensuales': predicciones_mensuales,
            'total_anual_devengos': total_anual_devengos,
            'total_anual_deducciones': total_anual_deducciones,
            'total_anual_liquido': total_anual_liquido,
            'promedio_devengos': promedio_devengos,
            'promedio_deducciones': promedio_deducciones,
            'promedio_liquido': promedio_liquido
        }
    
    def editar_nomina_predicha_manual(self, id_nomina_predicha: int, 
                                     conceptos_modificados: List[Dict]) -> Dict:
        """Edita manualmente una nómina predicha.
        
        Args:
            id_nomina_predicha: ID de la nómina predicha
            conceptos_modificados: Lista de conceptos a modificar
            
        Returns:
            Diccionario con resultado de la operación
        """
        cursor = self.conn.cursor()
        
        # Verificar que la nómina predicha existe
        cursor.execute('''
        SELECT id_nomina_predicha
        FROM NominasPredecidas
        WHERE id_nomina_predicha = ?
        ''', (id_nomina_predicha,))
        
        if not cursor.fetchone():
            return {'error': 'No se encontró la nómina predicha'}
        
        # Actualizar cada concepto modificado
        for concepto in conceptos_modificados:
            cursor.execute('''
            UPDATE ConceptosNominaPredecida
            SET unidades = ?, tarifa = ?, importe = ?
            WHERE id_nomina_predicha = ? AND tipo = ? AND concepto = ?
            ''', (
                concepto['unidades'],
                concepto['tarifa'],
                concepto['importe'],
                id_nomina_predicha,
                concepto['tipo'],
                concepto['concepto']
            ))
            
            # Si no se actualizó ninguna fila, insertar nuevo concepto
            if cursor.rowcount == 0:
                cursor.execute('''
                INSERT INTO ConceptosNominaPredecida
                (id_nomina_predicha, tipo, concepto, unidades, tarifa, importe, es_retroactivo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    id_nomina_predicha,
                    concepto['tipo'],
                    concepto['concepto'],
                    concepto['unidades'],
                    concepto['tarifa'],
                    concepto['importe'],
                    0  # No es retroactivo por defecto
                ))
        
        # Recalcular totales
        cursor.execute('''
        SELECT SUM(importe) as total_devengos
        FROM ConceptosNominaPredecida
        WHERE id_nomina_predicha = ? AND tipo = 'devengo'
        ''', (id_nomina_predicha,))
        
        total_devengos = cursor.fetchone()['total_devengos'] or 0
        
        cursor.execute('''
        SELECT SUM(importe) as total_deducciones
        FROM ConceptosNominaPredecida
        WHERE id_nomina_predicha = ? AND tipo = 'deduccion'
        ''', (id_nomina_predicha,))
        
        total_deducciones = cursor.fetchone()['total_deducciones'] or 0
        
        liquido = total_devengos - total_deducciones
        
        # Actualizar nómina predicha
        cursor.execute('''
        UPDATE NominasPredecidas
        SET total_devengos = ?, total_deducciones = ?, liquido = ?, comentario = ?
        WHERE id_nomina_predicha = ?
        ''', (
            total_devengos,
            total_deducciones,
            liquido,
            "Editado manualmente",
            id_nomina_predicha
        ))
        
        self.conn.commit()
        
        return {
            'resultado': 'éxito',
            'id_nomina_predicha': id_nomina_predicha,
            'total_devengos': total_devengos,
            'total_deducciones': total_deducciones,
            'liquido': liquido
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del predictor
    predictor = PredictorNomina()
    
    # Ejemplo de configuración
    id_empleado = 1  # Ajustar según la base de datos
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    
    # Establecer configuración básica
    predictor.establecer_configuracion_prediccion(
        id_empleado=id_empleado,
        concepto='salario_base',
        valor=1800.0,
        fecha_inicio=fecha_actual,
        descripcion='Salario base configurado manualmente'
    )
    
    predictor.establecer_configuracion_prediccion(
        id_empleado=id_empleado,
        concepto='porcentaje_irpf',
        valor=16.0,
        fecha_inicio=fecha_actual,
        descripcion='Porcentaje IRPF configurado manualmente'
    )
    
    # Predecir nómina para el mes actual
    anio_actual = datetime.now().year
    mes_actual = datetime.now().month
    
    prediccion = predictor.predecir_nomina_mes(id_empleado, anio_actual, mes_actual)
    print(f"Predicción para {mes_actual}/{anio_actual}:")
    print(f"Total devengos: {prediccion['total_devengos']}")
    print(f"Total deducciones: {prediccion['total_deducciones']}")
    print(f"Líquido: {prediccion['liquido']}")
    
    # Obtener la nómina predicha
    nomina_predicha = predictor.obtener_nomina_predicha(prediccion['id_nomina_predicha'])
    print("\nConceptos de devengo:")
    for concepto in nomina_predicha['conceptos_devengo']:
        print(f"{concepto['concepto']}: {concepto['importe']}")
    
    print("\nConceptos de deducción:")
    for concepto in nomina_predicha['conceptos_deduccion']:
        print(f"{concepto['concepto']}: {concepto['importe']}")
    
    print("\nProceso completado.")
