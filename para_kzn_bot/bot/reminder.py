#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from suport_fl import button
import os
from aiogram import Bot
from aiogram.utils.exceptions import ChatNotFound, MessageIsTooLong
from db.manager import ManagerDjango

load_dotenv()

class ReminderBot:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TOKEN'))
        self.manager = ManagerDjango(self.bot)

    async def _close_resources(self):
        """Корректное закрытие всех ресурсов"""
        if hasattr(self.bot, '_session') and self.bot._session:
            await self.bot._session.close()
        if hasattr(self.bot, '_connector') and self.bot._connector:
            await self.bot._connector.close()

    async def send_message_safe(self, user_id: int, text: str) -> bool:
        """Безопасная отправка сообщения с отключенным превью"""
        try:
            if len(text) > 4096:
                return await self._send_long_message(user_id, text)
                
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True  # Отключаем превью ссылок
            )
            return True
        except ChatNotFound:
            await self.manager.del_user(user_id)
            return False
        except Exception:
            return False

    async def _send_long_message(self, user_id: int, text: str) -> bool:
        """Отправка длинных сообщений с сохранением форматирования"""
        parts = []
        while text:
            split_pos = text.rfind('\n\n', 0, 4000) or \
                      text.rfind('\n', 0, 4000) or \
                      text.rfind('. ', 0, 4000) or \
                      4000
            part = text[:split_pos].strip()
            if part:
                parts.append(part)
            text = text[split_pos:].strip()
        
        for part in parts:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=part,
                    parse_mode='HTML',
                    disable_web_page_preview=True  # Также для частей сообщения
                )
            except Exception:
                return False
        return bool(parts)

    async def run_reminder(self):
        """Основная логика работы бота"""
        try:
            dates = button.day_5()
            users = await self.manager.get_all_users()
            cities = await self.manager.get_all_city()

            for user in users:
                if not user.get('get_remainder'):
                    continue

                forecast = await self.manager.create_meteo_message(
                    city=user['city'],
                    lst_days=dates
                )
                if not forecast:
                    continue

                if isinstance(forecast, list):
                    for msg in forecast:
                        await self.send_message_safe(user['user_id'], msg)
                else:
                    await self.send_message_safe(user['user_id'], forecast)

        finally:
            await self._close_resources()

async def main():
    bot = ReminderBot()
    try:
        await bot.run_reminder()
    finally:
        await bot._close_resources()

if __name__ == '__main__':
    asyncio.run(main())
