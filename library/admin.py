from django.contrib import admin
from .models import Book, Reader, Checkout


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'title', 'author', 'active_checkout')
    search_fields = ('serial_number', 'title', 'author')


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'name', 'created_at')
    search_fields = ('card_number', 'name')


@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display = ('book', 'reader', 'checked_out_at', 'returned_at')
    list_filter = ('checked_out_at', 'returned_at')
    search_fields = ('book__title', 'reader__card_number')
