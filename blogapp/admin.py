from django.contrib import admin
from .models import Blog, Review, Comment, Category, Subcategory

admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Blog)
admin.site.register(Review)
admin.site.register(Comment)

