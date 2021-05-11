from rest_framework import serializers

from hackernews.models import UserDTO


class UserDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDTO
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.about = validated_data.get('about', instance.about)
        return instance
