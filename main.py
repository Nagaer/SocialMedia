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
    def __init__(self, api, choice, source_id):
        self.api = api
        self.choice = choice
        self.source_id = source_id

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
        if self.choice == 1:
            ids_list = self.get_members(self.source_id)
        elif self.choice == 2:
            ids_list = self.get_friends(self.source_id)
        else:
            print("Неверный выбор. Перезапустите программу. ")
            exit()

        res = {'sex': [], 'rel': [], 'dat': [], 'loc': []}
        data = dict()
        curr_year = datetime.datetime.now().year

        bar = progressbar.ProgressBar(maxval=len(ids_list)).start()
        for i, userid in enumerate(ids_list):
            data[userid] = self.api.users.get(user_ids=userid, fields=['sex', 'bdate', 'city', 'relation'])
            q = data[userid][0]

            res['sex'].append(int(q.get('sex', 0)))
            res['rel'].append(int(q.get('relation', 0)))
            z = q.get('bdate', 0)
            if z == 0:  # Не указана вообще
                res['dat'].append(z)
            elif int(z.split('.')[-1]) > 31:  # Указан год
                y = z.split('.')
                res['dat'].append(curr_year - int(y[-1]))
            else:  # Год не указан
                res['dat'].append(0)
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

        d1 = self.change_keys(d1, ['не указано', 'жен', 'муж'])
        d2 = self.change_keys(d2, ['не указано', 'не женат/не замужем', 'есть друг/есть подруга',
                                   'помолвлен/помолевлена', 'женат/замужем', 'все сложно', 'в активном поиске',
                                   'влюблен', 'в гражданском браке'])
        d3 = self.change_keys(dict((k, v) for (k, v) in d3.items() if k < 100), ['не указано'])
        d4 = self.change_keys(dict((k, v) for (k, v) in self.get_cities(d4).items() if v > 1), ['не указано'])

        df = pd.DataFrame.from_dict({'Пол': d1, 'Семейное положение': d2, 'Возраст': d3, 'Место проживания': d4})

        df.plot.pie(subplots=True, legend=True, layout=(2, 2), figsize=(30, 30), startangle=-45)
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
        layout.addWidget(self.checkbox1, 3, 0)
        self.checkbox2 = QCheckBox("Семейное положение")
        layout.addWidget(self.checkbox2, 3, 1)
        self.checkbox3 = QCheckBox("Возраст")
        layout.addWidget(self.checkbox3, 3, 2)
        self.checkbox4 = QCheckBox("Место проживания")
        layout.addWidget(self.checkbox4, 3, 3)

        self.btn = QPushButton("Расчёт")
        self.btn.clicked.connect(self.showData)
        layout.addWidget(self.btn, 6, 9)

        self.setGeometry(windll.user32.GetSystemMetrics(0) // 4, windll.user32.GetSystemMetrics(1) // 4,
                         windll.user32.GetSystemMetrics(0) // 6, windll.user32.GetSystemMetrics(1) // 6)
        self.setWindowTitle("Статистика социальных сетей")

    def showData(self):
        session = vk_api.VkApi(self.line_edit2.text(), self.line_edit3.text())
        session.auth()
        api = session.get_api()
        choice = 1
        if self.radiobutton1.isChecked():
            choice = 1
        elif self.radiobutton2.isChecked():
            choice = 2
        VKStatistic(api, choice, self.line_edit1.text()).get_and_output_data()


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())
