from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import User
from django.db.models import Count, Q
from kanmind_app.models import Board, Task
from .serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardCreateSerializer,
    UserSerializer,
)


class BoardListCreateView(generics.ListCreateAPIView):
    """
    View für das Abrufen einer Liste von Boards oder das Erstellen eines neuen Boards.

    Diese View erlaubt es authentifizierten Benutzern, eine Liste der Boards abzurufen, bei denen
    der Benutzer entweder der Eigentümer ist oder Mitglied eines Boards. Darüber hinaus können
    Benutzer neue Boards erstellen.

    Permissions:
        - IsAuthenticated: Nur authentifizierte Benutzer können diese View verwenden.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Gibt den entsprechenden Serializer basierend auf der HTTP-Methode zurück.

        - Für 'POST' wird der BoardCreateSerializer verwendet.
        - Für 'GET' wird der BoardListSerializer verwendet.

        Returns:
            serializer_class (BaseSerializer): Der Serializer, der für die Anfrage verwendet wird.
        """
        if self.request.method == 'POST':
            return BoardCreateSerializer
        return BoardListSerializer

    def get_queryset(self):
        """
        Gibt eine Liste von Boards zurück, bei denen der Benutzer entweder der Eigentümer oder ein
        Mitglied ist.

        Die Boards werden mit zusätzlichen Annotationsdaten geliefert, wie:
            - member_count: Anzahl der Mitglieder des Boards (einschließlich des Benutzers, falls
              er Mitglied ist).
            - ticket_count: Anzahl der Aufgaben, die dem Board zugewiesen sind.
            - tasks_to_do_count: Anzahl der Aufgaben mit dem Status 'to-do'.
            - tasks_high_prio_count: Anzahl der Aufgaben mit hoher Priorität.

        Die Abfrage filtert die Boards so, dass nur die Boards zurückgegeben werden, bei denen der
        Benutzer entweder der Eigentümer (`owner`) oder ein Mitglied (`members`) ist. Dabei wird
        die `distinct()`-Methode verwendet, um doppelte Einträge zu vermeiden, falls der Benutzer
        sowohl Eigentümer als auch Mitglied eines Boards ist.

        Das Ergebnis enthält für jedes Board die folgenden berechneten Felder:
            - **member_count**: Die Anzahl der eindeutigen Mitglieder des Boards.
            - **ticket_count**: Die Gesamtzahl der Aufgaben, die dem Board zugewiesen sind.
            - **tasks_to_do_count**: Die Anzahl der Aufgaben mit dem Status 'to-do'.
            - **tasks_high_prio_count**: Die Anzahl der Aufgaben mit einer hohen Priorität.

        Returns:
            queryset (QuerySet): Eine Liste von Boards mit den annotierten Daten, die zusätzliche
            Informationen über Mitglieder und Aufgaben liefern.
        """
        return Board.objects.filter(
            Q(owner=self.request.user) |
            Q(members=self.request.user)
        ).distinct().annotate(
            member_count=Count('members', distinct=True),
            ticket_count=Count('tasks', distinct=True),
            tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to-do')),
            tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high')),
        )

    def perform_create(self, serializer):
        """
        Führt die Erstellung eines neuen Boards durch.

        Der anfragende Benutzer wird automatisch als Eigentümer des neuen Boards gesetzt,
        und die Mitglieder werden auf der Grundlage der übermittelten Daten hinzugefügt.

        Args:
            serializer (BoardCreateSerializer): Der Serializer, der die Board-Daten validiert und
            speichert.
        """
        serializer.save()


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View für das Abrufen, Aktualisieren und Löschen eines bestimmten Boards.

    Diese View ermöglicht:
    - Abrufen der Detailansicht eines Boards, einschließlich der Mitglieder und Aufgaben, die
    diesem Board zugewiesen sind.
    - Aktualisieren von Board-Daten (z.B. Titel oder Mitglieder).
    - Löschen eines Boards.

    Die View unterstützt die folgenden HTTP-Methoden:
    - GET: Gibt detaillierte Informationen zu einem Board zurück.
    - PUT/PATCH: Ermöglicht das Aktualisieren des Boards (z.B. Titel oder Mitglieder).
    - DELETE: Löscht das Board.

    Permissions:
        - IsAuthenticated: Nur authentifizierte Benutzer können diese View verwenden. Das bedeutet,
        der Benutzer muss in der Anfrage authentifiziert sein.

    Attributes:
        permission_classes (list): Eine Liste von Berechtigungen, die für den Zugriff auf diese
        View erforderlich sind.
        serializer_class (BoardDetailSerializer): Der Serializer, der für die Darstellung der
        Board-Daten verwendet wird.
        queryset (QuerySet): Die Abfrage, um die Boards aus der Datenbank zu holen. In diesem Fall
        alle Boards.
        lookup_field (str): Das Feld, das verwendet wird, um das Board in der URL zu
        identifizieren. Hier wird die `id` verwendet.
        lookup_url_kwarg (str): Der URL-Parameter, der die Board-ID übergibt. In diesem Fall wird
        `board_id` erwartet.

    Methods:
        perform_destroy(instance):
            Diese Methode wird verwendet, um das Board zu löschen. Sie wird aufgerufen, wenn eine
            DELETE-Anfrage erfolgt.
            - Vor dem Löschen kann zusätzliche Logik hinzugefügt werden, falls erforderlich (z.B.
              Überprüfungen der Benutzerberechtigungen).
            - Sobald das Board gelöscht wurde, wird eine leere Antwort mit dem Statuscode `204 No
              Content` zurückgegeben.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BoardDetailSerializer
    queryset = Board.objects.all()
    lookup_field = 'id'   # Das Board wird anhand der 'id' im URL-Pfad abgerufen
    lookup_url_kwarg = 'board_id'   # Der URL-Param. für die Board-ID wird als 'board_id' erwartet

    def perform_destroy(self, instance):
        """
        Löscht das Board-Objekt und gibt eine leere Antwort mit dem Statuscode `204 No Content`
        zurück.

        Args:
            instance (Board): Das Board-Objekt, das gelöscht werden soll.

        Returns:
            Response: Eine leere Antwort mit dem Statuscode `204 No Content`, falls das Löschen
            erfolgreich war.
        """
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailCheckView(APIView):
    """
    View für die Überprüfung, ob eine bestimmte E-Mail-Adresse bereits einem registrierten
    Benutzer zugeordnet ist.

    Diese View ermöglicht es, zu überprüfen, ob eine angegebene E-Mail-Adresse in der Datenbank
    existiert.

    Methode:
        - GET: Überprüft, ob die angegebene E-Mail-Adresse zu einem existierenden Benutzer gehört.

    Rückgabe:
        - Ein UserSerializer, wenn die E-Mail einem registrierten Benutzer entspricht.
        - Ein 404-Fehler, wenn der Benutzer mit dieser E-Mail nicht gefunden wird.
    """

    def get(self, request):
        """
        Überprüft, ob ein Benutzer mit der angegebenen E-Mail-Adresse existiert.

        Wenn der Benutzer existiert, wird der UserSerializer mit den Benutzerdaten zurückgegeben.
        Wenn der Benutzer nicht existiert, wird eine leere Antwort mit dem HTTP-Status 404
        zurückgegeben.

        Args:
            request (Request): Die HTTP-Anfrage, die die E-Mail-Adresse im Query-Parameter enthält.

        Returns:
            Response: Die Benutzerdaten als JSON, falls der Benutzer existiert, oder ein
            404-Fehler.
        """
        email = request.query_params.get('email')

        # Zusätzliche Fehlerprüfung:
        # Überprüfe, ob die E-Mail-Adresse überhaupt im Query-Parameter vorhanden ist
        if not email:
            return Response({"error": "Email parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"error": "User with this email not found."},
                            status=status.HTTP_404_NOT_FOUND)
