"""
ЛИЛУ: ПОЖИРАТЕЛЬ ВСЕЛЕННЫХ
Игра на pygame.
  ПК:      WASD или стрелки. Мышкой можно тянуть джойстик.
  Телефон: джойстик в правом нижнем углу (кружок в кружке).
"""
import os
import math
import random
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")

W, H = 540, 960          # логическое разрешение (портрет, как телефон)
FPS = 60
TAU = math.tau

WHITE = (255, 255, 255)
GOLD = (255, 214, 102)
PINK = (255, 120, 170)
SOFT = (230, 230, 245)
RED = (255, 80, 80)
DARK_TEXT = (30, 20, 40)

START_R = 4.0            # стартовый размер (атом)
PLAYER_SPEED = 1.6       # скорость = PLAYER_SPEED * размер
MAX_OBJECTS = 70         # сколько объектов одновременно на экране
JOY_RADIUS = 85
GROWTH_PER_EAT = 0.25     # сколько «массы» добавляет съеденный объект


def asset(name):
    return os.path.join(ASSETS, name)


def load_font(size):
    """Шрифт с кириллицей. Если положишь assets/font.ttf (например DejaVuSans) — будет он."""
    for name in ("font.ttf", "DejaVuSans.ttf"):
        path = asset(name)
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size + 8)


def load_dog():
    """Загружает фото Лилу и убирает фон (если фон прозрачный — берём как есть)."""
    path = asset("Lilu.png")
    if os.path.exists(path):
        try:
            raw = pygame.image.load(path)
            img = raw.convert_alpha()
            # если фон непрозрачный (белый) — вырезаем белое
            if img.get_at((0, 0)).a == 255:
                rgb = raw.convert()
                mask = pygame.mask.from_threshold(rgb, (255, 255, 255, 255), (28, 28, 28, 255))
                mask.invert()
                mask_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
                img.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            rect = img.get_bounding_rect()
            return img.subsurface(rect).copy()
        except Exception as e:  # запасной вариант, если картинка битая
            print("Не удалось загрузить Lilu.png:", e)
    # запасной рисунок, если файла нет
    surf = pygame.Surface((300, 300), pygame.SRCALPHA)
    pygame.draw.circle(surf, (235, 200, 160), (150, 150), 140)
    pygame.draw.circle(surf, (40, 30, 30), (105, 130), 16)
    pygame.draw.circle(surf, (40, 30, 30), (195, 130), 16)
    pygame.draw.circle(surf, (30, 20, 20), (150, 175), 14)
    return surf


def wrap_text(font, text, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = w if not cur else cur + " " + w
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_atom(surf, cx, cy, R, tnow):
    """Атом Лилу в начале игры: ядро и три орбиты с электронами."""
    nuc = max(4.0, R * 0.22)
    pygame.draw.circle(surf, (255, 110, 150), (int(cx), int(cy)), int(nuc))
    pygame.draw.circle(surf, (255, 205, 230),
                       (int(cx - nuc * 0.3), int(cy - nuc * 0.3)), max(2, int(nuc * 0.35)))
    for k in range(3):
        tilt = k * math.pi / 3 + 0.4

        def orbit_pt(a, tilt=tilt):
            x = math.cos(a) * R * 0.9
            y = math.sin(a) * R * 0.36
            return (cx + x * math.cos(tilt) - y * math.sin(tilt),
                    cy + x * math.sin(tilt) + y * math.cos(tilt))

        pts = [orbit_pt(i / 40 * TAU) for i in range(40)]
        pygame.draw.lines(surf, (110, 190, 255), True, pts, 2)
        ex, ey = orbit_pt(tnow * (1.6 + k * 0.5) + k * 2.1)
        pygame.draw.circle(surf, (170, 235, 255), (int(ex), int(ey)), max(3, int(R * 0.07)))


def draw_machine(scr, font, t):
    """Светящаяся машина с табличкой «НЕ НАЖИМАТЬ» (для катсцен)."""
    x, y = int(W * 0.68), int(H * 0.36)
    pygame.draw.rect(scr, (70, 74, 92), (x - 90, y, 180, 210), border_radius=14)
    pygame.draw.rect(scr, (40, 44, 60), (x - 70, y + 20, 140, 90), border_radius=8)
    glow = 150 + int(90 * math.sin(t * 4))
    pygame.draw.circle(scr, (glow, 40, 40), (x, y + 160), 26)
    pygame.draw.rect(scr, (30, 10, 12), (x - 100, y - 70, 200, 52), border_radius=8)
    pygame.draw.rect(scr, RED, (x - 100, y - 70, 200, 52), 2, border_radius=8)
    txt = font.render("НЕ НАЖИМАТЬ", True, RED)
    scr.blit(txt, txt.get_rect(center=(x, y - 44)))


def draw_button(scr, rect, text, font, primary=True):
    if primary:
        pygame.draw.rect(scr, GOLD, rect, border_radius=18)
        color = DARK_TEXT
    else:
        pygame.draw.rect(scr, (30, 30, 50), rect, border_radius=18)
        pygame.draw.rect(scr, SOFT, rect, 2, border_radius=18)
        color = SOFT
    t = font.render(text, True, color)
    scr.blit(t, t.get_rect(center=rect.center))


class Obj:
    __slots__ = ("x", "y", "r", "name", "color", "kind", "vx", "vy", "rot", "spin")

    def __init__(self, x, y, r, name, color, kind):
        self.x, self.y, self.r = x, y, r
        self.name, self.color, self.kind = name, color, kind
        self.vx = self.vy = 0.0
        self.rot = random.uniform(0, TAU)
        self.spin = random.uniform(-1.0, 1.0)


class Popup:
    def __init__(self, text, x, y, color):
        self.text, self.x, self.y, self.color, self.t = text, x, y, color, 0.0


TRACK_FOR_CHAPTER = ["early", "early", "early", "early", "space", "space", "cosmic", "cosmic"]


class Audio:
    """Музыка и звуки. Если звук недоступен, игра всё равно работает."""

    def __init__(self):
        self.enabled = True
        self.ok = False
        self.sfx = {}
        self.current = None
        try:
            pygame.mixer.init()
            self.ok = True
        except Exception as e:
            print("Звук недоступен:", e)
        if self.ok:
            for name in ("eat", "boom", "bump", "click"):
                path = asset(os.path.join("sfx", name + ".wav"))
                if os.path.exists(path):
                    try:
                        self.sfx[name] = pygame.mixer.Sound(path)
                    except Exception as e:
                        print("Не загрузился звук", name, e)

    def _music_volume(self):
        return 0.45 if self.enabled else 0.0

    def play_music(self, name):
        if not self.ok or name == self.current:
            return
        path = asset(os.path.join("music", name + ".wav"))
        if not os.path.exists(path):
            return
        self.current = name
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume())
            pygame.mixer.music.play(-1, fade_ms=600)
        except Exception as e:
            print("Не получилось включить музыку:", e)

    def play_sfx(self, name, vol=0.6):
        snd = self.sfx.get(name)
        if snd and self.enabled:
            snd.set_volume(vol)
            snd.play()

    def toggle(self):
        self.enabled = not self.enabled
        if self.ok:
            pygame.mixer.music.set_volume(self._music_volume())

    def label(self):
        return "ЗВУК: ВКЛ" if self.enabled else "ЗВУК: ВЫКЛ"


