import pyxel
import random

class Star:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(0.5, 1.5)
        self.color = random.choice([7, 15])  # 白または灰色

    def update(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = pyxel.width
            self.y = random.randint(0, pyxel.height)

    def draw(self):
        pyxel.pset(self.x, self.y, self.color)

class Frog:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 16
        self.h = 16
        self.alive = True
        self.direction = 1 # 1: 右, -1: 左
        self.animation_frame = 0

    def update(self):
        if (pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP)) and self.y > 0:
            self.y -= 2
        if (pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)) and self.y < pyxel.height - self.h:
            self.y += 2
        if (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)) and self.x > 0:
            self.x -= 2
            self.direction = -1
        if (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)) and self.x < pyxel.width - self.w:
            self.x += 2
            self.direction = 1

        self.animation_frame = (self.animation_frame + 1) % 10  # アニメーション速度

    def draw(self):
        # 方向に応じて画像を反転
        u = 0 if self.direction == 1 else 16

        # アニメーション: 若干上下に揺れる
        offset_y = 0
        if self.animation_frame == 3:
            offset_y = 3
        elif self.animation_frame == 6:
            offset_y = -3

        pyxel.blt(self.x, self.y + offset_y, 0, u, 0, self.w * self.direction, self.h, 0)  # 反転描画

    def shoot(self):
        return Bullet(self.x + self.w // 2, self.y)

    def is_colliding(self, enemy):
        return (self.x < enemy.x + enemy.w and
                self.x + self.w > enemy.x and
                self.y < enemy.y + enemy.h and
                self.y + self.h > enemy.y)

    def is_colliding_enemy_bullet(self, bullet):
        return (self.x < bullet.x + 4 and
                self.x + self.w > bullet.x and
                self.y < bullet.y + 2 and
                self.y + self.h > bullet.y)

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 4
        self.is_enemy = False

    def update(self):
        self.x += self.speed

    def draw(self):
        pyxel.rect(self.x, self.y + 4, 4, 2, 10)  # 明るい青

    def is_offscreen(self):
        return self.x > pyxel.width

class EnemyBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 0  # 敵の弾は左に飛ぶ
        self.is_enemy = True

    def update(self):
        self.x += self.speed

    def draw(self):
        pyxel.rect(self.x, self.y + 4, 4, 2, 8)  # 赤

    def is_offscreen(self):
        return self.x < 0

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.w = 16
        self.h = 16
        self.speed = random.uniform(1, 4)
        self.alive = True
        self.type = enemy_type
        self.animation_frame = 0
        self.pattern = random.randint(0,1) # 動きのパターンをランダムに決定
        self.shoot_delay = random.randint(60, 180) # 射撃間隔
        self.shoot_timer = 0

        if self.type == 0: # 基本的な敵
            self.score_value = 10
            self.image_x = 0
            self.image_y = 16
        elif self.type == 1: # 上下に移動する敵
            self.speed_y = random.uniform(0.5, 1.5)
            self.score_value = 20
            self.image_x = 16
            self.image_y = 16
        elif self.type == 2: # 弾を撃つ敵
            self.score_value = 30
            self.image_x = 32
            self.image_y = 16

    def update(self):
        self.x -= self.speed

        if self.type == 1: # 上下に移動する敵
           if self.pattern == 0:
              self.y += self.speed_y
              if self.y > pyxel.height - self.h or self.y < 0:
                  self.speed_y *= -1  # 反転
           else:
               # サイン波のような動き
               self.y = 50 + 30 * pyxel.sin(self.x / 30)

        if self.x < -self.w:
            self.alive = False
            #self.x = pyxel.width  # 画面右端から再出現

        self.animation_frame = (self.animation_frame + 1) % 4  # アニメーション速度

        # 射撃処理
        if self.type == 5:
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_delay:
                self.shoot_timer = 0
                return EnemyBullet(self.x, self.y) # 弾を返す
        return None

    def draw(self):
        pyxel.blt(self.x, self.y, 0, self.image_x, self.image_y, self.w, self.h, 0)

    def is_colliding(self, bullet):
        return (self.x < bullet.x + 4 and
                self.x + self.w > bullet.x and
                self.y < bullet.y + 6 and
                self.y + self.h > bullet.y + 4)

class App:
    def __init__(self):
        pyxel.init(256, 192,) # 画面サイズ変更
        pyxel.load("frog_shooting.pyxres")
        self.frog = Frog(32, pyxel.height // 2)
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.stars = [Star(random.randint(0, pyxel.width), random.randint(0, pyxel.height)) for _ in range(50)]
        self.score = 0
        self.frame_count = 0 # フレーム数をカウント
        self.game_over = False # ゲームオーバーフラグ
        pyxel.run(self.update, self.draw)

    def update(self):
        if self.game_over:
            return  # ゲームオーバーなら更新処理を停止

        self.frame_count += 1

        # 星の更新
        for star in self.stars:
            star.update()

        # カエルの更新
        self.frog.update()

        # 弾丸の更新
        for bullet in self.bullets:
            bullet.update()

        # 敵の弾丸の更新
        for bullet in self.enemy_bullets:
            bullet.update()

        # 弾丸が画面外に出たら削除
        self.bullets = [bullet for bullet in self.bullets if not bullet.is_offscreen()]
        self.enemy_bullets = [bullet for bullet in self.enemy_bullets if not bullet.is_offscreen()]

        # 敵の生成 (少し生成頻度を下げる)
        if self.frame_count % 30 == 0:
            enemy_type = random.randint(0, 2)  # 敵のタイプをランダムに決定
            self.enemies.append(Enemy(pyxel.width, random.randint(0, pyxel.height - 16), enemy_type))

        # 敵の更新
        for enemy in self.enemies:
            enemy_bullet = enemy.update()
            if enemy_bullet:
                self.enemy_bullets.append(enemy_bullet)

        # 敵が画面外に出たら削除
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

        # 衝突判定 (弾丸 vs 敵)
        for bullet in self.bullets[:]: # リストをコピーしてイテレート
            for enemy in self.enemies[:]: # リストをコピーしてイテレート
                if enemy.is_colliding(bullet):
                    self.score += enemy.score_value  # 敵の種類に応じてスコアを加算
                    self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    break

        # カエルと敵の衝突判定
        for enemy in self.enemies[:]:
            if self.frog.is_colliding(enemy):
                self.game_over = True
                break

        # カエルと敵の弾の衝突判定
        for bullet in self.enemy_bullets[:]:
            if self.frog.is_colliding_enemy_bullet(bullet):
                self.game_over = True
                break

        # 弾丸の発射
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
            self.bullets.append(self.frog.shoot())

    def draw(self):
        pyxel.cls(1)  # 濃い青
        # 星の描画
        for star in self.stars:
            star.draw()

        if not self.game_over:
            self.frog.draw()
            for bullet in self.bullets:
                bullet.draw()
            for bullet in self.enemy_bullets:
                bullet.draw()
            for enemy in self.enemies:
                enemy.draw()

            pyxel.text(5, 5, f"SCORE: {self.score}", 7)
        else:
            pyxel.text(pyxel.width // 2 - 30, pyxel.height // 2 - 10, "GAME OVER", 8)
            #pyxel.text(pyxel.width // 2 - 50, pyxel.height // 2 + 5, "PRESS SPACE TO RESTART", 7) # リスタートの指示を削除
            pyxel.text(pyxel.width // 2 - 40, pyxel.height // 2 + 5, f"SCORE: {self.score}", 7) # スコアを表示

App()