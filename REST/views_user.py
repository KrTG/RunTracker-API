import django
from django import urls
from django.contrib import auth
from django.core import exceptions
from django.http import QueryDict
from django.http.response import HttpResponse
from django.http.response import JsonResponse
from django.http.response import HttpResponseForbidden
from django.http.response import HttpResponseBadRequest
from django.http.response import HttpResponseNotFound

from .models import User, UserManager
from .view_functions import get_stats
from .decorators import login_required, require_http_methods
from .helpers import MessageResponse

@require_http_methods(["POST"])
def register(request):
    try:
        email = request.POST['email']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']        
    except KeyError:
        return HttpResponseBadRequest("Required field empty")

    weight = request.POST.get('weight', 70)
        
    try:
        user = User.objects.create_user(
            email,
            password,
            first_name=first_name,
            last_name=last_name,
            weight=weight
        )  
    except exceptions.ValidationError as e:
        return HttpResponseForbidden(e.messages[0])

    response = JsonResponse(
        user.serialize(),
        status=201,
    )
    response['Location'] = urls.reverse('profile', args=[user.pk])
    return response


@require_http_methods(["POST"])
def login(request):
    try:
        email = request.POST['username']
        password = request.POST['password']
    except KeyError:
        return HttpResponseBadRequest('No email or password field')

    user = auth.authenticate(request, username=email, password=password)
    if user is not None:
        request.session.set_expiry(2 * 7 * 24 * 60 * 60)
        auth.login(request, user)
        return MessageResponse('Logged in', status=200)
    else:
        return HttpResponse('Invalid login or password', status=401)


@require_http_methods(["POST"])
def logout(request):
    auth.logout(request)
    return MessageResponse('Logged out', status=200)


@require_http_methods(["GET"])
def check_login(request):    
    return JsonResponse({
        'logged_in': request.user.is_authenticated
    }, status=200) 

@require_http_methods(["POST"])
@login_required
def change_avatar(request):
    try:
        image = request.POST['image']
    except KeyError:
        return HttpResponseBadRequest("Parameter 'image' is needed")

    request.user.avatar = image
    request.user.save()

    return MessageResponse("New avatar uploaded")

@require_http_methods(["GET"])
@login_required
def my_profile(request):
    return JsonResponse(request.user.serialize())


@require_http_methods(["GET"])
def profile(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return HttpResponseNotFound("No such user")

    return JsonResponse(user.serialize())


@require_http_methods(["GET"])
@login_required
def my_stats(request):
    return stats(request, request.user.pk)


@require_http_methods(["GET"])
def stats(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return HttpResponseNotFound("No such user")

    return JsonResponse(
        {
            'user': user.serialize(),
            'stats': get_stats(user),
        }
    )