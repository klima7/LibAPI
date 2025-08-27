from rest_framework.routers import DefaultRouter
from .views import BookViewSet, ReaderViewSet, CheckoutViewSet

router = DefaultRouter()
router.register('books', BookViewSet, basename='book')
router.register('readers', ReaderViewSet, basename='reader')
router.register('checkouts', CheckoutViewSet, basename='checkout')

urlpatterns = router.urls