from rest_framework import serializers
from .models import Card, Collection, CardEntry, Profile
from django.contrib.auth.models import User


class SignUpSerializer(serializers.ModelSerializer):
    """Serializer fo signing up"""
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password2",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]
        password2 = validated_data["password2"]
        if password != password2:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        user = User(username=username)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User entity"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile entity"""
    class Meta:
        model = Profile
        fields = '__all__'


class CardSerializer(serializers.ModelSerializer):
    """Serializer for Card entity"""
    class Meta:
        model = Card
        fields = '__all__'


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection entity"""
    class Meta:
        model = Collection
        fields = '__all__'


class CardEntrySerializer(serializers.ModelSerializer):
    """Serializer for CardEntry entity"""
    class Meta:
        model = CardEntry
        fields = '__all__'
