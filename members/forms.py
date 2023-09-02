from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from .models import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth import password_validation


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))

    error_messages = {
        "invalid_login": _(
            "Please enter a valid Username and/or Password. Note that both "
            "fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
    }


class SignUpForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['year'].widget.attrs['class'] = 'form-control'
        self.fields['country'].widget.attrs['class'] = 'form-control'
        self.fields['currency'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
            
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("first_name", "country", "year", "email", "currency")

# Average word length is 5.1 characters
# 510 characters per 100 words

html = { 
            "class": "form-control",
            "onInput" : "this.parentNode.dataset.replicatedValue = this.value",
            # Maxlength is enforced at browser level
            "maxlength" : "25000"
        }

# Add form class to include widgets (classes) in form
class IeltsWritingTask2Form(forms.ModelForm):

    class Meta:
        model = IeltsWritingTask2
        fields = ['explanation_language', 'question', 'answer']
        widgets = {
            'explanation_language' : forms.Select(attrs={ 
                "class": "form-control"
            }),

            'question' : forms.Textarea(attrs={ 
                "class": "form-control",
                "onInput" : "this.parentNode.dataset.replicatedValue = this.value",
                "rows" : 5,
                "maxlength" : "500"
            }),
            'answer' :  forms.Textarea(attrs={ 
            "class": "form-control",
            "onInput" : "this.parentNode.dataset.replicatedValue = this.value",
            # Maxlength is enforced at browser level
            "maxlength" : "3000"
        })
        }
        # labels = {'question' : 'Type or Paste In Your Question',
        #           'answer' : 'Type or Paste In Your Answer'
        #         }

class CorrectedForm(forms.ModelForm):

    class Meta:
        model = CorrectedSubmission
        fields = ['submission']
        widgets = {'submission' :  forms.Textarea(attrs=html)}
        # labels = {'submission' : ''}


class ImprovedForm(forms.ModelForm):

    class Meta:
        model = ImprovedSubmission
        fields = ['submission']
        widgets = {'submission' :  forms.Textarea(attrs=html)}
        # labels = {'submission' : ''}


class ReportForm(forms.ModelForm):

    class Meta:
        model = UserReportedResults
        fields = ['reason']
        widgets = {'reason' :  forms.Textarea(attrs=html)}


class ContactForm(forms.Form):
    message = forms.CharField(widget = forms.Textarea(attrs=html))


class BuyCreditsForm(forms.Form):
    amount = forms.IntegerField()


class PasswordResetEmail(PasswordResetForm):

    email = forms.EmailField(
    # Same as orginal
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            # Add these styles
            "placeholder": "Enter Your Email Address",
            "class": "form-control"
        })
    )

class PasswordResetPass(SetPasswordForm):
    
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Enter A New Password",
            "class": "form-control"
            }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Enter The Same Password Again",
            "class": "form-control"
            }),
    )



    # Dynamically create fields
# class UserDeleteForm(forms.Form):
#     def __init__(self, *args, **kwargs):
#         super(UserDeleteForm, self).__init__(*args, **kwargs)
#         # dynamic fields here ...
#         self.fields['checkbox'] = forms.BooleanField()



class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class FileFieldForm(forms.Form):
    file_field = MultipleFileField()