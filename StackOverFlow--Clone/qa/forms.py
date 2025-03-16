from django import forms
from .models import Question,Answer,Bounty,ProtectQuestion
from .models import BannedUser
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")



class InlineTagEditForm(forms.ModelForm):

	class Meta:
		model = Question
		fields = ['tags']

class SearchForm(forms.Form):
	noAnswers = forms.BooleanField(initial=False)

class BanUser_Form(forms.ModelForm):

	class Meta:
		model = BannedUser
		fields = ['banned_reasons', 'ban_till']

class BountyForm(forms.ModelForm):

	class Meta:
		model = Bounty
		fields = ['bounty_value','why_bounting']

class CommentForm(forms.Form):
      comment = forms.CharField(max_length=65)
      question_id = forms.CharField(max_length=65)
      username = forms.CharField(max_length=65)

class QuestionForm(forms.ModelForm):

	class Meta:
		model = Question
		fields = ['title','body','tags', 'post_owner']

class AnswerForm(forms.Form):
	pk = forms.IntegerField(max_value=1000)
	username = forms.CharField(max_length=65)
	body = forms.CharField(max_length=200)

class UpdateQuestion(forms.ModelForm):

	class Meta:
		model = Question
		fields = ['title','body','tags','why_editing_question']

class EditAnswerForm(forms.ModelForm):

	class Meta:
		model = Answer
		fields = ['body','why_editing_answer']

# class ReviewAnswer(forms.ModelForm):

# 	class Meta:
# 		model = ReviewFirstAnswer
# 		fields = ['actions']

CHOICES=[('select1','select 1'),
         ('select2','select 2')]


class ProtectForm(forms.ModelForm):

	class Meta:
		model = ProtectQuestion
		fields = ['why_want_toProtect']