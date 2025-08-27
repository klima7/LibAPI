from rest_framework import serializers
from .models import Book, Reader, Checkout


class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = ['card_number', 'name', 'created_at']
        read_only_fields = ['created_at']

    def validate_card_number(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Card number must be exactly 6 digits")
        return value


class CheckoutSerializer(serializers.ModelSerializer):
    book_serial = serializers.CharField(source='book.serial_number', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    reader_card = serializers.CharField(source='reader.card_number', read_only=True)
    reader_name = serializers.CharField(source='reader.name', read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Checkout
        fields = [
            'id', 'book_serial', 'book_title', 'reader_card', 
            'reader_name', 'checked_out_at', 'returned_at', 'is_active'
        ]
        read_only_fields = ['checked_out_at']

    def get_is_active(self, obj):
        return obj.returned_at is None


class BookSerializer(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()
    current_reader = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'serial_number', 'title', 'author', 'is_available',
            'current_reader', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_serial_number(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Serial number must be exactly 6 digits")
        return value

    def get_is_available(self, obj):
        return obj.active_checkout is None

    def get_current_reader(self, obj):
        if obj.active_checkout:
            return {
                'card_number': obj.active_checkout.reader.card_number,
                'name': obj.active_checkout.reader.name,
                'checked_out_at': obj.active_checkout.checked_out_at
            }
        return None


class CreateCheckoutSerializer(serializers.Serializer):
    book_serial = serializers.CharField(max_length=6)
    card_number = serializers.CharField(max_length=6)

    def validate_book_serial(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Book serial number must be exactly 6 digits")
        return value

    def validate_card_number(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Card number must be exactly 6 digits")
        return value