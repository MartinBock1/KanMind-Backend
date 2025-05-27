from rest_framework import serializers
from django.contrib.auth.models import User
from kanmind_app.models import Board, Task


class UserSerializer(serializers.ModelSerializer):
    """
    Serialisiert einen Benutzer (User) und gibt grundlegende Benutzerinformationen zurück.

    Attributes:
        fullname (str): Der vollständige Name des Benutzers (wird hier als 'username' dargestellt).
    """
    fullname = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serialisiert eine Aufgabe (Task) und gibt alle relevanten Informationen zur Aufgabe zurück.

    Attributes:
        assignee (UserSerializer): Der Benutzer, dem die Aufgabe zugewiesen wurde (optional).
        reviewer (UserSerializer): Der Benutzer, der die Aufgabe überprüfen soll (optional).
    """
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date', 'comments_count']


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serialisiert eine Liste von Boards und gibt grundlegende Informationen zu jedem Board zurück.

    Attributes:
        member_count (int): Die Anzahl der Mitglieder des Boards.
        ticket_count (int): Die Anzahl der Tickets, die dem Board zugewiesen sind.
        tasks_to_do_count (int): Die Anzahl der Aufgaben, die den Status 'to-do' haben.
        tasks_high_prio_count (int): Die Anzahl der Aufgaben mit hoher Priorität.
    """
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count',
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serialisiert die Detailansicht eines Boards, einschließlich aller Mitglieder und Aufgaben.

    Attributes:
        members (list[int]): Eine Liste der IDs der Mitglieder des Boards.
        tasks (list[TaskSerializer]): Eine Liste der Aufgaben, die diesem Board zugewiesen sind.
    """
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True)  # IDs der Mitglieder
    tasks = TaskSerializer(many=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serialisiert die Eingabedaten zur Erstellung eines neuen Boards und ermöglicht es, Mitglieder
    hinzuzufügen.

    Attributes:
        members (list[int]): Eine Liste der IDs der Mitglieder, die dem Board hinzugefügt werden
        sollen.
    """
    members = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = Board
        fields = ['title', 'members']

    def create(self, validated_data):
        """
        Erstellt ein neues Board und fügt Mitglieder hinzu. Der anfragende Benutzer wird als
        Eigentümer gesetzt.

        Args:
            validated_data (dict): Die validierten Eingabedaten für das neue Board.

        Returns:
            board (Board): Das erstellte Board-Objekt.
        """
        members_ids = validated_data.pop('members')
        request = self.context['request']
        board = Board.objects.create(title=validated_data['title'], owner=request.user)
        board.members.set(User.objects.filter(id__in=members_ids + [request.user.id]))
        return board
