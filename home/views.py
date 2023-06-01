from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.template import loader
from . import models
import re
from DateTimePersian import DateTimePersian
from persian_tools import national_id,phone_number
from datetime import datetime,timedelta
from persiantools.jdatetime import JalaliDate
import requests
import json
import uuid

# Create your views here.

#This is Main Link Response
def home(request):
    template = loader.get_template('home_page.html')
    context = {
        "login" : {
            'valid' : 'dont-show'
        },
        "parking" : range(2),
        "index" : 0,
        "isLogined" : "false",
        "inparking" : ""
    }
    # Check request for Login or Home User Page Or login Page
    if request.method == 'GET':
        valid = 'dont-show'
        #Check Cooki Valid For Auto Login
        if bool(request.COOKIES):
            user = request.COOKIES
            users = models.User.objects.filter(username=user['username'],password = user['password']).values()
            users_p = models.ParkingManagers.objects.filter(username=user['username'],password = user['password']).values()
            # Check Account Type
            if users.count() == 1:
                context = {
                        "login" : {
                            'valid' : 'dont-show'
                        },
                        "parking" : range(0),
                        "index" : 0,
                        "user" : models.User.objects.filter(username=user['username'],password = user['password']).values()[0],
                        "isLogined" : "true",
                        "inparking" : ""
                    }
                template = loader.get_template('dashbordcontroller.html')
                if(request.GET):
                    parkings_list = models.ParkingsLists.objects.all().values()
                    payloads = []
                    for parking_data in parkings_list:
                        payloads.append(
                            {
                                "id" : parking_data['id'],
                                "latitude" : float(parking_data['parking_location'].split(' ')[0]),
                                "longitude" : float(parking_data['parking_location'].split(' ')[1])
                            }
                        )
                    payloads = json.dumps(payloads)
                    url = 'https://apimapsmartparking.iran.liara.run/?latitude='+request.GET['la']+'&longitude='+request.GET['lo']

                    headers = {
                        'Content-Type': 'application/json'
                    }

                    response = requests.request("GET", url, headers=headers, data=payloads)
                    print(response,)
                    parkings_e = []
                    for i in response.json():
                        get_db = models.ParkingsLists.objects.filter(id=i['id']).values()[0]
                        logins = models.Logins.objects.filter(parking_id = i['id'],status=True).values()
                        exits = models.Exits.objects.filter(parking_id = i['id'],status=True).values()
                        capacity_full = logins.count() - exits.count()

                        parkings_e.append(
                            {
                                'distanse' : "%.1f" % i['distance'],
                                'parking_name_fa' : get_db['parking_name_pr'],
                                'parking_name' : get_db['parking_name'],
                                'parking_like' : get_db['parking_like'],
                                'parking_image' : get_db['parking_image'],
                                'capacity_full' : models.ParkingManagers.objects.filter(parking_id=i['id']).values()[0]['parking_capacity'] - capacity_full,
                                'capacity' : models.ParkingManagers.objects.filter(parking_id=i['id']).values()[0]['parking_capacity'],
                                'router_link' : get_db['parking_routing_link'],
                                'parking_id' : get_db['id']
                            }
                        )
                    in_parking = ''
                    parking_id = ''
                    get_login_user = models.Logins.objects.filter(user_id = users[0]['id'],status=True).values()
                    for i in get_login_user:
                        get_exit_user = models.Exits.objects.filter(login_id=i['id'],status=True).values()
                        if get_exit_user.count() == 0:
                            print(i)
                            in_parking = models.ParkingsLists.objects.filter(id=i['parking_id']).values()[0]['parking_name_pr']
                            parking_id = i['parking_id']
                    
                    context = {
                        "login" : {
                            'valid' : 'dont-show'
                        },
                        "parking" : parkings_e,
                        "index" : 0,
                        "user" : models.User.objects.filter(username=user['username'],password = user['password']).values()[0],
                        "isLogined" : "true",
                        "inparking" : in_parking,
                        "parking_id" : parking_id
                    }
                    
                return HttpResponse(template.render(context))
                
            elif users_p.count() == 1:
                template = loader.get_template('dashbordcontrollerparking.html')
                logins = models.Logins.objects.filter(parking_id = users_p[0]['parking_id'],status = True).values()
                exits = models.Exits.objects.filter(parking_id = users_p[0]['parking_id'],status=True).values()
                capacity_full = logins.count() - exits.count()
                print(datetime.now().date())
                income = 0
                # income mohasebe
                for i in exits:
                    if i['exit_date'] == datetime.now().date():
                        income = i['price']
                # income nemodar
                date_list = ['']
                income_list = [0]
                exit_list = [0]
                date_get = datetime.now() - timedelta(days=6)
                parking_id = users_p[0]['parking_id']
                for i in range(7):
                    get_exits = models.Exits.objects.filter(status = True,parking_id = parking_id,exit_date = date_get.date())
                    exit_list.append(get_exits.count())
                    sum_income = 0
                    for inco in get_exits:
                        sum_income = inco.price
                    income_list.append(sum_income)
                    date_list.append(
                        
                        str(JalaliDate(date_get)).split(' ')[0]
                    )
                    date_get = date_get + timedelta(days=1)
                    print(date_get)
                context = {
                    "user" : users_p[0],
                    "index" : 0,
                    "date" : ' ' + DateTimePersian().today(Type=str).split(' ')[2] +' '+ DateTimePersian().today(Type=str).split(' ')[1] +' '+ DateTimePersian().today(Type=str).split(' ')[0] + ' ',
                    "zarfiat" : {
                        "capacity" : users_p[0]['parking_capacity'],
                        "capacity_full" : users_p[0]['parking_capacity'] - capacity_full 
                    },
                    "income" : income,
                    "date_list" : json.dumps(date_list),
                    "income_list" : json.dumps(income_list),
                    "exit_list" : json.dumps(exit_list)
                }
                return HttpResponse(template.render(context))
        # Login Check  request
        try:
            user = request.GET
            users = models.User.objects.filter(username=user['username'],password = user['password']).values()
            if users.count() == 1:
                context = {
                    "login" : {
                        'valid' : 'dont-show'
                    },
                    "parking" : range(10),
                    "index" : 0,
                    "isLogined" : "true"
                }
                response = HttpResponseRedirect(redirect_to='/')
                response.set_cookie('username',user['username'])
                response.set_cookie('password',user['password'])
                return response
            else:
                context = {
                    "login" : {
                        'valid' : ''
                    },
                    "parking" : range(2),
                    "isLogined" : "false"
                }
        except:
            return HttpResponse(template.render(context))
        return HttpResponse(template.render(context))

