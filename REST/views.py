import json
from datetime import datetime

import django
from django import urls
from django.contrib import auth
from django.core import exceptions
from django.http.response import HttpResponse
from django.http.response import JsonResponse
from django.http.response import HttpResponseForbidden
from django.http.response import HttpResponseBadRequest
from django.http.response import HttpResponseNotFound
from django.db.models import Max
from django.shortcuts import render

from .models import Run, Participation, Split, Comment, Watching, Like
from .view_functions import reached_finish
from .decorators import login_required, require_http_methods
from .helpers import MessageResponse


@require_http_methods(["GET"])
def test_view(request):
    return render(request, 'views/test.html')


@require_http_methods(["GET"])
def version(request):
    return JsonResponse({'version': '0.1.4'})

@require_http_methods(["GET"])
def time(request):
    time_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return JsonResponse({'time': time_now})


@require_http_methods(["GET"])
def runs_get(request):
    _filter = request.GET.get('filter', None)
    status = request.GET.get('status', None)
    privacy = request.GET.get('privacy', 'all')

    participations = Participation.objects.filter(run__privacy_level=privacy)

    if status == 'finished':
        participations = participations.filter(run__finished=True)
    else:
        participations = participations.filter(run__finished=False)
        timestamp = datetime.now().replace(microsecond=0, second=0)
        if status == 'ongoing':
            participations = participations.filter(run__start_datetime__lt=timestamp)
        elif status == 'upcoming':
            participations = participations.exclude(run__start_datetime__lt=timestamp)
        
    if _filter=="joined" and request.user.is_authenticated:        
        participations = participations.filter(user=request.user)

    runs = [p.run for p in participations]
         
    return JsonResponse([
        {
            'run': run.serialize(),            
            'creator': run.creator.serialize() if run.creator else None,
            'runners': [runner.serialize() for runner in run.runners.all()],
            'participating': run.runners.all().filter(pk=request.user.pk).exists(),
            'likes': run.get_likes(),
            'watching': run.num_watching(),
        } 
        for run in runs
    ], safe=False)

    
@require_http_methods(["POST"])
@login_required
def run_create(request):    
    try:
        distance = request.POST['distance']
        date = request.POST['date']
        time = request.POST['time']
        privacy_level = request.POST['privacy']    
        max_runners = request.POST.get('runners', 1)            
    except KeyError as e:
        return HttpResponseBadRequest("Argument {} is required".format(e.args[0]))

    start_datetime = datetime.strptime("{}T{}".format(date, time), "%Y-%m-%dT%H:%M") 
    timestamp = datetime.now().replace(microsecond=0, second=0)
    if privacy_level != Run.ONLY_ME and start_datetime < timestamp:
        return HttpResponseForbidden("Cannot create runs in the past")
    
    try:
        run = Run(
            distance=distance,
            start_datetime=start_datetime,
            privacy_level=privacy_level,
            max_runners=max_runners,    
            creator=request.user,    
        )     
        run.full_clean()
    except exceptions.ValidationError as e:
        return HttpResponseBadRequest(e.messages[0])
    except ValueError as e:
        return HttpResponseBadRequest("Invalid date or time")

    run.save()
    
    participation = Participation(
        run=run,
        user=request.user,
    )
    participation.save()
    
    response = JsonResponse(
        run.serialize(),
        status=201,
    )
    response['Location'] = urls.reverse('run_get', args=[run.id])

    return response


@require_http_methods(["GET"])
def run_get(request, run_id):
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    participating = run.runners.all().filter(pk=request.user.pk).exists()
    if run.privacy_level == Run.ONLY_ME and not participating:            
        return HttpResponseForbidden("This run is private")

    return JsonResponse(
        {
            'run': run.serialize(),
            'creator': run.creator.serialize(),
            'runners': [runner.serialize() for runner in run.runners.all()],
            'participating': participating,
            'likes': run.get_likes(),
            'watching': run.num_watching(),
        }
    )


@require_http_methods(["POST"])
@login_required
def run_join(request, run_id):  
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")
    
    if run.privacy_level == Run.ONLY_ME:
        return HttpResponseForbidden("You cannot join private runs.")

    num_runners = run.runners.all().count()
    if num_runners == run.max_runners:
        return HttpResponseForbidden("Run is full.")

    try:
        participation = Participation(
            run=run,
            user=request.user,
        )
        participation.full_clean()
    except exceptions.ValidationError as e:
        return HttpResponseBadRequest(e.messages[0])

    participation.save()
            
    return JsonResponse(
        {
            'run': run.serialize(),
            'runners': [runner.serialize() for runner in run.runners.all()],
        }
    )


@require_http_methods(["DELETE"])
@login_required
def run_quit(request, run_id):  
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")
        
    try:
        participation = Participation.objects.get(run=run, user=request.user)
        participation.delete()
    except Participation.DoesNotExist:
        return HttpResponseNotFound("You don't participate in this run")
    
    return MessageResponse("Successfully quit.")


@require_http_methods(["GET"])
def run_results(request, run_id):
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")
    
    participations = Participation.objects.filter(run=run)

    return JsonResponse(
        {
            'run': run.serialize(),
            'runners': [
                {
                    'runner': p.user.serialize(),
                    'stats': p.serialize() if not p.position is None else None,
                }
                for p in participations
            ],
        }
    )


@require_http_methods(["GET", "POST"])
def splits(request, run_id):
    if (request.method == "POST"):
        return splits_post(request, run_id)
    else:
        return splits_get(request, run_id)

    
