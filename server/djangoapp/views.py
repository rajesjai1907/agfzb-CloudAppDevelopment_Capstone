from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
# from .restapis import related methods
from .restapis import get_dealers_from_cf
from .restapis import get_dealer_by_id_from_cf
from .restapis import get_dealer_reviews_from_cf, create_new_review
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('/djangoapp/')
        else:
            # If not, return to login page again
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('/djangoapp')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("/djangoapp/")
        else:
            return render(request, 'djangoapp/registration.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://93cde033.eu-gb.apigw.appdomain.cloud/api/dealership"
        
        # Get list of dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context['dealership_list'] = dealerships
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealerId):
    if request.method == "GET":
        context = {}
        dealer_url = "https://93cde033.eu-gb.apigw.appdomain.cloud/api/dealership"
        dealer = get_dealer_by_id_from_cf(dealer_url, dealerId=dealerId)
        context["dealer"] = dealer
        print(dealer)
        #try:
        review_url = "https://93cde033.eu-gb.apigw.appdomain.cloud/api/review"
        reviews = get_dealer_reviews_from_cf(review_url, dealerId=dealerId)
        context["reviews"] = reviews
        print(reviews)
        #except:
        print("No reviews")
        #return HttpResponse(context["reviews"])
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    context = {}
    if request.user.is_authenticated:
        url = 'https://93cde033.eu-gb.apigw.appdomain.cloud/api/dealership'
        # Get dealer from the URL
        dealership = get_dealers_from_cf(url, id=dealer_id)[0]
        context['dealer_id'] = dealer_id
        context['dealer_name'] = dealership.full_name
        context['cars'] = CarModel.objects.filter(dealer_id=dealer_id)
        # New review submission
        if request.method == 'POST':
            url = 'https://93cde033.eu-gb.apigw.appdomain.cloud/api/reviews'
            last_review = get_dealer_reviews_from_cf(url, getLastReview=True)[0]
            review = dict()
            review['id'] = last_review.id
            review['name'] = request.user.username
            review['time'] = datetime.utcnow().isoformat()
            review['dealership'] = dealer_id
            review['review'] = request.POST['content']
            # Only use fields if included
            if request.POST['purchasecheck'] and request.POST['purchasedate']:
                review['purchase'] = True
                review['purchase_date'] = request.POST['purchasedate']
            else:
                review['purchase'] = False
            # Select car chosen
            car = CarModel.objects.get(id=int(request.POST['car']))
            review['car_make'] = car.make.name
            review['car_model'] = car.name
            review['car_year'] = car.year.year
            json_payload = dict()
            json_payload['review'] = review
            print(json_payload)
            review_created = create_new_review(url, json_payload)
            print(review_created)
            return redirect('djangoapp:dealer_details', dealer_id=dealer_id)
        return render(request, 'djangoapp/add_review.html', context)

