from rest_framework import serializers
from users.models import CustomUser

class CustomUserCreateSerializer(serializers.ModelSerializer):
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
        
        
# Serializers updated to include computed properties
class CustomUserSerializer(serializers.ModelSerializer):
    total_khoraki = serializers.IntegerField(read_only=True)
    total_advance = serializers.IntegerField(read_only=True)
    total_presents = serializers.FloatField(read_only=True)
    last_session_payable = serializers.IntegerField(read_only=True)
    total_salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserSerializerForViewer(serializers.ModelSerializer):
    total_khoraki = serializers.IntegerField(read_only=True)
    total_advance = serializers.IntegerField(read_only=True)
    total_presents = serializers.FloatField(read_only=True)
    last_session_payable = serializers.IntegerField(read_only=True)
    total_salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'is_active',
            'date_joined', 'designation', 'address', 'phone', 'current_site',
            'user_type', 'total_khoraki', 'total_advance', 'total_presents',
            'last_session_payable', 'total_salary'
        ]

class CustomUserSerializerForMainManager(serializers.ModelSerializer):
    total_khoraki = serializers.IntegerField(read_only=True)
    total_advance = serializers.IntegerField(read_only=True)
    total_presents = serializers.FloatField(read_only=True)
    last_session_payable = serializers.IntegerField(read_only=True)
    total_salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'is_active',
            'date_joined', 'designation', 'address', 'phone', 'current_site',
            'total_khoraki', 'total_advance', 'total_presents',
            'last_session_payable', 'total_salary'
        ]

class CustomUserSerializerForSiteManager(serializers.ModelSerializer):
    total_khoraki = serializers.IntegerField(read_only=True)
    total_advance = serializers.IntegerField(read_only=True)
    total_presents = serializers.FloatField(read_only=True)
    last_session_payable = serializers.IntegerField(read_only=True)
    total_salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'designation', 'address', 'phone',
            'total_khoraki', 'total_advance', 'total_presents',
            'last_session_payable', 'total_salary'
        ]
