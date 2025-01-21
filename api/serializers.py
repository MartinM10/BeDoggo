from rest_framework import serializers
from beDoggo.models import User, Pet, Location, PetAccess


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address', 'on_boarding']


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ['id', 'name', 'breed', 'age', 'observations', 'is_lost', 'owner']
        read_only_fields = ['owner']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'location', 'timestamp', 'pet']


class PetAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetAccess
        fields = ['id', 'user', 'pet']
