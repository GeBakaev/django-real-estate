from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import generic

from .forms import ContactForm
from .models import Listing

CONTACT_SUCCESS_MESSAGE = "Thank you for contacting us. We will get back to you shortly."


def _handle_contact_form(request):
    """Bind the contact form; save and return True when a valid POST arrived."""
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, CONTACT_SUCCESS_MESSAGE)
        return form, True
    return form, False


def home(request):
    form, submitted = _handle_contact_form(request)
    if submitted:
        return redirect("home")

    listings = Listing.objects.published().prefetch_related("images")[:3]
    context = {"nbar": "Home", "listing_list": listings, "form": form}
    return render(request, "index.html", context)


class PostList(generic.ListView):
    template_name = "properties.html"
    paginate_by = settings.PAGINATION_LIMIT
    extra_context = {"nbar": "Properties"}

    def get_queryset(self):
        return Listing.objects.published().prefetch_related("images")


class PostDetail(generic.DetailView):
    template_name = "post_detail.html"
    extra_context = {"nbar": "Properties"}

    def get_queryset(self):
        # Drafts must never be reachable by guessing the slug.
        return Listing.objects.published().prefetch_related("images")


def about_us(request):
    return render(request, "about.html", {"nbar": "About"})


def contact_us(request):
    form, submitted = _handle_contact_form(request)
    if submitted:
        return redirect("contact-us")
    return render(request, "contact.html", {"nbar": "Contact", "form": form})
