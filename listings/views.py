# Django Libs
from django.shortcuts import render
from django.views import generic

# Settings
from real_estate.settings import GEOPOSITION_GOOGLE_MAPS_API_KEY as GOOGLE_MAP_KEY


# Import models and forms
from listings.models import Listing, Contact
from listings.forms import ContactForm
from real_estate.settings import PAGINATION_LIMIT


# Pages
# Home Page
def HomePage(request):
    # Form
    form = ContactForm(request.POST or None)

    # Get Most Recent Listings
    listing_list = Listing.objects.filter(status=1).order_by("-created_on")
    # Return the first 3 only
    listing_list = listing_list[:3]

    # Context
    context = {
        "nbar": "Home",
        "listing_list": listing_list,
        "form": form,
    }

    # Code For Contact Us Form
    if request.method == "POST" and form.is_valid():
        addContactToDB(request)
        context["contact_us"] = True

    # Render
    return render(request, "index.html", context)


# Properties Page
class PostList(generic.ListView):
    # Listings
    queryset = Listing.objects.filter(status=1).order_by("-created_on")
    template_name = "properties.html"
    paginate_by = PAGINATION_LIMIT
    extra_context = {
        "nbar": "Properties",
    }


# Post Details
class PostDetail(generic.DetailView):
    model = Listing
    template_name = "post_detail.html"
    extra_context = {
        "Listing": model,
        "nbar": "Properties",
        "GOOGLE_MAP_KEY": GOOGLE_MAP_KEY,
    }


# About US
def about_us(request):
    return render(request, "about.html", {"nbar": "About"})


# Contact Us
def contact_us(request):
    # Form
    form = ContactForm(request.POST or None)

    # Context
    context = {"nbar": "Contact", "form": form}

    # Code For Contact Us Form
    if request.method == "POST" and form.is_valid():
        addContactToDB(request)
        context["contact_us"] = True

    # Render
    return render(request, "contact.html", context)


# UTILS
# Add Contact Us To DB
def addContactToDB(request):
    name = request.POST.get("name")
    email = request.POST.get("email")
    subject = request.POST.get("subject")
    message = request.POST.get("message")

    contactEmail = Contact.objects.create(
        name=name, email=email, subject=subject, message=message
    )
    contactEmail.save()
