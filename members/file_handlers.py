from io import BytesIO
import docx
from striprtf.striprtf import rtf_to_text
import fitz
from zipfile import ZipFile
import time

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .views import BalanceCheckMixin, FormView
from .forms import FileFieldForm
from .tasks import get_corrected_results, get_improved_results, r
from django.http import HttpResponse



class FileFieldFormView(BalanceCheckMixin,FormView):
    
    form_class = FileFieldForm
    template_name = 'members/home/input-form-general.html'
    success_url = 'upload-success.html' 


    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        t0 = time.time()
        user_id = request.user.id


    # MAKE SURE DATA GETS SANITISED!
        if form.is_valid():
            return self.form_valid(form, t0, user_id)
        else:
            return self.form_invalid(form)

    def form_valid(self, form, t0, user_id):

        file = self.request.FILES['file']
        file_type = file.content_type
        # print(file_type)
        if file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            sub = self.get_docx_text(file)
            res = self.process_text(t0,sub)            

        elif file_type == 'application/pdf':
            sub = self.get_pdf_text(file)
            res = self.process_text(t0,sub)

        elif file_type == 'text/rtf':
            print(f'Type: {type(file)}') 
            sub = self.get_rtf_text(file)
            res = self.process_text(t0,sub)

        elif file_type == 'text/plain':
            sub = self.get_txt_text(file)
            res = self.process_text(t0,sub)

        elif file_type == 'application/zip':
            subs = self.unzip_files(file)
            for s in subs:
        # Keep track of cost as this processes
            # s[0] sub & s[1] filename
                print(f'SUBS: {subs}')
                print(f'VAR: {s}')
                res = self.process_text(t0,s[0],s[1])

# Handle folders that aren't zipped
        elif file_type == 'application/octet-stream':

            print('MADE IT HERE!')
            print(f'CONTENT TYPE: {file.name}')

            if file.name.endswith('docx'):
                sub = self.get_docx_text(file)
                res = self.process_text(t0,sub)

            elif file.name.endswith('pdf'):
                sub = self.get_pdf_text(file)
                res = self.process_text(t0,sub)

            elif file.name.endswith('rtf'):
                for f in file:
                    b = BytesIO(f)
                    sub = self.get_rtf_text(b)
                    res = self.process_text(t0,sub)

            elif file.name.endswith('txt'):
                sub = self.get_txt_text(file)
                res = self.process_text(t0,sub)

            elif file.name.endswith('zip'):
                subs = self.unzip_files(file)
                for s in subs:
                    res = self.process_text(t0,s[0],file_name=s[1])

            else:
                print(f"Can't process file type {file.name}")  

        else:
            print(f"Can't open file type: {file_type}")

        print(f'RES {res}')

        if res == 'Too Long':
            response = HttpResponse('Please submit content less than 5000 words in length.')
            response.status_code = 403
            return response
        
        return super().form_valid(form)



        
    
    def process_text(self,t0,sub,file_name=None):
        args = self.check_user_has_sufficient_funds('corrected_results', sub=sub, multi=True)
        # [ price_per_100_words, total_words, charged ]

        print(f'ARGS: {args}')
# Insufficient Funds
    # Reject if over 5000 words
        if args[1] >= 5000:
            # args[3] = 'Rejected: Submit content less than 5000 words in length'
            # response = HttpResponse()
            # response.status_code = 500
            # response = HttpResponseBadRequest()
            return 'Too Long'
      
        file_name = file_name if file_name else self.request.FILES['file'].name
        username = self.request.user.username
        user_id = self.request.user.id

    # Increase the id by 1 each time
        id = r.hincrby(username,'num')
        print(f'ID: {id}')    
        curr = '$' if self.request.user.currency == 'USD' else '¥'
        
        # print(f'USER: {self.request.user.username}')
        channel_name = r.get(f'{username}_channel_name')
        print(f'CHANNEL NAME: {channel_name}')
        if channel_name:
            channel_layer = get_channel_layer()
            
        async_to_sync(channel_layer.send)(channel_name, {
                'type': 'update',
                'wordCount': args[1],
                'cost': f'{curr}{args[2]}',
                'fileName': file_name,
                'id' : id,
                'status': args[3],
            })
        
        # print(f"sub_type: {self.request.POST.get('sub_type')}")
        
        
        
    # Only process if awaiting response, otherwise reject via ws and do nothing
        if args[3] == 'Awaiting Response':
            #Remove 'insufficient funds' info from args before passing through
            args.pop()
            if 'corrected' in self.request.path_info:
                get_corrected_results.delay(t0, username, user_id, sub, id, 'multi', *args)
            else:
                get_improved_results.delay(t0, username, user_id, sub, id, 'multi', *args)
        
  
    def get_docx_text(self, file):
        doc = docx.Document(file)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        final = '\n'.join(fullText)
        print(final)
        return final
    

    def get_pdf_text(self, file):

        if isinstance(file, bytes):
        # Zipped files don't need to be read
            b = BytesIO(file)
        else:
            b = BytesIO(file.read())
        with fitz.open('pdf',b) as doc:
            text = ""
            for page in doc:
        # Produces weird unicode so needs replacing
                text += page.get_text().replace('�', ' ')
        print(text)
        return text


    def get_rtf_text(self, file):
        text = rtf_to_text(file.read().decode())
        print(text)
        return text
    

    def get_txt_text(self, file):
        text = ''
        for line in file:
            text += line.decode()
        print(text)
        return text


    def unzip_files(self, input_zip):
        input_zip = ZipFile(input_zip)
        all_zips = []
        print(f'NAMELIST: {input_zip.namelist()}')
        for name in input_zip.namelist():
            print(f'FILE NAME: {name}')
        # Archived files on MACOS produce weird extra files
        # Do this check to make sure they are not parsed
            if not name.startswith('__MACOSX'):
                if name.endswith('docx'):
                    txt = self.get_docx_text(BytesIO(input_zip.read(name)))
                    all_zips.append((txt,f'{name} [ZIPPED]'))
                elif name.endswith('pdf'): 
                    txt = self.get_pdf_text(input_zip.read(name))
                    all_zips.append((txt,f'{name} [ZIPPED]'))
                elif name.endswith('rtf'):
                    txt = rtf_to_text(input_zip.read(name).decode())
                    all_zips.append((txt,f'{name} [ZIPPED]'))
                elif name.endswith('txt'):
                    txt = input_zip.read(name).decode()
                    all_zips.append((txt,f'{name} [ZIPPED]'))
                else:
                    print('Ignored')
                # all_zips.append((txt,f'{name} [ZIPPED]'))
        return all_zips