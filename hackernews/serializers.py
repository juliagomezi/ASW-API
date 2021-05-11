from rest_framework import serializers

from hackernews.models import UserDTO, ContributionDTO, ContributionCreationDTO


class UserDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDTO
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.about = validated_data.get('about', instance.about)
        return instance


class ContributionDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionDTO
        fields = '__all__'


class ContributionCreationDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionCreationDTO
        fields = '__all__'
