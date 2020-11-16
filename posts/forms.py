from django import forms

from.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["group", "text", "image"]
        label = {"group": "Введите группу", "text": "Введите текст",
                 "image": "Вставьте картинку"}
        help_text = {"group": "Из уже существующих",
                     "text": "Введите текст поста",
                     "image": "Нужно вставить картинку"}

    def empty_text(self):
        data = self.cleaned_data["text"]
        if data == "":
            raise forms.ValidationError("Пост без текста "
                                        "не будет опубликован.")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        label = {"text": "Введите текст"}
        help_text = {"text": "Введите текст комментария"}
        widjets = {'text': forms.Textarea}
