import asyncio
import logging
from typing import Optional, Dict, List, Union, Tuple
from aiogram import Bot
from aiogram.types import Message, CallbackQuery

from db.async_requests import RequestToDjango
from suport_fl.set_up import *
from suport_fl.suport import build_user_info
from meteo_analysis import get_meteo
from suport_fl.mess import meteo_message

logger = logging.getLogger(__name__)

class ManagerDjango:
    def __init__(self, bot: Bot):
        self.req = RequestToDjango(LOCAL_HOST, OPEN_API_HOST)
        self.bot = bot
        self.cache_meteo = {}
        self.cache_timeout = 3600  # 1 час в секундах

    async def create_user(self, message: Message) -> Dict:
        """Создает нового пользователя в системе с проверкой существующего города"""
        try:
            print(f"\n=== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ {message.from_user.id} ===")
            
            # Получаем список всех городов
            cities = await self.req.get_all_city()
            print(f"Доступные города: {cities}")
            
            if not cities:
                print("❌ Нет городов в базе данных!")
                return {}
            
            # Ищем город с ID=1
            default_city = None
            for city in cities:
                if city.get('id') == 1:
                    default_city = city
                    print(f"✅ Найден город с ID=1: {city}")
                    break
            
            # Если города с ID=1 нет, берем первый доступный город
            if not default_city:
                default_city = cities[0]
                print(f"⚠️ Город с ID=1 не найден, используем: {default_city}")
            
            # Формируем данные пользователя с правильным ID города
            user_info = {
                'user_id': message.from_user.id,
                'city': default_city['id'],
                'city_name': default_city['name'],
                'username': message.from_user.username or '',
                'first_name': message.from_user.first_name or '',
                'last_name': message.from_user.last_name or '',
                'language_code': message.from_user.language_code or 'ru',
                'is_blocked_bot': False,
                'is_banned': False,
                'is_admin': False,
                'is_moderator': False,
                'get_remainder': True
            }
            
            print(f"📤 Отправляем данные пользователя: {user_info}")
            
            # Отправляем запрос на создание пользователя
            result = await self.req.post_new_users(user_info)
            print(f"📥 Результат создания: {result}")
            
            if result:
                logger.info(f"✅ Created user: {message.from_user.id} with city {default_city['name']} (ID: {default_city['id']})")
                return user_info
            else:
                logger.error(f"❌ Failed to create user: {message.from_user.id}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            print(f"Ошибка создания пользователя: {e}")
            import traceback
            traceback.print_exc()
            return {}

    async def update_user(self, message: Union[Message, CallbackQuery], 
                         update_inf: Dict) -> bool:
        """Обновляет данные пользователя - сохраняет существующие поля"""
        try:
            print(f"\n=== UPDATE USER ===")
            print(f"User ID: {message.from_user.id}")
            print(f"Update data: {update_inf}")
            
            # ПОЛУЧАЕМ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ ИЗ БД
            current_user = await self.req.get_user_by_id(str(message.from_user.id))
            
            if not current_user:
                print("❌ Пользователь не найден в БД")
                return False
            
            print(f"Current user from DB: {current_user}")
            
            # СОЗДАЕМ ОБНОВЛЕННЫЕ ДАННЫЕ, НО СОХРАНЯЕМ ВСЕ СУЩЕСТВУЮЩИЕ ПОЛЯ
            updated_user = dict(current_user)  # Копируем все текущие данные
            
            # Обновляем только те поля, которые пришли в update_inf
            for key, value in update_inf.items():
                updated_user[key] = value
                print(f"Updated field {key} = {value}")
            
            print(f"Sending updated user: {updated_user}")
            
            # Отправляем обновление
            result = await self.req.put_update_users(updated_user)
            print(f"Update result: {result}")
            
            if result:
                logger.info(f"✅ Updated user: {message.from_user.id}")
                return True
            else:
                logger.error(f"❌ Failed to update user: {message.from_user.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def del_user(self, user_id: int) -> bool:
        """Удаляет пользователя из системы"""
        try:
            await self.req.del_users(user_id)
            logger.info(f"Deleted user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    async def get_all_users(self) -> List[Dict]:
        """Получает всех пользователей с подпиской"""
        try:
            users = await self.req.get_all_users()
            return [user for user in users if user.get('get_remainder')]
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    async def get_all_city(self) -> List[Dict]:
        """Получает список всех городов"""
        try:
            return await self.req.get_all_city()
        except Exception as e:
            logger.error(f"Error getting cities: {e}")
            return []

    async def get_user_and_spots(self, message: Union[Message, CallbackQuery]) -> Tuple[Dict, List]:
        """Получает информацию о пользователе и список мест"""
        try:
            user_id = str(message.from_user.id)
            print(f"\n=== get_user_and_spots для пользователя {user_id} ===")
            
            # Сначала получаем список городов (он нам понадобится для создания пользователя)
            cities = await self.req.get_all_city()
            print(f"Доступные города: {cities}")
            
            # Получаем пользователя
            user_info = await self.req.get_user_by_id(user_id)
            print(f"Получен user_info: {user_info}")
            
            # Если пользователя нет, создаем с правильным городом
            if not user_info:
                print("Пользователь не найден, создаем нового")
                
                if not cities:
                    print("❌ Нет городов в БД!")
                    return {}, []
                
                # Находим подходящий город
                default_city = None
                for city in cities:
                    if city.get('id') == 1:
                        default_city = city
                        break
                if not default_city:
                    default_city = cities[0]
                
                # Создаем пользователя с правильным ID города
                user_data = {
                    'user_id': message.from_user.id,
                    'city': default_city['id'],
                    'city_name': default_city['name'],
                    'username': message.from_user.username or '',
                    'first_name': message.from_user.first_name or '',
                    'last_name': message.from_user.last_name or '',
                    'language_code': message.from_user.language_code or 'ru',
                    'is_blocked_bot': False,
                    'is_banned': False,
                    'is_admin': False,
                    'is_moderator': False,
                    'get_remainder': True
                }
                
                result = await self.req.post_new_users(user_data)
                if result:
                    user_info = user_data
                    print(f"✅ Пользователь создан с городом {default_city['name']} (ID: {default_city['id']})")
                else:
                    print("❌ Не удалось создать пользователя")
                    return {}, []
            
            # Получаем места для города пользователя
            spots = await self.req.get_spots_by_city_id({'city_id': str(user_info['city'])})
            print(f"Получены места: {len(spots) if spots else 0}")
            
            return user_info, spots or []
            
        except Exception as e:
            logger.error(f"Error getting user and spots: {e}")
            print(f"Исключение в get_user_and_spots: {e}")
            import traceback
            traceback.print_exc()
            return {}, []

    async def create_meteo_message(self, city: int, 
                                 lst_days: List[str], 
                                 chat_id: Optional[int] = None) -> Union[str, List[str]]:
        """Создает сообщение с прогнозом погоды"""
        try:
            spots = await self.req.get_spots_by_city_id({'city_id': str(city)})
            if not spots:
                return 'Горки не добавлены'

            # Проверка кэша
            if city in self.cache_meteo:
                logger.debug(f"Using cached meteo for city {city}")
                result = self.cache_meteo[city]
            else:
                logger.debug(f"Fetching fresh meteo for city {city}")
                if chat_id:
                    await self.bot.send_message(
                        chat_id, 
                        text='Прогноз обновляется...',
                        disable_web_page_preview=True
                    )
                
                # Параллельный запрос данных для всех мест
                tasks = [self.req.get_meteo((sp['lat'], sp['lon'])) for sp in spots]
                result = await asyncio.gather(*tasks)
                
                # Кэшируем результат
                self.cache_meteo[city] = result
                asyncio.create_task(self._clear_city_cache(city))

            # Формируем прогноз
            spot_names = [s['name'] for s in spots]
            result_spots_dict = dict(zip(spot_names, result))
            
            meteo_res = get_meteo.analytics_main(lst_days, result_spots_dict, spots)
            return meteo_message(meteo_res, spots, lst_days)
            
        except Exception as e:
            logger.error(f"Error creating meteo message: {e}")
            return f"Ошибка формирования прогноза: {e}"

    async def _clear_city_cache(self, city_id: int):
        """Очищает кэш для конкретного города через заданное время"""
        await asyncio.sleep(self.cache_timeout)
        if city_id in self.cache_meteo:
            del self.cache_meteo[city_id]
            logger.debug(f"Cleared cache for city {city_id}")