def S(text, speaker="", **kw):
    """Короткий помощник для описания слайда катсцены."""
    d = {"text": text, "speaker": speaker}
    d.update(kw)
    return d


# ---------------------------------------------------------------------------
#  СЮЖЕТ: катсцены
# ---------------------------------------------------------------------------
LAB_BG = (18, 22, 36)
SPACE_BG = (4, 4, 14)

INTRO = [
    S("Лаборатория доктора Фишкина. Поздний вечер. Все уже ушли домой... почти все.",
      bg=LAB_BG, machine=True),
    S("Из-под стола выкатилась собака по имени Лилу. Её интересует только одно: "
      "что тут так вкусно пахнет?",
      bg=LAB_BG, machine=True, fig="dog", fig_from=(0.05, 0.42), fig_to=(0.3, 0.42), fig_scale=0.9),
    S("На большой светящейся машине висит табличка «НЕ НАЖИМАТЬ». Лилу не умеет читать. "
      "Зато умеет нажимать лапой.",
      bg=LAB_BG, machine=True, fig="dog", fig_from=(0.3, 0.42), fig_to=(0.36, 0.42), fig_scale=0.9),
    S("Гав?.. А это что за красная кнопка?",
      speaker="Лилу", bg=LAB_BG, machine=True, fig="dog", fig_from=(0.36, 0.42),
      fig_to=(0.36, 0.42), fig_scale=0.9),
    S("БАМ!", bg=(0, 0, 0), flash=True),
    S("Лилу стала крошечным атомом. А мир вокруг стал огромным.",
      bg=SPACE_BG, stars=True, fig="atom", fig_from=(0.5, 0.5), fig_to=(0.5, 0.45), fig_scale=0.8),
    S("Гав?.. Почему всё такое большое? И почему мне так... хочется есть?",
      speaker="Лилу", bg=SPACE_BG, stars=True, fig="atom", fig_scale=0.8),
    S("Внутри атома что-то гудит. Пора начинать есть. Тяни джойстик справа внизу, "
      "а на компьютере — WASD или стрелки.",
      bg=SPACE_BG, stars=True, fig="atom", fig_scale=0.8),
]

FINAL = [
    S("Лилу сидит посреди пустоты. Всё съедено. Совсем всё. Тишина такая, "
      "что слышно, как хвост виляет.",
      bg=SPACE_BG, stars=True, fig="giant", fig_from=(0.5, 0.75), fig_to=(0.5, 0.7), fig_scale=0.9),
    S("Вдали, очень-очень далеко, горит крошечный огонёк. Лилу смотрит на него.",
      bg=SPACE_BG, stars=True, fig="lab_light", fig_from=(0.5, 0.45), fig_to=(0.5, 0.45)),
    S("«Лилу?! Где ты?! Почему в Солнечной системе не хватает Солнца?!» — кричит доктор Фишкин.",
      speaker="Доктор Фишкин", bg=SPACE_BG, stars=True, fig="lab_light",
      fig_from=(0.5, 0.45), fig_to=(0.5, 0.45)),
    S("Лилу облизнулась. Вселенная ей больше не интересна. Но очень хочется домой.",
      bg=SPACE_BG, stars=True, fig="dog", fig_from=(0.5, 0.6), fig_to=(0.5, 0.6), fig_scale=0.8),
    S("И тут Лилу выдохнула. Вся Вселенная стала размером с горошину у неё на носу.",
      bg=(0, 0, 0), stars=True, fig="dot", fig_from=(0.5, 0.45), fig_to=(0.5, 0.45)),
]

POST = [
    S("Тем временем в лаборатории...", bg=LAB_BG, machine=True),
    S("Маленький светящийся атом одиноко стоит на столе. Под столом раздалось тихое: «Гав?»",
      bg=LAB_BG, machine=True, fig="atom", fig_from=(0.5, 0.5), fig_to=(0.5, 0.5), fig_scale=0.6),
    S("Продолжение следует?", bg=(0, 0, 0), fig="dog", fig_from=(0.5, 0.6), fig_to=(0.5, 0.6),
      fig_scale=0.7),
]

CREDITS = [
    "ЛИЛУ",
    "Пожиратель Вселенных",
    "",
    "Главная героиня",
    "Лилу",
    "",
    "Учёный, который всё проспал",
    "Доктор Фишкин",
    "",
    "Режиссёр пожирания",
    "Лилу (без дублей)",
    "",
    "Особая благодарность",
    "Кнопке «НЕ НАЖИМАТЬ»",
    "",
    "Спасибо, что играете!",
]

