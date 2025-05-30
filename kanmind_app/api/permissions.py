from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrMember(BasePermission):
   def has_object_permission(self, request, view, obj):
       return (
           obj.owner == request.user or
           request.user in obj.members.all()
       )


class IsBoardMemberOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Lesezugriff ist für alle angemeldeten Benutzer erlaubt
        if request.method in SAFE_METHODS:
            return True

        # Schreibzugriff nur für Mitglieder des Boards oder Owner
        return (
            request.user == obj.board.owner or
            request.user in obj.board.members.all()
        )
