from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)
    fullname = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def save(self):
        pw = self.validated_data['password']
        repeated_pw = self.validated_data['repeated_password']
        email = self.validated_data['email']
        username = self.validated_data['username']

        if pw != repeated_pw:
            raise serializers.ValidationError({'error': 'dont`t match'})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'error': 'this email-address allready exists.'})

        account = User(email=self.validated_data['email'],
                       username=self.validated_data['username'])
        account.set_password(pw)
        account.save()
        return account


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")

            user = authenticate(username=user_obj.username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Both email and password are required.")

        attrs['user'] = user
        return attrs
