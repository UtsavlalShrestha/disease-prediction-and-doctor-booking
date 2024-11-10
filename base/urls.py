from django.urls import path
from .import views



urlpatterns = [
    path('', views.home, name = "home"),
    path('login/', views.loginUser, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('signup/', views.signupUser, name="signup"),
    path('confirmOption/', views.confirmOption, name="confirmOption"),
    path('predict/', views.predict, name="predict"),
    path('appoint/', views.appoint, name="appoint"),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('prediction/', views.predict_view, name="prediction"),

]
