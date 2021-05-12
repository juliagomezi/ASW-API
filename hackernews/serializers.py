from rest_framework import serializers

from hackernews.models import UserDTO, ContributionDTO, ContributionCreationDTO, CommentCreationDTO, CommentDTO, Comment


class UserDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDTO
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.about = validated_data.get('about', instance.about)
        return instance


class CommentDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentDTO
        fields = ('id', 'level', 'author', 'text', 'votes', 'date', 'contributionId', 'fatherId', 'replies')

    def get_fields(self):
        fields = super(CommentDTOSerializer, self).get_fields()
        fields['replies'] = CommentDTOSerializer(many=True)
        return fields


class ContributionDTOSerializer(serializers.ModelSerializer):
    comments = CommentDTOSerializer(many=True)

    class Meta:
        model = ContributionDTO
        fields = '__all__'


class ContributionCreationDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionCreationDTO
        fields = '__all__'


class CommentCreationDTOSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentCreationDTO
        fields = '__all__'
