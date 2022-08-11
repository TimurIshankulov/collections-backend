from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (SignUpView, UserView, ProfileView, AddCardToCollectionView,
                    AddCardView, AddCardAdminView, CraftCardView, TurnCardIntoDustView,
                    CardsBulkView, CollectionProgressView, GetUserStatisticsView,
                    IsAddableToCollectionView, IsDailyCardAvailableView, IsCraftableView)
from .views import CardViewSet, CollectionViewSet, MyCardsViewSet

router = DefaultRouter()
router.register('cards', CardViewSet, basename='cards')
router.register('collections', CollectionViewSet, basename='collections')
router.register('my/cards', MyCardsViewSet, basename='my_cards')

urlpatterns = [
    path('', include(router.urls)),
    path('signup/', SignUpView.as_view()),
    path('user/', UserView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('add_card_to_collection/<int:entry_id>', AddCardToCollectionView.as_view()),
    path('add_card/', AddCardView.as_view()),
    path('add_card_admin/', AddCardAdminView.as_view()),
    path('craft_card/<int:card_id>', CraftCardView.as_view()),
    path('turn_to_dust/<int:entry_id>', TurnCardIntoDustView.as_view()),
    path('cards_bulk/', CardsBulkView.as_view()),
    path('collection_progress/<int:collection_id>', CollectionProgressView.as_view()),
    path('get_user_statistics/', GetUserStatisticsView.as_view()),
    path('is_addable/<int:entry_id>', IsAddableToCollectionView.as_view()),
    path('is_daily_card_available/', IsDailyCardAvailableView.as_view()),
    path('is_craftable/<int:card_id>', IsCraftableView.as_view()),
]