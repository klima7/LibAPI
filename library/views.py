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
    CreateCheckoutSerializer
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

    @swagger_auto_schema(
        method='post',
        request_body=CreateCheckoutSerializer,
        responses={
            201: CheckoutSerializer,
            400: 'Bad Request - Book already checked out or invalid data',
            404: 'Book not found'
        }
    )
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        serializer = CreateCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            book = Book.objects.get(serial_number=serializer.validated_data['book_serial'])
        except Book.DoesNotExist:
            return Response(
                {'error': 'Book not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if book.active_checkout:
            return Response(
                {'error': 'Book is already checked out'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Get or create reader
            reader, created = Reader.objects.get_or_create(
                card_number=serializer.validated_data['card_number']
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
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT),
        responses={
            200: CheckoutSerializer,
            400: 'Bad Request - Book is not checked out or already returned',
            404: 'Checkout not found'
        }
    )
    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, pk=None):
        checkout = self.get_object()
        
        if checkout.returned_at:
            return Response(
                {'error': 'Book has already been returned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            checkout.returned_at = timezone.now()
            checkout.save()
            
            # Clear book's active checkout
            book = checkout.book
            if book.active_checkout_id == checkout.id:
                book.active_checkout = None
                book.save()
        
        return Response(
            CheckoutSerializer(checkout).data,
            status=status.HTTP_200_OK
        )
