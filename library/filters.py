import django_filters
from .models import Book, Reader, Checkout


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.CharFilter(lookup_expr='icontains')
    is_available = django_filters.BooleanFilter(method='filter_is_available')
    current_reader = django_filters.NumberFilter(field_name='active_checkout__reader__id')

    class Meta:
        model = Book
        fields = ['title', 'author', 'is_available', 'current_reader']

    def filter_is_available(self, queryset, name, value):
        if value is True:
            return queryset.filter(active_checkout__isnull=True)
        elif value is False:
            return queryset.filter(active_checkout__isnull=False)
        return queryset


class ReaderFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Reader
        fields = ['name']


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