# This View For Login Parking Manager 
def loginforparking(request):
    template = loader.get_template('loginforparking.html')
    context = {
        "login" : {
            'valid' : ''
        }
    }
    # Response The Page
    if request.method == 'GET':
        template = loader.get_template('loginforparking.html')
        context = {
            "login" : {
                'valid' : 'dont-show'
            }
        }
        return HttpResponse(template.render(context),)
    # Check Input Data And redirect to home Page And Set cookie
    elif request.method == 'POST':
        data = request.POST
        user = models.ParkingManagers.objects.filter(username = data['username'],password = data['password'],tel_number=data['phone'],national_code=data['ncode']).values()
        if len(user) == 1:
            response = HttpResponseRedirect('/')
            response.set_cookie('username',data['username'])
            response.set_cookie('password',data['password'])
            response.set_cookie('ncode',data['ncode'])
            response.set_cookie('number',data['phone'])
            return response
    return HttpResponse(template.render(context))

#User Account Create
def signinuser(request):
    if validcookie(request) == False:
        template = loader.get_template("signinuser.html")
        context = {
            "login":{
                "valid" : "dont-show"
            }
        }
        valid = "dont-show"
        # Check input valid for Create new Account
        if request.POST:
            user = request.POST
            if len(re.findall('[0-9]+', user['name'])) > 0 or len(re.findall('[0-9]+', user['lastname'])) > 0:
                valid = ""
                print("name")
            if models.User.objects.filter(username=user['username']).values().count() > 0 or user['username'].find(" ") > -1:
                valid = ""
                print("username")
            if user['password'] != user['repassword'] or user['password'] == "":
                valid = ""
                print("password")
            if national_id.validate(user['ncode']) == False or models.User.objects.filter(national_code=user['ncode']).values().count() > 0:
                valid = ""
                print(user['ncode'])
                print(national_id.validate(user['ncode']))
            if phone_number.validate(user['number']) == False or models.User.objects.filter(tel_number=user['number']).values().count() > 0:
                valid = ""
                print("phone")
            if models.User.objects.filter(car_tag_1=user['carPlateSection1']).values().count() > 0 and models.User.objects.filter(car_tag_2=user['hpelak']).values().count() > 0 and models.User.objects.filter(car_tag_3=user['carPlateSection3']).count()>0 and models.User.objects.filter(car_tag_4=user['carPlateSection4']).values().count()>0:
                valid = ""
                print('car_tag')
            if valid != "":
                response = HttpResponseRedirect(redirect_to='/')
                response.set_cookie('username',user['username'])
                response.set_cookie('password',user['password'])
                user_create = models.User(
                    username = user['username'],
                    password = user['password'],
                    firstname = user['name'],
                    lastname = user['lastname'],
                    national_code = user['ncode'],
                    tel_number = user['number'],
                    email = user['email'],
                    date_of_birth = user['birth'],
                    car_tag_1 = user['carPlateSection1'],
                    car_tag_2 = user['hpelak'],
                    car_tag_3 = user['carPlateSection3'],
                    car_tag_4 = user['carPlateSection4'],
                    status=False
                )
                user_create.save()
                return response
            context = {
                "login":{
                    "valid" : ""
                }
            }
        return HttpResponse(template.render(context))