# ---------------------------------------------------------------------------
#  ГЛАВЫ ИГРЫ. grow — во сколько раз вырастает Лилу в главе (от этого зависит длина).
#  palette — обычные объекты (съедобные), big — большие (станут съедобными, когда подрастёшь).
# ---------------------------------------------------------------------------
CHAPTERS = [
    {
        "title": "Лаборатория", "unit": "нм", "bg": (24, 30, 48), "style": "grid", "grow": 40,
        "palette": [
            ("пылинка", (190, 190, 200), "blob"),
            ("капля кофе", (120, 66, 34), "blob"),
            ("пробирка", (120, 220, 200), "square"),
            ("мячик Лилу", (240, 120, 140), "blob"),
            ("тапочек", (150, 100, 210), "square"),
            ("конфетка", (250, 200, 80), "star"),
        ],
        "big": [("табуретка", (170, 120, 80), "square"), ("микроскоп", (110, 120, 140), "square")],
        "intro": [],
        "outro": [
            S("Лаборатория съедена дочиста. Остались только обрывки пробирок и записка: "
              "«Кто-нибудь, выключите эту штуку».", bg=LAB_BG),
            S("Лилу больше не атом. Она... ну, почти собака. Пора осмотреть дом!", bg=LAB_BG,
              fig="dog", fig_scale=0.8),
        ],
    },
    {
        "title": "Квартира", "unit": "см", "bg": (44, 32, 40), "style": "grid", "grow": 45,
        "palette": [
            ("крошка от печенья", (200, 150, 90), "blob"),
            ("носок-призрак", (230, 230, 240), "blob"),
            ("пульт", (70, 70, 80), "square"),
            ("книжка", (200, 60, 60), "square"),
            ("чашка", (240, 240, 250), "blob"),
            ("клубок пыли", (170, 160, 150), "blob"),
        ],
        "big": [("диван", (120, 80, 160), "square"), ("холодильник", (220, 230, 240), "square")],
        "intro": [
            S("Квартира хозяина. Лилу нырнула под диван и нашла носок, который пропал ещё в прошлом году.",
              bg=(44, 32, 40), fig="dog", fig_scale=0.8),
        ],
        "outro": [
            S("Квартира пуста. Даже люстра теперь там, где ей и не место: в Лилу.",
              bg=(44, 32, 40)),
        ],
    },
    {
        "title": "Город", "unit": "м", "bg": (50, 70, 90), "style": "grid", "grow": 55,
        "palette": [
            ("машинка", (230, 80, 60), "square"),
            ("фонарь", (255, 230, 120), "star"),
            ("дерево", (60, 160, 80), "blob"),
            ("домик-печенька", (210, 160, 100), "square"),
            ("автобус", (240, 200, 40), "square"),
            ("велосипед", (80, 160, 240), "ring"),
        ],
        "big": [("небоскрёб", (90, 100, 130), "square"), ("мост", (130, 130, 140), "square")],
        "intro": [
            S("Лилу выбежала на улицу. Внизу — город. Машинки выглядят как конфетки, "
              "а дома — как печенье.", bg=(50, 70, 90), fig="giant", fig_scale=0.7,
              fig_from=(0.5, 0.7), fig_to=(0.5, 0.7)),
        ],
        "outro": [
            S("Город съеден. Мэр прислал письмо: «Лилу, пожалуйста, оставь хотя бы парк». "
              "Лилу оставила. Но только потому, что он был слишком колючий.", bg=(50, 70, 90)),
        ],
    },
    {
        "title": "Земля", "unit": "км", "bg": (30, 90, 130), "style": "stars", "grow": 60,
        "palette": [
            ("остров", (80, 180, 90), "blob"),
            ("город", (200, 200, 210), "blob"),
            ("гора", (140, 120, 100), "star"),
            ("озеро", (60, 140, 230), "blob"),
            ("лес", (40, 120, 60), "blob"),
            ("облако", (240, 240, 250), "blob"),
        ],
        "big": [("континент", (90, 170, 90), "blob"), ("океан", (40, 100, 200), "ring")],
        "intro": [
            S("Лилу вспомнила, что живёт на Земле. Вспомнила ровно настолько, чтобы понять: "
              "эта штука тоже очень вкусная.", bg=(30, 90, 130), fig="dog", fig_scale=0.6),
        ],
        "outro": [
            S("Земля стала крошечной и немного мокрой. Лилу сыта, но понимает, что это только начало. "
              "Её тянет в космос.", bg=(30, 90, 130)),
        ],
    },
    {
        "title": "Солнечная система", "unit": "млн км", "bg": (5, 5, 20), "style": "stars", "grow": 70,
        "palette": [
            ("астероид", (150, 140, 130), "star"),
            ("Луна-печенька", (210, 210, 200), "face"),
            ("Марс", (200, 80, 50), "blob"),
            ("Венера", (240, 200, 120), "blob"),
            ("кольцо Сатурна", (230, 200, 140), "ring"),
            ("комета", (200, 230, 255), "star"),
        ],
        "big": [("Юпитер", (220, 160, 110), "blob"), ("Нептун", (70, 110, 240), "blob")],
        "intro": [
            S("Солнечная система. Луна выглядит как печенька с трещинкой. Марс — как мячик. "
              "Юпитер — как очень большой мячик.", bg=(5, 5, 20), stars=True),
        ],
        "outro": [
            S("Солнце оказалось очень горячим и очень невкусным. Лилу больше никогда "
              "не будет брать его в рот. Ни за что.", bg=(5, 5, 20), stars=True),
        ],
    },
    {
        "title": "Галактика", "unit": "св. лет", "bg": (20, 8, 40), "style": "stars", "grow": 75,
        "palette": [
            ("звёздочка", (255, 240, 160), "star"),
            ("туманность", (200, 120, 255), "blob"),
            ("пульсар", (120, 255, 230), "star"),
            ("звезда-карлик", (255, 190, 120), "blob"),
            ("леденец", (255, 110, 170), "star"),
            ("чёрная дыра-малютка", (20, 20, 30), "ring"),
        ],
        "big": [("красный гигант", (255, 90, 60), "blob"), ("галактика-карлик", (170, 140, 255), "ring")],
        "intro": [
            S("Млечный Путь. Миллиарды звёзд, и все они выглядят как очень вкусные леденцы.",
              bg=(20, 8, 40), stars=True),
        ],
        "outro": [
            S("Галактика оказалась просто миской с мелочью. Лилу чихнула, и где-то родилась "
              "новая звезда.", bg=(20, 8, 40), stars=True),
        ],
    },
    {
        "title": "Космические хрени", "unit": "млрд св. лет", "bg": (10, 20, 50), "style": "stars", "grow": 90,
        "palette": [
            ("звёздный тапок", (255, 160, 200), "blob"),
            ("космическая гречка", (200, 160, 60), "blob"),
            ("тостер-планета", (180, 180, 190), "square"),
            ("пицца-туманность", (255, 120, 60), "blob"),
            ("хвостатая комета", (180, 240, 255), "star"),
            ("квазар-лайкер", (255, 80, 200), "face"),
        ],
        "big": [("Космический кит", (120, 170, 230), "face"), ("Галактический кот", (255, 150, 80), "face")],
        "intro": [
            S("Что-то огромное шевелится в глубине космоса. Длинное, пушистое, с хвостом. "
              "Оно смотрит прямо на Лилу.", bg=(10, 20, 50), stars=True),
            S("Это Космический кит! Он явно не против знакомства. Лилу — тоже.",
              speaker="Лилу", bg=(10, 20, 50), stars=True),
        ],
        "outro": [
            S("Кит оказался очень вкусным. Его хвост до сих пор летает где-то в туманности, "
              "если прислушаться.", bg=(10, 20, 50), stars=True),
            S("Лилу икнула, и из икоты родились три новые галактики. Она решила, что это хорошо.",
              bg=(10, 20, 50), stars=True),
        ],
    },
    {
        "title": "Вселенная", "unit": "Вселенных", "bg": (3, 0, 12), "style": "stars", "grow": 120,
        "palette": [
            ("пончик-галактика", (255, 180, 120), "ring"),
            ("сгусток времени", (160, 255, 200), "blob"),
            ("тёмная материя", (60, 40, 90), "blob"),
            ("маленькая вселенная", (120, 200, 255), "face"),
            ("осколок Большого взрыва", (255, 250, 200), "star"),
            ("мультивселенная", (200, 120, 255), "ring"),
        ],
        "big": [("Вселенная-пончик", (255, 200, 140), "ring"), ("Бесконечность", (255, 255, 255), "face")],
        "intro": [
            S("Вселенная. Всё, что осталось. Звёзды, пыль, пончиковые кольца времени. "
              "И единственный вопрос: чем бы закусить?", bg=(3, 0, 12), stars=True),
        ],
        "outro": [],
    },
]


