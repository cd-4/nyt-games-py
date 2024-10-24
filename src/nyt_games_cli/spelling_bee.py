import curses
import random


from pycurses.window import Window

from nyt_games_cli import utils

class SpellingBee(Window):

    def __init__(self, *args, **kwargs):
        self.use_colors = True
        self.game_data = {}
        super().__init__(*args, **kwargs)
        self.set_title('Spelling Bee')
        self.done = False
        self.current_word = ''
        self.guessed_words = []

    def update_data(self, data):
        self.game_data = data
        self.center_letter = data['centerLetter'].upper()
        self.outer_letters = [x.upper() for x in data['outerLetters']]
        self.valid_words = [word.upper() for word in data['answers']]

    def is_valid_word(self, word):
        return word in self.valid_words

    def is_valid_letter(self, letter):
        return letter in self.outer_letters or letter == self.center_letter

    def create_bee(self):
        self.clear_page()
        self.draw_board()
        self.draw_current_text()
        self.draw_guessed_words()

    def clear_page(self):
        for c in range(self.width):
            for r in range(self.height):
                self.update_value(r, c, ' ', 0)

    def get_start_row(self):
        return (self.height - 10) // 2

    def get_start_column(self):
        return (self.width - 16) // 2

    def draw_current_text(self):
        text = self.current_word + '_'
        start_col = (self.width - len(text)) // 2
        self.draw_text(text, self.get_start_row() - 2, start_col, curses.A_BOLD)

    def highlight_color(self, row, col, color_mod):
        if row >= len(self.data) or row < 0:
            return
        if col >= len(self.data[row]) or col < 0:
            return
        letter = self.data[row][col][0]
        self.update_value(row, col, letter, color_mod)

    def highlight_cell(self, letter_position):
        values = [
                    [-1, -1], [-1, 0], [-1, 1],
                    [0, -2], [0, -1], [0, 0], [0, 1], [0, 2],
                    [1, -1], [1, 0], [1, 1],
                 ]
        row, col = letter_position
        yellow_mod = self.colors.get_color_id('Yellow', 'Black')
        for row_off, col_off in values:
            r = row + row_off
            c = col + col_off
            self.highlight_color(r, c, yellow_mod)

    def draw_guessed_words(self):
        start_row = self.get_start_row() + 13
        max_width = self.width

        text_lines = []
        text = ''
        for word in self.guessed_words:
            text += word + ', '
            if len(text) > max_width - 2:
                text = text[:-(len(word) + 2)]
                text_lines.append(text)
                text = word + ', '
        text_lines.append(text)

        word_count = "Words: " + str(len(self.guessed_words))
        c = (self.width - len(word_count)) // 2
        self.draw_text(word_count, start_row - 2, c, curses.A_UNDERLINE | curses.A_BOLD)
        for r in range(len(text_lines)):
            line = text_lines[r]
            start_col = (self.width - len(line)) // 2
            self.draw_text(line, start_row + r, start_col, 0)


    def draw_board(self):
        line1  = "       ___"
        line2  = "      /   \\"
        line3  = "  .--  *  --."
        line4  = " /    \\___/    \\"
        line5  = " \\ *  /   \\  * /"
        line6  = "  --  *  --"
        line7  = " /    \\___/    \\"
        line8  = " \\ *  /   \\  * /"
        line9  = "  '--  *  --'"
        line10 = "      \\___/"
        lines = [line1, line2, line3, line4, line5,
                 line6, line7, line8, line9, line10]

        letter_positions = [
                [2, 8],
                [4, 3],
                [4, 13],
                [7, 3],
                [7, 13],
                [8, 8],
                ]
        center_position = [5, 8]

        outer = self.outer_letters

        #for row, col in letter_positions + [center_position]:
        for i in range(len(self.outer_letters)):
            row, col = letter_positions[i]
            line_letters = [l for l in lines[row]]
            line_letters[col] = self.outer_letters[i]
            lines[row] = ''.join(line_letters)

        crow, ccol = center_position
        line_letters = [l for l in lines[crow]]
        line_letters[ccol] = self.center_letter
        lines[crow] = ''.join(line_letters)

        start_row = self.get_start_row()
        start_col = self.get_start_column()
        yellow = self.colors.get_color_id('Yellow', 'Black')
        for i in range(len(lines)):
            line = lines[i]
            row = start_row + i
            color_mod = 0
            self.draw_text(line, row, start_col, 0)

        self.highlight_cell([start_row + crow, start_col + ccol])


    def prerefresh(self):
        super().prerefresh()
        if self.game_data:
            self.create_bee()

    def add_letter(self, letter):
        if not self.is_valid_letter(letter):
            return
        self.current_word += letter

    def enter(self):
        if not self.is_valid_word(self.current_word):
            return
        if self.current_word in self.guessed_words:
            return

        self.guessed_words.append(self.current_word)
        self.clear_selection()

    def backspace(self):
        if not self.current_word:
            return
        self.current_word = self.current_word[:-1]

    def clear_selection(self):
        self.current_word = ''

    def shuffle_letters(self):
        random.shuffle(self.outer_letters)

    def accept_char(self, num):
        char = chr(num)

        if not self.done:

            # CTRL + R
            if num == 18:
                #self.clear_selection()
                self.shuffle_letters()

            if num == curses.KEY_BACKSPACE:
                self.backspace()

            if num == 10:
                self.enter()

            if char in 'abcdefghijklmnopqrstuvwxyz':
                self.add_letter(char.upper())

        self.refresh(self.stdscr, force=True)
