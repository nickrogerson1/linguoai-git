from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2
from ..api_funcs.corrections import find_difference
from fpdf import FPDF
from io import BytesIO

from weasyprint import HTML

from zipfile import ZipFile, ZIP_DEFLATED

from bs4 import BeautifulSoup



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

        self.ln()
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-ExtraLight.ttf')
        self.set_font("Poppins-ExtraLight", size=11)
        self.set_text_color(0,0,0)
        self.multi_cell(0, 6, txt)
        self.ln()

    def add_ielts_res_text(self, txt):
        soup = BeautifulSoup(txt, 'html.parser')
        h3s = soup.find_all('h3')
        ps = soup.find_all('p')
        h5 = soup.find('h5')

        for i in range(4):
            print(h3s[i])
            self.set_text_color(0, 71, 171)
            self.add_font(fname='members/copies/ttf/Poppins/Poppins-Medium.ttf')
            self.set_font('Poppins-Medium', size=14)
            self.cell(0, 6, h3s[i].string)
            self.ln()

            print(ps[i])
            self.add_font(fname='members/copies/ttf/Poppins/Poppins-ExtraLight.ttf')
            self.set_font("Poppins-ExtraLight", size=11)
            self.set_text_color(0,0,0)
            # print(f'TYPE: {type(ps[i]).string}')
            self.multi_cell(0, 6, ps[i].string)
            self.ln()
        
        self.set_text_color(0, 0, 0)
        self.add_font(fname='members/copies/ttf/Poppins/Poppins-Light.ttf')
        self.set_font('Poppins-Medium', size=11)
        self.multi_cell(0, 6, h5.string)
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
        self.add_heading(f'Overall Band {band}')
        self.add_ielts_res_text(score_res)
        self.add_ielts_body(question, 'q')
        self.add_ielts_body(answer, 'a')


# To format the dates
def suffix(d):
    return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

def custom_strftime(t):
    date_format = '%A {S} %B %Y at %-I:%M %p'
    return t.strftime(date_format).replace('{S}', str(t.day) + suffix(t.day))

def get_pdf(sub_type, user, pk, base_uri, type=True, multi=False):
    
    pdf = PDF()

    if sub_type == 'corrected-results':
        look_up = CorrectedSubmission.objects.get(pk=pk)

    # Side by side corrections
        if type:
            sub = look_up.submission
            result = look_up.result
            date = look_up.time_created

            corrections = find_difference(sub, result)
            template = get_template('members/pdfs/corrected-submission.html')
            html = template.render({ 'corrections' : corrections, 'date' : date })
            pdf = HTML(string=html,base_url=base_uri).write_pdf()
            filename = f'{user}-parallel-corrections-{pk}.pdf'

            if multi:
                return [pdf, filename]
        
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        else:
            sub = look_up.submission.replace('<br>', '\n')
            corrected = look_up.result.replace('<br>', '\n')
            filename = f'{user}-split-corrected-{pk}.pdf'
            pdf.make_section("Your Corrected Work", corrected)
            pdf.make_section("Your Original Work", sub)
    
    elif sub_type == 'improved-results':

        look_up = ImprovedSubmission.objects.get(pk=pk)
        sub = look_up.submission.replace('<br>', '\n')
        improved = look_up.improved_sub.replace('<br>', '\n')
        filename = f'{user}-improved-{pk}.pdf'
        pdf.make_section("Your Improved Work", improved)
        pdf.make_section("Your Original Work", sub)
    
    else:
        look_up = IeltsWritingTask2.objects.get(pk=pk)
        
        question = look_up.question
        answer = look_up.answer.replace('<br>', '\n')
        # print(f'LOOK UP: {look_up.score_res}')
        score_res = look_up.score_res.replace('<br>', '\n')

        band = look_up.band
        filename = f'{user}-ielts-writing-task-2-{pk}.pdf'
        pdf.make_ielts(question,answer,score_res,band)


    date = custom_strftime(look_up.time_created)
    pdf.add_date(date)
    # Need to convert it to bytes and save as new var
    pdf = bytes(pdf.output())

    if multi:
        return [pdf, filename]
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
    



# Handler function for single PDF requests
def get_pdf_version(request, pk, type=False):
    sub_type = request.path.split('/')[1]
    user = request.user.username
    if type:
        type = int(type)

    base_uri = request.build_absolute_uri()
    return get_pdf(sub_type, user, pk, base_uri, type)




def get_bulk_pdf(request, pks, type=False):

    if type:
        type = int(type)

    sub_type = request.path.split('/')[1]
    user = request.user.username

    # origin = request.path.split('/')[1]
    if sub_type == 'corrected-results':
        filename = f'{user}-pdf-corrections.zip'
    elif sub_type == 'improved-results':
        filename = f'{user}-pdf-improved.zip'
    else:
        filename = f'{user}-pdf-ielts-writing-task-2.zip'
        
    base_uri = request.build_absolute_uri()
        
    # Ignore last one as it's empty
    pks = pks.split('/')[:-1]
    print(f'PKS: {pks}')

    # if just one file, return as is 
    if len(pks) == 1:
        return get_pdf(sub_type, user, pks[0], base_uri)

    # Otherwise zip them
    buffer = BytesIO()

    base_uri = request.build_absolute_uri()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pk in pks:
            fetch_file = get_pdf(sub_type, user, pk, base_uri, type, multi=True)
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
    
    base_uri = request.build_absolute_uri()

    # # Otherwise zip them
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pair in pairs:
            fetch_file = get_pdf(pair[0], user, pair[1], base_uri, multi=True)
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