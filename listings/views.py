# Django Libs
from django.shortcuts import render
from django.views import generic

# Import models and forms
from .models import Listing, Contact, WebsiteInfo
from .forms import ContactForm

# Pages
# Home Page
def HomePage(request):
    # Form
    form = ContactForm(request.POST or None)

    # Get Most Recent Listings
    listing_list = Listing.objects.filter(status=1).order_by('-created_on')
    # Website Info
    website_info = WebsiteInfo.objects.get(info_id = 1)

    # Context
    context = {
        'nbar': "Home",
        'listing_list': listing_list,
        'website_info': website_info,
        'form': form
    }

    # Code For Contact Us Form
    if request.method == 'POST' and form.is_valid():
        addContactToDB(request)
        context['contact_us'] = True

    # Render
    return render(request, 'index.html', context)

# Properties Page
class PostList(generic.ListView):
    # Listings
    queryset = Listing.objects.filter(status=1).order_by('-created_on')
    # Website Info
    website_info = WebsiteInfo.objects.get(info_id = 1)
    template_name = 'properties.html'
    extra_context = {
        'listing_list': queryset,
        'website_info': website_info,
        'nbar': "Properties"
    }

# Post Details
class PostDetail(generic.DetailView):
    model = Listing
    template_name = 'post_detail.html'
    # Website Info
    website_info = WebsiteInfo.objects.get(info_id = 1)
    extra_context = {
        'Listing': model,
        'website_info': website_info,
        'nbar': "Properties"
    }

# About US
def about_us(request):
    # Website Info
    website_info = WebsiteInfo.objects.get(info_id = 1)
    return render(request, 'about.html', {'nbar': "About", 'website_info': website_info})

# Contact Us
def contact_us(request):
    # Form
    form = ContactForm(request.POST or None)

    # Website Info
    website_info = WebsiteInfo.objects.get(info_id = 1)

    # Context
    context = {
        'nbar': "Contact",
        'website_info': website_info,
        'form': form
    }

    # Code For Contact Us Form
    if request.method == 'POST' and form.is_valid():
        addContactToDB(request)
        context['contact_us'] = True

    # Render
    return render(request, 'contact.html', context)


# UTILS
# Add Contact Us To DB
def addContactToDB(request):
    name = request.POST.get("name")
    email = request.POST.get("email")
    subject = request.POST.get("subject")
    message = request.POST.get("message")
    
    contactEmail = Contact.objects.create(name=name, email=email, subject=subject, message=message)
    contactEmail.save()
