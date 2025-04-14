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
            pdf.set_t
(Content truncated due to size limit. Use line ranges to read in chunks)