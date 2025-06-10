"""
Módulo de Visualizaciones Gráficas

Este módulo implementa la funcionalidad para generar visualizaciones gráficas
de los datos procesados por los demás módulos del sistema.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as mtick

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class VisualizadorGraficas:
    """Clase para generar visualizaciones gráficas de los datos."""
    
    def __init__(self, db_path: str = DB_PATH, directorio_salida: str = '/home/ubuntu/workspace/graficas'):
        """Inicializa el visualizador de gráficas.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            directorio_salida: Directorio donde se guardarán las gráficas
        """
        self.db_path = db_path
        self.conn = None
        self.directorio_salida = directorio_salida
        self._conectar_bd()
        self._crear_directorio_salida()
        
        # Configurar estilo de las gráficas
        plt.style.use('ggplot')
        sns.set_style("whitegrid")
        
        # Paleta de colores personalizada
        self.paleta_colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    def _conectar_bd(self):
        """Conecta a la base de datos."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    
    def _crear_directorio_salida(self):
        """Crea el directorio de salida si no existe."""
        if not os.path.exists(self.directorio_salida):
            os.makedirs(self.directorio_salida)
    
    def generar_grafica_evolucion_nominas(self, id_empleado: int, 
                                         periodo_inicio: str = None, 
                                         periodo_fin: str = None) -> str:
        """Genera una gráfica de evolución de nóminas a lo largo del tiempo.
        
        Args:
            id_empleado: ID del empleado
            periodo_inicio: Fecha de inicio en formato 'DD/MM/YYYY' (opcional)
            periodo_fin: Fecha de fin en formato 'DD/MM/YYYY' (opcional)
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT periodo_fin, importe_bruto, importe_neto
        FROM Nominas
        WHERE id_empleado = ?
        '''
        params = [id_empleado]
        
        # Añadir filtros de periodo si se proporcionan
        if periodo_inicio:
            periodo_inicio_dt = datetime.strptime(periodo_inicio, '%d/%m/%Y')
            query += ' AND periodo_fin >= ?'
            params.append(periodo_inicio_dt.strftime('%Y-%m-%d'))
        
        if periodo_fin:
            periodo_fin_dt = datetime.strptime(periodo_fin, '%d/%m/%Y')
            query += ' AND periodo_fin <= ?'
            params.append(periodo_fin_dt.strftime('%Y-%m-%d'))
        
        # Ordenar por fecha
        query += ' ORDER BY periodo_fin'
        
        cursor.execute(query, params)
        
        # Preparar datos para la gráfica
        fechas = []
        importes_brutos = []
        importes_netos = []
        
        for row in cursor.fetchall():
            fecha = datetime.strptime(row['periodo_fin'], '%Y-%m-%d')
            fechas.append(fecha)
            importes_brutos.append(row['importe_bruto'])
            importes_netos.append(row['importe_neto'])
        
        if not fechas:
            return None
        
        # Crear gráfica
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(fechas, importes_brutos, marker='o', linestyle='-', color=self.paleta_colores[0], 
                linewidth=2, markersize=8, label='Importe Bruto')
        ax.plot(fechas, importes_netos, marker='s', linestyle='-', color=self.paleta_colores[1], 
                linewidth=2, markersize=8, label='Importe Neto')
        
        # Añadir etiquetas y título
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Importe (€)', fontsize=12)
        ax.set_title('Evolución de Nóminas', fontsize=16, fontweight='bold')
        
        # Formatear eje X para mostrar fechas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Formatear eje Y para mostrar euros
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir cuadrícula
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Añadir leyenda
        ax.legend(fontsize=10)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"evolucion_nominas_{id_empleado}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_comparacion_conceptos(self, id_nomina1: int, id_nomina2: int, 
                                             titulo: str = None) -> str:
        """Genera una gráfica de comparación de conceptos entre dos nóminas.
        
        Args:
            id_nomina1: ID de la primera nómina
            id_nomina2: ID de la segunda nómina
            titulo: Título personalizado para la gráfica (opcional)
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Obtener información de las nóminas
        cursor.execute('''
        SELECT id_nomina, periodo_inicio, periodo_fin
        FROM Nominas
        WHERE id_nomina IN (?, ?)
        ''', (id_nomina1, id_nomina2))
        
        info_nominas = {}
        for row in cursor.fetchall():
            periodo_fin = datetime.strptime(row['periodo_fin'], '%Y-%m-%d')
            info_nominas[row['id_nomina']] = periodo_fin.strftime('%m/%Y')
        
        # Obtener conceptos de ambas nóminas
        cursor.execute('''
        SELECT id_nomina, concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina IN (?, ?) AND es_devengo = 1
        ''', (id_nomina1, id_nomina2))
        
        # Organizar datos por nómina y concepto
        datos_nomina1 = {}
        datos_nomina2 = {}
        
        for row in cursor.fetchall():
            if row['id_nomina'] == id_nomina1:
                datos_nomina1[row['concepto']] = row['importe']
            else:
                datos_nomina2[row['concepto']] = row['importe']
        
        # Obtener todos los conceptos únicos
        todos_conceptos = sorted(set(list(datos_nomina1.keys()) + list(datos_nomina2.keys())))
        
        if not todos_conceptos:
            return None
        
        # Preparar datos para la gráfica
        importes_nomina1 = [datos_nomina1.get(concepto, 0) for concepto in todos_conceptos]
        importes_nomina2 = [datos_nomina2.get(concepto, 0) for concepto in todos_conceptos]
        
        # Crear gráfica de barras agrupadas
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Configurar posiciones de las barras
        x = np.arange(len(todos_conceptos))
        width = 0.35
        
        # Crear barras
        rects1 = ax.bar(x - width/2, importes_nomina1, width, label=f'Nómina {info_nominas.get(id_nomina1, "1")}', 
                        color=self.paleta_colores[0])
        rects2 = ax.bar(x + width/2, importes_nomina2, width, label=f'Nómina {info_nominas.get(id_nomina2, "2")}', 
                        color=self.paleta_colores[1])
        
        # Añadir etiquetas y título
        ax.set_xlabel('Conceptos', fontsize=12)
        ax.set_ylabel('Importe (€)', fontsize=12)
        
        if titulo:
            ax.set_title(titulo, fontsize=16, fontweight='bold')
        else:
            ax.set_title('Comparación de Conceptos entre Nóminas', fontsize=16, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(todos_conceptos, rotation=45, ha='right')
        
        # Formatear eje Y para mostrar euros
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir valores sobre las barras
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    ax.annotate(f'{height:.2f} €',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 puntos de desplazamiento vertical
                                textcoords="offset points",
                                ha='center', va='bottom', rotation=90, fontsize=8)
        
        autolabel(rects1)
        autolabel(rects2)
        
        # Añadir leyenda
        ax.legend(fontsize=10)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"comparacion_conceptos_{id_nomina1}_{id_nomina2}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_distribucion_nomina(self, id_nomina: int) -> str:
        """Genera una gráfica de distribución de conceptos de una nómina.
        
        Args:
            id_nomina: ID de la nómina
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Obtener información de la nómina
        cursor.execute('''
        SELECT periodo_fin, importe_bruto
        FROM Nominas
        WHERE id_nomina = ?
        ''', (id_nomina,))
        
        info_nomina = cursor.fetchone()
        if not info_nomina:
            return None
        
        periodo = datetime.strptime(info_nomina['periodo_fin'], '%Y-%m-%d').strftime('%m/%Y')
        
        # Obtener conceptos de devengo
        cursor.execute('''
        SELECT concepto, importe
        FROM ConceptosNomina
        WHERE id_nomina = ? AND es_devengo = 1
        ORDER BY importe DESC
        ''', (id_nomina,))
        
        conceptos = []
        importes = []
        
        for row in cursor.fetchall():
            conceptos.append(row['concepto'])
            importes.append(row['importe'])
        
        if not conceptos:
            return None
        
        # Crear gráfica de pastel
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Gráfica de pastel
        wedges, texts, autotexts = ax1.pie(
            importes, 
            autopct='%1.1f%%',
            textprops={'fontsize': 10},
            colors=self.paleta_colores[:len(importes)],
            startangle=90,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        
        # Añadir leyenda
        ax1.legend(
            wedges, 
            conceptos,
            title="Conceptos",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        
        ax1.set_title(f'Distribución de Conceptos - {periodo}', fontsize=16, fontweight='bold')
        
        # Gráfica de barras horizontales
        y_pos = np.arange(len(conceptos))
        ax2.barh(y_pos, importes, color=self.paleta_colores[:len(importes)])
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(conceptos)
        ax2.invert_yaxis()  # Invertir eje Y para que el mayor valor esté arriba
        ax2.set_xlabel('Importe (€)')
        ax2.set_title('Ranking de Conceptos por Importe', fontsize=16, fontweight='bold')
        
        # Formatear eje X para mostrar euros
        ax2.xaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir valores al final de cada barra
        for i, v in enumerate(importes):
            ax2.text(v + 0.1, i, f'{v:.2f} €', va='center')
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"distribucion_nomina_{id_nomina}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_evolucion_concepto(self, id_empleado: int, concepto: str,
                                          periodo_inicio: str = None,
                                          periodo_fin: str = None) -> str:
        """Genera una gráfica de evolución de un concepto específico a lo largo del tiempo.
        
        Args:
            id_empleado: ID del empleado
            concepto: Nombre del concepto a analizar
            periodo_inicio: Fecha de inicio en formato 'DD/MM/YYYY' (opcional)
            periodo_fin: Fecha de fin en formato 'DD/MM/YYYY' (opcional)
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        query = '''
        SELECT n.periodo_fin, c.importe
        FROM Nominas n
        JOIN ConceptosNomina c ON n.id_nomina = c.id_nomina
        WHERE n.id_empleado = ? AND c.concepto = ?
        '''
        params = [id_empleado, concepto]
        
        # Añadir filtros de periodo si se proporcionan
        if periodo_inicio:
            periodo_inicio_dt = datetime.strptime(periodo_inicio, '%d/%m/%Y')
            query += ' AND n.periodo_fin >= ?'
            params.append(periodo_inicio_dt.strftime('%Y-%m-%d'))
        
        if periodo_fin:
            periodo_fin_dt = datetime.strptime(periodo_fin, '%d/%m/%Y')
            query += ' AND n.periodo_fin <= ?'
            params.append(periodo_fin_dt.strftime('%Y-%m-%d'))
        
        # Ordenar por fecha
        query += ' ORDER BY n.periodo_fin'
        
        cursor.execute(query, params)
        
        # Preparar datos para la gráfica
        fechas = []
        importes = []
        
        for row in cursor.fetchall():
            fecha = datetime.strptime(row['periodo_fin'], '%Y-%m-%d')
            fechas.append(fecha)
            importes.append(row['importe'])
        
        if not fechas:
            return None
        
        # Crear gráfica
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(fechas, importes, marker='o', linestyle='-', color=self.paleta_colores[0], 
                linewidth=2, markersize=8)
        
        # Añadir etiquetas y título
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Importe (€)', fontsize=12)
        ax.set_title(f'Evolución del Concepto: {concepto}', fontsize=16, fontweight='bold')
        
        # Formatear eje X para mostrar fechas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Formatear eje Y para mostrar euros
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir valores sobre los puntos
        for i, (x, y) in enumerate(zip(fechas, importes)):
            ax.annotate(f'{y:.2f} €', 
                        (x, y), 
                        textcoords="offset points",
                        xytext=(0, 10), 
                        ha='center')
        
        # Añadir cuadrícula
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"evolucion_{concepto.replace(' ', '_')}_{id_empleado}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_comparacion_empleados(self, id_nomina: int, id_nomina_ref: int) -> str:
        """Genera una gráfica de comparación entre la nómina propia y una de referencia.
        
        Args:
            id_nomina: ID de la nómina propia
            id_nomina_ref: ID de la nómina de referencia
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Obtener información de la comparación
        cursor.execute('''
        SELECT c.id_comparacion
        FROM ComparacionesNominas c
        WHERE c.id_nomina = ? AND c.id_nomina_ref = ?
        ORDER BY c.fecha_comparacion DESC
        LIMIT 1
        ''', (id_nomina, id_nomina_ref))
        
        comparacion = cursor.fetchone()
        if not comparacion:
            # Si no existe una comparación, intentar crearla
            return None
        
        id_comparacion = comparacion['id_comparacion']
        
        # Obtener resultados de la comparación
        cursor.execute('''
        SELECT concepto, importe_nomina, importe_nomina_ref, diferencia, porcentaje_diferencia
        FROM ResultadosComparacion
        WHERE id_comparacion = ? AND es_devengo = 1
        ORDER BY ABS(porcentaje_diferencia) DESC
        LIMIT 10
        ''', (id_comparacion,))
        
        # Preparar datos para la gráfica
        conceptos = []
        importes_nomina = []
        importes_nomina_ref = []
        diferencias_porcentuales = []
        
        for row in cursor.fetchall():
            conceptos.append(row['concepto'])
            importes_nomina.append(row['importe_nomina'])
            importes_nomina_ref.append(row['importe_nomina_ref'])
            diferencias_porcentuales.append(row['porcentaje_diferencia'])
        
        if not conceptos:
            return None
        
        # Obtener información de las nóminas
        cursor.execute('''
        SELECT n.periodo_fin, e.nombre, e.es_anonimo, e.id_empleado_ref
        FROM NominasReferencia n
        JOIN EmpleadosReferencia e ON n.id_empleado_ref = e.id_empleado_ref
        WHERE n.id_nomina_ref = ?
        ''', (id_nomina_ref,))
        
        info_nomina_ref = cursor.fetchone()
        periodo_ref = datetime.strptime(info_nomina_ref['periodo_fin'], '%Y-%m-%d').strftime('%m/%Y')
        
        nombre_ref = info_nomina_ref['nombre']
        if info_nomina_ref['es_anonimo']:
            nombre_ref = f"Anónimo_{info_nomina_ref['id_empleado_ref']}"
        
        # Crear gráfica
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [2, 1]})
        
        # Gráfica de barras comparativas
        x = np.arange(len(conceptos))
        width = 0.35
        
        rects1 = ax1.bar(x - width/2, importes_nomina, width, label='Tu Nómina', color=self.paleta_colores[0])
        rects2 = ax1.bar(x + width/2, importes_nomina_ref, width, label=f'Nómina de {nombre_ref}', color=self.paleta_colores[1])
        
        ax1.set_ylabel('Importe (€)', fontsize=12)
        ax1.set_title(f'Comparación de Conceptos - Periodo {periodo_ref}', fontsize=16, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(conceptos, rotation=45, ha='right')
        ax1.legend()
        
        # Formatear eje Y para mostrar euros
        ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Gráfica de diferencias porcentuales
        colors = ['red' if x < 0 else 'green' for x in diferencias_porcentuales]
        ax2.bar(conceptos, diferencias_porcentuales, color=colors)
        ax2.set_ylabel('Diferencia (%)', fontsize=12)
        ax2.set_title('Diferencias Porcentuales', fontsize=16, fontweight='bold')
        ax2.set_xticklabels(conceptos, rotation=45, ha='right')
        
        # Añadir línea de referencia en 0%
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Formatear eje Y para mostrar porcentajes
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=1))
        
        # Añadir valores sobre las barras
        for i, v in enumerate(diferencias_porcentuales):
            ax2.text(i, v + (5 if v >= 0 else -5), f'{v:.1f}%', ha='center', va='center' if v >= 0 else 'top')
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"comparacion_empleados_{id_nomina}_{id_nomina_ref}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_calendario_laboral(self, id_empleado: int, anio: int, mes: int = None) -> str:
        """Genera una visualización del calendario laboral.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            mes: Mes específico (1-12) (opcional)
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Preparar consulta
        if mes:
            # Obtener días del mes específico
            query = '''
            SELECT c.fecha, c.horas_teoricas, t.codigo as tipo_codigo, t.nombre as tipo_nombre, 
                   t.color as tipo_color, tu.codigo as turno_codigo
            FROM CalendarioLaboral c
            LEFT JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
            LEFT JOIN Turnos tu ON c.id_turno = tu.id_turno
            WHERE c.id_empleado = ? AND strftime('%Y', c.fecha) = ? AND strftime('%m', c.fecha) = ?
            ORDER BY c.fecha
            '''
            params = [id_empleado, str(anio), str(mes).zfill(2)]
        else:
            # Obtener resumen anual
            query = '''
            SELECT t.codigo, t.nombre, t.color, COUNT(*) as dias
            FROM CalendarioLaboral c
            JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
            WHERE c.id_empleado = ? AND strftime('%Y', c.fecha) = ?
            GROUP BY t.id_tipo_dia
            ORDER BY dias DESC
            '''
            params = [id_empleado, str(anio)]
        
        cursor.execute(query, params)
        
        if mes:
            # Crear calendario mensual
            dias_mes = cursor.fetchall()
            
            if not dias_mes:
                return None
            
            # Determinar primer día del mes y número de días
            primer_dia = date(anio, mes, 1)
            if mes == 12:
                ultimo_dia = date(anio + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia = date(anio, mes + 1, 1) - timedelta(days=1)
            
            num_dias = ultimo_dia.day
            
            # Crear matriz para el calendario
            primer_dia_semana = primer_dia.weekday()  # 0 es lunes, 6 es domingo
            
            # Número de filas necesarias para el calendario
            num_filas = (num_dias + primer_dia_semana + 6) // 7
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Eliminar ejes
            ax.axis('off')
            
            # Título del calendario
            nombre_mes = calendar.month_name[mes]
            ax.set_title(f'Calendario Laboral - {nombre_mes} {anio}', fontsize=16, fontweight='bold')
            
            # Nombres de los días de la semana
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            # Dibujar cabecera con días de la semana
            for i, dia in enumerate(dias_semana):
                ax.text(i / 7 + 1/14, 0.95, dia, ha='center', va='center', fontweight='bold')
            
            # Dibujar calendario
            for fila in range(num_filas):
                for col in range(7):
                    idx = fila * 7 + col - primer_dia_semana + 1
                    
                    if 1 <= idx <= num_dias:
                        fecha = date(anio, mes, idx)
                        fecha_str = fecha.strftime('%Y-%m-%d')
                        
                        # Buscar información del día
                        info_dia = None
                        for dia in dias_mes:
                            if dia['fecha'] == fecha_str:
                                info_dia = dia
                                break
                        
                        # Color de fondo según tipo de día
                        if info_dia and info_dia['tipo_color']:
                            color = info_dia['tipo_color']
                        else:
                            color = '#FFFFFF'  # Blanco por defecto
                        
                        # Dibujar celda
                        rect = plt.Rectangle((col / 7, 0.9 - (fila + 1) / num_filas), 1/7, 1/num_filas, 
                                            fill=True, color=color, alpha=0.5, transform=ax.transAxes)
                        ax.add_patch(rect)
                        
                        # Añadir número de día
                        ax.text(col / 7 + 1/14, 0.9 - (fila + 1) / num_filas + 0.8/num_filas, 
                                str(idx), ha='center', va='center', fontweight='bold')
                        
                        # Añadir información adicional
                        if info_dia:
                            # Tipo de día
                            ax.text(col / 7 + 1/14, 0.9 - (fila + 1) / num_filas + 0.5/num_filas, 
                                    info_dia['tipo_codigo'], ha='center', va='center', fontsize=8)
                            
                            # Turno
                            if info_dia['turno_codigo']:
                                ax.text(col / 7 + 1/14, 0.9 - (fila + 1) / num_filas + 0.3/num_filas, 
                                        info_dia['turno_codigo'], ha='center', va='center', fontsize=8)
                            
                            # Horas
                            ax.text(col / 7 + 1/14, 0.9 - (fila + 1) / num_filas + 0.1/num_filas, 
                                    f"{info_dia['horas_teoricas']}h", ha='center', va='center', fontsize=8)
            
            # Añadir leyenda
            cursor.execute('''
            SELECT DISTINCT t.codigo, t.nombre, t.color
            FROM CalendarioLaboral c
            JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
            WHERE c.id_empleado = ? AND strftime('%Y-%m', c.fecha) = ?
            ''', [id_empleado, f"{anio}-{str(mes).zfill(2)}"])
            
            tipos_dia = cursor.fetchall()
            
            for i, tipo in enumerate(tipos_dia):
                rect = plt.Rectangle((0.05 + i * 0.15, 0.05), 0.02, 0.02, 
                                    fill=True, color=tipo['color'])
                ax.add_patch(rect)
                ax.text(0.08 + i * 0.15, 0.06, f"{tipo['codigo']}: {tipo['nombre']}", 
                        va='center', fontsize=8)
            
        else:
            # Crear gráfica de resumen anual
            datos_resumen = cursor.fetchall()
            
            if not datos_resumen:
                return None
            
            # Preparar datos para la gráfica
            tipos = []
            dias = []
            colores = []
            
            for row in datos_resumen:
                tipos.append(f"{row['codigo']}: {row['nombre']}")
                dias.append(row['dias'])
                colores.append(row['color'] if row['color'] else '#CCCCCC')
            
            # Crear gráfica
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
            
            # Gráfica de pastel
            wedges, texts, autotexts = ax1.pie(
                dias, 
                autopct='%1.1f%%',
                textprops={'fontsize': 10},
                colors=colores,
                startangle=90,
                wedgeprops={'edgecolor': 'w', 'linewidth': 1}
            )
            
            # Añadir leyenda
            ax1.legend(
                wedges, 
                tipos,
                title="Tipos de Día",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1)
            )
            
            ax1.set_title(f'Distribución de Días - {anio}', fontsize=16, fontweight='bold')
            
            # Gráfica de barras horizontales
            y_pos = np.arange(len(tipos))
            ax2.barh(y_pos, dias, color=colores)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(tipos)
            ax2.invert_yaxis()  # Invertir eje Y para que el mayor valor esté arriba
            ax2.set_xlabel('Número de Días')
            ax2.set_title('Días por Tipo', fontsize=16, fontweight='bold')
            
            # Añadir valores al final de cada barra
            for i, v in enumerate(dias):
                ax2.text(v + 0.1, i, str(v), va='center')
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        if mes:
            nombre_archivo = f"calendario_{id_empleado}_{anio}_{mes}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        else:
            nombre_archivo = f"calendario_resumen_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_prediccion_nomina(self, id_empleado: int, anio: int) -> str:
        """Genera una gráfica de predicción de nóminas para un año.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para la predicción
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Obtener predicciones mensuales
        cursor.execute('''
        SELECT mes, importe_bruto_predicho, importe_neto_predicho
        FROM PrediccionesNomina
        WHERE id_empleado = ? AND anio = ?
        ORDER BY mes
        ''', (id_empleado, anio))
        
        predicciones = cursor.fetchall()
        
        if not predicciones:
            return None
        
        # Preparar datos para la gráfica
        meses = []
        importes_brutos = []
        importes_netos = []
        
        for row in predicciones:
            meses.append(calendar.month_abbr[row['mes']])
            importes_brutos.append(row['importe_bruto_predicho'])
            importes_netos.append(row['importe_neto_predicho'])
        
        # Obtener nóminas reales para comparar
        cursor.execute('''
        SELECT strftime('%m', n.periodo_fin) as mes, n.importe_bruto, n.importe_neto
        FROM Nominas n
        WHERE n.id_empleado = ? AND strftime('%Y', n.periodo_fin) = ?
        ORDER BY n.periodo_fin
        ''', (id_empleado, str(anio)))
        
        nominas_reales = cursor.fetchall()
        
        # Preparar datos de nóminas reales
        meses_reales = []
        importes_brutos_reales = []
        importes_netos_reales = []
        
        for row in nominas_reales:
            mes_num = int(row['mes'])
            meses_reales.append(calendar.month_abbr[mes_num])
            importes_brutos_reales.append(row['importe_bruto'])
            importes_netos_reales.append(row['importe_neto'])
        
        # Crear gráfica
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [1, 1]})
        
        # Gráfica de importes brutos
        x = np.arange(len(meses))
        width = 0.35
        
        rects1 = ax1.bar(x - width/2, importes_brutos, width, label='Predicción', color=self.paleta_colores[0])
        
        if meses_reales:
            # Mapear meses reales a índices de meses predichos
            indices_reales = [meses.index(mes) for mes in meses_reales if mes in meses]
            valores_reales = [importes_brutos_reales[meses_reales.index(mes)] for mes in meses_reales if mes in meses]
            
            if indices_reales:
                rects2 = ax1.bar([x[i] + width/2 for i in indices_reales], valores_reales, width, 
                                label='Real', color=self.paleta_colores[1])
        
        ax1.set_ylabel('Importe Bruto (€)', fontsize=12)
        ax1.set_title(f'Predicción vs. Real - Importe Bruto {anio}', fontsize=16, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(meses)
        ax1.legend()
        
        # Formatear eje Y para mostrar euros
        ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Gráfica de importes netos
        rects3 = ax2.bar(x - width/2, importes_netos, width, label='Predicción', color=self.paleta_colores[2])
        
        if meses_reales:
            # Mapear meses reales a índices de meses predichos
            indices_reales = [meses.index(mes) for mes in meses_reales if mes in meses]
            valores_reales = [importes_netos_reales[meses_reales.index(mes)] for mes in meses_reales if mes in meses]
            
            if indices_reales:
                rects4 = ax2.bar([x[i] + width/2 for i in indices_reales], valores_reales, width, 
                                label='Real', color=self.paleta_colores[3])
        
        ax2.set_ylabel('Importe Neto (€)', fontsize=12)
        ax2.set_title(f'Predicción vs. Real - Importe Neto {anio}', fontsize=16, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(meses)
        ax2.legend()
        
        # Formatear eje Y para mostrar euros
        ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir valores sobre las barras
        def autolabel(rects, ax):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.2f} €',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 puntos de desplazamiento vertical
                            textcoords="offset points",
                            ha='center', va='bottom', rotation=90, fontsize=8)
        
        autolabel(rects1, ax1)
        autolabel(rects3, ax2)
        
        if meses_reales and indices_reales:
            if 'rects2' in locals():
                autolabel(rects2, ax1)
            if 'rects4' in locals():
                autolabel(rects4, ax2)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"prediccion_nomina_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_incrementos_salariales(self, id_empleado: int, 
                                              anio_inicio: int, anio_fin: int) -> str:
        """Genera una gráfica de incrementos salariales a lo largo del tiempo.
        
        Args:
            id_empleado: ID del empleado
            anio_inicio: Año de inicio
            anio_fin: Año de fin
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Obtener histórico de salarios
        cursor.execute('''
        SELECT fecha, concepto, valor_anterior, valor_nuevo, porcentaje_incremento, motivo
        FROM HistoricoSalarios
        WHERE id_empleado = ? AND concepto = 'Salario Base' 
              AND fecha BETWEEN ? AND ?
        ORDER BY fecha
        ''', (
            id_empleado, 
            f"{anio_inicio}-01-01", 
            f"{anio_fin}-12-31"
        ))
        
        historico = cursor.fetchall()
        
        if not historico:
            return None
        
        # Preparar datos para la gráfica
        fechas = []
        salarios = []
        incrementos = []
        motivos = []
        
        for row in historico:
            fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
            fechas.append(fecha)
            salarios.append(row['valor_nuevo'])
            incrementos.append(row['porcentaje_incremento'])
            motivos.append(row['motivo'])
        
        # Crear gráfica
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # Gráfica de evolución salarial
        ax1.plot(fechas, salarios, marker='o', linestyle='-', color=self.paleta_colores[0], 
                linewidth=2, markersize=8)
        
        # Añadir etiquetas y título
        ax1.set_xlabel('Fecha', fontsize=12)
        ax1.set_ylabel('Salario Base (€)', fontsize=12)
        ax1.set_title('Evolución del Salario Base', fontsize=16, fontweight='bold')
        
        # Formatear eje X para mostrar fechas
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
        
        # Formatear eje Y para mostrar euros
        ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir valores sobre los puntos
        for i, (x, y, m) in enumerate(zip(fechas, salarios, motivos)):
            ax1.annotate(f'{y:.2f} €\n{m}', 
                        (x, y), 
                        textcoords="offset points",
                        xytext=(0, 10), 
                        ha='center',
                        fontsize=8)
        
        # Gráfica de incrementos porcentuales
        ax2.bar(fechas, incrementos, color=self.paleta_colores[1])
        
        ax2.set_xlabel('Fecha', fontsize=12)
        ax2.set_ylabel('Incremento (%)', fontsize=12)
        ax2.set_title('Incrementos Porcentuales', fontsize=16, fontweight='bold')
        
        # Formatear eje X para mostrar fechas
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
        ax2.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Formatear eje Y para mostrar porcentajes
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
        
        # Añadir valores sobre las barras
        for i, (x, y) in enumerate(zip(fechas, incrementos)):
            ax2.annotate(f'{y:.1f}%', 
                        (x, y), 
                        textcoords="offset points",
                        xytext=(0, 5), 
                        ha='center')
        
        # Añadir cuadrícula
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"incrementos_salariales_{id_empleado}_{anio_inicio}_{anio_fin}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_grafica_pagas_extras(self, id_empleado: int, anio: int) -> str:
        """Genera una gráfica de pagas extras para un año específico.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para las pagas extras
            
        Returns:
            Ruta al archivo de la gráfica generada
        """
        cursor = self.conn.cursor()
        
        # Obtener pagas extras
        cursor.execute('''
        SELECT p.id_paga_empleado, p.fecha_pago, p.importe_bruto, p.importe_neto, 
               p.porcentaje_irpf, p.importe_irpf, p.porcentaje_ss, p.importe_ss, 
               p.otros_descuentos, p.es_pagada,
               t.codigo, t.nombre
        FROM PagasExtrasEmpleados p
        JOIN TiposPagaExtra t ON p.id_tipo_paga = t.id_tipo_paga
        WHERE p.id_empleado = ? AND p.anio = ?
        ORDER BY p.fecha_pago
        ''', (id_empleado, anio))
        
        pagas = cursor.fetchall()
        
        if not pagas:
            return None
        
        # Preparar datos para la gráfica
        nombres = []
        importes_brutos = []
        importes_netos = []
        retenciones = []
        
        for row in pagas:
            nombres.append(row['codigo'])
            importes_brutos.append(row['importe_bruto'])
            importes_netos.append(row['importe_neto'])
            retenciones.append(row['importe_irpf'] + row['importe_ss'] + row['otros_descuentos'])
        
        # Crear gráfica
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Gráfica de barras apiladas
        width = 0.35
        x = np.arange(len(nombres))
        
        ax1.bar(x, importes_netos, width, label='Neto', color=self.paleta_colores[0])
        ax1.bar(x, retenciones, width, bottom=importes_netos, label='Retenciones', color=self.paleta_colores[1])
        
        ax1.set_ylabel('Importe (€)', fontsize=12)
        ax1.set_title(f'Pagas Extras {anio}', fontsize=16, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(nombres)
        ax1.legend()
        
        # Formatear eje Y para mostrar euros
        ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
        
        # Añadir valores sobre las barras
        for i, (bruto, neto) in enumerate(zip(importes_brutos, importes_netos)):
            ax1.annotate(f'Bruto: {bruto:.2f} €', 
                        (i, importes_netos[i] + retenciones[i]), 
                        textcoords="offset points",
                        xytext=(0, 5), 
                        ha='center')
            
            ax1.annotate(f'Neto: {neto:.2f} €', 
                        (i, importes_netos[i] / 2), 
                        textcoords="offset points",
                        xytext=(0, 0), 
                        ha='center')
        
        # Gráfica de pastel para distribución
        ax2.pie(
            importes_brutos, 
            labels=nombres,
            autopct='%1.1f%%',
            startangle=90,
            colors=self.paleta_colores[:len(nombres)],
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        
        ax2.set_title('Distribución de Pagas Extras', fontsize=16, fontweight='bold')
        
        # Ajustar diseño
        plt.tight_layout()
        
        # Guardar gráfica
        nombre_archivo = f"pagas_extras_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo
    
    def generar_dashboard_completo(self, id_empleado: int, anio: int) -> str:
        """Genera un dashboard completo con múltiples gráficas.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para el dashboard
            
        Returns:
            Ruta al archivo del dashboard generado
        """
        # Crear figura grande para el dashboard
        fig = plt.figure(figsize=(20, 16))
        
        # Definir grid para las gráficas
        gs = fig.add_gridspec(3, 3)
        
        # Añadir título general
        fig.suptitle(f'Dashboard Completo - Año {anio}', fontsize=20, fontweight='bold')
        
        # Obtener datos para las gráficas
        cursor = self.conn.cursor()
        
        # 1. Evolución de nóminas
        ax1 = fig.add_subplot(gs[0, :])
        
        cursor.execute('''
        SELECT periodo_fin, importe_bruto, importe_neto
        FROM Nominas
        WHERE id_empleado = ? AND strftime('%Y', periodo_fin) = ?
        ORDER BY periodo_fin
        ''', (id_empleado, str(anio)))
        
        nominas = cursor.fetchall()
        
        if nominas:
            fechas = [datetime.strptime(row['periodo_fin'], '%Y-%m-%d') for row in nominas]
            importes_brutos = [row['importe_bruto'] for row in nominas]
            importes_netos = [row['importe_neto'] for row in nominas]
            
            ax1.plot(fechas, importes_brutos, marker='o', linestyle='-', color=self.paleta_colores[0], 
                    linewidth=2, markersize=8, label='Importe Bruto')
            ax1.plot(fechas, importes_netos, marker='s', linestyle='-', color=self.paleta_colores[1], 
                    linewidth=2, markersize=8, label='Importe Neto')
            
            ax1.set_title('Evolución de Nóminas', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Fecha')
            ax1.set_ylabel('Importe (€)')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
            ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
            ax1.legend()
            ax1.grid(True, linestyle='--', alpha=0.7)
        else:
            ax1.text(0.5, 0.5, 'No hay datos de nóminas para este año', 
                    ha='center', va='center', fontsize=12)
            ax1.set_title('Evolución de Nóminas', fontsize=14, fontweight='bold')
        
        # 2. Distribución de conceptos (última nómina)
        ax2 = fig.add_subplot(gs[1, 0])
        
        cursor.execute('''
        SELECT n.id_nomina, n.periodo_fin
        FROM Nominas n
        WHERE n.id_empleado = ? AND strftime('%Y', n.periodo_fin) = ?
        ORDER BY n.periodo_fin DESC
        LIMIT 1
        ''', (id_empleado, str(anio)))
        
        ultima_nomina = cursor.fetchone()
        
        if ultima_nomina:
            id_nomina = ultima_nomina['id_nomina']
            periodo = datetime.strptime(ultima_nomina['periodo_fin'], '%Y-%m-%d').strftime('%m/%Y')
            
            cursor.execute('''
            SELECT concepto, importe
            FROM ConceptosNomina
            WHERE id_nomina = ? AND es_devengo = 1
            ORDER BY importe DESC
            ''', (id_nomina,))
            
            conceptos = cursor.fetchall()
            
            if conceptos:
                labels = [row['concepto'] for row in conceptos]
                sizes = [row['importe'] for row in conceptos]
                
                ax2.pie(
                    sizes, 
                    labels=labels if len(labels) <= 5 else None,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=self.paleta_colores[:len(sizes)],
                    wedgeprops={'edgecolor': 'w', 'linewidth': 1}
                )
                
                if len(labels) > 5:
                    ax2.legend(labels, title="Conceptos", loc="center left", 
                              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
                
                ax2.set_title(f'Distribución de Conceptos\n{periodo}', fontsize=14, fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'No hay conceptos para la última nómina', 
                        ha='center', va='center', fontsize=12)
                ax2.set_title('Distribución de Conceptos', fontsize=14, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'No hay nóminas para este año', 
                    ha='center', va='center', fontsize=12)
            ax2.set_title('Distribución de Conceptos', fontsize=14, fontweight='bold')
        
        # 3. Calendario laboral (resumen)
        ax3 = fig.add_subplot(gs[1, 1])
        
        cursor.execute('''
        SELECT t.codigo, t.nombre, t.color, COUNT(*) as dias
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND strftime('%Y', c.fecha) = ?
        GROUP BY t.id_tipo_dia
        ORDER BY dias DESC
        ''', (id_empleado, str(anio)))
        
        datos_calendario = cursor.fetchall()
        
        if datos_calendario:
            labels = [f"{row['codigo']}: {row['nombre']}" for row in datos_calendario]
            sizes = [row['dias'] for row in datos_calendario]
            colors = [row['color'] if row['color'] else '#CCCCCC' for row in datos_calendario]
            
            ax3.pie(
                sizes, 
                labels=labels if len(labels) <= 5 else None,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                wedgeprops={'edgecolor': 'w', 'linewidth': 1}
            )
            
            if len(labels) > 5:
                ax3.legend(labels, title="Tipos de Día", loc="center left", 
                          bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
            
            ax3.set_title(f'Distribución de Días - {anio}', fontsize=14, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'No hay datos de calendario para este año', 
                    ha='center', va='center', fontsize=12)
            ax3.set_title('Distribución de Días', fontsize=14, fontweight='bold')
        
        # 4. Pagas extras
        ax4 = fig.add_subplot(gs[1, 2])
        
        cursor.execute('''
        SELECT p.fecha_pago, p.importe_bruto, p.importe_neto, 
               t.codigo, t.nombre
        FROM PagasExtrasEmpleados p
        JOIN TiposPagaExtra t ON p.id_tipo_paga = t.id_tipo_paga
        WHERE p.id_empleado = ? AND p.anio = ?
        ORDER BY p.fecha_pago
        ''', (id_empleado, anio))
        
        pagas = cursor.fetchall()
        
        if pagas:
            nombres = [row['codigo'] for row in pagas]
            importes_brutos = [row['importe_bruto'] for row in pagas]
            importes_netos = [row['importe_neto'] for row in pagas]
            
            x = np.arange(len(nombres))
            width = 0.35
            
            ax4.bar(x - width/2, importes_brutos, width, label='Bruto', color=self.paleta_colores[0])
            ax4.bar(x + width/2, importes_netos, width, label='Neto', color=self.paleta_colores[1])
            
            ax4.set_title(f'Pagas Extras - {anio}', fontsize=14, fontweight='bold')
            ax4.set_xticks(x)
            ax4.set_xticklabels(nombres)
            ax4.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
            ax4.legend()
        else:
            ax4.text(0.5, 0.5, 'No hay datos de pagas extras para este año', 
                    ha='center', va='center', fontsize=12)
            ax4.set_title('Pagas Extras', fontsize=14, fontweight='bold')
        
        # 5. Predicción vs. Real
        ax5 = fig.add_subplot(gs[2, :2])
        
        # Obtener predicciones
        cursor.execute('''
        SELECT mes, importe_bruto_predicho
        FROM PrediccionesNomina
        WHERE id_empleado = ? AND anio = ?
        ORDER BY mes
        ''', (id_empleado, anio))
        
        predicciones = cursor.fetchall()
        
        # Obtener nóminas reales
        cursor.execute('''
        SELECT strftime('%m', n.periodo_fin) as mes, n.importe_bruto
        FROM Nominas n
        WHERE n.id_empleado = ? AND strftime('%Y', n.periodo_fin) = ?
        ORDER BY n.periodo_fin
        ''', (id_empleado, str(anio)))
        
        nominas_reales = cursor.fetchall()
        
        if predicciones:
            meses = [calendar.month_abbr[row['mes']] for row in predicciones]
            importes_predichos = [row['importe_bruto_predicho'] for row in predicciones]
            
            x = np.arange(len(meses))
            width = 0.35
            
            ax5.bar(x - width/2, importes_predichos, width, label='Predicción', color=self.paleta_colores[0])
            
            if nominas_reales:
                # Mapear meses reales a índices de meses predichos
                meses_reales = [calendar.month_abbr[int(row['mes'])] for row in nominas_reales]
                importes_reales = [row['importe_bruto'] for row in nominas_reales]
                
                indices_reales = [meses.index(mes) for mes in meses_reales if mes in meses]
                valores_reales = [importes_reales[meses_reales.index(mes)] for mes in meses_reales if mes in meses]
                
                if indices_reales:
                    ax5.bar([x[i] + width/2 for i in indices_reales], valores_reales, width, 
                           label='Real', color=self.paleta_colores[1])
            
            ax5.set_title(f'Predicción vs. Real - {anio}', fontsize=14, fontweight='bold')
            ax5.set_xticks(x)
            ax5.set_xticklabels(meses)
            ax5.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
            ax5.legend()
        else:
            ax5.text(0.5, 0.5, 'No hay datos de predicción para este año', 
                    ha='center', va='center', fontsize=12)
            ax5.set_title('Predicción vs. Real', fontsize=14, fontweight='bold')
        
        # 6. Incrementos salariales
        ax6 = fig.add_subplot(gs[2, 2])
        
        cursor.execute('''
        SELECT fecha, valor_nuevo, porcentaje_incremento
        FROM HistoricoSalarios
        WHERE id_empleado = ? AND concepto = 'Salario Base' 
              AND strftime('%Y', fecha) = ?
        ORDER BY fecha
        ''', (id_empleado, str(anio)))
        
        incrementos = cursor.fetchall()
        
        if incrementos:
            fechas = [datetime.strptime(row['fecha'], '%Y-%m-%d') for row in incrementos]
            valores = [row['valor_nuevo'] for row in incrementos]
            porcentajes = [row['porcentaje_incremento'] for row in incrementos]
            
            # Crear dos ejes Y
            ax6b = ax6.twinx()
            
            # Gráfica de salario
            ax6.plot(fechas, valores, marker='o', linestyle='-', color=self.paleta_colores[0], 
                    linewidth=2, markersize=8, label='Salario')
            
            # Gráfica de porcentaje
            ax6b.bar(fechas, porcentajes, alpha=0.3, color=self.paleta_colores[1], label='% Incremento')
            
            ax6.set_title(f'Incrementos Salariales - {anio}', fontsize=14, fontweight='bold')
            ax6.set_xlabel('Fecha')
            ax6.set_ylabel('Salario (€)', color=self.paleta_colores[0])
            ax6b.set_ylabel('Incremento (%)', color=self.paleta_colores[1])
            
            ax6.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
            plt.setp(ax6.get_xticklabels(), rotation=45, ha='right')
            
            ax6.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.2f} €'))
            ax6b.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
            
            # Leyendas
            lines1, labels1 = ax6.get_legend_handles_labels()
            lines2, labels2 = ax6b.get_legend_handles_labels()
            ax6.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            ax6.text(0.5, 0.5, 'No hay datos de incrementos para este año', 
                    ha='center', va='center', fontsize=12)
            ax6.set_title('Incrementos Salariales', fontsize=14, fontweight='bold')
        
        # Ajustar diseño
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Dejar espacio para el título general
        
        # Guardar dashboard
        nombre_archivo = f"dashboard_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        return ruta_archivo


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del visualizador
    visualizador = VisualizadorGraficas()
    
    # Generar algunas gráficas de ejemplo
    id_empleado = 1  # Ajustar según la base de datos
    anio_actual = datetime.now().year
    
    # Dashboard completo
    ruta_dashboard = visualizador.generar_dashboard_completo(id_empleado, anio_actual)
    print(f"Dashboard generado: {ruta_dashboard}")
    
    print("\nProceso completado.")
