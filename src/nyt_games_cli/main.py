
import setproctitle
from pycurses.mainwindow import MainWindow
from pycurses.layout import Layout

from nyt_games_cli.letterboxed import LetterBoxed
from nyt_games_cli.wordle import Wordle
from nyt_games_cli.nyt_data import load_game_data
from nyt_games_cli.strands import Strands
from nyt_games_cli.mini_crossword import Mini
from nyt_games_cli.connections import Connections
from nyt_games_cli.spelling_bee import SpellingBee

class NYTGames(MainWindow):

    def __init__(self):
        super().__init__([])
        setproctitle.setproctitle('Python - NYT Cli Games')
        self.base_layout = Layout(colors=self.colors, defaultchar='.', defaultattr=0)
        self.add_child(self.base_layout)

        self.mini = Mini(colors=self.colors, defaultchar=' ', defaultattr=0)
        #self.base_layout.add_child(self.mini)

        self.letter_boxed = LetterBoxed(colors=self.colors, defaultchar=' ', defaultattr=0)
        #self.base_layout.add_child(self.letter_boxed)

        self.strands = Strands(colors=self.colors, defaultchar=' ', defaultattr=0)
        #self.base_layout.add_child(self.strands)

        self.wordle = Wordle(colors=self.colors, defaultchar=' ', defaultattr=0)
        self.base_layout.add_child(self.wordle)

        self.connections = Connections(colors=self.colors, defaultchar=' ', defaultattr=0)
        #self.base_layout.add_child(self.connections)

        self.spelling_bee = SpellingBee(colors=self.colors, defaultchar=' ', defaultattr=0)
        #self.base_layout.add_child(self.spelling_bee)

        self.load()

    def set_app_focus(self, app):
        self.base_layout.children = [app]
        app.resize(self.width, self.height)
        self.refresh(self.stdscr, force=True)

    def load(self):
        self.game_data = load_game_data()
        self.letter_boxed.update_data(self.game_data['letterboxed'])
        self.wordle.update_data(self.game_data['wordle'])
        self.strands.update_data(self.game_data['strands'])
        self.mini.update_data(self.game_data['mini'])
        self.connections.update_data(self.game_data['connections'])
        self.spelling_bee.update_data(self.game_data['spelling-bee'])

    def process_char(self, char):
        if char == -1:
            self.terminate()
            exit(0)
        if char == 49: # 1
            self.set_app_focus(self.wordle)
            return
        if char == 50: # 2
            self.set_app_focus(self.connections)
            return
        if char == 51: # 3
            self.set_app_focus(self.strands)
            return
        if char == 52: # 4
            self.set_app_focus(self.mini)
            return
        if char == 53: #5
            self.set_app_focus(self.letter_boxed)
            return
        if char == 54: #6
            self.set_app_focus(self.spelling_bee)
            return

        self.base_layout.children[0].accept_char(char)
        self.refresh(self.stdscr, force=True)


