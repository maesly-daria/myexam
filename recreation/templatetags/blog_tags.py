from django import template
from django.utils import timezone
from ..models import Post
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

register = template.Library()

@register.filter
def custom_filter(value):
    return f"Custom: {value}"

@register.filter
def upper(value):
    return value.upper()

@register.filter
def lower(value):
    return value.lower()

@register.simple_tag
def current_time():
    return timezone.now()

@register.simple_tag
def create_thumbnail(image_path, size=(100, 100)):
    image = Image.open(image_path)
    image.thumbnail(size)
    thumb_io = BytesIO()
    image.save(thumb_io, 'JPEG')
    return ContentFile(thumb_io.getvalue(), name=image_path.name)

@register.inclusion_tag('blog/post_list.html')
def show_posts(count=5):
    posts = Post.objects.filter(status='published')[:count]
    return {'posts': posts}

@register.simple_tag
def format_post(post):
    return f"{post.title} by {post.author}"

@register.simple_tag
def get_recent_posts(count=5):
    return Post.objects.filter(status='published').order_by('-publish')[:count]
