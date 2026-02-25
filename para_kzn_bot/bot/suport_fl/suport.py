from datetime import date, datetime
from statistics import mean

import prettytable as pt
import re
from typing import List, Optional


def build_user_info(message, cities: Optional[List] = None, update=None):
    """
    Создает словарь с информацией о пользователе
    cities - список городов из API для выбора правильного ID
    update - словарь с полями для обновления
    """
    # По умолчанию используем ID=1
    city_id = 1
    city_name = "Kazan"
    
    # Если передан список городов, выбираем правильный
    if cities and isinstance(cities, list) and len(cities) > 0:
        # Ищем город с ID=1
        for city in cities:
            if city.get('id') == 1:
                city_id = city['id']
                city_name = city['name']
                break
        else:
            # Если нет ID=1, берем первый город
            city_id = cities[0].get('id', 1)
            city_name = cities[0].get('name', 'Kazan')
    
    # Если есть update с city, используем его
    if update and 'city' in update:
        city_id = update['city']
        if cities:
            for city in cities:
                if city.get('id') == city_id:
                    city_name = city['name']
                    break
    
    user_inf_by_put_or_post = {
        'user_id': message.id,
        'city_name': city_name,
        'username': message.username,
        'first_name': message.first_name,
        'last_name': message.last_name,
        'language_code': message.language_code,
        'is_blocked_bot': False,
        'is_banned': False,
        'is_admin': False,
        'is_moderator': False,
        'get_remainder': True,
        'city': city_id
    }

    if update is not None:
        for key, value in update.items():
            user_inf_by_put_or_post[key] = value

    return user_inf_by_put_or_post

def build_spot_info(message, file=None):
    spot_inf = {
        "city_name": "",
        "name": "",
        "description": "",
        "url_map": "",
        "url_forecast": "",
        "lat": None,
        "lon": None,
        "wind_degree_l": None,
        "wind_degree_r": None,
        "wind_min": None,
        "wind_max": None,
        "city": None
    }
    return spot_inf


def create_table(header: list, body: List[dict], point=None):
    if not body:
        raise Exception('Dates are not update')
    table_meteo = pt.PrettyTable(header)
    table_meteo.align = 'r'
    table_meteo.align['Час'] = 'l'

    while body:
        one_hour = body.pop(0)
        time = one_hour["time"][1:-3]
        w_s, w_g = list(map(lam_wind_all, [one_hour["wind_speed"], one_hour["wind_gust"]]))
        wdg = one_hour["wind_degree"]
        if point:
            v = next(point)
            row = [time, w_s, w_g, wdg, v]
        else:
            row = [time, w_s, w_g, wdg]
        table_meteo.add_row(row)

    return table_meteo


def lam_wind(x):
    res = str(round(float(x), 1))
    return res


def lam_degree(x):
    res = str(x)
    if len(res) == 1:
        res = f'{x}°'
    elif len(res) == 2:
        res = f'{x}°'
    elif len(res) == 3:
        res = f'{x}°'
    return res


def lam_temp(x):
    res = int(round(float(x)))
    if 0 <= res < 10:
        res = f'{res}'
    elif res >= 10:
        res = f'{res}'
    elif 0 > res >= -9:
        res = f'{res}'
    elif res <= -10:
        res = f'{res}'
    return str(res)


def lam_wind_all(x):
    res = str(round(float(x)))
    if len(res) == 1:
        res = f'{res}'
    elif len(res) == 2:
        res = f'{res}'
    return res


def ampop(m_d):
    pop_time = [tm["time"][1:-3] for tm in m_d if float(tm['pop']) >= 0.4]
    if len(pop_time) > 0:
        return f'Осадки в\n({", ".join(pop_time)}) ч'
    else:
        return 'Осадков нет'


def middle_temp(fly_lst):
    return mean([temp['temp'] for temp in fly_lst])


def amdegree(dg):
    dg = int(dg)
    if 345 < dg or 15 > dg:
        return 'с'
    elif 15 <= dg <= 30:
        return 'ссв'
    elif 30 <= dg <= 60:
        return 'св'
    elif 60 <= dg <= 75:
        return 'всв'
    elif 75 <= dg <= 105:
        return 'в'
    elif 105 <= dg <= 120:
        return 'вюв'
    elif 120 <= dg <= 150:
        return 'юв'
    elif 150 <= dg <= 165:
        return 'ююв'
    elif 165 <= dg <= 195:
        return 'ю'
    elif 195 <= dg <= 210:
        return 'ююз'
    elif 210 <= dg <= 240:
        return 'юз'
    elif 240 <= dg <= 255:
        return 'зюз'
    elif 255 <= dg <= 285:
        return 'з'
    elif 285 <= dg <= 300:
        return 'зсз'
    elif 300 <= dg <= 330:
        return 'сз'
    elif 330 <= dg <= 345:
        return 'ссз'


def amdate(dat):
    mon_dct = {'01': 'Января', '02': 'февраля', '03': 'марта', '04': 'апреля',
               '05': 'майя', '06': 'июня', '07': 'июля', '08': 'августа',
               '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'}
    week_dict = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Вс'}
    new_dat = str(dat).split('-')
    mon = mon_dct[new_dat[1]]
    day = new_dat[2]
    x = map(int, dat.split('-'))
    week = week_dict[datetime.isoweekday(date(*x))]
    return f'{week} {day} {mon}'


def re_amdate(dat: str):
    mon_dct = {'01': 'Января', '02': 'февраля', '03': 'марта', '04': 'апреля',
               '05': 'майя', '06': 'июня', '07': 'июля', '08': 'августа',
               '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'}
    new_dat = str(dat).split(' ')
    mon = ''
    for num in mon_dct:
        if mon_dct[num] == new_dat[2]:
            mon = num
    day = new_dat[1]
    now = datetime.now()
    year = str(now.year)
    return f'{year}-{mon}-{day}'


def re_amcommand_change(message):
    lst_command = re.findall(r'(\w+?)\s([А-Яа-я.]+?)\s(.+)', message)
    command_dict = {'слева': "wind_degree_l", 'справа': "wind_degree_r", 'с.ш': "lat",
                    'в.д': "lon", 'макс.ветер': "w_max", 'мин.ветер': "w_min",
                    'ссылка': "url", 'описание': "description"}
    return [lst_command[0][0], command_dict[lst_command[0][1]], lst_command[0][2]]