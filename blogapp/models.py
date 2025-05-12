from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg #IMPORTA LIBRERÍA DE PROMEDIO
from ckeditor_uploader.fields import RichTextUploadingField #Importa la libreria STEP 3
# MODELOS

class Category(models.Model): #DELIMITANDO LA SECCION DE CATEGORIAS
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
 
class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextUploadingField() #RickTextFiel de CKeditor STEP 3
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.title
    
    @property
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg is not None else None


class Review(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1, message="El rating debe ser al menos 1."), #Para el mensaje de restricción
                     MaxValueValidator(5, message="El rating no puede ser mayor a 5")]) #Para el mensaje de restricción
    comment = models.TextField(blank=False, null=False) #Restricción por campos vacíos
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} - {self.blog.title}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['blog', 'reviewer'],
                name='unique_review_per_user_per_blog'
            )
        ]



class Comment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter.username}"