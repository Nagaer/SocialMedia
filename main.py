import datetime
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import progressbar
import vk_api
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
from ctypes import *


class VKStatistic:
    def __init__(self, api, choice, source_id, dict_points):
        self.api = api
        self.choice = choice
        self.source_id = source_id
        self.dict_points = dict_points

    def get_friends(self, user_id):
        return self.api.friends.get(user_id=user_id)['items']

    def get_members(self, group_id):
        q = self.api.groups.getMembers(group_id=group_id)
        res = q['items']
        length = q['count']
        if length <= 1000:
            return res
        else:
            k = 1000
            while k < length:
                res += self.api.groups.getMembers(group_id=group_id, offset=k)['items']
                k += 1000
            return res

    def change_keys(self, d, a):
        for i, v in enumerate(a):
            try:
                d[i]
            except KeyError:
                continue
            else:
                d[v] = d.pop(i)
        return d

    def get_cities(self, d):
        locations = self.api.database.getCitiesById(city_ids=list(d.keys()))
        locs = dict()
        for loc in locations:
            locs.update({loc['id']: loc['title']})

        for k, v in locs.items():
            if d[k]:
                d[v] = d.pop(k)

        return d

    def get_and_output_data(self):
        if self.choice == 1:  #  Выбор источника id
            ids_list = self.get_members(self.source_id)
        elif self.choice == 2:
            ids_list = self.get_friends(self.source_id)
        else:
            print("Неверный выбор. Перезапустите программу. ")
            exit()

        #  res = {'sex': [], 'rel': [], 'dat': [], 'loc': []}
        res = dict()
        for x in self.dict_points: #  Заполнение словаря кодами в зависимости от выбора пользователя
            if self.dict_points[x][0]:
                res[x] = []
        data = dict()
        curr_year = datetime.datetime.now().year

        bar = progressbar.ProgressBar(maxval=len(ids_list)).start()
        for i, userid in enumerate(ids_list):
            data[userid] = self.api.users.get(user_ids=userid, fields=list(res.keys()))
            q = data[userid][0]
            for x in res:
                if x == 'bdate':
                    z = q.get(x, 0)
                    if z == 0:  # Не указана вообще
                        res[x].append(z)
                    elif int(z.split('.')[-1]) > 31:  # Указан год
                        y = z.split('.')
                        res[x].append(curr_year - int(y[-1]))
                    else:  # Год не указан
                        res[x].append(0)
                elif x == 'city':
                    w = q.get(x, 0)
                    if type(w) is int:
                        res[x].append(w)
                    else:
                        res[x].append(w.get('id', 0))
                else: #sex and relation
                    res[x].append(int(q.get(x, 0)))
            bar.update(i)
        bar.finish()
        print("Сбор статистики окончен")

        dict_result = dict()
        for x in res:  #Заполняем по ключам итогового отображения словарём с посчитанным числом каждого из значений
            dict_result[self.dict_points[x][1]] = dict(Counter(res[x]))

        for x in dict_result:
            if x == 'Пол':
                dict_result[x] = self.change_keys(dict_result[x], ['не указано', 'жен', 'муж'])
            elif x == 'Семейное положение':
                dict_result[x] = self.change_keys(dict_result[x], ['не указано', 'не женат/не замужем',
                                                                   'есть друг/есть подруга', 'помолвлен/помолевлена',
                                                                   'женат/замужем', 'все сложно', 'в активном поиске',
                                                                   'влюблен', 'в гражданском браке'])
            elif x == 'Возраст':
                dict_result[x] = self.change_keys(dict((k, v) for (k, v) in dict_result[x].items() if k < 100),
                                                  ['не указано'])
            elif x == 'Место проживания':
                dict_result[x] = self.change_keys(dict((k, v) for (k, v) in self.get_cities(dict_result[x]).items()
                                                       if v > 1), ['не указано'])

        df = pd.DataFrame.from_dict(dict_result)

        num_size = len(ids_list)/15
        df.plot.pie(subplots=True, legend=True, layout=(2, 2), figsize=(num_size, num_size), startangle=-45)
        plt.tight_layout()
        plt.show()


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QGridLayout()
        self.setLayout(layout)

        self.radiobutton1 = QRadioButton("Подписчики группы")
        self.radiobutton1.setChecked(True)
        self.radiobutton1.choice = "Group"
        layout.addWidget(self.radiobutton1, 0, 0)

        self.radiobutton2 = QRadioButton("Друзья человека")
        self.radiobutton2.choice = "Friends"
        layout.addWidget(self.radiobutton2, 0, 1)

        self.log_output1 = QLabel("Введите id: ")
        layout.addWidget(self.log_output1, 1, 0)

        self.line_edit1 = QLineEdit()
        self.line_edit1.setValidator(QIntValidator())
        layout.addWidget(self.line_edit1, 1, 1)

        self.log_output2 = QLabel("Введите логин и пароль: ")
        layout.addWidget(self.log_output2, 2, 0)

        self.line_edit2 = QLineEdit()
        layout.addWidget(self.line_edit2, 2, 1)
        self.line_edit3 = QLineEdit()
        layout.addWidget(self.line_edit3, 2, 2)

        self.checkbox1 = QCheckBox("Пол")
        self.checkbox1.setChecked(True)
        self.checkbox1.code = "sex"
        layout.addWidget(self.checkbox1, 3, 0)
        self.checkbox2 = QCheckBox("Семейное положение")
        self.checkbox2.setChecked(True)
        self.checkbox2.code = "relation"
        layout.addWidget(self.checkbox2, 3, 1)
        self.checkbox3 = QCheckBox("Возраст")
        self.checkbox3.setChecked(True)
        self.checkbox3.code = "bdate"
        layout.addWidget(self.checkbox3, 3, 2)
        self.checkbox4 = QCheckBox("Место проживания")
        self.checkbox4.setChecked(True)
        self.checkbox4.code = "city"
        layout.addWidget(self.checkbox4, 3, 3)

        self.btn = QPushButton("Расчёт")
        self.btn.clicked.connect(self.show_data)
        layout.addWidget(self.btn, 6, 9)

        self.setGeometry(windll.user32.GetSystemMetrics(0) // 4, windll.user32.GetSystemMetrics(1) // 4,
                         windll.user32.GetSystemMetrics(0) // 6, windll.user32.GetSystemMetrics(1) // 6)
        self.setWindowTitle("Статистика социальных сетей")

    def show_data(self):
        session = vk_api.VkApi(self.line_edit2.text(), self.line_edit3.text())
        session.auth()
        api = session.get_api()
        choice = 0
        if self.radiobutton1.isChecked():
            choice = 1 #  Выбор в качестве источника подписчиков группы
        elif self.radiobutton2.isChecked():
            choice = 2 #  Выбор в качестве источника друзей человека
        dict_p = dict() #  Заполнение словаря по ключам кодов значениями "Собирать ли данные по этому пункту" и "Итоговый текст отображения поля"
        dict_p[self.checkbox1.code] = [True, self.checkbox1.text()] if self.checkbox1.isChecked() else [False, self.checkbox1.text()]
        dict_p[self.checkbox2.code] = [True, self.checkbox2.text()] if self.checkbox2.isChecked() else [False, self.checkbox2.text()]
        dict_p[self.checkbox3.code] = [True, self.checkbox3.text()] if self.checkbox3.isChecked() else [False, self.checkbox3.text()]
        dict_p[self.checkbox4.code] = [True, self.checkbox4.text()] if self.checkbox4.isChecked() else [False, self.checkbox4.text()]

        VKStatistic(api, choice, self.line_edit1.text(), dict_p).get_and_output_data()


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())
