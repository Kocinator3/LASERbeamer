import pygame
import math
import sys
import os
import random
import json
import shapely
from pygame._sdl2.video import Window
from screeninfo import get_monitors

pygame.init()
monitor_index = 0
info_monitoru = pygame.display.Info()
sirka = 800
vyska = 500
monitor_kraje = get_monitors()[monitor_index]

def assets(jmeno_souboru):
    # 1. Běžíme jako normální skript v Pythonu (při programování)
    if not getattr(sys, 'frozen', False):
        slozka = os.path.dirname(__file__)
        return os.path.join(slozka, "assets", jmeno_souboru)

    # 2. Běžíme jako zkompilovaný .exe soubor
    cesta_k_exe = os.path.dirname(sys.executable)
    modovana_cesta = os.path.join(cesta_k_exe, "assets", jmeno_souboru)

    # Zkusíme zjistit, jestli hráč nevytvořil složku "assets" vedle .exe souboru
    if os.path.exists(modovana_cesta):
        return modovana_cesta # Našel se mód! Použijeme ho.
    
    # 3. Mód neexistuje, použijeme originální obrázky zabalené uvnitř .exe
    return os.path.join(sys._MEIPASS, "assets", jmeno_souboru)

with open(assets("polygons.json"), "r", encoding="utf-8") as file:
    polygon_hitboxes = json.load(file)

def refresh_screen(pygame_resize : str = "RESIZABLE"):
    global sirka, vyska, okno, textures, big_big_font, big_font, retro_font, small_font, textura, overlay, fyzicke_okno, player_width, player_height, info_monitoru, laser_width, laser_height, scale_ratio
    info_monitoru = pygame.display.Info()

    scale_ratio = 15*sirka//2560
    okno = pygame.display.set_mode((sirka, vyska), getattr(pygame, pygame_resize))
    pygame.display.set_caption("LASER beamer")
    textures = {
        "normal": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Spaceship.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "forward1": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward1.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "forward2": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward2.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "forward3": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward3.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "forward4": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward4.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "forward5": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward5.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "left": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Left.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "right": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Right.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "sawer": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("enemies/sawer/sawer.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)],
        "healthbar": [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets("healthbar/healthbar.png")).convert_alpha(), scale_ratio),angle) for angle in range(360)]
    }
    big_big_font = pygame.font.Font(assets("fonts/press_start.ttf"), 100 * sirka // 2560)
    big_font = pygame.font.Font(assets("fonts/press_start.ttf"), 50*sirka//2560)
    retro_font = pygame.font.Font(assets("fonts/press_start.ttf"), 36*sirka//2560)
    small_font = pygame.font.Font(assets("fonts/press_start.ttf"), 15*sirka//2560)
    overlay = pygame.Surface((sirka, vyska), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    player_width = textures["normal"][0].get_width()
    player_height = textures["normal"][0].get_height()
    fyzicke_okno = Window.from_display_module()


    # Používáme dopředná lomítka pro bezproblémový běh na Windows i Linuxu
    not_png_file = 0
    for i, name in enumerate(os.listdir(assets("enemies/sawer/saws"))):
        if name.endswith(".png"):
            relativni_cesta_souboru = os.path.join("enemies/sawer/saws", name)
            textures["saws" + str(i - not_png_file)] = [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets(relativni_cesta_souboru)).convert_alpha(), scale_ratio), angle) for angle in range(360)]
        else:
            not_png_file += 1
            print(f"File {name} is not a PNG file and will be skipped.")
    not_png_file = 0
    for i, name in enumerate(os.listdir(assets("healthbar/lasers"))):
        if name.endswith(".png"):
            relativni_cesta_souboru = os.path.join("healthbar/lasers", name)
            textures[name] = [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets(relativni_cesta_souboru)).convert_alpha(), scale_ratio), angle) for angle in range(360)]
        else:
            not_png_file += 1
            print(f"File \"{name}\" is not a PNG file and will be skipped.")
    not_png_file = 0
    for i, name in enumerate(os.listdir(assets("enemies/sawer/trails"))):
        if name.endswith(".png"):
            relativni_cesta_souboru = os.path.join("enemies/sawer/trails", name)
            textures["trails" + str(i - not_png_file)] = [pygame.transform.rotate(pygame.transform.scale_by(pygame.image.load(assets(relativni_cesta_souboru)).convert_alpha(), scale_ratio), angle) for angle in range(360)]
        else:
            not_png_file += 1
            print(f"File \"{name}\" is not a PNG file and will be skipped.")

    laser_width = textures["red_laser_0.png"][0].get_width()
    laser_height = textures["red_laser_0.png"][0].get_height()
    textura = "normal"

