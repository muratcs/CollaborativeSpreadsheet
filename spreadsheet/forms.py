from django import forms
from django.contrib.auth.models import User


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']


class setNameForm(forms.Form):
    name = forms.CharField(max_length=25)

class getCellForm(forms.Form):
    celladdr = forms.CharField(max_length=5)

class getCellsForm(forms.Form):
    cellrange = forms.CharField(max_length=5)

class setCellForm(forms.Form):
    celladdr = forms.CharField(max_length=5)
    content = forms.CharField(max_length=40)

class evaluateForm(forms.Form):
    iters = forms.IntegerField()

class cutForm(forms.Form):
    cellrange = forms.CharField(max_length=5)

class copyForm(forms.Form):
    cellrange = forms.CharField(max_length=5)

class pasteForm(forms.Form):
    celladdr = forms.CharField(max_length=5)

class uploadForm(forms.Form):
    file = forms.FileField()





