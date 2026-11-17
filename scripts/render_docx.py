"""Render the project's Markdown subset into a DOCX while preserving its cover.

Supports paragraphs, three heading levels, pipe tables, equations as quoted
paragraphs, and local PNG figures. No external office automation is required.
"""
import argparse
from copy import deepcopy
import io
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as E
from zipfile import ZipFile

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
PIC = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
q = lambda tag: f'{{{W}}}{tag}'


def node(parent, tag, attributes=None):
    return E.SubElement(parent, q(tag), {q(k): str(v) for k, v in (attributes or {}).items()})


def paragraph(text, level=0, small=False, bold=False, centered=False, first=False):
    p = E.Element(q('p'))
    props = node(p, 'pPr')
    if level:
        node(props, 'pStyle', {'val': f'Heading{level}'})
        node(props, 'keepNext')
        node(props, 'keepLines')
    if first:
        node(props, 'pageBreakBefore')
    node(props, 'spacing', {'before': 180 if level else 0, 'after': 100,
                           'line': 260 if small else 320, 'lineRule': 'auto'})
    node(props, 'jc', {'val': 'center' if centered else ('left' if level or small else 'both')})
    run = node(p, 'r')
    run_props = node(run, 'rPr')
    node(run_props, 'rFonts', {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'cs': 'Times New Roman'})
    node(run_props, 'sz', {'val': 19 if small else (28 if level == 1 else 24)})
    if level or bold:
        node(run_props, 'b')
    t = node(run, 't')
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text
    return p