# Create Parking Manager Account
def signinparking(request):
    if bool(request.COOKIES) == False:
        template = loader.get_template("signinparking.html")
        context = {
            "login":{
                "valid" : "dont-show",
                "isok" : "dont-show"
            }
        }
        if request.method == 'GET':
            return HttpResponse(template.render(context))
        elif request.method == 'POST':
            valid = 'dont-show'
            user = request.POST
            if len(re.findall('[0-9]+', user['firstname'])) > 0 or len(re.findall('[0-9]+', user['lastname'])) > 0:
                    valid = ""
            if bool(models.ParkingManagers.objects.filter(username=user['username']).values()) or user['username'].find(" ") > -1:
                valid = ""
            if user['password'] != user['repassword'] or user['password'] == "":
                valid = ""
            if national_id.validate(user['ncode']) == False or bool(models.ParkingManagers.objects.filter(national_code=user['ncode']).values()):
                valid = ""
            if phone_number.validate(user['phone']) == False or bool(models.ParkingManagers.objects.filter(tel_number=user['phone']).values()):
                valid = ""
            if valid != "":
                context = {
                    "login":{
                        "valid" : "dont-show",
                        "isok" : ""
                    }
                }
                response = HttpResponse(template.render(context))
                user_create = models.Requests(
                    username = user['username'],
                    password = user['password'],
                    firstname = user['firstname'],
                    lastname = user['lastname'],
                    national_code = user['ncode'],
                    tel_number = user['phone'],
                    email = user['email'],
                    date_of_birth = user['birth'],
                    photo_of_business_license = user['image-business-license'],
                    photo_of_national_code = user['image-ncode'],
                    bank_information = user['cart-id'],
                    tax_returns = user['tax-return'],
                    parking_name = user['name-parking'],
                    parking_name_pr = user['name-pr-parking'],
                    parking_location = user['parking-location'],
                    parking_tariff = user['triff-parking'],
                    parking_capacity = user['capacity-parking'],
                )
                user_create.save()
                return response
            else:
                context = {
                    "login":{
                        "valid" : "",
                        "isok" : "dont-show"
                    }
                }
                response = HttpResponse(template.render(context))
                return response
# Check Cookie set in valid Data for parking Manager
def validcookie_parking_manager(request):
    if bool(request.COOKIES):
        user = request.COOKIES
        users = models.ParkingManagers.objects.filter(username=user['username'],password = user['password'],tel_number = user['number'] , national_code = user['ncode']).values()
        if users.count() == 1:
            return True
    return False
# Check Cookie set in valid Data for Public User
def validcookie(request):
    if bool(request.COOKIES):
        user = request.COOKIES
        users = models.User.objects.filter(username=user['username'],password = user['password']).values()
        if users.count() == 1:
            return True
    return False

