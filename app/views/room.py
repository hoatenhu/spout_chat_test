from django.shortcuts import render

def room(request, room_name):
    print(f"Room name: {room_name}")  # Debugging line
    
    return render(request, 'chat.html', {
        'room_name': room_name
    })
