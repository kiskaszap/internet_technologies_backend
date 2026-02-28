from rest_framework import serializers
from .models import User, Category, Listing, Comment


#  """
#     Minimal user representation.

#     Only exposes safe public fields to prevent
#     leaking sensitive authentication data.
#     """

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "phone_number"]

#  """
#     Simple serializer for listing categorisation.
#     """
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

# """
#     Comment serializer with nested user representation.

#     User is read-only to prevent client-side user spoofing.
#     """
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "listing", "text", "created_at", "user"]
        read_only_fields = ["user", "created_at"]
# """
#     Main listing serializer.

#     Includes:
#     - Nested user info
#     - Nested comments
#     - Read-only relationships for security
#     """

 # Nested user ensures frontend receives creator information
    # without exposing private authentication data

class ListingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "price",
            "image",
            "status",
            "created_at",
            "phone_number",
            "user",
            "category",
            "comments",
        ]
