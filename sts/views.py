import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from .models import System
from .utils import get_natural_duration


def serialize(system):
    transitions = []

    last = None
    for trans in system.transitions.select_related('event', 'state'):

        if last:
            delay = get_natural_duration(last.end_time, trans.start_time)
        else:
            delay = None

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
        last = trans

    return {
        'name': unicode(system),
        'created': system.created,
        'modified': system.modified,
        'transitions': transitions,
    }


def systems(request):
    return render(request, 'sts/systems.html', {
    })


def system_detail(request, pk):
    system = get_object_or_404(System, pk=pk)
    data = json.dumps(serialize(system), cls=DjangoJSONEncoder)

    if request.is_ajax():
        return HttpResponse(data, mimetype='application/json')

    return render(request, 'sts/system_detail.html', {
        'system': system,
        'json': data,
    })
