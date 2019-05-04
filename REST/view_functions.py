from django.db.models import Sum, Avg

from .models import Split, Participation, Run, User

def reached_finish(run, participation):    
    splits = Split.objects.filter(participation=participation).order_by('timestamp')
    start_time = participation.run.start_datetime
    run_time = splits.last().timestamp - start_time
    avg_tempo = run_time / run.distance

    max_tempo = None
    min_tempo = None
    if splits[0].distance != 0:
        max_tempo = (splits[0].timestamp - start_time) / (splits[0].distance / 1000)
        min_tempo = max_tempo
    
    for i in range(1, len(splits)):
        split_time = splits[i].timestamp - splits[i-1].timestamp
        split_difference = splits[i].distance - splits[i-1].distance
        if split_difference != 0:
            tempo = split_time / (split_difference / 1000)
            if max_tempo is None and min_tempo is None:
                max_tempo = tempo
                min_tempo = tempo
            else:
                max_tempo = tempo if tempo > max_tempo else max_tempo
                min_tempo = tempo if tempo < min_tempo else min_tempo  

    # determining the place by how many people finished already

    num_finished = len(Participation.objects.filter(run=run).exclude(position=None))
    num_runners = len(run.runners.all())
    num_finished += 1
    position = num_finished

    participation.position = position
    participation.time = run_time
    participation.avg_tempo = avg_tempo
    participation.max_tempo = max_tempo
    participation.min_tempo = min_tempo
    participation.save()

    if num_finished == num_runners:
        run.finished = True
        run.save()
    
def get_stats(user):
    completed_runs = Participation.objects.filter(user=user).exclude(position=None)
    completed_races = completed_runs.exclude(run__privacy_level=Run.ONLY_ME)
    total_runs = completed_runs.count()
    race_wins = completed_races.filter(position=1).count()
    total_km = completed_runs.aggregate(Sum('run__distance'))
    total_km = total_km['run__distance__sum']

    return {
        'runs': total_runs,
        'wins': race_wins,
        'total_km': total_km if total_km else 0,
    }