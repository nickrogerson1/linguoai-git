from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.http.request import HttpRequest
from .models import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from .api_funcs.corrections import find_difference


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "country", "year", "balance", "_currency", "is_staff")
    # fieldsets = UserAdmin.fieldsets + ((None, {"fields": ["country"]}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ["country"]}),)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "email", "country", "year", "balance", 
            "currency", "reports", "total_submissions", "percent_reported", "reports_blocked")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description="currency")
    def _currency(self, obj):
        return obj.currency
    

# Update the user when submissions are deleted from the database by admin
class AdminMixin:

    def delete_model(self, request: HttpRequest, obj: any) -> None:
        print(f'Check: {obj.userreportedresults_set}')
        sub = obj.userreportedresults_set.exists()
        print(f'Post check: {sub}')
        user = obj.owner
        user.reports -= 1 if obj.userreportedresults_set.exists() else 0
        user.total_submissions -= 1
        user.percent_reported = (user.reports / user.total_submissions) * 100
        user.save()
        print(f'User total subs: {user.total_submissions}')
        return super().delete_model(request, obj)
      
# This is used for the "Delete Selected" bulk removal in Admin
    def delete_queryset(self, request, queryset):
          
        for obj in queryset:
            print(f'Check: {obj.userreportedresults_set}')
            sub = obj.userreportedresults_set.exists()
            print(f'Post check: {sub}')
        #Need to get the user's up-to-date info and not use data from queryset otherwise will fail
            user = User.objects.get(pk=obj.owner.pk)
            print(obj.owner.pk)
            print(user)
            user.reports -= 1 if obj.userreportedresults_set.exists() else 0
            reports = user.reports
            print(reports)
            print(f'User total subs before: {user.total_submissions}')
            user.total_submissions -= 1
            
            user.percent_reported = (user.reports / user.total_submissions) * 100
            user.save()
            print(f'User total subs after: {user.total_submissions}')

        queryset.delete()
           
    
    
base_fields = ['owner', 'time_created', 'model_used', 'prompt_tokens', 'completion_tokens', 'total_tokens', 
               'cost', 'total_words','currency', 'usd_exchange_rate', 'price_per_100_words', 'charged', 'usd_charge', 
               'profit', '_margin', 'new_balance', 'processing_time', 'user_reported', ]

class IeltsWritingTask2Admin(AdminMixin, admin.ModelAdmin):
    list_display = ('owner', 'time_created', 'band', '_question')
    list_per_page = 25
    fields = base_fields + ['band', 'explanation_language', '_score_res', '_question', '_answer', 'comments', 'user_deleted']
    readonly_fields = base_fields + [ 'band', 'explanation_language', '_score_res', '_question', '_answer', 'time_created']
    

# Display the HTML properly for these cols
    @admin.display(description="score_res")
    def _score_res(self, obj):
        return mark_safe(obj.score_res)
    
    @admin.display(description="question")
    def _question(self, obj):
        return mark_safe(obj.question)
    
    @admin.display(description="answer")
    def _answer(self, obj):
        return mark_safe(obj.answer)
    
    @admin.display(description="margin")
    def _margin(self, obj):
        return str(obj.margin) + '%'

    class Media:
        css = {
            'all': ('css/admin.css',)
        }



class CorrectedSubAdmin(AdminMixin, admin.ModelAdmin):
    list_display = ('owner', 'time_created', 'corrected_result')
    list_per_page = 25
    fields = base_fields + ['_sub', '_result',  'corrected_result', 'comments', 'user_deleted']
    readonly_fields = base_fields + ['_sub',  'corrected_result', '_result', 'time_created'] 
    

    @admin.display(description="submission")
    def _sub(self, obj):
        return mark_safe(obj.submission)

    @admin.display(description="result")
    def _result(self, obj):
        return mark_safe(obj.result)
    
    @admin.display(description="margin")
    def _margin(self, obj):
        return str(obj.margin) + '%'

    class Media:
        css = {
            'all': ('css/admin.css',)
        }

    
    def corrected_result(self, obj):
        return mark_safe(find_difference(obj.submission, obj.result))



class ImprovedSubAdmin(AdminMixin, admin.ModelAdmin):
    list_display = ('owner', 'time_created', '_submission', '_improved_sub')
    list_per_page = 25
    fields = base_fields + ['_submission', '_improved_sub', 'comments', 'user_deleted']
    readonly_fields = base_fields + ['_margin', '_submission', '_improved_sub', 'time_created']

    @admin.display(description="submission")
    def _submission(self, obj):
        return mark_safe(obj.submission)

    @admin.display(description="improved version")
    def _improved_sub(self, obj):
        return mark_safe(obj.improved_sub)
    
    @admin.display(description="margin")
    def _margin(self, obj):
        return str(obj.margin) + '%'

    class Media:
        css = {
            'all': ('css/admin.css',)
        }




class UserReportedResultsAdmin(admin.ModelAdmin):
    list_display = ('owner', 'time_created', 'decision', '_reason')
    list_per_page = 25
    fields = ['time_created', '_reason', 'ielts_writing_task_2', 'corrected', 'improved', 'owner', 'refunded', 'refund_amount', 'decision', 'comments'] 
    readonly_fields = ['time_created', '_reason', 'ielts_writing_task_2', 'corrected', 'improved', 'owner', 'refund_amount'] 
# 'refunded', 
# Display the HTML properly for these cols
    @admin.display(description="reason")
    def _reason(self, obj):
        return mark_safe(obj.reason)
    
    def save_model(self, request, obj, form, change):
        print(f'Obj: {obj.decision}')
    # Check if report has been accepted and it's not already been refunded
        if obj.decision == 'Accepted' and not obj.refunded:
        # Update the refund so they can't get their money back twice
            obj.refunded = True

        # Find the model and the object's PK
        # Then get the object and find out what the cost was
            if obj.ielts_writing_task_2:
                sub = obj.ielts_writing_task_2
            elif obj.improved:
                sub = obj.improved
            else:
                sub = obj.corrected
            
            refund_amount = sub.charged
            usd_refund_amount = sub.usd_charge if sub.usd_charge else sub.charged
            print(f'usd refund: {usd_refund_amount}')
            print(refund_amount)
            print(obj.owner.balance)

            obj.owner.balance += refund_amount
            obj.refund_amount = usd_refund_amount
            obj.owner.save()
            print(obj.owner.balance)
    # Then run regular code
        super().save_model(request, obj, form, change)




class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ('owner', 'time_created', 'currency', 'amount')
    list_per_page = 25
    # readonly_fields = ['owner', 'time_created', 'amount', 'currency']



admin.site.register(User, CustomUserAdmin)
admin.site.register(IeltsWritingTask2,  IeltsWritingTask2Admin)
admin.site.register(CorrectedSubmission,  CorrectedSubAdmin)
admin.site.register(ImprovedSubmission,  ImprovedSubAdmin)
admin.site.register(PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(UserReportedResults, UserReportedResultsAdmin)

admin.site.unregister(Group)
admin.site.site_header = 'LinguoAI Admin'
