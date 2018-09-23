"""website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    url('^$', views.index, name='index'),
    url('^control/$', views.control, name="control"),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^controlJSON/([a-zA-z]+)/$', views.controlJSON),
    url(r'^createJSON/([a-zA-z]+)/$', views.createJSON),
    url(r'^updatesJSON/$', views.getUpdatesJSON),
    url(r'^uploadJSON/$', views.uploadJSON),
    url(r'^encodeJSON/([0-9]+)/([0-9]+)/$', views.encodeJSON),

]

