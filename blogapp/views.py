from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.urls import reverse_lazy
from .models import Blog, Review, Comment, Category
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .forms import ReviewForm #REVIEW FORMS PARA VALIDACION
from django.db.models import Avg #CONTEO 

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
    paginate_by = 5 #PAGINACION

    def get_queryset(self): #editado para las categorias
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
    fields = ['title', 'content', 'category'] #Se agrega el dato "category"
    template_name = 'blogapp/blog_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blogapp:blog_detail', kwargs={'pk': self.object.pk})

# SE AÑADEN CAMBIOS PARA LA RESTRICCIÓN DE USUARIOS -- LoginRequiredMixin

class ReviewCreateView(LoginRequiredMixin, CreateView): #CAMBIOS PARA VALIDACION DE REVIEWS
    model = Review
    form_class = ReviewForm  # Usar el formulario personalizado
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
    

class BlogDeleteView (LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Blog
    template_name = 'blogApp/blog_confirm_delete.html'
    success_url = reverse_lazy('blogapp:blog_list')

    def test_func(self):
        blog = self.get_object()
        return self.request.user == blog.author or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        messages.success(request, '¡Blog eliminado exitosamente!')
        return super().delete(request, *args, **kwargs)

