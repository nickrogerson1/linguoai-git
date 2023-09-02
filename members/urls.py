from django.urls import path, re_path, include
from .views import *
from .copies.docx import *
from .copies.pdf import *
from .payments.stripe import *
from django.contrib.auth.views import *
from django.views.generic import TemplateView

urlpatterns = [
    # Auth
    path('login/', LoginUser.as_view(), name="login"),
    path('register/', Registration.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),

    #  path("pay/", create_checkout_session, name="pay"),
    path("top-up/", CreateStripeCheckoutSessionView.as_view(), name="top-up"),
    path("insufficient-funds/", TemplateView.as_view(template_name="members/home/insufficient-funds.html"), name="insufficient-funds"),
    
    # path('payment-successful', TemplateView.as_view(template_name="members/stripe/success.html")),
    # path('top-up/', TemplateView.as_view(template_name="members/home/buy-credits.html"), name="top-up"),
    path('payment-successful', SuccessfulPaymentView.as_view()),
    path('payment-canceled/', TemplateView.as_view(template_name="members/stripe/cancel.html")),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),

    # The home page
    path('dash/', index, name='home'),

    re_path(r'report([0-9a-z/-]+)', report_bad_result, name='report'),
    

     # Internal Contact Form
    path('contact-us/', InternalContactForm.as_view(), name='internal-contact'),
    path('message-success/', TemplateView.as_view(template_name='members/home/message-success.html'), name='message-success'),


    path('dropzone-files/', FileFieldFormView.as_view(), name='dropzone'),


    # Activate account
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$',
        activate_account, name='activate'),
    path('account-activated/', TemplateView.as_view(template_name='registration/account_activated.html'), name='activated'),

    # Password Reset
    path('reset_password/', CustomPasswordResetView.as_view(), name ='reset_password'),
    path('reset_password_sent/', PasswordResetDoneView.as_view(), name ='password_reset_done'),
    re_path('reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>set-password)/', CustomPasswordResetConfirmView.as_view(), name ='password_reset_confirm'),
    path('reset_password_complete/', PasswordResetCompleteView.as_view(), name ='password_reset_complete'),


    # Account Management
    # re_path(r"^accounts/", include("django.contrib.auth.urls")),
    path('', include("django.contrib.auth.urls")),

    # Website functionality
    path('ielts-writing-task-2/', IeltsWritingTask2View.as_view(), name='ielts-writing-task-2'),
    path('corrected/', CorrectedFormView.as_view(), name='corrected'),
    path('improved/', ImprovedFormView.as_view(), name='improved'),
    path('service-unavailable/', TemplateView.as_view(template_name="members/home/service-unavailable.html"), name="unavailable"),

    path('ielts-writing-task-2/submitted/', TemplateView.as_view(template_name="members/home/sent-success.html"), name='ielts-writing-task-2-sent'),
    path('corrected/submitted/', TemplateView.as_view(template_name="members/home/sent-success.html"), name='corrected-sent'),
    path('improved/submitted/', TemplateView.as_view(template_name="members/home/sent-success.html"), name='improved-sent'),


    path('log/', ResultsLogView.as_view(), name='log'),

    # Dashboard user DB searches
    path('ielts-writing-task-2-results/', IeltsResultsView.as_view(), name='ielts-writing-task-2-results'),
    path('ielts-writing-task-2-results/<int:pk>/', IeltsResultsDetailView.as_view(), name='ielts-writing-task-2-results-detail'),
    path('corrected-results/', CorrectedResultsView.as_view(), name='corrected-results'),
    path('corrected-results/<int:pk>/', CorrectedResultsDetailView.as_view(), name='corrected-results-detail'),
    path('improved-results/', ImprovedResultsView.as_view(), name='improved-results'),
    path('improved-results/<int:pk>/', ImprovedResultsDetailView.as_view(), name='improved-results-detail'),


    # re_path(r'^corrected-results/delete/(?P<pks>([0-9]+/)+)?$', UpdateCorrectedResults.as_view(), name='delete-corrected-results'),
    path('corrected-delete-files/', CorrectedDeleteFiles.as_view(), name='corrected-delete'),
    path('improved-delete-files/', ImprovedDeleteFiles.as_view(), name='improved-delete'),
    path('ielts-writing-task-2-delete-files/', IeltsWritingTask2DeleteFiles.as_view(), name='ielts-writing-task-2-delete'),
    path('log-delete-files/', LogDeleteFiles.as_view(), name='log-delete'),

    # PDF & DOCX Requests
    re_path(r'^corrected-results/bulk-pdf/(?P<type>[01])/(?P<pks>([0-9]+/)+)?$', get_bulk_pdf_task, name='get_bulk_corrected_pdf'),
    re_path(r'^corrected-results/bulk-docx/(?P<type>[01])/(?P<pks>([0-9]+/)+)?$', get_bulk_docx, name='get_bulk_corrected_docx'),
    re_path(r'^improved-results/bulk-pdf/(?P<pks>([0-9]+/)+)?$', get_bulk_pdf_task, name='get_bulk_improved_pdf'),
    re_path(r'^improved-results/bulk-docx/(?P<pks>([0-9]+/)+)?$', get_bulk_docx, name='get_bulk_improved_docx'),
    re_path(r'^ielts-writing-task-2-results/bulk-pdf/(?P<pks>([0-9]+/)+)?$', get_bulk_pdf_task, name='get_bulk_ielts_writing_pdf'),
    re_path(r'^ielts-writing-task-2-results/bulk-docx/(?P<pks>([0-9]+/)+)?$', get_bulk_docx, name='get_bulk_ielts_writing_docx'),
    re_path(r'^log/bulk-pdf/(?P<url_str>([\w-]+results/[0-9]+/)+)?$', get_bulk_mixed_pdf_task, name='get_bulk_pdf'),
    re_path(r'^log/bulk-docx/(?P<url_str>([\w-]+results/[0-9]+/)+)?$', get_bulk_mixed_docx, name='get_bulk_docx'),

    path('corrected-results/pdf/<int:pk>/<int:type>/', get_pdf, name='get_corrected_pdf'),
    path('corrected-results/docx/<int:pk>/<int:type>/', get_docx, name='get_corrected_docx'),
    path('improved-results/pdf/<int:pk>/', get_pdf, name='get_improved_pdf'),
    path('improved-results/docx/<int:pk>/', get_docx, name='get_improved_docx'),
    path('ielts-writing-task-2-results/pdf/<int:pk>/', get_pdf, name='get_ielts_writing_pdf'),
    path('ielts-writing-task-2-results/docx/<int:pk>/', get_docx, name='get_ielts_writing_docx'),

    # Matches any html file
    re_path(r'^.*\.*', pages, name='pages')
]