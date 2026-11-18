
from rest_framework.routers import DefaultRouter
from .api import ReviewViewSet

router = DefaultRouter()
router.register('reviews', ReviewViewSet, basename='review')

urlpatterns = router.urls