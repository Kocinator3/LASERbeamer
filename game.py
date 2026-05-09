import pygame
import data
import copy
import math
import sys
import os
import random

# Nastavení cesty k souborům
slozka = os.path.dirname(__file__)
def assets(jmeno_souboru):
    return os.path.join(slozka, "assets", jmeno_souboru)

pygame.init()

info_monitoru = pygame.display.Info()
sirka = info_monitoru.current_w
vyska = info_monitoru.current_h

okno = pygame.display.set_mode((sirka, vyska))
pygame.display.set_caption("Hello world")

normal = pygame.transform.scale_by(pygame.image.load(assets("spaceship.png")).convert_alpha(), 15)
forward1 = pygame.transform.scale_by(pygame.image.load(assets("forward1.png")).convert_alpha(), 15)
forward2 = pygame.transform.scale_by(pygame.image.load(assets("forward2.png")).convert_alpha(), 15)
left = pygame.transform.scale_by(pygame.image.load(assets("left.png")).convert_alpha(), 15)
right = pygame.transform.scale_by(pygame.image.load(assets("right.png")).convert_alpha(), 15)
textura = normal

#random stars
stars = []
for _ in range(200):
    stars.append((random.randint(-3000, 3000), random.randint(-3000, 3000)))

bezi = True
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

#obdelnik u obrazku
rect = textura.get_rect(center=(sirka//2, vyska//2))

#pre start nececeratiess
rotated_player = pygame.transform.rotate(textura, uhel_lode)
new_player = rotated_player.get_rect(center=rect.center)

menu_rect = pygame.Rect(0, 0, 0, 0)
quit_rect = pygame.Rect(0, 0, 0, 0)
back_rect = pygame.Rect(0, 0, 0, 0)
delete_rect = pygame.Rect(0, 0, 0, 0)

while bezi:
    aktualni_cas = pygame.time.get_ticks()
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

    
    #non-menu actions
    if menu == False:
        #keys
        if pygame.key.get_pressed()[pygame.K_a]:
            uhel_lode += 4
        elif pygame.key.get_pressed()[pygame.K_d]:
            uhel_lode -= 4
        if pygame.key.get_pressed()[pygame.K_w]:
            acc += 0.1
            if textura != forward1 and textura != forward2:
                textura = forward1
            elif pygame.key.get_pressed()[pygame.K_a]:
                textura = right
                accrotation += 2
            elif pygame.key.get_pressed()[pygame.K_d]:
                textura = left
                accrotation -= 2
            elif textura == forward1:
                textura = forward2
            elif textura == forward2:
                textura = forward1
        else: textura = normal

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
    okno.fill((30, 30, 30))
    x -= velocity_x
    y += velocity_y
    for star in stars:
        star_x = star[0] + x + (sirka//2)
        star_y = star[1] + y + (vyska//2)
        if 0 <= star_x <= sirka and 0 <= star_y <= vyska:
            pygame.draw.circle(okno, (255, 255, 255), (star_x, star_y), 2)
    rotated_player = pygame.transform.rotate(textura, uhel_lode)
    new_player = rotated_player.get_rect(center=rect.center)
    okno.blit(rotated_player, new_player)
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