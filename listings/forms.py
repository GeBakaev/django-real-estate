from django import forms

from .models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["name", "email", "subject", "message"]
        labels = {field: "" for field in fields}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "John Doe"}),
            "email": forms.EmailInput(attrs={"placeholder": "example@live.com"}),
            "subject": forms.TextInput(attrs={"placeholder": "Title"}),
            "message": forms.Textarea(attrs={"placeholder": "Ask us anything"}),
        }
