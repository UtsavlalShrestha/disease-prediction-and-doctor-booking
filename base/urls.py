from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .import views, admin_view



urlpatterns = [
    path('', views.home, name = "home"),
    # path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('login/', views.loginUser, name="login"),
    path('profile/', views.profile, name="profile"),
    path('logout/', views.logoutUser, name="logout"),
    path('signup/', views.signupUser, name="signup"),
    path('confirmOption/', views.confirmOption, name="confirmOption"),
    path('predict/', views.predict, name="predict"),
    path('appoint/', views.appoint, name="appoint"),
    path('add_patient_details/<int:schedule_id>/', views.add_patient_details, name='add_patient_details'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('prediction/', views.predict_view, name="prediction"),
    path('doctor/<int:pk>', views.doctor_profile, name="doctorprofile"),
    path('doctor_schedule/<int:pk>', views.doctor_schedule_view, name="doctorschedule"),
    path('book/<int:schedule_id>/', views.book_appointment, name='book_appointment'),
    path('confirmation/<int:appointment_id>/', views.appointment_confirmation, name='appointment_confirmation'),
    path('hospital_dashboard/', views.hospital_dashboard, name="hospital_dashboard"),
    path('recommend-doctors/<int:prediction_id>/', views.recommend_doctors_view, name='recommend_doctors'),

    #Forget Password
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Doctor URLs
    path('doctors/', admin_view.doctor_list, name='doctor_list'),
    path('doctor/add/', admin_view.doctor_add, name='doctor_add'),
    path('doctor/edit/<int:pk>/', admin_view.doctor_edit, name='doctor_edit'),
    path('doctor/delete/<int:pk>/', admin_view.doctor_delete, name='doctor_delete'),
    
    # Schedule URLs
    path('schedules/', admin_view.schedule_list, name='schedule_list'),
    path('schedule/add/', admin_view.schedule_add, name='schedule_add'),
    path('schedule/edit/<int:pk>/', admin_view.schedule_edit, name='schedule_edit'),
    path('schedule/delete/<int:pk>/', admin_view.schedule_delete, name='schedule_delete'),
    
    # Appointment URLs
    path('appointments/', admin_view.appointment_list, name='appointment_list'),
    path('appointment/add/', admin_view.appointment_add, name='appointment_add'),
    path('appointment/edit/<int:pk>/', admin_view.appointment_edit, name='appointment_edit'),
    path('appointments/approve/', admin_view.approve_appointments, name='approve_appointments'),
    path('appointment/delete/<int:pk>/', admin_view.appointment_delete, name='appointment_delete'),
    path('approved_appointments/', admin_view.approved_appointments, name='approved_appointments'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)