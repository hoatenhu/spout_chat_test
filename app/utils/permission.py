from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and has an admin role
        return request.user and request.user.is_authenticated and str(request.user.role) == 'admin'
    
class IsOwner(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and has an owner role
        return request.user and request.user.is_authenticated and str(request.user.role) == 'owner'
    
class IsTeamAdmin(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and has a team admin role
        return request.user and request.user.is_authenticated and str(request.user.role) == 'team admin'

class IsAdminOrTeamAdmin(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        # Check if the user is an admin or a team admin
        user_role = str(request.user.role).lower()
        return user_role == 'admin' or user_role == 'team admin'