# ---------------------------------------------------------------------------
#  КАТСЦЕНЫ
# ---------------------------------------------------------------------------
class Cutscene:
    def __init__(self, game, slides, on_done, default_bg=(0, 0, 0)):
        self.g = game
        self.slides = slides
        self.on_done = on_done
        self.default_bg = default_bg
        self.played = set()
        self.i = 0
        self.t = 0.0
        self.shown = 0

    def cur(self):
        return self.slides[self.i]

    def update(self, dt):
        self.t += dt
        if self.cur().get("flash") and self.i not in self.played:
            self.played.add(self.i)
            self.g.audio.play_sfx("boom", 0.8)
        full = len(self.cur().get("text", ""))
        self.shown = min(full, int(self.t * 40))

    def tap(self):
        full = len(self.cur().get("text", ""))
        if self.shown < full:
            self.shown = full
            return
        self.i += 1
        self.t = 0.0
        self.shown = 0
        if self.i >= len(self.slides):
            self.on_done()

    def skip(self):
        self.on_done()

    def draw(self, scr):
        g = self.g
        s = self.cur()
        scr.fill(s.get("bg", self.default_bg))
        if s.get("stars"):
            g.draw_stars(scr, g.anim_t * 30, g.anim_t * 10, 1.0)
        if s.get("machine"):
            draw_machine(scr, g.f_tiny, g.anim_t)

        # фигура (Лилу / атом / светящийся огонёк)
        p = min(1.0, self.t / 1.6)
        g.draw_figure(scr, s, p)

        if s.get("flash"):
            alpha = int(255 * max(0.0, 1 - self.t / 1.4))
            if alpha > 0:
                fl = pygame.Surface((W, H))
                fl.fill(WHITE)
                fl.set_alpha(alpha)
                scr.blit(fl, (0, 0))

        # диалоговое окно
        box = pygame.Rect(18, H - 300, W - 36, 270)
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill((8, 8, 22, 215))
        scr.blit(panel, box)
        pygame.draw.rect(scr, GOLD, box, 2, border_radius=16)

        y = box.y + 18
        speaker = s.get("speaker", "")
        if speaker:
            scr.blit(g.f_med.render(speaker, True, GOLD), (box.x + 24, y))
            y += 38
        text = s.get("text", "")[: self.shown]
        for line in wrap_text(g.f_med, text, box.w - 48):
            scr.blit(g.f_med.render(line, True, SOFT), (box.x + 24, y))
            y += 34

        if self.shown >= len(s.get("text", "")):
            if int(g.anim_t * 2) % 2 == 0:
                hint = g.f_small.render("Тап, чтобы продолжить", True, GOLD)
                scr.blit(hint, hint.get_rect(bottomright=(box.right - 20, box.bottom - 12)))

        # кнопка пропуска
        pygame.draw.rect(scr, (30, 30, 50), g.skip_btn, border_radius=12)
        pygame.draw.rect(scr, SOFT, g.skip_btn, 2, border_radius=12)
        st = g.f_tiny.render("ПРОПУСТИТЬ", True, SOFT)
        scr.blit(st, st.get_rect(center=g.skip_btn.center))


