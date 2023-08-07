from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2
import pdfkit


@login_required(login_url="/login/")
def get_pdf(request, pk):

    origin = request.path.split('/')[1]
    user = request.user
    options={"enable-local-file-access" : False}


    if origin == 'corrected-results':
        print(origin)
        look_up = CorrectedSubmission.objects.get(pk=pk)
        corrections = look_up.corrections
        date = look_up.time_created

        template = get_template('members/pdfs/corrected-submission.html')
        html = template.render({ 'corrections' : corrections, 'date' : date })

        pdf = pdfkit.from_string(html, options=options)
        filename = f'{user}-corrections-{pk}.pdf'

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    if origin == 'improved-results':

        look_up = ImprovedSubmission.objects.get(pk=pk)
        sub = look_up.submission
        improved = look_up.improved_sub
        date = look_up.time_created

        template = get_template('members/pdfs/improved-submission.html')
        html = template.render({ 'sub' : sub, 'improved' : improved, 'date' : date })
        pdf = pdfkit.from_string(html, options=options)
        filename = f'{user}-improved-{pk}.pdf'

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

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response