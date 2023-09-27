from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2
from ..api_funcs.corrections import find_difference
from fpdf import FPDF
from io import BytesIO

# NOTE: 
# Standard Corrected PDF doesn't work. Everything else works including bulk.



class PDF(FPDF):
    def header(self):
    # Reset margins for each page
        self.set_margins(left=1,right=-1, top=1)
        self.add_font(fname='members/copies/ttf/JetBrainsMono/JetBrainsMono-Light.ttf')
        self.set_font("JetBrainsMono-Light", "", 15)
        self.set_text_color(37,37,37)
        self.cell(0, 10, txt='linguo::ai')
        self.set_margins(left=25,right=25, top=5)
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_text_color(128)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_heading(self, txt):
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-Light.ttf')
        self.set_font("Poppins-Light", size=25)
        self.set_text_color(0, 71, 171)
        self.cell(txt=txt, center=True)
        self.ln(15)
        
    def add_body(self, txt):
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-ExtraLight.ttf')
        self.set_font("Poppins-ExtraLight", size=11)
        self.set_text_color(0,0,0)
        # self.multi_cell(0, 6, txt)
        self.write_html(txt)
        self.ln()

    def add_ielts_body(self, txt, type):
        self.set_text_color(0, 71, 171)
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-Medium.ttf')
        self.set_font('Poppins-Medium', size=14)
        if type == 'q':
            self.cell(0, 6, 'Your Question:')
        elif type == 'a':
            self.cell(0, 6, 'Your Answer:')
        else:
            self.cell(0, 6, 'Detailed Explanation:')
            # self.ln()

        self.ln()
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-ExtraLight.ttf')
        self.set_font("Poppins-ExtraLight", size=11)
        self.set_text_color(0,0,0)
        self.multi_cell(0, 6, txt)
        self.ln()

    def add_date(self, date):
        self.ln(15)
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-Medium.ttf')
        self.set_font("Poppins-Medium", size=12)
        self.set_text_color(0, 71, 171)
        txt = f'This submission was made on {date} UTC.'
        self.cell(txt=txt)

    def make_section(self, heading, content):
        self.add_page()
        self.add_heading(heading)
        self.add_body(content)

    def make_ielts(self,question,answer,score_res,band):
        self.add_page()
        self.add_heading(f'Band {band}')
        self.add_ielts_body(score_res, 'r')
        self.add_ielts_body(question, 'q')
        self.add_ielts_body(answer, 'a')


# To format the dates
def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def custom_strftime(t):
    date_format = '%A {S} %B %Y at %-I:%M %p'
    return t.strftime(date_format).replace('{S}', str(t.day) + suffix(t.day))

def get_pdf(sub_type, user, pk, type=None, multi=False):
    
    pdf = PDF()

    if sub_type == 'corrected-results':

        look_up = CorrectedSubmission.objects.get(pk=pk)
        sub = look_up.submission.replace('<br>', '\n')
        corrected = look_up.result.replace('<br>', '\n')
        date = custom_strftime(look_up.time_created)
        filename = f'{user}-corrected-{pk}.pdf'


# This should probably be changed at the template level
# Only one option at the moment as PDF kit too slow
        if(type):
