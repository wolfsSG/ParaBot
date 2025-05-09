from suport_fl.suport import *
import re
import logging
from typing import List, Union, Dict, Any

def split_long_message(text, max_length=4000):
    if len(text) <= max_length:
        return [text]
    parts = []
    while len(text) > 0:
        part = text[:max_length]
        last_newline = part.rfind('\n')
        if last_newline > 0:
            part = part[:last_newline]
        parts.append(part)
        text = text[len(part):].lstrip()
    return parts

def header_mess(message):
    text = (f'<b>Привет, {message.from_user.first_name}!</b>\n'
            f'Бот следит за прогнозом погоды и показывает наиболее\n'
            f'подходящие под погодные условия летные места.\n'
            f'Упрощает мониторинг прогноза погоды и выбор места для полетов.\n'
            f'При желании, каждый день в 11:00 по местному времени\n'
            f'вам будет приходить уведомление о летных местах на 5 дней,\n'
            f'города, которого вы выберете.\n\n'
            f'<b>Как им пользоваться?!</b>\n'
            f'1. Выберите город, где хочется полетать.\n'
            f'2. Выберите дату.\n'
            f'3. Отчет вам покажет место, время и благоприятность\n'
            f'условий в процентах, учитывая направление, силу\n'
            f'ветра и вероятность осадков.\n\n'
            f'Также бот удобен тем, что в нем хранится\n'
            f'информация о летных местах и, приезжая в незнакомое место,\n'
            f'можно сразу узнать какие горки есть поблизости,\n'
            f'ведь добавленные места будут доступны всем.\n\n'
            f'<b>ВАЖНО!!!</b> Бот всего лишь упрощает поиск летной погоды,\n'
            f'а не заменяет его. Обязательно перепроверяйте его прогнозы!!!\n'
            f'Внизу каждого отчета есть ссылка на подробный прогноз.\n\n'
            f'<b>Как добавить новые летные места?</b>\n'
            f'Добавлять горки можно через админку,\n'
            f'напишите мне @wolfs_SG и я дам вам доступ к админ-панели.\n\n'
            f'<b>Команды:</b>\n'
            f'/start - это меню\n'
            f'/help - получить доп. информацию по командам\n\n'
            f'p.s. Этот бот написан пилотом из Казани Кобяковым Ярославом\n'
            f'Адаптирован, переделан и частично переписан Лучшевым Сергеем')
    return text


def help_mess():
    return (f'Бот позволяет узнать где и когда <b>можно полетать</b>.\n\n'
            f'<b>Команды:</b>\n'
            f'/start - главное меню\n'
            f'/help - это меню\n\n'
            f'/city - выбрать другой город\n'
            f'/get_spot - Посмотреть добавленные горки\n'
            f'/days - обновить дни\n\n'
            f'/go - <b>включить</b> уведомления\n'
            f'/stop - <b>отключить</b> уведомления\n\n'
            f'<b>Обозначения в прогнозе:</b>\n'
            f'Ч - Время в часах\n'
            f'В - Ср. скорость ветра в м/с\n'
            f'Пор - Порывы ветра в м/с\n'
            f'Нап - Направление ветра в градусах\n'
            f'% - Оценка погодных условий (Сила и Направление ветра), чем больше процентов тем лучше условия\n\n'
            f'Если вы хотите добавить собственные летные места,\n'
            f'напишите мне @wolfs_SG и я дам вам доступ\n'
            f'к админ-панели, где можно будет добавлять свои горки.\n\n'
            f'Побольше летных дней и удачи &#128521;\n')


def err_mess(err):
    now = datetime.now()
    return f"Type:  {str(type(err))[7:-1]}\n"\
           f"Error:  {err}\n"\
           f"Date:  {now.strftime('%d-%m-%Y %H:%M')}"

from suport_fl.suport import *
import re
import logging
from typing import List, Union, Dict, Any

logger = logging.getLogger(__name__)

def split_long_text(text: str, max_len: int = 4000) -> List[str]:
    """Разбивает текст на части по логическим блокам"""
    if len(text) <= max_len:
        return [text]
    
    parts = []
    while text:
        # Сначала пробуем разделить по двойным переносам
        split_pos = text.rfind('\n\n', 0, max_len)
        # Если нет - по обычным переносам
        if split_pos == -1:
            split_pos = text.rfind('\n', 0, max_len)
        # Если нет - по точкам
        if split_pos == -1:
            split_pos = text.rfind('. ', 0, max_len)
        # Если все еще нет - просто по max_len
        if split_pos == -1:
            split_pos = max_len
        
        part = text[:split_pos].strip()
        if part:
            parts.append(part)
        text = text[split_pos:].strip()
    
    return parts

