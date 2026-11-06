from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views import generic

from .emails import notify_new_contact
from .forms import ContactForm, ListingFilterForm
from .models import Listing

CONTACT_SUCCESS_MESSAGE = "Thank you for contacting us. We will get back to you shortly."


def _handle_contact_form(request, listing=None):
    """Bind the contact form; save and return True when a valid POST arrived.

    With ``listing`` the submission is stored as an inquiry about that property.
    """
    form = ContactForm(request.POST or None, listing=listing)
    if request.method == "POST" and form.is_valid():
        contact = form.save()
        listing_url = request.build_absolute_uri(listing.get_absolute_url()) if listing else ""
        notify_new_contact(contact, listing_url=listing_url)
        messages.success(request, CONTACT_SUCCESS_MESSAGE)
        return form, True
    return form, False


def home(request):
    form, submitted = _handle_contact_form(request)
    if submitted:
        return redirect("home")

    listings = Listing.objects.published().prefetch_related("images")[:3]
    context = {"nbar": "Home", "listing_list": listings, "form": form}
    return render(request, "home.html", context)


class PostList(generic.ListView):
    template_name = "properties.html"
    partial_template_name = "partials/listing_results.html"
    paginate_by = settings.PAGINATION_LIMIT
    extra_context = {"nbar": "Properties"}

    def get_queryset(self):
        published = Listing.objects.published()
        locations = published.order_by("location").values_list("location", flat=True).distinct()
        self.filter_form = ListingFilterForm(self.request.GET or None, locations=locations)
        return self.filter_form.filter(published.prefetch_related("images"))

    def get_template_names(self):
        # htmx swaps only the results block; everyone else gets the full page.
        if self.request.headers.get("HX-Request"):
            return [self.partial_template_name]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context["page_obj"]
        context["filter_form"] = self.filter_form
        context["elided_page_range"] = page_obj.paginator.get_elided_page_range(
            page_obj.number, on_each_side=1, on_ends=1
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        patch_vary_headers(response, ["HX-Request"])
        return response


class PostDetail(generic.DetailView):
    template_name = "post_detail.html"
    extra_context = {"nbar": "Properties"}

    def get_queryset(self):
        # Drafts must never be reachable by guessing the slug.
        return Listing.objects.published().prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("form", ContactForm(listing=self.object))
        listing_url = self.request.build_absolute_uri(self.object.get_absolute_url())
        context["whatsapp_text"] = f"Hello, I am interested in {self.object.title}: {listing_url}"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form, submitted = _handle_contact_form(request, listing=self.object)
        if submitted:
            return redirect(self.object)
        return self.render_to_response(self.get_context_data(form=form))


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def about_us(request):
    return render(request, "about.html", {"nbar": "About"})


def contact_us(request):
    form, submitted = _handle_contact_form(request)
    if submitted:
        return redirect("contact-us")
    return render(request, "contact.html", {"nbar": "Contact", "form": form})
