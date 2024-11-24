from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .import views



urlpatterns = [
    path('', views.home, name = "home"),
    path('login/', views.loginUser, name="login"),
    path('profile/', views.profile, name="profile"),
    path('logout/', views.logoutUser, name="logout"),
    path('signup/', views.signupUser, name="signup"),
    path('confirmOption/', views.confirmOption, name="confirmOption"),
    path('predict/', views.predict, name="predict"),
    path('appoint/', views.appoint, name="appoint"),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('prediction/', views.predict_view, name="prediction"),
    path('doctor/<int:pk>', views.doctor_profile, name="doctorprofile"),
    path('book/<int:schedule_id>/', views.book_appointment, name='book_appointment'),
    path('confirmation/<int:appointment_id>/', views.appointment_confirmation, name='appointment_confirmation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)