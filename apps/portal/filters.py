"""So'rov parametrlarini o'qish. Noto'g'ri qiymatda tushunarli 400 qaytadi."""

from rest_framework.exceptions import ValidationError

# Viloyat/tuman id yoki slug bo'yicha - monitoring bilan bir xil qoida
from apps.monitoring.filters import resolve_district, resolve_region  # noqa: F401


def get_bool(request, name):
    """true/false yoki berilmagan bo'lsa None."""
    raw = (request.query_params.get(name) or '').strip().lower()
    if not raw:
        return None
    if raw in ('1', 'true', 'yes'):
        return True
    if raw in ('0', 'false', 'no'):
        return False
    raise ValidationError({name: "true yoki false bo'lishi kerak."})


def get_int(request, name, minimum=None, maximum=None):
    raw = (request.query_params.get(name) or '').strip()
    if not raw:
        return None
    if not raw.lstrip('-').isdigit():
        raise ValidationError({name: "Butun son bo'lishi kerak."})
    value = int(raw)
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValidationError({name: f"{minimum} va {maximum} oralig'ida bo'lishi kerak."})
    return value


def get_list(request, name):
    raw = request.query_params.get(name) or ''
    return [item.strip().lower() for item in raw.split(',') if item.strip()]


def get_choice(request, name, choices):
    raw = (request.query_params.get(name) or '').strip()
    if not raw:
        return None
    if raw not in choices:
        raise ValidationError({name: f"Mumkin qiymatlar: {', '.join(choices)}"})
    return raw
