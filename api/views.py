import random
import datetime
import pytz

from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import pagination
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings

from .serializers import (SignUpSerializer, UserSerializer, ProfileSerializer,
                          CardSerializer, CollectionSerializer, CardEntrySerializer)
from .models import Card, Collection, CardEntry

# Static variables with error description
MESSAGE_USER_CREATED_SUCCESS = 'Успех. Пользователь создан.'
MESSAGE_ADD_CARD_TO_COLLECTION_SUCCESS = 'Успех. Карточка добавлена в коллекцию.'
MESSAGE_TURN_TO_DUST_SUCCESS = 'Успех. Карточка превращена в пыль.'

ERROR_ADD_CARD_SOURCE_REQUIRED = 'Ошибка. Укажите источник получения карточки.'
ERROR_ADD_CARD_DAILY_REFUSED = 'Ошибка. Отказано в получении ежедневной карточки.'
ERROR_ADD_CARD_TO_COLLECTION_DUPLICATE = 'Ошибка. Карточка с таким ID уже находится в коллекции.'
ERROR_CRAFT_CARD_NOT_ENOUGH_DUST = 'Ошибка. Недостаточно пыли для создания карточки.'
ERROR_CRAFT_CARD_ALREADY_IN_COLLECTION = 'Ошибка. Карточка с таким ID уже находится в коллекции'
ERROR_CARD_ENTRY_DOES_NOT_EXIST = 'Ошибка. Записи с указанным ID не существует.'
ERROR_CARD_DOES_NOT_EXIST = 'Ошибка. Карточки с указанным ID не существует.'
ERROR_CARD_ENTRY_USER_INCORRECT = 'Ошибка. Неверно указано имя пользователя.'

random.seed()


