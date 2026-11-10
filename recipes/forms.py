from django import forms
from django.core.files.uploadedfile import UploadedFile

from .models import CUISINES, Rating, Recipe

MAX_PHOTO_BYTES = 5 * 1024 * 1024


def _lines(text):
    return [line for line in (text or "").splitlines() if line.strip()]


class RecipeForm(forms.ModelForm):
    """Server-side checks match static/recipes/js/validate.js."""

    class Meta:
        model = Recipe
        fields = ["title", "is_veg", "cuisine", "cook_time", "ingredients", "steps", "image", "image_url"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "maxlength": 120,
                                            "placeholder": "e.g. Paneer Butter Masala"}),
            "cuisine": forms.Select(attrs={"class": "form-select"}),
            "cook_time": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 600,
                                                  "inputmode": "numeric", "placeholder": "e.g. 30"}),
            "ingredients": forms.Textarea(attrs={"class": "form-control", "rows": 6,
                                                 "placeholder": "200 g paneer\n2 tomatoes\n1 tbsp butter"}),
            "steps": forms.Textarea(attrs={"class": "form-control", "rows": 6,
                                           "placeholder": "Heat butter in a pan\nAdd tomato puree and cook 5 minutes"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".jpg,.jpeg,.png"}),
            "image_url": forms.URLInput(attrs={"class": "form-control", "inputmode": "url",
                                               "placeholder": "https://…/photo.jpg"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cuisine"].choices = [(name, f"{emoji} {name}") for name, emoji, _ in CUISINES]
        # Built-in checks run before clean_<field>(), so give them the same wording as validate.js
        messages = {
            "title": {"required": "Enter a recipe name of at least 3 characters."},
            "cook_time": dict.fromkeys(["required", "invalid", "min_value", "max_value"],
                                       "Enter the cooking time in whole minutes, between 1 and 600."),
            "ingredients": {"required": "Add at least 2 ingredients, one per line."},
            "steps": {"required": "Add at least one step."},
            "image": {"invalid_image": "This photo couldn’t be read. Choose another JPG or PNG."},
            "image_url": {"invalid": "Paste a full image link that starts with https://"},
        }
        for name, errors in messages.items():
            self.fields[name].error_messages.update(errors)

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Enter a recipe name of at least 3 characters.")
        same = Recipe.objects.filter(title__iexact=title).exclude(pk=self.instance.pk)
        if same.exists():
            raise forms.ValidationError("A recipe with this name already exists. Use a different name.")
        return title

    def clean_cook_time(self):
        minutes = self.cleaned_data["cook_time"]
        if minutes is None or not 1 <= minutes <= 600:
            raise forms.ValidationError("Enter the cooking time in whole minutes, between 1 and 600.")
        return minutes

    def clean_ingredients(self):
        text = self.cleaned_data["ingredients"]
        if len(_lines(text)) < 2:
            raise forms.ValidationError("Add at least 2 ingredients, one per line.")
        return text

    def clean_steps(self):
        text = self.cleaned_data["steps"]
        if len(_lines(text)) < 1:
            raise forms.ValidationError("Add at least one step.")
        return text

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if isinstance(image, UploadedFile):   # a new upload (not the existing photo or "clear")
            if not image.name.lower().endswith((".jpg", ".jpeg", ".png")):
                raise forms.ValidationError("Choose a JPG or PNG photo.")
            if image.size > MAX_PHOTO_BYTES:
                raise forms.ValidationError("Choose a photo smaller than 5 MB.")
        return image

    def clean_image_url(self):
        link = self.cleaned_data.get("image_url", "").strip()
        if link and not link.lower().startswith("https://"):
            raise forms.ValidationError("Paste a full image link that starts with https://")
        return link


# Show Veg / Non-veg as two radio buttons instead of a checkbox.
RecipeForm.base_fields["is_veg"] = forms.TypedChoiceField(
    label="Type",
    choices=((True, "Veg"), (False, "Non-veg")),
    coerce=lambda value: value in (True, "True"),
    widget=forms.RadioSelect,
    initial=True,
)


class RatingForm(forms.ModelForm):
    """Same rules as the CGI page (cgi-feedback/cgi-bin/rate.py)."""
    recipe = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-select"}),
                               error_messages={"required": "Choose a recipe."})
    stars = forms.TypedChoiceField(
        choices=[(n, f"{n} star{'s' if n > 1 else ''}") for n in range(5, 0, -1)],
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={"required": "Pick a rating from 1 to 5 stars."},
    )

    class Meta:
        model = Rating
        fields = ["name", "recipe", "stars", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "maxlength": 60}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "maxlength": 300}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        titles = Recipe.objects.order_by("title").values_list("title", flat=True)
        self.fields["recipe"].choices = [("", "Choose a recipe")] + [(t, t) for t in titles]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Enter your name (at least 2 characters).")
        return name
