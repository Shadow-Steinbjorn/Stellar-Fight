import pygame
from fighter import Fighter
import json
import os
import datetime
from stellar_sdk import Keypair
from stellar_integration import load_or_create_player_data, update_player_coins, get_balance, initialize_game_stellar_setup, setup_smart_contract
from guilds import load_guilds, save_guilds, load_guild_data, draw_checkbox

# Initialize Stellar setup
initialize_game_stellar_setup()

pygame.init()

# create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Stellar Fight")

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
NOT_ENOUGH_COINS = 4
GUILDS = 5
GUILD_HOME = 6
GUILD_SELECTION = 7
GUILD_AGREEMENT = 8

current_state = MAIN_MENU

# player data
username = "warrior"

# JSON file for persistent data
JSON_FILE = "game_data.json"

# Load guilds
guilds = load_guilds()
guild_data = load_guild_data()
for guild, data in zip(guilds, guild_data):
    guild.members = data["members"]
    guild.total_collected = data["total_collected"]
    guild.last_collection_date = datetime.date.fromisoformat(data["last_collection_date"])

# Load player data
player_data = load_or_create_player_data(username)
# Initialize player's guild
player_guild = None
agreement_checked = False

# Load data from JSON file or create default data
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
else:
    data = {
        "personal_score": 30,
        "wins": 0,
        "losses": 0,
        "win_streak": 0,
        "leaderboard": [("warrior", 30)]
    }

# Get data from loaded JSON
personal_score = data["personal_score"]
wins = data["wins"]
losses = data["losses"]
win_streak = data["win_streak"]
coins = get_balance(player_data["public_key"])
leaderboard = data["leaderboard"]

def save_data():
    data["personal_score"] = personal_score
    data["wins"] = wins
    data["losses"] = losses
    data["win_streak"] = win_streak
    data["leaderboard"] = leaderboard
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f)

def reset_game():
    global fighter_1, fighter_2, score, intro_count, round_over
    fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS)
    fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS)
    score = [0, 0]
    intro_count = 3
    round_over = False

def update_leaderboard():
    global leaderboard
    leaderboard = [entry for entry in leaderboard if entry[0] != username]
    leaderboard.append((username, personal_score))
    leaderboard = sorted(leaderboard, key=lambda x: x[1], reverse=True)
    if len(leaderboard) > 10:
        leaderboard = leaderboard[:10]

def calculate_score_increase():
    return min(18, 12 + win_streak)

def calculate_coin_reward():
    base_reward = 20
    streak_bonus = min(5, win_streak) * 2  # 2 extra coins per win streak, up to 5
    return base_reward + streak_bonus

