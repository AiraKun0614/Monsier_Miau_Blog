from django import forms
from tinymce.widgets import TinyMCE
from .models import Blog

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'content']
        widgets = {
            'content': TinyMCE(attrs={'cols': 80, 'rows': 20}),
        }