def table(rows):
    n = len(rows[0])
    if any(len(row) != n for row in rows):
        raise ValueError('Jumlah kolom tabel tidak konsisten.')
    tbl = E.Element(q('tbl'))
    props = node(tbl, 'tblPr')
    node(props, 'tblW', {'w': 9026, 'type': 'dxa'})
    borders = node(props, 'tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        node(borders, edge, {'val': 'single', 'sz': 4, 'color': 'A6A6A6'})
    node(props, 'tblLayout', {'type': 'fixed'})
    margins = node(props, 'tblCellMar')
    for edge in ('top', 'left', 'bottom', 'right'):
        node(margins, edge, {'w': 75, 'type': 'dxa'})
    if n == 7:
        widths = [1950, 420, 1250, 1956, 1250, 950, 1250]
    elif n == 6:
        widths = [2600, 550, 1469, 1469, 1469, 1469]
    elif n == 3:
        widths = [2100, 3463, 3463]
    elif n == 2:
        widths = [3000, 6026]
    else:
        widths = [9026 // n] * n
        widths[-1] += 9026 - sum(widths)
    grid = node(tbl, 'tblGrid')
    for width in widths:
        node(grid, 'gridCol', {'w': width})
    for i, row in enumerate(rows):
        tr = node(tbl, 'tr')
        trprops = node(tr, 'trPr')
        node(trprops, 'cantSplit')
        if i == 0:
            node(trprops, 'tblHeader')
        for text, width in zip(row, widths):
            cell = node(tr, 'tc')
            props = node(cell, 'tcPr')
            node(props, 'tcW', {'w': width, 'type': 'dxa'})
            node(props, 'vAlign', {'val': 'center'})
            if i == 0:
                node(props, 'shd', {'fill': 'E7EDF5'})
            cell.append(paragraph(text, small=True, bold=i == 0))
    return tbl


def png_paragraph(data, relationship_id, drawing_id):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Gambar harus PNG.')
    width, height = struct.unpack('>II', data[16:24])
    scale = min(5_600_000 / width, 6_000_000 / height)
    cx, cy = int(width * scale), int(height * scale)
    p = paragraph('', centered=True)
    props = p.find(q('pPr'))
    node(props, 'keepNext')
    drawing = node(node(p, 'r'), 'drawing')
    inline = E.SubElement(drawing, f'{{{WP}}}inline')
    E.SubElement(inline, f'{{{WP}}}extent', {'cx': str(cx), 'cy': str(cy)})
    E.SubElement(inline, f'{{{WP}}}docPr', {'id': str(drawing_id), 'name': f'Figure {drawing_id}'})
    graphic = E.SubElement(inline, f'{{{A}}}graphic')
    gd = E.SubElement(graphic, f'{{{A}}}graphicData', {'uri': PIC})
    pic = E.SubElement(gd, f'{{{PIC}}}pic')
    nv = E.SubElement(pic, f'{{{PIC}}}nvPicPr')
    E.SubElement(nv, f'{{{PIC}}}cNvPr', {'id': str(drawing_id), 'name': f'figure-{drawing_id}.png'})
    E.SubElement(nv, f'{{{PIC}}}cNvPicPr')
    fill = E.SubElement(pic, f'{{{PIC}}}blipFill')
    E.SubElement(fill, f'{{{A}}}blip', {f'{{{R}}}embed': relationship_id})
    stretch = E.SubElement(fill, f'{{{A}}}stretch')
    E.SubElement(stretch, f'{{{A}}}fillRect')
    sp = E.SubElement(pic, f'{{{PIC}}}spPr')
    xf = E.SubElement(sp, f'{{{A}}}xfrm')
    E.SubElement(xf, f'{{{A}}}off', {'x': '0', 'y': '0'})
    E.SubElement(xf, f'{{{A}}}ext', {'cx': str(cx), 'cy': str(cy)})
    geom = E.SubElement(sp, f'{{{A}}}prstGeom', {'prst': 'rect'})
    E.SubElement(geom, f'{{{A}}}avLst')
    return p


def render(source: Path, markdown: Path, output: Path):
    if source.resolve() == output.resolve():
        raise ValueError('Output harus berbeda dari sumber; simpan dokumen sumber sebagai arsip.')
    with ZipFile(source) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    content = {info.filename: data for info, data in entries}
    # Public manuscript omits student identifiers; source archive is untouched.
    for name, data in content.items():
        if name.endswith('.xml'):
            content[name] = re.sub(rb'\b[A-Z][0-9]{7,}\b', b'[NIM dihapus]', data)
    raw = content['word/document.xml']
    for _, (prefix, uri) in E.iterparse(io.BytesIO(raw), events=['start-ns']):
        if not re.fullmatch(r'ns\d+', prefix):
            E.register_namespace(prefix, uri)
    root = E.fromstring(raw)
    body = root.find(q('body'))
    start = next(i for i, e in enumerate(body) if ''.join(t.text or '' for t in e.iter(q('t'))).startswith('1. Permasalahan:'))
    cover = [deepcopy(e) for e in list(body)[:start]]
    section = deepcopy(body.find(q('sectPr')))
    for element in list(body):
        body.remove(element)
    body.extend(cover)
    relationships = E.fromstring(content['word/_rels/document.xml.rels'])
    types = E.fromstring(content['[Content_Types].xml'])
    media = {}
    lines = markdown.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', v) for v in cells):
                    rows.append(cells)
                i += 1
            body.append(table(rows))
            body.append(paragraph(''))
            continue
        figure = re.fullmatch(r'!\[(.*)\]\((.*)\)', line)
        if figure:
            data = (markdown.parent / figure[2]).read_bytes()
            image_number = 1000 + len(media)
            rid = f'rIdPaperFigure{image_number}'
            if any(rel.get('Id') == rid for rel in relationships):
                raise ValueError(f'ID gambar sudah ada: {rid}')
            filename = f'paper-figure-{image_number}.png'
            media[f'word/media/{filename}'] = data
            E.SubElement(relationships, f'{{{REL}}}Relationship', {
                'Id': rid, 'Type': f'{R}/image', 'Target': f'media/{filename}'})
            body.append(png_paragraph(data, rid, image_number))
            body.append(paragraph(figure[1], small=True, centered=True))
        else:
            heading = re.match(r'^(#{1,3}) (.*)', line)
            if heading:
                body.append(paragraph(heading[2], level=len(heading[1]), first=len(heading[1]) == 1))
            elif line.startswith('> '):
                body.append(paragraph(line[2:], centered=True))
            else:
                body.append(paragraph(line))
        i += 1
    body.append(section)
    # Keep the original namespace declarations used by mc:Ignorable and cover drawings.
    original = raw.decode('utf-8')
    opening = original[:original.index('>', original.index('<w:document')) + 1]
    content['word/document.xml'] = (opening + E.tostring(body, encoding='unicode') + '</w:document>').encode()
    if media:
        if not any(entry.get('Extension') == 'png' for entry in types):
            E.SubElement(types, f'{{{CT}}}Default', {'Extension': 'png', 'ContentType': 'image/png'})
        content['word/_rels/document.xml.rels'] = E.tostring(relationships, encoding='utf-8', xml_declaration=True)
        content['[Content_Types].xml'] = E.tostring(types, encoding='utf-8', xml_declaration=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp.docx')
    with ZipFile(temporary, 'w') as archive:
        for info, _ in entries:
            archive.writestr(info, content[info.filename])
        for name, data in media.items():
            archive.writestr(name, data)
    with ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError('DOCX ZIP rusak.')
        for name in archive.namelist():
            if name.endswith(('.xml', '.rels')):
                E.fromstring(archive.read(name))
        updated = E.fromstring(archive.read('word/document.xml')).find(q('body'))
        for before, after in zip(cover, list(updated)[:len(cover)]):
            if E.tostring(before) != E.tostring(after):
                raise ValueError('Sampul berubah.')
    temporary.replace(output)
    print(f'DOCX valid, sampul dipertahankan, {len(media)} gambar: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('markdown', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    render(args.source, args.markdown, args.output)
