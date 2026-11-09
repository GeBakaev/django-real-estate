from django import forms
from django.db.models import Q

from .models import Contact, Listing

INPUT_CLASS = "field-input"


class ContactForm(forms.ModelForm):
    """Contact form; pass ``listing`` to turn it into an inquiry about that property."""

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        if listing is not None:
            max_length = self.fields["subject"].max_length
            self.fields["subject"].initial = f"Inquiry about {listing.title}"[:max_length]
            self.fields["message"].widget.attrs["placeholder"] = (
                "I would like to know more about this property"
            )

    def save(self, commit=True):
        self.instance.listing = self.listing
        return super().save(commit)

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


class ListingFilterForm(forms.Form):
    """GET form that narrows and sorts the public listing index.

    Invalid values (e.g. ``min_price=abc``) are ignored rather than rejected, so a
    hand-edited URL still renders results.
    """

    SORT_CHOICES = [
        ("newest", "Newest first"),
        ("price_asc", "Price: low to high"),
        ("price_desc", "Price: high to low"),
        ("area_desc", "Largest first"),
    ]
    SORT_ORDERING = {
        "newest": ("-created_on",),
        "price_asc": ("price", "-created_on"),
        "price_desc": ("-price", "-created_on"),
        "area_desc": ("-area", "-created_on"),
    }
    BEDROOM_CHOICES = [("", "Any"), ("1", "1+"), ("2", "2+"), ("3", "3+"), ("4", "4+")]
    FILTER_FIELDS = (
        "q",
        "listing_type",
        "location",
        "property_type",
        "min_bedrooms",
        "min_price",
        "max_price",
        "min_area",
    )

    q = forms.CharField(
        required=False,
        max_length=100,
        label="Search",
        widget=forms.TextInput(attrs={"type": "search", "placeholder": "Title, area or keyword"}),
    )
    listing_type = forms.ChoiceField(
        required=False,
        label="Sale or rent",
        choices=[("", "Sale and rent")] + Listing.ListingType.choices,
    )
    location = forms.ChoiceField(required=False, label="Location")
    property_type = forms.ChoiceField(
        required=False,
        label="Type",
        choices=[("", "Any type")] + Listing.PropertyType.choices,
    )
    min_bedrooms = forms.TypedChoiceField(
        required=False, label="Bedrooms", choices=BEDROOM_CHOICES, coerce=int, empty_value=None
    )
    min_price = forms.IntegerField(
        required=False,
        min_value=0,
        label="Min price ($)",
        widget=forms.NumberInput(attrs={"placeholder": "0", "step": 1000}),
    )
    max_price = forms.IntegerField(
        required=False,
        min_value=0,
        label="Max price ($)",
        widget=forms.NumberInput(attrs={"placeholder": "Any", "step": 1000}),
    )
    min_area = forms.IntegerField(
        required=False,
        min_value=0,
        label="Min area (m²)",
        widget=forms.NumberInput(attrs={"placeholder": "0", "step": 10}),
    )
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, label="Sort by")

    def __init__(self, data=None, *, locations=(), **kwargs):
        super().__init__(data, **kwargs)
        self.fields["location"].choices = [("", "All locations")] + [
            (location, location) for location in locations
        ]
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS

    @property
    def is_active(self):
        """True when any narrowing filter (not just the sort) is set."""
        return any(self.cleaned_data.get(name) not in (None, "") for name in self.FILTER_FIELDS)

    def filter(self, queryset):
        if not self.is_bound:
            self.cleaned_data = {}
            return queryset.order_by(*self.SORT_ORDERING["newest"])
        self.is_valid()  # populates cleaned_data with the fields that validated
        data = self.cleaned_data
        if data.get("q"):
            term = data["q"]
            queryset = queryset.filter(
                Q(title__icontains=term)
                | Q(location__icontains=term)
                | Q(description__icontains=term)
            )
        if data.get("listing_type"):
            queryset = queryset.filter(listing_type=data["listing_type"])
        if data.get("location"):
            queryset = queryset.filter(location=data["location"])
        if data.get("property_type"):
            queryset = queryset.filter(property_type=data["property_type"])
        if data.get("min_bedrooms") is not None:
            queryset = queryset.filter(bedrooms__gte=data["min_bedrooms"])
        if data.get("min_price") is not None:
            queryset = queryset.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            queryset = queryset.filter(price__lte=data["max_price"])
        if data.get("min_area") is not None:
            queryset = queryset.filter(area__gte=data["min_area"])
        sort = data.get("sort") or "newest"
        return queryset.order_by(*self.SORT_ORDERING[sort])
