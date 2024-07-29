from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Doctor, Patient, Department, PatientRecord, User
from .serializers import DoctorSerializer, PatientSerializer, DepartmentSerializer, PatientRecordSerializer, UserRegistrationSerializer
from rest_framework import viewsets, generics, permissions
from .models import Doctor, Patient, Department, PatientRecord
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsDoctor, IsDoctorOrPatientOwner




class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Registration successful",
            "user": UserRegistrationSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_logout(request):
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Please provide a refresh token in the body."}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
    
    except Exception as e:
        print(f"Error: {e}")
        return Response({"error": "An error occurred during logout."}, status=status.HTTP_400_BAD_REQUEST)

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_doctor:
            return Doctor.objects.all()
        return Doctor.objects.none()

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsDoctorOrPatientOwner]
        return super().get_permissions()

    def retrieve(self, request, pk=None):
        try:
            doctor = Doctor.objects.get(pk=pk)
        except Doctor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, doctor)

        serializer = DoctorSerializer(doctor)
        return Response(serializer.data)

    def update(self, request, pk=None):
        try:
            doctor = Doctor.objects.get(pk=pk)
        except Doctor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, doctor)

        serializer = DoctorSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Doctor profile updated successfully.",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            doctor = Doctor.objects.get(pk=pk)
        except Doctor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, doctor)

        doctor.delete()
        return Response({
            "message": "Doctor profile deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)




class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorOrPatientOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_doctor:
            return Patient.objects.all()
        elif user.is_patient:
            return Patient.objects.filter(user=user)
        return Patient.objects.none()

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated, IsDoctorOrPatientOwner])
def patient_detail(request, pk):
    try:
        patient = Patient.objects.get(pk=pk)
    except Patient.DoesNotExist:
        return Response(status=404)

    if request.method == 'GET':
        if request.user.is_superuser or request.user == patient.user or (request.user.is_doctor and request.user.doctor.department == patient.department):
            serializer = PatientSerializer(patient)
            return Response(serializer.data)
        return Response(status=403)

    elif request.method in ['PUT', 'DELETE']:
        if request.user.is_superuser or request.user == patient.user or (request.user.is_doctor and request.user.doctor.department == patient.department):
            if request.method == 'PUT':
                serializer = PatientSerializer(patient, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=400)
            else:
                patient.delete()
                return Response(status=204)
        return Response(status=403)

class PatientRecordViewSet(viewsets.ModelViewSet):
    serializer_class = PatientRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return PatientRecord.objects.all()
        if user.is_doctor:
            return PatientRecord.objects.filter(department=user.doctor.department)
        if user.is_patient:
            return PatientRecord.objects.filter(patient__user=user)
        return PatientRecord.objects.none()

    
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def department_doctors(request, pk):
    try:
        department = Department.objects.get(pk=pk)
    except Department.DoesNotExist:
        return Response(status=404)

    if request.method == 'GET':
        doctors = Doctor.objects.filter(department=department)
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data)

    elif request.method == 'PUT':
        if request.user.is_superuser or (request.user.is_doctor and request.user.doctor.department == department):
            return Response(status=200)
        return Response(status=403)

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def department_patients(request, pk):
    try:
        department = Department.objects.get(pk=pk)
    except Department.DoesNotExist:
        return Response(status=404)

    if request.method == 'GET':
        if request.user.is_superuser or (request.user.is_doctor and request.user.doctor.department == department):
            patients = Patient.objects.filter(department=department)
            serializer = PatientSerializer(patients, many=True)
            return Response(serializer.data)
        return Response(status=403)

    elif request.method == 'PUT':
        if request.user.is_superuser or (request.user.is_doctor and request.user.doctor.department == department):
            return Response(status=200)
        return Response(status=403)