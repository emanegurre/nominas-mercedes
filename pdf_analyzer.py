import PyPDF2
import os
import re
import pandas as pd
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extrae el texto completo de un archivo PDF."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        return f"Error al procesar el PDF {pdf_path}: {str(e)}"

def analyze_pdf_structure(pdf_path):
    """Analiza la estructura del PDF e intenta identificar patrones."""
    text = extract_text_from_pdf(pdf_path)
    
    # Dividir por líneas para análisis
    lines = text.split('\n')
    
    # Filtrar líneas vacías
    lines = [line for line in lines if line.strip()]
    
    # Identificar posibles encabezados (líneas cortas al principio de página)
    potential_headers = lines[:10]
    
    # Identificar posibles tablas (líneas con múltiples espacios o tabulaciones)
    potential_table_lines = [line for line in lines if line.count(' ') > 5 or '\t' in line]
    
    # Identificar posibles datos numéricos (líneas con números)
    numeric_pattern = re.compile(r'\d+[.,]\d+')
    potential_numeric_data = [line for line in lines if numeric_pattern.search(line)]
    
    # Identificar posibles fechas
    date_pattern = re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}')
    potential_dates = [line for line in lines if date_pattern.search(line)]
    
    # Crear un resumen
    summary = {
        "filename": os.path.basename(pdf_path),
        "total_pages": len(PyPDF2.PdfReader(open(pdf_path, 'rb')).pages),
        "total_lines": len(lines),
        "potential_headers": potential_headers[:5],  # Primeros 5 encabezados potenciales
        "table_line_sample": potential_table_lines[:5] if potential_table_lines else [],
        "numeric_data_sample": potential_numeric_data[:5] if potential_numeric_data else [],
        "date_sample": potential_dates[:5] if potential_dates else [],
        "text_sample": text[:500] + "..." if len(text) > 500 else text  # Muestra del texto
    }
    
    return summary

def save_text_to_file(text, output_path):
    """Guarda el texto extraído en un archivo."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(text)
    return f"Texto guardado en {output_path}"

# Analizar los tres archivos PDF
pdf_files = [
    "/home/ubuntu/upload/nominas all_redacted.pdf",
    "/home/ubuntu/upload/saldos all_redacted.pdf",
    "/home/ubuntu/upload/tiempos nominas all_redacted.pdf"
]

# Crear directorio para los resultados
output_dir = "/home/ubuntu/workspace/pdf_analysis"
os.makedirs(output_dir, exist_ok=True)

# Analizar cada archivo y guardar resultados
results = []
for pdf_file in pdf_files:
    print(f"Analizando {os.path.basename(pdf_file)}...")
    
    # Extraer texto completo
    text = extract_text_from_pdf(pdf_file)
    
    # Guardar texto en archivo
    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
    text_file = os.path.join(output_dir, f"{base_name}_text.txt")
    save_text_to_file(text, text_file)
    
    # Analizar estructura
    summary = analyze_pdf_structure(pdf_file)
    results.append(summary)
    
    # Guardar resumen en archivo
    summary_file = os.path.join(output_dir, f"{base_name}_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as file:
        for key, value in summary.items():
            file.write(f"{key}: {value}\n\n")

# Crear un informe general
report_file = os.path.join(output_dir, "analisis_general.txt")
with open(report_file, 'w', encoding='utf-8') as file:
    file.write("ANÁLISIS GENERAL DE ARCHIVOS PDF\n")
    file.write("===============================\n\n")
    file.write(f"Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    for result in results:
        file.write(f"Archivo: {result['filename']}\n")
        file.write(f"Páginas: {result['total_pages']}\n")
        file.write(f"Líneas totales: {result['total_lines']}\n")
        file.write("Muestra de texto:\n")
        file.write(f"{result['text_sample']}\n\n")
        file.write("-----------------------------------\n\n")

print(f"Análisis completo. Resultados guardados en {output_dir}")
