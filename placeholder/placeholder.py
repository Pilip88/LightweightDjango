import os
import sys
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw

from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.conf.urls import url
from django.core.wsgi import get_wsgi_application
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.views.decorators.http import etag


# settings
DEBUG = os.environ.get('DEBUG', 'on') == 'on'
SECRET_KEY = os.environ.get(
                    'SECRET_KEY',
                    'hzhik8s61ar@4n-ci82l1p8yufw)q=5+%_uyxm^yhpm&=3up8v')
BASE_DIR = os.path.dirname(__file__)
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

settings.configure(
        DEBUG=DEBUG,
        SECRET_KEY=SECRET_KEY,
        ALLOWED_HOSTS=ALLOWED_HOSTS,
        ROOT_URLCONF=__name__,
        MIDDLEWARE_CLASSES=(
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ),
        INSTALLED_APPS=(
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
            ),
        TEMPLATE_DIRS=(
                os.path.join(BASE_DIR, 'templates'),
            ),
        STATICFILES_DIRS=(
                os.path.join(BASE_DIR, 'static'),
            ),
        STATIC_URL='/static/',
        )


# forms
class ImageForm(forms.Form):

    """Form to validate requested placeholder image"""
    height = forms.IntegerField(min_value=1, max_value=2000)
    width = forms.IntegerField(min_value=1, max_value=2000)

    def generate(self, image_format='PNG'):
        """Generate an image of the given type ande return as raw bytes."""
        height = self.cleaned_data['height']
        width = self.cleaned_data['width']
        key = '{}.{}.{}'.format(width, height, image_format)
        content = cache.get(key)
        if content is None:
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            text = '{} x {}'.format(width, height)
            textwidth, textheight = draw.textsize(text)
            if textwidth < width and textheight < height:
                texttop = (height - textheight) // 2
                textleft = (width - textwidth) // 2
                draw.text((textleft, texttop), text, fill=(255, 255, 255))
            content = BytesIO()
            image.save(content, image_format)
            content.seek(0)
            cache.set(key, content, 60*60)
        return content


# views
def generate_etag(request, width, height):
    content = 'Placeholder: {} x {}'.format(width, height)
    return hashlib.sha1(content.encode('utf-8')).hexdigest()


@etag(generate_etag)
def placeholder(request, width, height):
    form = ImageForm({'height': height, 'width': width})
    if form.is_valid():
        image = form.generate()
        return HttpResponse(image, content_type='image/png')
    else:
        return HttpResponseBadRequest('Invalid Image Request.')


def index(request):
    example = reverse('placeholder', kwargs={'width': 50, 'height': 50})
    context = {
        'example': request.build_absolute_uri(example)
    }
    return render(request, 'home.html', context)


# urls
urlpatterns = (
        url(
            r'^$',
            index,
            name='homepage'),
        url(
            r'^image/(?P<width>[0-9]+)x(?P<height>[0-9]+)/$',
            placeholder,
            name='placeholder'),
    )


# wsgi
application = get_wsgi_application()

# manage
if __name__ == '__main__':
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)