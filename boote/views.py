from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from datetime import datetime, timedelta
import time 
from django.shortcuts import render
from .models import Boat, BoatType, Booking, BoatIssue
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from .forms import NewReservationForm, BootIssueForm


def booking_overview(request):
    template = loader.get_template('boote/booking_overview.html')

    user = request.user

    mybookings = []
    for booking in Booking.objects.filter(user=user, date__gte=datetime.now()).order_by('date'):
        mybookings.append([booking.date.strftime("%A"),booking.date.strftime("%Y/%d/%m"),booking.time_from.strftime("%H:%M"),booking.time_to.strftime("%H:%M"), booking.boat, booking.pk])

    overview = []
    for boat in Boat.objects.all():
        overview.append([boat.name + " (" + boat.type.name +")", boat.pk, boat.getBookings7days()])

    dates = []
    d = datetime.now()
    for i in range(0,7):
        dates.append([d.strftime("%A"), d.strftime("%Y/%d/%m")])
        d = d + timedelta(days=1)

    context = RequestContext(request, {'booking_overview': overview, "booking_dates":dates, "mybookings":mybookings})
    return HttpResponse(template.render(context))

def booking_my_bookings(request):
    template = loader.get_template('boote/booking_my_bookings.html')

    user = request.user

    mybookings = []
    for booking in Booking.objects.filter(user=user, date__gte=datetime.now()).order_by('date'):
        mybookings.append([booking.date.strftime("%A"),booking.date.strftime("%Y/%d/%m"),booking.time_from.strftime("%H:%M"),booking.time_to.strftime("%H:%M"), booking.boat, booking.pk])

    context = RequestContext(request, {"mybookings":mybookings})
    return HttpResponse(template.render(context))

def boot_liste(request):
    template = loader.get_template('boote/boot_liste.html')

    user = request.user
    
    boots = []
    for boat in Boat.objects.all().order_by('-type'):
        boots.append([boat, boat.getNumberOfIssues])
        
    context = RequestContext(request, {'boots': boots})
    return HttpResponse(template.render(context))

def boot_detail(request, boot_pk):
    template = loader.get_template('boote/boot_detail.html')
    boat = Boat.objects.get(pk=boot_pk)
    user = request.user
    numIssues = boat.getNumberOfIssues
    
    
    context = RequestContext(request, {        
        'boot': boat,
        'user': user,
        'numIssues' : numIssues
    })
    return HttpResponse(template.render(context))


def booking_boot(request, boot_pk):
    template = loader.get_template('boote/booking_boot.html')
    boot = Boat.objects.get(pk=boot_pk)
    user = request.user

    bookings = Boat.getDetailedBookings7Days(boot)
    overview = []
    d = datetime.now()
    for i in range(0,7):
        overview.append([d.strftime("%A"), d.strftime("%Y/%d/%m"), bookings[i]])
        d = d + timedelta(days=1)

    # check which bookings are done for current user
    mybookings = []
    for booking in Booking.objects.filter(user=user, date__gte=datetime.now()).order_by('date'):
        mybookings.append([booking.date.strftime("%A"),booking.date.strftime("%Y/%d/%m"),booking.time_from.strftime("%H:%M"),booking.time_to.strftime("%H:%M"), booking.boat, booking.pk])

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NewReservationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            res_date = form.cleaned_data['res_date']
            res_start = form.cleaned_data['res_start']
            res_duration = form.cleaned_data['res_duration']
            res_duration = int(res_duration)
            
            start = datetime.strptime(res_date + " " + res_start, '%Y-%m-%d %H:%M')
            end = start + timedelta(0,0,0,0,res_duration) # minutes
                        
            res_end =  end
            b = Booking(user=user, boat=boot, date=res_date, time_from=res_start, time_to=res_end)
            b.save()
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('booking-my-bookings'))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NewReservationForm()

    context = RequestContext(request, {
        'form': form,
        'boot': boot,
        'user': user,
        'mybookings': mybookings,
        'booking_overview':overview,

    })
    return HttpResponse(template.render(context))

def booking_remove(request, booking_pk):
    booking = Booking.objects. get(pk=booking_pk, user=request.user)
    booking.delete()
    return redirect('booking-my-bookings')


def boot_issues(request, boot_pk):
    template = loader.get_template('boote/boot_issue.html')
    boot = Boat.objects.get(pk=boot_pk)
    user = request.user
    issues = BoatIssue.objects.filter(boat=boot_pk)
    
    
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = BootIssueForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            res_reported_descr = form.cleaned_data['res_reported_descr']
            
            b = BoatIssue(boat=boot, status=1, reported_descr=res_reported_descr, reported_by=user, reported_date=datetime.now())
            b.save()
            # redirect to a new URL:
            return redirect('boot-issues', boot.pk)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = BootIssueForm()

    context = RequestContext(request, {
        'form_issue': form,
        'boot': boot,
        'user': user,
        'issues' : issues,        
    })
    return HttpResponse(template.render(context))

def boot_fix_issue(request, issue_pk):
    issue = BoatIssue.objects.get(pk=issue_pk)
    issue.status = 2
    issue.fixed_by = request.user
    issue.fixed_date = datetime.now()
    issue.save()
    return redirect('boot-issues', issue.boat.pk)
    
    