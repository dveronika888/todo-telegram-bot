def create_calendar_event(
    task_id: int,
    user_id: int,
    title: str,
    start_time: str,
    end_time: str,
):
    """
    Заглушка для интеграции с календарной подсистемой.

    В дальнейшем здесь будет вызов модуля Google Calendar.
    Модуль календаря должен создать событие и вернуть его идентификатор.
    """

    print("Передача события в календарный модуль:")
    print(f"ID задачи: {task_id}")
    print(f"ID пользователя: {user_id}")
    print(f"Название: {title}")
    print(f"Начало: {start_time}")
    print(f"Окончание: {end_time}")

    return {
        "id": f"calendar_event_{task_id}"
    }


def delete_calendar_event(calendar_event_id: str):
    """
    Заглушка для удаления одного события из календаря.
    """

    if not calendar_event_id:
        return False

    print(f"Удаление события из календаря: {calendar_event_id}")

    return True


def delete_calendar_events(calendar_event_ids: list):
    """
    Заглушка для удаления нескольких событий из календаря.
    """

    for event_id in calendar_event_ids:
        delete_calendar_event(event_id)

    return True