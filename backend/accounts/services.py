from django.contrib.auth import authenticate, login, logout


def login_user(request, email, password):
    user = authenticate(request, username=email, password=password)
    if user is None:
        return None
    login(request, user)
    return user


def logout_user(request):
    logout(request)