import pygame
import sys
import random
import math
import os

def resource_path(relative_path):
    """Для доступа к файлам внутри .exe или рядом с .py"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) # noqa
    return os.path.join(os.path.abspath("."), relative_path)

def get_data_folder():
    """Возвращает путь к папке хранения данных (в зависимости от ОС)"""
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.local/share")

    path = os.path.join(base, "PacMan")
    os.makedirs(path, exist_ok=True)
    return path

def get_score_file_path():
    return os.path.join(get_data_folder(), "highscore.txt")

def save_high_score(score): # noqa
    try:
        with open(get_score_file_path(), 'w') as f:
            f.write(str(score))
    except Exception as e:
        print(f"Ошибка при сохранении рекорда: {e}")

def load_high_score():
    try:
        with open(get_score_file_path(), 'r') as f:
            return int(f.read())
    except:
        return 0

# --- НАСТРОЙКИ ---
TILE_SIZE = 24
ROWS = 21
COLS = 20
WIDTH = TILE_SIZE * COLS
HEIGHT = TILE_SIZE * ROWS + 40  # +40 для UI
FPS = 60

# --- ЦВЕТА ---
BLACK = (0, 0, 0)
BLUE = (33, 33, 222)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
PINK = (255, 184, 255)
ORANGE = (255, 184, 82)
GREEN = (0, 255, 0)

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ СОСТОЯНИЯ ---
game_state = "menu"
current_score = 0  # Текущий счёт (сохраняется между уровнями)
high_score = 0     # Рекорд (сохраняется всегда)
player: 'Player' = None
ghosts: list['Ghost'] = []
coins = []
bonuses = []
score = 0
lives = 3
ghost_speeds = 1.0  # значение по умолчанию

# --- КАРТА ---
MAP = [
    "11111111111111111111",
    "100000000011000000E1",
    "10111011101101110101",
    "10000000000000000001",
    "10111110111110111101",
    "10000010000E10000001",
    "11110111101111011111",
    "P000010000000000000P",
    "11110101111110101111",
    "10000000001000000001",
    "10111111101111111101",
    "10000000000000000001",
    "10111110111110110101",
    "10000E100000000000E1",
    "11111111111HH1111111",
    "111111111HHHHHH11111",
    "111111111HHHHHH11111",
    "11111111111111111111"
]

LOGICAL_WIDTH = 480  # фиксированное логическое разрешение
LOGICAL_HEIGHT = 576

game_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))

fullscreen = False

# --- ИНИЦИАЛИЗАЦИЯ ---
pygame.init()
screen = pygame.display.set_mode((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pac-Man (SUAI edition)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 36)

# --- ЗВУКИ ---
chomp = pygame.mixer.Sound(resource_path('assets/sounds/Pac Man Chomp.wav'))
death = pygame.mixer.Sound(resource_path('assets/sounds/death.mp3'))
win = pygame.mixer.Sound(resource_path('assets/sounds/win.mp3'))
eat_ghost = pygame.mixer.Sound(resource_path('assets/sounds/pac-man-ghost-eat.mp3'))
power_up = pygame.mixer.Sound(resource_path('assets/sounds/Power Up.mp3'))



# --- КЛАССЫ ---
class Player:
    def __init__(self, x, y): # noqa
        self.grid_x = x
        self.grid_y = y
        self.pix_x = x * TILE_SIZE
        self.pix_y = y * TILE_SIZE
        self.direction = pygame.Vector2(0, 0)
        self.next_direction = pygame.Vector2(0, 0)
        self.buffer_direction = pygame.Vector2(0, 0)
        self.speed = 1.5
        self.mouth_angle = 0
        self.mouth_opening = True
        self.animation_frame = 0
        self.is_alive = True
        self.death_frame = 0
        self.immune_timer = 120  # Иммунитет после смерти
        self.portal_cooldown = 0
        self.death_animation_frames = 60  # Количество кадров анимации смерти
        self.death_animation_speed = 2  # Скорость анимации смерти

    def update(self):
        if not self.is_alive:
            self.death_frame += self.death_animation_speed
            if self.death_frame > self.death_animation_frames:
                self.is_alive = True
                self.death_frame = 0
                self.immune_timer = 180
                # Возвращаем в стартовую позицию
                self.grid_x, self.grid_y = 1, 1
                self.pix_x, self.pix_y = self.grid_x * TILE_SIZE, self.grid_y * TILE_SIZE
                self.direction = pygame.Vector2(0, 0)
            return

            # Уменьшаем таймер иммунитета, если он активен
        if self.immune_timer > 0:
            self.immune_timer -= 1

        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1

        at_center = (
                abs(self.pix_x - self.grid_x * TILE_SIZE) < 2 and
                abs(self.pix_y - self.grid_y * TILE_SIZE) < 2
        )

        if at_center:
            if self.can_move(self.next_direction):
                self.direction = self.next_direction
                self.next_direction = pygame.Vector2(0, 0)
            elif self.can_move(self.buffer_direction):
                self.direction = self.buffer_direction
                self.buffer_direction = pygame.Vector2(0, 0)

        if not self.can_move(self.direction):
            self.direction = pygame.Vector2(0, 0)
            self.pix_x = self.grid_x * TILE_SIZE
            self.pix_y = self.grid_y * TILE_SIZE
        else:
            self.pix_x += self.direction.x * self.speed
            self.pix_y += self.direction.y * self.speed

        self.grid_x = round(self.pix_x / TILE_SIZE)
        self.grid_y = round(self.pix_y / TILE_SIZE)

        # Телепортация
        if (self.portal_cooldown == 0 and 0 <= self.grid_y < len(MAP) and
                0 <= self.grid_x < len(MAP[0]) and MAP[self.grid_y][self.grid_x] == 'P'):
            if self.grid_x == 0:
                self.pix_x = (COLS - 1) * TILE_SIZE
                self.grid_x = COLS - 1
                self.portal_cooldown = 10
            elif self.grid_x == COLS - 1:
                self.pix_x = 0
                self.grid_x = 0
                self.portal_cooldown = 10

        # Анимация рта
        speed = 5
        if self.mouth_opening:
            self.mouth_angle = min(self.mouth_angle + speed, 50)  # Максимальный угол
        else:
            self.mouth_angle = max(self.mouth_angle - speed, 0)  # Минимальный угол

        # Переключение направления анимации
        if self.mouth_angle >= 50:
            self.mouth_opening = False
        elif self.mouth_angle <= 0:
            self.mouth_opening = True

    def can_move(self, direction):
        if direction == (0, 0):
            return False
        new_x = self.grid_x + int(direction.x)
        new_y = self.grid_y + int(direction.y)
        return 0 <= new_y < len(MAP) and 0 <= new_x < len(MAP[0]) and MAP[new_y][new_x] != '1'

    def draw(self):
        center = (int(self.pix_x + TILE_SIZE // 2), int(self.pix_y + TILE_SIZE // 2))
        radius = TILE_SIZE // 2 - 2

        if not self.is_alive:
            # Анимация смерти - уменьшающийся круг
            current_frame = min(self.death_frame, self.death_animation_frames)
            progress = current_frame / self.death_animation_frames
            radius = int((TILE_SIZE // 2 - 2) * (1 - progress))

        # Логика мигания при иммунитете
        should_draw = True
        if self.immune_timer > 0:
            # Мигаем каждые 10 кадров (при 60 FPS - 6 раз в секунду)
            should_draw = (self.immune_timer // 10) % 2 == 0

        if not should_draw:
            return  # Пропускаем отрисовку в этом кадре

        # 1. Рисуем основное тело (жёлтый круг)
        pygame.draw.circle(game_surface, YELLOW, center, radius)

        # 2. Определяем углы рта для разных направлений
        if self.direction.x > 0:  # Вправо
            mouth_width = math.radians(30 + self.mouth_angle)
            angle = 0  # 0° - горизонтально вправо
        elif self.direction.x < 0:  # Влево
            mouth_width = math.radians(30 + self.mouth_angle)
            angle = math.pi  # 180° - горизонтально влево
        elif self.direction.y > 0:  # Вниз
            mouth_width = math.radians(30 + self.mouth_angle)
            angle = math.pi / 2  # 90° - вертикально вниз
        elif self.direction.y < 0:  # Вверх
            mouth_width = math.radians(30 + self.mouth_angle)
            angle = 3 * math.pi / 2  # 270° - вертикально вверх
        else:  # Стоит
            mouth_width = math.radians(30)
            angle = 0

        # 3. Рассчитываем точки рта
        start_angle = angle - mouth_width / 2
        end_angle = angle + mouth_width / 2

        # 4. Рисуем рот (чёрный треугольник)
        points = [center]
        steps = 20
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            points.append((
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle)
            ))
        pygame.draw.polygon(game_surface, BLACK, points)

class Ghost:
    def __init__(self, x, y, color, speed): # noqa
        self.grid_x = x
        self.grid_y = y
        self.pix_x = x * TILE_SIZE
        self.pix_y = y * TILE_SIZE
        self.color = color
        self.base_speed = speed
        self.direction = pygame.Vector2(0, 0)
        self.target = None
        self.personality = self.set_personality()
        self.state = "scatter"  # scatter | chase | frightened
        self.state_timer = 0
        self.frightened_timer = 0
        self.last_decision_point = (x, y)
        self.portal_cooldown = 0  # Таймер задержки после телепортации
        self.last_portal = None  # Последний использованный портал ('left' или 'right')
        self.wave_offset = 0
        self.home_position = (x, y)  # Позиция в доме для возрождения
        self.respawn_timer = 0
        self.is_in_house = True  # Начинаем в доме
        self.respawn_position = (x, y)  # Позиция для возрождения
        self.is_returning_home = False
        self.frightened_color = BLUE  # Цвет в испуганном состоянии
        self.normal_color = color  # Оригинальный цвете
        self.home_exit_pos = (12, 15)  # Позиция выхода из дома
        self.start_position = (x, y)  # Сохраняем стартовые позиции
        self.is_active = True  # Флаг активности призрака
        self.respawn_alpha = 0  # Прозрачность при возрождении (0-255)
        self.respawn_delay = 180  # 1.5 секунды при 60 FPS
        self.respawn_blink_speed = 8  # Скорость мерцания
        # Инициализация первого направления
        possible_dirs = self.get_possible_directions()
        if possible_dirs:
            self.direction = random.choice(possible_dirs)

    def reset(self):
        self.grid_x, self.grid_y = self.start_position
        self.pix_x = self.grid_x * TILE_SIZE
        self.pix_y = self.grid_y * TILE_SIZE
        self.state = "scatter"
        self.color = self.normal_color
        self.is_active = True

        dirs = self.get_possible_directions()
        if dirs:
            self.direction = random.choice(dirs)
        else:
            self.direction = pygame.Vector2(0, 0)

    def reset_to_start(self):
        """Возвращает призрака на стартовую позицию"""
        self.grid_x, self.grid_y = self.start_position
        self.pix_x, self.pix_y = self.grid_x * TILE_SIZE, self.grid_y * TILE_SIZE
        self.state = "scatter"
        self.color = self.normal_color
        self.direction = pygame.Vector2(0, 0)
        self.respawn_timer = FPS * 2  # 2 секунды перед возрождением

    def set_personality(self):
        personalities = {
            RED: {
                "name": "Blinky",
                "scatter_pos": (COLS - 2, 1),
                "chase_mode": "direct",
                "speed_boost": 1.05,
                "scatter_duration": 7,
                "chase_duration": 20
            },
            PINK: {
                "name": "Pinky",
                "scatter_pos": (1, 1),
                "chase_mode": "ambush",
                "speed_boost": 1.0,
                "scatter_duration": 7,
                "chase_duration": 20
            },
            CYAN: {
                "name": "Inky",
                "scatter_pos": (COLS - 2, ROWS - 2),
                "chase_mode": "mirror",
                "speed_boost": 0.95,
                "scatter_duration": 5,
                "chase_duration": 20
            },
            ORANGE: {
                "name": "Clyde",
                "scatter_pos": (1, ROWS - 2),
                "chase_mode": "random",
                "speed_boost": 0.9,
                "scatter_duration": 5,
                "chase_duration": 20
            }
        }
        return personalities.get(self.color)

    def update(self, player, ghosts): # noqa
        # Призрак был съеден — идёт в дом
        if self.state == "eaten":
            self.return_to_home()
            return

        # Призрак в доме — ожидает возрождение
        if self.state == "respawning":
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.reset()
            return

        # Призрак отключён — ничего не делает
        if not self.is_active:
            return

        # Обычный цикл
        self.update_state()
        self.grid_x = round(self.pix_x / TILE_SIZE)
        self.grid_y = round(self.pix_y / TILE_SIZE)

        if self.at_decision_point():
            self.last_decision_point = (self.grid_x, self.grid_y)
            self.make_decision(player, ghosts)

        self.move()
        self.handle_portals()

    def update_state(self):
        """Управление состояниями scatter/chase/frightened"""
        if self.state == "frightened":
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.state = "chase"
                self.state_timer = 0
                # Возвращаем оригинальный цвет
                if self.personality["name"] == "Blinky":
                    self.color = RED
                elif self.personality["name"] == "Pinky":
                    self.color = PINK
                elif self.personality["name"] == "Inky":
                    self.color = CYAN
                elif self.personality["name"] == "Clyde":
                    self.color = ORANGE
        else:
            self.state_timer += 1
            if self.state == "scatter" and self.state_timer > self.personality["scatter_duration"] * FPS:
                self.state = "chase"
                self.state_timer = 0
            elif self.state == "chase" and self.state_timer > self.personality["chase_duration"] * FPS:
                self.state = "scatter"
                self.state_timer = 0

    def set_frightened(self, duration):
        if self.state != "eaten":  # Не действует на уже съеденных
            self.state = "frightened"
            self.frightened_timer = duration * FPS
            self.color = self.frightened_color
            # Разворачиваем призрака при испуге
            self.direction = -self.direction if random.random() > 0.5 else self.direction

    def at_decision_point(self):
        return (abs(self.pix_x - self.grid_x * TILE_SIZE) < 2 and
                abs(self.pix_y - self.grid_y * TILE_SIZE) < 2)

    def make_decision(self, player, ghosts): # noqa
        possible_dirs = self.get_possible_directions()
        if not possible_dirs:
            return

        # Запрет разворота на 180° (если есть другие варианты)
        opposite_dir = -self.direction
        if len(possible_dirs) > 1 and opposite_dir in possible_dirs:
            possible_dirs.remove(opposite_dir)

        # Выбор цели в зависимости от состояния
        if self.state == "scatter":
            target = self.personality["scatter_pos"]
        elif self.state == "frightened":
            target = self.get_random_target()
        else:  # chase
            target = self.get_chase_target(player, ghosts)

        # Выбор оптимального направления
        if self.state == "frightened":
            self.direction = random.choice(possible_dirs)
        else:
            distances = []
            for direction in possible_dirs:
                new_x = self.grid_x + direction.x
                new_y = self.grid_y + direction.y
                dist = math.dist((new_x, new_y), target)
                distances.append(dist)

            min_dist = min(distances)
            best_dirs = [d for d, dist in zip(possible_dirs, distances) if dist == min_dist]
            self.direction = random.choice(best_dirs)

    def get_chase_target(self, player, ghosts): # noqa
        """Персонализированные стратегии преследования"""
        mode = self.personality["chase_mode"]

        if mode == "direct":  # Blinky
            return (player.grid_x, player.grid_y) # noqa

        elif mode == "ambush":  # Pinky
            target_x = player.grid_x + player.direction.x * 4
            target_y = player.grid_y + player.direction.y * 4
            return (target_x, target_y) # noqa

        elif mode == "mirror":  # Inky
            blinky = next((g for g in ghosts if g.color == RED), None)
            if blinky:
                dx = player.grid_x - blinky.grid_x
                dy = player.grid_y - blinky.grid_y
                return (player.grid_x + dx, player.grid_y + dy) # noqa
            return (player.grid_x, player.grid_y) # noqa

        else:  # Clyde
            dist_to_player = math.dist((self.grid_x, self.grid_y),
                                       (player.grid_x, player.grid_y))
            if dist_to_player < 8:
                return self.personality["scatter_pos"]
            return (player.grid_x, player.grid_y) # noqa

    @staticmethod
    def get_random_target():
        """Случайная цель в режиме frightened"""
        return (random.randint(2, COLS - 3), random.randint(2, ROWS - 3)) # noqa

    def get_possible_directions(self):
        directions = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            direction = pygame.Vector2(dx, dy)
            if self.can_move(direction):
                directions.append(direction)
        return directions

    def move(self):
        """Движение с учетом текущей скорости"""
        speed = self.base_speed * self.personality["speed_boost"]
        if self.state == "frightened":
            speed *= 0.5  # Замедление в frightened режиме

        self.pix_x += self.direction.x * speed
        self.pix_y += self.direction.y * speed

    def handle_portals(self):
        """Обработка телепортации через порталы"""
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1
            return

        # Проверяем, что призрак находится в центре тайла
        at_center = (
                abs(self.pix_x - self.grid_x * TILE_SIZE) < 2 and
                abs(self.pix_y - self.grid_y * TILE_SIZE) < 2
        )

        if not at_center:
            return

        # Проверяем, что находимся на портале
        if (0 <= self.grid_y < len(MAP) and
                0 <= self.grid_x < len(MAP[0]) and MAP[self.grid_y][self.grid_x] == 'P'):

            # Определяем какой это портал
            current_portal = 'left' if self.grid_x == 0 else 'right' if self.grid_x == COLS - 1 else None

            # Если это новый портал (не тот, из которого только что вышли)
            if current_portal and current_portal != self.last_portal:
                if self.grid_x == 0 and self.direction.x < 0:  # Выход слева
                    self.pix_x = (COLS - 2) * TILE_SIZE
                    self.grid_x = COLS - 2
                    self.last_portal = 'right'
                    self.portal_cooldown = 15
                elif self.grid_x == COLS - 1 and self.direction.x > 0:  # Выход справа
                    self.pix_x = 1 * TILE_SIZE
                    self.grid_x = 1
                    self.last_portal = 'left'
                    self.portal_cooldown = 15
            else:
                self.last_portal = None

    def draw(self):
        # Если призрак съеден - рисуем только глаза
        if self.state == "eaten":
            # Создаем поверхность с прозрачностью
            ghost_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

            # Рисуем глаза (белые круги)
            eye_size = TILE_SIZE // 6
            left_eye = (TILE_SIZE // 2 - 6, TILE_SIZE // 2 - 4)
            right_eye = (TILE_SIZE // 2 + 6, TILE_SIZE // 2 - 4)

            pygame.draw.circle(ghost_surface, WHITE, left_eye, eye_size)
            pygame.draw.circle(ghost_surface, WHITE, right_eye, eye_size)

            # Рисуем зрачки (черные круги) с учетом направления движения
            pupil_offset = 2
            pygame.draw.circle(ghost_surface, BLACK,
                               (left_eye[0] + self.direction.x * pupil_offset,
                                left_eye[1] + self.direction.y * pupil_offset),
                               eye_size // 2)
            pygame.draw.circle(ghost_surface, BLACK,
                               (right_eye[0] + self.direction.x * pupil_offset,
                                right_eye[1] + self.direction.y * pupil_offset),
                               eye_size // 2)

            game_surface.blit(ghost_surface, (self.pix_x, self.pix_y))
            return

        # Остальной код отрисовки для обычных состояний...
        x, y = int(self.pix_x), int(self.pix_y) # noqa
        size = TILE_SIZE - 4
        center_x = x + TILE_SIZE // 2
        center_y = y + TILE_SIZE // 2

        # Цвет призрака в зависимости от состояния
        ghost_color = self.frightened_color if self.state == "frightened" else self.color

        # 1. Верхний полукруг (голова) - БЕЗ ИЗМЕНЕНИЙ
        head_height = size // 2  # Половина высоты для головы
        pygame.draw.ellipse(game_surface, ghost_color,
                            [x + 2, y + 2, size, head_height])

        # 2. Основное тело - начинаем ниже головы
        body_top = y + 2 + head_height - 3  # Поднимаем на 3 пикселя
        body_height = size // 2 + 3  # Компенсируем поднятие
        body_rect = pygame.Rect(x + 2, body_top, size, body_height)
        pygame.draw.rect(game_surface, ghost_color, body_rect)

        # 3. Волнистая часть - начинаем строго от низа тела
        wave_height = 5
        points = []
        steps = 6

        # Стартовая точка (левый край тела)
        points.append((x + 2, body_top + body_height))

        # Волны
        for i in range(1, steps):
            px = x + 2 + i * size // (steps - 1)
            wave = wave_height * math.sin(self.wave_offset + i)
            points.append((px, (body_top + body_height) - wave))

        # Финишная точка (правый край тела)
        points.append((x + 2 + size, body_top + body_height))

        # Рисуем волнистую часть
        pygame.draw.polygon(game_surface, ghost_color, points)

        # 4. Глаза - БЕЗ ИЗМЕНЕНИЙ
        eye_size = size // 6
        left_eye = (center_x - 6, center_y - 4)
        right_eye = (center_x + 6, center_y - 4)

        pygame.draw.circle(game_surface, WHITE, left_eye, eye_size)
        pygame.draw.circle(game_surface, WHITE, right_eye, eye_size)

        # Зрачки
        pupil_offset = 2
        pygame.draw.circle(game_surface, BLACK,
                           (left_eye[0] + self.direction.x * pupil_offset,
                            left_eye[1] + self.direction.y * pupil_offset),
                           eye_size // 2)
        pygame.draw.circle(game_surface, BLACK,
                           (right_eye[0] + self.direction.x * pupil_offset,
                            right_eye[1] + self.direction.y * pupil_offset),
                           eye_size // 2)

        # Анимация волны
        self.wave_offset += 0.2

    def can_move(self, direction):
        if self.state == "eaten":  # В состоянии "съеден" игнорируем стены
            return True
        if direction == (0, 0):
            return False
        new_x = self.grid_x + int(direction.x)
        new_y = self.grid_y + int(direction.y)
        return 0 <= new_y < len(MAP) and 0 <= new_x < len(MAP[0]) and MAP[new_y][new_x] != '1'

    def handle_eaten_state(self):
        """Обработка состояния, когда призрак съеден"""
        # Двигаемся к дому (коробке)
        target_x, target_y = self.home_position
        target_rect = pygame.Rect(target_x * TILE_SIZE, target_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        ghost_rect = pygame.Rect(self.pix_x, self.pix_y, TILE_SIZE, TILE_SIZE) # noqa

        # Если достигли дома
        if ghost_rect.colliderect(target_rect):
            self.state = "scatter"
            self.respawn_timer = FPS * 3  # 3 секунды в доме
            self.is_in_house = True
        else:
            # Двигаемся к дому
            if self.at_decision_point():
                possible_dirs = self.get_possible_directions()
                if possible_dirs:
                    distances = []
                    for direction in possible_dirs:
                        new_x = self.grid_x + direction.x
                        new_y = self.grid_y + direction.y
                        dist = math.dist((new_x, new_y), self.home_position)
                        distances.append(dist)

                    min_dist = min(distances)
                    best_dirs = [d for d, dist in zip(possible_dirs, distances) if dist == min_dist]
                    self.direction = random.choice(best_dirs)

            self.move()

    def handle_eaten(self):
        self.state = "eaten"
        self.color = WHITE
        self.is_active = False
        self.respawn_alpha = 0
        self.respawn_timer = 0  # пока не нужен

    def return_to_home(self):
        # Если уже дома - запускаем respawn
        if (self.grid_x, self.grid_y) == self.start_position:
            self.state = "respawning"
            self.respawn_timer = FPS * 3
            return

        # Рассчитываем направление к дому
        dx = self.start_position[0] - self.grid_x
        dy = self.start_position[1] - self.grid_y

        # Нормализуем направление (делаем длину 1)
        length = max(1, math.sqrt(dx * dx + dy * dy))
        dx /= length
        dy /= length

        # Устанавливаем направление (без проверки стен)
        self.direction = pygame.Vector2(dx, dy)

        # Двигаемся с увеличенной скоростью (x2)
        speed = self.base_speed * 2
        self.pix_x += self.direction.x * speed
        self.pix_y += self.direction.y * speed

        # Обновляем позицию в сетке
        self.grid_x = round(self.pix_x / TILE_SIZE)
        self.grid_y = round(self.pix_y / TILE_SIZE)

    def update_respawn(self):
        """Обновление состояния возрождения"""
        self.respawn_timer -= 1

        # Полная невидимость в первые 2 секунды
        if self.respawn_timer > self.respawn_delay - 120:  # 120 кадров = 2 сек
            self.respawn_alpha = 0
        # Мерцание в последнюю секунду
        elif self.respawn_timer > 0:
            self.respawn_alpha = min(255, self.respawn_alpha + self.respawn_blink_speed)
            # Мерцающий эффект
            if random.random() < 0.2:  # 20% chance to blink
                self.respawn_alpha = 0
        else:
            # Полное возрождение
            self.reset()
            self.respawn_alpha = 255


class Bonus:
    def __init__(self, x, y, is_energizer=False): # noqa
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.radius = 6 if not is_energizer else 10
        self.active = True
        self.blink_timer = 0
        self.is_energizer = is_energizer
        self.color = GREEN if not is_energizer else (255, 184, 255)  # Розовый для энерджайзеров
        self.is_energizer = is_energizer

    def draw(self):
        if not self.active:
            return
        # Энерджайзеры не мигают, обычные бонусы мигают
        if self.is_energizer or self.blink_timer % 30 < 15:
            pygame.draw.circle(game_surface, self.color, (self.x, self.y), self.radius)
            # Для энерджайзеров добавляем белую обводку
            if self.is_energizer:
                pygame.draw.circle(game_surface, WHITE, (self.x, self.y), self.radius, 2)
        self.blink_timer += 1


class Menu:
    def __init__(self):
        self.buttons = [
            {"text": "Start Game", "action": "start"},
            {"text": "Difficulty", "action": "difficulty"},
            {"text": "Exit", "action": "exit"}
        ]
        self.selected = 0
        self.difficulty = 1  # 1 - easy, 2 - medium, 3 - hard

    def draw(self):
        game_surface.fill(BLACK)
        title = big_font.render("PAC-MAN", True, ORANGE)
        game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        for i, button in enumerate(self.buttons):
            color = WHITE if i != self.selected else YELLOW
            text = big_font.render(button["text"], True, color)
            game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 150 + i * 50))

        # Отображение сложности
        if self.buttons[self.selected]["action"] == "difficulty":
            diff_text = font.render(f"Current: {['Easy', 'Medium', 'Hard'][self.difficulty - 1]}", True, CYAN)
            game_surface.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 300))

    def handle_input(self, event): # noqa
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.buttons)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.buttons)
            elif event.key == pygame.K_RETURN:
                return self.buttons[self.selected]["action"]
            elif event.key == pygame.K_LEFT and self.buttons[self.selected]["action"] == "difficulty":
                self.difficulty = max(1, self.difficulty - 1)
            elif event.key == pygame.K_RIGHT and self.buttons[self.selected]["action"] == "difficulty":
                self.difficulty = min(3, self.difficulty + 1)
        return None


# --- ИНИЦИАЛИЗАЦИЯ ИГРЫ ---
def init_game(difficulty):
    global player, ghosts, coins, bonuses, score, lives, game_state, ghost_speeds, high_score, current_score

    if game_state != "win":
        score = 0

    ghost_speeds = [0.6, 1.0, 1.4][difficulty - 1]

    coins = []
    bonuses = []
    for y, row in enumerate(MAP): # noqa
        for x, tile in enumerate(row): # noqa
            if tile == '0':
                if MAP[y][x] != 'H':
                    coins.append(pygame.Rect(x * TILE_SIZE + 8, y * TILE_SIZE + 8, 8, 8))
            elif tile == 'E':  # Энерджайзеры
                bonuses.append(Bonus(x, y, is_energizer=True))

    # Спавн игрока
    player = Player(1, 1)

    # Спавн призраков внутри коробки (координаты области H)
    ghosts = [
        Ghost(12, 15, RED, ghost_speeds),
        Ghost(12, 16, PINK, ghost_speeds),
        Ghost(13, 16, CYAN, ghost_speeds),
        Ghost(13, 15, ORANGE, ghost_speeds)
    ]
    for ghost in ghosts: # noqa
        ghost.home_position = (ghost.grid_x, ghost.grid_y)  # Запоминаем стартовые позиции
        ghost.home_exit_pos = (12, 15)  # Позиция выхода из дома

    high_score = load_high_score()
    lives = 3
    game_state = "playing"
    coins = []
    bonuses = []
    for y, row in enumerate(MAP): # noqa
        for x, tile in enumerate(row): # noqa
            if tile == '0':
                if MAP[y][x] != 'H':
                    coins.append(pygame.Rect(x * TILE_SIZE + 8, y * TILE_SIZE + 8, 8, 8))
            elif tile == 'B':
                bonuses.append(Bonus(x, y))
            elif tile == 'E':  # Энерджайзеры
                bonuses.append(Bonus(x, y, is_energizer=True))


# --- ГЛАВНЫЙ ЦИКЛ ---
menu = Menu()
high_score = load_high_score() # noqa
init_game(menu.difficulty)
game_state = "menu"  # noqa

# Главный игровой цикл
running = True
while running:
    # Обработка событий для всех состояний
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.RESIZABLE)
        elif event.type == pygame.VIDEORESIZE and not fullscreen:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        if event.type == pygame.QUIT:
            running = False

        # Обработка меню
        if game_state == "menu":
            action = menu.handle_input(event)
            if action == "start":
                init_game(menu.difficulty)
                game_state = "playing"
            elif action == "exit":
                running = False

        # Обработка игрового процесса
        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player.next_direction = pygame.Vector2(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    player.next_direction = pygame.Vector2(1, 0)
                elif event.key == pygame.K_UP:
                    player.next_direction = pygame.Vector2(0, -1)
                elif event.key == pygame.K_DOWN:
                    player.next_direction = pygame.Vector2(0, 1)
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"

        # Обработка завершения игры
        elif game_state in ["game_over", "win"]:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and game_state == "win":
                    init_game(menu.difficulty)
                    game_state = "playing"
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"

    # --- ОБНОВЛЕНИЕ ИГРЫ ---
    if game_state == "menu":
        menu.draw()

    elif game_state == "playing":
        # Обновление объектов
        player.update()
        for ghost in ghosts:
            ghost.update(player, ghosts)

        # Проверка столкновений с призраками
        player_rect = pygame.Rect(player.pix_x + 4, player.pix_y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        for ghost in ghosts:
            ghost_rect = pygame.Rect(ghost.pix_x + 4, ghost.pix_y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
            if player_rect.colliderect(ghost_rect) and player.is_alive:
                if ghost.state == "frightened":
                    ghost.handle_eaten()
                    current_score += 200
                    if eat_ghost: eat_ghost.play()
                elif ghost.state != "eaten" and player.immune_timer <= 0:
                    lives -= 1
                    player.is_alive = False
                    if death: death.play()
                    if lives <= 0:
                        game_state = "game_over"
                        pygame.time.wait(1000)

        # Проверка сбора монеток
        for coin in coins[:]:
            if player_rect.colliderect(coin):
                coins.remove(coin)
                current_score += 10
                if chomp: chomp.play()

        # Проверка сбора бонусов
        for bonus in bonuses[:]:
            player_center = (player.pix_x + TILE_SIZE // 2, player.pix_y + TILE_SIZE // 2)
            if bonus.active and math.dist(player_center, (bonus.x, bonus.y)) < TILE_SIZE // 2:
                bonus.active = False
                current_score += 100 if bonus.is_energizer else 50
                if power_up: power_up.play()

                if bonus.is_energizer:
                    for ghost in ghosts:
                        if ghost.state != "eaten":
                            ghost.set_frightened(5)

        # Проверка условия победы
        if not coins and not any(b.active for b in bonuses):
            if win: win.play()
            game_state = "win"
            pygame.time.wait(1000)
            if current_score > high_score:
                high_score = current_score
                save_high_score(high_score)

        # --- ОТРИСОВКА ---
        game_surface.fill(BLACK)

        # Отрисовка стен
        for y, row in enumerate(MAP):
            for x, tile in enumerate(row):
                if tile == '1':
                    pygame.draw.rect(game_surface, BLUE,
                                     (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                                     border_radius=3)

        # Отрисовка монеток
        for coin in coins:
            pygame.draw.circle(game_surface, GOLD, coin.center, 3)

        # Отрисовка бонусов
        for bonus in bonuses:
            bonus.draw()

        # Отрисовка призраков
        for ghost in ghosts:
            ghost.draw()

        # Отрисовка игрока
        player.draw()

        # Отрисовка UI
        pygame.draw.rect(game_surface, BLACK, (0, HEIGHT - 40, WIDTH, 40))
        # Счет
        score_text = font.render(f"Score: {current_score}", True, WHITE)
        game_surface.blit(score_text, (10, HEIGHT - 30))
        # Рекорд
        high_text = font.render(f"Record: {high_score}", True, YELLOW)
        game_surface.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, HEIGHT - 55))
        # Жизни
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        game_surface.blit(lives_text, (WIDTH - 120, HEIGHT - 30))

        # Таймер иммунитета
        if player.immune_timer > 0:
            immune_text = font.render(f"Immune: {player.immune_timer // 60 + 1}s", True, CYAN)
            game_surface.blit(immune_text, (WIDTH // 2 - immune_text.get_width() // 2, HEIGHT - 30))

    elif game_state == "win":
        game_surface.fill(BLACK)
        win_text = big_font.render("YOU WIN!", True, GREEN)
        game_surface.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, 100))

        score_text = font.render(f"Score: {current_score}", True, WHITE)
        game_surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 180))

        high_text = font.render(f"New Record: {high_score}", True, GOLD)
        game_surface.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, 230))

        continue_text = font.render("Press ENTER to continue", True, CYAN)
        game_surface.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, 300))

        menu_text = font.render("Press ESC for menu", True, WHITE)
        game_surface.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, 340))

    elif game_state == "game_over":
        game_surface.fill(BLACK)
        over_text = big_font.render("GAME OVER", True, RED)
        game_surface.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 50))

        score_text = font.render(f"Score: {current_score}", True, WHITE)
        game_surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))

        high_text = font.render(f"Record: {high_score}", True, YELLOW)
        game_surface.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, HEIGHT // 2 + 40))

        menu_text = font.render("Press ESC to return to menu", True, WHITE)
        game_surface.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 80))

    # --- МАСШТАБИРОВАНИЕ И ОТРИСОВКА НА ЭКРАН ---

    window_width, window_height = screen.get_size()
    game_width, game_height = game_surface.get_size()

    scale_w = window_width / game_width
    scale_h = window_height / game_height
    scale = min(scale_w, scale_h)  # сохранение пропорций

    new_width = int(game_width * scale)
    new_height = int(game_height * scale)

    scaled_surface = pygame.transform.smoothscale(game_surface, (new_width, new_height))

    pos_x = (window_width - new_width) // 2
    pos_y = (window_height - new_height) // 2

    screen.fill((0, 0, 0))  # черный фон вокруг

    screen.blit(scaled_surface, (pos_x, pos_y))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()