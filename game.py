import pygame
import math
import sys
import os
import random
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
def refresh_screen(pygame_resize : str = "RESIZABLE"):
    global sirka, vyska, okno, textures, big_big_font, big_font, retro_font, small_font, textura, overlay, fyzicke_okno, player_width, player_height, info_monitoru, laser_width, laser_height
    info_monitoru = pygame.display.Info()

    okno = pygame.display.set_mode((sirka, vyska), getattr(pygame, pygame_resize))
    pygame.display.set_caption("LASER beamer")
    textures = {
        "normal": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Spaceship.png")).convert_alpha(), 15*sirka/2560),
        "forward1": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward1.png")).convert_alpha(), 15*sirka/2560),
        "forward2": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward2.png")).convert_alpha(), 15*sirka/2560),
        "forward3": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward3.png")).convert_alpha(), 15*sirka/2560),
        "forward4": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward4.png")).convert_alpha(), 15*sirka/2560),
        "forward5": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Forward5.png")).convert_alpha(), 15*sirka/2560),
        "left": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Left.png")).convert_alpha(), 15*sirka/2560),
        "right": pygame.transform.scale_by(pygame.image.load(assets("ship/ship1/Right.png")).convert_alpha(), 15*sirka/2560),
        "sawer": pygame.transform.scale_by(pygame.image.load(assets("enemies/sawer/sawer.png")).convert_alpha(), 15*sirka/2560),
        "healthbar": pygame.transform.scale_by(pygame.image.load(assets("healthbar/healthbar.png")).convert_alpha(), 4*sirka/2560)
    }
    big_big_font = pygame.font.Font(assets("fonts/press_start.ttf"), 100 * sirka // 2560)
    big_font = pygame.font.Font(assets("fonts/press_start.ttf"), 50*sirka//2560)
    retro_font = pygame.font.Font(assets("fonts/press_start.ttf"), 36*sirka//2560)
    small_font = pygame.font.Font(assets("fonts/press_start.ttf"), 15*sirka//2560)
    overlay = pygame.Surface((sirka, vyska), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    player_width = textures["normal"].get_width()
    player_height = textures["normal"].get_height()
    fyzicke_okno = Window.from_display_module()

    # Používáme dopředná lomítka pro bezproblémový běh na Windows i Linuxu
    not_png_file = 0
    for i, name in enumerate(os.listdir(assets("enemies/sawer/saws"))):
        if name.endswith(".png"):
            relativni_cesta_souboru = os.path.join("enemies/sawer/saws", name)
            textures["saws" + str(i - not_png_file)] = pygame.transform.scale_by(
                pygame.image.load(assets(relativni_cesta_souboru)).convert_alpha(), 15*sirka/2560
            )
        else:
            not_png_file += 1
            print(f"File {name} is not a PNG file and will be skipped.")
    not_png_file = 0
    for i, name in enumerate(os.listdir(assets("healthbar/lasers"))):
        if name.endswith(".png"):
            relativni_cesta_souboru = os.path.join("healthbar/lasers", name)
            textures[name] = pygame.transform.scale_by(
                pygame.image.load(assets(relativni_cesta_souboru)).convert_alpha(), 15*sirka/2560
            )
        else:
            not_png_file += 1
            print(f"File \"{name}\" is not a PNG file and will be skipped.")
    not_png_file = 0
    for i, name in enumerate(os.listdir(assets("enemies/sawer/trays"))):
        if name.endswith(".png"):
            relativni_cesta_souboru = os.path.join("enemies/sawer/trays", name)
            textures["trays" + str(i - not_png_file)] = pygame.transform.scale_by(
                pygame.image.load(assets(relativni_cesta_souboru)).convert_alpha(), 15*sirka/2560
            )
        else:
            not_png_file += 1
            print(f"File \"{name}\" is not a PNG file and will be skipped.")

    laser_width = textures["red_laser_0.png"].get_width()
    laser_height = textures["red_laser_0.png"].get_height()
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
                    rotated_player = pygame.transform.rotate(textures[object[0][2:]], object[3])
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

def colison(enemy_texture, enemy_x, enemy_y, enemy_angel, laser_x, laser_y, laser_angle=0, laser_length=1, laser_width=1, laser_color=(255, 0, 0), laser_texture=None):
        enemy_img = pygame.transform.rotate(textures[enemy_texture], enemy_angel)
        enemy_mask = pygame.mask.from_surface(enemy_img)
        if laser_texture == None:
            laser_surf = pygame.Surface((laser_width, laser_length), pygame.SRCALPHA)
            pygame.draw.rect(laser_surf, laser_color, (0, 0, laser_width, laser_length))
            laser_img = pygame.transform.rotate(laser_surf, laser_angle)
            laser_mask = pygame.mask.from_surface(laser_img)
        else:
            laser_img = pygame.transform.rotate(textures[laser_texture], laser_angle)
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
            aktualni_cas = pygame.time.get_ticks()
            if menu == False:
                if cooldown_time <= 0:
                    ratio = 1
                else:
                    ratio = (aktualni_cas - last_used_time) / (cooldown_time)
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

#random stars
stars = []
for _ in range(200):
    stars.append((random.randint(-3000, 3000), random.randint(-3000, 3000), random.randint(5000, 10000)/10000))

lasers = []
lasery_k_vymazani = []
enemies_k_vymazani = []
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
max_health = 50
health = max_health
space_pressed = False
sawcounter = 0
menu_time = 0
enemy_spawn_time = 0
start_laser_time = 0
hold_laser_index = 0
range_hold_space = 30
locked_position = False
hold_e_action = False
e_cooldown = 0
sawindex = 0
traycounter = 0
trayindex = 0
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
    aktualni_cas = pygame.time.get_ticks()

    if menu == True and was_menu == False:
        open_menu_time = aktualni_cas
        was_menu = True
    if menu == False and was_menu == True:
        time_in_menu = aktualni_cas - open_menu_time
        last_used_time += time_in_menu
        last_turbo_time += time_in_menu
        last_animation_time1 += time_in_menu
        start_laser_time += time_in_menu
        enemy_spawn_time += time_in_menu
        sawcounter += time_in_menu
        traycounter += time_in_menu
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
        #localization of potentional laser
        laser_hypotenuse = ((player_height / 2) + (laser_height / 2))*4.5
        laser_x = (math.cos(math.radians(uhel_lode)) * laser_hypotenuse) + (sirka // 2 )
        laser_y = (0 - math.sin(math.radians(uhel_lode)) * laser_hypotenuse) + (vyska // 2 )
        #keys
        if pygame.key.get_pressed()[pygame.K_p]:
            cooldown(5000, aktualni_cas)
        if pygame.key.get_pressed()[pygame.K_SPACE] and space_pressed == False and aktualni_cas > last_used_time + cooldown_time:
            space_pressed = True
            hold_laser = False
            start_laser_time = aktualni_cas
        if pygame.key.get_pressed()[pygame.K_SPACE] and space_pressed == True and aktualni_cas - start_laser_time > 200 and aktualni_cas > last_used_time + cooldown_time:
            locked_position = True
            textura = "normal"
        if pygame.key.get_pressed()[pygame.K_SPACE] == True and space_pressed == True and hold_laser_index < range_hold_space and aktualni_cas - start_laser_time > 1000 and aktualni_cas > last_used_time + cooldown_time:
            cooldown(2000, aktualni_cas)
            hold_laser = True
            while hold_laser_index < range_hold_space:
                axe_shift = 0 - range_hold_space/2 + hold_laser_index
                hold_laser_index += 10
                axe_shift_hypotense = 2 * (math.sin(math.radians(axe_shift/2)) * (laser_width / 2))
                relative_axe_shift = (180 + axe_shift) / 2 + uhel_lode
                x_shift = math.cos(math.radians(relative_axe_shift)) * axe_shift_hypotense
                y_shift = math.sin(math.radians(relative_axe_shift)) * axe_shift_hypotense
                relative_laser_x, relative_laser_y, relative_laser_angle = laser_x + x_shift, laser_y - y_shift, uhel_lode - 90 + axe_shift
                lasers.append([relative_laser_x, relative_laser_y, relative_laser_angle, 2, "blue", 0, aktualni_cas, relative_laser_angle])
        if pygame.key.get_pressed()[pygame.K_SPACE] == False:
            if aktualni_cas - start_laser_time < 150 and space_pressed == True and hold_laser == False:
                cooldown(100, aktualni_cas)
                lasers.append([laser_x, laser_y, uhel_lode-90, 2, "red", 0, aktualni_cas, uhel_lode-90])
            if aktualni_cas - start_laser_time >= 1000:
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
            if pygame.key.get_pressed()[pygame.K_w] and pygame.key.get_pressed()[pygame.K_b] and last_turbo_time + 1000 < aktualni_cas:
                acc += 250
                last_turbo_time = aktualni_cas
            if pygame.key.get_pressed()[pygame.K_w]:
                acc += 0.1
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    acc += 0.2
                if pygame.key.get_pressed()[pygame.K_a]:
                    textura = "right"
                    if aktualni_cas - last_animation_time1 > 100:
                        textura = "forward" + str(random.randint(1, 5))
                    accrotation += 1
                if pygame.key.get_pressed()[pygame.K_d]:
                    textura = "left"
                    if aktualni_cas - last_animation_time1 > 100:
                        textura = "forward" + str(random.randint(1, 5))
                    accrotation -= 1
                elif aktualni_cas - last_animation_time1 > 50:
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
                    last_animation_time1 = aktualni_cas
            else: textura = "normal"

        uhel_lode += accrotation/5
        velocity_x = math.cos(math.radians(uhel_lode)) * acc
        velocity_y = math.sin(math.radians(uhel_lode)) * acc
        accrotation *= 0.93
        acc *= 0.93
    draw("&\\" + textura, sirka//2, vyska//2, uhel_lode, vrstva = 5)

    
    #stars
    for star in stars:
        star_distance = star[2]
        draw("$\\circle|" + str(star_distance*2), star[0] + x * star_distance + (sirka//2), star[1] + y * star_distance + (vyska//2))
    #lasers
#lasers
    lasers_rect = []
    for laser in lasers:

        if laser[6] + 100 < aktualni_cas:
            laser[5] += 1
        draw("&\\" + laser[4] + "_laser_" + str(laser[5]) + ".png", laser[0], laser[1], laser[2] + 90, vrstva=3)

        if laser[4] == "blue":
            locked_position = True
        else:
            locked_position = False

        lasers_rect.append(pygame.transform.rotate(pygame.Surface((200, 20)), laser[2] + 90).get_rect(center=(laser[0], laser[1])))
        if laser[5] >= 5:
            if laser not in lasery_k_vymazani:
                lasery_k_vymazani.append(laser)
                locked_position = False

    #enemies
    if enemy_spawn_time < aktualni_cas and menu == False and enemies.__len__() < 10:
        direction = random.randint(0,360)
        enx, eny = math.sin(direction) * (math.sqrt(sirka ** 2 + vyska ** 2) / 2), math.cos(direction) * (math.sqrt(sirka ** 2 + vyska ** 2) / 2)
        enemies.append([enx - x + sirka//2, eny - y + vyska//2 , 0, 5])
        enemy_spawn_time = aktualni_cas + 5000
    for enemy in enemies:
        entexture = "sawer"
        direction = math.atan2(vyska // 2 - (enemy[1] +y), sirka // 2 - (enemy[0] +x))
        enemy_uhel = enemy[2]
        enemyrect = pygame.transform.rotate(textures["sawer"], enemy_uhel).get_rect(center=(enemy[0] + x, enemy[1] + y))
        if menu == False:
            enemy_uhel += 1 if ((-math.degrees(direction) - enemy_uhel) + 180) % 360 - 180 > 10 else (-1 if ((-math.degrees(direction) - enemy_uhel) + 180) % 360 - 180 < -10 else 0)
        enemy[2] = enemy_uhel
        vzdalenost = math.hypot(enemy[0] - (sirka//2 - x), enemy[1] - (vyska//2 - y))
        if menu == False and vzdalenost  > 150:
            enemy[0] += math.cos(math.radians(-enemy_uhel)) * 0.8
            enemy[1] += math.sin(math.radians(-enemy_uhel)) * 0.8
        draw("&\\saws" + str(sawindex), enemy[0] +x, enemy[1] +y, enemy_uhel, vrstva=4)
        draw("&\\sawer", enemy[0] +x, enemy[1] +y, enemy_uhel, vrstva=6)
        draw("&\\trays" + str(trayindex), enemy[0] +x, enemy[1] +y, enemy_uhel, vrstva=6)

        #animation
        if sawcounter < aktualni_cas and menu == False:
            sawcounter = aktualni_cas + 100
            sawindex += 1
            if sawindex >= os.listdir(assets("enemies/sawer/saws")).__len__():
                sawindex = 0

        if traycounter < aktualni_cas and menu == False:
            traycounter = aktualni_cas + 100
            trayindex += 1
            if trayindex >= os.listdir(assets("enemies/sawer/trays")).__len__():
                trayindex = 0
        if vzdalenost <= 500 and menu == False:
            if colison("saws0", enemy[0], enemy[1], enemy_uhel, sirka//2 - x, vyska//2 - y, uhel_lode, laser_texture="normal")>0 and health >= 0:
                health -= 0.5 * colison("saws0", enemy[0], enemy[1], enemy_uhel, sirka//2 - x, vyska//2 - y, uhel_lode, laser_texture="normal") / 100
        colide_lasers = enemyrect.collidelistall(lasers_rect)
        uhlopricka = math.sqrt(textures[entexture].get_width() ** 2 + textures[entexture].get_height() ** 2)
        for index, laser in enumerate(lasers):
            if index in colide_lasers:
                print("laser " + str(index) + " colide")
                if enemy[3] > 0: 
                    if colison("sawer", enemy[0] + x, enemy[1] + y, enemy_uhel, laser[0], laser[1], laser[2] + 90, laser_texture="red_laser_" + str(laser[5]) + ".png") > 0:
                        enemy[3] -= laser[3]
                        print("enemy health: " + str(enemy[3]))
                        if laser not in lasery_k_vymazani:
                            lasery_k_vymazani.append(laser)
                        if enemy not in enemies_k_vymazani and enemy[3] <= 0:
                            enemies_k_vymazani.append(enemy)

    for laser in lasery_k_vymazani:
        if laser in lasers:
            lasers.remove(laser)
    for enemy in enemies_k_vymazani:
        if enemy in enemies:
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

    #status bar
    if health < 0 and menu == False:
        health = 0
        game_over = True
    text = retro_font.render(str(int(health)) + " / " + str(max_health), True, (255, 255, 255))
    rect = text.get_rect(center=(sirka - sirka//2, vyska - vyska//20))
    okno.blit(text, rect)
    rect_health_icon = textures["healthbar"].get_rect()
    rect_health_icon.centery = rect.centery
    rect_health_icon.left = rect.right + 10
    okno.blit(textures["healthbar"], rect_health_icon)
    rect_health_icon = textures["healthbar"].get_rect()
    rect_health_icon.centery = rect.centery
    rect_health_icon.right = rect.left - 10
    okno.blit(textures["healthbar"], rect_health_icon)
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
    #omezovac snímků za sekundu
    pygame.display.flip()
    hodiny.tick(50)
pygame.quit()
sys.exit()
