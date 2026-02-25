#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from suport_fl import button
import os
import logging
from aiogram import Bot
from aiogram.utils.exceptions import ChatNotFound, MessageIsTooLong, RetryAfter
from db.manager import ManagerDjango

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class ReminderBot:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TOKEN'))
        self.manager = ManagerDjango(self.bot)

    async def _close_resources(self):
        """Корректное закрытие всех ресурсов"""
        try:
            if hasattr(self.bot, '_session') and self.bot._session:
                await self.bot._session.close()
            if hasattr(self.bot, '_connector') and self.bot._connector:
                await self.bot._connector.close()
        except Exception as e:
            logger.error(f"Error closing resources: {e}")

    async def send_message_safe(self, user_id: int, text: str) -> bool:
        """Безопасная отправка сообщения с отключенным превью"""
        try:
            if not text:
                return False
                
            if len(text) > 4096:
                return await self._send_long_message(user_id, text)
                
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"Message sent to user {user_id}")
            return True
            
        except ChatNotFound:
            logger.warning(f"Chat not found for user {user_id}, deleting user")
            await self.manager.del_user(user_id)
            return False
            
        except RetryAfter as e:
            logger.warning(f"Rate limited for user {user_id}, waiting {e.timeout} seconds")
            await asyncio.sleep(e.timeout)
            # Повторяем отправку
            return await self.send_message_safe(user_id, text)
            
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            return False

    async def _send_long_message(self, user_id: int, text: str) -> bool:
        """Отправка длинных сообщений с сохранением форматирования"""
        try:
            # Разбиваем на части по 4000 символов, стараясь не разрывать логические блоки
            parts = []
            current_pos = 0
            text_length = len(text)
            
            while current_pos < text_length:
                # Ищем место для разрыва
                if current_pos + 4000 >= text_length:
                    # Остаток текста
                    parts.append(text[current_pos:])
                    break
                
                # Ищем конец логического блока (двойной перенос строки)
                split_pos = text.rfind('\n\n', current_pos, current_pos + 4000)
                if split_pos == -1:
                    # Если нет двойного переноса, ищем одиночный
                    split_pos = text.rfind('\n', current_pos, current_pos + 4000)
                if split_pos == -1:
                    # Если нет переноса, ищем точку с пробелом
                    split_pos = text.rfind('. ', current_pos, current_pos + 4000)
                if split_pos == -1:
                    # Если ничего не нашли, режем по максимальной длине
                    split_pos = current_pos + 4000
                else:
                    split_pos += 1  # Включаем символ разделителя
                
                parts.append(text[current_pos:split_pos])
                current_pos = split_pos
            
            # Отправляем части
            for i, part in enumerate(parts):
                if part.strip():  # Отправляем только непустые части
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=part,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    # Небольшая задержка между частями одного сообщения
                    if i < len(parts) - 1:
                        await asyncio.sleep(0.5)
            
            logger.info(f"Long message sent to user {user_id} in {len(parts)} parts")
            return True
            
        except Exception as e:
            logger.error(f"Error sending long message to user {user_id}: {e}")
            return False

    async def run_reminder(self):
        """Основная логика работы бота"""
        logger.info("Starting reminder run")
        sent_count = 0
        error_count = 0
        
        try:
            # Получаем даты на 5 дней вперед
            dates = button.day_5()
            logger.info(f"Dates for forecast: {dates}")
            
            # Получаем всех пользователей с подпиской
            users = await self.manager.get_all_users()
            logger.info(f"Found {len(users)} subscribed users")
            
            # Получаем список городов для проверки
            cities = await self.manager.get_all_city()
            city_names = {city['id']: city['name'] for city in cities}
            
            for user in users:
                try:
                    user_id = user.get('user_id')
                    city_id = user.get('city')
                    
                    if not user_id or not city_id:
                        logger.warning(f"Invalid user data: {user}")
                        continue
                    
                    city_name = city_names.get(city_id, 'Неизвестный город')
                    logger.info(f"Processing user {user_id}, city: {city_name} (ID: {city_id})")
                    
                    # Получаем прогноз
                    forecast = await self.manager.create_meteo_message(
                        city=city_id,
                        lst_days=dates,
                        chat_id=user_id
                    )
                    
                    if not forecast:
                        logger.warning(f"No forecast data for user {user_id}")
                        continue
                    
                    # Отправляем прогноз (может быть строкой или списком строк)
                    if isinstance(forecast, list):
                        # Это список сообщений
                        for msg in forecast:
                            if await self.send_message_safe(user_id, msg):
                                sent_count += 1
                            else:
                                error_count += 1
                            # Небольшая задержка между сообщениями одному пользователю
                            await asyncio.sleep(1)
                    else:
                        # Это одно сообщение
                        if await self.send_message_safe(user_id, forecast):
                            sent_count += 1
                        else:
                            error_count += 1
                    
                    # Задержка между разными пользователями (важно для избежания rate limiting)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing user {user.get('user_id')}: {e}")
                    error_count += 1
                    continue
            
            logger.info(f"Reminder completed. Sent: {sent_count}, Errors: {error_count}")
            
        except Exception as e:
            logger.error(f"Critical error in run_reminder: {e}")
        finally:
            await self._close_resources()

async def main():
    """Точка входа"""
    bot = ReminderBot()
    try:
        await bot.run_reminder()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
    finally:
        await bot._close_resources()

if __name__ == '__main__':
    asyncio.run(main())