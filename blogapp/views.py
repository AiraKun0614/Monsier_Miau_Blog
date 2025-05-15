from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import Blog, Review, Comment, Category, Subcategory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .forms import BlogForm

from django.http import JsonResponse
from .models import Subcategory

def load_subcategories(request):
    category_id = request.GET.get('category')
    subcategories = Subcategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

#vistas para el sistema de usuario

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() #para crear el usuario 
            login(request, user) #para registro automatico
            messages.success(request, f' Bienvenido, {user.username}! Tu cuenta ha sido creada.')
            return redirect('blogapp:blog_list')
        else:
            messages.error(request, 'Error al crear el usuario, por favor corrige los errores')
    else:
        form = UserCreationForm()
    return render(request, 'blogapp/register.html', {'form': form})

#vista para el inicio de sesion
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f' Bienvenido, {user.username}!')
                return redirect('blogapp:blog_list')
            else:
                messages.error(request, 'Credenciales incorrectas')
        else:
            messages.error(request, 'Error al iniciar sesión, por favor corrige el formulario')
    else:
        form = AuthenticationForm()
    return render(request, 'blogapp/login.html', {'form': form})

#vista para el cierre de sesion
def user_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('blogapp:blog_list')  #redirecciona a la pagina principal

class BlogListView(ListView):
    model = Blog
    template_name = 'blogapp/blog_list.html'
    context_object_name = 'blogs'

    def get_queryset(self):
        queryset = Blog.objects.all().order_by('-created_at')
        subcat = self.request.GET.get('subcategory')
        cat = self.request.GET.get('category')

        if subcat:
            queryset = queryset.filter(subcategory__id=subcat)
        elif cat:
            queryset = queryset.filter(subcategory__category__id=cat)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.prefetch_related('subcategories').all()
        context['selected_category'] = self.request.GET.get('category')
        context['selected_subcategory'] = self.request.GET.get('subcategory')
        return context

class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blogapp/blog_detail.html'


class BlogCreateView(LoginRequiredMixin, CreateView):
    model = Blog
    form_class = BlogForm
    template_name = 'blogapp/blog_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blogapp:blog_detail', kwargs={'pk': self.object.pk})


# SE AÑADEN CAMBIOS PARA LA RESTRICCIÓN DE USUARIOS -- LoginRequiredMixin

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
