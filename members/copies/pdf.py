from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2
from ..api_funcs.corrections import find_difference
import pdfkit


# Main processing function for individual PDFs 
# @login_required(login_url="/login/")
def get_pdf(sub_type, user, pk, type=None, multi=False, sub=None):

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