# This view For Response History Page 
def historyuser(request):
    if validcookie(request):
        user = request.COOKIES
        user_id = models.User.objects.filter(username=user['username'])[0].id
        data_list = []
        exits_historys = models.Exits.objects.filter(user_id = user_id,status=True)
        for exits_data in exits_historys:
            data_list.append(
                {
                    "parking_name" : models.ParkingsLists.objects.get(id=exits_data.parking_id).parking_name_pr,
                    "login_time" : str(models.Logins.objects.get(id=exits_data.login_id).login_time).split(':')[0]+':'+str(models.Logins.objects.get(id=exits_data.login_id).login_time).split(':')[1],
                    "exit_time" : str(exits_data.exit_time).split(':')[0]+':'+str(exits_data.exit_time).split(':')[1],
                    "price" : exits_data.price,
                    "parking_img" : models.ParkingsLists.objects.get(id=exits_data.parking_id).parking_image
                }
            )
        in_parking = ''
        parking_id = ''
        get_login_user = models.Logins.objects.filter(user_id = user_id,status=True).values()
        for i in get_login_user:
            get_exit_user = models.Exits.objects.filter(login_id=i['id'],status=True).values()
            if get_exit_user.count() == 0:
                in_parking = models.ParkingsLists.objects.filter(id=i['parking_id']).values()[0]['parking_name_pr']
                parking_id = i['parking_id']
        context = {
            "parkings" : data_list,
            "index" : 1,
            "user" : models.User.objects.filter(username=user['username'],password = user['password']).values()[0],
            "parking_id" : parking_id,
            "inparking" : in_parking
        }
        template = loader.get_template('dashbordcontroller.html')
        return HttpResponse(template.render(context))

# Response The User Inf Page
def infouser(request):
    if validcookie(request):
        user_l = request.COOKIES
        user = models.User.objects.filter(username=user_l['username'],password=user_l['password']).values()[0]
        user_id = models.User.objects.filter(username=user['username'])[0].id
        in_parking = ''
        parking_id = ''
        get_login_user = models.Logins.objects.filter(user_id = user_id,status=True).values()
        for i in get_login_user:
            get_exit_user = models.Exits.objects.filter(login_id=i['id'],status=True).values()
            if get_exit_user.count() == 0:
                in_parking = models.ParkingsLists.objects.filter(id=i['parking_id']).values()[0]['parking_name_pr']
                parking_id = i['parking_id']
        context = {
            'user':user,
            'index' : 3,
            "parking_id" : parking_id,
            "inparking" : in_parking
        }
        template = loader.get_template("dashbordcontroller.html")
        return HttpResponse(template.render(context))
#Chane User Password View
def changepassworduser(request):
    if validcookie(request):
        template = loader.get_template("dashbordcontroller.html")
        user_id = models.User.objects.filter(username=request.COOKIES['username'])[0].id
        in_parking = ''
        parking_id = ''
        get_login_user = models.Logins.objects.filter(user_id = user_id,status=True).values()
        for i in get_login_user:
            get_exit_user = models.Exits.objects.filter(login_id=i['id'],status=True).values()
            if get_exit_user.count() == 0:
                in_parking = models.ParkingsLists.objects.filter(id=i['parking_id']).values()[0]['parking_name_pr']
                parking_id = i['parking_id']
        # Response the Page
        if request.method == 'GET':
            user_l = request.COOKIES
            user = models.User.objects.filter(username=user_l['username'],password=user_l['password']).values()[0]
            context = {
                'user':user,
                'valid' : 'dont-show',
                'index' : 4,
                "parking_id" : parking_id,
                "inparking" : in_parking
            }
            
            return HttpResponse(template.render(context))
        # Check Valid Data
        if request.method == 'POST':
            valid = 'dont-show'
            passwords = request.POST
            user_l = request.COOKIES
            user = models.User.objects.filter(username=user_l['username'],password=user_l['password'])[0]
            if passwords['lpassword'] != user.password:
                valid = ''
            if passwords['npassword'] != passwords['repassword'] or passwords['npassword'] == "":
                valid = ''
            if valid != "":
                user.password = passwords['npassword']
                user.save()
            context = {
                'user':user,
                'valid' : valid,
                'index' : 4,
                "parking_id" : parking_id,
                "inparking" : in_parking
            }
            response = HttpResponse(template.render(context))
            response.set_cookie('password',user.password)
            return response
#Clear Cookie And Redirect to Home Page
def logout(request):
    response = HttpResponseRedirect('/')
    response.delete_cookie('username')
    response.delete_cookie('password')
    try:
        response.delete_cookie('ncode')
        response.delete_cookie('number')
    except:
        pass
    return response
