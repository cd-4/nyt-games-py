import curses

from pycurses.window import Window
from pycurses import lines

class LetterBoxed(Window):

    def __init__(self, *args, **kwargs):
        self.use_colors = True
        self.box_width = 40
        self.box_height = 20
        self.game_data = {}
        self.current_word = ""
        self.words = []
        super().__init__(*args, **kwargs)
        self.set_title('LetterBoxed')
        self.sides = []
        self.done = False

    def update_data(self, data):
        self.game_data = data
        self.sides = data['sides']
        self.valid_words = data['dictionary']
        self.par = data['par']

    def locate_letter_points(self):
        corners = self.get_box_corners()
        tl, tr, br, bl = corners
        top, right, bottom, left = self.sides
        letter_data = {}

        hor_row_piece = self.box_width // 6
        hor_center_piece = self.box_width // 2

        top_row_row = tl[0] - 1
        letter_data[top[0]] = {
                'point': [top_row_row, tl[1] + hor_row_piece],
                'offset': [2, 0]
                }
        letter_data[top[1]] = {
                'point': [top_row_row, tl[1] + hor_center_piece],
                'offset': [2, 0]
                }
        letter_data[top[2]] = {
                'point': [top_row_row, tr[1] - hor_row_piece],
                'offset': [2, 0]
                }

        bottom_row_row = bl[0] + 1
        letter_data[bottom[0]] = {
                'point': [bottom_row_row, tl[1] + hor_row_piece],
                'offset': [-2, 0]
                }
        letter_data[bottom[1]] = {
                'point': [bottom_row_row, tl[1] + hor_center_piece],
                'offset': [-2, 0]
                }
        letter_data[bottom[2]] = {
                'point': [bottom_row_row, tr[1] - hor_row_piece],
                'offset': [-2, 0]
                }

        ver_col_piece = self.box_height // 6
        ver_center_piece = self.box_height // 2

        right_col_col = tr[1] + 2
        letter_data[right[0]] = {
                'point': [tr[0] + ver_col_piece, right_col_col],
                'offset':  [0, -3]
                }
        letter_data[right[1]] = {
                'point': [tr[0] + ver_center_piece, right_col_col],
                'offset':  [0, -3]
                }
        letter_data[right[2]] = {
                'point': [br[0] - ver_col_piece, right_col_col],
                'offset':  [0, -3]
                }

        left_col_col = tl[1] - 2
        letter_data[left[0]] = {
                'point': [tr[0] + ver_col_piece, left_col_col],
                'offset':  [0, 3]
                }
        letter_data[left[1]] = {
                'point': [tr[0] + ver_center_piece, left_col_col],
                'offset':  [0, 3]
                }
        letter_data[left[2]] = {
                'point': [br[0] - ver_col_piece, left_col_col],
                'offset':  [0, 3]
                }

        return letter_data


    def create_letterboxed(self):
        self.letter_data = self.locate_letter_points()
        self.clear_page()
        self.draw_box()
        self.draw_words()
        self.draw_past_words()
        self.update_current_word()
        self.draw_help()

    def draw_help(self):
        help_str= 'Enter Word: <Enter> | Delete: <Backspace> | Restart <Ctrl+R>'
        row = self.height - 1
        for i in range(len(help_str)):
            self.update_value(row, i, help_str[i], 0)

    def calc_box_height(self):
        self.box_height = min([self.height - 7, 25])
        self.box_width = min([self.box_height * 2, 50])

    def get_box_corners(self):
        self.calc_box_height()
        w = self.width
        h = self.height
        start_col = (w - self.box_width) // 2
        start_row = ((h - self.box_height) // 2) + 1
        end_col = start_col + self.box_width
        end_row = start_row + self.box_height
        return [[start_row, start_col],
                [start_row, end_col],
                [end_row, end_col],
                [end_row, start_col]]

    def clear_page(self):
        corners = self.get_box_corners()
        tl, tr, br, bl = corners
        for row in range(self.height):
            for col in range(self.width):
                self.update_value(row, col, ' ', 0)

    def update_current_word(self):
        if self.done:
            count = len(self.words)
            word = f"You won in {count} words!"
        elif self.current_word:
            word = self.current_word + '_'
        else:
            word = f'Try to solve in {self.par} words'
        tl = self.get_box_corners()[0]
        row = tl[0] - 3
        center_col = tl[1] + self.box_width // 2
        start_word_col = center_col - len(word) // 2
        for i in range(len(word)):
            letter = word[i]
            self.update_value(row, start_word_col + i, letter, 0)


    def draw_box(self):
        corners = self.get_box_corners()
        points = lines.draw_line_series(corners, connect=True)
        for row, col, letter in points:
            self.update_value(row, col, letter, 0)

        for row, col in corners:
            self.update_value(row, col, '+', 0)

        last_letter = self.get_last_letter()
        for letter in self.letter_data:
            data = self.letter_data[letter]
            point = data['point']
            color_mod = 0
            if self.is_letter_seen(letter):
                if self.use_colors:
                    color_mod = self.colors.get_color_id('Black', 'Yellow')
                color_mod = color_mod | curses.A_BOLD
            self.update_value(point[0], point[1], letter, color_mod)

            if letter == last_letter:
                offset = data['offset']
                offset = [-x for x in offset]
                arrow_char = '@'
                arrow_point = [point[0] + offset[0] // 2, point[1] + offset[1]]
                if offset[0] == 0:
                    if offset[1] > 0:
                        arrow_char = '<'
                    else:
                        arrow_char = '>'
                else:
                    if offset[0] > 0:
                        arrow_char = '^'
                    else:
                        arrow_char = 'v'
                
                color_mod = 0
                if self.use_colors:
                    color_mod = self.colors.get_color_id('Black', 'Green')
                self.update_value(arrow_point[0], arrow_point[1], arrow_char, color_mod)


    def get_letter_line_point(self, letter):
        data = self.letter_data[letter]
        point = data['point']
        offset = data['offset']
        return [point[0] + offset[0], point[1] + offset[1]]

    def draw_word_lines(self, word, mod=0):
        line_chunks = []
        for letter in word:
            point = self.get_letter_line_point(letter)
            line_chunks.append(point)
        if line_chunks:
            line_points = lines.draw_line_series(line_chunks)
            for row, col, letter in line_points:
                self.update_value(row, col, letter, mod)


    def draw_words(self):
        for word in self.words:
            self.draw_word_lines(word, mod=0)
        if self.current_word:
            color_mod = 0
            if self.use_colors:
                color_mod = self.colors.get_color_id('Black', 'Red')
            self.draw_word_lines(self.current_word, mod=color_mod)

    def max_word_length(self):
        return max([len(w) for w in self.valid_words])

    def draw_past_words(self):
        tl, tr, br, bl = self.get_box_corners()

        max_word_length = self.max_word_length()
        num_words = len(self.words)
        start_col = tl[1] - max_word_length - 5
        for i in range(num_words):
            word = self.words[i]
            row = tl[0] + i + 2
            for i in range(len(word)):
                letter = word[i]
                self.update_value(row, start_col + i, letter, 0)


    def prerefresh(self):
        super().prerefresh()
        if self.game_data:
            self.create_letterboxed()

    def get_last_letter(self):
        if self.current_word:
            return self.current_word[-1]
        elif self.words:
            return self.words[-1][-1]
        else:
            return ''

    def try_update_current_word(self, letter):
        last_letter = self.get_last_letter()
        if last_letter:
            for side in self.sides:
                if last_letter.upper() in side and letter.upper() in side:
                    return
        self.current_word += letter

    def backspace(self):
        if self.current_word:
            self.current_word = self.current_word[:-1]
        if self.current_word == '':
            if self.words:
                self.current_word = self.words[-1]
                self.words = self.words[:-1]

    def enter(self):
        word = self.current_word
        if word not in self.valid_words:
            return

        self.words.append(word)
        self.current_word = word[-1]

        self.check_completion()

    def restart(self):
        self.current_word = ""
        self.words = []

    def is_letter_seen(self, letter):
        for word in self.words:
            for word_letter in word:
                if letter == word_letter:
                    return True
        return False

    def check_completion(self):
        letters = set(self.letter_data.keys())
        seen = []
        for word in self.words:
            for letter in word:
                seen.append(letter)
        if set(seen) == letters:
            self.done = True

    def accept_char(self, num):
        char = chr(num).upper()
        if not self.done:
            if char in self.letter_data:
                self.try_update_current_word(char)

            if num == curses.KEY_BACKSPACE:
                self.backspace()

            if num == 10:
                self.enter()

        if num == 18:
            self.restart()

        self.refresh(self.stdscr, force=True)
