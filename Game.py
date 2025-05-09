import pygame
import sys
import random
import os
import json

pygame.init()

CONFIG_FILE = "game_config.json"

default_config = {
    "window": {"width": 800, "height": 600, "title": "Stick of Truth but Stan`s story"},
    "colors": {
        "white": [255, 255, 255], "black": [0, 0, 0], "red": [255, 0, 0],
        "green": [0, 255, 0], "blue": [0, 0, 255], "dialog_bg": [50, 50, 50],
        "battle_bg": [50, 50, 80]
    },
    "characters": {
        "player": {
            "name": "Warrior Stan", "image": "player.png", "portrait": "stan_portrait.png",
            "width": 150, "height": 150, "hp": 100, "default_position": [100, 400],
            "battle_position": [200, 400], "placeholder_color": [0, 200, 0]
        },
        "enemies": [
            {
                "name": "Princess Kenny", "image": "kenny.png", "portrait": "kenny_portrait.png",
                "width": 150, "height": 150, "hp": 80, "default_position": [500, 400],
                "battle_position": [550, 400], "placeholder_color": [200, 0, 0],
                "dialogs": [
                    {"text": "Mfhhfh !", "portrait": "kenny_portrait.png"},
                    {"text": "Muhuhu Fuhhnh", "portrait": "kenny_portrait.png"},
                    {"text": "Kenny please shut your mouth", "portrait": "stan_portrait.png"}
                ]
            },
            {
                "name": "Kyle the Elf King", "image": "kyle.png", "portrait": "kyle_portrait.png",
                "width": 150, "height": 150, "hp": 90, "default_position": [600, 350],
                "battle_position": [550, 400], "placeholder_color": [0, 100, 200],
                "dialogs": [
                    {"text": "Behold the Elven King!", "portrait": "kyle_portrait.png"},
                    {"text": "Hand over the Stick of Truth!", "portrait": "kyle_portrait.png"},
                    {"text": "I'll never surrender it to you, Kyle!", "portrait": "stan_portrait.png"}
                ]
            }
        ],
        "npcs": [
            {
                "name": "Butters", "image": "butters.png", "portrait": "butters_portrait.png",
                "width": 150, "height": 150, "default_position": [300, 350],
                "placeholder_color": [200, 200, 0],
                "dialogs": [
                    {"text": "Oh hamburgers!", "portrait": "butters_portrait.png"},
                    {"text": "Gee whiz, Stan!", "portrait": "butters_portrait.png"},
                    {"text": "What's up, Butters?", "portrait": "stan_portrait.png"}
                ]
            }
        ]
    },
    "battle": {
        "actions": ["Attack", "Special", "Item", "Run"],
        "player_move_damage": {
            "Attack": {"min": 15, "max": 25},
            "Special": {"min": 25, "max": 40}
        },
        "enemy_move_damage": {"min": 10, "max": 20},
        "heal_amount": 20,
        "block_reduction": 0.5
    },
    "game": {
        "movement_speed": 5,
        "interaction_distance": 150,
        "frame_rate": 60
    }
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

config = load_config()

WIDTH = config["window"]["width"]
HEIGHT = config["window"]["height"]
WHITE = tuple(config["colors"]["white"])
BLACK = tuple(config["colors"]["black"])
RED = tuple(config["colors"]["red"])
GREEN = tuple(config["colors"]["green"])
BLUE = tuple(config["colors"]["blue"])
DIALOG_BG = tuple(config["colors"]["dialog_bg"])
BATTLE_BG = tuple(config["colors"]["battle_bg"])

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(config["window"]["title"])
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

os.makedirs('images', exist_ok=True)

def create_placeholder_image(width, height, color):
    surface = pygame.Surface((width, height))
    surface.fill(color)
    return surface

def get_image(filename, width, height, color):
    filepath = os.path.join('images', filename)
    try:
        if os.path.exists(filepath):
            img = pygame.image.load(filepath)
            return pygame.transform.scale(img, (width, height))
    except pygame.error:
        pass
    return create_placeholder_image(width, height, color)

class Character:
    def __init__(self, name, image_path, portrait_path, width, height, hp, position, battle_position, placeholder_color):
        self.name = name
        self.original_img = get_image(image_path, width, height, placeholder_color)
        self.img = self.original_img.copy()
        self.portrait = get_image(portrait_path, 100, 100, placeholder_color)
        self.width, self.height = width, height
        self.hp, self.max_hp = hp, hp
        self.x, self.y = position
        self.battle_x, self.battle_y = battle_position
        self.is_dead = False
        self.animation_frame = 0
        self.dialogs = []
        self.direction = 0
        self.last_direction = "right"
        
        self.walk_cycle = 0
        self.walk_timer = 0
        self.walking = False
        self.walk_switch_frames = 10
    
    def rotate(self, direction):
        base_angle = 0
        if direction == "left":
            self.last_direction = "left"
            base_angle = 0
        elif direction == "right":
            self.last_direction = "right"
            base_angle = 0
        
        if self.walking:
            self.walk_timer += 1
            if self.walk_timer >= self.walk_switch_frames:
                self.walk_timer = 0
                self.walk_cycle = 1 - self.walk_cycle
            
            if self.walk_cycle == 0:
                tilt_angle = 33
            else:
                tilt_angle = -33
            
            if direction == "left":
                self.direction = tilt_angle
            elif direction == "right":
                self.direction = tilt_angle
            elif direction == "up" or direction == "down":
                self.direction = tilt_angle
        else:
            self.direction = base_angle
        
        self.img = pygame.transform.rotate(self.original_img, self.direction)
    
    def draw(self, surface, x=None, y=None):
        draw_x = x if x is not None else self.x
        draw_y = y if y is not None else self.y
        
        rotated_rect = self.img.get_rect(center=(draw_x + self.width//2, draw_y + self.height//2))
        
        if self.animation_frame > 0:
            self.animation_frame -= 1
            offset = random.randint(-5, 5)
            surface.blit(self.img, (rotated_rect.x + offset, rotated_rect.y + offset))
        else:
            surface.blit(self.img, rotated_rect)
    
    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        self.animation_frame = 10
        if self.hp <= 0:
            self.is_dead = True
    
    def draw_health_bar(self, surface, x, y):
        bar_width, bar_height = 200, 20
        fill_width = (self.hp / self.max_hp) * bar_width
        
        pygame.draw.rect(surface, RED, (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (x, y, fill_width, bar_height))
        pygame.draw.rect(surface, BLACK, (x, y, bar_width, bar_height), 2)
        
        health_text = font.render(f'{self.name}: {self.hp}/{self.max_hp} HP', True, WHITE)
        surface.blit(health_text, (x, y - 25))

class NPC(Character):
    def __init__(self, character_config):
        super().__init__(
            character_config["name"],
            character_config["image"],
            character_config["portrait"],
            character_config["width"],
            character_config["height"],
            character_config.get("hp", 1),
            character_config["default_position"],
            character_config.get("battle_position", [0, 0]),
            character_config["placeholder_color"]
        )
        self.dialogs = character_config.get("dialogs", [])
        self.movement_timer = 0
        self.move_direction = random.choice(["left", "right", "up", "down"])
    
    def wander(self):
        if self.movement_timer <= 0:
            self.movement_timer = random.randint(30, 120)
            self.move_direction = random.choice(["left", "right", "up", "down"])
            self.walking = True
            self.rotate(self.move_direction)
        else:
            self.movement_timer -= 1
        
        if self.move_direction == "left" and self.x > 50:
            self.x -= 1
            self.walking = True
        elif self.move_direction == "right" and self.x < WIDTH - self.width - 50:
            self.x += 1
            self.walking = True
        elif self.move_direction == "up" and self.y > 250:
            self.y -= 1
            self.walking = True
        elif self.move_direction == "down" and self.y < HEIGHT - self.height - 50:
            self.y += 1
            self.walking = True
        else:
            self.walking = False
            
        self.rotate(self.move_direction)

class Enemy(Character):
    def __init__(self, character_config):
        super().__init__(
            character_config["name"],
            character_config["image"],
            character_config["portrait"],
            character_config["width"],
            character_config["height"],
            character_config["hp"],
            character_config["default_position"],
            character_config["battle_position"],
            character_config["placeholder_color"]
        )
        self.dialogs = character_config.get("dialogs", [])

class DialogSystem:
    def __init__(self):
        self.dialogs = []
        self.current_dialog = 0
        self.active = False
    
    def start_dialog(self, dialogs):
        self.dialogs = dialogs
        self.current_dialog = 0
        self.active = True
    
    def next_dialog(self):
        self.current_dialog += 1
        if self.current_dialog >= len(self.dialogs):
            self.active = False
            return False
        return True
    
    def draw(self, surface):
        if not self.active or self.current_dialog >= len(self.dialogs):
            return
        
        current = self.dialogs[self.current_dialog]
        
        dialog_box = pygame.Rect(50, 400, WIDTH - 100, 150)
        pygame.draw.rect(surface, DIALOG_BG, dialog_box)
        pygame.draw.rect(surface, WHITE, dialog_box, 2)
        
        text_x = 70
        if "portrait" in current:
            portrait_img = get_image(current["portrait"], 100, 100, (150, 150, 150))
            portrait_box = pygame.Rect(60, 410, 100, 100)
            pygame.draw.rect(surface, (70, 70, 70), portrait_box)
            surface.blit(portrait_img, portrait_box)
            text_x = 180
        
        text = current["text"]
        words = text.split()
        lines, current_line = [], ""
        
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] < WIDTH - 200:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        
        lines.append(current_line)
        
        for i, line in enumerate(lines):
            surface.blit(font.render(line, True, WHITE), (text_x, 430 + i * 30))
        
        surface.blit(small_font.render("Press SPACE to continue...", True, WHITE), (WIDTH - 250, 520))

class BattleSystem:
    def __init__(self, player, config):
        self.player = player
        self.enemy = None
        self.config = config
        self.player_turn = True
        self.message = ""
        self.actions = config["actions"]
        self.selected_action = 0
        self.active = False
        self.animation_timer = 0
        self.animation_duration = 30
        self.enemy_attack_pending = False
        self.battle_result = None
        self.block_active = False
        self.block_prompt_visible = False
        self.block_prompt_timer = 0
        self.block_prompt_duration = 90
        self.block_window_timer = 0
        self.block_window_duration = 60
        self.battle_background = get_image('battle_background.png', WIDTH, HEIGHT, BATTLE_BG)
    
    def start_battle(self, enemy):
        self.enemy = enemy
        self.player_turn = True
        self.message = f"Battle with {enemy.name} started!"
        self.active = True
        self.animation_timer = 0
        self.enemy_attack_pending = False
        self.battle_result = None
        self.block_active = False
        self.block_prompt_visible = False
    
    def select_action(self, direction):
        self.selected_action = (self.selected_action + direction) % len(self.actions)
    
    def execute_action(self):
        action = self.actions[self.selected_action]
        
        if action == "Attack":
            damage_config = self.config["player_move_damage"]["Attack"]
            damage = random.randint(damage_config["min"], damage_config["max"])
            self.enemy.take_damage(damage)
            self.message = f"You hit {self.enemy.name} for {damage} damage!"
            self.player_turn = False
            self.enemy_attack_pending = True
            self.animation_timer = self.animation_duration
            self.block_prompt_visible = True
            self.block_prompt_timer = self.block_prompt_duration
            self.block_window_timer = self.block_window_duration
        
        elif action == "Special":
            damage_config = self.config["player_move_damage"]["Special"]
            damage = random.randint(damage_config["min"], damage_config["max"])
            self.enemy.take_damage(damage)
            self.message = f"Special attack! {damage} damage dealt to {self.enemy.name}!"
            self.player_turn = False
            self.enemy_attack_pending = True
            self.animation_timer = self.animation_duration
            self.block_prompt_visible = True
            self.block_prompt_timer = self.block_prompt_duration
            self.block_window_timer = self.block_window_duration
        
        elif action == "Item":
            heal = self.config["heal_amount"]
            self.player.hp = min(self.player.hp + heal, self.player.max_hp)
            self.message = f"You used a health potion. +{heal} HP!"
            self.player_turn = False
            self.enemy_attack_pending = True
            self.animation_timer = self.animation_duration
            self.block_prompt_visible = True
            self.block_prompt_timer = self.block_prompt_duration
            self.block_window_timer = self.block_window_duration
        
        elif action == "Run":
            self.active = False
            self.message = "You ran away!"
            self.battle_result = "run"
        
        if self.enemy.is_dead:
            self.message = f"You defeated {self.enemy.name}!"
            self.active = False
            if self.enemy.name == "Kyle the Elf King":
                self.battle_result = "kyle_defeated"
            else:
                self.battle_result = "win"
        
        return self.battle_result
    
    def activate_block(self):
        if not self.player_turn and self.enemy_attack_pending and self.block_window_timer > 0:
            self.block_active = True
            return True
        return False
    
    def enemy_turn(self):
        damage_config = self.config["enemy_move_damage"]
        base_damage = random.randint(damage_config["min"], damage_config["max"])
    
        if self.block_active:
            block_reduction = self.config.get("block_reduction", 0.5)
            damage = int(base_damage * block_reduction)
            self.message = f"BLOCKED! {self.enemy.name} attacks! You take only {damage} damage!"
        else:
            damage = base_damage
            self.message = f"{self.enemy.name} attacks! You take {damage} damage!"
    
        self.player.take_damage(damage)
    
        self.block_active = False
        self.block_prompt_visible = False
    
        if self.player.is_dead:
            self.message = "You were defeated!"
            self.active = False
            self.battle_result = "lose"
            return self.battle_result
        else:
            self.player_turn = True
        return None
    
    def update(self):
        if self.enemy_attack_pending:
            if self.block_prompt_timer > 0:
                self.block_prompt_timer -= 1
                if self.block_prompt_timer <= 0:
                    self.block_prompt_visible = False
            
            if self.block_window_timer > 0:
                self.block_window_timer -= 1
            
            if self.animation_timer > 0:
                self.animation_timer -= 1
                return None
            else:
                self.enemy_attack_pending = False
                return self.enemy_turn()
        return None
    
    def draw(self, surface):
        if not self.active:
            return
        
        surface.blit(self.battle_background, (0, 0))
        
        self.player.draw(surface, self.player.battle_x, self.player.battle_y)
        self.enemy.draw(surface, self.enemy.battle_x, self.enemy.battle_y)
        
        self.player.draw_health_bar(surface, 50, 50)
        self.enemy.draw_health_bar(surface, WIDTH - 250, 50)
        
        message_text = font.render(self.message, True, WHITE)
        surface.blit(message_text, (WIDTH // 2 - message_text.get_width() // 2, 150))
        
        if self.block_prompt_visible:
            if (self.block_prompt_timer // 10) % 2 == 0:
                block_text = font.render("Press SPACE to BLOCK!", True, (255, 255, 0))
                block_box = pygame.Rect(WIDTH // 2 - 150, 200, 300, 50)
                pygame.draw.rect(surface, (100, 0, 0), block_box)
                pygame.draw.rect(surface, (255, 255, 0), block_box, 3)
                surface.blit(block_text, (WIDTH // 2 - block_text.get_width() // 2, 210))
        
        if self.block_active:
            block_indicator = font.render("BLOCKING!", True, (0, 255, 0))
            surface.blit(block_indicator, (self.player.battle_x, self.player.battle_y - 40))
        
        if self.player_turn and not self.enemy_attack_pending:
            action_box = pygame.Rect(50, 200, 200, 30 * len(self.actions) + 20)
            pygame.draw.rect(surface, DIALOG_BG, action_box)
            pygame.draw.rect(surface, WHITE, action_box, 2)
            
            for i, action in enumerate(self.actions):
                color = GREEN if i == self.selected_action else WHITE
                action_text = font.render(action, True, color)
                surface.blit(action_text, (70, 210 + i * 30))

EXPLORE, DIALOG, BATTLE, GAME_OVER, VICTORY = 0, 1, 2, 3, 4

background = get_image('background.png', WIDTH, HEIGHT, (100, 100, 200))
stick_of_truth = get_image('stick_of_truth.png', 300, 300, (220, 180, 50))

player_config = config["characters"]["player"]
player = Character(
    player_config["name"],
    player_config["image"],
    player_config["portrait"],
    player_config["width"],
    player_config["height"],
    player_config["hp"],
    player_config["default_position"],
    player_config["battle_position"],
    player_config["placeholder_color"]
)

enemies = [Enemy(enemy_config) for enemy_config in config["characters"]["enemies"]]
npcs = [NPC(npc_config) for npc_config in config["characters"]["npcs"]]

kyle_defeated = False
victory_timer = 0

current_state = EXPLORE
dialog_system = DialogSystem()
battle_system = BattleSystem(player, config["battle"])
current_interactive = None

MOVEMENT_SPEED = config["game"]["movement_speed"]
INTERACTION_DISTANCE = config["game"]["interaction_distance"]
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if current_state == BATTLE:
                    if not battle_system.player_turn and battle_system.enemy_attack_pending:
                        battle_system.activate_block()
                elif current_state == DIALOG:
                    if not dialog_system.next_dialog():
                        if isinstance(current_interactive, Enemy):
                            current_state = BATTLE
                            battle_system.start_battle(current_interactive)
                        else:
                            current_state = EXPLORE
                elif current_state == EXPLORE:
                    for character in enemies + npcs:
                        if isinstance(character, Enemy) and character.is_dead:
                            continue
                        if abs(player.x - character.x) < INTERACTION_DISTANCE:
                            current_interactive = character
                            if character.dialogs:
                                current_state = DIALOG
                                dialog_system.start_dialog(character.dialogs)
                                break
                            elif isinstance(character, Enemy):
                                current_state = BATTLE
                                battle_system.start_battle(character)
                                break
            
            elif current_state == BATTLE:
                if battle_system.player_turn and not battle_system.enemy_attack_pending:
                    if event.key == pygame.K_w:
                        battle_system.select_action(-1)
                    elif event.key == pygame.K_s:
                        battle_system.select_action(1)
                    elif event.key == pygame.K_RETURN:
                        result = battle_system.execute_action()
                        if result == "run":
                            current_state = EXPLORE
                        elif result == "win":
                            current_state = EXPLORE
                        elif result == "kyle_defeated":
                            current_state = VICTORY
                            victory_timer = 180
                            kyle_defeated = True
                        elif result == "lose":
                            current_state = GAME_OVER
            
            elif current_state == GAME_OVER:
                if event.key == pygame.K_r:
                    player.hp = player.max_hp
                    player.is_dead = False
                    for enemy in enemies:
                        enemy.hp = enemy.max_hp
                        enemy.is_dead = False
                    current_state = EXPLORE
                    player.x, player.y = player_config["default_position"]
    
    screen.fill(BLACK)
    screen.blit(background, (0, 0))
    
    if current_state == EXPLORE:
        keys = pygame.key.get_pressed()
        moved = False
        
        if keys[pygame.K_a] and player.x > 0:
            player.x -= MOVEMENT_SPEED
            player.walking = True
            player.rotate("left")
            moved = True
        if keys[pygame.K_d] and player.x < WIDTH - player.width:
            player.x += MOVEMENT_SPEED
            player.walking = True
            player.rotate("right")
            moved = True
        if keys[pygame.K_w] and player.y > 200:
            player.y -= MOVEMENT_SPEED
            player.walking = True
            player.rotate("up")
            moved = True
        if keys[pygame.K_s] and player.y < HEIGHT - player.height:
            player.y += MOVEMENT_SPEED
            player.walking = True
            player.rotate("down")
            moved = True
            
        if not moved:
            player.walking = False
            player.direction = 0
            player.img = player.original_img.copy()
        
        player.draw(screen)
        for enemy in enemies:
            if not enemy.is_dead:
                enemy.draw(screen)
        for npc in npcs:
            npc.wander()
            npc.draw(screen)
    
    elif current_state == DIALOG:
        player.draw(screen)
        current_interactive.draw(screen)
        dialog_system.draw(screen)
    
    elif current_state == BATTLE:
        result = battle_system.update()
        if result == "lose":
            current_state = GAME_OVER
        elif result == "run" or result == "win":
            current_state = EXPLORE
        elif result == "kyle_defeated":
            current_state = VICTORY
            victory_timer = 180
            kyle_defeated = True
        
        battle_system.draw(screen)
    
    elif current_state == VICTORY:
        pygame.draw.rect(screen, (20, 20, 50), (0, 0, WIDTH, HEIGHT))
        
        stick_rect = stick_of_truth.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        screen.blit(stick_of_truth, stick_rect)
        
        victory_text = font.render("You got the Stick of Truth!", True, (255, 215, 0))
        congrats_text = font.render("You are now the ruler of the Kingdom!", True, (255, 215, 0))
        
        screen.blit(victory_text, (WIDTH//2 - victory_text.get_width()//2, HEIGHT//2 + 100))
        screen.blit(congrats_text, (WIDTH//2 - congrats_text.get_width()//2, HEIGHT//2 + 150))
        
        victory_timer -= 1
        if victory_timer <= 0:
            current_state = EXPLORE
    
    elif current_state == GAME_OVER:
        screen.fill((50, 0, 0))
        
        game_over_text = font.render("GAME OVER", True, RED)
        restart_text = font.render("Press R to restart", True, WHITE)
        
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 50))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
    
    if current_state == EXPLORE:
        health_text = small_font.render(f"HP: {player.hp}/{player.max_hp}", True, WHITE)
        health_bar_width = 150
        health_bar_height = 15
        health_fill_width = (player.hp / player.max_hp) * health_bar_width
        
        pygame.draw.rect(screen, (0, 0, 0, 150), (10, 10, health_bar_width + 10, 50))
        pygame.draw.rect(screen, RED, (15, 35, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (15, 35, health_fill_width, health_bar_height))
        pygame.draw.rect(screen, BLACK, (15, 35, health_bar_width, health_bar_height), 2)
        screen.blit(health_text, (15, 15))
        
        for character in enemies + npcs:
            if not (isinstance(character, Enemy) and character.is_dead) and abs(player.x - character.x) < INTERACTION_DISTANCE:
                hint_text = small_font.render(f"Press SPACE to interact with {character.name}", True, WHITE)
                screen.blit(hint_text, (WIDTH//2 - hint_text.get_width()//2, HEIGHT - 50))
                break
        
        if kyle_defeated:
            stick_icon = pygame.transform.scale(stick_of_truth, (50, 50))
            screen.blit(stick_icon, (WIDTH - 60, 10))
            stick_text = small_font.render("Stick of Truth", True, (255, 215, 0))
            screen.blit(stick_text, (WIDTH - 130, 60))
    
    pygame.display.flip()
    clock.tick(config["game"]["frame_rate"])

pygame.quit()
sys.exit()