#Change Password For Parking Manager
def changepassworduser_parking_manager(request):

    if validcookie_parking_manager(request):
        user_l = request.COOKIES
        user = models.ParkingManagers.objects.filter(username=user_l['username'],password=user_l['password']).values()[0]
        template = loader.get_template("dashbordcontrollerparking.html")
        # Response Change Password Page
        if request.method == 'GET':
            context = {
                'user':user,
                'valid' : 'dont-show',
                'index' : 4
            }
            return HttpResponse(template.render(context))
        # Check and valid Input Data
        if request.method == 'POST':
            valid = 'dont-show'
            passwords = request.POST
            user_l = request.COOKIES
            user = models.ParkingManagers.objects.filter(username=user_l['username'],password=user_l['password'])[0]
            if passwords['lpassword'] != user.password:
                valid = ''
            if passwords['npassword'] != passwords['repassword'] or passwords['npassword'] == "":
                valid = ''
            if valid != "":
                user.password = passwords['npassword']
                user.save()
            context = {
                'user':user,
                'valid' : valid,
                'index' : 4
            }
            response = HttpResponse(template.render(context))
            response.set_cookie('password',user.password)
            return response    

#User Info for parking manager
def info_manager(request):
    if validcookie_parking_manager(request):
        user_l = request.COOKIES
        user = models.ParkingManagers.objects.filter(username=user_l['username'],password=user_l['password']).values()[0]
        parking = models.ParkingsLists.objects.get(id=user['parking_id'])
        context = {
            'user':user,
            'index' : 3,
            'parking' : parking
        }
        template = loader.get_template("dashbordcontrollerparking.html")
        return HttpResponse(template.render(context))

# Get All Car Traffic in Parking and response the car traffic page
def car_traffics(request):
    if validcookie_parking_manager(request):
        user_l = request.COOKIES
        user = models.ParkingManagers.objects.filter(username=user_l['username'],password=user_l['password']).values()[0]
        getlogindata = models.Logins.objects.filter(parking_id=user['parking_id'],status = True).values()
        cars = []
        for _user in getlogindata:
            _user['login_time'] = str(_user['login_time']).split(':')[0] + ':' + str(_user['login_time']).split(':')[1]
            car = models.User.objects.filter(id=_user['user_id']).values()[0]
            exit_list = models.Exits.objects.filter(parking_id=user['parking_id'],login_id = _user['id'],status = True).values()
            cars.append(
                {
                    'logindata':_user,
                    'user' : car,
                    'exit_time' : '' if exit_list.count() < 1 else str(exit_list[0]['exit_time']).split(':')[0] + ':'+ str(exit_list[0]['exit_time']).split(':')[1],
                    'exit' : 'ok' if exit_list.count() < 1 else ''
                }
            )
        print(getlogindata)
        context = {
            'index' : 1,
            'cars' : cars,
            'user' : user
        }
        template = loader.get_template("dashbordcontrollerparking.html")
        return HttpResponse(template.render(context))

# Get All Car in Parking And response Car in Parking page
def car_in_parking(request):
    if validcookie_parking_manager(request):
        user_l = request.COOKIES
        user = models.ParkingManagers.objects.filter(username=user_l['username'],password=user_l['password']).values()[0]
        getlogindata = models.Logins.objects.filter(parking_id=user['parking_id'],status=True).values()
        cars = []
        for _user in getlogindata:
            _user['login_time'] = str(_user['login_time']).split(':')[0] + ':' + str(_user['login_time']).split(':')[1]
            car = models.User.objects.filter(id=_user['user_id']).values()[0]
            exit_list = models.Exits.objects.filter(parking_id=user['parking_id'],user_id=car['id'],status = True,login_id=_user['id']).values()
            if(exit_list.count() < 1):
                cars.append(
                    {
                        'logindata':_user,
                        'user' : car,
                    }
                )
        context = {
            'index' : 2,
            'cars' : cars,
            'user' : user
        }
        template = loader.get_template("dashbordcontrollerparking.html")
        return HttpResponse(template.render(context))
# This View For Login To Parking And Generate QRCode
def logintoparking(request,id):
    user_id = models.User.objects.filter(username=request.COOKIES['username']).values()[0]['id']
    login_user = models.Logins.objects.filter(user_id = user_id).values()
    exit_user = models.Exits.objects.filter(user_id = user_id,status=True).values()
    imglink = ''
    _status = 'ok'
    if exit_user.count() == login_user.count():
        qrcode = str(uuid.uuid4())
        imglink = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+qrcode
        set_new_login = models.Logins(
            user_id = user_id,
            parking_id = id,
            login_date = datetime.now().date(),
            login_time = datetime.now().time(),
            qr_code = qrcode,
            status = False
        )
        set_new_login.save()
    else:
        login_user = models.Logins.objects.filter(user_id = user_id,status = False,parking_id = id).values()
        if login_user.count() == 1:
            imglink = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+login_user[0]['qr_code']
        else:
            _status = 'not'
    template = loader.get_template('getqrcode.html')
    context = {
        "status" : _status,
        "qrcode" : imglink
    }
    return HttpResponse(template.render(context))

