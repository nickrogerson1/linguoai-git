from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2
from ..api_funcs.corrections import find_difference
import pdfkit


# Main processing function for individual PDFs 
# @login_required(login_url="/login/")
def old_get_pdf(sub_type, user, pk, type=None, multi=False, sub=None):

    if type:
        type = int(type)

    # sub_type = sub if sub else request.path.split('/')[1]
    # user = request.user
    options={"enable-local-file-access" : False}


    if sub_type == 'corrected-results':
        
        look_up = CorrectedSubmission.objects.get(pk=pk)
        sub = look_up.submission
        result = look_up.result
        date = look_up.time_created

        if(type):
            corrections = find_difference(sub, result)
            template = get_template('members/pdfs/corrected-submission.html')
            html = template.render({ 'corrections' : corrections, 'date' : date })
        else:
            template = get_template('members/pdfs/standard-submission.html')
            html = template.render({ 'corrected' : True, 'sub' : sub, 'result' : result, 'date' : date })

        pdf = pdfkit.from_string(html, options=options)
        split = '' if type else 'split-'
        filename = f'{user}-{split}corrections-{pk}.pdf'

        if multi:
            return [pdf, filename]

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    if sub_type == 'improved-results':

        look_up = ImprovedSubmission.objects.get(pk=pk)
        sub = look_up.submission
        improved = look_up.improved_sub
        date = look_up.time_created

        template = get_template('members/pdfs/standard-submission.html')
        html = template.render({ 'sub' : sub, 'result' : improved, 'date' : date })
        pdf = pdfkit.from_string(html, options=options)
        filename = f'{user}-improved-{pk}.pdf'

        print(f'Type: {type(pdf)}')

        if multi:
            return [pdf, filename]
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    # Can only be IELTS
    else:
        look_up = IeltsWritingTask2.objects.get(pk=pk)
        question = look_up.question
        answer = look_up.answer
        score_res = look_up.score_res
        band = look_up.band
        date = look_up.time_created

        cxt = {
            'question' : question,
            'answer' : answer,
            'score_res' : score_res,
            'band' : band,
            'date' : date
        }

        template = get_template('members/pdfs/ielts-form-submission.html')
        html = template.render( cxt )
        pdf = pdfkit.from_string(html, options=options)
        filename = f'{user}-ielts-writing-task-2-result-{pk}.pdf'

        if multi:
            return [pdf, filename]

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    

# Helper function to handle raw data
def get_pdf_version(request, pk, type=None):
    sub_type = request.path.split('/')[1]
    user = request.user.username
    return get_pdf(sub_type, user, pk, type=type)











from fpdf import FPDF


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
            self.ln()

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



def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def custom_strftime(t):
    date_format = '%A {S} %B %Y at %-I:%M %p'
    return t.strftime(date_format).replace('{S}', str(t.day) + suffix(t.day))



from io import BytesIO

def get_pdf(request, pk, type=None, sub=None):

    sub_type = sub if sub else request.path.split('/')[1]
    user = request.user
    multi = None
    filename = f'{user}-improved-{pk}.pdf'
    
    pdf = PDF()

    if sub_type == 'corrected-results':

        look_up = CorrectedSubmission.objects.get(pk=pk)
        sub = look_up.submission.replace('<br>', '\n')
        corrected = look_up.result.replace('<br>', '\n')
        date = custom_strftime(look_up.time_created)


        if(type):
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


        pdf.make_ielts(question,answer,score_res,band)
        
        pdf.add_date(date)
        # Need to convert it to bytes and save as new var
        pdf = bytes(pdf.output())

        if multi:
            return [pdf, filename]
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response