import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from library.models import Book, Reader, Checkout


class Command(BaseCommand):
    help = 'Adds fake data to the database for testing purposes'

    def __init__(self):
        super().__init__()
        self.fake = Faker()
        self.created_readers = []
        self.created_books = []
        self.created_checkouts = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--readers',
            type=int,
            default=10,
            help='Number of readers to generate (default: 10)'
        )
        parser.add_argument(
            '--books',
            type=int,
            default=20,
            help='Number of books to generate (default: 20)'
        )
        parser.add_argument(
            '--checkouts',
            type=int,
            default=15,
            help='Number of checkouts to generate (default: 15)'
        )

    def handle(self, *args, **options):
        readers_count = options['readers']
        books_count = options['books']
        checkouts_count = options['checkouts']
        
        self.generate_readers(readers_count)
        self.generate_books(books_count)
        self.generate_checkouts(checkouts_count, books_count)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully generated:\n'
                f'  {len(self.created_readers)} readers\n'
                f'  {len(self.created_books)} books\n'
                f'  {len(self.created_checkouts)} checkouts'
            )
        )

    def generate_readers(self, count):
        self.stdout.write('Creating readers...')
        for _ in range(count):
            reader = self.create_single_reader()
            self.created_readers.append(reader)

    def create_single_reader(self):
        card_number = self.fake.unique.numerify(text='######')
        name = self.fake.name()
        return Reader.objects.create(
            card_number=card_number,
            name=name
        )

    def generate_books(self, count):
        self.stdout.write('Creating books...')
        for _ in range(count):
            book = self.create_single_book()
            self.created_books.append(book)

    def create_single_book(self):
        serial_number = self.fake.unique.numerify(text='######')
        title = self.fake.catch_phrase()
        author = self.fake.name()
        return Book.objects.create(
            serial_number=serial_number,
            title=title,
            author=author
        )

    def generate_checkouts(self, checkouts_count, books_count):
        self.stdout.write('Creating checkouts...')
        
        books_to_checkout = books_count // 2
        active_books = self.select_books_for_active_checkouts(books_to_checkout)
        
        self.create_checkouts_batch(checkouts_count, active_books, books_to_checkout)

    def select_books_for_active_checkouts(self, count):
        random.shuffle(self.created_books)
        return self.created_books[:count]

    def create_checkouts_batch(self, checkouts_count, active_books, books_to_checkout):
        active_checkouts_count = 0
        
        for i in range(min(checkouts_count, len(self.created_readers) * len(self.created_books))):
            reader = random.choice(self.created_readers)
            should_be_active = active_checkouts_count < books_to_checkout and i < checkouts_count
            
            if should_be_active and active_books:
                checkout = self.create_active_checkout(active_books.pop(), reader)
                active_checkouts_count += 1
            else:
                checkout = self.create_historical_checkout(reader)
            
            self.created_checkouts.append(checkout)

    def create_active_checkout(self, book, reader):
        checkout = Checkout.objects.create(
            book=book,
            reader=reader,
            checked_out_at=self.fake.date_time_between(
                start_date='-30d',
                end_date='now',
                tzinfo=timezone.get_current_timezone()
            )
        )
        book.active_checkout = checkout
        book.save()
        return checkout

    def create_historical_checkout(self, reader):
        book = random.choice(self.created_books)
        checkout_date = self.fake.date_time_between(
            start_date='-60d',
            end_date='-5d',
            tzinfo=timezone.get_current_timezone()
        )
        return_date = checkout_date + timedelta(days=random.randint(1, 14))
        
        return Checkout.objects.create(
            book=book,
            reader=reader,
            checked_out_at=checkout_date,
            returned_at=return_date
        )