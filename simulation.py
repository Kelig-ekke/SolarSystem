import json
import pygame
import math
import os
import sys
from planet import Planet

class SolarSystemSimulation:
    def __init__(self, settings_file='settings.json'):
        self.load_settings(settings_file)
        self.planets = []
        self.time_scale = 1.0
        self.zoom_scale = 1.0
        self.scale = 1.0
        self.base_sun_radius = self.sun_radius  # Сохраняем базовый радиус Солнца
        self.is_paused = False
        self.camera_x = self.window_width // 2
        self.camera_y = self.window_height // 2
        self.follow_planet = None
        
        # Для плавного масштабирования
        self.target_scale = 1.0
        self.scale_speed = 8.0  # Скорость анимации масштабирования (выше = быстрее)
        self.min_scale_diff = 0.001  # Минимальная разница для завершения анимации
        
        self.setup_planets()
        self.setup_ui()
    
    def load_settings(self, settings_file):
        # Найти settings.json в правильной директории
        # Для PyInstaller: проверяем sys._MEIPASS (временная папка)
        # Для обычного запуска: проверяем текущую директорию
        
        possible_paths = [
            settings_file,  # Текущая директория
            os.path.join(os.path.dirname(__file__), settings_file),  # Рядом с скриптом
            os.path.join(sys._MEIPASS, settings_file) if hasattr(sys, '_MEIPASS') else None,  # PyInstaller
        ]
        
        settings_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                settings_path = path
                break
        
        if not settings_path:
            raise FileNotFoundError(f"settings.json не найден. Проверьте, что файл находится в папке с программой.")
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        self.window_width = settings['window_width']
        self.window_height = settings['window_height']
        self.bg_color = tuple(settings['background_color'])
        self.sun_radius = settings['sun_radius']
        self.planet_data = settings['planets']
    
    def setup_planets(self):

        for data in self.planet_data:
            
            planet = Planet(
                name=data['name'],
                orbit_radius=data['orbit_radius'],
                orbit_speed=data['orbit_speed']/1000,
                size=data['size']/5000,
                color=tuple(data['color']),
                show_orbit=True
            )
            
            # Начальные углы для красивого расположения
            planet.angle = len(self.planets) * (2 * math.pi / len(self.planet_data))
            
            self.planets.append(planet)
    
    def setup_ui(self):
        # Сохраняем базовые размеры для масштабирования
        self.base_button_width = 100
        self.base_button_height = 40
        self.base_small_button_size = 40
        self.base_planet_button_width = 140
        self.base_planet_button_height = 40
        
        # Создаем поверхности для кнопок
        self.buttons = {
            'start_pause': {'text': 'Пауза'},
            'slow_down': {'text': '<<'},
            'speed_up': {'text': '>>'},
            'zoom_out': {'text': '-'},
            'zoom_in': {'text': '+'},
            'reset': {'text': 'Сбросить вид'}
        }
        
        # Добавляем кнопки для слежения за каждой планетой
        for i, planet in enumerate(self.planets):
            self.buttons[f'follow_planet_{i}'] = {
                'text': planet.name,
                'planet_index': i
            }
        
        # Пересчитываем позиции кнопок
        self.update_button_positions()
    
    def update_button_positions(self):
        """Пересчитывает позиции и размеры кнопок при изменении размера окна"""
        # Масштабный коэффициент (относительно базового размера 1600x900)
        scale_x = self.window_width / 1600.0
        scale_y = self.window_height / 900.0
        
        # Масштабируем размеры кнопок
        btn_width = max(int(self.base_button_width * scale_x), 50)
        btn_height = max(int(self.base_button_height * scale_y), 30)
        small_btn = max(int(self.base_small_button_size * scale_x), 30)
        planet_btn_width = max(int(self.base_planet_button_width * scale_x), 60)
        planet_btn_height = max(int(self.base_planet_button_height * scale_y), 30)
        
        # Подступы
        margin_x = int(10 * scale_x)
        margin_y = int(10 * scale_y)
        
        # Верхние кнопки
        x_pos = margin_x
        y_pos = margin_y
        
        self.buttons['start_pause']['rect'] = pygame.Rect(x_pos, y_pos, btn_width, btn_height)
        x_pos += btn_width + margin_x
        
        self.buttons['slow_down']['rect'] = pygame.Rect(x_pos, y_pos, small_btn, btn_height)
        x_pos += small_btn + margin_x
        
        self.buttons['speed_up']['rect'] = pygame.Rect(x_pos, y_pos, small_btn, btn_height)
        x_pos += small_btn + margin_x
        
        self.buttons['zoom_out']['rect'] = pygame.Rect(x_pos, y_pos, small_btn, btn_height)
        x_pos += small_btn + margin_x
        
        self.buttons['zoom_in']['rect'] = pygame.Rect(x_pos, y_pos, small_btn, btn_height)
        
        # Кнопка сброса вида - привязана к нижней левой границе
        # С дополнительным отступом от блока кнопок планет
        reset_y = self.window_height - planet_btn_height - margin_y
        self.buttons['reset']['rect'] = pygame.Rect(margin_x, reset_y, planet_btn_width, planet_btn_height)
        
        # Кнопки слежения за планетами - привязаны к нижней левой границе
        button_spacing = planet_btn_height + margin_y // 2
        for i, planet in enumerate(self.planets):
            button_key = f'follow_planet_{i}'
            y_pos = reset_y - button_spacing * (i + 1) - 10*scale_y
            # Если кнопка выходит за верхнюю границу, не показываем её позицию
            if y_pos >= margin_y:
                self.buttons[button_key]['rect'] = pygame.Rect(margin_x, y_pos, planet_btn_width, planet_btn_height)
            else:
                # Размещаем за видимой областью
                self.buttons[button_key]['rect'] = pygame.Rect(margin_x, -planet_btn_height, planet_btn_width, planet_btn_height)
    
    def update(self, delta_time):
        # Плавное масштабирование с использованием экспоненциальной интерполяции
        if abs(self.scale - self.target_scale) > self.min_scale_diff:
            # Используем экспоненциальное затухание для более гладкого замыкания
            alpha = 1.0 - pow(0.05, delta_time * self.scale_speed)
            self.scale += (self.target_scale - self.scale) * alpha
        else:
            self.scale = self.target_scale
        
        if not self.is_paused:
            for planet in self.planets:
                planet.update(delta_time, self.time_scale)
        
        # Пересчитываем позиции кнопок (на случай изменения размера окна)
        self.update_button_positions()
        
        # Если следим за планетой, центрируем камеру на ней
        if self.follow_planet is not None:
            planet = self.planets[self.follow_planet]
            x, y = planet.get_position()
            self.camera_x = self.window_width // 2 - x * self.scale
            self.camera_y = self.window_height // 2 - y * self.scale
    
    def draw(self, screen):
        # Очищаем экран
        screen.fill(self.bg_color)
        
        # Рисуем звезды на фоне
        self.draw_stars(screen)
        
        # Рисуем орбиты планет
        for planet in self.planets:
            planet.draw(screen, self.camera_x, self.camera_y, self.scale)
        
        # Рисуем названия планет
        self.draw_planet_names(screen)
        
        # Рисуем Солнце с масштабированием
        self.draw_sun(screen)
        
        # Отображаем информацию
        self.draw_info(screen)
        
        # Отображаем информацию о планете при зуме
        if self.follow_planet is not None:
            self.draw_planet_info(screen)
        
        # Рисуем кнопки
        self.draw_buttons(screen)

    def draw_planet_names(self, screen):
        # Отображаем названия планет рядом с ними
        font = pygame.font.Font(None, 16)
        for planet in self.planets:
            x, y = planet.get_position()
            screen_x = self.camera_x + x * self.scale
            screen_y = self.camera_y + y * self.scale
            
            # Вычисляем экранный радиус планеты и позицию над верхней точкой
            planet_screen_radius = max(2, int(planet.size * self.scale))
            text = font.render(planet.name, True, (200, 200, 200))
            text_x = int(screen_x) - text.get_width() // 2
            text_y = int(screen_y) - planet_screen_radius - text.get_height() - 4
            screen.blit(text, (text_x, text_y))
    
    
    def draw_stars(self, screen):
        # Рисуем звездочки на фоне
        import random
        random.seed(42)  # Для постоянного расположения звезд
        
        for i in range(100):
            x = random.randint(0, self.window_width)
            y = random.randint(0, self.window_height)
            brightness = random.randint(100, 255)
            size = random.randint(1, 3)
            pygame.draw.circle(screen, (brightness, brightness, brightness), 
                             (x, y), size)
    
    def draw_sun(self, screen):
        # Солнце находится в начале координат (0, 0)
        sun_x = self.camera_x
        sun_y = self.camera_y
        
        # Масштабируем Солнце вместе с общим масштабом
        current_sun_radius = self.base_sun_radius * self.scale
        
        # Рисуем свечение Солнца
        for i in range(3, 0, -1):
            glow_radius = current_sun_radius * (1 + i * 0.2)
            alpha = 50 - i * 10
            glow_surface = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, 
                             (255, 255, 100, alpha), 
                             (int(glow_radius), int(glow_radius)), 
                             int(glow_radius))
            screen.blit(glow_surface, 
                       (sun_x - glow_radius, sun_y - glow_radius))
        
        # Рисуем само Солнце
        pygame.draw.circle(screen, (255, 255, 0), 
                          (int(sun_x), int(sun_y)), 
                          int(current_sun_radius))
        
    def draw_info(self, screen):
        # Масштабируем размер шрифта и позицию текста в зависимости от размера окна
        scale = self.window_height / 900.0
        font_size = max(int(24 * scale), 14)
        font = pygame.font.Font(None, font_size)
        
        # Масштабируем отступы
        margin_x = int(10 * scale)
        start_y = int(60 * scale)
        line_spacing = int(30 * scale)
        
        # Информация о скорости и масштабе
        speed_text = f"Скорость: {self.time_scale:.1f}x"
        scale_text = f"Масштаб: {self.scale:.2f}"
        status_text = "Пауза" if self.is_paused else "Симуляция запущена"
        
        # Информация о слежении
        follow_text = "Слежение: Нет"
        if self.follow_planet is not None:
            follow_text = f"Слежение: {self.planets[self.follow_planet].name}"
        
        texts = [
            speed_text,
            scale_text,
            status_text,
            follow_text
        ]
        
        for i, text in enumerate(texts):
            rendered = font.render(text, True, (255, 255, 255))
            screen.blit(rendered, (margin_x, start_y + i * line_spacing))
    
    def draw_planet_info(self, screen):
        if self.follow_planet is None:
            return
        
        planet = self.planets[self.follow_planet]
        planet_data = self.planet_data[self.follow_planet]
        
        # Масштабируем размер шрифта и отступы
        scale = self.window_height / 900.0
        font_size = max(int(28 * scale), 16)
        font = pygame.font.Font(None, font_size)
        
        margin_x = int(20 * scale)
        line_spacing = int(28 * scale)
        
        # Формируем текст информации
        info_lines = [
            f"{planet.name}",
            f"Растояние от Солнца: {planet_data['orbit_radius']} млн км",
            f"Диаметр: {planet_data['size']} км",
            f"Скорость движения: {planet_data['orbit_speed']} км/с",
            f"Продолжительность дня: {planet_data['day']}"
        ]
        
        # Вычисляем размер блока текста
        rendered_lines = [font.render(line, True, (255, 255, 255)) for line in info_lines]
        
        # Находим максимальную ширину текста
        max_width = max(line.get_width() for line in rendered_lines)
        
        # Вычисляем позицию блока (справа, по центру по вертикали)
        block_width = max_width + margin_x * 2
        block_height = len(info_lines) * line_spacing + margin_x
        
        block_x = self.window_width - block_width - margin_x
        block_y = (self.window_height - block_height) // 2
        
        # Рисуем полупрозрачный фон блока
        background = pygame.Surface((block_width, block_height))
        background.set_alpha(200)
        background.fill((20, 20, 60))
        screen.blit(background, (block_x, block_y))
        
        # Рисуем бордюр блока
        pygame.draw.rect(screen, (100, 100, 200), (block_x, block_y, block_width, block_height), 2)
        
        # Рисуем текст
        text_x = block_x + margin_x
        text_y = block_y + margin_x // 2
        
        for i, rendered_line in enumerate(rendered_lines):
            screen.blit(rendered_line, (text_x, text_y + i * line_spacing))
    
    def draw_buttons(self, screen):
        # Масштабируем размер шрифта в зависимости от размера окна
        scale = self.window_height / 900.0
        font_size = max(int(28 * scale), 16)
        font = pygame.font.Font(None, font_size)
        
        for name, button in self.buttons.items():
            if 'rect' not in button:
                continue
            # Рисуем прямоугольник кнопки
            pygame.draw.rect(screen, (50, 50, 100), button['rect'])
            pygame.draw.rect(screen, (100, 100, 200), button['rect'], 2)
            
            # Рисуем текст кнопки
            text = font.render(button['text'], True, (255, 255, 255))
            text_rect = text.get_rect(center=button['rect'].center)
            screen.blit(text, text_rect)
    
    def handle_click(self, pos):
        for name, button in self.buttons.items():
            if button['rect'].collidepoint(pos):
                self.handle_button_click(name)
                return True
        return False
    
    def handle_button_click(self, button_name):
        if button_name == 'start_pause':
            self.is_paused = not self.is_paused
            self.buttons['start_pause']['text'] = 'Старт' if self.is_paused else 'Пауза'
        
        elif button_name == 'slow_down':
            self.change_speed(up=False)
        
        elif button_name == 'speed_up':
            self.change_speed(up=True)
        
        elif button_name == 'zoom_in':
            self.change_zoom(plus=True)
        
        elif button_name == 'zoom_out':
            self.change_zoom(plus=False)
        
        elif button_name == 'reset':
            self.camera_x = self.window_width // 2
            self.camera_y = self.window_height // 2
            self.target_scale = 1.0
            self.follow_planet = None
        
        elif button_name.startswith('follow_planet_'):
            # Обработка кнопок слежения за планетами
            planet_index = self.buttons[button_name]['planet_index']
            
            if self.follow_planet == planet_index:
                # Если уже следим за этой планетой, отключаем фокус
                self.camera_x = self.window_width // 2
                self.camera_y = self.window_height // 2
                self.target_scale = 1.0
                self.follow_planet = None
            else:
                # Иначе включаем фокус на выбранную планету
                self.follow_planet = planet_index
                self.target_scale = 2.0

    
    def handle_keypress(self, key):
        # Управление с клавиатуры
        if key == pygame.K_SPACE:
            self.is_paused = not self.is_paused
            self.buttons['start_pause']['text'] = 'Start' if self.is_paused else 'Pause'
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            self.change_zoom(plus=True)
        elif key == pygame.K_MINUS:
            self.change_zoom(plus=False)
        elif key == pygame.K_UP:
            self.change_speed(up=True)
        elif key == pygame.K_DOWN:
            self.change_speed(up=False)
        elif key == pygame.K_r:
            self.camera_x = self.window_width // 2
            self.camera_y = self.window_height // 2
            self.target_scale = 1.0
            self.follow_planet = None

    def change_speed(self, up=True):
        speed_levels = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 40, 50, 80, 100]
        
        if up:
            # Находим следующую скорость в списке
            for speed in speed_levels:
                if speed > self.time_scale:
                    self.time_scale = speed
                    return
            # Если уже на максимуме, остаемся на месте
            if self.time_scale < speed_levels[-1]:
                self.time_scale = speed_levels[-1]
        else:
            # Находим предыдущую скорость в списке
            for speed in reversed(speed_levels):
                if speed < self.time_scale:
                    self.time_scale = speed
                    return
            # Если уже на минимуме, остаемся на месте
            if self.time_scale > speed_levels[0]:
                self.time_scale = speed_levels[0]

    def change_zoom(self, plus=True):
        zoom_levels = [0.01, 0.05, 0.1, 0.5, 1, 2, 5, 8]

        if plus:
            for zoom in zoom_levels:
                if zoom > self.target_scale:
                    self.target_scale = zoom
                    return
            # Если уже на максимуме, остаемся на месте
            if self.target_scale < zoom_levels[-1]:
                self.target_scale = zoom_levels[-1]
        else:
            for zoom in reversed(zoom_levels):
                if zoom < self.target_scale:
                    self.target_scale = zoom
                    return
            # Если уже на минимуме, остаемся на месте
            if self.target_scale > zoom_levels[0]:
                self.target_scale = zoom_levels[0]