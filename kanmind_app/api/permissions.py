from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrMember(BasePermission):
    """
    Custom permission to allow access only to the owner of the object
    or users who are members of the object.
    """
    def has_object_permission(self, request, view, obj):
       """
        Returns True if the requesting user is either the owner of the object
        or listed among the object's members.
        """
       return (
           obj.owner == request.user or
           request.user in obj.members.all()
       )


class IsBoardMemberOrReadOnly(BasePermission):
    """
    Custom permission to allow full access to board members and the board owner,
    while allowing read-only access to others.
    """
    def has_object_permission(self, request, view, obj):
        """
        Allows read-only access (e.g. GET, HEAD, OPTIONS) to everyone.
        Allows write access only if the user is the board owner or one of the board's members.
        """
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user == obj.board.owner or
            request.user in obj.board.members.all()
        )
