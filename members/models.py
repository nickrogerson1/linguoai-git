from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django_countries.fields import CountryField
from django.utils.translation import gettext_lazy as _
import datetime
from django.core.validators import MaxValueValidator, MinValueValidator, EmailValidator
from django.core.exceptions import ValidationError


min_comment = "Whooaa, looks like the year you entered was a little early. Have a go at entering a year after 1920."
max_comment = "Hang on, you can't be that young! Try entering your REAL year of birth."

def twenty_years_ago():
    return datetime.date.today().year - 20

def max_year(v):
    five_years_ago = datetime.date.today().year - 5
    return MaxValueValidator(five_years_ago, max_comment)(v)

CURR_CHOICES = [
        ('USD', '$ United States Dollar'),
        ('CNY', '¥ Chinese RMB'),
    ]

SM_CHOICES = [
        # ('', ''),
        ('FB', 'Facebook'),
        ('X', 'X'),
        ('TT', 'Tik Tok'),
        ('IN', 'Instagram'),
        ('DY', 'Douyin')
]


class Affiliate(models.Model):

    name = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateField()
    website = models.CharField(max_length=150, blank=True)
    social_media_app = models.CharField(max_length=2, choices=SM_CHOICES, blank=True)
    social_media_handle = models.CharField(max_length=50, unique=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURR_CHOICES, default='USD')
    total_sales = models.PositiveIntegerField(default=0)
    total_new_users = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(f'{self.pk} {self.name}')


class DiscountCodes(models.Model):

    code_name = models.CharField(max_length=50, unique=True)
    code_title = models.CharField(max_length=150, blank=True)
    discount_code = models.CharField(max_length=30)
    currency = models.CharField(max_length=3, choices=CURR_CHOICES, default='USD')
    bonus_amount = models.PositiveSmallIntegerField(default=0)
    bonus_percent = models.DecimalField(default=0, max_digits=10, decimal_places=3)
    for_purchases = models.BooleanField(default=False) #Whether it should only be applied just for purchases
    first_purchase = models.BooleanField(default=True) #Whether it's just for 1st purchases (one-off)
    time_created = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField()
    times_used = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(default=0, max_digits=10, decimal_places=3)
    # affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Discount Codes"

    def __str__(self):
        return str(f'{self.pk} {self.code_name}')



class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True, validators=[EmailValidator()], error_messages={
            "unique": _("That email address has already been registered. Please use another one."),
        })
    first_name = models.CharField(_("Name"), max_length=150)
    country = CountryField()
    year = models.PositiveIntegerField(default=twenty_years_ago(), validators=[MinValueValidator(1920, min_comment), max_year])
    balance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
# Keep track of how many reports they've made
    reports = models.PositiveIntegerField(default=0)
    total_submissions = models.PositiveIntegerField(default=0)
    percent_reported = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    reports_blocked = models.BooleanField(default=False)
    currency = models.CharField(max_length=3, choices=CURR_CHOICES, default='USD')
    total_spent = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    discount_code = models.ForeignKey(DiscountCodes, on_delete=models.CASCADE, blank=True, null=True)
    discount_code_used = models.BooleanField(default=False)
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, blank=True, null=True)





class BaseModel(models.Model):
    model_used = models.CharField(max_length=128)
    prompt_tokens = models.PositiveIntegerField()
    completion_tokens = models.PositiveIntegerField()
    total_tokens = models.PositiveIntegerField()
    total_words = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    cost = models.DecimalField(max_digits=10, decimal_places=6)
    price_per_word = models.DecimalField(max_digits=7, decimal_places=5)
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
    


def word_count(sub): return len(sub.strip().split())

def max_word_count_general_validator(sub):
    if word_count(sub) > 5000:
        raise ValidationError('Your submission is greater than 5000 words in length. Please reduce the size of the content and resubmit it.')


class IeltsWritingTask2(BaseModel):
    CHOICES = [
        ('EN', 'English'),
        ('MS', 'Malaysian Bahasa Melayu'),
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
        ('HI', 'Hindi हिंदी'),
        ('UR', 'Urdu اردو'),
        ('TA', 'Tagalog')
    ]

    explanation_language = models.CharField(max_length=2, choices=CHOICES, default='EN')
    question = models.TextField()
    answer = models.TextField()
    score_res = models.TextField()
    band = models.CharField(max_length=20)

    def __str__(self):
        return self.owner.username
    
    class Meta:
        verbose_name_plural = "IELTS Writing Task 2"



class CorrectedSubmission(BaseModel):
    submission = models.TextField(validators=[max_word_count_general_validator])
    result = models.TextField()
        
    def __str__(self):
        return self.owner.username

    class Meta:
        verbose_name_plural = "Corrected Submissions"


class ImprovedSubmission(BaseModel):
    submission = models.TextField(validators=[max_word_count_general_validator])
    improved_sub = models.TextField()

    def __str__(self):
        return self.owner.username

    class Meta:
        verbose_name_plural = "Improved Submissions"



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