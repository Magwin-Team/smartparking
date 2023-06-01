from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from . import models
import requests
import json
import uuid
from datetime import datetime,timedelta

def api_get_parkings(request):
    location = raw_body_convert(request.body)
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
    url = 'https://apimapsmartparking.iran.liara.run?latitude='+str(location['lat'])+'&longitude='+str(location['lon'])

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payloads)

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
    return JsonResponse({"data":parkings_e})


def valid_user(username,password):
    user = models.User.objects.filter(username=username,password=password)
    if user.count() == 0:
        return False
    return True


def api_infouser(request):
    data = raw_body_convert(request.body)
    username = data['username']
    password = data['password']
    user = {}
    if valid_user(username,password) == True:
        user = models.User.objects.filter(username=username,password=password).values()[0]
    return JsonResponse(user)


def api_historyuser(request):
    data = raw_body_convert(request.body)
    username = data['username']
    password = data['password']
    data_list = []
    if valid_user(username,password) == True:
        user_id = models.User.objects.filter(username=username)[0].id
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
    return JsonResponse({"data":data_list})

def api_change_password(request):
    data = raw_body_convert(request.body)
    if valid_user(data['username'],data['password']) == True:
        user = models.User.objects.filter(username=data['username'],password=data['password'])[0]
        user.password = data["new-password"]
        user.save()
        return JsonResponse({"status" : True})
    return JsonResponse({"status" : False})

def api_get_login_qrcode(request):
    data = raw_body_convert(request.body)
    username = data['username']
    password = data['password']
    id = data['parking-id']
    imglink = ''
    _status = 'not'
    if valid_user(username,password) == True:
        user_id = models.User.objects.filter(username=username).values()[0]['id']
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
    return JsonResponse({'status' : _status,'qrcode-link':imglink})

def api_remove_login_qrcode(request):
    user = raw_body_convert(request.body)
    if valid_user(user['username'],user['password']) == True:
        user_id = models.User.objects.filter(username=user['username']).values()[0]['id']
        login_data = models.Logins.objects.filter(user_id=user_id,status=False)[0]
        login_data.delete()
        return JsonResponse({'status' : True})
    return JsonResponse({'status' : False})

def api_get_exit_parking_qrcode(request):
    data = raw_body_convert(request.body)
    username = data['username']
    password = data['password']
    id = data['parking-id']
    imglink = ''
    status = 'not'
    if valid_user(username,password) == True:
        user_id = models.User.objects.filter(username=username).values()[0]['id']
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
    return JsonResponse({'status' : status,'qrcode-link':imglink})

def api_get_user_status(request):
    user = raw_body_convert(request.body)
    username = user['username']
    password = user['password']
    response = {
        'valid' : 'not ok'
    }
    if valid_user(username,password) == True:
        user = models.User.objects.filter(username=username)[0]
        login_count = models.Logins.objects.filter(user_id=user.id,status=True).count() - models.Exits.objects.filter(user_id=user.id,status=True).count()
        status = ''
        parking_id = -1
        if login_count == 1:
            parking_id = models.Logins.objects.filter(user_id=user.id,status=True).last().parking_id
            status = models.ParkingsLists.objects.filter(id=parking_id)[0].parking_name_pr
        response = {
            'name' : user.firstname + ' ' + user.lastname,
            'car_1' : user.car_tag_1,
            'car_2' : user.car_tag_2,
            'car_3' : user.car_tag_3,
            'car_4' : user.car_tag_4,
            'status' : status,
            'parking-id' : parking_id
        }
    return JsonResponse(response)


def api_login(request):
    data = raw_body_convert(request.body)
    username = data['username']
    password = data['password']
    finder = models.User.objects.filter(username=username,password=password).count()
    if finder == 1:
        return JsonResponse({'status' : True})
    else:
        return JsonResponse({'status' : False})


def raw_body_convert(data):
    return json.loads(data.decode('utf-8'))