from django.db import models


class Book(models.Model):
    serial_number = models.CharField(max_length=6, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    active_checkout = models.OneToOneField(
        'Checkout', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='active_for_book'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Reader(models.Model):
    card_number = models.CharField(max_length=6, unique=True)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Checkout(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='checkouts')
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='checkouts')
    checked_out_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
