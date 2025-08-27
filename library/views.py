from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Book, Reader, Checkout
from .serializers import (
    BookSerializer, ReaderSerializer, CheckoutSerializer,
    CheckoutActionSerializer
)
from .filters import CheckoutFilter


class BookViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Book.objects.select_related('active_checkout__reader').all()
    serializer_class = BookSerializer
    lookup_field = 'serial_number'

    @swagger_auto_schema(
        method='post',
        request_body=CheckoutActionSerializer,
        responses={
            201: CheckoutSerializer,
            400: 'Bad Request - Book already checked out or invalid data',
            404: 'Book not found'
        }
    )
    @action(detail=True, methods=['post'])
    def checkout(self, request, serial_number=None):
        book = self.get_object()
        
        if book.active_checkout:
            return Response(
                {'error': 'Book is already checked out'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CheckoutActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Get or create reader
            reader, created = Reader.objects.get_or_create(
                card_number=serializer.validated_data['card_number'],
                defaults={'name': serializer.validated_data.get('reader_name', '')}
            )
            
            # Create checkout
            checkout = Checkout.objects.create(
                book=book,
                reader=reader
            )
            
            # Update book's active checkout
            book.active_checkout = checkout
            book.save()
        
        return Response(
            CheckoutSerializer(checkout).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        method='post',
        responses={
            200: CheckoutSerializer,
            400: 'Bad Request - Book is not checked out',
            404: 'Book not found'
        }
    )
    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, serial_number=None):
        book = self.get_object()
        
        if not book.active_checkout:
            return Response(
                {'error': 'Book is not checked out'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            checkout = book.active_checkout
            checkout.returned_at = timezone.now()
            checkout.save()
            
            book.active_checkout = None
            book.save()
        
        return Response(
            CheckoutSerializer(checkout).data,
            status=status.HTTP_200_OK
        )


class ReaderViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    queryset = Reader.objects.all()
    serializer_class = ReaderSerializer
    lookup_field = 'card_number'


class CheckoutViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Checkout.objects.select_related('book', 'reader').all()
    serializer_class = CheckoutSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CheckoutFilter
    ordering = ['-checked_out_at']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'book',
                openapi.IN_QUERY,
                description='Filter by book serial number',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'reader',
                openapi.IN_QUERY,
                description='Filter by reader card number',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_active',
                openapi.IN_QUERY,
                description='Filter by active status (true/false)',
                type=openapi.TYPE_BOOLEAN
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