class SignUpView(generics.GenericAPIView):
    """View for signing up"""
    permission_classes = [permissions.AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request, *args,  **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        message = {'user': SignUpSerializer(user, context=self.get_serializer_context()).data,
                   'message': MESSAGE_USER_CREATED_SUCCESS}
        return Response(message)


class UserView(generics.GenericAPIView):
    """View for User"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args,  **kwargs):
        message = {'user': UserSerializer(request.user, context=self.get_serializer_context()).data}
        return Response(message)


class ProfileView(generics.GenericAPIView):
    """View for Profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get(self, request, *args,  **kwargs):
        message = {'user': ProfileSerializer(request.user.profile, context=self.get_serializer_context()).data}
        return Response(message)


class CardPagination(pagination.PageNumberPagination):
    """Pagination class for Card list"""
    page_size = 18
    page_size_query_param = 'page_size'


class CardViewSet(viewsets.ModelViewSet):
    """ViewSet for Cards. Lookup field is 'id'."""
    search_fields = ['name', 'short_description', 'long_description']
    filter_backends = (filters.SearchFilter,)
    serializer_class = CardSerializer
    queryset = Card.objects.all()
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CardPagination


class CollectionPagination(pagination.PageNumberPagination):
    """Pagination class for Collection list"""
    page_size = 10
    page_size_query_param = 'page_size'
    ordering = 'created'


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Collections. Lookup field is 'id'."""
    search_fields = ['name', 'description']
    filter_backends = (filters.SearchFilter,)
    serializer_class = CollectionSerializer
    queryset = Collection.objects.all()
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CollectionPagination


class MyCardsPagination(pagination.PageNumberPagination):
    """Pagination class for MyCards list"""
    page_size = 18
    page_size_query_param = 'page_size'


class MyCardsViewSet(viewsets.ModelViewSet):
    """ViewSet for MyCards. Lookup field is 'id'."""
    search_fields = ['name', 'short_description', 'long_description']
    filter_backends = (filters.SearchFilter,)
    serializer_class = CardEntrySerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MyCardsPagination

    def get_queryset(self):
        user = self.request.user
        queryset = CardEntry.objects.filter(user=user).order_by('card__name')
        return queryset


class AddCardToCollectionView(generics.GenericAPIView):
    """
    View for adding card to User's collection.
    Checks if CardEntry exists, if user in request is the same user in
    CardEntry and if Card is not already in a collection. If everything
    is ok, adds card to a collection, checks if collection is completed
    and adds it to collection list if completed.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CardSerializer

    def post(self, request, *args,  **kwargs):
        try:
            card_entry = CardEntry.objects.get(id=self.kwargs['entry_id'])
        except CardEntry.DoesNotExist:
            message = {'error': ERROR_CARD_ENTRY_DOES_NOT_EXIST}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        user = card_entry.user
        if user != request.user:
            message = {'error': ERROR_CARD_ENTRY_USER_INCORRECT}
            return Response(message, status=status.HTTP_403_FORBIDDEN)

        card = card_entry.card
        cards_list = list(user.profile.cards.all().values())
        cards_list = [c['id'] for c in cards_list]

        if card.id in cards_list:
            message = {'error': ERROR_ADD_CARD_TO_COLLECTION_DUPLICATE}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        user.profile.cards.add(card)
        collection = card.related_collection
        collection_cards = list(collection.cards.values_list('id', flat=True))
        user_profile_cards = list(user.profile.cards.values_list('id', flat=True))

        completed = True
        for collection_card in collection_cards:
            if collection_card not in user_profile_cards:
                completed = False
                break
        if completed:
            user.profile.collections.add(collection)

        user.profile.save()
        card_entry.delete()

        message = {'card': CardSerializer(card, context=self.get_serializer_context()).data,
                   'message': MESSAGE_ADD_CARD_TO_COLLECTION_SUCCESS}
        return Response(message)


class AddCardView(generics.GenericAPIView):
    """
    Adds card to a User card list.
    If source is daily Card, then checks the data when last card was
    acquired. Randomize the card that User will receive and adds CardEntry.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CardEntrySerializer

    def post(self, request, *args,  **kwargs):
        source = request.GET.get('source', None)
        if source is None:
            message = {'error': ERROR_ADD_CARD_SOURCE_REQUIRED}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        if source == 'daily':
            last_daily = CardEntry.objects.filter(user=request.user).filter(source='daily').last()
            if last_daily is None:
                last_date = datetime.date(year=2000, month=1, day=1)
            else:
                last_date = last_daily.acquired
                
            today = datetime.datetime.now(pytz.utc)
            if today.date() == last_date.date():
                message = {'error': ERROR_ADD_CARD_DAILY_REFUSED}
                return Response(message, status=status.HTTP_400_BAD_REQUEST)

        chance = random.randint(1, 100)
        if chance <= 70:
            rarity = 'common'
        elif 70 < chance <= 90:
            rarity = 'rare'
        elif 90 < chance <= 100:
            rarity = 'epic'

        cards = list(Card.objects.filter(rarity=rarity).all())
        random_card = random.choice(cards)
        card_entry = CardEntry()
        card_entry.card = random_card
        card_entry.user = request.user
        card_entry.source = source
        card_entry.save()

        message = {'card': CardEntrySerializer(card_entry, context=self.get_serializer_context()).data}
        return Response(message)


class AddCardAdminView(generics.GenericAPIView):
    """
    Adds card to a User card list.
    This is admin view. No restriction defined.
    Randomize the card that User will receive and adds CardEntry.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CardEntrySerializer

    def post(self, request, *args,  **kwargs):
        source = request.GET.get('source', None)
        if source is None:
            message = {'error': ERROR_ADD_CARD_SOURCE_REQUIRED}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        chance = random.randint(1, 100)
        if chance <= 70:
            rarity = 'common'
        elif 70 < chance <= 90:
            rarity = 'rare'
        elif 90 < chance <= 100:
            rarity = 'epic'

        cards = list(Card.objects.filter(rarity=rarity).all())
        random_card = random.choice(cards)
        card_entry = CardEntry()
        card_entry.card = random_card
        card_entry.user = request.user
        card_entry.source = source
        card_entry.save()

        message = {'card': CardEntrySerializer(card_entry, context=self.get_serializer_context()).data}
        return Response(message)


class CraftCardView(generics.GenericAPIView):
    """
    View for crafting cards.
    Checks if User has enough dust and adds CardEntry.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CardEntrySerializer

    def post(self, request, *args,  **kwargs):
        card_id = self.kwargs['card_id']
        card = Card.objects.get(id=card_id)
        profile = request.user.profile

        if profile.dust < card.craft_cost:
            message = {'error': ERROR_CRAFT_CARD_NOT_ENOUGH_DUST}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        if card in profile.cards.all():
            message = {'error': ERROR_CRAFT_CARD_ALREADY_IN_COLLECTION}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        profile.dust -= card.craft_cost
        profile.save()
        
        card_entry = CardEntry()
        card_entry.card = card
        card_entry.user = request.user
        card_entry.source = 'craft'
        card_entry.save()

        message = {'card': CardEntrySerializer(card_entry, context=self.get_serializer_context()).data,
                   'remaining_dust': profile.dust}
        return Response(message)


class TurnCardIntoDustView(generics.GenericAPIView):
    """View for turning card into a dust. Adds dust to a profile."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CardSerializer

    def delete(self, request, *args,  **kwargs):
        try:
            card_entry = CardEntry.objects.get(id=self.kwargs['entry_id'])
        except CardEntry.DoesNotExist:
            message = {'error': ERROR_CARD_ENTRY_DOES_NOT_EXIST}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
        user = card_entry.user
        if user != request.user:
            message = {'error': ERROR_CARD_ENTRY_USER_INCORRECT}
            return Response(message, status=status.HTTP_403_FORBIDDEN)

        card = card_entry.card
        user.profile.dust += card.turn_to_dust_value
        user.profile.save()
        card_entry.delete()
        message = {'card': CardSerializer(card, context=self.get_serializer_context()).data,
                   'message': MESSAGE_TURN_TO_DUST_SUCCESS}
        return Response(message)


class CardsBulkView(generics.GenericAPIView):
    """View for multiple Card set. Returns the list with cards specified."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = []
        cards = []
        user = request.user
        card_list = request.data.get('cards', [])
        ordering = request.data.get('ordering', None)

        user_profile_cards = list(user.profile.cards.values_list('id', flat=True))
        
        if card_list:
            for card_id in card_list:
                try:
                    card = Card.objects.get(id=card_id)
                except CardEntry.DoesNotExist:
                    message = {'error': ERROR_CARD_DOES_NOT_EXIST}
                    return Response(message, status=status.HTTP_400_BAD_REQUEST)
                cards.append(card)

        if ordering == 'rarity':
            epic_list = [card for card in cards if card.rarity == 'epic']
            rare_list = [card for card in cards if card.rarity == 'rare']
            common_list = [card for card in cards if card.rarity == 'common']
            cards = epic_list + rare_list + common_list
        
        for card in cards:
            addable = 'false' if card.id in user_profile_cards else 'true'
            data.append({'card': CardSerializer(card, context=self.get_serializer_context()).data,
                         'addable': addable})

        message = {'results': data}
        return Response(message)


class CollectionProgressView(generics.GenericAPIView):
    """View for collection progress"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        collection = Collection.objects.get(id=self.kwargs['collection_id'])
        collection_cards = collection.cards.all()
        collection_card_ids = [card.id for card in collection_cards]

        user = request.user
        user_cards = user.profile.cards.all()
        user_card_ids = [card.id for card in user_cards]

        acquired = [id for id in collection_card_ids if id in user_card_ids]
        not_acquired = [id for id in collection_card_ids if id not in user_card_ids]

        message = {'acquired': acquired,
                   'not_acquired': not_acquired}
        return Response(message)


class GetUserStatisticsView(generics.GenericAPIView):
    """View for User statistics across collected Cards and Collections"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        n_user_cards = user.profile.cards.count()
        n_user_collections = user.profile.collections.count()
        n_cards = Card.objects.count()
        n_collections = Collection.objects.count()

        message = {'n_user_cards': n_user_cards,
                   'n_user_collections': n_user_collections,
                   'n_cards': n_cards,
                   'n_collections': n_collections}
        return Response(message)


class IsAddableToCollectionView(generics.GenericAPIView):
    """View for checking if Card is addable to a Collection"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            card_entry = CardEntry.objects.get(id=self.kwargs['entry_id'])
        except CardEntry.DoesNotExist:
            message = {'error': ERROR_CARD_ENTRY_DOES_NOT_EXIST}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        user = card_entry.user
        card = card_entry.card
        cards_list = list(user.profile.cards.all().values())
        cards_list = [c['id'] for c in cards_list]

        if card.id in cards_list:
            message = {'result': 'false'}
        else:
            message = {'result': 'true'}
        return Response(message)


class IsDailyCardAvailableView(generics.GenericAPIView):
    """View for checking if daily Card available to obtain"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        last_daily = CardEntry.objects.filter(user=request.user).filter(source='daily').last()
        if last_daily is None:
            last_date = datetime.date(year=2000, month=1, day=1)
        else:
            last_date = last_daily.acquired

        today = datetime.datetime.now(pytz.utc)
        if today.date() == last_date:
            message = {'result': 'false'}
        else:
            message = {'result': 'true'}
        return Response(message)


class IsCraftableView(generics.GenericAPIView):
    """View for checking if Card is craftable"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CardEntrySerializer

    def get(self, request, *args,  **kwargs):
        card_id = self.kwargs['card_id']
        card = Card.objects.get(id=card_id)
        profile = request.user.profile

        if card in profile.cards.all():
            message = {'result': 'already_in_collection'}
        elif profile.dust < card.craft_cost:
            message = {'result': 'not_enough_dust'}
        else:
            message = {'result': 'true'}

        return Response(message)
