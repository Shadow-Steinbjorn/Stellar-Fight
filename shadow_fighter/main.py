import pygame
from fighter import Fighter

pygame.init()

# create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shadow Fight")

# set framerate
clock = pygame.time.Clock()
FPS = 60

# define colours
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# define game variables
intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]  # player scores. [P1, P2]
round_over = False
ROUND_OVER_COOLDOWN = 2000

# define fighter variables
WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 56]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 107]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

# load background image
bg_image = pygame.image.load("assets/images/background/background.jpg").convert_alpha()

# load spritesheets
warrior_sheet = pygame.image.load("assets/images/warrior/Sprites/warrior.png").convert_alpha()
wizard_sheet = pygame.image.load("assets/images/wizard/Sprites/wizard.png").convert_alpha()

# load victory image
victory_img = pygame.image.load("assets/images/icons/victory.png").convert_alpha()

# define number of steps in each animation
WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

# define font
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)
menu_font = pygame.font.Font("assets/fonts/turok.ttf", 40)

# function for drawing text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# function for drawing background
def draw_bg():
    scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))

# function for drawing fighter health bars
def draw_health_bar(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, BLACK, (x, y, 400, 30))
    pygame.draw.rect(screen, WHITE, (x, y, 400 * ratio, 30))

# function to draw button
def draw_button(text, font, text_col, x, y, width, height):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, WHITE, button_rect)
    pygame.draw.rect(screen, BLACK, button_rect, 2)
    text_img = font.render(text, True, text_col)
    text_rect = text_img.get_rect(center=button_rect.center)
    screen.blit(text_img, text_rect)
    return button_rect

# create two instances of fighters
fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS)
fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS)

# game states
MAIN_MENU = 0
PLAYING = 1
GAME_OVER = 2
LEADERBOARD = 3

current_state = MAIN_MENU

# player data
username = "warrior"
personal_score = 30

# leaderboard data (you can expand this to read/write from a file)
leaderboard = [("warrior", 30)]

def reset_game():
    global fighter_1, fighter_2, score, intro_count, round_over
    fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS)
    fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS)
    score = [0, 0]
    intro_count = 3
    round_over = False

def update_leaderboard():
    global leaderboard
    leaderboard = sorted(leaderboard, key=lambda x: x[1], reverse=True)
    if len(leaderboard) > 10:
        leaderboard = leaderboard[:10]

# game loop
run = True
while run:
    clock.tick(FPS)

    # draw background
    draw_bg()

    if current_state == MAIN_MENU:
        # draw menu options
        play_button = draw_button("Play", menu_font, BLACK, 400, 200, 200, 50)
        leaderboard_button = draw_button("Leaderboard", menu_font, BLACK, 400, 300, 200, 50)
        quit_button = draw_button("Quit", menu_font, BLACK, 400, 400, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    current_state = PLAYING
                    reset_game()
                elif leaderboard_button.collidepoint(event.pos):
                    current_state = LEADERBOARD
                elif quit_button.collidepoint(event.pos):
                    run = False

    elif current_state == PLAYING:
        # show player stats
        draw_health_bar(fighter_1.health, 20, 20)
        draw_health_bar(fighter_2.health, 580, 20)
        draw_text("P1: " + str(score[0]), score_font, RED, 20, 60)
        draw_text("P2: " + str(score[1]), score_font, RED, 580, 60)

        # update countdown
        if intro_count <= 0:
            # move fighters
            fighter_1.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, fighter_2, round_over)
            fighter_2.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, fighter_1, round_over)
        else:
            # display count timer
            draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
            # update count timer
            if (pygame.time.get_ticks() - last_count_update) >= 1000:
                intro_count -= 1
                last_count_update = pygame.time.get_ticks()

        # update fighters
        fighter_1.update()
        fighter_2.update()

        # draw fighters
        fighter_1.draw(screen)
        fighter_2.draw(screen)

        # check for player defeat
        if round_over == False:
            if fighter_1.alive == False:
                score[1] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
            elif fighter_2.alive == False:
                score[0] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
        else:
            # display victory image
            screen.blit(victory_img, (360, 150))
            if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
                if score[0] == 3 or score[1] == 3:
                    current_state = GAME_OVER
                else:
                    round_over = False
                    intro_count = 3
                    fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS)
                    fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS)

        # event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

    elif current_state == GAME_OVER:
        # display final score
        draw_text("Final Score", menu_font, WHITE, 400, 200)
        draw_text(f"P1: {score[0]}  P2: {score[1]}", menu_font, WHITE, 400, 250)

        # update personal score
        if score[0] > score[1]:
            personal_score += 12
            result_text = "You Win!"
        else:
            personal_score -= 6
            result_text = "You Lose!"

        draw_text(result_text, menu_font, WHITE, 400, 300)
        draw_text(f"Personal Score: {personal_score}", menu_font, WHITE, 400, 350)

        # update leaderboard
        leaderboard = [entry for entry in leaderboard if entry[0] != username]
        leaderboard.append((username, personal_score))
        update_leaderboard()

        # draw back to menu button
        back_button = draw_button("Back to Menu", menu_font, BLACK, 400, 400, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    current_state = MAIN_MENU

    elif current_state == LEADERBOARD:
        draw_text("Leaderboard", menu_font, WHITE, 400, 100)
        for i, (name, score) in enumerate(leaderboard):
            draw_text(f"{i+1}. {name}: {score}", score_font, WHITE, 400, 150 + i * 40)

        back_button = draw_button("Back to Menu", menu_font, BLACK, 400, 500, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    current_state = MAIN_MENU

    # update display
    pygame.display.update()

# exit pygame
pygame.quit()