# Delete Login Request 
def removeloginqr(request):
    user_id = models.User.objects.filter(username=request.COOKIES['username']).values()[0]['id']
    login_data = models.Logins.objects.filter(user_id=user_id,status=False)[0]
    login_data.delete()
    return HttpResponseRedirect('/')
# Generate And set valid for Exit Qrcode
def addexit(request,id):
    template = loader.get_template('exitqrcode.html')
    user_id = models.User.objects.filter(username=request.COOKIES['username']).values()[0]['id']
    logins = models.Logins.objects.filter(user_id = user_id,status = True,parking_id = id).values()
    exits = models.Exits.objects.filter(user_id = user_id,parking_id = id).values()
    status = 'ok'
    imglink = ''
    if logins.count() - exits.count() == 1:
        qrcode = str(uuid.uuid4())
        login_id = models.Logins.objects.filter(user_id = user_id,status = True,parking_id = id).last()
        parking_data = models.ParkingsLists.objects.get(id=id)
        date_login = login_id.login_date
        time_login = login_id.login_time
        length_stay = datetime.now() - datetime.combine(date_login,time_login)
        length_stay = length_stay.seconds
        imglink = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+qrcode
        add_exit = models.Exits(
            user_id = user_id,
            parking_id = id,
            login_id = login_id.id,
            qr_code = qrcode,
            exit_date = datetime.now().date(),
            exit_time = datetime.now().time(),
            length_of_stay = length_stay,
            price = (parking_data.parking_tariff / 60) * length_stay,
            status = False
        )
        add_exit.save()
    else:
        exits = models.Exits.objects.filter(user_id = user_id,parking_id = id,status = False)
        if exits.count() == 1:
            if ((datetime.now() -  datetime.combine(exits[0].exit_date,exits[0].exit_time)).seconds // 60) > 10 :
                exits[0].status = True
                exits[0].save()
                new_login = models.Logins(
                    user_id = user_id,
                    parking_id = id,
                    login_date = exits[0].exit_date,
                    login_time = exits[0].exit_time,
                    qr_code = '',
                    status = True
                )
                new_login.save()
                qrcode = str(uuid.uuid4())
                login_id = models.Logins.objects.filter(user_id = user_id,status = True,parking_id = id).last()
                parking_data = models.ParkingsLists.objects.get(id=id)
                date_login = login_id.login_date
                time_login = login_id.login_time
                length_stay = datetime.now() - datetime.combine(date_login,time_login)
                length_stay = length_stay.seconds
                imglink = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+qrcode
                add_exit = models.Exits(
                    user_id = user_id,
                    parking_id = id,
                    login_id = login_id.id,
                    qr_code = qrcode,
                    exit_date = datetime.now().date(),
                    exit_time = datetime.now().time(),
                    length_of_stay = length_stay,
                    price = (parking_data.parking_tariff / 60) * length_stay,
                    status = False
                )
                add_exit.save()
            else:
                imglink = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+exits[0].qr_code
        else:
            status = ''

    context = {
        "status" : status,
        "qrcode" : imglink
    }
    return HttpResponse(template.render(context))

# This Api for Accepet qrcodes for login or exits and use in parking manager System
def api_accept_qrcode(request):
    data = raw_body_convert(request.body)
    parking_valid = models.ParkingsLists.objects.get(id=data['parking_id'])
    if parking_valid.atue_code == data['atue_code']:
        logins_false = models.Logins.objects.filter(qr_code = data['qr_code'],status = False)
        exits_false = models.Exits.objects.filter(qr_code = data['qr_code'],status=False)
        if logins_false.count() == 1:
            logins_false = logins_false[0]
            logins_false.status = True
            logins_false.save()
            return JsonResponse(
                {
                    "valid":True,
                    "atue":True
                }
            )
        elif exits_false.count() == 1:
            exits_false = exits_false[0]
            exits_false.status = True
            exits_false.save()
            return JsonResponse(
                {
                    "valid":True,
                    "atue":True
                }
            )
        return JsonResponse(
            {
                "valid":False,
                "atue":True
            }
        )
    return JsonResponse({'valid':False,'atue':False})



def aboutus(request):
    template = loader.get_template('about.html')
    return HttpResponse(template.render())
#Decode body Request
def raw_body_convert(data):
    return json.loads(data.decode('utf-8'))

