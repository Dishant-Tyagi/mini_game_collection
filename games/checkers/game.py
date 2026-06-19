# =====================================
# CHECKERS GAME — Clean Multiplayer Safe Version
# =====================================
from kivy.clock import Clock
from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Ellipse


class CheckersGame(BaseGame):

    def __init__(self, db):
        super().__init__(db, "Checkers")

        self.board = self.create_board()
        self.current_player = 1
        self.player_role = 1
        self.selected = None
        self.valid_moves = []

        self.app = None

        self.multiplayer_enabled = False
        self.is_my_turn = True
        self.is_remote_move = False

        self.board_widget = None
        self.turn_label = None

    # ---------------------------------
    # BOARD INIT
    # ---------------------------------
    def create_board(self):
        board = [[0 for _ in range(8)] for _ in range(8)]

        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 1:
                    board[r][c] = 2

        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 1:
                    board[r][c] = 1

        return board

    # ---------------------------------
    # START
    # ---------------------------------
    def start(self, app):
        self.app = app
        self.begin_session()
        self.build_ui()
       
        Clock.schedule_once(lambda dt: self.draw_board())

    # ---------------------------------
    # UI
    # ---------------------------------
    def build_ui(self):
        screen = self.app.game_screen
        screen.clear_widgets()

        root = BoxLayout(orientation="vertical", spacing=6, padding=6)

        self.turn_label = Label(
            text="Red Turn",
            font_size=22,
            size_hint_y=None,
            height=40
        )
        root.add_widget(self.turn_label)

        self.board_widget = Widget()
        root.add_widget(self.board_widget)

        btns = BoxLayout(size_hint_y=None, height=50)
        btns.add_widget(Button(text="Restart", on_release=lambda *_: self.reset()))
        btns.add_widget(Button(text="Menu", on_release=lambda *_: self.app.switch_to("menu")))
        root.add_widget(btns)

        screen.add_widget(root)
        self.app.switch_to("game")

        self.board_widget.bind(on_touch_down=lambda w, t: self.on_touch(w, t))
        self.board_widget.bind(size=lambda *a: self.draw_board())

    # ---------------------------------
    # TOUCH
    # ---------------------------------
    def on_touch(self, widget, touch):

        if self.multiplayer_enabled and not self.is_my_turn:
            return

        if not widget.collide_point(*touch.pos):
            return

        w = widget.width
        h = widget.height
        board_size = min(w, h)
        cell = board_size / 8

        offset_x = widget.x + (w - board_size) / 2
        offset_y = widget.y + (h - board_size) / 2

        col = int((touch.x - offset_x) / cell)
        row = int((touch.y - offset_y) / cell)

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board[row][col]

        if self.multiplayer_enabled:
            if piece != 0 and piece not in (self.player_role, self.player_role+2):
                return

        if self.selected:
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected, (row, col))
                self.selected = None
                self.valid_moves = []
                return

        if self.belongs_to_current(piece):
            self.selected = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)
            self.draw_board()

    # ---------------------------------
    # GAME LOGIC
    # ---------------------------------
    def belongs_to_current(self, piece):
        if self.current_player == 1:
            return piece in (1,3)
        else:
            return piece in (2,4)

    def get_valid_moves(self, r, c):
        moves = []

        piece = self.board[r][c]

        directions = []

        if piece in (1,3):
            directions.append(-1)
        if piece in (2,4):
            directions.append(1)
        if piece in (3,4):
            directions = [-1,1]

        for d in directions:
            for dc in [-1,1]:

                nr = r + d
                nc = c + dc

                if 0 <= nr < 8 and 0 <= nc < 8:

                    if self.board[nr][nc] == 0:
                        moves.append((nr,nc))

                    elif not self.belongs_to_current(self.board[nr][nc]):
                        jr = nr + d
                        jc = nc + dc
                        if 0 <= jr < 8 and 0 <= jc < 8:
                            if self.board[jr][jc] == 0:
                                moves.append((jr,jc))

        return moves

    # ---------------------------------
    # MOVE
    # ---------------------------------
    def move_piece(self, start, end):

        sr, sc = start
        er, ec = end

        piece = self.board[sr][sc]

        if abs(er - sr) == 2:
            mid_r = (sr + er) // 2
            mid_c = (sc + ec) // 2
            self.board[mid_r][mid_c] = 0

        self.board[er][ec] = piece
        self.board[sr][sc] = 0

        # KING PROMOTION
        if piece == 1 and er == 0:
            self.board[er][ec] = 3
        if piece == 2 and er == 7:
            self.board[er][ec] = 4

        if self.multiplayer_enabled and not self.is_remote_move:
            move_data = {"from":start,"to":end}
            self.app.multiplayer_manager.send_move(move_data)
            self.is_my_turn = False

        self.switch_turn()
        self.draw_board()
        self.check_game_over()

    # ---------------------------------
    # REMOTE MOVE
    # ---------------------------------
    def apply_remote_move(self, data):

        self.is_remote_move = True

        start = tuple(data["from"])
        end = tuple(data["to"])

        self.move_piece(start,end)

        self.is_remote_move = False
        self.is_my_turn = True

    # ---------------------------------
    # TURN
    # ---------------------------------
    def switch_turn(self):
        self.current_player = 2 if self.current_player == 1 else 1
        self.turn_label.text = "Red Turn" if self.current_player == 1 else "White Turn"

    # ---------------------------------
    # DRAW
    # ---------------------------------
    def draw_board(self):
        self.board_widget.canvas.clear()

        with self.board_widget.canvas:

            w = self.board_widget.width
            h = self.board_widget.height
            board_size = min(w,h)
            cell = board_size/8

            offset_x = self.board_widget.x + (w-board_size)/2
            offset_y = self.board_widget.y + (h-board_size)/2

            for r in range(8):
                for c in range(8):

                    if (r+c)%2==0:
                        Color(0.9,0.9,0.9,1)
                    else:
                        Color(0.3,0.3,0.3,1)

                    Rectangle(
                        pos=(offset_x+c*cell,offset_y+r*cell),
                        size=(cell,cell)
                    )

                    if self.selected==(r,c):
                        Color(1,1,0,0.6)
                        Rectangle(
                            pos=(offset_x+c*cell,offset_y+r*cell),
                            size=(cell,cell)
                        )

                    if (r,c) in self.valid_moves:
                        Color(0,1,0,0.5)
                        Rectangle(
                            pos=(offset_x+c*cell,offset_y+r*cell),
                            size=(cell,cell)
                        )

                    piece=self.board[r][c]

                    if piece!=0:

                        if piece in (1,3):
                            Color(1,0.2,0.2,1)
                        else:
                            Color(0.95,0.95,0.95,1)

                        Ellipse(
                            pos=(offset_x+c*cell+cell*0.15,
                                 offset_y+r*cell+cell*0.15),
                            size=(cell*0.7,cell*0.7)
                        )

                        Color(0,0,0,0.4)
                        Ellipse(
                            pos=(offset_x+c*cell+cell*0.18,
                                 offset_y+r*cell+cell*0.18),
                            size=(cell*0.64,cell*0.64)
                        )

                        # KING VISUAL
                        if piece in (3,4):
                            Color(1,0.85,0,1)
                            Ellipse(
                                pos=(offset_x+c*cell+cell*0.35,
                                     offset_y+r*cell+cell*0.35),
                                size=(cell*0.3,cell*0.3)
                            )

    # ---------------------------------
    # RESET
    # ---------------------------------
    def reset(self):
        self.board=self.create_board()
        self.current_player=1
        self.selected=None
        self.valid_moves=[]
        self.is_my_turn=True
        self.draw_board()

    # ---------------------------------
    # GAME OVER
    # ---------------------------------
    def check_game_over(self):
        red=any(1 in row or 3 in row for row in self.board)
        white=any(2 in row or 4 in row for row in self.board)

        if not red or not white:
            winner="Red" if red else "White"
            self.end_session()
            self.show_game_over(winner)

    def show_game_over(self,winner):
        popup=Popup(
            title="Game Over",
            content=Label(text=f"{winner} Wins!"),
            size_hint=(0.5,0.4)
        )
        popup.open()