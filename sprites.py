import pygame
import os
import random
from settings import *


def load_image_helper(path):
    return pygame.image.load(path).convert_alpha()


class Soldier(pygame.sprite.Sprite):
    def __init__(self, game, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.damage_multiplier = 1.0
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            temp_list = []
            try:
                num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
                for i in range(num_of_frames):
                    img = load_image_helper(f'img/{self.char_type}/{animation}/{i}.png')
                    img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                    temp_list.append(img)
            except FileNotFoundError:
                print(f"Warning: Animation folder 'img/{self.char_type}/{animation}' not found.")
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index] if self.animation_list and self.animation_list[
            self.action] else pygame.Surface((40, 50))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        screen_scroll = 0
        dx, dy = 0, 0

        if moving_left: dx = -self.speed; self.flip = True; self.direction = -1
        if moving_right: dx = self.speed; self.flip = False; self.direction = 1

        if self.jump and not self.in_air:
            self.vel_y = -15
            self.jump = False
            self.in_air = True
            self.game.jump_fx.play()

        self.vel_y += GRAVITY
        if self.vel_y > 10: self.vel_y = 10
        dy += self.vel_y

        for tile in self.game.world.obstacle_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                if self.char_type in ['enemy', 'boss']: self.direction *= -1; self.move_counter = 0
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.vel_y < 0:
                    self.vel_y = 0; dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0; self.in_air = False; dy = tile[1].top - self.rect.bottom

        if pygame.sprite.spritecollide(self, self.game.water_group, False): self.health = 0

        level_complete = False
        if pygame.sprite.spritecollide(self, self.game.exit_group, False): level_complete = True

        if self.rect.bottom > SCREEN_HEIGHT: self.health = 0
        if self.char_type == 'player' and (self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH): dx = 0

        self.rect.x += dx
        self.rect.y += dy

        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and self.game.bg_scroll < (
                    self.game.world.level_length * TILE_SIZE) - SCREEN_WIDTH) or \
                    (self.rect.left < SCROLL_THRESH and self.game.bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            damage = PLAYER_DAMAGE * self.damage_multiplier if self.char_type == 'player' else ENEMY_DAMAGE
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction, damage, self, self.game)
            self.game.bullet_group.add(bullet)
            self.ammo -= 1
            self.game.shot_fx.play()

    def ai(self):
        if self.alive and self.game.player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)
                self.idling = True
                self.idling_counter = 50

            if self.vision.colliderect(self.game.player.rect):
                self.update_action(0)
                self.shoot()
            else:
                if not self.idling:
                    ai_moving_right = self.direction == 1
                    self.move(not ai_moving_right, ai_moving_right)
                    self.update_action(1)
                    self.move_counter += 1
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    if self.move_counter > TILE_SIZE: self.direction *= -1; self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0: self.idling = False

        self.rect.x += self.game.screen_scroll

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        if not self.animation_list or not self.animation_list[self.action]: return
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self, surface):
        surface.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class Boss(Soldier):
    def __init__(self, game, char_type, x, y, scale, speed, ammo, grenades):
        super().__init__(game, char_type, x, y, scale, speed, ammo, grenades)
        self.health = BOSS_HEALTH
        self.max_health = self.health
        self.vision = pygame.Rect(0, 0, 400, 40)

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20  # Можно сделать босса более скорострельным, уменьшив это число
            damage = BOSS_DAMAGE

            bullet_y_position = self.rect.centery + 40  # Высота выстрела

            bullet = Bullet(
                self.rect.centerx + (0.75 * self.rect.size[0] * self.direction),
                bullet_y_position,
                self.direction,
                damage,
                self,
                self.game
            )
            self.game.bullet_group.add(bullet)

            if self.char_type == 'player':
                self.ammo -= 1

            self.game.shot_fx.play()

    def ai(self):
        if self.alive and self.game.player.alive:
            player_is_to_the_right = self.game.player.rect.centerx > self.rect.centerx

            if player_is_to_the_right:
                self.direction = 1
                self.flip = False
            else:
                self.direction = -1
                self.flip = True
            self.vision.center = (self.rect.center[0], self.rect.center[1] + 40)
            if self.vision.colliderect(self.game.player.rect):

                self.update_action(0)
                self.shoot()
            else:
                moving_left = not player_is_to_the_right
                moving_right = player_is_to_the_right
                self.move(moving_left, moving_right)
                self.update_action(1)

        self.rect.x += self.game.screen_scroll


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, game, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.item_type = item_type
        self.image = self.game.item_boxes_images[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += self.game.screen_scroll
        if pygame.sprite.collide_rect(self, self.game.player):
            self.game.powerup_fx.play()
            if self.item_type == 'Health':
                self.game.player.health = min(self.game.player.health + 25, self.game.player.max_health)
            elif self.item_type == 'Ammo':
                self.game.player.ammo += 15
            elif self.item_type == 'Grenade':
                self.game.player.grenades += 3
            elif self.item_type == 'Damage':
                self.game.player.damage_multiplier += 0.5
            self.kill()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, damage, owner, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.speed = 10
        self.image = self.game.bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.damage = damage
        self.owner = owner

    def update(self):
        self.rect.x += (self.direction * self.speed) + self.game.screen_scroll
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH: self.kill()

        for tile in self.game.world.obstacle_list:
            if tile[1].colliderect(self.rect): self.kill(); break


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = self.game.grenade_img_icon
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width, self.height = self.image.get_width(), self.image.get_height()
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx, dy = self.direction * self.speed, self.vel_y
        for tile in self.game.world.obstacle_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width,
                                   self.height): self.direction *= -1; dx = self.direction * self.speed
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                if self.vel_y < 0:
                    self.vel_y = 0; dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0; dy = tile[1].top - self.rect.bottom

        self.rect.x += dx + self.game.screen_scroll
        self.rect.y += dy

        self.timer -= 1
        if self.timer <= 0:
            self.kill();
            self.game.grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5, self.game)
            self.game.explosion_group.add(explosion)
            if abs(self.rect.centerx - self.game.player.rect.centerx) < TILE_SIZE * 2: self.game.player.health -= 50
            for enemy in self.game.enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2: enemy.health -= 50


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.images = []
        for num in range(1, 6):
            img = load_image_helper(f'img/explosion/exp{num}.png')
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        self.rect.x += self.game.screen_scroll
        EXPLOSION_SPEED = 4
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


class ScreenFade:
    def __init__(self, colour, speed, screen, fade_in=False):
        self.colour = colour
        self.speed = speed
        self.screen = screen
        self.fade_in = fade_in
        self.reset()

    def reset(self):
        self.fade_counter = SCREEN_HEIGHT if self.fade_in else 0

    def fade(self):
        fade_complete = False
        if self.fade_in:
            self.fade_counter -= self.speed
            pygame.draw.rect(self.screen, self.colour, (0, 0, SCREEN_WIDTH, self.fade_counter))
            if self.fade_counter <= 0:
                fade_complete = True
        else:
            self.fade_counter += self.speed
            pygame.draw.rect(self.screen, self.colour, (0, 0, SCREEN_WIDTH, self.fade_counter))
            if self.fade_counter >= SCREEN_HEIGHT:
                fade_complete = True

        return fade_complete