#!/usr/bin/env python3
"""
Complete pipeline: MinerU table output → Flattened table → RAG JSON schema

This script:
1. Extracts HTML tables from MinerU output (markdown or middle.json)
2. Flattens merged cells (rowspan/colspan) so each row is complete
3. Converts to structured JSON matching the afalon_50_sc_adama.json schema
"""

import re
import json
import argparse
from datetime import date
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional


class TableCell:
    """Represents a table cell with span information"""
    def __init__(self, content: str, rowspan: int = 1, colspan: int = 1):
        self.content = content.strip()
        self.rowspan = rowspan
        self.colspan = colspan


class TableHTMLParser(HTMLParser):
    """Parse HTML tables into structured cell objects"""
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell_content = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell_attrs = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
            self.current_table = []
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag == 'td' and self.in_row:
            self.in_cell = True
            self.current_cell_content = []
            self.current_cell_attrs = dict(attrs)

    def handle_endtag(self, tag):
        if tag == 'table':
            if self.current_table:
                self.tables.append(self.current_table)
            self.in_table = False
            self.current_table = []
        elif tag == 'tr' and self.in_row:
            if self.current_row:
                self.current_table.append(self.current_row)
            self.in_row = False
            self.current_row = []
        elif tag == 'td' and self.in_cell:
            content = ''.join(self.current_cell_content)
            rowspan = int(self.current_cell_attrs.get('rowspan', 1))
            colspan = int(self.current_cell_attrs.get('colspan', 1))
            cell = TableCell(content, rowspan, colspan)
            self.current_row.append(cell)
            self.in_cell = False
            self.current_cell_content = []
            self.current_cell_attrs = {}

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell_content.append(data)


def flatten_table(table: List[List[TableCell]]) -> List[List[str]]:
    """
    Flatten table by expanding merged cells.
    Each row in output contains complete data with merged content repeated.

    This is CRITICAL for RAG: every row must be self-contained.
    """
    if not table:
        return []

    # Calculate grid dimensions
    max_cols = sum(cell.colspan for cell in table[0])
    num_rows = len(table)

    # Create empty grid
    grid = [[None for _ in range(max_cols)] for _ in range(num_rows)]

    # Fill grid using occupancy tracking
    for row_idx, row in enumerate(table):
        grid_col = 0

        for cell in row:
            # Skip already-occupied cells (from previous rowspan)
            while grid_col < max_cols and grid[row_idx][grid_col] is not None:
                grid_col += 1

            if grid_col >= max_cols:
                break

            # Fill the cell and ALL positions it spans
            for r in range(row_idx, min(row_idx + cell.rowspan, num_rows)):
                for c in range(grid_col, min(grid_col + cell.colspan, max_cols)):
                    grid[r][c] = cell.content

            grid_col += cell.colspan

    # Replace None with empty string
    for row in grid:
        for i in range(len(row)):
            if row[i] is None:
                row[i] = ''

    return grid


def parse_weed_list(weed_text: str) -> List[Dict[str, str]]:
    """
    Parse comma/semicolon separated weed names into structured list.

    Input: "Yuyo, Bledo, Mostaza, Quingüilla"
    Output: [{"nombre_comun": "Yuyo"}, {"nombre_comun": "Bledo"}, ...]
    """
    if not weed_text or weed_text.strip() in ['-', '', 'N/A']:
        return []

    # Split by common separators
    weeds = re.split(r'[,;]', weed_text)

    result = []
    for weed in weeds:
        weed = weed.strip()
        if weed and weed not in ['-', '']:
            result.append({"nombre_comun": weed})

    return result


