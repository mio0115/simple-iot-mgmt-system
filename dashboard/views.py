from django.shortcuts import render
from django.urls import reverse


# Create your views here.
def home(request):
    url = reverse('dashboard:home')
    return render(request, url)
