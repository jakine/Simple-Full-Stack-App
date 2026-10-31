from core.models import ActivityEvent


def target_label(target):
    return target._meta.label_lower


def record_event(request, verb, target, project=None, data=None):
    return ActivityEvent.objects.create(
        company=request.company,
        actor=request.user if request.user.is_authenticated else None,
        project=project,
        verb=verb,
        target_type=target_label(target),
        target_id=target.pk,
        data=data or {},
    )


def events_for(target, company=None):
    queryset = ActivityEvent.objects.filter(
        target_type=target_label(target),
        target_id=target.pk,
    ).select_related("actor")
    if company is not None:
        queryset = queryset.filter(company=company)
    return queryset