def parse_dose(dose_text: str) -> Dict[str, Any]:
    """
    Parse dose text into structured format.
    Handles both European (1,2-1,5) and US (1.2-1.5) number formats.

    Examples:
    - "1,2-1,5 L/ha" → {valor_min: 1.2, valor_max: 1.5, unidad: "L/ha"}
    - "1.2-1.5 L/ha" → {valor_min: 1.2, valor_max: 1.5, unidad: "L/ha"}
    - "2,0 L/ha" → {valor_min: 2.0, valor_max: 2.0, unidad: "L/ha"}
    - "0,8 - 1,0" → {valor_min: 0.8, valor_max: 1.0, unidad: ""}
    """
    dose_text = dose_text.strip()

    if not dose_text or dose_text in ['-', '', 'N/A']:
        return {
            "texto_original": dose_text,
            "valor_min": None,
            "valor_max": None,
            "unidad": "",
            "condicion_suelo": ""
        }

    # Match range patterns like "1.2-1.5 L/ha" or "1,2 - 1,5 L/ha" or "0,8-1,0"
    # Handles various dash types: - – —
    match = re.search(r'([\d]+[.,]?[\d]*)\s*[-–—]\s*([\d]+[.,]?[\d]*)\s*([A-Za-z/]*)', dose_text)
    if match:
        min_str = match.group(1).replace(',', '.')
        max_str = match.group(2).replace(',', '.')
        unit = match.group(3).strip()

        try:
            min_val = float(min_str)
            max_val = float(max_str)
            return {
                "texto_original": dose_text,
                "valor_min": min_val,
                "valor_max": max_val,
                "unidad": unit if unit else "",
                "condicion_suelo": "Según textura"
            }
        except ValueError:
            pass

    # Match single value like "2.0 L/ha" or "2,5 L/ha"
    match = re.search(r'([\d]+[.,]?[\d]*)\s*([A-Za-z/]+)', dose_text)
    if match:
        val_str = match.group(1).replace(',', '.')
        unit = match.group(2).strip()

        try:
            val = float(val_str)
            return {
                "texto_original": dose_text,
                "valor_min": val,
                "valor_max": val,
                "unidad": unit,
                "condicion_suelo": "Según textura"
            }
        except ValueError:
            pass

    # Match number only (no unit) - like "1,5" or "2.0"
    match = re.search(r'([\d]+[.,]?[\d]*)', dose_text)
    if match:
        val_str = match.group(1).replace(',', '.')
        try:
            val = float(val_str)
            return {
                "texto_original": dose_text,
                "valor_min": val,
                "valor_max": val,
                "unidad": "",
                "condicion_suelo": "Según textura"
            }
        except ValueError:
            pass

    # Fallback - could not parse
    return {
        "texto_original": dose_text,
        "valor_min": None,
        "valor_max": None,
        "unidad": "",
        "condicion_suelo": ""
    }


def convert_table_to_schema(
    flattened_table: List[List[str]],
    producto_nombre: str = "",
    archivo_origen: str = ""
) -> Dict[str, Any]:
    """
    Convert flattened table to RAG JSON schema matching afalon_50_sc_adama.json

    Expected table columns (flexible):
    - Cultivo
    - Malezas/Objetivo
    - Dosis
    - Momento/Aplicación
    - Observaciones
    """
    if not flattened_table or len(flattened_table) < 2:
        return {}

    headers = flattened_table[0]
    data_rows = flattened_table[1:]

    # Try to identify columns (case-insensitive)
    col_cultivo = None
    col_malezas = None
    col_dosis = None
    col_momento = None
    col_obs = None

    for i, header in enumerate(headers):
        header_lower = header.lower()
        if 'cultivo' in header_lower:
            col_cultivo = i
        elif 'maleza' in header_lower or 'objetivo' in header_lower:
            col_malezas = i
        elif 'dosis' in header_lower:
            col_dosis = i
        elif 'momento' in header_lower or 'aplicac' in header_lower:
            col_momento = i
        elif 'observ' in header_lower or 'restric' in header_lower:
            col_obs = i

    # Build instrucciones_uso_desagregadas
    instrucciones = []

    for row_idx, row in enumerate(data_rows):
        # Ensure row has enough columns
        while len(row) < len(headers):
            row.append('')

        cultivo = row[col_cultivo] if col_cultivo is not None else ''
        malezas_text = row[col_malezas] if col_malezas is not None else ''
        dosis_text = row[col_dosis] if col_dosis is not None else ''
        momento_text = row[col_momento] if col_momento is not None else ''
        obs_text = row[col_obs] if col_obs is not None else ''

        # Skip empty rows
        if not cultivo.strip():
            continue

        instruccion = {
            "id_fila": row_idx + 1,
            "cultivo_autorizado": cultivo.strip(),
            "tipo_aplicacion": momento_text.strip() if momento_text else "No especificado",
            "malezas_objetivo": parse_weed_list(malezas_text),
            "dosis": parse_dose(dosis_text),
            "momento_aplicacion": {
                "estado_cultivo": momento_text.strip(),
                "estado_maleza": ""
            },
            "observaciones_especificas": obs_text.strip()
        }

        instrucciones.append(instruccion)

    # Build complete schema
    schema = {
        "metadatos_registro": {
            "fecha_procesamiento": date.today().isoformat(),
            "nombre_archivo_origen": archivo_origen,
            "extractor_responsable": "MinerU_Pipeline"
        },
        "identificacion_producto": {
            "nombre_comercial": producto_nombre,
            "tipo_producto": "HERBICIDA",
            "formulacion": "",
            "ingredientes_activos": [],
            "numero_registro_sag": "",
            "clasificacion_hrac": {},
            "titular_distribuidor": ""
        },
        "parametros_tecnicos_globales": {
            "protocolo_aplicacion": {},
            "protocolo_mezcla": {},
            "compatibilidad_quimica": {}
        },
        "instrucciones_uso_desagregadas": instrucciones,
        "restricciones_seguridad": {
            "carencias": [],
            "periodos_reingreso": {},
            "rotacion_cultivos_plantback": []
        }
    }

    return schema


