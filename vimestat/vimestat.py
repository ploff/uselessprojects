import requests

print('vimeworld session check')
idid = input('enter nickname: ')

# getting id of nickname
nicklink = requests.get("https://api.vimeworld.com/user/name/" + idid)
nickjson = nicklink.json()[0]
nickid = str(nickjson["id"])

# getting session of id
sessionlink = requests.get("https://api.vimeworld.ru/user/session/" + nickid)
session = sessionlink.json()[0]

if session["online"]["value"] == True:
    booleanstatus = 'Да'
elif session["online"]["value"] == False:
    booleanstatus = 'Нет'

# main info
print('\nник:', session["username"])
print('онлайн?:', booleanstatus)
print('статус:', session["online"]["message"])
print('\nуровень:', session["level"])
print('ранг:', session["rank"])
print('играл всего:', session["playedSeconds"], 'миллисекунд')
print('последний онлайн:', session["lastSeen"], 'unix millis')

# guild info
if session["guild"] != None:
    print('\nид гильдии:',session["guild"]["id"])
    print('название гильдии:',session["guild"]["name"])
    print('тэг:',session["guild"]["tag"])
    print('цвет тэга:',session["guild"]["color"])
    print('уровень:',session["guild"]["tag"])
    print('процент уровня:',session["guild"]["tag"])
    if session["guild"]["avatar_url"] != None:
        print('url аватара:',session["guild"]["avatar_url"])
    else:
        print('у гильдии нет аватара')
else:
    print('\n',session["username"], 'не состоит в гильдии')
