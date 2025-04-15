# Django Libs
from django import forms


# Contact Form
class ContactForm(forms.Form):
    name = forms.CharField(
        required=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "John Doe"}),
    )
    email = forms.EmailField(
        required=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "example@live.com"}),
    )
    subject = forms.CharField(
        required=True, label="", widget=forms.TextInput(attrs={"placeholder": "Title"})
    )
    message = forms.CharField(
        required=True,
        label="",
        widget=forms.Textarea(attrs={"placeholder": "Ask us anything"}),
    )