def extract_tables_from_markdown(md_file: str) -> List[str]:
    """Extract HTML tables from markdown file"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = re.findall(r'<table>.*?</table>', content, re.DOTALL)
    return tables


def extract_tables_from_json(json_file: str) -> List[str]:
    """Extract HTML tables from middle.json file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tables = []
    for page in data:
        if 'layout_dets' in page:
            for det in page['layout_dets']:
                if det.get('category_type') == 'table' and 'html' in det:
                    tables.append(det['html'])

    return tables


def main():
    parser = argparse.ArgumentParser(
        description='Convert MinerU tables to RAG JSON schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From markdown
  %(prog)s document.md -o output.json --product "AFALON 50 SC"

  # From middle.json
  %(prog)s path/middle.json -o output.json --product "LINUREX 50 WP"
        """
    )
    parser.add_argument('input', help='Input file (.md or _middle.json)')
    parser.add_argument('-o', '--output', required=True, help='Output JSON file')
    parser.add_argument('--product', default='', help='Product name')
    parser.add_argument('--debug', action='store_true', help='Save flattened tables as CSV for debugging')

    args = parser.parse_args()

    # Extract tables
    if args.input.endswith('.json'):
        print(f"📄 Extracting from JSON: {args.input}")
        html_tables = extract_tables_from_json(args.input)
    elif args.input.endswith('.md'):
        print(f"📄 Extracting from Markdown: {args.input}")
        html_tables = extract_tables_from_markdown(args.input)
    else:
        print("❌ Error: Input must be .json or .md")
        return 1

    if not html_tables:
        print("❌ No tables found")
        return 1

    print(f"✓ Found {len(html_tables)} table(s)")

    # Process tables
    all_schemas = []

    for idx, html_table in enumerate(html_tables):
        print(f"\n📊 Processing table {idx + 1}...")

        # Parse HTML
        parser = TableHTMLParser()
        parser.feed(html_table)

        for table in parser.tables:
            # Flatten merged cells
            flattened = flatten_table(table)

            if not flattened:
                print("  ⚠️  Empty table, skipping")
                continue

            print(f"  ✓ Flattened to {len(flattened)} rows x {len(flattened[0])} cols")

            # Debug: save flattened table
            if args.debug:
                import csv
                debug_file = args.output.replace('.json', f'_table{idx+1}_flattened.csv')
                with open(debug_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(flattened)
                print(f"  📝 Debug CSV: {debug_file}")

            # Convert to schema
            schema = convert_table_to_schema(
                flattened,
                producto_nombre=args.product,
                archivo_origen=args.input
            )

            if schema and schema.get('instrucciones_uso_desagregadas'):
                all_schemas.append(schema)
                print(f"  ✓ Converted {len(schema['instrucciones_uso_desagregadas'])} crop instructions")

    if not all_schemas:
        print("\n❌ No valid schemas generated")
        return 1

    # Save output (merge if multiple tables)
    if len(all_schemas) == 1:
        output_schema = all_schemas[0]
    else:
        # Merge multiple tables into one schema
        output_schema = all_schemas[0]
        for schema in all_schemas[1:]:
            output_schema['instrucciones_uso_desagregadas'].extend(
                schema['instrucciones_uso_desagregadas']
            )

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_schema, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved to: {args.output}")
    print(f"   Total instructions: {len(output_schema['instrucciones_uso_desagregadas'])}")

    return 0


if __name__ == '__main__':
    exit(main())