# ---------------------------------------------------------------------------
#  ИГРА
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.f_tiny = load_font(16)
        self.f_small = load_font(20)
        self.f_med = load_font(26)
        self.f_big = load_font(44)
        self.f_huge = load_font(74)

        self.dog = load_dog()
        self._dog_cache = {}
        self.stars = [(random.random(), random.random(), random.random()) for _ in range(140)]
        self.uni_blobs = [(random.random(), random.random(), random.uniform(10, 60),
                           random.choice([(255, 120, 200), (120, 200, 255), (255, 220, 120), (180, 120, 255)]))
                          for _ in range(26)]

        self.anim_t = 0.0
        self.running = True
        self.state = "menu"          # menu | cutscene | play | pause | credits
        self.cutscene = None
        self.credits_t = 0.0

        self.chapter_idx = 0
        self.ch = CHAPTERS[0]
        self.ch_start_r = START_R
        self.end_r = START_R * self.ch["grow"]
        self.r = START_R
        self.play_time = 0.0
        self.bump = 0.0
        self.bump_cd = 0.0
        self.px = self.py = self.vx = self.vy = 0.0
        self.objects = []
        self.popups = []
        self.particles = []

        self.joy_active = False
        self.joy_dx = self.joy_dy = 0.0
        self.joy_center = (W - 120, H - 150)
        self.joy_surf = self._make_joy_surface()

        # кнопки
        self.menu_play = pygame.Rect(W // 2 - 140, H - 320, 280, 76)
        self.menu_quit = pygame.Rect(W // 2 - 140, H - 226, 280, 64)
        self.pause_btn = pygame.Rect(W - 66, 14, 52, 52)
        self.pause_resume = pygame.Rect(W // 2 - 140, 400, 280, 70)
        self.pause_menu = pygame.Rect(W // 2 - 140, 490, 280, 70)
        self.skip_btn = pygame.Rect(W - 180, 14, 160, 40)
        self.audio = Audio()
        self.menu_sound = pygame.Rect(W - 150, 14, 136, 40)
        self.pause_sound = pygame.Rect(W // 2 - 140, 580, 280, 70)
        self.audio.play_music("menu")

    # ----------------------------------------------------------- вспомогательное
    def _make_joy_surface(self):
        r = JOY_RADIUS + 8
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, 35), (r, r), JOY_RADIUS)
        pygame.draw.circle(surf, (255, 255, 255, 150), (r, r), JOY_RADIUS, 4)
        pygame.draw.circle(surf, (255, 255, 255, 70), (r, r), 36, 2)
        return surf

    def scaled_dog(self, max_side):
        """Фото Лилу, масштабированное так, чтобы большая сторона = max_side."""
        key = int(max_side)
        key = max(2, key)
        if key not in self._dog_cache:
            if len(self._dog_cache) > 12:
                self._dog_cache.clear()
            w, h = self.dog.get_size()
            f = key / max(w, h)
            size = (max(1, int(w * f)), max(1, int(h * f)))
            self._dog_cache[key] = pygame.transform.smoothscale(self.dog, size)
        return self._dog_cache[key]

    def disp_r(self):
        """Визуальный радиус Лилу на экране (растёт очень медленно)."""
        return min(230.0, 60 + 45 * math.log(1 + self.r / 4.0))

    def to_screen(self, x, y):
        s = self.disp_r() / self.r
        return W / 2 + (x - self.px) * s, H / 2 + (y - self.py) * s

    def world_half_diag(self):
        """Половина диагонали экрана в мировых единицах."""
        return 0.5 * math.hypot(W, H) * self.r / self.disp_r()

    def draw_stars(self, scr, ox, oy, k):
        for ux, uy, b in self.stars:
            x = (ux * W - ox * k * 0.05) % W
            y = (uy * H - oy * k * 0.05) % H
            c = int(110 + b * 145)
            pygame.draw.circle(scr, (c, c, min(255, c + 20)), (int(x), int(y)), 2 if b > 0.8 else 1)

    def draw_figure(self, scr, s, p):
        kind = s.get("fig")
        if not kind:
            return
        fx0, fy0 = s.get("fig_from", (0.5, 0.55))
        fx1, fy1 = s.get("fig_to", (fx0, fy0))
        e = p * p * (3 - 2 * p)
        fx = W * (fx0 + (fx1 - fx0) * e)
        fy = H * (fy0 + (fy1 - fy0) * e)
        sc = s.get("fig_scale", 1.0)
        if kind in ("dog", "giant"):
            img = self.scaled_dog(H * 0.42 * sc)
            bob = math.sin(self.anim_t * 3) * 6
            scr.blit(img, img.get_rect(center=(fx, fy + bob)))
        elif kind == "atom":
            draw_atom(scr, fx, fy, 90 * sc, self.anim_t)
        elif kind == "lab_light":
            for rr, c in ((70, (40, 60, 40)), (36, (90, 120, 60)), (12, (255, 230, 150))):
                pygame.draw.circle(scr, c, (int(fx), int(fy)), rr)
        elif kind == "dot":
            pygame.draw.circle(scr, WHITE, (int(fx), int(fy)), 3)
        elif kind == "universe":
            for bx, by, br, bc in self.uni_blobs:
                pygame.draw.circle(scr, bc, (int(bx * W), int(by * H)), int(br))

    # ----------------------------------------------------------- переходы
    def set_cutscene(self, slides, on_done, bg=(0, 0, 0)):
        if not slides:
            on_done()
            return
        self.cutscene = Cutscene(self, slides, on_done, default_bg=bg)
        self.state = "cutscene"

    def new_game(self):
        self.r = START_R
        self.chapter_idx = 0
        self.set_cutscene(INTRO, lambda: self.start_chapter(0), bg=SPACE_BG)

    def start_chapter(self, idx):
        self.chapter_idx = idx
        self.ch = CHAPTERS[idx]
        self.ch_start_r = self.r
        self.end_r = self.r * self.ch["grow"]
        self.objects, self.popups, self.particles = [], [], []
        self.px = self.py = self.vx = self.vy = 0.0
        self.joy_dx = self.joy_dy = 0.0
        self.joy_active = False
        self.play_time = 0.0
        self.state = "play"
        self.audio.play_music(TRACK_FOR_CHAPTER[idx])
        for _ in range(MAX_OBJECTS):
            self.spawn_object(initial=True)

    def on_chapter_complete(self):
        idx = self.chapter_idx
        outro = list(self.ch["outro"])
        bg = self.ch["bg"]
        if idx + 1 < len(CHAPTERS):
            nxt = idx + 1

            def after():
                self.set_cutscene(CHAPTERS[nxt]["intro"], lambda: self.start_chapter(nxt),
                                  bg=CHAPTERS[nxt]["bg"])
            self.set_cutscene(outro, after, bg=bg)
        else:
            self.set_cutscene(outro + FINAL, self.start_credits, bg=bg)

    def start_credits(self):
        self.state = "credits"
        self.audio.play_music("ending")
        self.credits_t = 0.0

    def go_post_credits(self):
        self.set_cutscene(POST, self.go_menu, bg=LAB_BG)

    def go_menu(self):
        self.state = "menu"
        self.audio.play_music("menu")

    # ----------------------------------------------------------- объекты
    def spawn_object(self, initial=False):
        ch = self.ch
        diag = self.world_half_diag()
        ang = random.uniform(0, TAU)
        if initial:
            dist = diag * random.uniform(0.2, 1.0)
        else:
            dist = diag * random.uniform(1.02, 1.2)
        if random.random() < 0.12:
            r = self.r * random.uniform(1.25, 2.1)
            name, color, kind = random.choice(ch["big"])
        else:
            r = self.r * random.uniform(0.12, 0.55)
            name, color, kind = random.choice(ch["palette"])
        o = Obj(self.px + math.cos(ang) * dist, self.py + math.sin(ang) * dist, r, name, color, kind)
        o.vx = random.uniform(-0.25, 0.25) * self.r
        o.vy = random.uniform(-0.25, 0.25) * self.r
        self.objects.append(o)

    def eat(self, o, sx, sy):
        # Лилу растёт от съеденного, но не слишком быстро (иначе игра кончится за пару минут)
        self.r = math.sqrt(self.r * self.r + GROWTH_PER_EAT * o.r * o.r)
        self.objects.remove(o)
        self.bump = 1.0
        self.audio.play_sfx("eat", 0.45)
        color = o.color if sum(o.color) > 150 else GOLD
        self.popups.append(Popup("+ " + o.name, sx, sy - 20, color))
        for _ in range(10):
            a = random.uniform(0, TAU)
            sp = random.uniform(60, 200)
            self.particles.append({"x": sx, "y": sy, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                                   "t": 0.0, "life": random.uniform(0.4, 0.8), "c": color})

    # ----------------------------------------------------------- обновление
    def keyboard_vector(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    def update_play(self, dt):
        self.play_time += dt
        kx, ky = self.keyboard_vector()
        if kx or ky:
            dx, dy = kx, ky
        else:
            dx, dy = self.joy_dx, self.joy_dy

        speed = PLAYER_SPEED * self.r
        k = min(1.0, dt * 6.0)
        self.vx += (dx * speed - self.vx) * k
        self.vy += (dy * speed - self.vy) * k
        self.px += self.vx * dt
        self.py += self.vy * dt

        self.bump = max(0.0, self.bump - dt * 4)
        self.bump_cd = max(0.0, self.bump_cd - dt)

        # подселяем новые объекты
        spawned = 0
        while len(self.objects) < MAX_OBJECTS and spawned < 4:
            self.spawn_object()
            spawned += 1

        diag = self.world_half_diag()
        for o in self.objects:
            o.x += o.vx * dt
            o.y += o.vy * dt
            o.rot += o.spin * dt * 0.8

        for o in list(self.objects):
            dxo = o.x - self.px
            dyo = o.y - self.py
            d = math.hypot(dxo, dyo)
            if d > diag * 2.4:            # слишком далеко — убираем
                self.objects.remove(o)
                continue

            if o.r * 1.1 <= self.r:       # съедобно
                if d < self.r - o.r * 0.35:
                    sx, sy = self.to_screen(o.x, o.y)
                    self.eat(o, sx, sy)
                    if self.r >= self.end_r:
                        self.on_chapter_complete()
                        return
                elif 1e-6 < d < self.r * 2.2:
                    # «засасывание» — мелочь подтягивается к Лилу
                    pull = self.r * 1.6 * (1 - d / (self.r * 2.2))
                    o.x -= dxo / d * pull * dt
                    o.y -= dyo / d * pull * dt
            else:                         # больше Лилу — отталкивает
                limit = self.r * 0.8 + o.r
                if 1e-6 < d < limit:
                    push = limit - d
                    self.px -= dxo / d * push
                    self.py -= dyo / d * push
                    self.vx *= 0.5
                    self.vy *= 0.5
                    if self.bump_cd <= 0:
                        self.popups.append(Popup("Ой! Слишком большое!", W / 2, H / 2 - 170, RED))
                        self.bump_cd = 1.5
                        self.audio.play_sfx("bump", 0.5)

        for p in self.popups:
            p.t += dt
            p.y -= 35 * dt
        self.popups = [p for p in self.popups if p.t < 1.2]
        for q in self.particles:
            q["t"] += dt
            q["x"] += q["vx"] * dt
            q["y"] += q["vy"] * dt
        self.particles = [q for q in self.particles if q["t"] < q["life"]]

    # ----------------------------------------------------------- отрисовка
    def draw_grid(self, scr, s):
        step = 64
        col = tuple(min(255, c + 18) for c in self.ch["bg"])
        ox = (W / 2 - self.px * s) % step
        oy = (H / 2 - self.py * s) % step
        x = ox
        while x < W:
            pygame.draw.line(scr, col, (int(x), 0), (int(x), H), 1)
            x += step
        y = oy
        while y < H:
            pygame.draw.line(scr, col, (0, int(y)), (W, int(y)), 1)
            y += step

    def draw_object(self, scr, o, sx, sy, sr, danger):
        c = o.color
        center = (int(sx), int(sy))
        if o.kind == "blob":
            pygame.draw.circle(scr, c, center, int(sr))
            hl = tuple(min(255, v + 70) for v in c)
            pygame.draw.circle(scr, hl, (int(sx - sr * 0.3), int(sy - sr * 0.3)), max(1, int(sr * 0.22)))
        elif o.kind == "square":
            pts = []
            for k in range(4):
                a = o.rot + math.pi / 4 + k * math.pi / 2
                pts.append((sx + math.cos(a) * sr, sy + math.sin(a) * sr))
            pygame.draw.polygon(scr, c, pts)
        elif o.kind == "star":
            pts = []
            for k in range(10):
                rr = sr if k % 2 == 0 else sr * 0.45
                a = o.rot + k * math.pi / 5
                pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
            pygame.draw.polygon(scr, c, pts)
        elif o.kind == "face":
            pygame.draw.circle(scr, c, center, int(sr))
            ex = sr * 0.35
            ey = sy - sr * 0.15
            for sgn in (-1, 1):
                pygame.draw.circle(scr, (20, 20, 30), (int(sx + sgn * ex), int(ey)), max(1, int(sr * 0.13)))
            rect = pygame.Rect(int(sx - sr * 0.35), int(sy - sr * 0.05), max(2, int(sr * 0.7)), max(2, int(sr * 0.6)))
            pygame.draw.arc(scr, (20, 20, 30), rect, math.pi * 1.15, math.pi * 1.85, max(1, int(sr * 0.06)))
        elif o.kind == "ring":
            pygame.draw.circle(scr, c, center, int(sr), max(2, int(sr * 0.22)))
        if danger and sr > 6:
            pygame.draw.circle(scr, RED, center, int(sr) + 3, 2)

    def draw_player(self):
        Ds = self.disp_r()
        cx, cy = W / 2, H / 2
        t = min(1.0, max(0.0, (self.r - 5) / 6))   # 0 — атом, 1 — собака
        if t < 1.0:
            R = Ds * (1 + 0.06 * self.bump)
            size = int(R * 2 + 24)
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            draw_atom(surf, size / 2, size / 2, R * 0.9, self.anim_t)
            surf.set_alpha(int(255 * (1 - t)))
            self.screen.blit(surf, (cx - size / 2, cy - size / 2))
        if t > 0.0 and self.dog:
            target = 2 * Ds * 1.04 * (1 + 0.06 * self.bump)
            img = self.scaled_dog(target)
            img.set_alpha(int(255 * t))
            self.screen.blit(img, img.get_rect(center=(cx, cy)))

    def draw_play(self):
        scr = self.screen
        ch = self.ch
        scr.fill(ch["bg"])
        s = self.disp_r() / self.r
        if ch["style"] == "grid":
            self.draw_grid(scr, s)
        else:
            self.draw_stars(scr, self.px, self.py, 1.0)

        for o in sorted(self.objects, key=lambda q: q.r, reverse=True):
            sx = W / 2 + (o.x - self.px) * s
            sy = H / 2 + (o.y - self.py) * s
            sr = max(2.0, o.r * s)
            if sx < -sr - 10 or sx > W + sr + 10 or sy < -sr - 10 or sy > H + sr + 10:
                continue
            danger = o.r * 1.1 > self.r
            self.draw_object(scr, o, sx, sy, sr, danger)

        self.draw_player()

        for q in self.particles:
            k = q["t"] / q["life"]
            rad = max(1, int(6 * (1 - k)))
            pygame.draw.circle(scr, q["c"], (int(q["x"]), int(q["y"])), rad)
        for p in self.popups:
            surf = self.f_small.render(p.text, True, p.color)
            surf.set_alpha(int(255 * max(0.0, 1 - p.t / 1.2)))
            scr.blit(surf, surf.get_rect(center=(p.x, p.y)))

        self.draw_hud()

    def draw_hud(self):
        scr = self.screen
        panel = pygame.Surface((270, 104), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        scr.blit(panel, (8, 6))
        scr.blit(self.f_med.render(self.ch["title"], True, GOLD), (18, 12))
        v = self.r / self.ch_start_r
        scr.blit(self.f_small.render(f"Размер: {v:.1f} {self.ch['unit']}", True, SOFT), (18, 46))
        frac = min(1.0, math.log(max(v, 1.0)) / math.log(self.ch["grow"]))
        bar = pygame.Rect(18, 76, 220, 12)
        pygame.draw.rect(scr, (40, 40, 60), bar, border_radius=6)
        fill = bar.copy()
        fill.w = max(6, int(bar.w * frac))
        pygame.draw.rect(scr, GOLD, fill, border_radius=6)

        if self.play_time < 14:
            for i, line in enumerate(("Ешь всё, что меньше Лилу.",
                                      "Красная обводка — слишком большое!")):
                scr.blit(self.f_tiny.render(line, True, SOFT), (18, 96 + i * 20))

        # кнопка паузы
        pygame.draw.rect(scr, (30, 30, 50), self.pause_btn, border_radius=12)
        pygame.draw.rect(scr, SOFT, self.pause_btn, 2, border_radius=12)
        pygame.draw.rect(scr, SOFT, (self.pause_btn.centerx - 9, self.pause_btn.y + 14, 6, 24))
        pygame.draw.rect(scr, SOFT, (self.pause_btn.centerx + 3, self.pause_btn.y + 14, 6, 24))

        # джойстик: кружок в кружке
        cx, cy = self.joy_center
        scr.blit(self.joy_surf, self.joy_surf.get_rect(center=(cx, cy)))
        kx = cx + self.joy_dx * JOY_RADIUS
        ky = cy + self.joy_dy * JOY_RADIUS
        pygame.draw.circle(scr, (235, 235, 250), (int(kx), int(ky)), 34)
        pygame.draw.circle(scr, (140, 140, 170), (int(kx), int(ky)), 34, 3)

    def draw_menu(self):
        scr = self.screen
        scr.fill((14, 16, 30))
        self.draw_stars(scr, self.anim_t * 40, 0, 1.0)
        title = self.f_huge.render("ЛИЛУ", True, GOLD)
        scr.blit(title, title.get_rect(center=(W / 2, 120)))
        sub = self.f_med.render("Пожиратель Вселенных", True, PINK)
        scr.blit(sub, sub.get_rect(center=(W / 2, 185)))
        if self.dog:
            img = self.scaled_dog(340)
            bob = math.sin(self.anim_t * 2) * 8
            scr.blit(img, img.get_rect(center=(W / 2, 480 + bob)))
        draw_button(scr, self.menu_play, "ИГРАТЬ", self.f_big, primary=True)
        draw_button(scr, self.menu_quit, "ВЫХОД", self.f_med, primary=False)
        draw_button(scr, self.menu_sound, self.audio.label(), self.f_tiny, primary=False)
        l1 = self.f_tiny.render("ПК: WASD или стрелки  ·  Телефон: джойстик справа внизу", True, SOFT)
        scr.blit(l1, l1.get_rect(center=(W / 2, H - 40)))

    def draw_pause(self):
        self.draw_play()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        self.screen.blit(ov, (0, 0))
        t = self.f_huge.render("ПАУЗА", True, GOLD)
        self.screen.blit(t, t.get_rect(center=(W / 2, 300)))
        draw_button(self.screen, self.pause_resume, "ПРОДОЛЖИТЬ", self.f_med, primary=True)
        draw_button(self.screen, self.pause_menu, "В МЕНЮ", self.f_med, primary=False)
        draw_button(self.screen, self.pause_sound, self.audio.label(), self.f_med, primary=False)

    def draw_credits(self):
        scr = self.screen
        scr.fill((0, 0, 0))
        for i, line in enumerate(CREDITS):
            y = H + i * 56 - self.credits_t * 55
            if y < -60 or y > H + 60 or not line:
                continue
            font = self.f_big if i == 0 else self.f_med
            color = GOLD if i in (0, len(CREDITS) - 1) else SOFT
            if i == 1:
                color = PINK
            txt = font.render(line, True, color)
            scr.blit(txt, txt.get_rect(center=(W / 2, y)))
        hint = self.f_tiny.render("Тап — пропустить", True, (120, 120, 140))
        scr.blit(hint, hint.get_rect(center=(W / 2, H - 30)))

    # ----------------------------------------------------------- главный цикл
    def update(self, dt):
        self.anim_t += dt
        if self.state == "cutscene" and self.cutscene:
            self.cutscene.update(dt)
        elif self.state == "play":
            self.update_play(dt)
        elif self.state == "credits":
            self.credits_t += dt
            if self.credits_t > (H + len(CREDITS) * 56) / 55 + 1:
                self.go_post_credits()

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "cutscene" and self.cutscene:
            self.cutscene.draw(self.screen)
        elif self.state == "play":
            self.draw_play()
        elif self.state == "pause":
            self.draw_pause()
        elif self.state == "credits":
            self.draw_credits()

    def joy_set(self, pos):
        cx, cy = self.joy_center
        vx, vy = pos[0] - cx, pos[1] - cy
        d = math.hypot(vx, vy)
        if d > JOY_RADIUS:
            vx, vy = vx / d * JOY_RADIUS, vy / d * JOY_RADIUS
        mag = math.hypot(vx, vy) / JOY_RADIUS
        if mag < 0.12:
            self.joy_dx = self.joy_dy = 0.0
        else:
            self.joy_dx, self.joy_dy = vx / JOY_RADIUS, vy / JOY_RADIUS

    def on_press(self, pos):
        if self.state == "menu":
            if self.menu_play.collidepoint(pos):
                self.audio.play_sfx("click")
                self.new_game()
            elif self.menu_quit.collidepoint(pos):
                self.running = False
            elif self.menu_sound.collidepoint(pos):
                self.audio.toggle()
        elif self.state == "cutscene":
            if self.skip_btn.collidepoint(pos):
                self.cutscene.skip()
            else:
                self.cutscene.tap()
        elif self.state == "play":
            if self.pause_btn.collidepoint(pos):
                self.state = "pause"
                self.joy_dx = self.joy_dy = 0.0
                return
            cx, cy = self.joy_center
            if math.hypot(pos[0] - cx, pos[1] - cy) < 160:
                self.joy_active = True
                self.joy_set(pos)
        elif self.state == "pause":
            if self.pause_resume.collidepoint(pos):
                self.state = "play"
            elif self.pause_menu.collidepoint(pos):
                self.go_menu()
            elif self.pause_sound.collidepoint(pos):
                self.audio.toggle()
        elif self.state == "credits":
            self.go_post_credits()

    def on_release(self):
        self.joy_active = False
        self.joy_dx = self.joy_dy = 0.0

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.state == "play":
                    self.state = "pause"
                elif self.state == "pause":
                    self.state = "play"
                elif self.state == "menu":
                    self.running = False
                elif self.state == "cutscene":
                    self.cutscene.skip()
            elif e.key == pygame.K_m:
                self.audio.toggle()
            elif e.key == pygame.K_p and self.state == "play":
                self.state = "pause"
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN) and self.state == "cutscene":
                self.cutscene.tap()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.on_press(e.pos)
        elif e.type == pygame.MOUSEMOTION and self.joy_active:
            self.joy_set(e.pos)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.on_release()


def main():
    pygame.init()
    pygame.display.set_caption("Лилу: Пожиратель Вселенных")
    screen = pygame.display.set_mode((W, H), pygame.SCALED)
    game = Game(screen)
    clock = pygame.time.Clock()
    while game.running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            game.handle_event(event)
        game.update(dt)
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
