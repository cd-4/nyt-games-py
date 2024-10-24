
import os
import requests
import curses
import time
import random

from pycurses.window import Window
from pycurses import lines

from nyt_games_cli import utils

class Connections(Window):

    def __init__(self, *args, **kwargs):
        self.game_data = {}
        super().__init__(*args, **kwargs)
        self.set_title('Connections')
        self.done = False
        self.selected = []
        self.solved = []
        self.guesses_remaining = 4
        self.was_close = False

    def update_data(self, new_data):
        self.game_data = new_data
        self.digest_data()

    def digest_data(self):
        categories = self.game_data['categories']
        self.all_cards = []
        self.solutions = []
        cat_colors = [
                self.colors.get_color_id('Yellow', 'Black'),
                self.colors.get_color_id('Green', 'Black'),
                self.colors.get_color_id('Cyan', 'Black'),
                self.colors.get_color_id('Magenta', 'Black'),
                ]

        cat_ind = 0
        self.cat_colors = {}
        for category_dict in categories:
            solution = {}
            category_title = category_dict['title']
            solution['title'] = category_title
            solution_words = []
            cards = category_dict['cards']
            self.cat_colors[category_title] = cat_colors[cat_ind]
            cat_ind += 1
            for card in cards:
                card['selected'] = False
                card['category'] = category_title
                self.all_cards.append(card)
                solution_words.append(card['content'])
            solution['words'] = set(solution_words)
            self.solutions.append(solution)


        self.all_cards.sort(key=lambda x: x['position'])
        self.max_card_length = max([len(x['content']) for x in self.all_cards])

    def create_connections(self):
        self.clear_page()
        self.draw_connections()
        self.draw_guesses()
        self.draw_close()
        self.draw_end_text()
        self.draw_help()

    def draw_end_text(self):
        if not self.done:
            return
        text = "You Lose!"
        if len(self.solved) == 4:
            text = "You Win!"

        start_row = self.get_start_row()
        start_col = (self.width - len(text)) // 2

        self.draw_text(text, start_row - 3, start_col, curses.A_BOLD)

    def draw_help(self):
        text = 'A-P: Toggle Cards | <Enter> Confirm Guess'
        self.draw_text(text, self.height - 1, 0, 0)

    def draw_close(self):
        row = self.get_start_row()
        col = self.get_start_column()

    def draw_guesses(self):
        row = self.get_start_row()
        col = self.get_start_column()

        guesses_str = 'Guesses:' + ' O' * self.guesses_remaining
        self.draw_text(guesses_str, row + 12, col, 0)
        if self.was_close:
            color_mod = self.colors.get_color_id('Black', 'Red')
            self.draw_text('Close!', row + 13, col, color_mod)

    def get_full_row_width(self):
        return self.max_card_length * 4 + 12

    def get_fixed_string(self, word, length=None):
        if length is None:
            length = self.max_card_length
        spaces = length - len(word)
        half = spaces // 2
        return ' ' * (half) + word + ' ' * half + ' ' * (spaces % 2)


    def clear_page(self):
        for r in range(self.height):
            for c in range(self.width):
                self.update_value(r, c, ' ', 0)

    def get_start_column(self):
        full_row_width = self.get_full_row_width()
        return (self.width  - full_row_width) // 2

    def get_start_row(self):
        return (self.height - 12) // 2

    def get_unsolved_cards(self):
        return [c for c in self.all_cards if c['category'] not in self.solved]

    def get_solved_cards(self):
        cards = []
        for r in range(len(self.solved)):
            cat = self.solved[r]
            category_cards = [c for c in self.all_cards if c['category'] == cat]
            cards.extend(category_cards)
        return cards

    def get_centered_text_col(self, text):
        return (self.width - len(text)) // 2

    def draw_connections(self):

        full_row_width = self.get_full_row_width()
        start_col = self.get_start_column()
        start_row = self.get_start_row()
        for r in range(len(self.solved)):
            cat = self.solved[r]
            cards = []
            color_mod = self.cat_colors[cat]
            category_cards = [c for c in self.all_cards if c['category'] == cat]
            card_text = ','.join([c['content'] for c in category_cards])
            line_text = '+' + '-' * (full_row_width + 1) + '+'
            row = start_row + r * 3
            line_str = self.get_fixed_string(card_text, length=full_row_width+1)
            category_str = self.get_fixed_string(cat, length=full_row_width+1)
            self.draw_text(line_text, row-1, start_col, color_mod)
            self.draw_text(cat, row-1, start_col+1, color_mod)
            self.draw_text('+' + line_str + '+', row, start_col, color_mod)
            self.draw_text(line_text, row+1, start_col, color_mod)

        unsolved_cards = [c for c in self.all_cards if c['category'] not in self.solved]

        for r in range(len(self.solved), 4):
            for c in range(4):
                ind = r * 4 + c - len(self.solved) * 4
                card = unsolved_cards[ind]
                self.draw_card(card, r, c, 0)

    def draw_card(self, card, r, c, color_mod=0):
        start_col = self.get_start_column()
        start_row = self.get_start_row()
        card_length = self.max_card_length + 2

        letter_mod = self.colors.get_color_id('Red', 'White')
        selected_mod = self.colors.get_color_id('White', 'Black')

        alphabet = 'ABCDEFGHIJKLMNOP'
        ind = r * 4 + c
        card_text = card['content']
        letter = alphabet[ind]
        string = self.get_fixed_string(card_text) + '|'
        row = start_row + r * 3
        col = start_col + c * (card_length + 2)

        #color_mod = 0
        if card['selected'] and color_mod == 0:
            color_mod = selected_mod
        #self.update_value(row, col, letter, letter_mod)
        self.draw_text(f' {letter} ', row, col-1, letter_mod)
        self.draw_text(string, row, col+2, color_mod)
        line_str = '+' + '-' * (self.max_card_length+1) + '+'
        self.draw_text(line_str, row-1, col, color_mod)
        self.draw_text(line_str, row+1, col, color_mod)


    def prerefresh(self):
        super().prerefresh()
        if self.game_data:
            self.create_connections()

    def get_selected_words(self):
        output = []
        for card in self.all_cards:
            if card['selected']:
                output.append(card['content'])
        return set(output)

    def num_selected(self):
        count = 0
        for card in self.all_cards:
            if card['selected']:
                count += 1
        return count

    def toggle_cell(self, index):
        card = self.all_cards[index]
        is_selected = card['selected']
        if card['category'] in self.solved:
            return

        if not is_selected:
            if self.num_selected() >= 4:
                return

        self.all_cards[index]['selected'] = not self.all_cards[index]['selected']
        if self.was_close:
            self.was_close = False

    def enter(self):
        if self.num_selected() != 4:
            return

        selected = self.get_selected_words()
        for solution in self.solutions:
            if selected == solution['words']:
                title = solution['title']
                self.solved.append(title)
                for card in self.all_cards:
                    card['selected'] = False
                self.all_cards = self.get_solved_cards() + self.get_unsolved_cards()
                if len(self.solved) == 4:
                    self.done = True
                return
            if len(selected.intersection(solution['words'])) == 3:
                self.was_close = True
        self.guesses_remaining -= 1
        if self.guesses_remaining == 0:
            self.done = True
        self.all_cards = self.get_solved_cards() + self.get_unsolved_cards()

    def shuffle(self):
        solved = self.get_solved_cards()
        unsolved = self.get_unsolved_cards()
        random.shuffle(unsolved)
        self.all_cards = solved + unsolved

    def backspace(self):
        pass

    def accept_char(self, num):
        char = chr(num).upper()
        letters = 'ABCDEFGHIJKLMNOP'

        if self.done:
            return

        if char in letters:
            ind = letters.index(char)
            self.toggle_cell(ind)

        if num == 10:
            self.enter()

        # CTRL + R
        if num == 18:
            self.shuffle()

        if num == curses.KEY_BACKSPACE:
            self.backspace()

        self.refresh(self.stdscr, force=True)
