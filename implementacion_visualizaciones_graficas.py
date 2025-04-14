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
  
(Content truncated due to size limit. Use line ranges to read in chunks)