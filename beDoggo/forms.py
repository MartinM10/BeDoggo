from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from beDoggo.models import Pet, MedicalRecord, Veterinarian, User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'address']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address', 'profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class VeterinarianRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    vet_license_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    clinic_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    clinic_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    clinic_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    available_hours = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personaliza los campos de contraseña para que usen las clases de Bootstrap
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_veterinarian = True  # Marcar al usuario como veterinario
        user.username = self.cleaned_data['email']  # Usar el email como nombre de usuario
        if commit:
            user.save()
            Veterinarian.objects.create(
                user=user,
                vet_license_number=self.cleaned_data['vet_license_number'],
                clinic_name=self.cleaned_data.get('clinic_name'),
                clinic_address=self.cleaned_data.get('clinic_address'),
                clinic_phone=self.cleaned_data.get('clinic_phone'),
                available_hours=self.cleaned_data.get('available_hours'),
            )
        return user


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'breed', 'age', 'observations', 'is_lost', 'image']

    def __init__(self, *args, **kwargs):
        super(PetForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.image:
            self.fields['image'].widget.attrs['data-current-image'] = self.instance.image.url

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age < 0:
            raise forms.ValidationError("Age cannot be negative.")
        return age


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'visit_reason', 'diagnosis', 'treatment', 'medication',
            'vaccines', 'allergies', 'test_results', 'observations', 'next_visit',
            'attachments', 'images'
        ]
        widgets = {
            'visit_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'treatment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medication': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vaccines': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'test_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_visit': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attachments': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'images': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
