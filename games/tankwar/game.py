from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Rectangle, PushMatrix, PopMatrix, Rotate, Color
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.uix.popup import Popup
import os
import random
import math


class TankWarGame(BaseGame):

    UPDATE_RATE = 1/60
    MAX_AMMO = 3
    RELOAD_TIME = 100

    def __init__(self, db):
        super().__init__(db, "TankWar")

        self.assets_path = os.path.join(os.path.dirname(__file__), "assets")
        self.load_assets()

        self.widget = None
        self.clock_event = None
        self.running = False

        self.level = 1
        self.max_health = 3

    # -------------------------------------------------
    # ASSETS
    # -------------------------------------------------

    def load_assets(self):

        img = os.path.join(self.assets_path, "images")

        self.background_texture = CoreImage(
            os.path.join(img, "others", "background.png")
        ).texture

        player_sheet = CoreImage(
            os.path.join(img, "playerTank",
                         sorted(os.listdir(os.path.join(img, "playerTank")))[0])
        ).texture

        self.player_texture = player_sheet.get_region(0,0,48,48)

        self.enemy_sheets = []
        enemy_folder = os.path.join(img,"enemyTank")

        for file in os.listdir(enemy_folder):
            tex = CoreImage(os.path.join(enemy_folder,file)).texture
            self.enemy_sheets.append(tex)

        self.bullet_texture = CoreImage(
            os.path.join(img,"bullet",
                         sorted(os.listdir(os.path.join(img,"bullet")))[0])
        ).texture

        scene = os.path.join(img,"scene")

        self.wall_textures = {
            "brick": CoreImage(os.path.join(scene,"brick.png")).texture,
            "iron": CoreImage(os.path.join(scene,"iron.png")).texture,
        }

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    def start(self, app):
        self.app = app
        self.begin_session()
        self.build_game_ui()
        Clock.schedule_once(lambda dt:self.reset(),0.2)

    # -------------------------------------------------
    # RESET
    # -------------------------------------------------

    def reset(self):

        self.enemies=[]
        self.bullets=[]
        self.walls=[]
        self.score=0

        self.generate_walls()

        self.player={
            "x":self.widget.width/2,
            "y":self.widget.height/2,
            "angle":0,
            "vx":0,
            "vy":0,
            "speed":170,
            "health":self.max_health,
            "ammo":self.MAX_AMMO,
            "reload":0
        }

        self.spawn_wave()

        self.running=True

        if self.clock_event:
            self.clock_event.cancel()

        self.clock_event=Clock.schedule_interval(self.update,self.UPDATE_RATE)

    # -------------------------------------------------
    # ENEMY SPAWN
    # -------------------------------------------------

    def spawn_wave(self):
        count=3+self.level
        for _ in range(count):
            self.spawn_enemy()

    def spawn_enemy(self):

        for _ in range(100):

            x=random.randint(80,int(self.widget.width-80))
            y=random.randint(80,int(self.widget.height-80))

            if not self.wall_collision(x,y):

                sheet=random.choice(self.enemy_sheets)
                texture=sheet.get_region(0,0,48,48)

                self.enemies.append({
                    "x":x,
                    "y":y,
                    "angle":0,
                    "speed":80,
                    "cooldown":60,
                    "ammo":self.MAX_AMMO,
                    "reload":0,
                    "health":1,
                    "texture":texture
                })
                return

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def build_game_ui(self):

        screen=self.app.game_screen
        screen.clear_widgets()

        layout=BoxLayout(orientation="vertical")

        self.top_label=Label(
            text="Score: 0 | Level: 1 | Ammo: 3",
            size_hint_y=None,
            height=40
        )

        layout.add_widget(self.top_label)

        center=BoxLayout(padding=10)

        self.widget=Widget()
        self.widget.bind(on_touch_down=self.on_mouse_click)

        center.add_widget(self.widget)
        layout.add_widget(center)

        btn=Button(
            text="Back to Menu",
            size_hint_y=None,
            height=50,
            on_release=lambda *_:self.exit_game()
        )

        layout.add_widget(btn)

        screen.add_widget(layout)
        self.app.switch_to("game")

        Window.bind(on_key_down=self.key_down)
        Window.bind(on_key_up=self.key_up)

    # -------------------------------------------------
    # INPUT
    # -------------------------------------------------

    def key_down(self,inst,key,*_):
        if key==119:self.player["vy"]=1
        elif key==115:self.player["vy"]=-1
        elif key==97:self.player["vx"]=-1
        elif key==100:self.player["vx"]=1

    def key_up(self,inst,key,*_):
        if key in (119,115):self.player["vy"]=0
        if key in (97,100):self.player["vx"]=0

    def on_mouse_click(self,inst,touch):

        local_x=touch.x-self.widget.x
        local_y=touch.y-self.widget.y

        dx=local_x-self.player["x"]
        dy=local_y-self.player["y"]

        angle=math.degrees(math.atan2(dy,dx))
        self.player["angle"]=angle

        if self.player["ammo"]>0:
            self.spawn_bullet(self.player["x"],self.player["y"],angle,"player")
            self.player["ammo"]-=1
        elif self.player["reload"]==0:
            self.player["reload"]=self.RELOAD_TIME

    # -------------------------------------------------
    # WALLS
    # -------------------------------------------------

    def generate_walls(self):

        self.walls.clear()

        cell=60
        cols=int(self.widget.width//cell)
        rows=int(self.widget.height//cell)

        start_x=cell/2
        start_y=cell/2

        for c in range(cols):
            for r in range(rows):

                if random.random()<0.25:

                    wall_type="brick" if random.random()<0.7 else "iron"

                    self._add_wall(
                        start_x+c*cell,
                        start_y+r*cell,
                        wall_type
                    )

    def _add_wall(self,x,y,wall_type="brick"):

        wall={
            "x":x,
            "y":y,
            "size":40,
            "type":wall_type
        }

        if wall_type=="brick":
            wall["health"]=2

        self.walls.append(wall)

    def wall_collision(self,x,y):

        tank_half=20

        for wall in self.walls:

            half=wall["size"]/2

            if (
                x+tank_half>wall["x"]-half and
                x-tank_half<wall["x"]+half and
                y+tank_half>wall["y"]-half and
                y-tank_half<wall["y"]+half
            ):
                return True

        return False

    # -------------------------------------------------
    # BULLETS
    # -------------------------------------------------

    def spawn_bullet(self,x,y,angle,owner):

        self.bullets.append({
            "x":x,
            "y":y,
            "angle":angle,
            "owner":owner,
            "speed":350
        })

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    def update(self,dt):

        if not self.running:
            return

        vx=self.player["vx"]
        vy=self.player["vy"]

        length=math.hypot(vx,vy)

        if length>0:
            vx/=length
            vy/=length

        new_x=self.player["x"]+vx*self.player["speed"]*dt
        new_y=self.player["y"]+vy*self.player["speed"]*dt

        if not self.wall_collision(new_x,new_y):
            self.player["x"]=new_x
            self.player["y"]=new_y

        # reload
        if self.player["reload"]>0:
            self.player["reload"]-=1
            if self.player["reload"]<=0:
                self.player["ammo"]=self.MAX_AMMO

        # enemy update
        for enemy in self.enemies:
            self.update_enemy(enemy,dt)

        # bullet update
        for b in self.bullets[:]:

            rad=math.radians(b["angle"])

            b["x"]+=math.cos(rad)*b["speed"]*dt
            b["y"]+=math.sin(rad)*b["speed"]*dt

            # screen bounds
            if (
                b["x"]<0 or
                b["x"]>self.widget.width or
                b["y"]<0 or
                b["y"]>self.widget.height
            ):
                self.bullets.remove(b)
                continue

            # wall collision
            for wall in self.walls[:]:

                half=wall["size"]/2

                if (
                    abs(b["x"]-wall["x"])<half and
                    abs(b["y"]-wall["y"])<half
                ):

                    if wall["type"]=="brick":
                        wall["health"]-=1
                        if wall["health"]<=0:
                            self.walls.remove(wall)

                    self.bullets.remove(b)
                    break

        self.check_collisions()
        self.draw()

    # -------------------------------------------------
    # ENEMY AI
    # -------------------------------------------------

    def update_enemy(self,enemy,dt):

        dx=self.player["x"]-enemy["x"]
        dy=self.player["y"]-enemy["y"]

        enemy["angle"]=math.degrees(math.atan2(dy,dx))

        rad=math.radians(enemy["angle"])

        new_x=enemy["x"]+math.cos(rad)*enemy["speed"]*dt
        new_y=enemy["y"]+math.sin(rad)*enemy["speed"]*dt

        if not self.wall_collision(new_x,new_y):
            enemy["x"]=new_x
            enemy["y"]=new_y

        # reload logic
        if enemy["reload"]>0:
            enemy["reload"]-=1
            if enemy["reload"]<=0:
                enemy["ammo"]=self.MAX_AMMO

        enemy["cooldown"]-=1

        if enemy["cooldown"]<=0:

            if enemy["ammo"]>0:

                self.spawn_bullet(
                    enemy["x"],
                    enemy["y"],
                    enemy["angle"],
                    "enemy"
                )

                enemy["ammo"]-=1
                enemy["cooldown"]=60

            elif enemy["reload"]==0:
                enemy["reload"]=self.RELOAD_TIME

    # -------------------------------------------------
    # COLLISIONS
    # -------------------------------------------------

    def check_collisions(self):

        for b in self.bullets[:]:

            if b["owner"]=="player":

                for enemy in self.enemies[:]:

                    if abs(enemy["x"]-b["x"])<20 and abs(enemy["y"]-b["y"])<20:

                        enemy["health"]-=1
                        self.bullets.remove(b)

                        if enemy["health"]<=0:
                            self.enemies.remove(enemy)
                            self.score+=20

                        break

            else:

                if abs(self.player["x"]-b["x"])<20 and abs(self.player["y"]-b["y"])<20:

                    self.player["health"]-=1
                    self.bullets.remove(b)

                    if self.player["health"]<=0:
                        self.game_over()

        if not self.enemies:
            self.level+=1
            self.spawn_wave()

        self.top_label.text=f"Score: {self.score} | Level: {self.level} | Ammo: {self.player['ammo']}"

    # -------------------------------------------------
    # GAME OVER POPUP
    # -------------------------------------------------

    def game_over(self):

        self.running=False

        if self.clock_event:
            self.clock_event.cancel()

        layout=BoxLayout(orientation="vertical",padding=20,spacing=20)

        layout.add_widget(Label(
            text=f"Game Over\nScore: {self.score}",
            font_size=22
        ))

        btns=BoxLayout(size_hint_y=None,height=60,spacing=10)

        restart=Button(text="Restart")
        restart.bind(on_release=lambda *_:self.restart_game())

        menu=Button(text="Menu")
        menu.bind(on_release=lambda *_:self.exit_game())

        btns.add_widget(restart)
        btns.add_widget(menu)

        layout.add_widget(btns)

        self.popup=Popup(
            title="Tank War",
            content=layout,
            size_hint=(0.4,0.4),
            auto_dismiss=False
        )

        self.popup.open()

    def restart_game(self):

        if hasattr(self,"popup"):
            self.popup.dismiss()

        self.level=1
        self.reset()

    # -------------------------------------------------

    def draw(self):

        self.widget.canvas.clear()

        with self.widget.canvas:

            Color(1,1,1,1)

            Rectangle(
                texture=self.background_texture,
                pos=(0,0),
                size=(self.widget.width,self.widget.height)
            )

            for wall in self.walls:

                if wall.get("health")==2:
                    Color(1,1,1,1)
                elif wall.get("health")==1:
                    Color(1,0.7,0.7,1)
                else:
                    Color(1,1,1,1)

                Rectangle(
                    texture=self.wall_textures.get(wall["type"]),
                    pos=(wall["x"]-20,wall["y"]-20),
                    size=(40,40)
                )

            PushMatrix()
            Rotate(angle=self.player["angle"],origin=(self.player["x"],self.player["y"]))

            Rectangle(
                texture=self.player_texture,
                pos=(self.player["x"]-24,self.player["y"]-24),
                size=(48,48)
            )

            PopMatrix()

            for enemy in self.enemies:

                PushMatrix()
                Rotate(angle=enemy["angle"],origin=(enemy["x"],enemy["y"]))

                Rectangle(
                    texture=enemy["texture"],
                    pos=(enemy["x"]-24,enemy["y"]-24),
                    size=(48,48)
                )

                PopMatrix()

            for b in self.bullets:

                Rectangle(
                    texture=self.bullet_texture,
                    pos=(b["x"]-8,b["y"]-8),
                    size=(16,16)
                )

    # -------------------------------------------------

    def exit_game(self):

        self.running=False

        if self.clock_event:
            self.clock_event.cancel()

        Window.unbind(on_key_down=self.key_down)
        Window.unbind(on_key_up=self.key_up)

        self.end_session()
        self.app.switch_to("menu")