from datetime import timedelta

from django.http.response import JsonResponse

class MessageResponse(JsonResponse):
    def __init__(self, message, status=200):
        super().__init__({'message': message}, status=status)

def format_tempo(delta):
    if delta is None:
        return None

    if delta.seconds >= 60 * 60:
        delta = timedelta(seconds=(60 * 60 - 1))

    total_seconds = int(delta.total_seconds())

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return "{}:{}".format(minutes, seconds)     

def format_run_time(delta):
    if delta is None:
        return None
        
    if delta.seconds >= 60 * 60:
        delta = timedelta(seconds=(24 * 60 * 60 - 1))
    
    total_seconds = int(delta.total_seconds())
    
    hours = total_seconds // (60 * 60)
    total_seconds %= 60 * 60
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return "{}:{}:{}".format(hours, minutes, seconds) 




    

    

    






