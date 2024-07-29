from rest_framework import serializers
from .models import User, Doctor, Patient, Department, PatientRecord

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_patient = serializers.BooleanField(required=True)
    is_doctor = serializers.BooleanField(required=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_patient', 'is_doctor', 'department']

    def create(self, validated_data):
        department = validated_data.pop('department', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_patient=validated_data['is_patient'],
            is_doctor=validated_data['is_doctor']
        )
        if user.is_patient and department:
            Patient.objects.create(user=user, department=department)
        elif user.is_doctor and department:
            Doctor.objects.create(user=user, department=department)
        return user

    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_patient', 'is_doctor']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'department']

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'department']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class PatientRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientRecord
        fields = '__all__'
    


