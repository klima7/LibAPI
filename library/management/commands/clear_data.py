from django.core.management.base import BaseCommand
from library.models import Book, Reader, Checkout


class Command(BaseCommand):
    help = 'Clears all data from the database (books, readers, checkouts)'

    def handle(self, *args, **options):
        self.stdout.write('Deleting all data...')
        
        Checkout.objects.all().delete()
        Book.objects.all().delete()
        Reader.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('All data has been deleted.'))