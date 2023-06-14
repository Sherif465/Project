from django.shortcuts import render
from django.shortcuts import HttpResponse ,redirect

from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
# pre built form for user registration **VERY IMPORTANT** **VERY USEFUL**
from django.contrib.auth.forms import UserCreationForm
# method to check if the user is logged in or not
from django.contrib.auth.decorators import login_required
# (Q) is for searching in the database 
# also helps in using AND, OR Operators to search for multiple things
from django.db.models import Q
from .models import Room , Topic , Message
from .forms import RoomForm

def loginPage(request):  
    page = 'login'
    # To check if someone is already logged in or not
    if request.user.is_authenticated:
        return redirect('home')
    # *************************************
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        # to check if the username exists
        try:
            user = User.objects.get(username=username)
        except Exception:
            messages.error(request,'Username does not exist')
        # to check if the username and password are correct
        user = authenticate(request,username=username,password=password)
        # if the user is not None then the username and password are correct
        if user is not None:
            login(request,user) # used to login the user
            return redirect('home') 
        else: 
            messages.error(request,'Username OR password is incorrect')
    context = {'page':page}
    return render(request,'base/login_register.html',context)

def logoutUser(request):
    logout(request)
    return redirect('home')
    
def registerPage(request):
    form = UserCreationForm()
    context = {'form':form}
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # to not save the user yet / to access the user object
            user.username = user.username.lower()
            user.save()
            login(request,user) # to login the user after registration
            return redirect('home')
        else:
            for msg in form.error_messages:
                messages.error(request,form.error_messages[msg])
    return render(request,'base/login_register.html',context)

def home(request):
    # to get whatever passed in the url
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # ******************************
    # To get the rooms that have the topic name that contains the q
    # and if q is empty then get all the rooms
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    topics = Topic.objects.all()
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q)) # to get the messages of the rooms that have the topic name that contains the q
    context={'rooms':rooms , 'topics':topics , 'room_count':room_count , 'room_messages':room_messages}
    return render(request,'base/home.html',context)

def room(request,pk): 
    room = Room.objects.get(id=pk)
    # to get child attributes of the room we type ******room.childAttribute_set.all()******
    room_messages = room.message_set.all() # to get all the messages of that room /**_set.all()** mostly used in 1 to many relationships
    participants = room.participants.all() # to get all the participants in the room /**.all()** mostly used in many to many relationships
    if request.method == 'POST': # to check if the user is sending a message
        message = Message.objects.create( # to create a message
            user = request.user, # to get the user that is sending the message
            room = room, # to get the room that the message is sent in
            body = request.POST.get('body') # to get the message body
        )
        room.participants.add(request.user) # to add the user to the participants of the room
        return redirect('room',pk=room.id) # to redirect to the same page in order to refresh the page to prevent the message from being sent multiple times
    context = {'room':room , 'room_messages':room_messages , 'participants':participants}
    return render(request,'base/room.html',context) 



def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all() # to get all the rooms of that user
    room_messages = user.message_set.all() # to get all the messages of that user
    topics = Topic.objects.all()
    context = {'user':user , 'rooms':rooms , 'room_messages':room_messages , 'topics':topics}
    return render(request,'base/profile.html',context)
# @login_required is used to check if the user is logged in or not
# and if not then it redirects to the login page
# also used as a restriction to some pages that only logged in users can access
@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        # to get the topic if it exists or create it if it doesn't
        topic, created = Topic.objects.get_or_create(name=topic_name) 
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'), # to get the name of the room
            description = request.POST.get('description')
        ) 
        return redirect('home')
    context={'form':form,'topics':topics}
    return render(request,'base/room_form.html',context)


@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    # we made an instance of the room \
    # so that we can update it so we it's values are read in the form
    form = RoomForm(instance=room)
    # to check if the user is the host of the room or not
    # in order to prevent someone else from editing the room
    topics = Topic.objects.all()
    
    if request.user != room.host :
        return HttpResponse('You are not allowed here')
    if request.method == 'POST':
        
        topic_name = request.POST.get('topic')
        # to get the topic if it exists or create it if it doesn't
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name') # adding our data to the form of that room
        # to get the topic if it exists or create it if it doesn't
        room.topic = topic 
        
        room.description = request.POST.get('description') # adding our data to the form of that room
        room.save()
        return redirect('home')
    context = {'form':form, 'topics':topics, 'room':room}
    return render(request,'base/room_form.html',context)


@login_required(login_url='login')
def deleteRoom(request,pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host :
        return HttpResponse('You are not allowed here')
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':room})


@login_required(login_url='login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)
    if request.user != message.user :
        return HttpResponse('You are not allowed here')
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':message})