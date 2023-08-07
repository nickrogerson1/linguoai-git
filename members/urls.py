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

    # Payment
    path("top-up/", CreateStripeCheckoutSessionView.as_view(), name="top-up"),
    path("insufficient-funds/", TemplateView.as_view(template_name="members/home/insufficient-funds.html"), name="insufficient-funds"),
    path('payment-successful', SuccessfulPaymentView.as_view()),
    path('payment-canceled/', TemplateView.as_view(template_name="members/stripe/cancel.html")),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),

    # The home page
    path('dash/', index, name='home'),

    re_path(r'report([0-9a-z/-]+)', report_bad_result, name='report'),
    

     # Internal Contact Form
    path('contact-us/', InternalContactForm.as_view(), name='internal-contact'),
    path('message-success/', TemplateView.as_view(template_name='members/home/message-success.html'), name='message-success'),


    # Activate account
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$',
        activate_account, name='activate'),
    path('account-activated/', TemplateView.as_view(template_name='registration/account_activated.html'), name='activated'),

    # Password Reset
    path('reset_password/', CustomPasswordResetView.as_view(), name ='reset_password'),
    path('reset_password_sent/', PasswordResetDoneView.as_view(), name ='password_reset_done'),
    re_path('reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>set-password)/', CustomPasswordResetConfirmView.as_view(), name ='password_reset_confirm'),
    path('reset_password_complete/', PasswordResetCompleteView.as_view(), name ='password_reset_complete'),


    # Sidebar pages
    path('icons/', TemplateView.as_view(template_name="members/home/icons.html")),
    path('map/', TemplateView.as_view(template_name="members/home/map.html")),
    path('notifications/', TemplateView.as_view(template_name="members/home/notifications.html")),
    path('user/', TemplateView.as_view(template_name="members/home/user.html")),
    path('tables/', TemplateView.as_view(template_name="members/home/tables.html")),
    path('typography/', TemplateView.as_view(template_name="members/home/typography.html")),
    path('rtl/', TemplateView.as_view(template_name="members/home/rtl.html")),



    # Account Management
    # re_path(r"^accounts/", include("django.contrib.auth.urls")),
    path('', include("django.contrib.auth.urls")),

    # Website functionality
    path('ielts-writing-task-2/', IeltsWritingTask2View.as_view(), name='ielts-writing-task-2'),
    path('corrected/', CorrectedFormView.as_view(), name='corrected'),
    path('improved/', ImprovedFormView.as_view(), name='improved'),
    path('service-unavailable/', TemplateView.as_view(template_name="members/home/service-unavailable.html"), name="unavailable"),


    # Dashboard user DB searches
    path('ielts-writing-task-2-results/', IeltsResultsView.as_view(), name='ielts-writing-task-2-results'),
    path('ielts-writing-task-2-results/<int:pk>/', IeltsResultsDetailView.as_view(), name='ielts-writing-task-2-results-detail'),
    path('corrected-results/', CorrectedResultsView.as_view(), name='corrected-results'),
    path('corrected-results/<int:pk>/', CorrectedResultsDetailView.as_view(), name='corrected-results-detail'),
    path('improved-results/', ImprovedResultsView.as_view(), name='improved-results'),
    path('improved-results/<int:pk>/', ImprovedResultsDetailView.as_view(), name='improved-results-detail'),

    # PDF & DOCX Requests
    path('corrected-results/pdf/<int:pk>/', get_pdf, name='get_corrected_pdf'),
    path('corrected-results/docx/<int:pk>/', get_docx, name='get_corrected_docx'),
    path('improved-results/pdf/<int:pk>/', get_pdf, name='get_improved_pdf'),
    path('improved-results/docx/<int:pk>/', get_docx, name='get_improved_docx'),
    path('ielts-task-2-results/pdf/<int:pk>/', get_pdf, name='get_ielts_writing_pdf'),
    path('ielts-task-2-results/docx/<int:pk>/', get_docx, name='get_ielts_writing_docx'),
   


    # Matches any html file
    re_path(r'^.*\.*', pages, name='pages'),
]
