"""Rebuild the article as editable Word text, code, links, and pictures."""
from pathlib import Path
import re
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Mm, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/docx/article.docx'
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.top_margin, sec.bottom_margin = Pt(57), Pt(55)
sec.left_margin = sec.right_margin = Pt(55)
sec.header_distance = sec.footer_distance = Pt(25)
width = sec.page_width - sec.left_margin - sec.right_margin

def set_style(name, font='Segoe UI', size=11, bold=False, color='263446'):
    style = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = font
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor.from_string(color)
    style.paragraph_format.widow_control = True
    return style

normal = set_style('Normal')
normal.paragraph_format.line_spacing = Pt(15.4)
normal.paragraph_format.space_after = Pt(8.5)
title = set_style('Title', size=26, bold=True, color='000000')
title.paragraph_format.line_spacing = Pt(31)
title.paragraph_format.space_after = Pt(18)
title.paragraph_format.keep_with_next = True
heading = set_style('Heading 1', size=15, bold=True, color='000000')
heading.paragraph_format.line_spacing = Pt(19)
heading.paragraph_format.space_before = Pt(13)
heading.paragraph_format.space_after = Pt(8)
heading.paragraph_format.keep_with_next = True
caption = set_style('Caption', size=9, color='607087')
caption.font.italic = True
caption.paragraph_format.line_spacing = Pt(12)
caption.paragraph_format.space_before = Pt(5)
caption.paragraph_format.space_after = Pt(12)
code = set_style('Article Code', font='Consolas', size=8.5)
code.paragraph_format.line_spacing = Pt(11.7)
code.paragraph_format.space_before = Pt(6)
code.paragraph_format.space_after = Pt(12)
code.paragraph_format.left_indent = Pt(10)
code.paragraph_format.right_indent = Pt(10)
code.paragraph_format.keep_together = True
code.paragraph_format.widow_control = True
code_props = code.element.get_or_add_pPr()
shade = OxmlElement('w:shd')
shade.set(qn('w:fill'), 'F1F5F9')
code_props.append(shade)

header = sec.header.paragraphs[0]
header.paragraph_format.space_after = Pt(0)
run = header.add_run('FLEET COMMAND')
run.font.name, run.font.size, run.bold = 'Segoe UI', Pt(8), True
run.font.color.rgb = RGBColor(0, 0, 0)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
footer.style.font.size = Pt(8)

def hyperlink(p, label, url):
    link = OxmlElement('w:hyperlink')
    link.set(qn('r:id'), p.part.relate_to(url, RT.HYPERLINK, is_external=True))
    r = OxmlElement('w:r')
    rp = OxmlElement('w:rPr')
    c = OxmlElement('w:color'); c.set(qn('w:val'), '006CA3'); rp.append(c)
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rp.append(u)
    r.append(rp)
    t = OxmlElement('w:t'); t.text = label; r.append(t)
    link.append(r)
    p._p.append(link)

inline_pattern = re.compile(r'(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\(https?://[^)]+\)|\*[^*]+\*)')
def inline(p, text):
    for part in inline_pattern.split(text):
        if not part:
            continue
        if part.startswith('`') and part.endswith('`'):
            r = p.add_run(part[1:-1]); r.font.name = 'Consolas'; r.font.size = Pt(10)
            r.font.color.rgb = RGBColor.from_string('254C6D')
        elif part.startswith('**') and part.endswith('**'):
            p.add_run(part[2:-2]).bold = True
        elif part.startswith('*') and part.endswith('*'):
            p.add_run(part[1:-1]).italic = True
        elif part.startswith('['):
            m = re.fullmatch(r'\[([^\]]+)\]\((https?://[^)]+)\)', part)
            hyperlink(p, m[1], m[2])
        else:
            p.add_run(part)

# A real Word numbered list remains editable when a takeaway is added or moved.
numbering = doc.part.numbering_part.element
abstract_ids = [int(x.get(qn('w:abstractNumId'))) for x in numbering.findall(qn('w:abstractNum'))]
abstract_id = max(abstract_ids, default=0) + 1
abstract = OxmlElement('w:abstractNum'); abstract.set(qn('w:abstractNumId'), str(abstract_id))
lvl = OxmlElement('w:lvl'); lvl.set(qn('w:ilvl'), '0')
for tag, val in [('w:start','1'),('w:numFmt','decimal'),('w:lvlText','%1.'),('w:lvlJc','left')]:
    node=OxmlElement(tag); node.set(qn('w:val'),val); lvl.append(node)
pp=OxmlElement('w:pPr'); ind=OxmlElement('w:ind')
ind.set(qn('w:left'),'360'); ind.set(qn('w:hanging'),'360'); pp.append(ind); lvl.append(pp)
abstract.append(lvl); numbering.append(abstract)
num_id=numbering.add_num(abstract_id).numId

source=(ROOT/'article.md').read_text(encoding='utf-8-sig')
lines=source.splitlines()
index=0
while index < len(lines):
    line=lines[index].strip()
    if not line:
        index+=1; continue
    if line.startswith('```'):
        index+=1; code_lines=[]
        while index<len(lines) and not lines[index].startswith('```'):
            code_lines.append(lines[index]); index+=1
        doc.add_paragraph('\n'.join(code_lines),style='Article Code')
        index+=1; continue
    if line.startswith('# '):
        p=doc.add_paragraph(style='Title')
        inline(p,line[2:].replace(' With Cross-Platform',' With\nCross-Platform'))
        index+=1; continue
    if line.startswith('## '):
        doc.add_paragraph(line[3:],style='Heading 1'); index+=1; continue
    image=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',line)
    if image:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=True
        p.paragraph_format.space_before=Pt(5)
        p.paragraph_format.space_after=Pt(0)
        p.paragraph_format.line_spacing=1.0
        picture=p.add_run().add_picture(image[2],width=width)
        picture._inline.docPr.set('descr',image[1])
        picture._inline.docPr.set('title',Path(image[2]).stem)
        index+=1; continue
    if re.fullmatch(r'\*[^*]+\*',line):
        inline(doc.add_paragraph(style='Caption'),line); index+=1; continue
    body=[line]; index+=1
    while index<len(lines) and lines[index].strip():
        body.append(lines[index].strip()); index+=1
    raw=' '.join(body)
    p=doc.add_paragraph()
    match=re.match(r'^\d+\. (.*)',raw)
    if match:
        raw=match[1]
        props=p._p.get_or_add_pPr().get_or_add_numPr()
        props.get_or_add_ilvl().val=0; props.get_or_add_numId().val=num_id
    inline(p,raw)
    following=index
    while following<len(lines) and not lines[following].strip(): following+=1
    if following<len(lines) and lines[following].startswith('```'):
        p.paragraph_format.keep_with_next=True

doc.core_properties.title=lines[0][2:]
doc.core_properties.subject='Verified support tickets and Hindsight memory'
doc.core_properties.author=''
doc.core_properties.last_modified_by=''
doc.core_properties.comments=''
settings=doc.settings.element
do_not_compress=OxmlElement('w:doNotAutoCompressPictures')
settings.append(do_not_compress)
# Remove inherited title rules from the bundled Word default template.
for tree in (doc.styles.element, doc.element):
    for border in tree.xpath('.//w:pBdr'):
        border.getparent().remove(border)
doc.save(OUT)
print(OUT)
print(f'{len(doc.inline_shapes)} independent picture objects; {len(doc.paragraphs)} editable paragraphs')
