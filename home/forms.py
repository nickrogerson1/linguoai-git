from django import forms

html = { 
            "class": "form-control",
            # Maxlength is enforced at browser level
            "maxlength" : "4000",
        }

class ContactForm(forms.Form):

    name = forms.CharField(widget = forms.TextInput(attrs={ "class" : "form-control" }))
    email = forms.EmailField(widget = forms.EmailInput(attrs={ "class" : "form-control" }))
    message = forms.CharField(widget = forms.Textarea(attrs=html))

