# from pyowm import OWM
# import json
# import pprint
# owm = OWM('0f8b321c68552dff33eeb5625f971c39')
# mgr = owm.weather_manager()
# one_call = mgr.one_call(lat=11.274562, lon=77.582603)
# current_data = json.dumps(one_call.current.__dict__)
# def status():
#     return one_call.current.__dict__["status"],one_call.current.__dict__["weather_code"]
# print(current_data)
# print(type(status()))
# #
# # print(one_call.current.humidity, one_call.current.temperature('celsius')['temp']) # Eg.: 81


def status():
    return "Drizzle", 300