refresh_screen()

objects = []
debug = False

def draw(textura=None, x=0, y=0, uhel_lode=0, barva=(255, 255, 255), vrstva=0):
    global objects, debug
    if textura == None:
        #renderování textur
        for i in range(len(objects)):
            for object in objects[i]:
                if not isinstance(object[0], str):
                    print("Chyba textury")
                elif object[0].startswith("&\\"):
                    rotated_player = textures[object[0][2:]][int(object[3])]
                    new_player = rotated_player.get_rect(center=(object[1], object[2]))
                    okno.blit(rotated_player, new_player)
                    if debug:
                        pygame.draw.rect(okno, (0, 255, 0), new_player, 2)
                        highlight = pygame.Surface((new_player.width, new_player.height), pygame.SRCALPHA)
                        highlight.fill((0, 255, 0, 10))
                        okno.blit(highlight, new_player.topleft)
                elif object[0].startswith("$\\"):
                    parts = object[0][2:].split("|")
                    if parts[0] == "circle":
                        pygame.draw.circle(okno, object[4], (object[1], object[2]), float(parts[1]))
                    if parts[0] == "rect":
                        rect_surface = pygame.Surface((float(parts[1]), float(parts[2])), pygame.SRCALPHA)
                        pygame.draw.rect(rect_surface, object[4], (0, 0, float(parts[1]), float(parts[2])))
                        rotated_rect = pygame.transform.rotate(rect_surface, object[3])
                        new_rect = rotated_rect.get_rect(center=(object[1], object[2]))
                        okno.blit(rotated_rect, new_rect)
                else: pass
    else: 
        objects[vrstva].append((textura, x, y, uhel_lode, barva))

