from xml.sax import handler
import pyxel
import random
from enum import Enum, IntEnum

from queue import Queue
import threading
import time
from mbit import Mbit, MAC_ADDRESSs

# デバッグ用
DEBUG_GAME = False  # False:通常, True:当たり判定表示
CAP_GAME = True  # False:通常, True:キャプチャ実施



# ゲーム定義
# OUTER_SIZE = (255, 200)    # 画面の大きさ
OUTER_SIZE = (240, 134)    # 画面の大きさ

# プレイヤー定義
# - プレイヤー大きさ
PLAYER_WIDTH = 16
PLAYER_HEIGHT = 16

# - プレイヤー位置
PLAYER_BASE_X = 10
PLAYER_BASE_Y = OUTER_SIZE[1] - PLAYER_HEIGHT - 4

# プレイヤー状態
class State(Enum):
    STANDING = 1  # 地面に立っている
    JUMPING = 2  # ジャンプ中

# カラーパレット
class Plt(IntEnum):
    BLACK = 0 # 000000
    NAVY = 1 # 2B335F
    PLUM = 2 # 7E2072 (ラズベリー、ロイヤルパープル)
    TURQUOISE = 3 # 19959C (ピーコックブルー、ナイトブルー)
    WINE_RED = 4 # 8B4852
    COBALT_BLUE = 5 # 395C98
    BABY_BLUE = 6 # A9C1FF
    SNOW_WHITE = 7 # EEEEEE
    MAGENTA = 8 # D4186C
    CAMEL_COLOR = 9 # D38441
    HONEY = 10 # E9C35B
    COBALT_GREEN = 11 # 70C6A9
    HYACINTH = 12 # 7696DE
    PEARL_GRAY = 13 # A3A3A3
    PINK = 14 # FF9798
    ASH_ROSE  = 15 # EDC7B0
    TRANS = 0   # 透過色
    BG = 12 # 背景色

# 障害物定義
HurdleType = {
    "type1":
        {
            "u": 0,
            "v": 152,
            "w": 16,
            "h": 16,
        },
    "type2":
        {
            "u": 0,
            "v": 168,
            "w": 16,
            "h": 16,
        },
    "type3":
        {
            "u": 16,
            "v": 152,
            "w": 16,
            "h": 32,
        },
}


class Effect:
    """エフェクト

    プレイヤーが障害物にぶつかった場合のエフェクト
    """
    def __init__(self):
        self.underEffect = []

    def start(self, fcount=20):
        self.underEffect.append([fcount])

    def move(self):
        for i in range(len(self.underEffect)-1, -1, -1):
            t = self.underEffect[i][0]
            if t == 1:
                self.underEffect.pop(i)
            else:
                self.underEffect[i][0] -= 1

    def draw(self, pos):
        img_x = 0
        for exp in self.underEffect:
            img_y = 120 if exp[0] % 2 == 0 else 136
            pyxel.blt(
                *pos,
                0,
                img_x, img_y,
                16, 16,
                Plt.TRANS
            )


