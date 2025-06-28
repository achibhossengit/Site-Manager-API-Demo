from rest_framework.serializers import ModelSerializer
from users.models import CustomUser

class CustomUserCreateSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name','username', 'user_type', 'current_site','password']
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
        
        
class CustomUserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'