# This section is reserved for printing the PDF in the side by side format
            corrections = find_difference(sub, corrected)
            template = get_template('members/pdfs/corrected-submission.html')
            html = template.render({ 'corrections' : corrections, 'date' : date })

            # pdf.make_section("Your Corrected Work", corrections)
            print('Converting...')
            # s = BytesIO()
            # pdf = converter.convert('https://linguo.ai', s)



        else:
            pdf.make_section("Your Corrected Work", corrected)
            pdf.make_section("Your Original Work", sub)
            pdf.add_date(date)
        # Need to convert it to bytes and save as new var
            pdf = bytes(pdf.output())

        if multi:
            return [pdf, filename]
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    elif sub_type == 'improved-results':

        look_up = ImprovedSubmission.objects.get(pk=pk)
        sub = look_up.submission.replace('<br>', '\n')
        improved = look_up.improved_sub.replace('<br>', '\n')
        date = custom_strftime(look_up.time_created)
        filename = f'{user}-improved-{pk}.pdf'

        pdf.make_section("Your Improved Work", improved)
        pdf.make_section("Your Original Work", sub)
        pdf.add_date(date)
        # Need to convert it to bytes and save as new var
        pdf = bytes(pdf.output())

        if multi:
            return [pdf, filename]
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    else:

        look_up = IeltsWritingTask2.objects.get(pk=pk)
        question = look_up.question
        answer = look_up.answer.replace('<br>', '\n')
        score_res = look_up.score_res.replace('<br>', '\n')
        band = look_up.band
        date = custom_strftime(look_up.time_created)
        filename = f'{user}-ielts-writing-task-2-{pk}.pdf'


        pdf.make_ielts(question,answer,score_res,band)
        
        pdf.add_date(date)
        # Need to convert it to bytes and save as new var
        pdf = bytes(pdf.output())

        if multi:
            return [pdf, filename]
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    


from weasyprint import HTML
import time

# Handler function for single PDF requests
def get_pdf_version(request, pk, type):
    sub_type = request.path.split('/')[1]
    user = request.user.username

    # If it's positive then they want the side-by-side version
    check_type = int(type)

    if check_type:
        print('Side-by-side')
        
        look_up = CorrectedSubmission.objects.get(pk=pk)
        sub = look_up.submission
        result = look_up.result
        date = look_up.time_created

        # if(type):
        corrections = find_difference(sub, result)
        template = get_template('members/pdfs/corrected-submission.html')
        html = template.render({ 'corrections' : corrections, 'date' : date })

        t0 = time.time()



        pdf = HTML(string=html).write_pdf()

        t1 = time.time()

        print(f'TIME TAKEN: {t1-t0}')


        split = '' if type else 'split-'
        filename = f'{user}-{split}corrections-{pk}.pdf'

        # if multi:
        #     return [pdf, filename]

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return get_pdf(sub_type, user, pk, type)



from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from django.http import HttpResponse


def get_bulk_pdf(request, pks, type=None):

    sub_type = request.path.split('/')[1]
    user = request.user.username

    # origin = request.path.split('/')[1]
    if sub_type == 'corrected-results':
        filename = f'{user}-pdf-corrections.zip'
    elif sub_type == 'improved-results':
        filename = f'{user}-pdf-improved.zip'
    else:
        filename = f'{user}-pdf-ielts-writing-task-2.zip'
        

    # Ignore last one as it's empty
    pks = pks.split('/')[:-1]
    print(f'PKS: {pks}')

    # if just one file, return as is 
    if len(pks) == 1:
        return get_pdf(sub_type, user, pks[0])

    # Otherwise zip them
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pk in pks:
            fetch_file = get_pdf(sub_type, user, pk, multi=True)
            pdf = fetch_file[0]
            lf = fetch_file[1]
            b = BytesIO(pdf)
            f.writestr(lf, b.getvalue())

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'application/zip'
    }
        
    return HttpResponse(buffer.getvalue(), headers=headers)




# When called from the submission log
def get_bulk_mixed_pdf(request, url_str):
    user = request.user.username
    filename = f'{user}-pdfs.zip'
    url_list = url_str.split("/")[:-1]

    # # Split them into chunks
    pairs = [url_list[i:i+2] for i in range(0, len(url_list),2)]
    print(f'Pairs: {pairs}')
    # [['corrected-results', '134']]
    # sub_type, pk

    # # if just one file, return as is 
    if len(pairs) == 1:
        return get_pdf(pairs[0][0], user, pairs[0][1])

    # # Otherwise zip them
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pair in pairs:
            fetch_file = get_pdf(pair[0], user, pair[1], multi=True)
            # get_pdf(sub_type, user, pk, type=None, multi=False)
            pdf = fetch_file[0]
            fn = fetch_file[1]
            b = BytesIO(pdf)
            f.writestr(fn, b.getvalue())

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'application/zip'
    }
        
    return HttpResponse(buffer.getvalue(), headers=headers)