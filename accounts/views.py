from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignUpForm
from .ratelimit import ratelimit_post


# Até 10 envios do cadastro por IP a cada hora (o sistema fica exposto num IP público)
@ratelimit_post('signup', limit=10, period=60 * 60)
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login() rotaciona a chave de sessão
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Conta criada com sucesso. Boas-vindas ao Coletta!')
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})
