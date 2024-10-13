import pygame
import json
from datetime import datetime, timedelta
from stellar_sdk import Keypair
from stellar_integration import load_or_create_guild_account, setup_smart_contract, execute_daily_transfer, load_or_create_player_data

class Guild:
    def __init__(self, name, icon_path):
        self.name = name
        self.icon = pygame.image.load(icon_path)
        self.members = []
        self.total_collected = 0
        self.last_collection_date = datetime.now().date()
        self.account = load_or_create_guild_account(name)

    def add_member(self, player):
        if player not in self.members:
            self.members.append(player)
            self.total_collected += 10  # Initial fee
            player_data = load_or_create_player_data(player)
            player_account = Keypair.from_secret(player_data["secret_key"])
            setup_smart_contract(player_account, self.account, 10)

    def remove_member(self, player):
        if player in self.members:
            self.members.remove(player)

    def daily_collection(self):
        today = datetime.now().date()
        if today > self.last_collection_date:
            days_passed = (today - self.last_collection_date).days
            for member in self.members:
                amount_to_collect = 10 * days_passed
                player_data = load_or_create_player_data(member)
                player_account = Keypair.from_secret(player_data["secret_key"])
                if execute_daily_transfer(player_account, self.account, amount_to_collect):
                    self.total_collected += amount_to_collect
            self.last_collection_date = today

    def render(self, screen, font):
        # Render guild information
        screen.blit(self.icon, (screen.get_width() // 2 - self.icon.get_width() // 2, 50))
        draw_text(self.name, font, (255, 255, 255), screen.get_width() // 2, 150, center=True)
        draw_text(f"Members: {len(self.members)}", font, (255, 255, 255), screen.get_width() // 2, 200, center=True)
        draw_text(f"Total Collected: {self.total_collected}", font, (255, 255, 255), screen.get_width() // 2, 250, center=True)

def load_guilds():
    guilds = [
        Guild("RED CROSS", "assets/images/guilds/red_cross.jpg"),
        Guild("BRITISH HEART FOUNDATION", "assets/images/guilds/bhf.jpg")
    ]
    return guilds

def save_guilds(guilds):
    guild_data = []
    for guild in guilds:
        guild_data.append({
            "name": guild.name,
            "members": guild.members,
            "total_collected": guild.total_collected,
            "last_collection_date": guild.last_collection_date.isoformat()
        })
    with open("guild_data.json", "w") as f:
        json.dump(guild_data, f)

def load_guild_data():
    try:
        with open("guild_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def draw_text(text, font, color, x, y, center=False):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    pygame.display.get_surface().blit(text_surface, text_rect)

def draw_checkbox(screen, x, y, checked):
    pygame.draw.rect(screen, (255, 255, 255), (x, y, 20, 20), 2)
    if checked:
        pygame.draw.line(screen, (255, 255, 255), (x, y), (x + 20, y + 20), 2)
        pygame.draw.line(screen, (255, 255, 255), (x, y + 20), (x + 20, y), 2)

def load_player_data(username):
    try:
        with open(f"{username}_stellar_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None