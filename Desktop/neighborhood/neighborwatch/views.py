# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, CreateHoodForm, CreateBizForm, CreatePostForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from .models import Neighbour, Profile, Join, Posts, Business

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your hoodwatch account.'
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('landing')
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

@login_required(login_url='/accounts/login/')
def index(request):
    """
    Renders the index page
    """
    if Join.objects.filter(user_id = request.user).exists():
        hood = Neighbour.objects.get(pk = request.user.join.hood_id)
        occupants = Profile.get_user_by_hood(id= request.user.join.hood_id).all()
        posts = Posts.get_post_by_hood(id = request.user.join.hood_id)
        biz = Business.get_biz_by_hood(id = request.user.join.hood_id)
        return render(request,'hood.html', locals())

    else:
        hoods = Neighbour.objects.all()
        return render(request, 'index.html', locals())


@login_required(login_url='/accounts/login/')
def createhood(request):
    """
    Renders the creating hood form
    """
    if request.method == 'POST':
        form = CreateHoodForm(request.POST)
        if form.is_valid():
            hood = form.save(commit = False)
            hood.user = request.user
            hood.save()
            return redirect('landing')
    else:
        form = CreateHoodForm()
        return render(request, 'forms/hood.html', {"form":form})


@login_required(login_url='/accounts/login/')
def edithood(request , id):
    """
    This view edits neighbour class
    """
    neighbour = Neighbour.objects.get(pk = id)
    if request.method == 'POST':
        form = CreateHoodForm(request.POST,instance = neighbour)
        if form.is_valid():
            hood = form.save(commit=False)
            hood.user = request.user
            hood.save()
        return redirect('landing')
    else:
        form = CreateHoodForm(instance = neighbour)
    return render(request, 'edit/hood.html', locals())


@login_required(login_url='/accounts/login/')
def delhood(request , id):
    """
    View function that deleted a hood
    """
    Neighbour.objects.filter(pk = id).delete()
    return redirect('landing')

@login_required(login_url='/accounts/login/')
def join(request , hoodid):
    """
    This view edits neighbour class
    """
    this_hood = Neighbour.objects.get(pk = hoodid)
    if Join.objects.filter(user = request.user).exists():
        Join.objects.filter(user_id = request.user).update(hood_id = this_hood.id)
    else:
        Join(user=request.user, hood_id = this_hood.id).save()
    messages.success(request, 'Success! You have succesfully joined this Neighbourhood ')
    return redirect('landing')


@login_required(login_url='/accounts/login/')
def createbiz(request):
    """
    Creates business class
    """
    hoods = Neighbour.objects.all()
    for hood in hoods:
        if Join.objects.filter(user_id = request.user).exists():
            if request.method == 'POST':
                form = CreateBizForm(request.POST)
                if form.is_valid():
                    business = form.save(commit = False)
                    business.user = request.user
                    business.hood = hood
                    business.save()
                    messages.success(request, 'Success! You have created a business')
                    return redirect('landing')
            else:
                form = CreateBizForm()
                return render(request, 'forms/biz.html',{"form":form})
        else:
            messages.error(request, 'Error! Join a Neighbourhood to create a Business')


@login_required(login_url='/accounts/login/')
def exithood(request, id):
    """
    Allows users to exit hoods
    """
    Join.objects.get(user_id = request.user).delete()
    messages.error(request, "Neighbourhood exited")
    return redirect('landing')

@login_required(login_url='/accounts/login/')
def createPost(request):
    """
    Allow users belonging to a neighbourhood to post
    """
    hoods = Neighbour.objects.all()
    for hood in hoods:
        if Join.objects.filter(user_id = request.user).exists():
            if request.method == 'POST':
                form = CreatePostForm(request.POST)
                if form.is_valid():
                    post = form.save(commit = False)
                    post.user = request.user
                    post.hood = hood
                    post.save()
                    messages.success(request,'You have succesfully created a Forum Post')
                    return redirect('landing')
            else:
                form = CreatePostForm()
                return render(request,'forms/posts.html',{"form":form})
        else:
            messages.error(request, 'Error! You can only create a post after Joining/Creating a neighbourhood')


@login_required(login_url='/accounts/login/')
def profile(request, user_id):
    """
    Function that enables one to see their profile
    """
    title = "Profile"
    profile = Profile.objects.get(user_id=user_id)
    biz = Business.objects.filter(user_id=user_id).all()
    hood = Neighbour.objects.filter(user_id=user_id).all()
    users = User.objects.get(id=user_id)
    return render(request, 'profile.html', locals())

@login_required(login_url='/accounts/login/')
def search_results(request):

    if 'hood' in request.GET and request.GET["hood"]:
        search_term = request.GET.get("hood")
        searched_hoods = Neighbour.search_by_title(search_term)
        message = f"{search_term}"

        return render(request, 'search.html',{"message":message,"hood": searched_hoods})

    else:
        message = "You haven't searched for any hood"
        return render(request, 'search.html',{"message":message})

