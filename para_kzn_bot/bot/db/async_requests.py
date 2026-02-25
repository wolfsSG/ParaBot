import os
from dotenv import load_dotenv

import aiohttp
from aiohttp import BasicAuth
import asyncio
from suport_fl.set_up import *


async def _get(host, path, param=None):
    address = host + path
    print(f"\n=== _get запрос ===")
    print(f"Полный URL: {address}")
    print(f"Параметры: {param}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(address, params=param) as resp:
                print(f"Статус ответа: {resp.status}")
                
                if resp.status in [200, 201]:
                    text = await resp.text()
                    print(f"Текст ответа (первые 200 символов): {text[:200]}")
                    try:
                        return await resp.json()
                    except:
                        print("Ответ не в JSON формате")
                        return text
                else:
                    error_text = await resp.text()
                    print(f"Ошибка {resp.status}: {error_text}")
                    return None
        except Exception as e:
            print(f"Исключение в _get: {e}")
            return None


async def _post(host, path, log, pas, data=None):
    address = host + path
    print(f"\n=== _post запрос ===")
    print(f"URL: {address}")
    print(f"Данные: {data}")
    
    auth = BasicAuth(log, pas)
    async with aiohttp.ClientSession() as session:
        try:
            # ВАЖНО: используем json=data для правильной сериализации
            async with session.post(address, json=data, auth=auth) as resp:
                print(f"Статус: {resp.status}")
                if resp.status in [200, 201]:
                    result = await resp.json()
                    print(f"Результат: {result}")
                    return result
                else:
                    error = await resp.text()
                    print(f"Ошибка {resp.status}: {error}")
                    return None
        except Exception as e:
            print(f"Исключение в _post: {e}")
            return None


async def _put(host, path, log, pas, data=None):
    address = host + path
    print(f"\n=== _put запрос ===")
    print(f"URL: {address}")
    print(f"Данные: {data}")
    
    auth = BasicAuth(log, pas)
    async with aiohttp.ClientSession() as session:
        try:
            # ВАЖНО: используем json=data для правильной сериализации
            async with session.put(address, json=data, auth=auth) as resp:
                print(f"Статус: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print(f"Результат: {result}")
                    return result
                else:
                    error = await resp.text()
                    print(f"Ошибка {resp.status}: {error}")
                    return None
        except Exception as e:
            print(f"Исключение в _put: {e}")
            return None


async def _del(host, path, data=None):
    address = host + path
    async with aiohttp.ClientSession() as session:
        async with session.delete(address, json=data):
            pass


class RequestToDjango:
    def __init__(self, host, open_api_host):
        load_dotenv()
        self.api_key = str(os.getenv("API_KEY"))
        self.admin_login = str(os.getenv("ADMIN_LOGIN"))
        self.admin_password = str(os.getenv("ADMIN_PASSWORD"))
        self.host = host
        self.open_api_host = open_api_host
        print(f"\n=== RequestToDjango инициализирован ===")
        print(f"Host: {self.host}")
        print(f"USER_PATH: {USER_PATH}")
        print(f"SPOTS_PATH: {SPOTS_PATH}")
        print(f"CITY_PATH: {CITY_PATH}")

    async def get_all_users(self):
        print("\n=== get_all_users ===")
        return await _get(self.host, USER_PATH)

    async def get_all_city(self):
        print("\n=== get_all_city ===")
        return await _get(self.host, CITY_PATH)

    async def get_user_by_id(self, user_id: str):
        print(f"\n=== get_user_by_id: {user_id} ===")
        path = f"{USER_PATH}{user_id}/"
        print(f"Path: {path}")
        return await _get(self.host, path)

    async def get_spots_by_city_id(self, city_id):
        print(f"\n=== get_spots_by_city_id: {city_id} ===")
        if isinstance(city_id, dict):
            param = city_id
        else:
            param = {'city_id': str(city_id)}
        
        print(f"Параметры запроса: {param}")
        return await _get(self.host, SPOTS_PATH, param=param)

    async def post_new_users(self, inf_usr):
        print(f"\n=== post_new_users ===")
        print(f"Данные для отправки: {inf_usr}")
        
        log, pas = self.admin_login, self.admin_password
        result = await _post(self.host, USER_PATH, log, pas, data=inf_usr)
        print(f"Результат: {result}")
        return result

    async def post_spots(self, inf_spot):
        print(f"\n=== post_spots ===")
        log, pas = self.admin_login, self.admin_password
        return await _post(self.host, SPOTS_PATH, log, pas, data=inf_spot)

    async def put_update_users(self, inf_usr):
        print(f"\n=== put_update_users ===")
        print(f"Data: {inf_usr}")
        
        log, pas = self.admin_login, self.admin_password
        user_id = str(inf_usr['user_id'])
        path = f"{USER_PATH}{user_id}/"
        
        result = await _put(self.host, path, log, pas, data=inf_usr)
        print(f"Put result: {result}")
        return result

    async def del_users(self, user_id):
        print(f"\n=== del_users: {user_id} ===")
        return await _del(self.host, USER_PATH + str(user_id) + '/')

    async def get_meteo(self, latlon):
        print(f"\n=== get_meteo: {latlon} ===")
        latlon = tuple(latlon)
        param = {'lang': 'ru',
                 'lat': latlon[0],
                 'lon': latlon[1],
                 'appid': self.api_key,
                 'units': 'metric'
                 }
        return await _get(self.open_api_host, OPEN_API_PATH, param=param)