class Player:
    """プレイヤーの管理
    """

    def __init__(self):
        self.init()

    def init(self):
        self.count = 3 # 残機
        self.x = PLAYER_BASE_X # プレイヤー表示水平位置
        self.y = PLAYER_BASE_Y # プレイヤー表示垂直位置
        self.w = PLAYER_WIDTH # プレイヤー表示水平幅
        self.h = PLAYER_HEIGHT # プレイヤー表示垂直幅
        self.state = State.STANDING
        self.vel = 0  # y方向の速度
        self.acc = 1  # 重力加速度
        self.vel_base = -20  # y方向の速度(初期値)
        self.acc_base = 1  # 重力加速度(初期値)


    def pos(self):
        return (self.x, self.y)

    def pos_for_hit(self):
        return ((self.x + self.w//2), (self.y + self.h//2))

    def dec(self):
        if self.count > 0:
            self.count -= 1

    def left(self):
        return self.count

    def move(self, ev_mbit=None):
        # キーボードイベント
        if pyxel.btnp(pyxel.KEY_SPACE) and self.state == State.STANDING:
            self.acc = self.acc_base
            self.vel = self.vel_base  # 初速を与える
            # ジャンプする
            self.state = State.JUMPING

        # キーボードイベント(for debug)
        if pyxel.btnp(pyxel.KEY_UP):
            self.vel_base -= 1
            print(f"vel_base:{self.vel_base}")

        # キーボードイベント(for debug)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.vel_base += 1
            print(f"vel_base:{self.vel_base}")

        # micro:bit event
        if ev_mbit is not None:
            print("ev_mbit is not None")
            if ev_mbit["action"] in "jump" and self.state == State.STANDING:
                print("ev_mbit : jump")
                self.vel_base = (-1) * ev_mbit["strength"]
                self.acc = self.acc_base
                self.vel = self.vel_base  # 初速を与える
                self.state = State.JUMPING
                # self.acc = self.acc_base
                # self.vel = self.vel_base  # 初速を与える
                # # ジャンプする
                # self.state = State.JUMPING



        # 更新
        self.vel += self.acc
        self.y += self.vel

        # 着地判定
        if self.y > PLAYER_BASE_Y:
            self.y = PLAYER_BASE_Y
            if self.state == State.JUMPING:
                self.state = State.STANDING

    def draw(self):
        # ジャンプ中の画柄
        if self.state == State.JUMPING:
            pyxel.blt(
                self.x, self.y,
                0,
                16, 0,
                PLAYER_WIDTH, PLAYER_HEIGHT,
                Plt.TRANS
            )
        # 走行中の画柄
        elif self.state == State.STANDING:
            pyxel.blt(
                self.x, self.y,
                0,
                0, 0,
                PLAYER_WIDTH, PLAYER_HEIGHT,
                Plt.TRANS
            )

        # デバッグ用 - 当たり判定位置の表示
        if DEBUG_GAME:
            pyxel.pset(self.x, self.y, Plt.MAGENTA)
            hit_pos = self.pos_for_hit()
            pyxel.pset(*hit_pos, Plt.MAGENTA)



class Hurdle:
    """障害物

    障害物の管理
    """
    def __init__(self):
        self.init()

    def init(self):
        self.hurdles = []   # x, y, u, v, w, h
        self.speed = 2
        self.max_count = 2

    def create(self):
        """障害物の生成
        """
        # 1画面中の最大障害数
        if len(self.hurdles) == self.max_count:
            return

        if pyxel.frame_count % 128 != 0:
            if random.randint(1, 10) != 1:
                return
            typ = "type" + str( random.randint(1, 3) )
            u, v = HurdleType[typ]["u"], HurdleType[typ]["v"]
            w, h = HurdleType[typ]["w"], HurdleType[typ]["h"]
            self.add(
                OUTER_SIZE[0] + 10, OUTER_SIZE[1] - h - 4, \
                    u, v, w, h)
        return

    def add(self, x, y, u, v, w, h):
        self.hurdles.append([x, y, u, v, w, h])

    def cal_hitrange(self, hardle):
        """当たり判定範囲の算出
        """
        off_x = 4
        off_y = 0
        return (hardle[0] + off_x), hardle[1] + off_y, \
                (hardle[4] - off_x*2), (hardle[5] - off_y*2)

    def hit_player(self, pos):
        """プレイヤーとの衝突判定
        """
        player_x, player_y = pos
        for i in range(len(self.hurdles)-1, -1, -1):
            h_x, h_y, h_w, h_h = self.cal_hitrange(self.hurdles[i])
            if h_x <= player_x and player_x <= (h_x + h_w) and \
                h_y <= player_y and player_y <= (h_y + h_h):
                self.hurdles.pop(i)
                return True
        return False

    def move(self):
        """障害物の移動
        """
        for i in range(len(self.hurdles)-1, -1, -1):
            if self.hurdles[i][0] < -10:
                self.hurdles.pop(i)
            else:
                self.hurdles[i][0] -= self.speed

    def draw(self):
        """障害物の描画
        """
        for hurdle in self.hurdles:
            pyxel.blt(
                hurdle[0], hurdle[1],   # x, y
                0,
                hurdle[2], hurdle[3],   # u, v
                hurdle[4], hurdle[5],   # w, h
                Plt.TRANS
            )
            # 障害物の
            if DEBUG_GAME:
                x, y, w, h = self.cal_hitrange(hurdle)
                pyxel.rectb(x, y, w, h, Plt.MAGENTA)


class Sand:
    """砂の装飾管理
    """

    def __init__(self):
        self.num_of_stars = 80
        self.sands = []
        for i in range(self.num_of_stars):
            self.sands.append([
                random.randint(0, OUTER_SIZE[0]),
                random.randint(OUTER_SIZE[1] - 16, OUTER_SIZE[1] - 8),
                random.randint(2, 15)
            ])

    def move(self):
        for i in range(self.num_of_stars):
            self.sands[i][0] -= 1
            if self.sands[i][0] < 0:
                self.sands[i][0] = OUTER_SIZE[0]
                self.sands[i][1] = random.randint(OUTER_SIZE[1] - 16, OUTER_SIZE[1] - 8)

    def draw(self):
        for i in range(self.num_of_stars):
            pyxel.pset(self.sands[i][0], self.sands[i][1], self.sands[i][2])


class Score:
    """点数管理
    """

    def __init__(self):
        self.init()
        self.hi_score = 0

    def init(self):
        self.score = 0

    def add(self, n):
        self.score += n
        self.hi_score = max(self.score, self.hi_score)

    def value(self):
        return self.score

    def hi_value(self):
        return self.hi_score


class Sound:
    """音声の管理
    """

    def __init__(self):
        # プレイヤーの衝突音
        pyxel.sound(1).set("f0f1", "n", "7", "s", 15)

    def playerBomb(self):
        pyxel.play(1, 1)




class Game:
    """ゲーム全体の管理
    """

    def __init__(self, rcv_que):
        # pyxelの初期化
        if CAP_GAME:
            pyxel.init(*OUTER_SIZE, title="JUMP GAME", display_scale=8, capture_scale=1, capture_sec=10)
        else:
            pyxel.init(*OUTER_SIZE, title="JUMP GAME", display_scale=8)

        # 各キャラクタの準備
        pyxel.load("jump_game.pyxres")
        self._rcv_que = rcv_que
        self.hurdle = Hurdle()
        self.sand = Sand()
        self.player = Player()
        self.effect = Effect()
        self.score = Score()
        self.sound = Sound()
        self.demoMode = True
        self.scene = 0

        self.far_cloud = [(-10, 75), (40, 65), (90, 60)]
        self.near_cloud = [(10, 25), (70, 35), (120, 15)]

        # pyxelの実行
        pyxel.run(self.update, self.draw)

    def init(self):
        self.hurdle.init()
        self.scene += 1

    def demoPlay(self):
        if self.player.left() == 0:
            pyxel.text(40+58, 40, "GAME OVER", 8)
        pyxel.text(40+50, 60, "Pyxel-JUMP GAME", 7)
        pyxel.text(40+45, 76, "START : SPACE KEY", 7)
        pyxel.text(40+50, 92, f"HIGH SCORE {self.score.hi_value()}", 7)
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.demoMode = False
            self.score.init()
            self.player.init()
            self.scene = 0
            self.init()

    def update(self):
        """フレーム更新時の処理"""

        # キー入力チェック
        # 各キャラクタの移動
        self.hurdle.create()
        self.hurdle.move()
        self.sand.move()
        self.effect.move()

        if self.demoMode:
            return

        if self._rcv_que.empty():
            m_ev = None
        else:
            m_ev = self._rcv_que.get()
        self.player.move(m_ev)

        if pyxel.frame_count % 16 == 0:
            self.score.add(10)

        # 衝突判定
        if self.hurdle.hit_player(self.player.pos_for_hit()):
            self.effect.start()
            self.sound.playerBomb()
            self.player.dec()
            self.hurdle.init()

        # 終了判定
        if self.player.left() == 0:
            self.demoMode = True

    def draw(self):
        """描画処理"""

        # 画面クリア
        pyxel.cls(Plt.BG)

        # 床の表示
        pyxel.rect(0, OUTER_SIZE[1] - 16, *OUTER_SIZE, Plt.ASH_ROSE)

        # 雲の表示
        offset = (pyxel.frame_count // 16) % 160
        for i in range(2):
            for x, y in self.far_cloud:
                pyxel.blt(x + i * 160 - offset, y, 0, 64, 32, 32, 8, 12)
        offset = (pyxel.frame_count // 8) % 160
        for i in range(2):
            for x, y in self.near_cloud:
                pyxel.blt(x + i * 160 - offset, y, 0, 0, 32, 56, 8, 12)

        # 各キャラクタの描画処理
        self.sand.draw()
        pyxel.text(10, 0,
                   " SCENE:{0:2d}   HI:{1:05d} SCORE:{2:05d} LEFT:{3:1d}".format(
                       self.scene,
                       self.score.hi_value(),
                       self.score.value(),
                       self.player.left()
                   ), 7)
        if self.demoMode:
            self.demoPlay()
        self.hurdle.draw()
        self.player.draw()
        self.effect.draw(self.player.pos())


if __name__ == "__main__":
    que_mbit = Queue()
    for ma in MAC_ADDRESSs:
        mbit_th = Mbit(ma, que_mbit)
        mbit_th.start()
    mbit_th = Mbit(que_mbit)
    mbit_th.start()

    Game(que_mbit)
