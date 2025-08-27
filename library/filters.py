import django_filters
from .models import Checkout


class CheckoutFilter(django_filters.FilterSet):
    book = django_filters.CharFilter(field_name='book__serial_number')
    reader = django_filters.CharFilter(field_name='reader__card_number')
    is_active = django_filters.BooleanFilter(method='filter_is_active')

    class Meta:
        model = Checkout
        fields = ['book', 'reader', 'is_active']

    def filter_is_active(self, queryset, name, value):
        if value is True:
            return queryset.filter(returned_at__isnull=True)
        elif value is False:
            return queryset.filter(returned_at__isnull=False)
        return queryset