from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django_countries.fields import CountryField
from django.utils.translation import gettext_lazy as _
import datetime
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.validators import MaxLengthValidator

min_comment = "Whooaa, looks like the year you entered was a little early. Have a go at entering a year after 1920."
max_comment = "Hang on, you can't be that young! Try entering your REAL year of birth."

def twenty_years_ago():
    return datetime.date.today().year - 20

def max_year(v):
    five_years_ago = datetime.date.today().year - 5
    return MaxValueValidator(five_years_ago, max_comment)(v)

class User(AbstractUser):
    country = CountryField()
    year = models.PositiveIntegerField(default=twenty_years_ago(), validators=[MinValueValidator(1920, min_comment), max_year])
    balance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
# Keep track of how many reports they've made
    reports = models.PositiveIntegerField(default=0)
    total_submissions = models.PositiveIntegerField(default=0)
    percent_reported = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    reports_blocked = models.BooleanField(default=False)

    CHOICES = [
        ('USD', '$ United States Dollar'),
        ('CNY', '¥ Chinese RMB'),
    ]

    currency = models.CharField(max_length=3, choices=CHOICES, default='USD')

User._meta.get_field('email').blank = False
User._meta.get_field('first_name').blank = False
User._meta.get_field('first_name').verbose_name = 'Name'





class BaseModel(models.Model):
    model_used = models.CharField(max_length=128)
    prompt_tokens = models.PositiveIntegerField()
    completion_tokens = models.PositiveIntegerField()
    total_tokens = models.PositiveIntegerField()
    total_words = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    cost = models.DecimalField(max_digits=10, decimal_places=6)
    price_per_100_words = models.DecimalField(max_digits=6, decimal_places=3)
    charged = models.DecimalField(max_digits=7, decimal_places=2)
    usd_charge = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    usd_exchange_rate = models.DecimalField(max_digits=8, decimal_places=6)
    profit = models.DecimalField(max_digits=8, decimal_places=3)
    margin = models.DecimalField(max_digits=8, decimal_places=3)
    processing_time = models.DecimalField(max_digits=6, decimal_places=3)
    time_created = models.DateTimeField(auto_now_add=True)
    user_reported = models.BooleanField(default=False)
    user_deleted = models.BooleanField(default=False)
    new_balance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    comments = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    


    class Meta:
        abstract = True
    


class IeltsWritingTask2(BaseModel):
    CHOICES = [
        ('EN', 'English'),
        ('CN', 'Chinese 中文'),
        ('ES', 'Spanish Español'),
        ('PT', 'Portuguese Português'),
        ('FR', 'French Français'),
        ('DE', 'German Deutsch'),
        ('JP', 'Japanese 日本語'),
        ('KO', 'Korean 한국어'),
        ('TH', 'Thai แบบไทย'),
        ('AR', 'Arabic عربي'),
        ('RU', 'Russian русский'),
        ('ID', 'Indonesian bahasa Indonesia'),
        ('FA', 'Farsi فارسی'),
        ('VI', 'Vietnamese Tiếng Việt'),
        ('BN', 'Bengali বাংলা'),
        ('HI', 'Hindi हिंदी')
    ]

    explanation_language = models.CharField(max_length=2, choices=CHOICES, default='EN')
    question = models.TextField(validators=[MaxLengthValidator(500)])
    answer = models.TextField(validators=[MaxLengthValidator(3000)])
    score_res = models.TextField()
    band = models.CharField(max_length=20)

    def __str__(self):
        return self.owner.username
    
    class Meta:
        verbose_name_plural = "IELTS Writing Task 2"



class CorrectedSubmission(BaseModel):
    submission = models.TextField(validators=[MaxLengthValidator(25000)])
    result = models.TextField()
        
    def __str__(self):
        return self.owner.username


class ImprovedSubmission(BaseModel):
    submission = models.TextField(validators=[MaxLengthValidator(25000)])
    improved_sub = models.TextField()

    def __str__(self):
        return self.owner.username



class PurchaseHistory(models.Model):
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, default='Stripe')
    time_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.owner.username

    class Meta:
        verbose_name_plural = "Total Purchases"


class UserReportedResults(models.Model):

    time_created = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    CHOICES = [
        ('Waiting', 'Awaiting Approval'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined')
    ]

    decision = models.CharField(max_length=10, choices=CHOICES, default='Waiting')
    refunded = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    comments = models.TextField()
    ielts_writing_task_2 = models.ForeignKey(IeltsWritingTask2, on_delete=models.CASCADE, blank=True, null=True)
    corrected = models.ForeignKey(CorrectedSubmission, on_delete=models.CASCADE, blank=True, null=True)
    improved = models.ForeignKey(ImprovedSubmission, on_delete=models.CASCADE, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "User Reported Results"