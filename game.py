import pygame
import math
import sys
import os
import random

pygame.init()

info_monitoru = pygame.display.Info()
sirka = info_monitoru.current_w
vyska = info_monitoru.current_h

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
        
    return os.path.join(slozka, "assets", jmeno_souboru)


okno = pygame.display.set_mode((sirka, vyska))
pygame.display.set_caption("Hello world")
textures = {
    "normal": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Spaceship.png")).convert_alpha(), 15),
    "forward1": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Forward1.png")).convert_alpha(), 15),
    "forward2": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Forward2.png")).convert_alpha(), 15),
    "forward3": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Forward3.png")).convert_alpha(), 15),
    "forward4": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Forward4.png")).convert_alpha(), 15),
    "forward5": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Forward5.png")).convert_alpha(), 15),
    "left": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Left.png")).convert_alpha(), 15),
    "right": pygame.transform.scale_by(pygame.image.load(assets("ship\ship1\Right.png")).convert_alpha(), 15),
    "enemy1": pygame.transform.scale_by(pygame.image.load(assets("enemies\enemy1\Enemy1.jpg")).convert_alpha(), 15),
}
textura = "normal"
objects = []

def draw(textura=None, x=0, y=0, uhel_lode=0, barva=(255, 255, 255)):
    if textura == None:
        #renderování textur
        for object in objects:
            if not isinstance(object[0], str):
                print("Chyba textury")
            elif object[0].startswith("&\\"):
                rotated_player = pygame.transform.rotate(textures[object[0][2:]], object[3])
                new_player = rotated_player.get_rect(center=(object[1], object[2]))
                okno.blit(rotated_player, new_player)
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
        objects.append((textura, x, y, uhel_lode, barva))

