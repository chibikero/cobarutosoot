import pyxel
import random

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
ENEMY_SPAWN_INTERVAL = 30
FROG_MAX_HP = 100
HP_BAR_WIDTH = 50
HP_BAR_HEIGHT = 5
MAX_STAGE = 10  # 最大ステージ数

# サウンドチャンネル
SOUND_ENEMY_DEATH = 0
SOUND_BULLET_SHOOT = 1
SOUND_BOSS_DEATH = 2
MUSIC_STAGE = 0

class Star:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(0.5, 1.5)
        self.color = random.choice([7, 15])  # 白または灰色

    def update(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = SCREEN_WIDTH
            self.y = random.randint(0, SCREEN_HEIGHT)

    def draw(self):
        pyxel.pset(self.x, self.y, self.color)

class Frog:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = FROG_WIDTH
        self.h = FROG_HEIGHT
        self.alive = True
        self.direction = 1  # 1: 右, -1: 左
        self.animation_frame = 0
        self.hp = FROG_MAX_HP  # HPを追加

    def update(self):
        if (pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP)) and self.y > 0:
            self.y -= 2
        if (pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)) and self.y < SCREEN_HEIGHT - self.h:
            self.y += 2
        if (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)) and self.x > 0:
            self.x -= 2
            self.direction = -1
        if (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)) and self.x < SCREEN_WIDTH - self.w:
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
        pyxel.play(SOUND_BULLET_SHOOT, 0) # 弾発射音
        return Bullet(self.x + self.w // 2, self.y)

    def is_colliding(self, enemy):
        # カエルと敵の当たり判定を大きく
        return (self.x - 3 < enemy.x + enemy.w and
                self.x + self.w + 3 > enemy.x and
                self.y - 3 < enemy.y + enemy.h and
                self.y + self.h + 3 > enemy.y)

    def is_colliding_enemy_bullet(self, bullet):
        # カエルと敵弾の当たり判定を大きく
        return (self.x - 3 < bullet.x + BULLET_WIDTH and
                self.x + self.w + 3 > bullet.x and
                self.y - 3 < bullet.y + BULLET_HEIGHT and
                self.y + self.h + 3 > bullet.y)

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw_hp_bar(self, x, y):
        # HPバーの描画
        bar_width = int(HP_BAR_WIDTH * (self.hp / FROG_MAX_HP))
        pyxel.rect(x, y, HP_BAR_WIDTH, HP_BAR_HEIGHT, 8)  # 背景 (暗い赤)
        pyxel.rect(x, y, bar_width, HP_BAR_HEIGHT, 10)  # HP (明るい赤)

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 4
        self.is_enemy = False

    def update(self):
        self.x += self.speed

    def draw(self):
        pyxel.rect(self.x, self.y + 4, BULLET_WIDTH, BULLET_HEIGHT, 10)  # 明るい青

    def is_offscreen(self):
        return self.x > SCREEN_WIDTH

class EnemyBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = -2  # 敵の弾は左に飛ぶ
        self.is_enemy = True

    def update(self):
        self.x += self.speed

    def draw(self):
        pyxel.rect(self.x, self.y + 4, BULLET_WIDTH, BULLET_HEIGHT, 8)  # 赤

    def is_offscreen(self):
        return self.x < 0

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.w = ENEMY_WIDTH
        self.h = ENEMY_HEIGHT
        self.speed = random.uniform(1, 4)
        self.alive = True
        self.type = enemy_type
        self.animation_frame = 0
        self.pattern = random.randint(0, 1)  # 動きのパターンをランダムに決定
        self.shoot_delay = random.randint(60, 180)  # 射撃間隔
        self.shoot_timer = 0
        self.explosion = None  # 爆発エフェクト

        if self.type == 0:  # 基本的な敵
            self.score_value = 10
            self.image_x = 0
            self.image_y = 16
            self.damage = 10  # ダメージ
        elif self.type == 1:  # 上下に移動する敵
            self.speed_y = random.uniform(0.5, 1.5)
            self.score_value = 20
            self.image_x = 16
            self.image_y = 16
            self.damage = 20  # ダメージ
        elif self.type == 2:  # 弾を撃つ敵
            self.score_value = 30
            self.image_x = 32
            self.image_y = 16
            self.damage = 30  # ダメージ

    def update(self):
        self.x -= self.speed

        if self.type == 1:  # 上下に移動する敵
            if self.pattern == 0:
                self.y += self.speed_y
                if self.y > SCREEN_HEIGHT - self.h or self.y < 0:
                    self.speed_y *= -1  # 反転
            else:
                # サイン波のような動き
                self.y = 50 + 30 * pyxel.sin(self.x / 30)

        if self.x < -self.w:
            self.alive = False

        self.animation_frame = (self.animation_frame + 1) % 4  # アニメーション速度

        # 射撃処理
        if self.type == 2:
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_delay:
                self.shoot_timer = 0
                return EnemyBullet(self.x, self.y)  # 弾を返す
        return None

    def draw(self):
        pyxel.blt(self.x, self.y, 0, self.image_x, self.image_y, self.w, self.h, 0)

    def is_colliding(self, bullet):
        # 敵と弾の当たり判定を小さく
        return (self.x - 3 < bullet.x + BULLET_WIDTH and
                self.x + self.w + 3 > bullet.x and
                self.y - 3 < bullet.y + BULLET_HEIGHT and
                self.y + self.h + 3 > bullet.y)

    def explode(self):
        self.explosion = Explosion(self.x, self.y)
        pyxel.play(SOUND_ENEMY_DEATH, 1)

class Boss(Enemy):  # Enemyクラスを継承
    def __init__(self, x, y):
        super().__init__(x, y, 2)  # type2の敵として初期化
        self.w = 32  # ボスの幅を大きく
        self.h = 32  # ボスの高さを大きく
        self.speed = 1  # ボスの速度を遅く
        self.image_x = 0  # ボスの画像X座標
        self.image_y = 32  # ボスの画像Y座標 (pyxresでボス画像を32,32の位置に配置)
        self.score_value = 500  # ボスのスコア
        self.max_hp = 300  # ボスの最大HP
        self.hp = self.max_hp  # ボスのHP
        self.damage = 50
        self.shoot_delay = 30  # ボスの射撃間隔を短く
        self.pattern = 0
        self.type = 2

    def update(self):
        self.x -= self.speed

        # ボスの動き (上下運動)
        if self.pattern == 0:
            self.y += 1
            if self.y > SCREEN_HEIGHT - self.h or self.y < 0:
                self.pattern = 1
        else:
            self.y -= 1
            if self.y > SCREEN_HEIGHT - self.h or self.y < 0:
                self.pattern = 0

        if self.x < -self.w:
            self.alive = False

        # 射撃処理
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            return EnemyBullet(self.x, self.y + self.h // 2)  # ボスは中心から弾を撃つ

        return None

    def draw(self):
        pyxel.blt(self.x, self.y, 0, self.image_x, self.image_y, self.w, self.h, 0)

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def is_colliding(self, bullet):
        return (self.x - 3 < bullet.x + BULLET_WIDTH and
                self.x + self.w + 3 > bullet.x and
                self.y - 3 < bullet.y + BULLET_HEIGHT and
                self.y + self.h + 3 > bullet.y)

    def explode(self):
        self.explosion = Explosion(self.x, self.y, is_boss=True)
        pyxel.play(SOUND_BOSS_DEATH, 2)

class Explosion:
    def __init__(self, x, y, is_boss=False):
        self.x = x
        self.y = y
        self.frame = 0
        self.is_boss = is_boss

    def update(self):
        self.frame += 1
        return self.frame > 15  # 15フレームで消滅

    def draw(self):
        # 爆発エフェクトを描画
        if self.is_boss:
          pyxel.blt(self.x - 8, self.y - 8, 0, 32, 0, 32, 32, 0)
        else:
          pyxel.blt(self.x, self.y, 0, 48, 16, 16, 16, 0)

class Stage:
    def __init__(self, stage_number):
        self.stage_number = stage_number
        self.enemy_spawn_interval = ENEMY_SPAWN_INTERVAL - stage_number * 2  # ステージが進むごとに敵の出現頻度を上げる
        if self.enemy_spawn_interval < 5:
            self.enemy_spawn_interval = 5
        self.background_color = stage_number % 16  # 背景色をステージ数で変化
        self.enemy_types = [0, 1, 2]  # 出現する敵の種類

        # ステージごとの初期化処理 (背景、敵の種類、出現頻度など)
        if stage_number == 1:
            self.enemy_types = [0, 1]
        elif stage_number == 2:
            self.enemy_types = [1, 2]
        elif stage_number == 3:
            self.enemy_types = [0, 2]
        # 以降、必要に応じてステージごとの設定を追加

    def update(self):
        # ステージ固有の更新処理 (時間経過による変化など)
        pass

    def draw(self):
        # ステージ固有の描画処理 (背景など)
        pyxel.cls(self.background_color)  # 背景色を設定

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT)  # 画面サイズ変更
        pyxel.load("frog_shooting.pyxres")

        # サウンドの設定 (pyxresファイルで定義)
        # BGMの再生
        pyxel.playm(MUSIC_STAGE, loop=True)

        self.frog = Frog(32, pyxel.height // 2)
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []  # 爆発エフェクトリスト
        self.stars = [Star(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(STAR_COUNT)]
        self.score = 0
        self.frame_count = 0  # フレーム数をカウント
        self.game_over = False  # ゲームオーバーフラグ
        self.stage_number = 1  # 現在のステージ番号
        self.stage = Stage(self.stage_number)
        self.stage_cleared = False
        self.boss = None  # ボス

        pyxel.run(self.update, self.draw)

    def reset_for_next_stage(self):
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.frog.hp = FROG_MAX_HP
        self.frog.alive = True
        self.stage_cleared = False
        self.boss = None

    def update(self):
        if self.game_over:
            return  # ゲームオーバーなら更新処理を停止

        if self.stage_cleared:
            return  # ステージクリア中は更新を停止

        self.frame_count += 1

        # ステージの更新
        self.stage.update()

        # 星の更新
        for star in self.stars:
            star.update()

        # カエルの更新
        if self.frog.alive:  # カエルが生きている時のみ更新
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

        if self.stage_number != MAX_STAGE:  # MAX_STAGE以外は通常の敵を生成
            # 敵の生成 (ステージごとに敵の出現頻度を変える)
            if self.frame_count % self.stage.enemy_spawn_interval == 0:
                enemy_type = random.choice(self.stage.enemy_types)  # ステージに合わせた敵タイプを選択
                self.enemies.append(Enemy(SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT - ENEMY_HEIGHT), enemy_type))
        else:  # MAX_STAGEはボスを生成
            if self.boss is None:  # ボスがいない時
                self.boss = Boss(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # ボスを生成
            else:  # ボスがいる時
                enemy_bullet = self.boss.update()  # ボスの更新
                if enemy_bullet:
                    self.enemy_bullets.append(enemy_bullet)

        # 敵の更新
        for enemy in self.enemies:
            enemy_bullet = enemy.update()
            if enemy_bullet:
                self.enemy_bullets.append(enemy_bullet)

        # 敵が画面外に出たら削除
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

        # 爆発エフェクトの更新
        for explosion in self.explosions[:]:
            if explosion.update():  # 更新処理をして、消滅判定があったら
                self.explosions.remove(explosion)  # リストから削除

        # 衝突判定 (弾丸 vs 敵)
        for bullet in self.bullets[:]:  # リストをコピーしてイテレート
            for enemy in self.enemies[:]:  # リストをコピーしてイテレート
                if enemy.is_colliding(bullet):
                    self.score += enemy.score_value  # 敵の種類に応じてスコアを加算
                    enemy.explode()  # 爆発エフェクト
                    self.explosions.append(enemy.explosion)
                    self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    break

        # 衝突判定 (弾丸 vs ボス)
        if self.boss and self.boss.alive:  # ボスが生きているとき
            for bullet in self.bullets[:]:
                if self.boss.is_colliding(bullet):
                    self.boss.take_damage(20)  # 仮のダメージ量
                    self.score += self.boss.score_value
                    self.bullets.remove(bullet)
                    if self.boss.hp <= 0:
                        self.boss.explode()  # 爆発エフェクト
                        self.explosions.append(self.boss.explosion)
                        self.boss.alive = False
                        self.stage_cleared = True
                    break

        # カエルと敵の衝突判定
        for enemy in self.enemies[:]:
            if self.frog.alive and self.frog.is_colliding(enemy):  # カエルが生きているときのみ当たり判定
                self.frog.take_damage(enemy.damage)  # ダメージを受ける
                enemy.explode()  # 爆発エフェクト
                self.explosions.append(enemy.explosion)
                self.enemies.remove(enemy)  # 敵を削除
                if not self.frog.alive:
                    self.game_over = True
                    break

        # カエルと敵の弾の衝突判定
        for bullet in self.enemy_bullets[:]:
            if self.frog.alive and self.frog.is_colliding_enemy_bullet(bullet):  # カエルが生きているときのみ当たり判定
                self.frog.take_damage(10)  # 固定ダメージ
                self.enemy_bullets.remove(bullet)
                if not self.frog.alive:
                    self.game_over = True
                    break

        # 弾丸の発射
        if self.frog.alive and (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):  # カエルが生きているときのみ弾を発射
            self.bullets.append(self.frog.shoot())

        # ステージクリア判定
        stage_clear_score = self.stage_number * 500  # ステージ数×500
        if self.score >= stage_clear_score:
            if self.stage_number != MAX_STAGE or (self.boss is not None and not self.boss.alive):  # MAX_STAGE以外 または ボスが倒されたら
                self.stage_cleared = True

        # ボスの当たり判定
        if self.boss and self.frog.alive and self.frog.is_colliding(self.boss):
            self.frog.take_damage(self.boss.damage)
            if not self.frog.alive:
                self.game_over = True

        for bullet in self.enemy_bullets[:]:  # ボスの弾との当たり判定
            if self.boss and self.frog.alive and self.frog.is_colliding_enemy_bullet(bullet):
                self.frog.take_damage(10)
                self.enemy_bullets.remove(bullet)
                if not self.frog.alive:
                    self.game_over = True
                    break

    def draw(self):
        # ステージの描画
        self.stage.draw()

        # 星の描画
        for star in self.stars:
            star.draw()

        if not self.game_over:
            if not self.stage_cleared:
                self.frog.draw()
                self.frog.draw_hp_bar(5, 15)  # HPバーを描画
                for bullet in self.bullets:
                    bullet.draw()
                for bullet in self.enemy_bullets:
                    bullet.draw()
                for enemy in self.enemies:
                    enemy.draw()

                pyxel.text(5, 5, f"SCORE: {self.score}", 7)
                pyxel.text(5, 25, f"STAGE: {self.stage_number}", 7)  # ステージ番号を表示

                if self.boss and self.boss.alive:  # ボスを描画
                    self.boss.draw()

                # 爆発エフェクトを描画
                for explosion in self.explosions:
                    explosion.draw()
            else:
                if self.stage_number != MAX_STAGE:
                    pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 10, "STAGE CLEAR!", 7)
                    pyxel.text(SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 5, "PRESS SPACE TO NEXT STAGE", 7)
                else:
                    pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 10, "GAME CLEAR!", 7)
                    pyxel.text(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 5, "THANKS FOR PLAYING!", 7)

                if (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):  # スペースキーで次のステージへ
                    if self.stage_number < MAX_STAGE:  # MAX_STAGEより小さい場合
                        self.stage_number += 1
                        self.stage = Stage(self.stage_number)
                        self.reset_for_next_stage()
                        self.score = 0  # スコアをリセット
        else:
            pyxel.text(SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT // 2 - 10, "GAME OVER", 8)
            pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 + 5, f"SCORE: {self.score}", 7)  # スコアを表示

App()