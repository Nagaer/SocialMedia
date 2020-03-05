import datetime
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import progressbar

import vk_api


def get_friends(api, user_id):
    return api.friends.get(user_id=user_id)['items']


def get_members(api, group_id):
    q = api.groups.getMembers(group_id=group_id)
    res = q['items']
    length = q['count']
    if length <= 1000:
        return res
    else:
        k = 1000
        while k < length:
            res += api.groups.getMembers(group_id=group_id, offset=k)['items']
            k += 1000
        return res


def make_adjacency(api, user_id):
    dic = {}
    friend_ids = get_friends(api, user_id)
    bar = progressbar.ProgressBar(maxval=len(friend_ids)).start()
    for j, friend in enumerate(friend_ids):
        try:
            ids = get_friends(api, friend)
        except vk_api.exceptions.ApiError:
            continue
        else:
            dic[friend] = {i for i in ids if i in friend_ids}
        bar.update(j)
    bar.finish()
    print("Создание словаря закончено")
    return dic, friend_ids


def changeKeys(d, a):
    for i, v in enumerate(a):
        try:
            d[i]
        except KeyError:
            continue
        else:
            d[v] = d.pop(i)
    return d


def get_cities(d):
    locations = vk.database.getCitiesById(city_ids=list(d.keys()))
    locs = dict()
    for loc in locations:
        locs.update({loc['id']: loc['title']})

    for k, v in locs.items():
        if d[k]:
            d[v] = d.pop(k)

    return d

session = vk_api.VkApi(input("Введите свой номер телефона или почту: "), input("Введите пароль: "))
session.auth()
vk = session.get_api()

choice = input("Выберите тип источника данных (1 - группа, 2 - друзья человека): ")
source_id = input("Введите id источника данных: ")
if choice == 1:
    ids_list = get_members(vk, source_id)
elif choice == 2:
    ids_list = get_friends(vk, source_id)
else:
    print("Неверный выбор. Перезапустите программу. ")
    exit()

res = {'sex': [], 'rel': [], 'dat': [], 'loc': []}
data = dict()
curr_year = datetime.datetime.now().year

bar = progressbar.ProgressBar(maxval=len(ids_list)).start()
for i, userid in enumerate(ids_list):
    data[userid] = vk.users.get(user_ids=userid, fields=['sex', 'bdate', 'city', 'relation'])
    q = data[userid][0]

    res['sex'].append(int(q.get('sex', 0)))
    res['rel'].append(int(q.get('relation', 0)))
    z = q.get('bdate', 0)
    if z == 0:  #Не указана вообще
        res['dat'].append(z)
    elif int(z.split('.')[-1]) > 31:  #Указан год
        y = z.split('.')
        res['dat'].append(curr_year-int(y[-1]))
    else:  #Год не указан
        res['dat'].append(0)
    #  res['dat'].append(curr_year-parser.parse(q.get('bdate', '1.'+y)).year)
    w = q.get('city', 0)
    if type(w) is int:
        res['loc'].append(w)
    else:
        res['loc'].append(w.get('id', 0))
    bar.update(i)
bar.finish()
print("Сбор статистики окончен")

d1 = dict(Counter(res['sex']))
d2 = dict(Counter(res['rel']))
d3 = dict(Counter(res['dat']))
d4 = dict(Counter(res['loc']))

d1 = changeKeys(d1, ['не указано', 'жен', 'муж'])
d2 = changeKeys(d2, ['не указано',
                     'не женат/не замужем',
                     'есть друг/есть подруга',
                     'помолвлен/помолевлена',
                     'женат/замужем',
                     'все сложно',
                     'в активном поиске',
                     'влюблен',
                     'в гражданском браке'])
d3 = changeKeys(dict((k, v) for (k, v) in d3.items() if k < 100), ['не указано'])
d4 = changeKeys(dict((k, v) for (k, v) in get_cities(d4).items() if v > 1), ['не указано'])

df = pd.DataFrame.from_dict({'Пол': d1, 'Семейное положение': d2, 'Возраст': d3, 'Место проживания': d4})

df.plot.pie(subplots=True, legend=True, layout=(2, 2), figsize=(30, 30), startangle=-45)
plt.tight_layout()
plt.show()

