from django.contrib import admin
from kanmind_app.models import Board, Task, Comment

# Register your models here.
# admin.site.register(Board),
# admin.site.register(Task),
# admin.site.register(Comment),


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'member_count')
    search_fields = ('title', 'owner__username', 'owner__email')
    filter_horizontal = ('members',)

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Mitglieder'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'priority', 'due_date', 'assignee', 'reviewer']

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if hasattr(self.model, 'comments_count'):
            display.append('comments_count')
        return display
    

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'content', 'created_at')
