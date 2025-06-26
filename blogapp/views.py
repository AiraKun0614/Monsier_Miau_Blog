from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.urls import reverse_lazy
from .models import Blog, Review, Comment, Category, Message
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .forms import ReviewForm, MessageForm
from django.db.models import Avg
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .models import Message

# Vistas para el sistema de usuario
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}! Tu cuenta ha sido creada.')
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
                messages.success(request, f'¡Bienvenido, {user.username}!')
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

# Vistas para blogs
class BlogListView(ListView):
    model = Blog
    template_name = 'blogapp/blog_list.html'
    context_object_name = 'blogs'
    paginate_by = 5

    def get_queryset(self):
        queryset = Blog.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('-created_at')
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        return context

class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blogapp/blog_detail.html'
    context_object_name = 'blogs'

class BlogCreateView(LoginRequiredMixin, CreateView):
    model = Blog
    fields = ['title', 'content', 'category']
    template_name = 'blogapp/blog_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blogapp:blog_detail', kwargs={'pk': self.object.pk})

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'blogapp/review_form.html'

    def form_valid(self, form):
        form.instance.reviewer = self.request.user
        form.instance.blog_id = self.kwargs['pk']
        messages.success(self.request, '¡Reseña creada exitosamente!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)

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

class BlogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Blog
    template_name = 'blogapp/blog_confirm_delete.html'
    success_url = reverse_lazy('blogapp:blog_list')

    def test_func(self):
        blog = self.get_object()
        return self.request.user == blog.author or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        messages.success(request, '¡Blog eliminado exitosamente!')
        return super().delete(request, *args, **kwargs)

@csrf_exempt
@login_required
def tinymce_upload(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No se proporcionó ninguna imagen'}, status=400)
    
    uploaded_file = request.FILES['file']
    allowed_types = ['image/jpeg', 'image/png', 'image/gif']
    if uploaded_file.content_type not in allowed_types:
        return JsonResponse({'error': 'Solo se permiten imágenes (JPEG, PNG, GIF)'}, status=400)
    
    ext = uploaded_file.name.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join('tinymce', filename)
    
    try:
        path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        file_url = f"{settings.MEDIA_URL}{path}"
        return JsonResponse({'location': file_url})
    except Exception as e:
        return JsonResponse({'error': f'Error al guardar la imagen: {str(e)}'}, status=500)

# Vistas de mensajería
@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    paginator = Paginator(messages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, 'blogapp/inbox.html', {
        'page_obj': page_obj,
        'unread_messages_count': unread_count
    })

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            if message.sender == message.receiver:
                messages.error(request, 'No puedes enviarte un mensaje a ti mismo. 😿')
                return render(request, 'blogapp/send_message.html', {
                    'form': form,
                    'unread_messages_count': Message.objects.filter(receiver=request.user, is_read=False).count()
                })
            message.save()
            messages.success(request, '¡Mensaje enviado exitosamente! 🐾')
            return redirect('blogapp:inbox')
        else:
            messages.error(request, 'Error al enviar el mensaje, por favor corrige el formulario. 😿')
    else:
        form = MessageForm()
    return render(request, 'blogapp/send_message.html', {
        'form': form,
        'unread_messages_count': Message.objects.filter(receiver=request.user, is_read=False).count()
    })

@login_required
def conversation(request, username):
    user = get_object_or_404(User, username=username)
    if user == request.user:
        messages.error(request, 'No puedes chatear contigo mismo. 😿')
        return redirect('blogapp:inbox')
    messages = Message.objects.filter(
        sender__in=[request.user, user],
        receiver__in=[request.user, user]
    ).order_by('timestamp')
    Message.objects.filter(receiver=request.user, sender=user, is_read=False).update(is_read=True)
    form = MessageForm(initial={'receiver': user})
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = user
            message.save()
            messages.success(request, '¡Mensaje enviado exitosamente! 🐾')
            return redirect('blogapp:conversation', username=username)
        else:
            messages.error(request, 'Error al enviar el mensaje, por favor corrige el formulario. 😿')
    return render(request, 'blogapp/conversation.html', {
        'messages': messages,
        'form': form,
        'receiver': user,
        'unread_messages_count': Message.objects.filter(receiver=request.user, is_read=False).count()
    })