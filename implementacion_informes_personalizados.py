"""
Módulo de Generación de Informes Personalizados

Este módulo implementa la funcionalidad para generar informes personalizados
sobre comparaciones y desviaciones en nóminas, saldos y tiempos.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union
import os
import re
import json
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import shutil

# Configuración de la base de datos
DB_PATH = 'nominas_comparador.db'

class GeneradorInformes:
    """Clase para generar informes personalizados."""
    
    def __init__(self, db_path: str = DB_PATH, directorio_salida: str = '/home/ubuntu/workspace/informes'):
        """Inicializa el generador de informes.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            directorio_salida: Directorio donde se guardarán los informes
        """
        self.db_path = db_path
        self.conn = None
        self.directorio_salida = directorio_salida
        self._conectar_bd()
        self._crear_directorio_salida()
    
    def _conectar_bd(self):
        """Conecta a la base de datos."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    
    def _crear_directorio_salida(self):
        """Crea el directorio de salida si no existe."""
        if not os.path.exists(self.directorio_salida):
            os.makedirs(self.directorio_salida)
    
    def generar_informe_nomina(self, id_nomina: int, incluir_graficas: bool = True) -> str:
        """Genera un informe detallado de una nómina.
        
        Args:
            id_nomina: ID de la nómina
            incluir_graficas: Si se deben incluir gráficas en el informe
            
        Returns:
            Ruta al archivo del informe generado
        """
        cursor = self.conn.cursor()
        
        # Obtener información de la nómina
        cursor.execute('''
        SELECT n.id_nomina, n.id_empleado, n.periodo_inicio, n.periodo_fin, 
               n.fecha_pago, n.importe_bruto, n.importe_neto, n.comentario,
               e.nombre as nombre_empleado, e.apellidos as apellidos_empleado,
               e.nif, e.categoria
        FROM Nominas n
        JOIN Empleados e ON n.id_empleado = e.id_empleado
        WHERE n.id_nomina = ?
        ''', (id_nomina,))
        
        nomina = cursor.fetchone()
        if not nomina:
            return None
        
        # Obtener conceptos de la nómina
        cursor.execute('''
        SELECT concepto, importe, es_devengo, es_plus, es_retencion
        FROM ConceptosNomina
        WHERE id_nomina = ?
        ORDER BY es_devengo DESC, es_retencion, concepto
        ''', (id_nomina,))
        
        conceptos = cursor.fetchall()
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'INFORME DE NÓMINA', 0, 1, 'C')
        
        # Información del empleado
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Datos del Empleado:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, 'Nombre:', 0, 0)
        pdf.cell(0, 7, f"{nomina['nombre_empleado']} {nomina['apellidos_empleado']}", 0, 1)
        
        pdf.cell(40, 7, 'NIF:', 0, 0)
        pdf.cell(0, 7, nomina['nif'], 0, 1)
        
        pdf.cell(40, 7, 'Categoría:', 0, 0)
        pdf.cell(0, 7, nomina['categoria'], 0, 1)
        
        # Información de la nómina
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Datos de la Nómina:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        
        periodo_inicio = datetime.strptime(nomina['periodo_inicio'], '%Y-%m-%d')
        periodo_fin = datetime.strptime(nomina['periodo_fin'], '%Y-%m-%d')
        fecha_pago = datetime.strptime(nomina['fecha_pago'], '%Y-%m-%d')
        
        pdf.cell(40, 7, 'Periodo:', 0, 0)
        pdf.cell(0, 7, f"Del {periodo_inicio.strftime('%d/%m/%Y')} al {periodo_fin.strftime('%d/%m/%Y')}", 0, 1)
        
        pdf.cell(40, 7, 'Fecha de pago:', 0, 0)
        pdf.cell(0, 7, fecha_pago.strftime('%d/%m/%Y'), 0, 1)
        
        pdf.cell(40, 7, 'Importe bruto:', 0, 0)
        pdf.cell(0, 7, f"{nomina['importe_bruto']:.2f} €", 0, 1)
        
        pdf.cell(40, 7, 'Importe neto:', 0, 0)
        pdf.cell(0, 7, f"{nomina['importe_neto']:.2f} €", 0, 1)
        
        # Conceptos de la nómina
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Conceptos:', 0, 1)
        
        # Tabla de devengos
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(100, 7, 'DEVENGOS', 0, 0)
        pdf.cell(0, 7, 'IMPORTE', 0, 1, 'R')
        
        pdf.set_font('Arial', '', 10)
        total_devengos = 0
        
        for concepto in conceptos:
            if concepto['es_devengo']:
                pdf.cell(100, 7, concepto['concepto'], 0, 0)
                pdf.cell(0, 7, f"{concepto['importe']:.2f} €", 0, 1, 'R')
                total_devengos += concepto['importe']
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(100, 7, 'Total Devengos:', 0, 0)
        pdf.cell(0, 7, f"{total_devengos:.2f} €", 0, 1, 'R')
        
        # Tabla de retenciones
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(100, 7, 'RETENCIONES', 0, 0)
        pdf.cell(0, 7, 'IMPORTE', 0, 1, 'R')
        
        pdf.set_font('Arial', '', 10)
        total_retenciones = 0
        
        for concepto in conceptos:
            if concepto['es_retencion']:
                pdf.cell(100, 7, concepto['concepto'], 0, 0)
                pdf.cell(0, 7, f"{concepto['importe']:.2f} €", 0, 1, 'R')
                total_retenciones += concepto['importe']
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(100, 7, 'Total Retenciones:', 0, 0)
        pdf.cell(0, 7, f"{total_retenciones:.2f} €", 0, 1, 'R')
        
        # Total líquido
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, 'TOTAL LÍQUIDO:', 0, 0)
        pdf.cell(0, 10, f"{nomina['importe_neto']:.2f} €", 0, 1, 'R')
        
        # Incluir gráficas si se solicita
        if incluir_graficas:
            # Crear gráfica de distribución de conceptos
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Preparar datos para la gráfica
                devengos = [c for c in conceptos if c['es_devengo']]
                labels = [c['concepto'] for c in devengos]
                sizes = [c['importe'] for c in devengos]
                
                # Crear gráfica de pastel
                plt.figure(figsize=(8, 6))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                plt.axis('equal')
                plt.title('Distribución de Conceptos')
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'distribucion_conceptos.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir nueva página para la gráfica
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Gráficas de la Nómina', 0, 1, 'C')
                
                # Añadir gráfica al PDF
                pdf.image(grafica_path, x=10, y=30, w=190)
                
            finally:
                # Limpiar archivos temporales
                shutil.rmtree(temp_dir)
        
        # Guardar PDF
        nombre_archivo = f"informe_nomina_{id_nomina}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        pdf.output(ruta_archivo)
        
        return ruta_archivo
    
    def generar_informe_comparacion_nominas(self, id_nomina1: int, id_nomina2: int, 
                                           incluir_graficas: bool = True) -> str:
        """Genera un informe de comparación entre dos nóminas.
        
        Args:
            id_nomina1: ID de la primera nómina
            id_nomina2: ID de la segunda nómina
            incluir_graficas: Si se deben incluir gráficas en el informe
            
        Returns:
            Ruta al archivo del informe generado
        """
        cursor = self.conn.cursor()
        
        # Obtener información de las nóminas
        cursor.execute('''
        SELECT n.id_nomina, n.id_empleado, n.periodo_inicio, n.periodo_fin, 
               n.importe_bruto, n.importe_neto,
               e.nombre as nombre_empleado
        FROM Nominas n
        JOIN Empleados e ON n.id_empleado = e.id_empleado
        WHERE n.id_nomina IN (?, ?)
        ''', (id_nomina1, id_nomina2))
        
        nominas = {}
        for row in cursor.fetchall():
            nominas[row['id_nomina']] = {
                'id_empleado': row['id_empleado'],
                'nombre_empleado': row['nombre_empleado'],
                'periodo_inicio': datetime.strptime(row['periodo_inicio'], '%Y-%m-%d'),
                'periodo_fin': datetime.strptime(row['periodo_fin'], '%Y-%m-%d'),
                'importe_bruto': row['importe_bruto'],
                'importe_neto': row['importe_neto']
            }
        
        if id_nomina1 not in nominas or id_nomina2 not in nominas:
            return None
        
        # Obtener conceptos de ambas nóminas
        cursor.execute('''
        SELECT id_nomina, concepto, importe, es_devengo, es_retencion
        FROM ConceptosNomina
        WHERE id_nomina IN (?, ?)
        ''', (id_nomina1, id_nomina2))
        
        conceptos_nomina1 = {}
        conceptos_nomina2 = {}
        
        for row in cursor.fetchall():
            if row['id_nomina'] == id_nomina1:
                conceptos_nomina1[row['concepto']] = {
                    'importe': row['importe'],
                    'es_devengo': row['es_devengo'],
                    'es_retencion': row['es_retencion']
                }
            else:
                conceptos_nomina2[row['concepto']] = {
                    'importe': row['importe'],
                    'es_devengo': row['es_devengo'],
                    'es_retencion': row['es_retencion']
                }
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'INFORME DE COMPARACIÓN DE NÓMINAS', 0, 1, 'C')
        
        # Información de las nóminas
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Nóminas Comparadas:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        
        # Nómina 1
        pdf.cell(40, 7, 'Nómina 1:', 0, 0)
        pdf.cell(0, 7, f"Empleado: {nominas[id_nomina1]['nombre_empleado']}", 0, 1)
        
        pdf.cell(40, 7, 'Periodo:', 0, 0)
        pdf.cell(0, 7, f"Del {nominas[id_nomina1]['periodo_inicio'].strftime('%d/%m/%Y')} al {nominas[id_nomina1]['periodo_fin'].strftime('%d/%m/%Y')}", 0, 1)
        
        pdf.cell(40, 7, 'Importe bruto:', 0, 0)
        pdf.cell(0, 7, f"{nominas[id_nomina1]['importe_bruto']:.2f} €", 0, 1)
        
        pdf.cell(40, 7, 'Importe neto:', 0, 0)
        pdf.cell(0, 7, f"{nominas[id_nomina1]['importe_neto']:.2f} €", 0, 1)
        
        pdf.ln(5)
        
        # Nómina 2
        pdf.cell(40, 7, 'Nómina 2:', 0, 0)
        pdf.cell(0, 7, f"Empleado: {nominas[id_nomina2]['nombre_empleado']}", 0, 1)
        
        pdf.cell(40, 7, 'Periodo:', 0, 0)
        pdf.cell(0, 7, f"Del {nominas[id_nomina2]['periodo_inicio'].strftime('%d/%m/%Y')} al {nominas[id_nomina2]['periodo_fin'].strftime('%d/%m/%Y')}", 0, 1)
        
        pdf.cell(40, 7, 'Importe bruto:', 0, 0)
        pdf.cell(0, 7, f"{nominas[id_nomina2]['importe_bruto']:.2f} €", 0, 1)
        
        pdf.cell(40, 7, 'Importe neto:', 0, 0)
        pdf.cell(0, 7, f"{nominas[id_nomina2]['importe_neto']:.2f} €", 0, 1)
        
        # Comparación de conceptos
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Comparación de Conceptos:', 0, 1)
        
        # Tabla de comparación
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 7, 'CONCEPTO', 1, 0, 'C')
        pdf.cell(40, 7, 'NÓMINA 1', 1, 0, 'C')
        pdf.cell(40, 7, 'NÓMINA 2', 1, 0, 'C')
        pdf.cell(50, 7, 'DIFERENCIA', 1, 1, 'C')
        
        # Todos los conceptos únicos
        todos_conceptos = sorted(set(list(conceptos_nomina1.keys()) + list(conceptos_nomina2.keys())))
        
        # Filtrar primero los devengos
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, 'DEVENGOS', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        for concepto in todos_conceptos:
            # Verificar si es devengo en alguna de las nóminas
            es_devengo1 = concepto in conceptos_nomina1 and conceptos_nomina1[concepto]['es_devengo']
            es_devengo2 = concepto in conceptos_nomina2 and conceptos_nomina2[concepto]['es_devengo']
            
            if not (es_devengo1 or es_devengo2):
                continue
            
            importe1 = conceptos_nomina1.get(concepto, {}).get('importe', 0)
            importe2 = conceptos_nomina2.get(concepto, {}).get('importe', 0)
            diferencia = importe1 - importe2
            
            pdf.cell(60, 7, concepto, 1, 0)
            pdf.cell(40, 7, f"{importe1:.2f} €", 1, 0, 'R')
            pdf.cell(40, 7, f"{importe2:.2f} €", 1, 0, 'R')
            
            # Colorear diferencias
            if diferencia > 0:
                pdf.set_text_color(0, 128, 0)  # Verde para positivo
            elif diferencia < 0:
                pdf.set_text_color(255, 0, 0)  # Rojo para negativo
            
            pdf.cell(50, 7, f"{diferencia:.2f} €", 1, 1, 'R')
            pdf.set_text_color(0, 0, 0)  # Restaurar color
        
        # Luego las retenciones
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, 'RETENCIONES', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        for concepto in todos_conceptos:
            # Verificar si es retención en alguna de las nóminas
            es_retencion1 = concepto in conceptos_nomina1 and conceptos_nomina1[concepto]['es_retencion']
            es_retencion2 = concepto in conceptos_nomina2 and conceptos_nomina2[concepto]['es_retencion']
            
            if not (es_retencion1 or es_retencion2):
                continue
            
            importe1 = conceptos_nomina1.get(concepto, {}).get('importe', 0)
            importe2 = conceptos_nomina2.get(concepto, {}).get('importe', 0)
            diferencia = importe1 - importe2
            
            pdf.cell(60, 7, concepto, 1, 0)
            pdf.cell(40, 7, f"{importe1:.2f} €", 1, 0, 'R')
            pdf.cell(40, 7, f"{importe2:.2f} €", 1, 0, 'R')
            
            # Para retenciones, invertir colores (menos es mejor)
            if diferencia > 0:
                pdf.set_text_color(255, 0, 0)  # Rojo para positivo (más retención)
            elif diferencia < 0:
                pdf.set_text_color(0, 128, 0)  # Verde para negativo (menos retención)
            
            pdf.cell(50, 7, f"{diferencia:.2f} €", 1, 1, 'R')
            pdf.set_text_color(0, 0, 0)  # Restaurar color
        
        # Resumen de diferencias
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Resumen de Diferencias:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        
        # Diferencia en bruto
        diferencia_bruto = nominas[id_nomina1]['importe_bruto'] - nominas[id_nomina2]['importe_bruto']
        pdf.cell(60, 7, 'Diferencia en Bruto:', 0, 0)
        
        if diferencia_bruto > 0:
            pdf.set_text_color(0, 128, 0)
        elif diferencia_bruto < 0:
            pdf.set_text_color(255, 0, 0)
        
        pdf.cell(0, 7, f"{diferencia_bruto:.2f} €", 0, 1)
        pdf.set_text_color(0, 0, 0)
        
        # Diferencia en neto
        diferencia_neto = nominas[id_nomina1]['importe_neto'] - nominas[id_nomina2]['importe_neto']
        pdf.cell(60, 7, 'Diferencia en Neto:', 0, 0)
        
        if diferencia_neto > 0:
            pdf.set_text_color(0, 128, 0)
        elif diferencia_neto < 0:
            pdf.set_text_color(255, 0, 0)
        
        pdf.cell(0, 7, f"{diferencia_neto:.2f} €", 0, 1)
        pdf.set_text_color(0, 0, 0)
        
        # Incluir gráficas si se solicita
        if incluir_graficas:
            # Crear gráficas de comparación
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Gráfica de barras comparativas
                conceptos_comunes = [c for c in todos_conceptos if c in conceptos_nomina1 and c in conceptos_nomina2]
                importes1 = [conceptos_nomina1[c]['importe'] for c in conceptos_comunes]
                importes2 = [conceptos_nomina2[c]['importe'] for c in conceptos_comunes]
                
                # Limitar a los 10 conceptos con mayor diferencia
                diferencias = [abs(i1 - i2) for i1, i2 in zip(importes1, importes2)]
                indices_ordenados = sorted(range(len(diferencias)), key=lambda i: diferencias[i], reverse=True)
                
                if len(indices_ordenados) > 10:
                    indices_ordenados = indices_ordenados[:10]
                
                conceptos_seleccionados = [conceptos_comunes[i] for i in indices_ordenados]
                importes1_seleccionados = [importes1[i] for i in indices_ordenados]
                importes2_seleccionados = [importes2[i] for i in indices_ordenados]
                
                # Crear gráfica
                plt.figure(figsize=(10, 6))
                
                x = np.arange(len(conceptos_seleccionados))
                width = 0.35
                
                plt.bar(x - width/2, importes1_seleccionados, width, label='Nómina 1')
                plt.bar(x + width/2, importes2_seleccionados, width, label='Nómina 2')
                
                plt.xlabel('Conceptos')
                plt.ylabel('Importe (€)')
                plt.title('Comparación de Conceptos')
                plt.xticks(x, conceptos_seleccionados, rotation=45, ha='right')
                plt.legend()
                plt.tight_layout()
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'comparacion_conceptos.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir nueva página para la gráfica
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Gráficas de Comparación', 0, 1, 'C')
                
                # Añadir gráfica al PDF
                pdf.image(grafica_path, x=10, y=30, w=190)
                
            finally:
                # Limpiar archivos temporales
                shutil.rmtree(temp_dir)
        
        # Guardar PDF
        nombre_archivo = f"informe_comparacion_{id_nomina1}_{id_nomina2}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        pdf.output(ruta_archivo)
        
        return ruta_archivo
    
    def generar_informe_desviaciones(self, id_empleado: int, anio: int, 
                                    umbral_desviacion: float = 5.0,
                                    incluir_graficas: bool = True) -> str:
        """Genera un informe de desviaciones en nóminas para un año específico.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para el análisis
            umbral_desviacion: Umbral de desviación porcentual para destacar (por defecto 5%)
            incluir_graficas: Si se deben incluir gráficas en el informe
            
        Returns:
            Ruta al archivo del informe generado
        """
        cursor = self.conn.cursor()
        
        # Obtener información del empleado
        cursor.execute('''
        SELECT id_empleado, nombre, apellidos, nif, categoria
        FROM Empleados
        WHERE id_empleado = ?
        ''', (id_empleado,))
        
        empleado = cursor.fetchone()
        if not empleado:
            return None
        
        # Obtener nóminas del año
        cursor.execute('''
        SELECT id_nomina, periodo_inicio, periodo_fin, importe_bruto, importe_neto
        FROM Nominas
        WHERE id_empleado = ? AND strftime('%Y', periodo_fin) = ?
        ORDER BY periodo_fin
        ''', (id_empleado, str(anio)))
        
        nominas = cursor.fetchall()
        if not nominas:
            return None
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'INFORME DE DESVIACIONES - AÑO {anio}', 0, 1, 'C')
        
        # Información del empleado
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Datos del Empleado:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, 'Nombre:', 0, 0)
        pdf.cell(0, 7, f"{empleado['nombre']} {empleado['apellidos']}", 0, 1)
        
        pdf.cell(40, 7, 'NIF:', 0, 0)
        pdf.cell(0, 7, empleado['nif'], 0, 1)
        
        pdf.cell(40, 7, 'Categoría:', 0, 0)
        pdf.cell(0, 7, empleado['categoria'], 0, 1)
        
        # Resumen de nóminas
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Resumen de Nóminas:', 0, 1)
        
        # Tabla de nóminas
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(50, 7, 'PERIODO', 1, 0, 'C')
        pdf.cell(40, 7, 'BRUTO', 1, 0, 'C')
        pdf.cell(40, 7, 'NETO', 1, 0, 'C')
        pdf.cell(60, 7, 'RATIO NETO/BRUTO', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        
        # Calcular valores medios para comparación
        brutos = [n['importe_bruto'] for n in nominas]
        netos = [n['importe_neto'] for n in nominas]
        ratios = [n['importe_neto'] / n['importe_bruto'] if n['importe_bruto'] > 0 else 0 for n in nominas]
        
        bruto_medio = sum(brutos) / len(brutos) if brutos else 0
        neto_medio = sum(netos) / len(netos) if netos else 0
        ratio_medio = sum(ratios) / len(ratios) if ratios else 0
        
        for nomina in nominas:
            periodo_inicio = datetime.strptime(nomina['periodo_inicio'], '%Y-%m-%d')
            periodo_fin = datetime.strptime(nomina['periodo_fin'], '%Y-%m-%d')
            
            periodo_str = f"{periodo_inicio.strftime('%m/%Y')}"
            
            ratio = nomina['importe_neto'] / nomina['importe_bruto'] if nomina['importe_bruto'] > 0 else 0
            
            # Calcular desviaciones
            desv_bruto = ((nomina['importe_bruto'] - bruto_medio) / bruto_medio * 100) if bruto_medio > 0 else 0
            desv_neto = ((nomina['importe_neto'] - neto_medio) / neto_medio * 100) if neto_medio > 0 else 0
            desv_ratio = ((ratio - ratio_medio) / ratio_medio * 100) if ratio_medio > 0 else 0
            
            pdf.cell(50, 7, periodo_str, 1, 0)
            
            # Colorear según desviación
            if abs(desv_bruto) > umbral_desviacion:
                pdf.set_text_color(255, 0, 0) if desv_bruto < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(40, 7, f"{nomina['importe_bruto']:.2f} €", 1, 0, 'R')
            pdf.set_text_color(0, 0, 0)
            
            if abs(desv_neto) > umbral_desviacion:
                pdf.set_text_color(255, 0, 0) if desv_neto < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(40, 7, f"{nomina['importe_neto']:.2f} €", 1, 0, 'R')
            pdf.set_text_color(0, 0, 0)
            
            if abs(desv_ratio) > umbral_desviacion:
                pdf.set_text_color(255, 0, 0) if desv_ratio < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(60, 7, f"{ratio:.2%}", 1, 1, 'R')
            pdf.set_text_color(0, 0, 0)
        
        # Valores medios
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(50, 7, 'MEDIA', 1, 0, 'C')
        pdf.cell(40, 7, f"{bruto_medio:.2f} €", 1, 0, 'R')
        pdf.cell(40, 7, f"{neto_medio:.2f} €", 1, 0, 'R')
        pdf.cell(60, 7, f"{ratio_medio:.2%}", 1, 1, 'R')
        
        # Análisis de desviaciones por conceptos
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Análisis de Desviaciones por Conceptos:', 0, 1)
        
        # Obtener todos los conceptos de las nóminas del año
        cursor.execute('''
        SELECT c.id_nomina, c.concepto, c.importe, n.periodo_fin
        FROM ConceptosNomina c
        JOIN Nominas n ON c.id_nomina = n.id_nomina
        WHERE n.id_empleado = ? AND strftime('%Y', n.periodo_fin) = ?
        ORDER BY c.concepto, n.periodo_fin
        ''', (id_empleado, str(anio)))
        
        conceptos_por_nomina = {}
        for row in cursor.fetchall():
            periodo = datetime.strptime(row['periodo_fin'], '%Y-%m-%d').strftime('%m/%Y')
            
            if row['concepto'] not in conceptos_por_nomina:
                conceptos_por_nomina[row['concepto']] = {}
            
            conceptos_por_nomina[row['concepto']][periodo] = row['importe']
        
        # Mostrar conceptos con desviaciones significativas
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 7, 'CONCEPTO', 1, 0, 'C')
        pdf.cell(40, 7, 'VALOR MÍNIMO', 1, 0, 'C')
        pdf.cell(40, 7, 'VALOR MÁXIMO', 1, 0, 'C')
        pdf.cell(50, 7, 'DESVIACIÓN', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        
        for concepto, valores in conceptos_por_nomina.items():
            if len(valores) < 2:
                continue  # Necesitamos al menos dos valores para comparar
            
            importes = list(valores.values())
            valor_min = min(importes)
            valor_max = max(importes)
            
            # Calcular desviación porcentual
            if valor_min > 0:
                desviacion = (valor_max - valor_min) / valor_min * 100
            else:
                desviacion = 100 if valor_max > 0 else 0
            
            # Solo mostrar conceptos con desviaciones significativas
            if desviacion > umbral_desviacion:
                pdf.cell(60, 7, concepto, 1, 0)
                pdf.cell(40, 7, f"{valor_min:.2f} €", 1, 0, 'R')
                pdf.cell(40, 7, f"{valor_max:.2f} €", 1, 0, 'R')
                
                # Colorear según magnitud de la desviación
                if desviacion > umbral_desviacion * 2:
                    pdf.set_text_color(255, 0, 0)  # Rojo para desviaciones muy altas
                else:
                    pdf.set_text_color(255, 128, 0)  # Naranja para desviaciones moderadas
                
                pdf.cell(50, 7, f"{desviacion:.2f}%", 1, 1, 'R')
                pdf.set_text_color(0, 0, 0)
        
        # Incluir gráficas si se solicita
        if incluir_graficas:
            # Crear gráficas de evolución
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Gráfica de evolución de importes
                periodos = [datetime.strptime(n['periodo_fin'], '%Y-%m-%d').strftime('%m/%Y') for n in nominas]
                
                plt.figure(figsize=(10, 6))
                plt.plot(periodos, brutos, marker='o', label='Bruto')
                plt.plot(periodos, netos, marker='s', label='Neto')
                
                plt.xlabel('Periodo')
                plt.ylabel('Importe (€)')
                plt.title('Evolución de Importes')
                plt.xticks(rotation=45)
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'evolucion_importes.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir nueva página para la gráfica
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Gráficas de Evolución', 0, 1, 'C')
                
                # Añadir gráfica al PDF
                pdf.image(grafica_path, x=10, y=30, w=190)
                
                # Gráfica de evolución de conceptos con mayor desviación
                # Seleccionar los 5 conceptos con mayor desviación
                conceptos_con_desviacion = []
                
                for concepto, valores in conceptos_por_nomina.items():
                    if len(valores) < 2:
                        continue
                    
                    importes = list(valores.values())
                    valor_min = min(importes)
                    valor_max = max(importes)
                    
                    if valor_min > 0:
                        desviacion = (valor_max - valor_min) / valor_min * 100
                    else:
                        desviacion = 100 if valor_max > 0 else 0
                    
                    if desviacion > umbral_desviacion:
                        conceptos_con_desviacion.append((concepto, desviacion))
                
                # Ordenar por desviación y tomar los 5 primeros
                conceptos_con_desviacion.sort(key=lambda x: x[1], reverse=True)
                conceptos_seleccionados = [c[0] for c in conceptos_con_desviacion[:5]]
                
                if conceptos_seleccionados:
                    plt.figure(figsize=(10, 6))
                    
                    for concepto in conceptos_seleccionados:
                        valores = conceptos_por_nomina[concepto]
                        periodos_concepto = list(valores.keys())
                        importes_concepto = list(valores.values())
                        
                        plt.plot(periodos_concepto, importes_concepto, marker='o', label=concepto)
                    
                    plt.xlabel('Periodo')
                    plt.ylabel('Importe (€)')
                    plt.title('Evolución de Conceptos con Mayor Desviación')
                    plt.xticks(rotation=45)
                    plt.legend()
                    plt.grid(True, linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    # Guardar gráfica temporalmente
                    grafica_path = os.path.join(temp_dir, 'evolucion_conceptos.png')
                    plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    # Añadir gráfica al PDF
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, 'Evolución de Conceptos con Mayor Desviación', 0, 1, 'C')
                    
                    pdf.image(grafica_path, x=10, y=30, w=190)
                
            finally:
                # Limpiar archivos temporales
                shutil.rmtree(temp_dir)
        
        # Guardar PDF
        nombre_archivo = f"informe_desviaciones_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        pdf.output(ruta_archivo)
        
        return ruta_archivo
    
    def generar_informe_calendario(self, id_empleado: int, anio: int, mes: int = None) -> str:
        """Genera un informe del calendario laboral.
        
        Args:
            id_empleado: ID del empleado
            anio: Año del calendario
            mes: Mes específico (1-12) (opcional)
            
        Returns:
            Ruta al archivo del informe generado
        """
        cursor = self.conn.cursor()
        
        # Obtener información del empleado
        cursor.execute('''
        SELECT id_empleado, nombre, apellidos
        FROM Empleados
        WHERE id_empleado = ?
        ''', (id_empleado,))
        
        empleado = cursor.fetchone()
        if not empleado:
            return None
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 16)
        if mes:
            nombre_mes = calendar.month_name[mes]
            pdf.cell(0, 10, f'INFORME DE CALENDARIO LABORAL - {nombre_mes.upper()} {anio}', 0, 1, 'C')
        else:
            pdf.cell(0, 10, f'INFORME DE CALENDARIO LABORAL - AÑO {anio}', 0, 1, 'C')
        
        # Información del empleado
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Datos del Empleado:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, 'Nombre:', 0, 0)
        pdf.cell(0, 7, f"{empleado['nombre']} {empleado['apellidos']}", 0, 1)
        
        # Preparar consulta
        if mes:
            # Obtener días del mes específico
            query = '''
            SELECT c.fecha, c.horas_teoricas, t.codigo as tipo_codigo, t.nombre as tipo_nombre, 
                   tu.codigo as turno_codigo, tu.nombre as turno_nombre
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
            SELECT t.codigo, t.nombre, COUNT(*) as dias
            FROM CalendarioLaboral c
            JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
            WHERE c.id_empleado = ? AND strftime('%Y', c.fecha) = ?
            GROUP BY t.id_tipo_dia
            ORDER BY dias DESC
            '''
            params = [id_empleado, str(anio)]
        
        cursor.execute(query, params)
        
        if mes:
            # Mostrar calendario mensual
            dias_mes = cursor.fetchall()
            
            if not dias_mes:
                pdf.ln(5)
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, 'No hay datos de calendario para el mes seleccionado.', 0, 1)
            else:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Detalle del Mes:', 0, 1)
                
                # Tabla de días
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(30, 7, 'FECHA', 1, 0, 'C')
                pdf.cell(30, 7, 'DÍA', 1, 0, 'C')
                pdf.cell(40, 7, 'TIPO', 1, 0, 'C')
                pdf.cell(40, 7, 'TURNO', 1, 0, 'C')
                pdf.cell(50, 7, 'HORAS', 1, 1, 'C')
                
                pdf.set_font('Arial', '', 10)
                
                total_horas = 0
                dias_por_tipo = {}
                
                for dia in dias_mes:
                    fecha = datetime.strptime(dia['fecha'], '%Y-%m-%d')
                    nombre_dia = calendar.day_name[fecha.weekday()]
                    
                    pdf.cell(30, 7, fecha.strftime('%d/%m/%Y'), 1, 0)
                    pdf.cell(30, 7, nombre_dia, 1, 0)
                    pdf.cell(40, 7, f"{dia['tipo_codigo']}: {dia['tipo_nombre']}", 1, 0)
                    pdf.cell(40, 7, f"{dia['turno_codigo']}: {dia['turno_nombre']}", 1, 0)
                    pdf.cell(50, 7, f"{dia['horas_teoricas']:.2f} h", 1, 1, 'R')
                    
                    total_horas += dia['horas_teoricas']
                    
                    # Contabilizar días por tipo
                    tipo = dia['tipo_codigo']
                    if tipo not in dias_por_tipo:
                        dias_por_tipo[tipo] = 0
                    dias_por_tipo[tipo] += 1
                
                # Mostrar resumen del mes
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Resumen del Mes:', 0, 1)
                
                pdf.set_font('Arial', '', 10)
                pdf.cell(60, 7, 'Total de horas:', 0, 0)
                pdf.cell(0, 7, f"{total_horas:.2f} h", 0, 1)
                
                # Mostrar días por tipo
                for tipo, dias in dias_por_tipo.items():
                    pdf.cell(60, 7, f"Días {tipo}:", 0, 0)
                    pdf.cell(0, 7, str(dias), 0, 1)
        else:
            # Mostrar resumen anual
            datos_resumen = cursor.fetchall()
            
            if not datos_resumen:
                pdf.ln(5)
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, 'No hay datos de calendario para el año seleccionado.', 0, 1)
            else:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Resumen Anual:', 0, 1)
                
                # Tabla de tipos de día
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(40, 7, 'TIPO', 1, 0, 'C')
                pdf.cell(100, 7, 'DESCRIPCIÓN', 1, 0, 'C')
                pdf.cell(50, 7, 'DÍAS', 1, 1, 'C')
                
                pdf.set_font('Arial', '', 10)
                
                total_dias = 0
                
                for row in datos_resumen:
                    pdf.cell(40, 7, row['codigo'], 1, 0)
                    pdf.cell(100, 7, row['nombre'], 1, 0)
                    pdf.cell(50, 7, str(row['dias']), 1, 1, 'R')
                    
                    total_dias += row['dias']
                
                # Mostrar total
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(140, 7, 'TOTAL', 1, 0, 'R')
                pdf.cell(50, 7, str(total_dias), 1, 1, 'R')
                
                # Obtener horas totales
                cursor.execute('''
                SELECT SUM(horas_teoricas) as total_horas
                FROM CalendarioLaboral
                WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
                ''', (id_empleado, str(anio)))
                
                total_horas = cursor.fetchone()['total_horas'] or 0
                
                pdf.ln(5)
                pdf.set_font('Arial', '', 10)
                pdf.cell(60, 7, 'Total de horas anuales:', 0, 0)
                pdf.cell(0, 7, f"{total_horas:.2f} h", 0, 1)
                
                # Obtener horas por mes
                cursor.execute('''
                SELECT strftime('%m', fecha) as mes, SUM(horas_teoricas) as horas
                FROM CalendarioLaboral
                WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
                GROUP BY strftime('%m', fecha)
                ORDER BY mes
                ''', (id_empleado, str(anio)))
                
                horas_por_mes = cursor.fetchall()
                
                if horas_por_mes:
                    pdf.ln(5)
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, 'Horas por Mes:', 0, 1)
                    
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(60, 7, 'MES', 1, 0, 'C')
                    pdf.cell(60, 7, 'HORAS', 1, 1, 'C')
                    
                    pdf.set_font('Arial', '', 10)
                    
                    for row in horas_por_mes:
                        mes_num = int(row['mes'])
                        nombre_mes = calendar.month_name[mes_num]
                        
                        pdf.cell(60, 7, nombre_mes, 1, 0)
                        pdf.cell(60, 7, f"{row['horas']:.2f} h", 1, 1, 'R')
        
        # Guardar PDF
        if mes:
            nombre_archivo = f"informe_calendario_{id_empleado}_{anio}_{mes}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        else:
            nombre_archivo = f"informe_calendario_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        pdf.output(ruta_archivo)
        
        return ruta_archivo
    
    def generar_informe_prediccion(self, id_empleado: int, anio: int) -> str:
        """Genera un informe de predicción de nóminas para un año.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para la predicción
            
        Returns:
            Ruta al archivo del informe generado
        """
        cursor = self.conn.cursor()
        
        # Obtener información del empleado
        cursor.execute('''
        SELECT id_empleado, nombre, apellidos
        FROM Empleados
        WHERE id_empleado = ?
        ''', (id_empleado,))
        
        empleado = cursor.fetchone()
        if not empleado:
            return None
        
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
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'INFORME DE PREDICCIÓN DE NÓMINAS - AÑO {anio}', 0, 1, 'C')
        
        # Información del empleado
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Datos del Empleado:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, 'Nombre:', 0, 0)
        pdf.cell(0, 7, f"{empleado['nombre']} {empleado['apellidos']}", 0, 1)
        
        # Predicciones mensuales
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Predicciones Mensuales:', 0, 1)
        
        # Tabla de predicciones
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 7, 'MES', 1, 0, 'C')
        pdf.cell(60, 7, 'IMPORTE BRUTO', 1, 0, 'C')
        pdf.cell(60, 7, 'IMPORTE NETO', 1, 0, 'C')
        pdf.cell(30, 7, 'RATIO', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        
        total_bruto = 0
        total_neto = 0
        
        for prediccion in predicciones:
            mes_num = prediccion['mes']
            nombre_mes = calendar.month_name[mes_num]
            
            bruto = prediccion['importe_bruto_predicho']
            neto = prediccion['importe_neto_predicho']
            ratio = neto / bruto if bruto > 0 else 0
            
            pdf.cell(40, 7, nombre_mes, 1, 0)
            pdf.cell(60, 7, f"{bruto:.2f} €", 1, 0, 'R')
            pdf.cell(60, 7, f"{neto:.2f} €", 1, 0, 'R')
            pdf.cell(30, 7, f"{ratio:.2%}", 1, 1, 'R')
            
            total_bruto += bruto
            total_neto += neto
        
        # Totales anuales
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 7, 'TOTAL ANUAL', 1, 0, 'C')
        pdf.cell(60, 7, f"{total_bruto:.2f} €", 1, 0, 'R')
        pdf.cell(60, 7, f"{total_neto:.2f} €", 1, 0, 'R')
        
        ratio_anual = total_neto / total_bruto if total_bruto > 0 else 0
        pdf.cell(30, 7, f"{ratio_anual:.2%}", 1, 1, 'R')
        
        # Obtener nóminas reales para comparar
        cursor.execute('''
        SELECT strftime('%m', n.periodo_fin) as mes, n.importe_bruto, n.importe_neto
        FROM Nominas n
        WHERE n.id_empleado = ? AND strftime('%Y', n.periodo_fin) = ?
        ORDER BY n.periodo_fin
        ''', (id_empleado, str(anio)))
        
        nominas_reales = cursor.fetchall()
        
        if nominas_reales:
            # Comparación con nóminas reales
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Comparación con Nóminas Reales:', 0, 1)
            
            # Tabla de comparación
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(30, 7, 'MES', 1, 0, 'C')
            pdf.cell(40, 7, 'BRUTO PRED.', 1, 0, 'C')
            pdf.cell(40, 7, 'BRUTO REAL', 1, 0, 'C')
            pdf.cell(40, 7, 'NETO PRED.', 1, 0, 'C')
            pdf.cell(40, 7, 'NETO REAL', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            
            # Crear diccionarios para facilitar la comparación
            predicciones_dict = {p['mes']: p for p in predicciones}
            nominas_dict = {int(n['mes']): n for n in nominas_reales}
            
            # Meses con datos reales
            for mes_num, nomina in nominas_dict.items():
                if mes_num in predicciones_dict:
                    prediccion = predicciones_dict[mes_num]
                    nombre_mes = calendar.month_name[mes_num]
                    
                    bruto_pred = prediccion['importe_bruto_predicho']
                    bruto_real = nomina['importe_bruto']
                    neto_pred = prediccion['importe_neto_predicho']
                    neto_real = nomina['importe_neto']
                    
                    pdf.cell(30, 7, nombre_mes, 1, 0)
                    
                    # Colorear según desviación
                    desv_bruto = ((bruto_real - bruto_pred) / bruto_pred * 100) if bruto_pred > 0 else 0
                    if abs(desv_bruto) > 5:
                        pdf.set_text_color(255, 0, 0) if desv_bruto < 0 else pdf.set_text_color(0, 128, 0)
                    
                    pdf.cell(40, 7, f"{bruto_pred:.2f} €", 1, 0, 'R')
                    pdf.cell(40, 7, f"{bruto_real:.2f} €", 1, 0, 'R')
                    pdf.set_text_color(0, 0, 0)
                    
                    desv_neto = ((neto_real - neto_pred) / neto_pred * 100) if neto_pred > 0 else 0
                    if abs(desv_neto) > 5:
                        pdf.set_text_color(255, 0, 0) if desv_neto < 0 else pdf.set_text_color(0, 128, 0)
                    
                    pdf.cell(40, 7, f"{neto_pred:.2f} €", 1, 0, 'R')
                    pdf.cell(40, 7, f"{neto_real:.2f} €", 1, 1, 'R')
                    pdf.set_text_color(0, 0, 0)
            
            # Calcular totales reales
            total_bruto_real = sum(n['importe_bruto'] for n in nominas_reales)
            total_neto_real = sum(n['importe_neto'] for n in nominas_reales)
            
            # Calcular totales predichos para los mismos meses
            meses_reales = [int(n['mes']) for n in nominas_reales]
            total_bruto_pred = sum(predicciones_dict[m]['importe_bruto_predicho'] for m in meses_reales if m in predicciones_dict)
            total_neto_pred = sum(predicciones_dict[m]['importe_neto_predicho'] for m in meses_reales if m in predicciones_dict)
            
            # Mostrar totales comparados
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(30, 7, 'TOTAL', 1, 0, 'C')
            
            # Colorear según desviación
            desv_bruto_total = ((total_bruto_real - total_bruto_pred) / total_bruto_pred * 100) if total_bruto_pred > 0 else 0
            if abs(desv_bruto_total) > 5:
                pdf.set_text_color(255, 0, 0) if desv_bruto_total < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(40, 7, f"{total_bruto_pred:.2f} €", 1, 0, 'R')
            pdf.cell(40, 7, f"{total_bruto_real:.2f} €", 1, 0, 'R')
            pdf.set_text_color(0, 0, 0)
            
            desv_neto_total = ((total_neto_real - total_neto_pred) / total_neto_pred * 100) if total_neto_pred > 0 else 0
            if abs(desv_neto_total) > 5:
                pdf.set_text_color(255, 0, 0) if desv_neto_total < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(40, 7, f"{total_neto_pred:.2f} €", 1, 0, 'R')
            pdf.cell(40, 7, f"{total_neto_real:.2f} €", 1, 1, 'R')
            pdf.set_text_color(0, 0, 0)
            
            # Resumen de precisión
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Resumen de Precisión:', 0, 1)
            
            pdf.set_font('Arial', '', 10)
            pdf.cell(60, 7, 'Desviación en Bruto:', 0, 0)
            
            if abs(desv_bruto_total) > 5:
                pdf.set_text_color(255, 0, 0) if desv_bruto_total < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(0, 7, f"{desv_bruto_total:.2f}%", 0, 1)
            pdf.set_text_color(0, 0, 0)
            
            pdf.cell(60, 7, 'Desviación en Neto:', 0, 0)
            
            if abs(desv_neto_total) > 5:
                pdf.set_text_color(255, 0, 0) if desv_neto_total < 0 else pdf.set_text_color(0, 128, 0)
            
            pdf.cell(0, 7, f"{desv_neto_total:.2f}%", 0, 1)
            pdf.set_text_color(0, 0, 0)
        
        # Crear gráfica de predicción vs. real
        if nominas_reales:
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Preparar datos para la gráfica
                meses = [calendar.month_abbr[p['mes']] for p in predicciones]
                brutos_pred = [p['importe_bruto_predicho'] for p in predicciones]
                netos_pred = [p['importe_neto_predicho'] for p in predicciones]
                
                # Crear arrays para datos reales (con None para meses sin datos)
                brutos_real = [None] * len(meses)
                netos_real = [None] * len(meses)
                
                for nomina in nominas_reales:
                    mes_idx = int(nomina['mes']) - 1  # Ajustar a índice 0-based
                    brutos_real[mes_idx] = nomina['importe_bruto']
                    netos_real[mes_idx] = nomina['importe_neto']
                
                # Crear gráfica
                plt.figure(figsize=(10, 6))
                
                # Gráfica de importes brutos
                plt.plot(meses, brutos_pred, marker='o', linestyle='-', color='blue', label='Bruto Predicho')
                plt.plot(meses, brutos_real, marker='s', linestyle='--', color='green', label='Bruto Real')
                
                plt.xlabel('Mes')
                plt.ylabel('Importe (€)')
                plt.title(f'Predicción vs. Real - Año {anio}')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.legend()
                plt.tight_layout()
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'prediccion_vs_real.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir nueva página para la gráfica
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Gráfica de Predicción vs. Real', 0, 1, 'C')
                
                # Añadir gráfica al PDF
                pdf.image(grafica_path, x=10, y=30, w=190)
                
                # Crear gráfica de importes netos
                plt.figure(figsize=(10, 6))
                
                plt.plot(meses, netos_pred, marker='o', linestyle='-', color='blue', label='Neto Predicho')
                plt.plot(meses, netos_real, marker='s', linestyle='--', color='green', label='Neto Real')
                
                plt.xlabel('Mes')
                plt.ylabel('Importe (€)')
                plt.title(f'Predicción vs. Real (Neto) - Año {anio}')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.legend()
                plt.tight_layout()
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'prediccion_vs_real_neto.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir gráfica al PDF
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Gráfica de Predicción vs. Real (Neto)', 0, 1, 'C')
                
                pdf.image(grafica_path, x=10, y=30, w=190)
                
            finally:
                # Limpiar archivos temporales
                shutil.rmtree(temp_dir)
        
        # Guardar PDF
        nombre_archivo = f"informe_prediccion_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        pdf.output(ruta_archivo)
        
        return ruta_archivo
    
    def generar_informe_completo(self, id_empleado: int, anio: int) -> str:
        """Genera un informe completo con toda la información del año.
        
        Args:
            id_empleado: ID del empleado
            anio: Año para el informe
            
        Returns:
            Ruta al archivo del informe generado
        """
        cursor = self.conn.cursor()
        
        # Obtener información del empleado
        cursor.execute('''
        SELECT id_empleado, nombre, apellidos, nif, categoria, fecha_alta
        FROM Empleados
        WHERE id_empleado = ?
        ''', (id_empleado,))
        
        empleado = cursor.fetchone()
        if not empleado:
            return None
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'INFORME ANUAL COMPLETO - {anio}', 0, 1, 'C')
        
        # Información del empleado
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Datos del Empleado:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, 'Nombre:', 0, 0)
        pdf.cell(0, 7, f"{empleado['nombre']} {empleado['apellidos']}", 0, 1)
        
        pdf.cell(40, 7, 'NIF:', 0, 0)
        pdf.cell(0, 7, empleado['nif'], 0, 1)
        
        pdf.cell(40, 7, 'Categoría:', 0, 0)
        pdf.cell(0, 7, empleado['categoria'], 0, 1)
        
        fecha_alta = datetime.strptime(empleado['fecha_alta'], '%Y-%m-%d') if empleado['fecha_alta'] else None
        if fecha_alta:
            pdf.cell(40, 7, 'Fecha de alta:', 0, 0)
            pdf.cell(0, 7, fecha_alta.strftime('%d/%m/%Y'), 0, 1)
        
        # 1. Resumen de nóminas
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '1. RESUMEN DE NÓMINAS', 0, 1)
        
        # Obtener nóminas del año
        cursor.execute('''
        SELECT id_nomina, periodo_inicio, periodo_fin, fecha_pago, importe_bruto, importe_neto
        FROM Nominas
        WHERE id_empleado = ? AND strftime('%Y', periodo_fin) = ?
        ORDER BY periodo_fin
        ''', (id_empleado, str(anio)))
        
        nominas = cursor.fetchall()
        
        if not nominas:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, 'No hay nóminas registradas para este año.', 0, 1)
        else:
            # Tabla de nóminas
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 7, 'PERIODO', 1, 0, 'C')
            pdf.cell(40, 7, 'FECHA PAGO', 1, 0, 'C')
            pdf.cell(40, 7, 'BRUTO', 1, 0, 'C')
            pdf.cell(40, 7, 'NETO', 1, 0, 'C')
            pdf.cell(30, 7, 'RATIO', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            
            total_bruto = 0
            total_neto = 0
            
            for nomina in nominas:
                periodo_inicio = datetime.strptime(nomina['periodo_inicio'], '%Y-%m-%d')
                periodo_fin = datetime.strptime(nomina['periodo_fin'], '%Y-%m-%d')
                fecha_pago = datetime.strptime(nomina['fecha_pago'], '%Y-%m-%d')
                
                periodo_str = f"{periodo_inicio.strftime('%m/%Y')}"
                
                bruto = nomina['importe_bruto']
                neto = nomina['importe_neto']
                ratio = neto / bruto if bruto > 0 else 0
                
                pdf.cell(40, 7, periodo_str, 1, 0)
                pdf.cell(40, 7, fecha_pago.strftime('%d/%m/%Y'), 1, 0)
                pdf.cell(40, 7, f"{bruto:.2f} €", 1, 0, 'R')
                pdf.cell(40, 7, f"{neto:.2f} €", 1, 0, 'R')
                pdf.cell(30, 7, f"{ratio:.2%}", 1, 1, 'R')
                
                total_bruto += bruto
                total_neto += neto
            
            # Totales
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 7, 'TOTAL ANUAL', 1, 0, 'C')
            pdf.cell(40, 7, f"{total_bruto:.2f} €", 1, 0, 'R')
            pdf.cell(40, 7, f"{total_neto:.2f} €", 1, 0, 'R')
            
            ratio_anual = total_neto / total_bruto if total_bruto > 0 else 0
            pdf.cell(30, 7, f"{ratio_anual:.2%}", 1, 1, 'R')
        
        # 2. Calendario laboral
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '2. CALENDARIO LABORAL', 0, 1)
        
        # Obtener resumen del calendario
        cursor.execute('''
        SELECT t.codigo, t.nombre, COUNT(*) as dias
        FROM CalendarioLaboral c
        JOIN TiposDia t ON c.id_tipo_dia = t.id_tipo_dia
        WHERE c.id_empleado = ? AND strftime('%Y', c.fecha) = ?
        GROUP BY t.id_tipo_dia
        ORDER BY dias DESC
        ''', (id_empleado, str(anio)))
        
        datos_calendario = cursor.fetchall()
        
        if not datos_calendario:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, 'No hay datos de calendario para este año.', 0, 1)
        else:
            # Tabla de tipos de día
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 7, 'TIPO', 1, 0, 'C')
            pdf.cell(100, 7, 'DESCRIPCIÓN', 1, 0, 'C')
            pdf.cell(50, 7, 'DÍAS', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            
            total_dias = 0
            
            for row in datos_calendario:
                pdf.cell(40, 7, row['codigo'], 1, 0)
                pdf.cell(100, 7, row['nombre'], 1, 0)
                pdf.cell(50, 7, str(row['dias']), 1, 1, 'R')
                
                total_dias += row['dias']
            
            # Mostrar total
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(140, 7, 'TOTAL', 1, 0, 'R')
            pdf.cell(50, 7, str(total_dias), 1, 1, 'R')
            
            # Obtener horas totales
            cursor.execute('''
            SELECT SUM(horas_teoricas) as total_horas
            FROM CalendarioLaboral
            WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
            ''', (id_empleado, str(anio)))
            
            total_horas = cursor.fetchone()['total_horas'] or 0
            
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            pdf.cell(60, 7, 'Total de horas anuales:', 0, 0)
            pdf.cell(0, 7, f"{total_horas:.2f} h", 0, 1)
            
            # Obtener horas por mes
            cursor.execute('''
            SELECT strftime('%m', fecha) as mes, SUM(horas_teoricas) as horas
            FROM CalendarioLaboral
            WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
            GROUP BY strftime('%m', fecha)
            ORDER BY mes
            ''', (id_empleado, str(anio)))
            
            horas_por_mes = cursor.fetchall()
            
            if horas_por_mes:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Horas por Mes:', 0, 1)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(60, 7, 'MES', 1, 0, 'C')
                pdf.cell(60, 7, 'HORAS', 1, 1, 'C')
                
                pdf.set_font('Arial', '', 10)
                
                for row in horas_por_mes:
                    mes_num = int(row['mes'])
                    nombre_mes = calendar.month_name[mes_num]
                    
                    pdf.cell(60, 7, nombre_mes, 1, 0)
                    pdf.cell(60, 7, f"{row['horas']:.2f} h", 1, 1, 'R')
        
        # 3. Incrementos salariales
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '3. INCREMENTOS SALARIALES', 0, 1)
        
        # Obtener incrementos del año
        cursor.execute('''
        SELECT fecha, concepto, valor_anterior, valor_nuevo, porcentaje_incremento, motivo
        FROM HistoricoSalarios
        WHERE id_empleado = ? AND strftime('%Y', fecha) = ?
        ORDER BY fecha
        ''', (id_empleado, str(anio)))
        
        incrementos = cursor.fetchall()
        
        if not incrementos:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, 'No hay incrementos salariales registrados para este año.', 0, 1)
        else:
            # Tabla de incrementos
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(30, 7, 'FECHA', 1, 0, 'C')
            pdf.cell(40, 7, 'CONCEPTO', 1, 0, 'C')
            pdf.cell(30, 7, 'ANTERIOR', 1, 0, 'C')
            pdf.cell(30, 7, 'NUEVO', 1, 0, 'C')
            pdf.cell(30, 7, 'INCREMENTO', 1, 0, 'C')
            pdf.cell(30, 7, 'MOTIVO', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            
            for incremento in incrementos:
                fecha = datetime.strptime(incremento['fecha'], '%Y-%m-%d')
                
                pdf.cell(30, 7, fecha.strftime('%d/%m/%Y'), 1, 0)
                pdf.cell(40, 7, incremento['concepto'], 1, 0)
                pdf.cell(30, 7, f"{incremento['valor_anterior']:.2f} €", 1, 0, 'R')
                pdf.cell(30, 7, f"{incremento['valor_nuevo']:.2f} €", 1, 0, 'R')
                pdf.cell(30, 7, f"{incremento['porcentaje_incremento']:.2f}%", 1, 0, 'R')
                pdf.cell(30, 7, incremento['motivo'], 1, 1)
        
        # 4. Pagas extras
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '4. PAGAS EXTRAS', 0, 1)
        
        # Obtener pagas extras
        cursor.execute('''
        SELECT p.fecha_pago, p.importe_bruto, p.importe_neto, 
               t.codigo, t.nombre
        FROM PagasExtrasEmpleados p
        JOIN TiposPagaExtra t ON p.id_tipo_paga = t.id_tipo_paga
        WHERE p.id_empleado = ? AND p.anio = ?
        ORDER BY p.fecha_pago
        ''', (id_empleado, anio))
        
        pagas = cursor.fetchall()
        
        if not pagas:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, 'No hay pagas extras registradas para este año.', 0, 1)
        else:
            # Tabla de pagas extras
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(30, 7, 'FECHA', 1, 0, 'C')
            pdf.cell(40, 7, 'TIPO', 1, 0, 'C')
            pdf.cell(40, 7, 'BRUTO', 1, 0, 'C')
            pdf.cell(40, 7, 'NETO', 1, 0, 'C')
            pdf.cell(40, 7, 'RATIO', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            
            total_bruto_pagas = 0
            total_neto_pagas = 0
            
            for paga in pagas:
                fecha = datetime.strptime(paga['fecha_pago'], '%Y-%m-%d')
                
                bruto = paga['importe_bruto']
                neto = paga['importe_neto']
                ratio = neto / bruto if bruto > 0 else 0
                
                pdf.cell(30, 7, fecha.strftime('%d/%m/%Y'), 1, 0)
                pdf.cell(40, 7, f"{paga['codigo']}: {paga['nombre']}", 1, 0)
                pdf.cell(40, 7, f"{bruto:.2f} €", 1, 0, 'R')
                pdf.cell(40, 7, f"{neto:.2f} €", 1, 0, 'R')
                pdf.cell(40, 7, f"{ratio:.2%}", 1, 1, 'R')
                
                total_bruto_pagas += bruto
                total_neto_pagas += neto
            
            # Totales
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(70, 7, 'TOTAL PAGAS EXTRAS', 1, 0, 'C')
            pdf.cell(40, 7, f"{total_bruto_pagas:.2f} €", 1, 0, 'R')
            pdf.cell(40, 7, f"{total_neto_pagas:.2f} €", 1, 0, 'R')
            
            ratio_pagas = total_neto_pagas / total_bruto_pagas if total_bruto_pagas > 0 else 0
            pdf.cell(40, 7, f"{ratio_pagas:.2%}", 1, 1, 'R')
        
        # 5. Resumen anual
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '5. RESUMEN ANUAL', 0, 1)
        
        # Calcular totales anuales (nóminas + pagas extras)
        total_bruto_anual = (total_bruto if 'total_bruto' in locals() else 0) + (total_bruto_pagas if 'total_bruto_pagas' in locals() else 0)
        total_neto_anual = (total_neto if 'total_neto' in locals() else 0) + (total_neto_pagas if 'total_neto_pagas' in locals() else 0)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Ingresos Totales:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(60, 7, 'Total bruto anual:', 0, 0)
        pdf.cell(0, 7, f"{total_bruto_anual:.2f} €", 0, 1)
        
        pdf.cell(60, 7, 'Total neto anual:', 0, 0)
        pdf.cell(0, 7, f"{total_neto_anual:.2f} €", 0, 1)
        
        # Calcular media mensual
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Medias Mensuales:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(60, 7, 'Media bruta mensual:', 0, 0)
        pdf.cell(0, 7, f"{(total_bruto_anual / 12):.2f} €", 0, 1)
        
        pdf.cell(60, 7, 'Media neta mensual:', 0, 0)
        pdf.cell(0, 7, f"{(total_neto_anual / 12):.2f} €", 0, 1)
        
        # Calcular ratio retención medio
        ratio_retencion = 1 - (total_neto_anual / total_bruto_anual) if total_bruto_anual > 0 else 0
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Retenciones:', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(60, 7, 'Ratio de retención medio:', 0, 0)
        pdf.cell(0, 7, f"{ratio_retencion:.2%}", 0, 1)
        
        pdf.cell(60, 7, 'Total retenciones:', 0, 0)
        pdf.cell(0, 7, f"{(total_bruto_anual - total_neto_anual):.2f} €", 0, 1)
        
        # Horas trabajadas
        if 'total_horas' in locals() and total_horas > 0:
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Análisis por Horas:', 0, 1)
            
            pdf.set_font('Arial', '', 10)
            pdf.cell(60, 7, 'Total horas trabajadas:', 0, 0)
            pdf.cell(0, 7, f"{total_horas:.2f} h", 0, 1)
            
            pdf.cell(60, 7, 'Precio hora bruto medio:', 0, 0)
            pdf.cell(0, 7, f"{(total_bruto_anual / total_horas):.2f} €/h", 0, 1)
            
            pdf.cell(60, 7, 'Precio hora neto medio:', 0, 0)
            pdf.cell(0, 7, f"{(total_neto_anual / total_horas):.2f} €/h", 0, 1)
        
        # Crear gráficas para el informe
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Gráfica de evolución de nóminas
            if 'nominas' in locals() and nominas:
                periodos = [datetime.strptime(n['periodo_fin'], '%Y-%m-%d').strftime('%m/%Y') for n in nominas]
                brutos = [n['importe_bruto'] for n in nominas]
                netos = [n['importe_neto'] for n in nominas]
                
                plt.figure(figsize=(10, 6))
                plt.plot(periodos, brutos, marker='o', linestyle='-', color='blue', label='Bruto')
                plt.plot(periodos, netos, marker='s', linestyle='-', color='green', label='Neto')
                
                plt.xlabel('Periodo')
                plt.ylabel('Importe (€)')
                plt.title(f'Evolución de Nóminas - {anio}')
                plt.xticks(rotation=45)
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'evolucion_nominas.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir nueva página para la gráfica
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Gráficas de Evolución', 0, 1, 'C')
                
                # Añadir gráfica al PDF
                pdf.image(grafica_path, x=10, y=30, w=190)
            
            # Gráfica de distribución de tipos de día
            if 'datos_calendario' in locals() and datos_calendario:
                labels = [row['codigo'] for row in datos_calendario]
                sizes = [row['dias'] for row in datos_calendario]
                
                plt.figure(figsize=(8, 8))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                plt.axis('equal')
                plt.title(f'Distribución de Tipos de Día - {anio}')
                
                # Guardar gráfica temporalmente
                grafica_path = os.path.join(temp_dir, 'distribucion_dias.png')
                plt.savefig(grafica_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Añadir gráfica al PDF
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Distribución de Tipos de Día', 0, 1, 'C')
                
                pdf.image(grafica_path, x=10, y=30, w=190)
            
        finally:
            # Limpiar archivos temporales
            shutil.rmtree(temp_dir)
        
        # Guardar PDF
        nombre_archivo = f"informe_completo_{id_empleado}_{anio}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        pdf.output(ruta_archivo)
        
        return ruta_archivo


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del generador de informes
    generador = GeneradorInformes()
    
    # Generar un informe de nómina
    id_nomina = 1  # Ajustar según la base de datos
    ruta_informe = generador.generar_informe_nomina(id_nomina)
    print(f"Informe de nómina generado: {ruta_informe}")
    
    # Generar un informe de comparación
    id_nomina1 = 1  # Ajustar según la base de datos
    id_nomina2 = 2  # Ajustar según la base de datos
    ruta_informe = generador.generar_informe_comparacion_nominas(id_nomina1, id_nomina2)
    print(f"Informe de comparación generado: {ruta_informe}")
    
    # Generar un informe de desviaciones
    id_empleado = 1  # Ajustar según la base de datos
    anio_actual = datetime.now().year
    ruta_informe = generador.generar_informe_desviaciones(id_empleado, anio_actual)
    print(f"Informe de desviaciones generado: {ruta_informe}")
    
    # Generar un informe completo
    ruta_informe = generador.generar_informe_completo(id_empleado, anio_actual)
    print(f"Informe completo generado: {ruta_informe}")
    
    print("\nProceso completado.")
