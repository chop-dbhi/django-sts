import json
from django.http import HttpResponse
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from .models import System
from .utils import get_natural_duration


def _system(system, include_transitions=True):
    data = {
        'id': system.pk,
        'name': unicode(system),
        'created': system.created,
        'modified': system.modified,
        'url': reverse('sts-system-detail', kwargs={'pk': system.pk}),
        'in_transition': system.in_transition(),
        'failed_last_transition': system.failed_last_transition(),
    }

    if system.content_type_id:
        content_type = unicode(system.content_type).title()
    else:
        content_type = None

    data['content_type'] = content_type

    if include_transitions:
        data['transitions'] = _transitions(system)
    return data


def _transitions(system):
    last = None
    data = []

    for trans in system.transitions.select_related('event', 'state'):
        # Get the delay from the last transition if one exists
        if last:
            delay = get_natural_duration(last.end_time, trans.start_time)
        else:
            delay = None

        last = trans

        data.append({
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

    return data


def _systems(systems, include_transitions=True):
    data = []

    for system in systems:
        # Ignore orphaned systems
        if system.object_id and not system.content_object:
            continue
        data.append(_system(system, include_transitions=include_transitions))

    return data


def systems(request, pk=None):
    systems = System.objects.annotate(count=Count('transitions')).filter(count__gt=0)

    if pk:
        data = _system(get_object_or_404(systems, pk=pk))
    else:
        data = _systems(systems, include_transitions=False)

    if request.is_ajax():
        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder),
            mimetype='application/json')
    return render(request, 'sts/systems.html')
