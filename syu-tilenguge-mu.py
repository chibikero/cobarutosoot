import pyxel
import random
import math

# 定数の定義
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192
STAR_COUNT = 50
FROG_WIDTH = 16
FROG_HEIGHT = 16
BULLET_WIDTH = 4
BULLET_HEIGHT = 2
ENEMY_WIDTH = 16
ENEMY_HEIGHT = 16
ENEMY_SPAWN_INTERVAL = 35
FROG_MAX_HP = 100
HP_BAR_WIDTH = 50
HP_BAR_HEIGHT = 5
FORCE_DELAY = 8

# サウンドチャンネル
SOUND_ENEMY_DEATH = 0
SOUND_BULLET_SHOOT = 1
MUSIC_STAGE = 0
SOUND_ITEM_GET = 3
SOUND_LASER_SHOOT = 2

class Star:
    def __init__(self, x, y):
        self.x, self.y = x, y; self.speed = random.uniform(0.5, 1.5); self.color = random.choice([7, 15])
    def update(self):
        self.x -= self.speed
        if self.x < 0: self.x, self.y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT)
    def draw(self): pyxel.pset(self.x, self.y, self.color)

class Force:
    def __init__(self, delay):
        self.delay, self.x, self.y, self.w, self.h, self.size = delay, -16, -16, 0, 0, 3
    def update(self, frog_history):
        if len(frog_history) > self.delay:
            pos = frog_history[self.delay]; self.x, self.y = pos[0] + FROG_WIDTH / 2, pos[1] + FROG_HEIGHT / 2
    def draw(self):
        if self.x >= 0: pyxel.circ(self.x, self.y, self.size, 10); pyxel.circb(self.x, self.y, self.size, 3)
    def shoot(self): return Bullet(self.x, self.y - BULLET_HEIGHT / 2)
    def is_colliding(self, bullet):
        if self.x < 0: return False
        return math.hypot(self.x - (bullet.x + bullet.w / 2), self.y - (bullet.y + bullet.h / 2)) < self.size + 2

