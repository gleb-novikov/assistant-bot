# Персональный ассистент

## Описание

Проект ассистента в интерфейсе Telegram-бота с Open Source LLM для решения различных задач пользователя.

## Целевая аудитория

LLM-исследователи

## Роли

- **Пользователь** – Telegram-пользователи, которые взаимодействуют с ботом;
- **Администраторы** – роль, имеющая возможность выдавать доступ к боту другим пользователям;

## Функциональные возможности

1. Регистрация и аутентификация пользователей;
2. Выдача администратором доступов к боту;
3. Взаимодействие с LLM через бота;
4. Отображение статистики по боту;

## База данных

### Таблица «Users»

- `id` (number)
- `created_at` (datatime)
- `telegram_username` (string)
- `telegram_chat_id` (number)
- `first_name` (string)
- `last_name` (string)
- `is_admin` (boolean)
- `is_allowed` (boolean)

### Таблица «Messages»

- `id` (number)
- `created_at` (datatime)
- `user_id` (number)
- `text` (string)
- `answer` (string)

## Стек

`Python` | `aiogram` | `PostgreSQL` | `SQL Alchemy` | `OpenAI` | `Docker` | `Nginx` | `Metabase`

## Разработчик

Глеб Новиков
