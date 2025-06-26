from django import forms
from .models import Review, Message
from django.contrib.auth.models import User

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 1}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rating = cleaned_data.get('rating')
        comment = cleaned_data.get('comment')
        if comment and not comment.strip():
            self.add_error('comment', 'El comentario no puede estar vacío.')
        return cleaned_data

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
        widgets = {
            'receiver': forms.Select(attrs={'class': 'w-full p-2 rounded-lg bg-cat-white dark:bg-cat-soft-purple text-gray-900 dark:text-white border border-cat-pink focus:outline-none focus:ring-2 focus:ring-cat-purple'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'w-full p-2 rounded-lg bg-cat-white dark:bg-cat-soft-purple text-gray-900 dark:text-white border border-cat-pink focus:outline-none focus:ring-2 focus:ring-cat-purple'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['receiver'].queryset = User.objects.exclude(id=kwargs.get('initial', {}).get('sender', None)).exclude(is_active=False)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']
        if hasattr(self, 'instance') and self.instance.sender == receiver:
            raise forms.ValidationError('No puedes enviarte un mensaje a ti mismo. 😿')
        return receiver