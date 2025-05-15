from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import Blog, Review, Comment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import os

# Vista para manejar la carga de imágenes de TinyMCE
def tinymce_upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # Guardar la imagen en MEDIA_ROOT/uploads/
        upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, uploaded_file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        # Devolver la URL de la imagen
        file_url = f"{settings.MEDIA_URL}uploads/{uploaded_file.name}"
        return JsonResponse({'location': file_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Vistas para el sistema de usuario
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username}! Tu cuenta ha sido creada.')
            return redirect('blogapp:blog_list')
        else:
            messages.error(request, 'Error al crear el usuario, por favor corrige los errores')
    else:
        form = UserCreationForm()
    return render(request, 'blogapp/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.username}!')
                return redirect('blogapp:blog_list')
            else:
                messages.error(request, 'Credenciales incorrectas')
        else:
            messages.error(request, 'Error al iniciar sesión, por favor corrige el formulario')
    else:
        form = AuthenticationForm()
    return render(request, 'blogapp/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('blogapp:blog_list')

class BlogListView(ListView):
    model = Blog
    template_name = 'blogapp/blog_list.html'

class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blogapp/blog_detail.html'

class BlogCreateView(LoginRequiredMixin, CreateView):
    model = Blog
    fields = ['title', 'content']
    template_name = 'blogapp/blog_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blogapp:blog_detail', kwargs={'pk': self.object.pk})

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    fields = ['rating', 'comment']
    template_name = 'blogapp/review_form.html'

    def form_valid(self, form):
        form.instance.reviewer = self.request.user
        form.instance.blog_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blogapp:blog_detail', kwargs={'pk': self.kwargs['pk']})

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['content']
    template_name = 'blogapp/comment_form.html'

    def form_valid(self, form):
        form.instance.commenter = self.request.user
        form.instance.review_id = self.kwargs['review_pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blogapp:blog_detail', kwargs={'pk': self.kwargs['blog_pk']})