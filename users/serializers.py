from rest_framework import serializers
from users.models import CustomUser, Promotion

class CustomUserIDsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username']

class CustomUserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name','username', 'current_site', 'phone', 'address','password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
        
    def create(self, validated_data):
        # Remove the password from validated_data to handle it securely
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)  # Encrypt the password
        user.save()
        return user
               
class CustomUserUpdateBioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username','email', 'phone', 'address']

class UpdateCurrentSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['current_site']

class UpdateUserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['current_site', 'user_type']
        


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'