def collison(enemy_texture, enemy_x, enemy_y, enemy_angle, laser_x, laser_y, laser_angle=0, laser_length=1, laser_width=1, laser_color=(255, 0, 0), laser_texture=None):
        enemy_img = textures[enemy_texture][int(enemy_angle)]
        enemy_mask = pygame.mask.from_surface(enemy_img)
        if laser_texture == None:
            laser_surf = pygame.Surface((laser_width, laser_length), pygame.SRCALPHA)
            pygame.draw.rect(laser_surf, laser_color, (0, 0, laser_width, laser_length))
            laser_img = pygame.transform.rotate(laser_surf, laser_angle)
            laser_mask = pygame.mask.from_surface(laser_img)
        else:
            laser_img = textures[laser_texture][int(laser_angle)]
            laser_mask = pygame.mask.from_surface(laser_img)
        offset_x = int((laser_x - laser_img.get_width()//2) - (enemy_x - enemy_img.get_width()//2))
        offset_y = int((laser_y - laser_img.get_height()//2) - (enemy_y - enemy_img.get_height()//2))
        
        # 1. Zjistíme, kolik pixelů laseru a pily se fyzicky překrývá
        prekryv_pixelu = enemy_mask.overlap_area(laser_mask, (offset_x, offset_y))
        
        if prekryv_pixelu > 0:
            # 2. Zjistíme celkový počet neprůhledných pixelů pily (její "plochu")
            plocha_pily = enemy_mask.count()
            
            # 3. Vypočítáme, kolik procent pily bylo zasaženo
            procento_zasahu = (prekryv_pixelu / plocha_pily) * 100
            
            return procento_zasahu
        else:
            return 0 # Žádná kolize
        
cooldown_time = 1
last_used_time = 1
current_time = 1
        
def cooldown(cooldown_time_parameter = None, last_used_time_parameter = None):
    global cooldown_time, last_used_time, cooldownpar, ratio
    if cooldown_time_parameter == None and last_used_time_parameter == None:
        if cooldown_time <= 0:
            pass
        else:
            actual_time = pygame.time.get_ticks()
            if menu == False:
                if cooldown_time <= 0:
                    ratio = 1
                else:
                    ratio = (actual_time - last_used_time) / (cooldown_time)
            else: pass
                    
            num_rects = int(ratio * 10)
            if num_rects > 10:
                num_rects = 10
            elif num_rects < 0:
                num_rects = 0
                
            mezera = 15
            celkova_dostupna_sirka = rect_health_icon.left - vyska // 10 # 10px zleva a 10px k obrazku
            sirka_obdelniku = max((celkova_dostupna_sirka - (9 * mezera)) / 10, 1)
            green_rect = pygame.Surface((sirka_obdelniku, rect_health_icon.height), pygame.SRCALPHA)
            dark_green_rect = pygame.Surface((sirka_obdelniku, rect_health_icon.height), pygame.SRCALPHA)
            pygame.draw.rect(green_rect, (0, 255, 0, 125), (0, 0, sirka_obdelniku, rect_health_icon.height))
            pygame.draw.rect(dark_green_rect, (0, 100, 0, 100), (0, 0, sirka_obdelniku, rect_health_icon.height))
            
            # 1. Nakreslení "pozadí" - všech 10 tmavých čtverečků
            for i in range(10):
                x_pozice = vyska // 20  + i * (sirka_obdelniku + mezera)
                okno.blit(dark_green_rect, (x_pozice, rect_health_icon.top))
                
            # 2. Nakreslení "aktivních" čtverečků na vrch - překryjí ty tmavé
            for i in range(num_rects):
                x_pozice = vyska // 20  + i * (sirka_obdelniku + mezera)
                okno.blit(green_rect, (x_pozice, rect_health_icon.top))
                if i == num_rects - 1:
                    cooldownpar = False
    else:
        cooldownpar = True
        cooldown_time = cooldown_time_parameter
        last_used_time = last_used_time_parameter

max_health = 50
health = max_health

#classes

class Object:

    objects = []

    def __init__(self, coordinates, angle, texture_name):
        self.coordinates = pygame.math.Vector2(coordinates)
        self.angle = angle
        self.angle = self.angle % 360
        self.texture_name = texture_name
        self.last_angle = None
        self.rotated_object = None
        Object.objects.append(self)
    
    def draw(self, display):
        global x, y
        self.display_coordinates = self.coordinates + pygame.math.Vector2(x, y)
        
        if self.rotated_object is None or self.last_angle != int(self.angle):
            self.rotated_object = textures[self.texture_name][int(self.angle)]
            self.last_angle = int(self.angle)
            
        self.object_rect = self.rotated_object.get_rect(center=(self.display_coordinates))
        display.blit(self.rotated_object, self.object_rect)
        if debug:
            pygame.draw.rect(display, (0, 255, 0), self.object_rect, 2)
            highlight = pygame.Surface((self.object_rect.width, self.object_rect.height), pygame.SRCALPHA)
            highlight.fill((0, 255, 0, 10))
            display.blit(highlight, self.object_rect.topleft)
        if hasattr(self, "relative_hitbox") and self.relative_hitbox != None:
            if debug:
                min_x, min_y, max_x, max_y = self.relative_hitbox.bounds
                transparent_surface = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)
                shifted = [(bod[0] - min_x, bod[1] - min_y) for bod in self.relative_hitbox.exterior.coords]
                pygame.draw.polygon(transparent_surface, (50,50,200,80), shifted)
                pygame.draw.polygon(transparent_surface, (50,50,200,255), shifted, width=2)
                display.blit(transparent_surface, (min_x + x, min_y + y))


class CollisionAble(Object):

    collisionables = []

    def __init__(self, coordinates, angle, texture_name, polygon_hitbox):
        super().__init__(coordinates, angle, texture_name)
        self.hitbox = polygon_hitbox
        CollisionAble.collisionables.append(self)

    def update(self):
        rotated_hit = shapely.affinity.scale(shapely.affinity.rotate(self.hitbox, 0 - self.angle, origin=(0, 0)), xfact=scale_ratio, yfact=scale_ratio, origin=(0, 0))
        self.relative_hitbox = shapely.affinity.translate(rotated_hit, xoff=self.coordinates.x, yoff=self.coordinates.y)   
        self.collisions_list = []
        for i in CollisionAble.collisionables:
            if hasattr(i, "object_rect") and hasattr(self, "object_rect"):
                if self.object_rect.colliderect(i.object_rect) and getattr(i, "relative_hitbox", None) != None:
                    if self.relative_hitbox.intersects(i.relative_hitbox):
                        self.collisions_list.append(i)

    def draw(self, display):
        return super().draw(display)

                                

class Laser(CollisionAble):

    def __init__(self, coordinates, angle, name, polygon_hitbox, damage):
        global actual_time, velocity_x, velocity_y
        super().__init__(coordinates, angle, f"{name}_laser_0.png", polygon_hitbox)
        self.name = name
        self.damage = damage
        self.frame = 0
        self.cooldown = 100
        self.start = actual_time
        self.relative_hitbox = None

    def draw(self, display):
        global actual_time, menu
        if menu == False:
            if actual_time >= self.start + self.cooldown:
                self.frame += 1
                self.start = actual_time
                if self.frame > 5:
                    if self not in lasers_for_ereasing:
                        lasers_for_ereasing.append(self)
                else:
                    self.texture_name = f"{self.name}_laser_{self.frame}.png"
                    self.hitbox = self.__class__.hitboxes[self.frame -1]
        super().draw(display)

    def update(self, velocity, delta_angle, ship_center):
        self.coordinates += velocity
        offset = self.coordinates - ship_center
        offset = offset.rotate(-delta_angle)
        self.coordinates = ship_center + offset
        self.angle += delta_angle

class RedLaser(Laser):

    hitboxes = []

    for i in range(5):
        hitboxes.append(shapely.geometry.Polygon(polygon_hitboxes[f"laser_{i}"]))

    def __init__(self, coordinates, angle):
        super().__init__(coordinates, angle, "red", RedLaser.hitboxes[0], 2)

class BlueLaser(Laser):

    hitboxes = []

    for i in range(5):
        hitboxes.append(shapely.geometry.Polygon(polygon_hitboxes[f"laser_{i}"]))
        
    def __init__(self, coordinates, angle):
        super().__init__(coordinates, angle, "blue", BlueLaser.hitboxes[0], 3)


class Enemy(CollisionAble):

    enemies = []

    def __init__(self, coordinates, angle, texture_name, polygon_hitbox, health, speed, turning_speed):
        super().__init__(coordinates, angle, texture_name, polygon_hitbox)
        self.health = health
        self.speed = speed
        self.turning_speed = turning_speed
        Enemy.enemies.append(self)
    
    def update(self, position):
        self.target_vector = pygame.math.Vector2(position)
        self.target_direction = self.target_vector - self.coordinates
        target_angle = math.degrees(math.atan2(self.target_direction.y, self.target_direction.x))
        actual_angle = -self.angle
        diff = (target_angle - actual_angle + 180) % 360 - 180
        # turning clockwise or non-clockwise?
        if diff > 0:
            self.angle -= min(self.turning_speed, diff)
        elif diff < 0:
            self.angle += min(self.turning_speed, abs(diff))
        
        self.angle %= 360
        
        # movement
        new_direction = pygame.math.Vector2(1, 0).rotate(-self.angle)
        self.coordinates += new_direction * self.speed

        self.display_coordinates = self.coordinates + pygame.math.Vector2(x, y)
        if hasattr(self, "rotated_object") and self.rotated_object is not None:
            self.object_rect = self.rotated_object.get_rect(center=(self.display_coordinates))

        # collisions

        super().update()

        for i in self.collisions_list:
            if "Laser" in [ii.__name__ for ii in type(i).__mro__]:
                self.health -= i.damage
                if self not in enemies_for_ereasing and self.health <= 0:
                    enemies_for_ereasing.append(self)
                if i not in lasers_for_ereasing:
                    lasers_for_ereasing.append(i)
    
    def draw_all(cls, display):
        for enemy in cls.enemies:
            enemy.draw(display)
    
    @classmethod
    def update_all(cls, target_x, target_y):
        for enemy in cls.enemies:
            enemy.update(target_x, target_y)

class Sawer(Enemy):

    polygon_hitbox = shapely.geometry.Polygon(polygon_hitboxes["sawer"])
    sawers = []
    shared_saw_mask = None

    def __init__(self, coordinates, angle):
        super().__init__(coordinates, angle, "sawer", Sawer.polygon_hitbox, 5, 1, 4, )
        self.saw_count = os.listdir(assets("enemies/sawer/saws")).__len__()
        self.trail_count = os.listdir(assets("enemies/sawer/trails")).__len__()
        self.trailcounter = 0
        self.sawcounter = 0
        self.sawindex = 0
        self.trailindex = 0
        self.saw_texture = "saw0"
        self.trail_texture = "trail0"
        self.rotated_saw_vector = pygame.math.Vector2(0,0)
        Sawer.sawers.append(self)
    def draw(self, display):
        global health, x, y, textures
        self.display_coordinates = self.coordinates + pygame.math.Vector2(x, y)
        self.saw_offset = pygame.math.Vector2(
            (textures["sawer"][0].get_width() // 2) - (textures["saws0"][0].get_width() // 2), 
            0
        )

        #animating saws and trails

        if self.sawcounter < actual_time and menu == False:
            self.sawcounter = actual_time + 100
            self.sawindex += 1
        if self.sawindex >= self.saw_count:
            self.sawindex = 0
        self.saw_texture = f"saws{self.sawindex}"

        if self.trailcounter < actual_time and menu == False:
            self.trailcounter = actual_time + 100
            self.trailindex += 1
            if self.trailindex >= self.trail_count:
                self.trailindex = 0
        self.trail_texture = f"trails{self.trailindex}"

        #saws
        rotated_saw_offset = self.saw_offset.rotate(-self.angle)
        self.rotated_saw_vector = rotated_saw_offset + self.display_coordinates

        rotated_saw = textures[self.saw_texture][int(self.angle)]
        self.saw_rect = rotated_saw.get_rect(center=(self.rotated_saw_vector))
        display.blit(rotated_saw, self.saw_rect)
          
        if debug:
            pygame.draw.rect(display, (255, 0, 0), self.saw_rect, 2)
            highlight = pygame.Surface((self.saw_rect.width, self.saw_rect.height), pygame.SRCALPHA)
            highlight.fill((255, 0, 0, 10))
            display.blit(highlight, self.saw_rect.topleft)
                
        #trails
        rotated_trail = textures[self.trail_texture][int(self.angle)]
        new_object = rotated_trail.get_rect(center=(self.display_coordinates))
        display.blit(rotated_trail, new_object)
        if debug:
            pygame.draw.rect(display, (0, 0, 255), new_object, 2)
            highlight = pygame.Surface((new_object.width, new_object.height), pygame.SRCALPHA)
            highlight.fill((0, 0, 255, 10))
            display.blit(highlight, new_object.topleft)

        super().draw(display)


player = []
class Player(CollisionAble):

    def __init__(self, texture, polygon_hitbox, health, speed, damage_multiplier):
        global player
        super().__init__((sirka//2, vyska//2), 0, texture, polygon_hitbox)
        player = []
        self.health = health
        self.speed = speed
        self.damage_multiplier = damage_multiplier
        player.append(self)

    def update(self):
        self.angle += self.accrotation

#random stars
stars = []
for _ in range(200):
    stars.append((random.randint(-3000, 3000), random.randint(-3000, 3000), random.randint(5000, 10000)/10000))

lasers = []
lasers_for_ereasing = []
enemies_for_ereasing = []
enemies = []
was_menu = False 
bezi = True
last_animation_time1 = 0
last_turbo_time = 0
uhel_lode = 0
game_over = False
sure = False
cooldownpar = False
ratio = 0
space_pressed = False
sawcounter = 0
trailcounter = 0
menu_time = 0
enemy_spawn_time = 0
start_laser_time = 0
hold_laser_index = 0
range_hold_space = 30
locked_position = False
hold_e_action = False
e_cooldown = 0
sawindex = 0
hodiny = pygame.time.Clock()
menu = True
escpressed = False
choosed_button = 0
accrotation = 0
acc = 0
x = 0
y = 0
velocity_x = 0
velocity_y = 0

#overlay settings
overlay = pygame.Surface((sirka, vyska), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 150))  # Poloprůhledný černý overlay hodnota [3] je průhlednost (0-255)


#pre start nececeratiess

rotated_player = pygame.Rect(0, 0, 0, 0)
new_player = pygame.Rect(0, 0, 0, 0)
menu_rect = pygame.Rect(0, 0, 0, 0)
quit_rect = pygame.Rect(0, 0, 0, 0)
back_rect = pygame.Rect(0, 0, 0, 0)
delete_rect = pygame.Rect(0, 0, 0, 0)
yes_rect = pygame.Rect(0, 0, 0, 0)
no_rect = pygame.Rect(0, 0, 0, 0)

while bezi:
    actual_time = pygame.time.get_ticks()

    if menu == True and was_menu == False:
        open_menu_time = actual_time
        was_menu = True
    if menu == False and was_menu == True:
        time_in_menu = actual_time - open_menu_time
        last_used_time += time_in_menu
        last_turbo_time += time_in_menu
        last_animation_time1 += time_in_menu
        start_laser_time += time_in_menu
        enemy_spawn_time += time_in_menu
        sawcounter += time_in_menu
        trailcounter += time_in_menu
        was_menu = False
    
    #when game is running, check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            bezi = False
        if event.type == pygame.VIDEORESIZE:
            sirka, vyska = event.size
            refresh_screen()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                debug = not debug
            if event.key == pygame.K_F11:
                if okno.get_width() == pygame.display.get_desktop_sizes()[monitor_index][0] and okno.get_height() == pygame.display.get_desktop_sizes()[monitor_index][1]:
                    sirka, vyska = bf_sirka, bf_vyska
                    fyzicke_okno.position = bf_monitor_position
                    refresh_screen()
                else:
                    bf_monitor_position = fyzicke_okno.position
                    fyzicke_okno.position = (monitor_kraje.x, monitor_kraje.y)
                    bf_sirka, bf_vyska = sirka, vyska
                    sirka, vyska = pygame.display.get_desktop_sizes()[monitor_index]
                    refresh_screen()
            if event.key == pygame.K_ESCAPE and game_over == False:
                menu = not menu
                choosed_button = 0
        #non-menu actions
        if menu == False:
            #mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and menu_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    menu = not menu
        #menu actions
        else:
            #mouse
            if event.type == pygame.MOUSEBUTTONDOWN and not sure:
                if back_rect.collidepoint(event.pos) and not game_over:  # Levé tlačítko myši
                    menu = not menu
                if delete_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    #delete progress
                    sure = True
                if quit_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    bezi = False
            elif event.type == pygame.MOUSEBUTTONDOWN and sure:
                if yes_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    reset = True
                    sure = False
                if no_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    sure = False

            #choosing of buttons by keys
            if event.type == pygame.KEYDOWN and not sure:
                if (event.key == pygame.K_UP or event.key == pygame.K_w):
                    if choosed_button >= 2:choosed_button -= 1
                    else: choosed_button = 3
                if (event.key == pygame.K_DOWN or event.key == pygame.K_s):
                    if choosed_button <= 2:choosed_button += 1
                    else: choosed_button = 1
            elif event.type == pygame.KEYDOWN and sure:
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a):
                    choosed_button = 1
                if (event.key == pygame.K_RIGHT or event.key == pygame.K_d):
                    choosed_button = 2

            #keys
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_KP_ENTER or event.key == pygame.K_RETURN and not sure:
                    if choosed_button == 1 and not game_over and not sure:   
                        menu = not menu
                    elif choosed_button == 2:
                        #delete progress
                        sure = True
                    elif choosed_button == 3:
                        bezi = False
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER and sure:
                    if choosed_button == 1:   
                        reset = True
                        sure = False
                    elif choosed_button == 2:
                        sure = False
    objects.clear()
    for i in range(11):
        objects.append([])
    
    if menu == False:
    #player
        old_direction = uhel_lode
        #localization of potentional laser
        laser_hypotenuse = ((player_height / 2) + (laser_height / 2))*4.5
        laser_x = (math.cos(math.radians(uhel_lode)) * laser_hypotenuse) + (sirka // 2 - x)
        laser_y = (0 - math.sin(math.radians(uhel_lode)) * laser_hypotenuse) + (vyska // 2 - y)
        #keys
        if pygame.key.get_pressed()[pygame.K_p]:
            cooldown(5000, actual_time)
        if pygame.key.get_pressed()[pygame.K_SPACE] and space_pressed == False and actual_time > last_used_time + cooldown_time:
            space_pressed = True
            hold_laser = False
            start_laser_time = actual_time
        if pygame.key.get_pressed()[pygame.K_SPACE] and space_pressed == True and actual_time - start_laser_time > 200 and actual_time > last_used_time + cooldown_time:
            locked_position = False
            textura = "normal"
        if pygame.key.get_pressed()[pygame.K_SPACE] == True and space_pressed == True and hold_laser_index < range_hold_space and actual_time - start_laser_time > 1000 and actual_time > last_used_time + cooldown_time:
            cooldown(2000, actual_time)
            hold_laser = True
            while hold_laser_index < range_hold_space:
                axe_shift = 0 - range_hold_space/2 + hold_laser_index
                hold_laser_index += 10
                axe_shift_hypotense = 2 * (math.sin(math.radians(axe_shift/2)) * (laser_width / 2))
                relative_axe_shift = (180 + axe_shift) / 2 + uhel_lode
                x_shift = math.cos(math.radians(relative_axe_shift)) * axe_shift_hypotense
                y_shift = math.sin(math.radians(relative_axe_shift)) * axe_shift_hypotense
                relative_laser_x, relative_laser_y, relative_laser_angle = laser_x + x_shift, laser_y - y_shift, uhel_lode + axe_shift
                lasers.append(BlueLaser((relative_laser_x, relative_laser_y), relative_laser_angle))
        if pygame.key.get_pressed()[pygame.K_SPACE] == False:
            if actual_time - start_laser_time < 150 and space_pressed == True and hold_laser == False:
                cooldown(100, actual_time)
                lasers.append(RedLaser((laser_x, laser_y), uhel_lode))
            if actual_time - start_laser_time >= 1000:
                locked_position = False
            space_pressed = False
            hold_laser_index = 0
        if not pygame.key.get_pressed()[pygame.K_SPACE] :
            space_pressed = False
        if locked_position == False:
            if pygame.key.get_pressed()[pygame.K_a]:
                uhel_lode += 4
            if pygame.key.get_pressed()[pygame.K_d]:
                uhel_lode -= 4
            if pygame.key.get_pressed()[pygame.K_w] and pygame.key.get_pressed()[pygame.K_b] and last_turbo_time + 1000 < actual_time:
                acc += 250
                last_turbo_time = actual_time
            if pygame.key.get_pressed()[pygame.K_w]:
                acc += 0.1
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    acc += 0.2
                if pygame.key.get_pressed()[pygame.K_a]:
                    textura = "right"
                    if actual_time - last_animation_time1 > 100:
                        textura = "forward" + str(random.randint(1, 5))
                    accrotation += 1
                if pygame.key.get_pressed()[pygame.K_d]:
                    textura = "left"
                    if actual_time - last_animation_time1 > 100:
                        textura = "forward" + str(random.randint(1, 5))
                    accrotation -= 1
                elif actual_time - last_animation_time1 > 50:
                    if textura == "forward1":
                        textura = "forward2"
                    elif textura == "forward2":
                        textura = "forward3"
                    elif textura == "forward3":
                        textura = "forward4"
                    elif textura == "forward4":
                        textura = "forward5"
                    elif textura == "forward5":
                        textura = "forward1"
                    else: textura = "forward" + str(random.randint(1, 5))
                    last_animation_time1 = actual_time
            else: textura = "normal"

        uhel_lode += accrotation/5
        uhel_lode %= 360
        velocity_x = math.cos(math.radians(uhel_lode)) * acc
        velocity_y = math.sin(math.radians(uhel_lode)) * acc
        accrotation *= 0.93
        acc *= 0.93
        ship_center = pygame.math.Vector2(sirka//2 - x, vyska//2 - y)
        direction_shif = uhel_lode - old_direction
    draw("&\\" + textura, sirka//2, vyska//2, uhel_lode, vrstva = 5)

    #stars
    for star in stars:
        star_distance = star[2]
        draw("$\\circle|" + str(star_distance*2), star[0] + x * star_distance + (sirka//2), star[1] + y * star_distance + (vyska//2))

    #enemies
    if enemy_spawn_time < actual_time and menu == False and enemies.__len__() < 10:
        direction = random.randint(0,360)
        spawn_circle = pygame.math.Vector2(sirka//2, 0).rotate(direction) + ship_center
        enemies.append(Sawer(spawn_circle, direction - 180))
        enemy_spawn_time = actual_time + random.randint(1500,6000)

    if not menu:
        for laser in lasers:
            laser.update(pygame.math.Vector2(velocity_x, -velocity_y), direction_shif, ship_center)
        for enemy in enemies:
            enemy.update((sirka//2 - x, vyska//2 - y))

    for laser in lasers_for_ereasing:
        if laser in lasers:
            lasers.remove(laser)
    for enemy in enemies_for_ereasing:
        if enemy in enemies:
            kill(enemy)
            enemies.remove(enemy)

    #menu actions
    else:
        #mouse position
        if not sure:
            mouse_pos = pygame.mouse.get_pos()
            if back_rect.collidepoint(mouse_pos):
                choosed_button = 1
            elif delete_rect.collidepoint(mouse_pos):
                choosed_button = 2
            elif quit_rect.collidepoint(mouse_pos):
                choosed_button = 3
        else:
            mouse_pos = pygame.mouse.get_pos()
            if yes_rect.collidepoint(mouse_pos):
                choosed_button = 1
            elif no_rect.collidepoint(mouse_pos):
                choosed_button = 2

    #vykreslování
    okno.fill((30, 30, 30))
    x -= velocity_x
    y += velocity_y
    draw()

    for enemy in enemies:
        enemy.draw(okno)
    for laser in lasers:
        laser.draw(okno)

    #status bar
    if health < 0 and menu == False:
        health = 0
        game_over = True
    text = retro_font.render(str(int(health)) + " / " + str(max_health), True, (255, 255, 255))
    rect = text.get_rect(center=(sirka - sirka//2, vyska - vyska//20))
    okno.blit(text, rect)
    rect_health_icon = textures["healthbar"][0].get_rect()
    rect_health_icon.centery = rect.centery
    rect_health_icon.left = rect.right + 10
    okno.blit(textures["healthbar"][0], rect_health_icon)
    rect_health_icon = textures["healthbar"][0].get_rect()
    rect_health_icon.centery = rect.centery
    rect_health_icon.right = rect.left - 10
    okno.blit(textures["healthbar"][0], rect_health_icon)
    cooldown()

    #non-menu
    if menu == False and game_over == False:
        #game is running
        text_menu = retro_font.render("menu", True, (255, 255, 255))
        menu_rect = text_menu.get_rect(x=sirka//20, y=vyska//20)
        okno.blit(text_menu, menu_rect)
    else:
        velocity_x, velocity_y = 0, 0
        okno.blit(overlay, (0, 0))  # Vykreslení overlaye přes celé okno

        #game over
        if game_over:
            menu = True
            health = 0
            text_game_over = big_big_font.render("GAME OVER", True, (255, 0, 0))
            game_over_rect = text_game_over.get_rect(center=(sirka//2, vyska//4))
            okno.blit(text_game_over, game_over_rect)
            first_button = vyska//2
        #menu
        else:
            text = big_big_font.render("LASER beamer", True, (255, 255, 255))
            text_rect = text.get_rect(center=(sirka//2, vyska//15 + 25))
            okno.blit(text, text_rect)
            first_button = vyska//15 + 150*vyska//1080

        #back to game tlacitko
        if choosed_button == 1 and game_over:
            text_back = retro_font.render("back to game", True, (130, 130, 130))
            back_rect = text_back.get_rect(center=(sirka//2, first_button))
        elif choosed_button == 1 and not game_over and not sure:
            text_back = big_font.render("back to game", True, (255, 255, 255))
            back_rect = text_back.get_rect(center=(sirka//2, first_button))
        else:
            text_back = retro_font.render("back to game", True, (255, 255, 255))
            back_rect = text_back.get_rect(center=(sirka//2, first_button))
        okno.blit(text_back, back_rect)

        #delete progress tlacitko
        if choosed_button == 2 or sure:
            text_delete = big_font.render("new game", True, (200, 200, 255))
            delete_rect = text_delete.get_rect(center=(sirka//2, first_button + 100*vyska/1080))
            text_delete_info = small_font.render("this will completly delete your progress", True, (255, 0, 0))
            delete_info_rect = text_delete_info.get_rect(center=(sirka//2, first_button + 150*vyska/1080))
            okno.blit(text_delete_info, delete_info_rect)
        else:
            text_delete = retro_font.render("new game", True, (255, 255, 255))
            delete_rect = text_delete.get_rect(center=(sirka//2, first_button + 100*vyska/1080))
        okno.blit(text_delete, delete_rect)

        #quit tlacitko
        if choosed_button == 3 and not sure:
            text_quit = big_font.render("quit", True, (255, 255, 255))
            quit_rect = text_quit.get_rect(center=(sirka//2, first_button + 200*vyska/1080))
        else:
            text_quit = retro_font.render("quit", True, (255, 255, 255))
            quit_rect = text_quit.get_rect(center=(sirka//2, first_button + 200*vyska/1080))
        okno.blit(text_quit, quit_rect)
        #are you sure
        if sure:
            okno.blit(overlay, (0, 0))  # Vykreslení overlaye přes celé okno
            text_sure = big_font.render("are you sure?", True, (255, 255, 255))
            text_sure_rect = text_sure.get_rect(center=(sirka//2, vyska//2 - 50*vyska/1080))
            okno.blit(text_sure, text_sure_rect)
            if choosed_button == 1:
                text_yes = big_font.render("yes", True, (150, 0, 0))
                yes_rect = text_yes.get_rect(center=(sirka//2 - 100, vyska//2 + 50*vyska/1080))
                text_no = retro_font.render("no", True, (255, 255, 255))
                no_rect = text_no.get_rect(center=(sirka//2 + 100, vyska//2 + 50*vyska/1080))
            elif choosed_button == 2:
                text_yes = retro_font.render("yes", True, (255, 255, 255))
                yes_rect = text_yes.get_rect(center=(sirka//2 - 100, vyska//2 + 50*vyska/1080))
                text_no = big_font.render("no", True, (0, 0, 150))
                no_rect = text_no.get_rect(center=(sirka//2 + 100, vyska//2 + 50*vyska/1080))
            okno.blit(text_yes, yes_rect)  
            okno.blit(text_no, no_rect)
    
    if debug:
        aktualni_fps = int(hodiny.get_fps())
        fps_text = retro_font.render(f"FPS: {aktualni_fps}", True, (0, 255, 0))
        fps_rect = fps_text.get_rect(topright=(sirka - 10, 10))
        okno.blit(fps_text, fps_rect)

    #omezovac snímků za sekundu
    pygame.display.flip()
    hodiny.tick(50)
pygame.quit()
sys.exit()
