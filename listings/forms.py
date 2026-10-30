from django import forms

from .models import Contact

INPUT_CLASS = "field-input"


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "Jane Doe", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "jane@example.com",
                    "autocomplete": "email",
                }
            ),
            "subject": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "What is this about?"}
            ),
            "message": forms.Textarea(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "Tell us what you are looking for",
                    "rows": 5,
                }
            ),
        }