def meteo_message(all_spot: Union[Dict, List], spots: List[Dict], d: List[str]) -> List[str]:
    """Генерирует прогноз погоды с автоматическим разделением"""
    try:
        messages = []
        current_message = ""
        current_date = None

        if isinstance(all_spot, dict):
            message = amdate(d[0]) if len(d) == 1 else 'В ближайшие 5 дней'
            content = f'\n--- <b>{message}</b> ---\n\n'
            content += '<u><b>Летная погода не найдена</b></u> &#128530;\n\n'
            content += f'{easy_meteo(all_spot["time"])}'
            return split_long_text(content)

        for dct in all_spot:
            section = ""
            if current_date is None or dct['meteo']['date'] != current_date:
                current_date = dct['meteo']['date']
                section = f'\n--- <b>{amdate(current_date)}</b> ---\n\n'
            
            section += f'<u><b>{dct["meteo"]["city"]}</b></u>\n'
            section += meteo(dct, spots)
            
            if len(current_message) + len(section) > 3500:
                messages.append(current_message)
                current_message = section
            else:
                current_message += section
        
        if current_message:
            messages.append(current_message)
        
        return messages if messages else ["Нет данных для отображения"]

    except Exception as e:
        logger.error(f"Error in meteo_message: {e}")
        return [f"Ошибка формирования отчета: {e}"]


def meteo(a, spots):
    sp_dc = {}
    for sp in spots:
        if sp['name'] == a['meteo']['city']:
            sp_dc = sp
            break

    degree = [(i["win_l"], i["win_r"]) for i in a["fly_time"]]
    fly_hour = [tm['time'][1:-3] for tm in a["fly_time"]]
    only_fly_hour = [tm['time'] for tm in a["fly_time"] if tm['wdg'] > 0 and tm['w_s'] > 0]
    prognoz = sp_dc['url_forecast']
    fly_meteo = [one_hour for one_hour in a['meteo']['time'] if one_hour['time'][1:-3] in fly_hour]

    lst_header = ['Ч', 'В', 'Пор', 'Нап', '%']
    point = (str(int((tm['w_s'] + tm['wdg']) * 100)) for tm in a["fly_time"])
    table_meteo = create_table(lst_header, fly_meteo, point)

    return (f'Направление ветра:  <b>{degree[0][0]}°-{degree[0][1]}°</b>\n'
            f'<u>Общая оценка: <b>{int((a["time_point"] + a["wind_point"]) * 0.5)}%</b></u>\n'
            f'Оценка ветра:  <b>{a["wind_point"]}%</b>\n'
            f'Летные часы:  <b>{a["time_point"]}%</b> \n({" ".join(only_fly_hour)} )\n\n'
            f'&#127777;  {int(middle_temp(a["meteo"]["time"]))}\n'
            f'&#127782;  {ampop(a["meteo"]["time"])}\n'
            f'<pre>{table_meteo}</pre>\n'
            f'<a href="{prognoz}">Подробнее...</a>\n\n\n')


def easy_meteo(a):
    fly_meteo = [one_hour for one_hour in a if str(one_hour['time'][1:-3]) in ['09', '15', '18']]
    lst_header = ['Час', 'Вет', 'Пор', 'Нап']
    table_meteo = create_table(lst_header, fly_meteo)
    return (f'&#127777;  {int(middle_temp(a))}\n'
            f'&#127782;  {ampop(a)}\n'
            f'<pre>{table_meteo}</pre>\n'
            f'<a href="https://www.windy.com/">Подробнее на Windy</a>\n')


def get_lst_spots_from_txt(message):
    reg = r'(\w+\b).+?(\d{2}[\.\,]\d{4}).+?(\d{2}[\.\,]\d{4}).+?(\d+).+?(\d+).+?(\d+).+?(\d+).+?(https?.+?)\s.+?(\w+.+)'
    return re.findall(reg, message)[0]


def mess_get_spot(spot_dict):
    return f'\n\n<b>Название:</b>  {spot_dict["name"]}\n'\
           f'<b>Координаты:</b>  с.ш "{spot_dict["lat"][:7]}", в.д "{spot_dict["lon"][:7]}"\n'\
           f'<b>Направление ветра:</b>  {spot_dict["wind_degree_l"]}°-{spot_dict["wind_degree_r"]}°\n'\
           f'<b>Ветер:</b>  мин - "{spot_dict["wind_min"]} м/с", макс - "{spot_dict["wind_max"]} м/с"\n\n' \
           f'<b><a href="{spot_dict["url_forecast"]}">Windy прогноз</a></b>\n' \
           f'<b><a href="{spot_dict["url_map"]}">Google map</a></b>  \n\n' \
           f'<b>Описание:</b>  {spot_dict["description"]}\n\n\n\n'


if __name__ == '__main__':
    pass
