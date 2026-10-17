
from django.http import HttpResponse


def home(request):
    return HttpResponse("Welcome to Southern Conxs Bazar Development Forum (SCDF)")