@require_http_methods(["GET"])
@login_required
def splits_get(request, run_id):
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    participations = Participation.objects.filter(run=run)

    if not participations.filter(user=request.user).exists():
        return HttpResponseNotFound("You don't participate in this run")

    later_than = request.GET.get('later_than', None)
    if later_than is None:
        later_than = "2000-01-01T22:22:22"
        
    return JsonResponse([
        {
            'user': participation.user.serialize(),
            'splits': [
                split.serialize() for split in
                    participation.splits()
                        .filter(timestamp__gt=later_than)
                        .order_by('timestamp')

            ]
        }
        for participation in participations
    ], safe=False)

@require_http_methods(["POST"])
@login_required
def splits_post(request, run_id):
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    if run.finished:
        return HttpResponseForbidden("Run already ended")

    try:
        splits = json.loads(request.POST['splits'])
    except KeyError as e:
        return HttpResponseBadRequest("Argument {} is required".format(e.args[0]))
    except json.JSONDecodeError as e:
        return HttpResponseBadRequest("'splits' must be valid JSON")

    try:
        participation = Participation.objects.get(run=run, user=request.user)        
    except Participation.DoesNotExist:
        return HttpResponseNotFound("You don't participate in this run")

    finish_reached = False
    db_splits = []
    for split in splits:
        try:
            timestamp = datetime.strptime(split['timestamp'], "%Y-%m-%dT%H:%M:%S") 
            timestamp = datetime.now().replace(microsecond=0)
        except ValueError as e:
            return HttpResponseBadRequest("Malformed 'timestamp' field".format(e.args[0]))

        try:
            distance = int(split['distance'])
        except ValueError as e:
            return HttpResponseBadRequest("Distance must be an integer".format(e.args[0]))

        try:
            split = Split(
                participation=participation,
                distance=split['distance'],
                timestamp=timestamp,
            )            
            split.full_clean()
            db_splits.append(split)
            if distance >= run.distance * 1000: # just reached the end
                finish_reached = True 
        except exceptions.ValidationError as e:
            return HttpResponseBadRequest(e.messages[0])
        except KeyError as e:
            return HttpResponseBadRequest("Each split needs an {} field".format(e.args[0]))
        
    
    if finish_reached == False:
        return HttpResponseBadRequest("Splits must be for the whole run from start to finish")    

    for split in db_splits:
        split.save()
    reached_finish(run, participation)
    
    return MessageResponse("Submitted")


@require_http_methods(["POST"])
@login_required
def split_create(request, run_id):
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    try:
        distance = int(request.POST['meters_traveled'])
    except KeyError as e:
        return HttpResponseBadRequest("Argument {} is required".format(e.args[0]))
    except ValueError:
        return HttpResponseBadRequest("'meters_traveled' must be an integer")

    if run.finished:
        return HttpResponseForbidden("Run has already finished")

    timestamp = datetime.now().replace(microsecond=0)

    if run.start_datetime > timestamp:
        return HttpResponseForbidden("Run hasn't started yet")

    try:
        participation = Participation.objects.get(run=run, user=request.user)
    except Participation.DoesNotExist:
        return HttpResponseNotFound("You don't participate in this run") 

    last_split = Split.objects.filter(participation=participation).order_by('timestamp').last()
    
    if not last_split is None:
        if last_split.distance >= run.distance * 1000:
            return HttpResponseForbidden("You already passed the finish line.")
        
        if distance < last_split.distance:
            return HttpResponseForbidden("Cannot run backwards.")
            
    try:
        split = Split(
            participation=participation,
            distance=distance,
            timestamp=timestamp,
        )
        split.full_clean()
    except exceptions.ValidationError as e:
        return HttpResponseBadRequest(e.messages[0])

    split.save()

    if distance >= run.distance * 1000: # just reached the end
        reached_finish(run, participation)

    return JsonResponse(split.serialize())

@require_http_methods(['GET'])
def comments_get(request, run_id):  
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    comments = Comment.objects.filter(run=run)    

    return JsonResponse(
        [c.serialize() for c in comments],
        safe=False,
    )

@login_required
@require_http_methods(['POST'])
def add_comment(request, run_id):
    try:
        text = request.POST['comment']
    except KeyError:
        return HttpResponseBadRequest("Parameter 'comment' is needed")
    
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    try:
        comment = Comment(
            user=request.user,
            run=run,
            text=text,
        )
        comment.full_clean()
    except exceptions.ValidationError as e:
        return HttpResponseBadRequest(e.messages[0])
    comment.save()

    return JsonResponse(comment.serialize(), status=201)

@login_required
@require_http_methods(['POST'])
def start_watching(request, run_id):     
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    try:
        watching = Watching(
            user=request.user,
            run=run,
        )
        watching.full_clean()
    except exceptions.ValidationError as e:
        return HttpResponseBadRequest(e.messages[0])
    watching.save()

    return MessageResponse("Started watching")


@require_http_methods(["DELETE"])
@login_required
def stop_watching(request, run_id):  
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")
        
    try:
        watching = Watching.objects.get(run=run, user=request.user)
        watching.delete()
    except Watching.DoesNotExist:
        return HttpResponseNotFound("You aren't watching this run")
    
    return MessageResponse("Stopped watching")


@login_required
@require_http_methods(['POST'])
def add_like(request, run_id):     
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")

    try:
        like = Like(
            user=request.user,
            run=run,
        )
        like.full_clean()
    except exceptions.ValidationError as e:
        return HttpResponseBadRequest(e.messages[0])
    like.save()

    return MessageResponse("Run liked")


@require_http_methods(["DELETE"])
@login_required
def remove_like(request, run_id):  
    try:
        run = Run.objects.get(pk=run_id)
    except Run.DoesNotExist:
        return HttpResponseNotFound("Run does not exist")
        
    try:
        like = Like.objects.get(run=run, user=request.user)
        like.delete()
    except Like.DoesNotExist:
        return HttpResponseNotFound("You haven't liked this run")
    
    return MessageResponse("Run unliked")


