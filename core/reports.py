"""Readable, paginated PDF reports. No network or temporary server files."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
FONT_DIR=Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('Cestas',str(FONT_DIR/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('CestasBold',str(FONT_DIR/'VeraBd.ttf')))
BRAND=colors.HexColor('#1693A5')
def families_pdf(rows,institute,issued_at,author,filters='Todas as famílias'):
    output=BytesIO();page=landscape(A4);width=page[0]-84
    doc=SimpleDocTemplate(output,pagesize=page,rightMargin=36,leftMargin=36,topMargin=42,bottomMargin=44,title='Relatório de famílias',author=institute)
    normal=ParagraphStyle('normal',fontName='Cestas',fontSize=9,leading=13,textColor=colors.HexColor('#000000'),splitLongWords=True)
    small=ParagraphStyle('small',parent=normal,fontSize=8,leading=11)
    title=ParagraphStyle('title',parent=normal,fontName='CestasBold',fontSize=23,leading=29,textColor=colors.black,spaceAfter=8)
    def text(value,style=normal):return Paragraph(escape(str(value)),style)
    story=[text(institute,ParagraphStyle('brand',parent=normal,fontName='CestasBold',fontSize=11,spaceAfter=14)),text('Relatório de famílias',title),text(f'Emitido em {issued_at:%d/%m/%Y às %H:%M} | Responsável pela emissão: {author}',small),Spacer(1,8),text('Seleção: '+filters,small),Spacer(1,18)]
    active=sum(r['state']!='encerrado' for r in rows);pending=sum(r['state']=='disponivel' for r in rows)
    labels=[('Famílias listadas',len(rows)),('Em atendimento',active),('Podem retirar',pending),('Encerradas',len(rows)-active)]
    cards=Table([[Paragraph(f'<font size="19">{number}</font><br/>{escape(label)}',normal) for label,number in labels]],colWidths=[width/4]*4)
    cards.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F0F0D8')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#D8D8C0')),('LEFTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    story.extend([cards,Spacer(1,22)])
    if rows:
        head=ParagraphStyle('head',parent=small,fontName='CestasBold',textColor=colors.black)
        data=[[text(h,head) for h in ['Família','Responsável','Contato e endereço','Início original','Fim do benefício','Situação atual']]]
        for row in rows:
            f=row['family'];contact=(f.phone or 'Telefone não informado')+'\n'+f.address
            data.append([text(f'F{f.pk:05d}',small),text(f.responsible.name),Paragraph(escape(contact).replace('\n','<br/>'),small),text(f.benefit.original_start.strftime('%d/%m/%Y'),small),text(row['end'].strftime('%d/%m/%Y'),small),text(row['label'],small)])
        table=Table(data,colWidths=[52,156,218,76,76,width-578],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BRAND),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F0D8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,BRAND),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D8D8C0')),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
        story.append(table)
    else:story.extend([text('Nenhuma família encontrada para esta seleção.'),Spacer(1,14),text('Altere os filtros e gere o relatório novamente.',small)])
    story.extend([Spacer(1,16),text('Uma cesta por período, durante seis períodos consecutivos. Faltas não acumulam nem prolongam o benefício. Este relatório não substitui o backup completo.',small)])
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#D8D8C0'));canvas.line(36,33,page[0]-36,33);canvas.setFont('Cestas',7);canvas.setFillColor(colors.HexColor('#000000'));canvas.drawString(36,21,'Uso interno - contém dados pessoais. Guarde em local privado.');canvas.drawRightString(page[0]-36,21,f'Página {doc.page}');canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()

