import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from .models import System
from .utils import get_natural_duration


def _system(system):
    last = None
    transitions = []

    for trans in system.transitions.select_related('event', 'state'):
        # Get the delay from the last transition if one exists
        if last:
            delay = get_natural_duration(last.end_time, trans.start_time)
        else:
            delay = None

        last = trans

        transitions.append({
            'id': trans.pk,
            'state': unicode(trans.state),
            'event': trans.event_id and unicode(trans.event) or None,
            'message': trans.message,
            'failed': trans.failed,
            'start_time': trans.start_time,
            'end_time': trans.end_time,
            'duration': trans.current_duration,
            'natural_duration': trans.natural_duration,
            'delay': delay,
        })

    return {
        'name': unicode(system),
        'created': system.created,
        'modified': system.modified,
        'url': reverse('sts-system-detail', kwargs={'pk': system.pk}),
        'transitions': transitions,
    }


def _system_urls(systems):
    urls = []

    for system in systems:
        urls.append({
            'name': unicode(system),
            'created': system.created,
            'modified': system.modified,
            'url': reverse('sts-system-detail', kwargs={'pk': system.pk}),
        })

    return urls


def systems(request):
    systems = System.objects.all()
    data = json.dumps(_system_urls(systems), cls=DjangoJSONEncoder)

    if request.is_ajax():
        return HttpResponse(data, mimetype='application/json')

    return render(request, 'sts/systems.html', {
        'system_links': data,
    })


def system_detail(request, pk):
    system = get_object_or_404(System, pk=pk)

    if request.is_ajax():
        data = json.dumps(_system(system), cls=DjangoJSONEncoder)
        return HttpResponse(data, mimetype='application/json')

    return render(request, 'sts/system_detail.html', {
        'system': system,
    })
