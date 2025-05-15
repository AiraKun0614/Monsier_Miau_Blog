from django import forms
from .models import Blog, Subcategory, Category
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget

class BlogForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Blog
        fields = ['title', 'content', 'image', 'category', 'subcategory']
        widgets = {
            'content': CKEditorUploadingWidget()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Subcategorías vacías por defecto
        self.fields['subcategory'].queryset = Subcategory.objects.none()

        # Si viene una categoría seleccionada en el POST (desde JS)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass
        # Si ya hay una instancia de blog existente
        elif self.instance.pk and self.instance.subcategory:
            self.fields['subcategory'].queryset = Subcategory.objects.filter(category=self.instance.subcategory.category)
            self.fields['category'].initial = self.instance.subcategory.category
