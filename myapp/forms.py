# forms.py

from django import forms


class VideoProcessingForm(forms.Form):
    tweet_link = forms.CharField(label='Tweet Link', max_length=255, required=True)
    video_file = forms.FileField(label='Upload Video', required=True)
