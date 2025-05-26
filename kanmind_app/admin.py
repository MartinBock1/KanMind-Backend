from django.contrib import admin
from kanmind_app.models import Boards, BoardUser, Task

# Register your models here.
admin.site.register(Boards),
admin.site.register(BoardUser),
admin.site.register(Task),
