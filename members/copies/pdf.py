from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..views import CorrectedSubmission, ImprovedSubmission, IeltsWritingTask2
from ..api_funcs.corrections import find_difference
import pdfkit


@login_required(login_url="/login/")
def get_pdf(request, pk, type=None, multi=False):
    print(f'Type {type}')
    if type:
        type = int(type)
    origin = request.path.split('/')[1]
    user = request.user
    options={"enable-local-file-access" : False}


    if origin == 'corrected-results':
        print(origin)
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
    
    if origin == 'improved-results':

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
    



from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO

def get_bulk_pdf(request, pks, type=None):

    origin = request.path.split('/')[1]
    if origin == 'corrected-results':
        filename = f'{request.user}-pdf-corrections.zip'
    elif origin == 'improved-results':
        filename = f'{request.user}-pdf-improved.zip'
    else:
        filename = f'{request.user}-pdf-ielts-writing-task-2.zip'
        

    # Ignore last one as it's empty
    pks = pks.split('/')[:-1]
    print(f'PKS: {pks}')

    # if just one file, return as is 
    if len(pks) == 1:
        return get_pdf(request, pks[0], type)

    # Otherwise zip them
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pk in pks:
            fetch_file = get_pdf(request, pk, type, multi=True)
            pdf = fetch_file[0]
            lf = fetch_file[1]
            b = BytesIO(pdf)
            f.writestr(lf, b.getvalue())

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'application/zip'
    }
        
    return HttpResponse(buffer.getvalue(), headers=headers)
    