from io import StringIO
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.management import call_command
from django.test import TestCase
from .models import Book, Reader, Checkout


class BookAPITest(APITestCase):
    def setUp(self):
        # Create test data
        self.book1 = Book.objects.create(
            serial_number='123456',
            title='Test Book 1',
            author='Author 1'
        )
        self.book2 = Book.objects.create(
            serial_number='234567',
            title='Test Book 2',
            author='Author 2'
        )
        
    def test_create_book(self):
        """Test creating a book with valid data"""
        url = reverse('book-list')
        data = {
            'serial_number': '345678',
            'title': 'New Book',
            'author': 'New Author'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)
        self.assertEqual(response.data['serial_number'], '345678')
        
    def test_create_book_invalid_serial(self):
        """Test creating a book with invalid serial number"""
        url = reverse('book-list')
        data = {
            'serial_number': '12345',  # Only 5 digits
            'title': 'Invalid Book',
            'author': 'Author'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_list_books_with_pagination(self):
        """Test listing books with pagination"""
        # Create more books for pagination
        for i in range(60):
            Book.objects.create(
                serial_number=f'{100000 + i}',
                title=f'Book {i}',
                author=f'Author {i}'
            )
        
        url = reverse('book-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 50)  # Default page size
        self.assertIn('next', response.data)
        
    def test_filter_books_by_availability(self):
        """Test filtering books by availability status"""
        # Create a checkout for book1
        reader = Reader.objects.create(card_number='111111', name='Test Reader')
        checkout = Checkout.objects.create(book=self.book1, reader=reader)
        self.book1.active_checkout = checkout
        self.book1.save()
        
        url = reverse('book-list')
        # Test available books
        response = self.client.get(url, {'is_available': 'true'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['serial_number'], '234567')
        
        # Test unavailable books
        response = self.client.get(url, {'is_available': 'false'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['serial_number'], '123456')
        
    def test_delete_book_cascades_checkouts(self):
        """Test that deleting a book deletes all its checkouts"""
        reader = Reader.objects.create(card_number='222222', name='Reader')
        Checkout.objects.create(book=self.book1, reader=reader)
        
        self.assertEqual(Checkout.objects.count(), 1)
        
        url = reverse('book-detail', kwargs={'serial_number': '123456'})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Checkout.objects.count(), 0)


class ReaderAPITest(APITestCase):
    def setUp(self):
        self.reader1 = Reader.objects.create(
            card_number='111111',
            name='Reader One'
        )
        self.book = Book.objects.create(
            serial_number='123456',
            title='Test Book',
            author='Test Author'
        )
        
    def test_create_reader(self):
        """Test creating a reader"""
        url = reverse('reader-list')
        data = {
            'card_number': '222222',
            'name': 'New Reader'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reader.objects.count(), 2)
        
    def test_delete_reader_cascades_checkouts(self):
        """Test that deleting a reader deletes their checkouts"""
        checkout = Checkout.objects.create(book=self.book, reader=self.reader1)
        self.assertEqual(Checkout.objects.count(), 1)
        
        url = reverse('reader-detail', kwargs={'card_number': '111111'})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reader.objects.count(), 0)
        self.assertEqual(Checkout.objects.count(), 0)
        
    def test_delete_reader_clears_book_active_checkout(self):
        """Test that deleting a reader clears the active_checkout in book"""
        checkout = Checkout.objects.create(book=self.book, reader=self.reader1)
        self.book.active_checkout = checkout
        self.book.save()
        
        url = reverse('reader-detail', kwargs={'card_number': '111111'})
        response = self.client.delete(url)
        
        self.book.refresh_from_db()
        self.assertIsNone(self.book.active_checkout)


class CheckoutAPITest(APITestCase):
    def setUp(self):
        self.book1 = Book.objects.create(
            serial_number='123456',
            title='Available Book',
            author='Author'
        )
        self.book2 = Book.objects.create(
            serial_number='234567',
            title='Another Book',
            author='Author'
        )
        self.reader = Reader.objects.create(
            card_number='111111',
            name='Test Reader'
        )
        
    def test_checkout_book_success(self):
        """Test successful book checkout"""
        url = reverse('checkout-checkout')
        data = {
            'book_serial': '123456',
            'card_number': '111111'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book1.refresh_from_db()
        self.assertIsNotNone(self.book1.active_checkout)
        self.assertEqual(Checkout.objects.count(), 1)
        
    def test_checkout_already_borrowed_book(self):
        """Test checking out an already borrowed book"""
        # First checkout
        checkout = Checkout.objects.create(book=self.book1, reader=self.reader)
        self.book1.active_checkout = checkout
        self.book1.save()
        
        # Create another reader for the second checkout attempt
        reader2 = Reader.objects.create(card_number='222222', name='Another Reader')
        
        # Try to checkout again with different reader
        url = reverse('checkout-checkout')
        data = {
            'book_serial': '123456',
            'card_number': '222222'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already checked out', response.data['error'])
        
    def test_checkout_with_nonexistent_reader(self):
        """Test that checkout fails when reader doesn't exist"""
        url = reverse('checkout-checkout')
        data = {
            'book_serial': '123456',
            'card_number': '999999'  # Non-existent reader
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Reader not found', response.data['error'])
        self.assertFalse(Reader.objects.filter(card_number='999999').exists())
    
    def test_checkout_with_nonexistent_book(self):
        """Test that checkout fails when book doesn't exist"""
        url = reverse('checkout-checkout')
        data = {
            'book_serial': '999999',  # Non-existent book
            'card_number': '111111'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Book not found', response.data['error'])
        
    def test_return_book_success(self):
        """Test successful book return"""
        # Create active checkout
        checkout = Checkout.objects.create(book=self.book1, reader=self.reader)
        self.book1.active_checkout = checkout
        self.book1.save()
        
        url = reverse('checkout-return-book', kwargs={'pk': checkout.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book1.refresh_from_db()
        self.assertIsNone(self.book1.active_checkout)
        
        checkout.refresh_from_db()
        self.assertIsNotNone(checkout.returned_at)
        
    def test_return_already_returned_book(self):
        """Test returning an already returned book"""
        from django.utils import timezone
        checkout = Checkout.objects.create(
            book=self.book1,
            reader=self.reader,
            returned_at=timezone.now()
        )
        
        url = reverse('checkout-return-book', kwargs={'pk': checkout.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been returned', response.data['error'])
        
    def test_list_checkouts_with_filters(self):
        """Test listing checkouts with various filters"""
        # Create checkouts
        checkout1 = Checkout.objects.create(book=self.book1, reader=self.reader)
        self.book1.active_checkout = checkout1
        self.book1.save()
        
        from django.utils import timezone
        checkout2 = Checkout.objects.create(
            book=self.book2,
            reader=self.reader,
            returned_at=timezone.now()
        )
        
        url = reverse('checkout-list')
        
        # Filter by active status
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], checkout1.id)
        
        # Filter by reader
        response = self.client.get(url, {'reader': '111111'})
        self.assertEqual(len(response.data['results']), 2)


class ManagementCommandsTest(TestCase):
    def test_add_fake_data_command_with_defaults(self):
        """Test add_fake_data command with default parameters"""
        out = StringIO()
        call_command('add_fake_data', stdout=out)
        
        self.assertEqual(Reader.objects.count(), 10)
        self.assertEqual(Book.objects.count(), 20)
        self.assertEqual(Checkout.objects.count(), 15)
        
        active_checkouts = Checkout.objects.filter(returned_at__isnull=True).count()
        self.assertGreater(active_checkouts, 0)
        self.assertLessEqual(active_checkouts, 10)
    
    def test_add_fake_data_command_with_custom_params(self):
        """Test add_fake_data command with custom parameters"""
        out = StringIO()
        call_command('add_fake_data', readers=5, books=10, checkouts=8, stdout=out)
        
        self.assertEqual(Reader.objects.count(), 5)
        self.assertEqual(Book.objects.count(), 10)
        self.assertEqual(Checkout.objects.count(), 8)
    
    def test_clear_data_command(self):
        """Test clear_data command removes all data"""
        Book.objects.create(
            serial_number='123456',
            title='Test Book',
            author='Test Author'
        )
        Reader.objects.create(
            card_number='111111',
            name='Test Reader'
        )
        
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Reader.objects.count(), 1)
        
        out = StringIO()
        call_command('clear_data', stdout=out)
        
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Reader.objects.count(), 0)
        self.assertEqual(Checkout.objects.count(), 0)
    
    def test_commands_integration(self):
        """Test that commands work together correctly"""
        out = StringIO()
        call_command('add_fake_data', readers=3, books=6, checkouts=4, stdout=out)
        self.assertEqual(Book.objects.count(), 6)
        self.assertEqual(Reader.objects.count(), 3)
        
        call_command('clear_data', stdout=out)
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Reader.objects.count(), 0)
        
        call_command('add_fake_data', readers=2, books=4, checkouts=2, stdout=out)
        self.assertEqual(Book.objects.count(), 4)
        self.assertEqual(Reader.objects.count(), 2)
