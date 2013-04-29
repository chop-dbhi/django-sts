from django.conf.urls import url, patterns
from . import views


urlpatterns = patterns('',
    url(r'^$', views.systems, name='sts-systems'),
    url(r'^(?P<pk>\d+)/$', views.systems, name='sts-system-detail'),
)
