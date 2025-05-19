import json
import random
from shapely.geometry import Point, shape
import base64
import math
from models import get_all_groups

class TelegramMapGenerator:
    # Параметры для размеров кружков
    MIN_CIRCLE_SIZE = 2.0  # минимальный размер кружка
    MAX_CIRCLE_SIZE = 8.0  # максимальный размер кружка
    CIRCLE_SIZE_MULTIPLIER = 1.5  # множитель для расчета размера

    # Параметры для размещения точек
    MIN_DISTANCE_BETWEEN_POINTS = 3.0  # минимальное расстояние между центрами точек
    DISTANCE_MULTIPLIER = 0.3  # множитель для расчета минимального расстояния с учетом размеров
    MAX_PLACEMENT_ATTEMPTS = 500  # максимальное количество попыток размещения точки
    MAX_RECURSION_DEPTH = 5  # максимальная глубина рекурсии при поиске точки

    def __init__(self, geojson_path, template_path, map_js_path, output_path):
        self.geojson_path = geojson_path
        self.template_path = template_path
        self.map_js_path = map_js_path
        self.output_path = output_path
        self.chuvashia_geojson = None
        self.telegram_channels = None

    def load_data(self):
        with open(self.geojson_path, 'r', encoding='utf-8') as f:
            self.chuvashia_geojson = json.load(f)
            self.chuvashia_geojson = {
                "type": "FeatureCollection",
                "features": [self.chuvashia_geojson['features']]
            }

        self.telegram_channels = get_all_groups()

    @staticmethod
    def get_image_base64(image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except:
            return None

    @staticmethod
    def random_point_in_polygon(polygon):
        minx, miny, maxx, maxy = polygon.bounds
        while True:
            p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if polygon.contains(p):
                return p

    @classmethod
    def get_circle_size(cls, members_count):
        if members_count is None:
            return cls.MIN_CIRCLE_SIZE
        return max(cls.MIN_CIRCLE_SIZE, min(cls.MAX_CIRCLE_SIZE, math.log(members_count) * cls.CIRCLE_SIZE_MULTIPLIER))

    @staticmethod
    def is_point_occupied(point, occupied_points, min_distance, point_size):
        for occupied_point, occupied_size in occupied_points:
            min_required_distance = (point_size + occupied_size) * TelegramMapGenerator.DISTANCE_MULTIPLIER
            if point.distance(occupied_point) < min_required_distance:
                return True
        return False

    @classmethod
    def find_free_point(cls, polygon, occupied_points, min_distance, max_attempts=MAX_PLACEMENT_ATTEMPTS, recursion_depth=0):
        if recursion_depth >= cls.MAX_RECURSION_DEPTH:
            return cls.random_point_in_polygon(polygon)
            
        minx, miny, maxx, maxy = polygon.bounds
        for _ in range(max_attempts):
            p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if polygon.contains(p) and not cls.is_point_occupied(p, occupied_points, min_distance, cls.get_circle_size(None)):
                return p
        return cls.find_free_point(polygon, occupied_points, min_distance * 1.2, max_attempts, recursion_depth + 1)

    def create_map_html(self):
        chuvashia_polygon = shape(self.chuvashia_geojson['features'][0]['geometry'])
        channel_points = []

        sorted_channels = sorted(self.telegram_channels, 
                               key=lambda x: (x['members_count'] if x['members_count'] is not None else 0,
                                            x['messages_count'] if x['messages_count'] is not None else 0), 
                               reverse=True)

        for channel in sorted_channels:
            point = self.random_point_in_polygon(chuvashia_polygon)
            circle_size = self.get_circle_size(channel['members_count'])
            
            channel_points.append({
                'name': channel['title'],
                'logo_url': f"data:image/jpeg;base64,{channel['photo_base64']}" if channel['photo_base64'] else None,
                'members_count': channel['members_count'],
                'messages_count': channel['messages_count'],
                'description': f"@{channel['username']}" if channel['username'] else "Нет username",
                'username': channel['username'],
                'x': point.x,
                'y': point.y,
                'size': circle_size
            })

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        with open(self.map_js_path, 'r', encoding='utf-8') as f:
            map_js = f.read()

        channels_list = self.generate_channels_list(channel_points)

        html = template.replace('{{channels_list}}', channels_list)
        html = html.replace('{{chuvashia_data}}', json.dumps(self.chuvashia_geojson, ensure_ascii=False))
        html = html.replace('{{channels_data}}', json.dumps(channel_points, ensure_ascii=False))
        html = html.replace('{{map_js}}', map_js)

        return html

    @staticmethod
    def generate_channels_list(channels):
        html = ""
        for channel in sorted(channels, key=lambda x: (x['members_count'] if x['members_count'] is not None else 0,
                                                     x['messages_count'] if x['messages_count'] is not None else 0), 
                             reverse=True):
            telegram_link = f"https://t.me/{channel['username']}" if channel['username'] else "#"
            html += f"""
            <div class="channel-item" data-name="{channel['name']}" data-subscribers="{channel['members_count'] or 0}" data-messages="{channel['messages_count'] or 0}">
                <img src="{channel['logo_url'] or 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIyMCIgZmlsbD0iIzRDQUY1MCIvPjwvc3ZnPg=='}" alt="{channel['name']}">
                <div class="channel-info">
                    <h4 class="channel-title">{channel['name']}</h4>
                    <p class="channel-subscribers">Подписчиков: {channel['members_count'] if channel['members_count'] is not None else 'Нет данных'}</p>
                    <p class="channel-messages">Сообщений: {channel['messages_count'] if channel['messages_count'] is not None else 'Нет данных'}</p>
                    <a href="{telegram_link}" class="channel-link" target="_blank">Перейти в канал</a>
                </div>
            </div>
            """
        return html

    def generate_map(self):
        self.load_data()
        self.html = self.create_map_html()
    
    def save_map(self):
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(self.html)

if __name__ == "__main__":
    generator = TelegramMapGenerator(
        geojson_path='data/chuvashia.json',
        template_path='data/map_template.html',
        map_js_path='data/map.js',
        output_path='data/map.html'
    )
    generator.generate_map()
    generator.save_map()



