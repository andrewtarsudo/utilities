# -*- coding: utf-8 -*-
import re
from typing import List, Dict, Optional, Tuple


def find_tables(text: str) -> List[str]:
    """
    Finds all Markdown and AsciiDoc tables in the input text and returns them as a list of table strings.
    Markdown tables: header |...|, separator |---|..., rows
    AsciiDoc tables: start with |===, end with |===
    """
    tables = []

    # Find Markdown tables
    md_pattern = re.compile(
        r'(?:^\s*\|.*\|\s*\n'  # header
        r'(?:^\s*\|[\s:\-]+\|\s*\n)'  # separator
        r'(?:^\s*\|.*\|\s*\n?)+)',  # at least one row
        re.MULTILINE | re.VERBOSE
    )
    tables += [match.group(0).strip() for match in md_pattern.finditer(text)]

    # Find AsciiDoc tables
    adoc_pattern = re.compile(
        r'^\s*\|===\s*\n'  # table start
        r'(?:.*\n)*?'  # table content (non-greedy)
        r'^\s*\|===\s*$',  # table end
        re.MULTILINE | re.VERBOSE
    )
    tables += [match.group(0).strip() for match in adoc_pattern.finditer(text)]

    return tables


def read_table(text: str) -> List[Dict[str, str]]:
    """
    Parses the input table and returns a list of dicts with keys: Parameter, OMPR, Description
    Supports both Markdown and AsciiDoc tables.
    """
    # Detect AsciiDoc table
    if text.strip().startswith('|==='):
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        # Remove |=== lines
        lines = [line for line in lines if line != '|===']
        if not lines:
            return []
        headers = [h.strip() for h in lines[0].strip('|').split('|')]
        data = []
        for line in lines[1:]:
            if not line.startswith('|'):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) != len(headers):
                continue
            row = dict(zip(headers, cells))
            data.append(row)
        return data
    else:
        # Markdown table
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        header_idx = None
        sep_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^\s*\|', line):
                header_idx = i
                if i + 1 < len(lines) and re.match(r'^\s*\|?[\s:-]+\|', lines[i + 1]):
                    sep_idx = i + 1
                break
        if header_idx is None or sep_idx is None:
            raise ValueError("Table header or separator not found")

        headers = [h.strip() for h in lines[header_idx].strip('|').split('|')]
        data = []
        for line in lines[sep_idx + 1:]:
            if not line.startswith('|'):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) != len(headers):
                continue
            row = dict(zip(headers, cells))
            data.append(row)
        return data


def extract_type(description: str) -> Optional[str]:
    match = re.search(r'Тип\s*--\s*(\w+)\.', description)
    return match.group(1) if match else None


def reorder_description(description: str) -> str:
    sentences = re.split(r'(?<=\.)\s+', description.strip())
    if not sentences:
        return description

    first = sentences[0]
    rest = sentences[1:]

    diapason_idx = next((i for i, s in enumerate(rest) if re.match(r'Диапазон:\s*\d+-\d+\.', s)), None)
    default_idx = next(
        (i for i, s in enumerate(rest) if re.match(r'(По умолчанию|Значение по умолчанию)\s*--\s*.+\.', s)), None)

    ordered = [first]
    if diapason_idx is not None:
        ordered.append(rest[diapason_idx])
    if default_idx is not None and default_idx != diapason_idx:
        ordered.append(rest[default_idx])
    for i, s in enumerate(rest):
        if i == diapason_idx or i == default_idx:
            continue
        ordered.append(s)
    return ' '.join(ordered)


def split_ompr(ompr: str) -> Tuple[str, str]:
    om = ompr[0] if len(ompr) > 0 else ''
    pr = ompr[1] if len(ompr) > 1 else ''
    return om, pr


def transform_row(row: Dict[str, str]) -> Dict[str, str]:
    param = row.get('Parameter', '')
    ompr = row.get('OMPR', '')
    desc = row.get('Description', '')

    type_val = extract_type(desc) or ''
    om, pr = split_ompr(ompr)
    desc_reordered = reorder_description(desc)

    return {
        'Параметр': param,
        'Описание': desc_reordered,
        'Тип': type_val,
        'O/M': om,
        'P/R': pr
    }


def transform_table(text: str) -> List[Dict[str, str]]:
    rows = read_table(text)
    return [transform_row(row) for row in rows]


def to_markdown(rows: List[Dict[str, str]]) -> str:
    headers = ['Параметр', 'Описание', 'Тип', 'O/M', 'P/R']
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|']
    for row in rows:
        out.append('| ' + ' | '.join(row.get(h, '') for h in headers) + ' |')
    return '\n'.join(out)


def to_asciidoc(rows: List[Dict[str, str]]) -> str:
    headers = ['Параметр', 'Описание', 'Тип', 'O/M', 'P/R']
    out = ['|===', '| ' + ' | '.join(headers)]
    for row in rows:
        out.append('| ' + ' | '.join(row.get(h, '') for h in headers))
    out.append('|===')
    return '\n'.join(out)


def process_tables_in_text(text: str, input_format: str = "markdown", output_format: Optional[str] = None) -> str:
    """
    Finds all tables in the text, transforms them, and returns the text with tables replaced by their transformed
    versions.
    """
    tables = find_tables(text)
    transformed_tables = []
    for table in tables:
        rows = transform_table(table)
        fmt = output_format or input_format
        if fmt == "markdown":
            transformed = to_markdown(rows)
        elif fmt == "asciidoc":
            transformed = to_asciidoc(rows)
        else:
            raise ValueError("Unknown output format: " + fmt)
        transformed_tables.append((table, transformed))

    # Replace each original table with its transformed version in the text
    new_text = text
    for original, transformed in transformed_tables:
        new_text = new_text.replace(original, transformed)
    return new_text
