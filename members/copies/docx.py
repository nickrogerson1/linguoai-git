import os
from io import BytesIO, StringIO
from html.parser import HTMLParser
from lxml import html, etree

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

import pypandoc
from docx import Document
from copy import deepcopy
from bs4 import BeautifulSoup
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2

import re

import pathlib

# Strip out any HTML tags in strings
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()
    
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


@login_required(login_url="/login/")
def get_docx(request, pk):

    origin = request.path.split('/')[1]
    user = request.user
    date_format = '%A %-d %B %Y at %-I:%M %p'
    
    if origin == 'corrected-results':

        look_up = CorrectedSubmission.objects.get(pk=pk)
        corrections = look_up.corrections
        date = look_up.time_created.strftime(date_format)

        corrections = (corrections.replace(' </span>', '</span> ')
                        .replace('<span class="diff_chg"> ', ' <span class="diff_chg">')
                        .replace('<span class="diff_sub"> ', ' <span class="diff_sub">')
                        .replace('<span class="diff_add"> ', ' <span class="diff_add">'))
        
        
    # Replace heading as colspan not supported
        table = html.fragment_fromstring(corrections)
        new_header = etree.fromstring('''
            <thead id="main-table">
                <tr>
                    <th></th>
                    <th><strong>Original</strong></th>
                    <th></th>
                    <th><strong>Edited</strong></th>
                </tr>
            </thead>
            ''')
        
        for el in table.getchildren():
            if el.tag == 'thead':
                el.getparent().replace(el, new_header)

        modified_header = html.tostring(table).decode('utf-8')
        
    # Change the classes over to suit the needs of Pandoc
        changed_classes = (modified_header.replace('class="diff_chg"', 'custom-style="Red"')
                        .replace('class="diff_sub"', 'custom-style="Yellow"')
                        .replace('class="diff_add"', 'custom-style="Green"'))
        
       

        print(changed_classes)

    # No other option but to save, reload and delete this file
        output = pypandoc.convert_text(source=changed_classes, format='html', to='markdown')
        filename = f'{user}-corrections-{pk}.docx'
    # Keep it in the copies directory although doesn't really matter
        file_path = f'{str(pathlib.Path(__file__).parent.resolve())}/{filename}'
        pypandoc.convert_text(source=output, format='markdown', to='docx', outputfile=file_path, extra_args=['--reference-doc=members/copies/docx_template.docx'])

    # Overwrite the existing styles to preserve the original styles
        doc = Document(file_path)
        doc_deep = deepcopy(doc)
        
    # # Clear it then rebuild it
        for element in doc.element.body:
            element.clear()

    # Rebuild the doc
        doc.add_heading('Corrected Version')
        for element in doc_deep.element.body:
            print(element)
            doc.element.body.append(element)

        doc.add_heading(f'This submission was made on {date}', 3)
            
        # Stream it and prepare for sending
        stream = BytesIO()
        doc.save(stream)
        stream.seek(0)

        response = HttpResponse(stream, content_type='application/vnd.openxmlformats')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        os.remove(file_path)
        stream.close()
        return response
    
    elif origin == 'improved-results':

        look_up = ImprovedSubmission.objects.get(pk=pk)
        sub = strip_tags(look_up.submission)
        improved = strip_tags(look_up.improved_sub)
        date = look_up.time_created.strftime(date_format)
    
    # Build document
        doc = Document()
        doc.add_heading('Improved Version')
        doc.add_paragraph(improved)
        doc.add_page_break()
        doc.add_heading('Original Version')
        doc.add_paragraph(sub)
        doc.add_heading(f'This submission was made on {date}', 3)
        
    # Stream it and prepare for sending
        stream = BytesIO()
        doc.save(stream)
        stream.seek(0)
        
        filename = f'{user}-improved-{pk}.docx'

        response = HttpResponse(stream, content_type='application/vnd.openxmlformats')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    # Can only be IELTS left 
    else:
        
        look_up = IeltsWritingTask2.objects.get(pk=pk)
        question = strip_tags(look_up.question)
        answer = strip_tags(look_up.answer)
        score_res = BeautifulSoup(look_up.score_res).get_text('\n')
        band = look_up.band
        date = look_up.time_created.strftime(date_format)
    
    # Build document
        doc = Document()
        doc.add_heading(f'Ielts Writing Task 2 - Band {band}')
        doc.add_heading('Submitted Question')
        doc.add_paragraph(question)
        doc.add_heading('Score Resolution')
        doc.add_paragraph(score_res)
        doc.add_heading('Your Original Answer')
        doc.add_paragraph(answer)
        doc.add_heading(f'This submission was made on {date} (UTC)', 3)
        
    # Stream it and prepare for sending
        stream = BytesIO()
        doc.save(stream)
        stream.seek(0)
        
        filename = f'{user}-ielts-writing-task-2-{pk}-result.docx'

        response = HttpResponse(stream, content_type='application/vnd.openxmlformats')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
