import pygame
from settings import *
from sprites import Soldier, Boss, ItemBox


class World:
    def __init__(self, game):
        self.game = game
        self.obstacle_list = []
        self.level_length = 0

    def process_data(self, data):
        self.level_length = len(data[0])
        player, health_bar = None, None

        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = self.game.img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x, img_rect.y = x * TILE_SIZE, y * TILE_SIZE
                    tile_data = (img, img_rect)

                    if 0 <= tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10:
                        self.game.water_group.add(Water(img, x * TILE_SIZE, y * TILE_SIZE, self.game))
                    elif 11 <= tile <= 14:
                        self.game.decoration_group.add(Decoration(img, x * TILE_SIZE, y * TILE_SIZE, self.game))
                    elif tile == 15:
                        player = Soldier(self.game, 'player', x * TILE_SIZE, y * TILE_SIZE, 1.65, PLAYER_SPEED,
                                         PLAYER_AMMO, PLAYER_GRENADES)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:
                        self.game.enemy_group.add(
                            Soldier(self.game, 'enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, ENEMY_SPEED, ENEMY_AMMO,
                                    ENEMY_GRENADES))
                    elif tile == 17:
                        self.game.item_box_group.add(ItemBox(self.game, 'Ammo', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 18:
                        self.game.item_box_group.add(ItemBox(self.game, 'Grenade', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 19:
                        self.game.item_box_group.add(ItemBox(self.game, 'Health', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 20:
                        self.game.exit_group.add(Exit(img, x * TILE_SIZE, y * TILE_SIZE, self.game))
                    elif tile == 21:
                        self.game.enemy_group.add(
                            Boss(self.game, 'boss', x * TILE_SIZE, y * TILE_SIZE, 0.6, BOSS_SPEED, BOSS_AMMO,
                                 BOSS_GRENADES))
                    elif tile == 23:
                        self.game.item_box_group.add(ItemBox(self.game, 'Damage', x * TILE_SIZE, y * TILE_SIZE))

        return player, health_bar

    def draw(self, surface, screen_scroll):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            surface.blit(tile[0], tile[1])


class HealthBar:
    def __init__(self, x, y, health, max_health):
        self.x, self.y, self.health, self.max_health = x, y, health, max_health

    def draw(self, surface, health):
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(surface, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(surface, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(surface, GREEN, (self.x, self.y, 150 * ratio, 20))


class WorldElement(pygame.sprite.Sprite):
    def __init__(self, img, x, y, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += self.game.screen_scroll


class Decoration(WorldElement): pass


class Water(WorldElement): pass


class Exit(WorldElement): pass