# game loop
run = True
while run:
    clock.tick(FPS)

    # draw background
    draw_bg()

    if current_state == MAIN_MENU:
        update_done = False
        # Update coins display to use Stellar balance
        coins = get_balance(player_data["public_key"])
        # draw menu options
        draw_text(f"Coins: {coins}", menu_font, WHITE, 20, 20)
        play_button = draw_button("Play", menu_font, BLACK, 400, 200, 200, 50)
        leaderboard_button = draw_button("Leaderboard", menu_font, BLACK, 400, 300, 200, 50)
        guilds_button = draw_button("Guilds", menu_font, BLACK, 400, 400, 200, 50)
        quit_button = draw_button("Quit", menu_font, BLACK, 400, 500, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    if coins >= 15:
                        current_state = PLAYING
                        reset_game()
                    else:
                        current_state = NOT_ENOUGH_COINS
                elif leaderboard_button.collidepoint(event.pos):
                    current_state = LEADERBOARD
                elif guilds_button.collidepoint(event.pos):
                    if player_guild:
                        current_state = GUILD_HOME
                    else:
                        current_state = GUILD_SELECTION
                        agreement_checked = False
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
        draw_text("Final Score", menu_font, WHITE, 400, 150)
        draw_text(f"P1: {score[0]}  P2: {score[1]}", menu_font, WHITE, 400, 200)

        # update personal score and stats
        if score[0] > score[1] and update_done == False:
            update_done = True
            wins += 1
            win_streak += 1
            score_increase = calculate_score_increase()
            personal_score += score_increase
            coin_reward = calculate_coin_reward()
            # Update Stellar balance
            coins = update_player_coins(player_data["public_key"], coin_reward)
            result_text = f"You Win! +{score_increase} points, +{coin_reward} coins"
        elif score[0] < score[1] and update_done == False:
            update_done = True
            losses += 1
            win_streak = 0
            personal_score -= 6
            # Update Stellar balance
            coins = update_player_coins(player_data["public_key"], -15)
            result_text = "You Lose! -6 points, -15 coins"

        draw_text(result_text, menu_font, WHITE, 400, 250)
        draw_text(f"Personal Score: {personal_score}", menu_font, WHITE, 400, 300)
        draw_text(f"Wins: {wins}, Losses: {losses}", menu_font, WHITE, 400, 350)
        draw_text(f"Win Streak: {win_streak}", menu_font, WHITE, 400, 400)
        draw_text(f"Coins: {coins}", menu_font, WHITE, 400, 450)

        # update leaderboard
        update_leaderboard()

        # save data
        save_data()

        # draw back to menu button
        back_button = draw_button("Back to Menu", menu_font, BLACK, 400, 500, 200, 50)

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

    elif current_state == NOT_ENOUGH_COINS:
        # Update coins display to use Stellar balance
        coins = get_balance(player_data["public_key"])
        draw_text("Not Enough Coins!", menu_font, RED, 400, 200)
        draw_text(f"You need at least 15 coins to play.", menu_font, WHITE, 400, 250)
        draw_text(f"Current coins: {coins}", menu_font, WHITE, 400, 300)

        back_button = draw_button("Back to Menu", menu_font, BLACK, 400, 400, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    current_state = MAIN_MENU
    
    elif current_state == GUILD_SELECTION:
        draw_text("Choose a Guild", menu_font, WHITE, 400, 100)
        
        guild1_button = draw_button(guilds[0].name, menu_font, BLACK, 200, 200, 250, 50)
        guild2_button = draw_button(guilds[1].name, menu_font, BLACK, 550, 200, 250, 50)
        back_button = draw_button("Back to Menu", menu_font, BLACK, 400, 500, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if guild1_button.collidepoint(event.pos):
                    selected_guild = guilds[0]
                    current_state = GUILD_AGREEMENT
                    agreement_checked = False  # Reset agreement check when selecting a guild
                elif guild2_button.collidepoint(event.pos):
                    selected_guild = guilds[1]
                    current_state = GUILD_AGREEMENT
                    agreement_checked = False  # Reset agreement check when selecting a guild
                elif back_button.collidepoint(event.pos):
                    current_state = MAIN_MENU

    elif current_state == GUILD_AGREEMENT:
        draw_text("Guild Agreement", menu_font, WHITE, 400, 100)
        draw_text(f"Join {selected_guild.name}", menu_font, WHITE, 400, 150)
        draw_text("By joining this guild, you agree to donate", menu_font, WHITE, 400, 200)
        draw_text("10 tokens daily to the guild's cause.", menu_font, WHITE, 400, 250)
        
        draw_checkbox(screen, 350, 300, agreement_checked)
        draw_text("I agree to the terms", menu_font, WHITE, 380, 300)
        
        agree_button = draw_button("Join Guild", menu_font, BLACK, 400, 350, 200, 50)
        back_button = draw_button("Back", menu_font, BLACK, 400, 420, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(350, 300, 20, 20).collidepoint(event.pos):
                    agreement_checked = not agreement_checked
                elif agree_button.collidepoint(event.pos) and agreement_checked:
                    if coins >= 10:
                        player_account = Keypair.from_secret(player_data["secret_key"])
                        if setup_smart_contract(player_account, selected_guild.account, 10):
                            selected_guild.add_member(username)
                            update_player_coins(player_data["public_key"], -10)
                            coins = get_balance(player_data["public_key"])
                            player_guild = selected_guild
                            current_state = GUILD_HOME
                        else:
                            # Handle smart contract setup failure
                            print("Failed to set up smart contract. Please try again.")
                    else:
                        current_state = NOT_ENOUGH_COINS
                elif back_button.collidepoint(event.pos):
                    current_state = GUILD_SELECTION
                    agreement_checked = False  # Reset agreement check when going back

    elif current_state == GUILD_HOME:
        if player_guild:
            player_guild.daily_collection()
            player_guild.render(screen, menu_font)
            
            exit_guild_button = draw_button("Exit Guild", menu_font, BLACK, 300, 500, 200, 50)
            back_button = draw_button("Back to Menu", menu_font, BLACK, 550, 500, 200, 50)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if exit_guild_button.collidepoint(event.pos):
                        player_guild.remove_member(username)
                        player_guild = None
                        current_state = MAIN_MENU
                    elif back_button.collidepoint(event.pos):
                        current_state = MAIN_MENU
        else:
            current_state = GUILD_SELECTION

    # update display
    pygame.display.update()

# save data before quitting
save_data()
save_guilds(guilds)

# exit pygame
pygame.quit()