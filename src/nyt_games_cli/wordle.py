import os
import requests
import curses
import time

from pycurses.window import Window
from pycurses import lines

from nyt_games_cli import utils

class Wordle(Window):

    def __init__(self, *args, **kwargs):
        self.use_colors = True
        self.solution = ''
        self.words = []
        self.valid_words = self.get_valid_words()
        self.current_word = ''
        self.num_attempts = 6
        self.word_size = 5
        super().__init__(*args, **kwargs)
        self.set_title('Wordle')
        self.done = False
        self.found_letters = []
        self.close_letters = []
        self.guessed_letters = []

    def get_valid_words(self):

        data_dir = utils.get_app_data_dir('wordle')
        word_file = os.path.join(data_dir, 'words.txt')
        if not os.path.exists(word_file):
            url = 'https://gist.githubusercontent.com/cfreshman/d97dbe7004522f7bc52ed2a6e22e2c04/raw/633058e11743065ad2822e1d2e6505682a01a9e6/wordle-nyt-words-14855.txt'
            res = requests.get(url)
            text = res.text.upper()
            with open(word_file, 'w+') as f:
                f.write(text)
            return text.split('\n')

        with open(word_file, 'r') as f:
            words = f.read()
        return words.split('\n')

    def is_valid_word(self, word):
        is_valid = word in self.valid_words
        return is_valid

    def update_data(self, data):
        self.solution = data.upper()

    def create_wordle(self):
        self.clear_page()
        self.draw_wordle()
        self.draw_keyboard()
        self.draw_help()

    def calc_box_height(self):
        self.box_height = min([self.height - 7, 25])
        self.box_width = min([self.box_height * 2, 50])

    def clear_page(self):
        for row in range(self.height):
            for col in range(self.width):
                self.update_value(row, col, ' ', 0)

    def get_wordle_start_row(self):
        h = self.height
        content_height = 6 + 2 + 3
        return (h - content_height) // 2

    def draw_victory_text(self, text):
        start_row = self.get_wordle_start_row()
        text_row = start_row - 2
        w = self.width
        start_col = (w - len(text)) // 2
        for i in range(len(text)):
            col = start_col + i
            row = text_row
            self.update_value(row, col, text[i], curses.A_BOLD)


    def draw_wordle(self):
        w = self.width
        h = self.height

        line_width = (self.word_size * 2) - 1
        start_col = (w - line_width) // 2
        start_row = self.get_wordle_start_row()

        if self.done:
            if self.words[-1] == self.solution:
                self.draw_victory_text('You Win!')
            else:
                self.draw_victory_text('You Lose!')


        self.found_letters = []
        self.close_letters = []
        self.guessed_letters = []

        first_underscore = True
        for r in range(self.num_attempts):
            word = ''
            verify = False
            if r < len(self.words):
                word = self.words[r]
                verify = True
            elif r == len(self.words) and self.current_word:
                word = self.current_word

            if verify:
                colors = self.get_colors(word)
            else:
                colors = [0 for i in range(self.word_size)]

            for c in range(self.word_size):
                row = start_row + r
                col = start_col + c*2
                letter = '_'
                color = colors[c]
                if c < len(word):
                    letter = word[c]
                if letter == '_' and first_underscore:
                    first_underscore = False
                    if len(self.current_word) != 5:
                        color = self.colors.get_color_id('White', 'Black')

                self.update_value(row, col, letter, color)

    def draw_help(self):
        text = 'A-Z: Add Letter | <Enter> Submit Guess'
        self.draw_text(text, self.height - 1, 0, 0)

    def draw_keyboard(self):
        wordle_bottom = self.get_wordle_start_row() + self.num_attempts + 2
        top_row = 'qwertyuiop'.upper()
        middle_row = 'asdfghjkl'.upper()
        bottom_row = 'zxcvbnm'.upper()

        w = self.width
        h = self.height
        row_start = wordle_bottom


        line_width = (len(top_row) * 2) - 1
        start_col = (w - line_width) // 2

        def draw_key_row(letters):
            for i in range(len(letters)):
                row = row_start
                col = start_col + i*2
                letter = letters[i]
                mod = curses.A_BOLD
                if letter in self.found_letters:
                    mod = self.colors.get_color_id('Green', 'Black') | curses.A_BOLD
                elif letter in self.close_letters:
                    mod = self.colors.get_color_id('Yellow', 'Black') | curses.A_BOLD
                elif letter in self.guessed_letters:
                    mod = 0
                self.update_value(row, col, letter, mod)

        draw_key_row(top_row)

        start_col += 1
        row_start += 1
        draw_key_row(middle_row)

        start_col += 1
        row_start += 1
        draw_key_row(bottom_row)

    def get_colors(self, word):
        colors = [0 for i in range(self.word_size)]

        word_letters = [l for l in word]
        target_letters = [l for l in self.solution]

        match_color = self.colors.get_color_id('Green', 'Black')
        close_color = self.colors.get_color_id('Yellow', 'Black')

        result = [0] * self.word_size

        
        # First pass: Check for green (correct position and letter)
        #target_letters = list(target)
        for i in range(self.word_size):
            if word_letters[i] == target_letters[i]:
                result[i] = match_color
                target_letters[i] = None  # Remove this letter from target_letters
                self.found_letters.append(word_letters[i])
              
        # Second pass: Check for yellow (correct letter, wrong position)
        for i in range(self.word_size):
            if result[i] == 0:
                if word_letters[i] in target_letters:
                    result[i] = close_color
                    target_letters[target_letters.index(word_letters[i])] = None
                    letter = word_letters[i]
                    if letter not in self.found_letters:
                        self.close_letters.append(letter)
        for letter in word:
            if letter not in self.solution:
                self.guessed_letters.append(letter)
                    
        return result



    def prerefresh(self):
        super().prerefresh()
        if self.solution:
            self.create_wordle()

    def add_letter(self, letter):
        if len(self.current_word) < 5:
            self.current_word += letter

    def enter(self):
        if len(self.current_word) != 5:
            return
        
        if not self.is_valid_word(self.current_word):
            return

        if self.current_word == self.solution:
            self.words.append(self.current_word)
            self.current_word = ''
            self.done = True
            return

        self.words.append(self.current_word)
        self.current_word = ''

        if len(self.words) == self.num_attempts:
            self.done = True

    def backspace(self):
        if self.current_word:
            self.current_word = self.current_word[:-1]

    def accept_char(self, num):
        char = chr(num).upper()

        if not self.done:
            if num == curses.KEY_BACKSPACE:
                self.backspace()

            if num == 10:
                self.enter()

            if char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                self.add_letter(char)

        self.refresh(self.stdscr, force=True)
