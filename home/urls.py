from django.urls import path,include
from . import views

from . import api
urlpatterns = [
    path('',views.home,name="home"),
    path('home',views.home,name="home"),
    path('loginparking',views.loginforparking),
    path('signin',views.signinuser),
    path('signinparking',views.signinparking),
    path('historyuser',views.historyuser),
    path('infouser',views.infouser),
    path('changeuserpassword',views.changepassworduser),
    path('logout',views.logout),
    path('changemanagerpassword',views.changepassworduser_parking_manager),
    path('historytraffic' , views.car_traffics),
    path('infomanager' , views.info_manager),
    path('carinparking' , views.car_in_parking),
    path('logintoparking/<int:id>',views.logintoparking),
    path('removeloginqr',views.removeloginqr),
    path('exitparking/<int:id>',views.addexit),
    path('validqrcode',views.api_accept_qrcode),
    path('api/getparking',api.api_get_parkings),
    path('api/userinfo',api.api_infouser),
    path('api/history',api.api_historyuser),
    path('api/changepassword',api.api_change_password),
    path('api/getloginqr',api.api_get_login_qrcode),
    path('api/removeqr',api.api_remove_login_qrcode),
    path('api/getexitqr',api.api_get_exit_parking_qrcode),
    path('api/status-user',api.api_get_user_status),
    path('api/login',api.api_login),
    path('aboutus',views.aboutus)
]