class ForceItem:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h = x, y, 8, 8; self.alive, self.speed_x, self.frame = True, -0.5, 0
    def update(self):
        self.x += self.speed_x; self.y += math.sin(self.frame * 0.1) * 5; self.frame += 1
        if self.x < -self.w: self.alive = False
    def draw(self):
        if (self.frame // 4) % 2 == 0:
            cx, cy, r = self.x + self.w/2, self.y + self.h/2, self.w/2
            pyxel.circ(cx, cy, r, 10); pyxel.circb(cx, cy, r, 3)
    def is_colliding(self, frog): return (self.x < frog.x + frog.w and self.x + self.w > frog.x and self.y < frog.y + frog.h and self.y + self.h > frog.y)

class Funnel:
    def __init__(self, frog):
        self.frog, self.x, self.y = frog, frog.x, frog.y; self.target_x, self.target_y, self.move_timer = self.x, self.y, 0
        self.move_speed, self.size = 0.05, 4; self.shoot_timer = random.randint(30, 90)
        self.w, self.h = 0, 0
    def update(self):
        self.move_timer -= 1
        if self.move_timer <= 0:
            frog_center_x, frog_center_y = self.frog.x + self.frog.w / 2, self.frog.y + self.frog.h / 2
            angle, radius = random.uniform(0, 360), random.uniform(30, 80)
            self.target_x, self.target_y = frog_center_x + math.cos(math.radians(angle)) * radius, frog_center_y + math.sin(math.radians(angle)) * radius
            self.move_timer = random.randint(30, 90)
        self.x += (self.target_x - self.x) * self.move_speed; self.y += (self.target_y - self.y) * self.move_speed
    def draw(self):
        pyxel.tri(self.x, self.y - self.size, self.x - self.size, self.y, self.x + self.size, self.y, 11)
        pyxel.tri(self.x, self.y + self.size, self.x - self.size, self.y, self.x + self.size, self.y, 11)
    def auto_shoot(self):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(60, 120); pyxel.play(SOUND_LASER_SHOOT, 11)
            return Laser(self.x, self.y, angle=random.uniform(0, 2 * math.pi))
        return None
    def is_colliding(self, bullet):
        return math.hypot(self.x - (bullet.x + bullet.w/2), self.y - (bullet.y + bullet.h/2)) < self.size + 2

class FunnelItem:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h = x, y, 8, 8; self.alive, self.speed_x, self.frame = True, -0.5, 0
    def update(self):
        self.x += self.speed_x; self.y += math.sin(self.frame * 0.08) * 4; self.frame += 1
        if self.x < -self.w: self.alive = False
    def draw(self):
        if (self.frame // 4) % 2 == 0:
            cx, cy, size = self.x + self.w/2, self.y + self.h/2, self.w/2
            pyxel.tri(cx, cy - size, cx - size, cy, cx + size, cy, 11)
            pyxel.tri(cx, cy + size, cx - size, cy, cx + size, cy, 11)
    def is_colliding(self, frog): return (self.x < frog.x + frog.w and self.x + self.w > frog.x and self.y < frog.y + frog.h and self.y + self.h > frog.y)

class Missile:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h, self.damage = x, y, 6, 6, 2
        self.speed, self.angle, self.turn_speed = 2.0, 0.0, 4.0
        self.target = None
    def update(self, enemies):
        if self.target is None or not self.target.alive: self.target = self.find_closest_enemy(enemies)
        if self.target:
            target_angle = math.degrees(math.atan2(self.target.y - self.y, self.target.x - self.x))
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += max(-self.turn_speed, min(self.turn_speed, angle_diff))
        self.x += self.speed * math.cos(math.radians(self.angle)); self.y += self.speed * math.sin(math.radians(self.angle))
    def find_closest_enemy(self, enemies):
        closest_enemy, min_dist = None, float('inf')
        for enemy in enemies:
            if not enemy.alive: continue
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < min_dist: min_dist, closest_enemy = dist, enemy
        return closest_enemy
    def draw(self):
        angle_rad = math.radians(self.angle)
        p1_x, p1_y = self.x + self.w*math.cos(angle_rad), self.y + self.h*math.sin(angle_rad)
        p2_x, p2_y = self.x + self.w*0.5*math.cos(angle_rad+math.radians(150)), self.y + self.h*0.5*math.sin(angle_rad+math.radians(150))
        p3_x, p3_y = self.x + self.w*0.5*math.cos(angle_rad-math.radians(150)), self.y + self.h*0.5*math.sin(angle_rad-math.radians(150))
        pyxel.tri(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, 8)
        tail_x, tail_y = self.x - self.w*0.7*math.cos(angle_rad), self.y - self.h*0.7*math.sin(angle_rad)
        pyxel.circ(tail_x, tail_y, random.uniform(1, 2.5), random.choice([9, 10]))
    def is_offscreen(self): return self.x < -self.w or self.x > SCREEN_WIDTH or self.y < -self.h or self.y > SCREEN_HEIGHT

class MissileItem:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h = x, y, 8, 8; self.alive, self.speed_x, self.frame = True, -0.5, 0
    def update(self):
        self.x += self.speed_x; self.y += math.sin(self.frame * 0.12) * 6; self.frame += 1
        if self.x < -self.w: self.alive = False
    def draw(self):
        if (self.frame // 4) % 2 == 0:
            cx, cy, size = self.x + self.w/2, self.y + self.h/2, self.w/2
            pyxel.tri(cx + size, cy, cx - size, cy - size, cx - size, cy + size, 8)
    def is_colliding(self, frog): return (self.x < frog.x + frog.w and self.x + self.w > frog.x and self.y < frog.y + frog.h and self.y + self.h > frog.y)

class Frog:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h = x, y, FROG_WIDTH, FROG_HEIGHT; self.alive, self.direction, self.animation_frame = True, 1, 0
        self.hp = FROG_MAX_HP; self.forces, self.funnels, self.history = [], [], []; self.has_missile = False
    def add_force(self): self.forces.append(Force(len(self.forces) * FORCE_DELAY + FORCE_DELAY)); pyxel.play(SOUND_ITEM_GET, 10)
    def add_funnel(self): self.funnels.append(Funnel(self)); pyxel.play(SOUND_ITEM_GET, 10)
    def add_missile(self): self.has_missile = True; pyxel.play(SOUND_ITEM_GET, 10)
    def update(self):
        if pyxel.btn(pyxel.KEY_UP): self.y = max(0, self.y - 2)
        if pyxel.btn(pyxel.KEY_DOWN): self.y = min(SCREEN_HEIGHT - self.h, self.y + 2)
        if pyxel.btn(pyxel.KEY_LEFT): self.x = max(0, self.x - 2); self.direction = -1
        if pyxel.btn(pyxel.KEY_RIGHT): self.x = min(SCREEN_WIDTH - self.w, self.x + 2); self.direction = 1
        self.history.insert(0, (self.x, self.y))
        if len(self.history) > len(self.forces) * FORCE_DELAY + 10: self.history.pop()
        for force in self.forces: force.update(self.history)
        for funnel in self.funnels: funnel.update()
        self.animation_frame = (self.animation_frame + 1) % 10
    def draw(self):
        for force in self.forces: force.draw()
        for funnel in self.funnels: funnel.draw()
        u, offset_y = (0, 3) if self.direction == 1 else (16, 3)
        if self.animation_frame not in [3, 6]: offset_y = 0
        pyxel.blt(self.x, self.y + offset_y, 0, u, 0, self.w * self.direction, self.h, 0)
    def shoot(self):
        new_bullets = [Bullet(self.x + self.w / 2, self.y)]
        for force in self.forces:
            if force.x >= 0: new_bullets.append(force.shoot())
        return new_bullets
    def is_colliding(self, obj): return (self.x-3 < obj.x+obj.w and self.x+self.w+3 > obj.x and self.y-3 < obj.y+obj.h and self.y+self.h+3 > obj.y)
    def take_damage(self, damage): self.hp = max(0, self.hp - damage); self.alive = self.hp > 0
    def draw_hp_bar(self, x, y):
        bar_width = int(HP_BAR_WIDTH * (self.hp / FROG_MAX_HP)); pyxel.rect(x, y, HP_BAR_WIDTH, HP_BAR_HEIGHT, 8); pyxel.rect(x, y, bar_width, HP_BAR_HEIGHT, 10)

class Bullet:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h = x, y, BULLET_WIDTH, BULLET_HEIGHT
        self.speed, self.damage = 4, 1
    def update(self): self.x += self.speed
    def draw(self): pyxel.rect(self.x, self.y + 4, self.w, self.h, 10)
    def is_offscreen(self): return self.x > SCREEN_WIDTH

class Laser:
    def __init__(self, x, y, angle, width=2, color=10, duration=15):
        self.x, self.y, self.angle_rad, self.width, self.color, self.duration, self.damage = x, y, angle, width, color, duration, 1
        self.length = SCREEN_WIDTH * 1.5
    def update(self): self.duration -= 1; return self.duration <= 0
    def draw(self):
        end_x, end_y = self.x + self.length * math.cos(self.angle_rad), self.y + self.length * math.sin(self.angle_rad)
        pyxel.line(self.x, self.y, end_x, end_y, self.color); pyxel.line(self.x + 1, self.y, end_x + 1, end_y, self.color)
    def is_colliding(self, enemy):
        x1, y1 = self.x, self.y; x2, y2 = self.x + self.length*math.cos(self.angle_rad), self.y + self.length*math.sin(self.angle_rad)
        cx, cy = enemy.x + enemy.w/2, enemy.y + enemy.h/2
        len_sq = (x2-x1)**2 + (y2-y1)**2
        if len_sq == 0.0: return math.hypot(cx - x1, cy - y1) < (enemy.w + enemy.h) / 2
        t = max(0, min(1, ((cx-x1)*(x2-x1) + (cy-y1)*(y2-y1)) / len_sq))
        dist = math.hypot(cx - (x1 + t*(x2-x1)), cy - (y1 + t*(y2-y1)))
        return dist < (enemy.w / 2) + self.width

class EnemyBullet:
    ### <<< 変更箇所 >>> ###
    def __init__(self, x, y, stage_number):
        self.x, self.y, self.w, self.h = x, y, BULLET_WIDTH, BULLET_HEIGHT
        # ステージレベルに応じて弾速アップ
        self.speed = -(2 + stage_number * 0.08)
    def update(self): self.x += self.speed
    def draw(self): pyxel.rect(self.x, self.y + 4, self.w, self.h, 8)
    def is_offscreen(self): return self.x < 0

class Enemy:
    def __init__(self, x, y, enemy_type, stage_number):
        self.x, self.y, self.w, self.h = x, y, ENEMY_WIDTH, ENEMY_HEIGHT
        self.stage_number = stage_number # ### <<< 追加 >>> ###
        self.speed = random.uniform(1, 4) + stage_number*0.05
        self.alive, self.type, self.animation_frame = True, enemy_type, 0
        self.pattern = random.randint(0, 1)
        self.explosion, self.drop_item_on_death = None, (self.type == 2)
        
        ### <<< 変更箇所 >>> ###
        # HP: 3ステージごとに1増加
        self.max_hp = 1 + (stage_number // 3)
        self.hp = self.max_hp
        
        # 攻撃頻度: ステージが進むと間隔が短くなる
        self.shoot_delay = max(20, random.randint(100, 180) - stage_number * 3)
        self.shoot_timer = 0
        
        # 接触ダメージ: 2ステージごとに1増加
        base_damage = 10
        if self.type == 1: base_damage = 20
        elif self.type == 2: base_damage = 30
        self.damage = base_damage + (stage_number // 2)

        if self.type == 0: self.score_value, self.image_x, self.image_y = 10, 0, 16
        elif self.type == 1: self.speed_y = random.uniform(0.5, 1.5) + stage_number*0.05; self.score_value, self.image_x, self.image_y = 20, 16, 16
        elif self.type == 2: self.score_value, self.image_x, self.image_y = 30, 32, 16
    
    def update(self):
        self.x -= self.speed
        if self.type == 1:
            if self.pattern == 0: self.y += self.speed_y
            else: self.y = 50 + 30 * math.sin(self.x / 30)
            if self.y > SCREEN_HEIGHT - self.h or self.y < 0: self.speed_y *= -1
        if self.x < -self.w: self.alive = False
        self.animation_frame = (self.animation_frame + 1) % 4
        if self.type == 2:
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_delay:
                self.shoot_timer = 0
                return EnemyBullet(self.x, self.y, self.stage_number)
        return None
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            
    def draw(self):
        pyxel.blt(self.x, self.y, 0, self.image_x, self.image_y, self.w, self.h, 0)
        # HPバーを描画
        if self.hp < self.max_hp:
            hp_ratio = self.hp / self.max_hp
            bar_color = 10 if hp_ratio > 0.5 else 9 if hp_ratio > 0.25 else 8
            pyxel.rect(self.x, self.y - 4, self.w * hp_ratio, 2, bar_color)
    
    def is_colliding(self, bullet): return (self.x-3 < bullet.x+bullet.w and self.x+self.w+3 > bullet.x and self.y-3 < bullet.y+bullet.h and self.y+self.h+3 > bullet.y)
    def explode(self): self.explosion = Explosion(self.x, self.y); pyxel.play(SOUND_ENEMY_DEATH, 1)

class Explosion:
    def __init__(self, x, y): self.x, self.y, self.frame = x, y, 0
    def update(self): self.frame += 1; return self.frame > 15
    def draw(self): pyxel.blt(self.x, self.y, 0, 48, 16, 16, 16, 0)

class Stage:
    def __init__(self, stage_number):
        self.stage_number = stage_number
        self.enemy_spawn_interval = max(2, ENEMY_SPAWN_INTERVAL - stage_number * 1.5)
        self.background_color, self.enemy_types = stage_number % 16, [0, 1, 2]
    def draw(self): pyxel.cls(self.background_color)

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT); pyxel.load("frog_shooting.pyxres"); pyxel.playm(MUSIC_STAGE, loop=True)
        self.frog = Frog(32, pyxel.height // 2)
        self.bullets, self.enemy_bullets, self.enemies, self.explosions, self.lasers, self.missiles = [], [], [], [], [], []
        self.stars = [Star(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(STAR_COUNT)]
        self.force_items, self.funnel_items, self.missile_items = [], [], []
        self.score, self.frame_count, self.game_over, self.stage_cleared = 0, 0, False, False
        self.stage_number, self.stage, self.missile_cooldown = 1, Stage(1), 0
        self.frog.add_force()
        pyxel.run(self.update, self.draw)

    def reset_for_next_stage(self):
        self.bullets, self.enemy_bullets, self.enemies, self.explosions, self.lasers, self.missiles = [], [], [], [], [], []
        self.force_items, self.funnel_items, self.missile_items = [], [], []
        self.frog.hp, self.frog.alive, self.stage_cleared = FROG_MAX_HP, True, False

    def update(self):
        if self.game_over or self.stage_cleared: return
        self.frame_count += 1
        if self.frog.alive: self.frog.update()
        
        for group in [self.stars, self.bullets, self.enemy_bullets, self.force_items, self.funnel_items, self.missile_items]:
            for obj in group: obj.update()
        for obj in self.explosions[:]:
            if obj.update(): self.explosions.remove(obj)
        for obj in self.lasers[:]:
            if obj.update(): self.lasers.remove(obj)
        for obj in self.missiles: obj.update(self.enemies)
        
        for funnel in self.frog.funnels:
            if new_laser := funnel.auto_shoot(): self.lasers.append(new_laser)
        if self.frog.has_missile:
            self.missile_cooldown -= 1
            if self.missile_cooldown <= 0 and self.enemies:
                self.missiles.append(Missile(self.frog.x + self.frog.w / 2, self.frog.y + self.frog.h / 2)); self.missile_cooldown = 45

        for enemy in self.enemies[:]:
            if bullet := enemy.update(): self.enemy_bullets.append(bullet)
        self.enemies = [e for e in self.enemies if e.alive]
        if self.frame_count % self.stage.enemy_spawn_interval == 0:
            self.enemies.append(Enemy(SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT - ENEMY_HEIGHT), random.choice(self.stage.enemy_types), self.stage_number))

        self.bullets = [b for b in self.bullets if not b.is_offscreen()]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.is_offscreen()]
        self.missiles = [m for m in self.missiles if not m.is_offscreen()]
        self.force_items, self.funnel_items, self.missile_items = [i for i in self.force_items if i.alive], [i for i in self.funnel_items if i.alive], [i for i in self.missile_items if i.alive]

        # Player projectiles vs Enemies
        projectiles = self.bullets + self.missiles
        for proj in projectiles:
            for enemy in self.enemies[:]:
                if enemy.alive and enemy.is_colliding(proj):
                    enemy.take_damage(proj.damage)
                    if not enemy.alive: self.handle_enemy_destruction(enemy)
                    if proj in self.bullets: self.bullets.remove(proj)
                    elif proj in self.missiles: self.missiles.remove(proj)
                    break
        for laser in self.lasers:
            for enemy in self.enemies[:]:
                if enemy.alive and laser.is_colliding(enemy):
                    enemy.take_damage(laser.damage)
                    if not enemy.alive: self.handle_enemy_destruction(enemy)

        # Enemy projectiles vs Shields
        for bullet in self.enemy_bullets[:]:
            if any(shield.is_colliding(bullet) for shield in self.frog.forces + self.frog.funnels): self.enemy_bullets.remove(bullet)
        
        # Player vs Dangers
        if self.frog.alive:
            for bullet in self.enemy_bullets[:]:
                if self.frog.is_colliding(bullet): self.frog.take_damage(10); self.enemy_bullets.remove(bullet); break
            for enemy in self.enemies[:]:
                if self.frog.is_colliding(enemy):
                    self.frog.take_damage(enemy.damage)
                    enemy.take_damage(999) # 敵も即死
                    if not enemy.alive: self.handle_enemy_destruction(enemy, no_item=True)
                    break
            for item in self.force_items[:]:
                if item.is_colliding(self.frog): self.frog.add_force(); self.force_items.remove(item)
            for item in self.funnel_items[:]:
                if item.is_colliding(self.frog): self.frog.add_funnel(); self.funnel_items.remove(item)
            for item in self.missile_items[:]:
                if item.is_colliding(self.frog): self.frog.add_missile(); self.missile_items.remove(item)

        if not self.frog.alive: self.game_over = True
        
        if self.frog.alive and (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)): self.bullets.extend(self.frog.shoot())
        if self.score >= (500 + self.stage_number * 100): self.stage_cleared = True
    
    def handle_enemy_destruction(self, enemy, no_item=False):
        self.score += enemy.score_value
        enemy.explode(); self.explosions.append(enemy.explosion)
        if not no_item and enemy.drop_item_on_death and random.randint(0, 3) == 0:
            item_choices = ['force', 'funnel']
            if not self.frog.has_missile: item_choices.append('missile')
            item_type = random.choice(item_choices)
            if item_type == 'force': self.force_items.append(ForceItem(enemy.x, enemy.y))
            elif item_type == 'funnel': self.funnel_items.append(FunnelItem(enemy.x, enemy.y))
            elif item_type == 'missile': self.missile_items.append(MissileItem(enemy.x, enemy.y))
        if enemy in self.enemies: self.enemies.remove(enemy)

    def draw(self):
        self.stage.draw()
        for star in self.stars: star.draw()
        if not self.game_over:
            if not self.stage_cleared:
                self.frog.draw(); self.frog.draw_hp_bar(5, 15)
                for group in [self.enemies, self.bullets, self.enemy_bullets, self.force_items, self.funnel_items, self.missile_items, self.explosions, self.lasers, self.missiles]:
                    for obj in group: obj.draw()
                pyxel.text(5, 5, f"SCORE: {self.score}", 7); pyxel.text(5, 25, f"STAGE: {self.stage_number}", 7)
            else:
                pyxel.text(SCREEN_WIDTH//2-40, SCREEN_HEIGHT//2-10, "STAGE CLEAR!", 7)
                pyxel.text(SCREEN_WIDTH//2-70, SCREEN_HEIGHT//2+5, "PRESS SPACE TO NEXT STAGE", 7)
                if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                    self.stage_number += 1; self.stage = Stage(self.stage_number); self.reset_for_next_stage(); self.score = 0
        else:
            pyxel.text(SCREEN_WIDTH//2-30, SCREEN_HEIGHT//2-10, "GAME OVER", 8)
            pyxel.text(SCREEN_WIDTH//2-40, SCREEN_HEIGHT//2+5, f"SCORE: {self.score}", 7)
            pyxel.text(SCREEN_WIDTH//2-45, SCREEN_HEIGHT//2+15, f"REACHED STAGE: {self.stage_number}", 7)

App()