from django.contrib import admin
from kanmind_app.models import Board, Task

# Register your models here.
# admin.site.register(Board),
admin.site.register(Task),


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'member_count')
    search_fields = ('title', 'owner__username', 'owner__email')
    filter_horizontal = ('members',)

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Mitglieder'


# @admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'board', 'status', 'priority',
#                     'assignee', 'due_date', 'comments_count')
#     list_filter = ('status', 'priority', 'due_date')
#     search_fields = ('title', 'description', 'assignee__username', 'reviewer__username')
#     autocomplete_fields = ('board', 'assignee', 'reviewer')
