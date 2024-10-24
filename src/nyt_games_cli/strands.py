import random
import curses

from pycurses.window import Window

from nyt_games_cli import utils

class Strands(Window):

    def __init__(self, *args, **kwargs):
        self.use_colors = True
        self.game_data = {}
        super().__init__(*args, **kwargs)
        self.set_title('Strands')
        self.done = False
        self.guessed_words = []
        self.found_words = []
        self.grid_width = 6
        self.grid_height = 8
        self.current_word = []
        self.found_spangram = False
        self.hints_used = 0
        self.hint_words = []

    def update_data(self, data):
        self.game_data = data

    def is_valid_word(self, word):
        return word in self.game_data['solutions']

    def current_position(self):
        if self.current_word:
            return self.current_word[-1]
        return None

    def get_clue_words(self):
        return self.game_data['solutions']

    def get_board_data(self):
        return self.game_data['startingBoard']

    def get_all_found_words(self):
        found = self.get_theme_words()
        spangram = self.get_spangram()
        output = {}
        for key in found:
            if key in self.found_words:
                output[key] = found[key]
        if self.found_spangram:
            for key in spangram:
                output[key] = spangram[key]
        return output

    def get_all_found_letter_positions(self):
        output = []
        found_words = self.get_all_found_words()
        for k in found_words:
            output.extend(found_words[k])
        return output

    def get_theme_words(self):
        return self.game_data['themeCoords']

    def get_spangram(self):
        spangram = self.game_data['spangram']
        coords = self.game_data['spangramCoords']
        return { spangram : coords }

    def create_strands(self):
        self.clear_page()
        self.draw_board()
        self.draw_words()
        self.draw_help()
        self.draw_hints()
        self.draw_clue()

    def clear_page(self):
        for c in range(self.width):
            for r in range(self.height):
                self.update_value(r, c, ' ', 0)

    def clear_page(self):
        for row in range(self.height):
            for col in range(self.width):
                self.update_value(row, col, ' ', 0)

    def highlight_word(self, cells, color_mod, line_color_mod):
        if not cells:
            return
        board_data = self.get_board_data()

        num_cells = len(cells)
        for i in range(len(cells) - 1):
            start_cell = cells[i]
            end_cell = cells[i+1]

            letter = board_data[start_cell[0]][start_cell[1]]
            r, c = self.get_cell_screen_location(start_cell)
            er, ec = self.get_cell_screen_location(end_cell)

            l_mod = color_mod
            l_mod = line_color_mod

            if er == r: # Same Row
                min_col = min([c, ec])
                max_col = max([c, ec])
                for line_c in range(min_col + 1, max_col, 1):
                    self.update_value(r, line_c, '-', l_mod)
            elif ec == c: # Same Col
                min_row = min([r, er])
                max_row = max([r, er])
                for line_r in range(min_row + 1, max_row, 1):
                    self.update_value(line_r, c, '|', l_mod)
            else: # Diagonal
                left = [r, c]
                right = [er, ec]
                if left[1] > right[1]:
                    tmp = left
                    left = right
                    right = tmp

                if left[0] > right[0]: # Diagonal Up
                    lr, lc = left
                    rr, rc = right
                    self.update_value(lr - 1, lc + 1, ',', l_mod)
                    self.update_value(lr - 1, lc + 2, '"', l_mod)
                else: # Diagonal Down
                    lr, lc = left
                    rr, rc = right
                    self.update_value(lr + 1, lc + 1, '"', l_mod)
                    self.update_value(lr + 1, lc + 2, ',', l_mod)

            self.update_value(r, c, letter, color_mod)

        last_cell = cells[-1]
        letter = board_data[last_cell[0]][last_cell[1]]
        r, c = self.get_cell_screen_location(last_cell)
        self.update_value(r, c, letter, color_mod)

    def draw_help(self):
        last_row = self.height - 1
        help_text_3 = 'Submit Word: <Enter> | Remove Letter: <Backspace>'
        help_text_2 = 'Clear Word: <Ctrl+R> | Use Hint: <?>'
        help_text =   'Next Letter: <Tab> | Prev Letter: <Shift+Tab>'
        self.draw_text(help_text_3, last_row - 2, 0, 0)
        self.draw_text(help_text_2, last_row - 1, 0, 0)
        self.draw_text(help_text, last_row, 0, 0)

    def draw_words(self):

        if self.found_spangram:
            spangram_color = self.colors.get_color_id('Yellow', 'Black')
            spangram_line_color = self.colors.get_color_id('Black', 'Yellow')
            spangram = self.get_spangram()
            key = list(spangram.keys())[0]
            spangram_cells = spangram[key]
            self.highlight_word(spangram_cells, spangram_color, spangram_line_color)

        # Draw found words
        found_color = self.colors.get_color_id('Cyan', 'Black')
        line_color = self.colors.get_color_id('Black', 'Cyan')
        theme_words = self.get_theme_words()
        for word in self.found_words:
            cells = theme_words[word]
            self.highlight_word(cells, found_color, line_color)

        current_color = self.colors.get_color_id('White', 'Black')
        line_color = self.colors.get_color_id('Black', 'White')
        current_word_cells = [r[1] for r in self.current_word]
        self.highlight_word(current_word_cells, current_color, line_color)

    def has_hint(self):
        used = self.hints_used
        num_guesses = len(self.guessed_words)
        return num_guesses - used * 3 > 2

    def draw_centered_text(self, text, row):
        w = self.width
        col = -1 + (w - len(text)) // 2
        self.draw_text(text, row, col, 0)

    def draw_clue(self):
        clue = self.game_data['clue']
        row, col = self.get_cell_screen_location([0, 0])
        self.draw_centered_text(clue, row - 3)

    def draw_hints(self):

        used = self.hints_used
        num_guesses = len(self.guessed_words)
        hints_allowed = (num_guesses // 3) - used
        hint_progress = 0
        if hints_allowed > 0:
            hint_progress = 3
        else:
            hint_progress = num_guesses % 3


        row, col = self.get_cell_screen_location([self.grid_height-1, 0])

        hint_row = row + 2
        hint_col = col + 4

        self.update_value(hint_row, hint_col, '[', 0)
        self.update_value(hint_row, hint_col + 7, ']', 0)

        hint_text = ' Hint '
        bar_color = self.colors.get_color_id('White', 'Black')
        bar_col = hint_col + 1
        for c in range(len(hint_text)):
            col = hint_col + c + 1
            if c < hint_progress * 2:
                self.update_value(hint_row, col, hint_text[c], bar_color)
            else:
                self.update_value(hint_row, col, hint_text[c], 0)

        if self.hint_words:
            board_data = self.get_board_data()
            hint_color = self.colors.get_color_id('Magenta', 'Black')
            for hint_word in self.hint_words:
                coords = self.get_theme_words()[hint_word]
                for coord in coords:
                    if self.current_word:
                        if coord == self.current_word[-1][1]:
                            continue
                    row, col = self.get_cell_screen_location(coord)
                    current_letter = board_data[coord[0]][coord[1]]
                    self.update_value(row, col, current_letter, hint_color)

    def get_cell_screen_location(self, cell):
        w = self.width
        h = self.height

        line_width = (self.grid_width * 3) - 1
        line_height = (self.grid_height * 2) - 1
        start_col = (w - line_width) // 2
        start_row = (h - line_height) // 2

        return [start_row + cell[0] * 2, start_col + cell[1] * 3]

    def draw_board(self):

        position = self.current_position()

        starting_board = self.get_board_data()
        for r in range(self.grid_height):
            for c in range(self.grid_width):
                row, col = self.get_cell_screen_location([r, c])
                letter = starting_board[r][c]
                color = 0
                if position and position[1] == [r,c]:
                    color = self.colors.get_color_id('Cyan', 'Black')

                self.update_value(row, col, letter, color)

    def prerefresh(self):
        super().prerefresh()
        if self.game_data:
            self.create_strands()

    def get_nearby_cells(self, pos=None):
        if pos is None:
            pos = self.current_position()
        output = []
        for r_off in range(-1, 2, 1):
            for c_off in range(-1, 2, 1):
                r = pos[1][0] + r_off
                c = pos[1][1] + c_off
                if r >= 0 and c >= 0 and r < self.grid_height and c < self.grid_width:
                    output.append([r, c])
        output = [o for o in output if o != pos[1]]
        return output

    def add_letter(self, letter):
        letter_positions = self.find_letter_instances(letter)
        if not letter_positions:
            return

        if not self.current_word:

            found_letters = self.get_all_found_letter_positions()
            for pos in letter_positions:
                if pos not in found_letters:
                    self.current_word = [[letter, pos]]
                    return
            self.current_word = [[letter, unmatched_positions[0]]]

        else:

            nearby = self.get_nearby_cells()
            current_selected = [x[1] for x in self.current_word]
            nearby = [n for n in nearby if n not in current_selected]
            if not nearby:
                return
            board = self.get_board_data()
            valid_nearby = [n for n in nearby if board[n[0]][n[1]] == letter]
            if not valid_nearby:
                return
            all_found_positions = self.get_all_found_letter_positions()
            cleaned_positions = [v for v in valid_nearby if v not in all_found_positions]
            if not cleaned_positions:
                self.current_word.append([letter, valid_nearby[0]])
            else:
                return self.current_word.append([letter, cleaned_positions[0]])

    def tupleset(self, cell_list):
        return set([(c[0], c[1]) for c in cell_list])

    def enter(self):
        current_word_text = ''.join([r[0] for r in self.current_word])
        current_word_cells = [r[1] for r in self.current_word]
        theme_words = self.get_theme_words()
        if current_word_text in theme_words:
            word_cells = theme_words[current_word_text]
            if self.tupleset(current_word_cells) == self.tupleset(word_cells):
                self.game_data['themeCoords'][current_word_text] = current_word_cells
                self.found_words.append(current_word_text)
                if current_word_text in self.hint_words:
                    self.hint_words.remove(current_word_text)
                self.current_word = []
                return

        spangram = self.get_spangram()
        if current_word_text in spangram:
            self.found_spangram = True
            self.current_word = []
            if current_word_text in self.hint_words:
                self.hint_words.remove(current_word_text)
            return

        if self.is_valid_word(current_word_text) and current_word_text not in self.guessed_words:
            self.guessed_words.append(current_word_text)
            self.current_word = []

    def backspace(self):
        if self.current_word:
            self.current_word = self.current_word[:-1]

    def find_letter_instances(self, letter):
        letter_positions = []
        board_data = self.get_board_data()
        for row in range(len(board_data)):
            line = board_data[row]
            for col in range(len(line)):
                if line[col] == letter:
                    letter_positions.append([row, col])
        return letter_positions

    def tab_anywhere(self, current_pos, reverse=False):
        letter, coords = current_pos
        letter_positions = self.find_letter_instances(letter)

        if len(letter_positions) == 1:
            return

        add = -1 if reverse else 1
        ind = letter_positions.index(coords) + add
        new_coords = letter_positions[ind % len(letter_positions)]
        self.current_word = [[letter, new_coords]]

    def tab_around(self, reverse=False):
        last_set_letter = self.current_word[-2]
        current_letter, current_coords = self.current_word[-1]

        board_data = self.get_board_data()
        nearby_cells = self.get_nearby_cells(pos=last_set_letter)
        letter_cells = [[board_data[c[0]][c[1]], c] for c in nearby_cells]
        matching_cells = [x[1] for x in letter_cells if current_letter == x[0]]
        if len(matching_cells) == 1:
            return

        add = -1 if reverse else 1
        ind = matching_cells.index(current_coords) + add
        new_coords = matching_cells[ind % len(matching_cells)]
        self.current_word[-1] = [current_letter, new_coords]

    def tab(self, reverse=False):
        if not self.current_word:
            return
        if len(self.current_word) == 1:
            pos = self.current_position()
            self.tab_anywhere(pos, reverse=reverse)
            return
        self.tab_around(reverse=reverse)

    def move_relative(self, char):
        offset = [0, 0]
        if char == 'W':
            offset = [-1, 0]
        if char == 'A':
            offset = [0, -1]
        if char == 'S':
            offset = [1, 0]
        if char == 'D':
            offset = [0, 1]

    def clear_selection(self):
        self.current_word = []

    def get_hint(self):
        if not self.has_hint():
            return

        theme_words = self.get_theme_words()
        trimmed = [w for w in theme_words if w not in self.found_words]
        hint_word = random.choice(trimmed)
        self.hint_words.append(hint_word)
        self.hints_used += 1

    def accept_char(self, num):
        char = chr(num)

        if not self.done:

            # CTRL + R
            if num == 18:
                self.clear_selection()

            if num == 353:
                self.tab(reverse=True)

            if num == 9:
                self.tab()

            if num == curses.KEY_BACKSPACE:
                self.backspace()

            if num == 10:
                self.enter()

            if num == 63: #?
                self.get_hint()

            if char in 'WASD':
                pass

            if char in 'abcdefghijklmnopqrstuvwxyz':
                self.add_letter(char.upper())

        self.refresh(self.stdscr, force=True)
