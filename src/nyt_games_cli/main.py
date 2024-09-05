
import setproctitle
from pycurses.mainwindow import MainWindow
from pycurses.layout import Layout



from nyt_games_cli.letterboxed import LetterBoxed
from nyt_games_cli.wordle import Wordle
from nyt_games_cli.nyt_data import load_game_data

class NYTGames(MainWindow):

    def __init__(self):
        super().__init__([])
        setproctitle.setproctitle('Python - NYT Cli Games')
        self.base_layout = Layout(colors=self.colors, defaultchar='.', defaultattr=0)
        self.add_child(self.base_layout)

        #self.letter_boxed = LetterBoxed(colors=self.colors, defaultchar=' ', defaultattr=0)
        #self.base_layout.add_child(self.letter_boxed)

        self.wordle = Wordle(colors=self.colors, defaultchar=' ', defaultattr=0)
        self.base_layout.add_child(self.wordle)

        self.load()

    def load(self):
        self.game_data = load_game_data()
        #self.letter_boxed.update_data(self.game_data['letterboxed'])
        self.wordle.update_data(self.game_data['wordle'])

    def process_char(self, char):
        if char == -1:
            self.terminate()
            exit(0)
        #self.letter_boxed.accept_char(char)
        self.wordle.accept_char(char)

if __name__ == '__main__':
    NYTGames().loop()

