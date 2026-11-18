from rest_framework import permissions


class IsConversationParticipant(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        return request.user.id in (obj.customer_id, obj.technician_id)


class IsMessageSenderOrParticipant(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.id in (
                obj.conversation.customer_id,
                obj.conversation.technician_id,
            )
        return obj.sender_id == request.user.id