from core.base_game import BaseGame
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
import random
import os
from kivy.graphics import Color, Line, Ellipse

class HangmanGame(BaseGame):

    MAX_FAILURE = 7

    def __init__(self, db):
        super().__init__(db, "Hangman")

        self.secret_word = ""
        self.correct_letters = []
        self.failure = 0

        self.app = None

        self.word_label = None
        self.hang_label = None
        self.input_box = None
        self.wrong_letters = []
        self.wrong_label = None
    # -------------------------------------------------
    # START
    # -------------------------------------------------

    def start(self, app):
        self.app = app
        self.begin_session()
        self.build_game_ui()
        self.reset()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def build_game_ui(self):

        screen = self.app.game_screen
        screen.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=20
        )

        title = Label(
            text="Hangman",
            font_size=32,
            size_hint_y=None,
            height=60
        )

        root.add_widget(title)
        self.wrong_label = Label(
        text="Wrong: ",
        font_size=18,
        size_hint_y=None,
        height=40
        )

        root.add_widget(self.wrong_label)

        self.word_label = Label(
            text="",
            font_size=28,
            size_hint_y=None,
            height=60
        )

        root.add_widget(self.word_label)

        self.hang_label = Label(
            text="",
            font_size=20
        )

        root.add_widget(self.hang_label)

        input_row = BoxLayout(
            size_hint_y=None,
            height=60,
            spacing=10
        )

        self.input_box = TextInput(
            multiline=False,
            size_hint_x=0.6
        )

        guess_btn = Button(text="Guess")
        guess_btn.bind(on_release=lambda *_: self.make_guess())

        input_row.add_widget(self.input_box)
        input_row.add_widget(guess_btn)

        root.add_widget(input_row)

        bottom = BoxLayout(
            size_hint_y=None,
            height=60,
            spacing=10
        )

        restart = Button(text="Restart")
        restart.bind(on_release=lambda *_: self.reset())

        menu = Button(text="Menu")
        menu.bind(on_release=lambda *_: self.exit_game())

        bottom.add_widget(restart)
        bottom.add_widget(menu)

        root.add_widget(bottom)

        screen.add_widget(root)
        self.app.switch_to("game")

    # -------------------------------------------------
    # RESET
    # -------------------------------------------------

    def reset(self):

        self.secret_word = self.upload_secret_word()

        self.correct_letters = self.initializes_correct_letters(self.secret_word)

        self.failure = 0
        self.wrong_letters = []

        self.update_display()
        

    # -------------------------------------------------
    # GUESS
    # -------------------------------------------------

    def make_guess(self):

        guess = self.input_box.text.strip().upper()
        self.input_box.text = ""

        if not guess:
            return
        
        if guess in self.correct_letters or guess in self.wrong_letters:
            return
        
        if guess in self.secret_word:

            self.correct_guess_mark(
                guess,
                self.correct_letters,
                self.secret_word
            )

        else:

            self.failure += 1
            self.wrong_letters.append(guess)

        self.update_display()

        if self.failure >= self.MAX_FAILURE:
            self.show_loser()

        if "_" not in self.correct_letters:
            self.show_winner()

    # -------------------------------------------------
    # DISPLAY
    # -------------------------------------------------

    def update_display(self):

        self.word_label.text = " ".join(self.correct_letters)

        self.draw_gallows()

        self.wrong_label.text = "Wrong: " + " ".join(self.wrong_letters)

    # -------------------------------------------------
    # HANG DRAWING
    # -------------------------------------------------

    def draw_gallows(self):

        

        canvas = self.hang_label.canvas
        canvas.clear()

        w = self.hang_label.width
        h = self.hang_label.height

        if w == 0 or h == 0:
            return

        base_y = h * 0.40      # base (your chosen position)

        pole_x = w * 0.35
        top_y = h * 0.92
        beam_end = w * 0.60
        rope_y = h * 0.82   # rope start

        with canvas:

            Color(1, 1, 1)

            # base
            Line(points=[w*0.2, base_y, w*0.8, base_y], width=2)

            # pole
            Line(points=[pole_x, base_y, pole_x, top_y], width=2)

            # top beam
            Line(points=[pole_x, top_y, beam_end, top_y], width=2)

            # rope
            Line(points=[beam_end, top_y, beam_end, rope_y], width=2)

            if self.failure > 0:
                Ellipse(pos=(beam_end-10, rope_y-25), size=(20,20))

            if self.failure > 1:
                Line(points=[beam_end, rope_y-25, beam_end, rope_y-70], width=2)

            if self.failure > 2:
                Line(points=[beam_end, rope_y-40, beam_end-20, rope_y-55], width=2)

            if self.failure > 3:
                Line(points=[beam_end, rope_y-40, beam_end+20, rope_y-55], width=2)

            if self.failure > 4:
                Line(points=[beam_end, rope_y-70, beam_end-20, rope_y-100], width=2)

            if self.failure > 5:
                Line(points=[beam_end, rope_y-70, beam_end+20, rope_y-100], width=2)

    # -------------------------------------------------
    # ORIGINAL LOGIC FUNCTIONS (UNCHANGED)
    # -------------------------------------------------

    def correct_guess_mark(self, guess, correct_letters, secret_word):

        index = 0

        for word in secret_word:

            if guess == word:
                correct_letters[index] = word

            index += 1

    def initializes_correct_letters(self, word):

        return ["_" for letter in word]

    def upload_secret_word(self):

        path = os.path.join(
            os.path.dirname(__file__),
            "list.txt"
        )

        words = []

        with open(path, "r") as archive:

            for line in archive:
                line = line.strip()
                words.append(line)

        number = random.randrange(0, len(words))

        return words[number].upper()

    # -------------------------------------------------
    # GAME OVER POPUPS
    # -------------------------------------------------

    def show_winner(self):

        layout = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=20
        )

        layout.add_widget(Label(
            text="Congratulations!\nYou Win!",
            font_size=22
        ))

        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)

        restart_btn = Button(text="Restart")
        restart_btn.bind(on_release=lambda *_: self.restart())

        menu_btn = Button(text="Menu")
        menu_btn.bind(on_release=lambda *_: self.popup_menu())

        btn_row.add_widget(restart_btn)
        btn_row.add_widget(menu_btn)

        layout.add_widget(btn_row)

        self.popup = Popup(
            title="Hangman",
            content=layout,
            size_hint=(0.4,0.4),
            auto_dismiss=False
        )

        self.popup.open()

    def show_loser(self):

        layout = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=20
        )

        layout.add_widget(Label(
            text=f"Game Over!\nWord was: {self.secret_word}",
            font_size=22
        ))

        btn = Button(text="Restart")

        btn.bind(on_release=lambda *_: self.restart())

        layout.add_widget(btn)

        self.popup = Popup(
            title="Hangman",
            content=layout,
            size_hint=(0.4,0.4),
            auto_dismiss=False
        )

        self.popup.open()

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------

    def restart(self):

        if hasattr(self, "popup"):
            self.popup.dismiss()

        self.reset()

    # -------------------------------------------------
    # EXIT
    # -------------------------------------------------

    def exit_game(self):

        self.end_session()
        self.app.switch_to("menu")
        