def colison(enemy_texture, enemy_x, enemy_y, enemy_angel, laser_x, laser_y, laser_angle):
        enemy_img = pygame.transform.rotate(textures[enemy_texture], enemy_angel)
        enemy_mask = pygame.mask.from_surface(enemy_img)
        laser_surf = pygame.Surface((5, 20), pygame.SRCALPHA)
        pygame.draw.rect(laser_surf, (255, 0, 0), (0, 0, 5, 20))
        laser_img = pygame.transform.rotate(laser_surf, laser_angle)
        laser_mask = pygame.mask.from_surface(laser_img)
        offset_x = (laser_x - laser_img.get_width()//2) - (enemy_x - enemy_img.get_width()//2)
        offset_y = (laser_y - laser_img.get_height()//2) - (enemy_y - enemy_img.get_height()//2)
        return enemy_mask.overlap(laser_mask, (offset_x, offset_y)) != None

#random stars
stars = []
for _ in range(200):
    stars.append((random.randint(-3000, 3000), random.randint(-3000, 3000), random.randint(5000, 10000)/10000))

lasers = []
lasery_k_vymazani = []
enemys_k_vymazani = []
enemies = [[0,0], [1000, 1000], [-1000, -1000], [1000, -1000], [-1000, 1000]]
bezi = True
last_animation_time1 = 0
last_turbo_time = 0
uhel_lode = 0
hodiny = pygame.time.Clock()
menu = True
escpressed = False
choosed_button = 0
big_big_font = pygame.font.Font(assets("fonts\press_start.ttf"), 100)
big_font = pygame.font.Font(assets("fonts\press_start.ttf"), 50)
retro_font = pygame.font.Font(assets("fonts\press_start.ttf"), 36)
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

while bezi:
    aktualni_cas = pygame.time.get_ticks()
    #when game is running, check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            bezi = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    menu = not menu
                if delete_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    #delete progress
                    pass
                if quit_rect.collidepoint(event.pos):  # Levé tlačítko myši
                    bezi = False

            #choosing of buttons by keys
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_UP or event.key == pygame.K_w):
                    if choosed_button >= 2:choosed_button -= 1
                    else: choosed_button = 3
                if (event.key == pygame.K_DOWN or event.key == pygame.K_s):
                    if choosed_button <= 2:choosed_button += 1
                    else: choosed_button = 1

            #keys
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_KP_ENTER or event.key == pygame.K_RETURN:
                    if choosed_button == 1:
                        menu = not menu
                    elif choosed_button == 2:
                        #delete progress
                        pass
                    elif choosed_button == 3:
                        bezi = False
    objects.clear()
    
    #stars
    for star in stars:
        star_distance = star[2]
        draw("$\\circle|" + str(star_distance*2), star[0] + x * star_distance + (sirka//2), star[1] + y * star_distance + (vyska//2))
    #lasers
    for laser in lasers:
        laser_x = laser[0] +x
        laser_y = laser[1] +y
        draw("$\\rect|5|20", laser_x, laser_y, laser[2] + 90, (255, 0, 0))
        laser[0] += math.cos(math.radians(laser[2])) * 20
        laser[1] += math.sin(math.radians(laser[2])) * -20
        if laser_x < -1000 or laser_x > sirka + 1000 or laser_y < -1000 or laser_y > vyska + 1000:
            lasers.remove(laser)
        else:
            
            draw("$\\rect|5|20", laser_x, laser_y, laser[2] + 90, (255, 0, 0))
    #enemies
    for enemy in enemies:
        direction = math.atan2(vyska // 2 - (enemy[1] +y), sirka // 2 - (enemy[0] +x))
        enemy_uhel = -math.degrees(direction) -90
        enemy[0] += math.cos(direction) * 2
        enemy[1] += math.sin(direction) * 2
        draw("&\\enemy1", enemy[0] +x, enemy[1] +y, enemy_uhel)
        for laser in lasers:
            if math.hypot(enemy[0] -laser[0], enemy[1] - laser[1]) < 200:
                if colison("enemy1", enemy[0], enemy[1], enemy_uhel, laser[0], laser[1], laser[2]):
                    if laser not in lasery_k_vymazani:
                        lasery_k_vymazani.append(laser)
                    if enemy not in enemys_k_vymazani:
                        enemys_k_vymazani.append(enemy)
    
    for laser in lasery_k_vymazani:
        if laser in lasers:
            lasers.remove(laser)
    for enemy in enemys_k_vymazani:
        if enemy in enemies:
            enemies.remove(enemy)

    #player
    if menu == False:
        #keys
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            lasers.append([sirka//2 -x, vyska//2 -y, uhel_lode ])
        if pygame.key.get_pressed()[pygame.K_a]:
            uhel_lode += 4
        if pygame.key.get_pressed()[pygame.K_d]:
            uhel_lode -= 4
        if pygame.key.get_pressed()[pygame.K_w] and pygame.key.get_pressed()[pygame.K_b] and last_turbo_time + 1000 < aktualni_cas:
            acc += 250
            last_turbo_time = aktualni_cas
        if pygame.key.get_pressed()[pygame.K_w]:
            acc += 0.1
            if pygame.key.get_pressed()[pygame.K_a]:
                textura = "right"
                if aktualni_cas - last_animation_time1 > 100:
                    textura = "forward" + str(random.randint(1, 5))
                accrotation += 2
            if pygame.key.get_pressed()[pygame.K_d]:
                textura = "left"
                if aktualni_cas - last_animation_time1 > 100:
                    textura = "forward" + str(random.randint(1, 5))
                accrotation -= 2
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
        accrotation *= 0.9
        acc *= 0.9

    #menu actions
    else:
        #mouse position
        mouse_pos = pygame.mouse.get_pos()
        if back_rect.collidepoint(mouse_pos):
            choosed_button = 1
        elif delete_rect.collidepoint(mouse_pos):
            choosed_button = 2
        elif quit_rect.collidepoint(mouse_pos):
            choosed_button = 3

    #vykreslování
    draw("&\\" + textura, sirka//2, vyska//2, uhel_lode)
    okno.fill((30, 30, 30))
    x -= velocity_x
    y += velocity_y
    draw()

    #non-menu
    if menu == False:
        #game is running
        text_menu = retro_font.render("menu", True, (255, 255, 255))
        menu_rect = text_menu.get_rect(center=(sirka//20, 50))
        okno.blit(text_menu, menu_rect)
    #menu
    else:
        velocity_x, velocity_y = 0, 0
        mouse_pos = pygame.mouse.get_pos()
        #menu 
        okno.blit(overlay, (0, 0))  # Vykreslení overlaye přes celé okno
        text = big_big_font.render("LASER beamer", True, (255, 255, 255))
        text_rect = text.get_rect(center=(sirka//2, vyska//15))
        okno.blit(text, text_rect)
        #back to game tlacitko
        if choosed_button == 1:
            text_back = big_font.render("back to game", True, (255, 255, 255))
            back_rect = text_back.get_rect(center=(sirka//2, vyska//15 + 150))
        else:
            text_back = retro_font.render("back to game", True, (255, 255, 255))
            back_rect = text_back.get_rect(center=(sirka//2, vyska//15 + 150))
        okno.blit(text_back, back_rect)
        #delete progress tlacitko
        if choosed_button == 2:
            text_delete = big_font.render("delete progress", True, (255, 0, 0))
            delete_rect = text_delete.get_rect(center=(sirka//2, vyska//15 + 250))
        else:
            text_delete = retro_font.render("delete progress", True, (255, 255, 255))
            delete_rect = text_delete.get_rect(center=(sirka//2, vyska//15 + 250))
        okno.blit(text_delete, delete_rect)
        #quit tlacitko
        if choosed_button == 3:
            text_quit = big_font.render("quit", True, (255, 255, 255))
            quit_rect = text_quit.get_rect(center=(sirka//2, vyska//15 + 350))
        else:
            text_quit = retro_font.render("quit", True, (255, 255, 255))
            quit_rect = text_quit.get_rect(center=(sirka//2, vyska//15 + 350))
        okno.blit(text_quit, quit_rect)

    #omezovac snímků za sekundu
    pygame.display.flip()
    hodiny.tick(60)
pygame.quit()
sys.exit()
