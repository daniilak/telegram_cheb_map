from peewee import *
import time
import base64
from pyrogram.types import Chat

# Создаем базу данных SQLite
db = SqliteDatabase('telegram_channels.db')

class BaseModel(Model):
    class Meta:
        database = db

class Groups(BaseModel):
    id = AutoField(primary_key=True)
    id_channel = BigIntegerField()
    time_added = IntegerField()
    time_updated = IntegerField()
    title = TextField()
    username = TextField(null=True)
    members_count = IntegerField(null=True)
    messages_count = IntegerField(null=True)
    photo_base64 = TextField(null=True)

    class Meta:
        table_name = 'groups'

class HistoryGroups(BaseModel):
    id = AutoField(primary_key=True)
    id_channel = BigIntegerField()
    time_created = IntegerField()
    key = CharField()
    value = TextField()

    class Meta:
        table_name = 'history_groups'

def create_tables():
    """Создание таблиц в базе данных"""
    db.connect()
    db.create_tables([Groups, HistoryGroups])
    db.close()

def save_history(id_channel, key, value, time_created):
    """Сохранение истории изменений"""
    HistoryGroups.create(
        id_channel=id_channel,
        time_created=time_created,
        key=key,
        value=str(value)
    )

def get_photo_base64(photo):
    """Конвертация фото в base64"""
    try:
        if photo:
            return base64.b64encode(photo).decode('utf-8')
    except Exception as e:
        print(f"Ошибка при конвертации фото в base64: {e}")
    return None

def process_group(chat: Chat, history_count: int, photo_bytes: bytes = None):
    """Обработка группы: создание новой или обновление существующей"""
    current_time = int(time.time())
    
    # Проверяем существование группы
    group = Groups.get_or_none(Groups.id_channel == chat.id)
    
    group_data = {
        "id": chat.id,
        "title": chat.title or chat.first_name,
        "username": chat.username,
        "members_count": chat.members_count,
        "messages_count": history_count,
    }
    
    if group is None:
        # Если группы нет, создаем новую
        photo_base64 = get_photo_base64(photo_bytes) if photo_bytes else None
        
        Groups.create(
            id_channel=group_data["id"],
            time_added=current_time,
            time_updated=current_time,
            title=group_data["title"],
            username=group_data["username"],
            members_count=group_data["members_count"],
            messages_count=group_data["messages_count"],
            photo_base64=photo_base64
        )
        print(f"Добавлена новая группа: {group_data['title']}")
    else:
        # Если группа существует, проверяем изменения
        changes = {}
        
        if group.title != group_data["title"]:
            changes["title"] = group.title
            group.title = group_data["title"]
            
        if group.username != group_data["username"]:
            changes["username"] = group.username
            group.username = group_data["username"]
            
        if group.members_count != group_data["members_count"]:
            changes["members_count"] = group.members_count
            group.members_count = group_data["members_count"]
            
        if group.messages_count != group_data["messages_count"]:
            changes["messages_count"] = group.messages_count
            group.messages_count = group_data["messages_count"]
        
        # Проверяем фото
        if photo_bytes:
            new_photo_base64 = get_photo_base64(photo_bytes)
            if new_photo_base64 != group.photo_base64:
                changes["photo"] = group.photo_base64
                group.photo_base64 = new_photo_base64
        
        # Если есть изменения, сохраняем их в историю
        if changes:
            return
            for key, value in changes.items():
                save_history(group.id_channel, key, value, group.time_updated)
            group.time_updated = current_time
            group.save()
            # print(f"Обновлена группа: {group_data['title']}")
    

def get_all_groups():
    """Получение всех групп из базы данных"""
    groups = Groups.select().order_by(Groups.members_count.desc())
    result = []
    for group in groups:
        result.append({
            'id': group.id_channel,
            'title': group.title,
            'username': group.username,
            'members_count': group.members_count,
            'messages_count': group.messages_count,
            'photo_base64': group.photo_base64
        })
    return result

if __name__ == '__main__':
    create_tables() 