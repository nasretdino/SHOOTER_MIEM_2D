import pygame
import csv
import sys
from settings import *
from button import Button
from world import World
from sprites import Grenade, ScreenFade


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Путь героя')
        self.clock = pygame.time.Clock()
        self.running = True
        self.start_game = False
        self.start_intro = False
        self.level = 1

        self.load_assets()

        self.screen_scroll, self.bg_scroll = 0, 0
        self.moving_left, self.moving_right, self.shoot, self.grenade, self.grenade_thrown = False, False, False, False, False

    def load_assets(self):
        try:
            def load_image(path):
                return pygame.image.load(path).convert_alpha()

            # Sounds
            self.jump_fx = pygame.mixer.Sound('../SHOOTER_MIEM_2D/audio/jump.mp3')
            self.jump_fx.set_volume(0.05)
            self.shot_fx = pygame.mixer.Sound('../SHOOTER_MIEM_2D/audio/shot.mp3')
            self.shot_fx.set_volume(0.05)
            self.grenade_fx = pygame.mixer.Sound('../SHOOTER_MIEM_2D/audio/shot.mp3')
            self.grenade_fx.set_volume(0.05)
            self.powerup_fx = pygame.mixer.Sound('../SHOOTER_MIEM_2D/audio/jump.mp3')
            self.powerup_fx.set_volume(0.05)

            # Images
            self.start_img = load_image('img/start_btn.png')
            self.exit_img = load_image('img/exit_btn.png')
            self.restart_img = load_image('img/restart_btn.png')

            self.pine1_img, self.pine2_img = load_image('img/Background/pine1.png'), load_image(
                'img/Background/pine2.png')
            self.mountain_img, self.sky_img = load_image('img/Background/mountain.png'), load_image(
                'img/Background/sky_cloud.png')

            self.bullet_img = load_image('img/icons/bullet.png')
            self.grenade_img_icon = load_image('img/icons/grenade.png')
            self.item_boxes_images = {
                'Health': load_image('img/icons/health_box.png'), 'Ammo': load_image('img/icons/ammo_box.png'),
                'Grenade': load_image('img/icons/grenade_box.png'), 'Damage': load_image('img/icons/damage_box.png')}

            # Tiles
            self.img_list = []
            for x in range(TILE_TYPES):
                # This inner try-except handles missing tiles gracefully without crashing the whole game
                try:
                    img = load_image(f'img/Tile/{x}.png')
                    self.img_list.append(pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)))
                except pygame.error:
                    print(f"Warning: Tile image 'img/Tile/{x}.png' not found.")
                    self.img_list.append(pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA))

            # Font
            try:
                self.font = pygame.font.SysFont('FluffyFont', 30)
            except:
                self.font = pygame.font.SysFont(FONT_NAME, 30)

        except (pygame.error, FileNotFoundError) as e:
            print(f"--- КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить файл! ---")
            print(f"--- Убедитесь, что все папки (img, audio) и их содержимое на месте. ---")
            print(f"--- Pygame Error: {e} ---")
            self.running = False

    def _create_sprite_groups(self):
        self.enemy_group = pygame.sprite.Group()
        self.bullet_group = pygame.sprite.Group()
        self.grenade_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.item_box_group = pygame.sprite.Group()
        self.decoration_group = pygame.sprite.Group()
        self.water_group = pygame.sprite.Group()
        self.exit_group = pygame.sprite.Group()

    def _load_level(self, level):
        self._create_sprite_groups()
        world_data = [[-1] * COLS for _ in range(ROWS)]
        try:
            with open(f'level{level}_data.csv', newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for x, row in enumerate(reader):
                    for y, tile in enumerate(row): world_data[x][y] = int(tile)
        except FileNotFoundError:
            print(f"Error: level{level}_data.csv not found.")
            self.running = False
            return
        self.world = World(self)
        self.player, self.health_bar = self.world.process_data(world_data)

    def _reset_level(self):
        self.bg_scroll, self.screen_scroll, self.start_intro = 0, 0, True
        self.intro_fade.reset()
        self.death_fade.reset()
        self._load_level(self.level)

    def _draw_text(self, text, font, text_col, x, y):
        self.screen.blit(font.render(text, True, text_col), (x, y))

    def _draw_bg(self):
        self.screen.fill(BG)
        width = self.sky_img.get_width()
        for x in range(5):
            self.screen.blit(self.sky_img, ((x * width) - self.bg_scroll * 0.5, 0))
            self.screen.blit(self.mountain_img,
                             ((x * width) - self.bg_scroll * 0.6, SCREEN_HEIGHT - self.mountain_img.get_height() - 300))
            self.screen.blit(self.pine1_img,
                             ((x * width) - self.bg_scroll * 0.7, SCREEN_HEIGHT - self.pine1_img.get_height() - 150))
            self.screen.blit(self.pine2_img,
                             ((x * width) - self.bg_scroll * 0.8, SCREEN_HEIGHT - self.pine2_img.get_height()))

    def _draw_hud(self):
        self.health_bar.draw(self.screen, self.player.health)
        self._draw_text('ПУЛИ: ', self.font, BLACK, 10, 35)
        for x in range(self.player.ammo): self.screen.blit(self.bullet_img, (90 + (x * 10), 40))
        self._draw_text('ГРАНАТЫ: ', self.font, BLACK, 10, 60)
        for x in range(self.player.grenades): self.screen.blit(self.grenade_img_icon, (135 + (x * 15), 60))
        self._draw_text(f'УРОН: x{self.player.damage_multiplier:.1f}', self.font, BLACK, 10, 85)

    def run(self):
        if not self.running: return  # Exit if assets failed to load

        self.start_button = Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, self.start_img, 1)
        self.exit_button = Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, self.exit_img, 1)
        self.restart_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, self.restart_img, 2)
        self.intro_fade = ScreenFade(BLACK, 4, self.screen, fade_in=True)
        self.death_fade = ScreenFade(PINK, 4, self.screen)

        self._load_level(self.level)

        while self.running:
            self.clock.tick(FPS)
            if not self.start_game:
                self.screen.fill(WHITE)
                if self.start_button.draw(self.screen): self.start_game, self.start_intro = True, True
                if self.exit_button.draw(self.screen): self.running = False
            else:
                self._draw_bg()
                self.world.draw(self.screen, self.screen_scroll)
                self._draw_hud()

                all_groups = [self.enemy_group, self.bullet_group, self.grenade_group, self.explosion_group,
                              self.item_box_group, self.decoration_group, self.water_group, self.exit_group]
                self.player.update()
                [group.update() for group in all_groups]
                [enemy.ai() for enemy in self.enemy_group]
                self.player.draw(self.screen)
                [group.draw(self.screen) for group in all_groups]

                if self.start_intro:
                    if self.intro_fade.fade(): self.start_intro = False

                if self.player.alive:
                    self.update_player_actions()
                else:
                    self.screen_scroll = 0
                    if self.death_fade.fade() and self.restart_button.draw(self.screen): self._reset_level()

            self.handle_events()
            pygame.display.update()

    def update_player_actions(self):
        if self.shoot:
            self.player.shoot()
        elif self.grenade and not self.grenade_thrown and self.player.grenades > 0:
            self.grenade_group.add(
                Grenade(self.player.rect.centerx + (0.5 * self.player.rect.size[0] * self.player.direction),
                        self.player.rect.top, self.player.direction, self))
            self.player.grenades -= 1
            self.grenade_thrown = True

        if self.player.in_air:
            self.player.update_action(2)
        elif self.moving_left or self.moving_right:
            self.player.update_action(1)
        else:
            self.player.update_action(0)

        self.screen_scroll, level_complete = self.player.move(self.moving_left, self.moving_right)
        self.bg_scroll -= self.screen_scroll

        for bullet in self.bullet_group:
            if bullet.owner != self.player and self.player.rect.colliderect(
                bullet.rect): self.player.health -= bullet.damage; bullet.kill()
            for enemy in self.enemy_group:
                if bullet.owner == self.player and enemy.rect.colliderect(
                    bullet.rect) and enemy.alive: enemy.health -= bullet.damage; bullet.kill(); break

        if level_complete:
            self.level += 1
            if self.level <= MAX_LEVELS:
                self._reset_level()
            else:
                self.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: self.moving_left = True
                if event.key == pygame.K_d: self.moving_right = True
                if event.key == pygame.K_SPACE: self.shoot = True
                if event.key == pygame.K_q: self.grenade = True
                if event.key == pygame.K_w and self.player.alive: self.player.jump = True
                if event.key == pygame.K_ESCAPE: self.running = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a: self.moving_left = False
                if event.key == pygame.K_d: self.moving_right = False
                if event.key == pygame.K_SPACE: self.shoot = False
                if event.key == pygame.K_q: self.grenade, self.grenade_thrown = False, False


if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()