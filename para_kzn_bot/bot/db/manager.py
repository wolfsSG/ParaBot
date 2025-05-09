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
        """Создает нового пользователя в системе"""
        try:
            user_info = build_user_info(message.from_user)
            await self.req.post_new_users(user_info)
            logger.info(f"Created user: {message.from_user.id}")
            return user_info
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {}

    async def update_user(self, message: Union[Message, CallbackQuery], 
                         update_inf: Dict) -> bool:
        """Обновляет данные пользователя"""
        try:
            user_info = build_user_info(message.from_user, update_inf)
            await self.req.put_update_users(user_info)
            logger.info(f"Updated user: {message.from_user.id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
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
            user_info = await self.req.get_user_by_id(str(message.from_user.id))
            
            if not user_info:
                await self.create_user(message)
                user_info = await self.req.get_user_by_id(str(message.from_user.id))

            spots = await self.req.get_spots_by_city_id({'city_id': str(user_info['city'])})
            return user_info, spots
            
        except Exception as e:
            logger.error(f"Error getting user and spots: {e}")
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
