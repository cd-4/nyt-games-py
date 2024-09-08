import math
from pycurses.window import Window

from nyt_games_cli import utils

class Mini(Window):

    def __init__(self, *args, **kwargs):
        self.use_colors = True
        self.game_data = {}
        super().__init__(*args, **kwargs)
        self.set_title('Mini')
        self.done = False
        self.guessed_words = []
        self.found_words = []
        self.grid_width = 6
        self.grid_height = 8
        self.current_word = []
        self.found_spangram = False

    def update_data(self, data):
        self.game_data = data
        self.digest_data()

    def digest_data(self):
        self.clues = self.game_data['clues']
        boxes = self.game_data['boxes']

        box_data = []
        self.box_size = int(math.sqrt(len(boxes)))

        row = []
        for box in boxes:
            if len(row) == self.box_size:
                box_data.append(row)
                row = []
            box['found'] = False
            row.append(box)
        box_data.append(row)
        self.grid_data = box_data

    def create_mini(self):
        self.clear_page()
        self.draw_board()

    def clear_page(self):
        for row in range(self.height):
            for col in range(self.width):
                self.update_value(row, col, ' ', 0)

    def draw_board(self):
        hor_gap_size = 3

        total_width = self.box_size * hor_gap_size + self.box_size + 1
        total_height = self.box_size * 2 + 1

        start_col = 3
        start_row = 3

        white = self.colors.get_color_id('White', 'Black')




        for r in range(total_height):
            if r % 2 == 0:
                line = ('+' + '-' * hor_gap_size) * self.box_size + '+'
            else:
                line = ('|' + ' ' * hor_gap_size) * self.box_size + '|'
            self.draw_text(line, start_row + r, start_col, white)

        for row_ind in range(len(self.grid_data)):
            data_row = self.grid_data[row_ind]

            for col_ind in range(len(data_row)):
                element = data_row[col_ind]
                clue = element['clue']
                letter = element['letter']
                found = element['found']

                if row_ind == 2 and col_ind == 1:
                    letter = None
                if row_ind == 2 and col_ind == 2:
                    letter = None
                if row_ind == 1 and col_ind == 2:
                    letter = None
                if row_ind == 0 and col_ind == 2:
                    letter = None
                if row_ind == 3 and col_ind == 4:
                    letter = None
                if row_ind == 0 and col_ind == 4:
                    letter = None

                row = start_row + 1 + row_ind * 2
                col = start_col + 1 + col_ind * 4

                if letter:
                    self.update_value(row, col + 1, letter, white)
                else:
                    '''
                    if row_ind == 0: # First Row
                        self.draw_text('---', row-1, col, 0)
                    elif row_ind == self.box_size - 1: # Last Row
                        self.draw_text('---', row+1, col, 0)

                    if col_ind == 0:
                        self.update_value(row, col-1, '|', 0)
                    elif col_ind == self.box_size - 1:
                        self.update_value(row, col+3, '|', 0)
                    '''

                    self.draw_text('   ', row, col, 0)

        # At this point the lines between black sections will be white still
        # so we need to change them

        for row_ind in range(len(self.grid_data)):
            data_row = self.grid_data[row_ind]

            for col_ind in range(len(data_row)):
                element = data_row[col_ind]

                row_s = start_row + 1 + row_ind * 2
                col_s = start_col + 1 + col_ind * 4

                # Check Left Line
                r = [row_s, col_s]
                l = [row_s, col_s - 2]
                self.match_color(r, l, [row_s, col_s-1])

                # Check Right Line
                r = [row_s, col_s + 4]
                l = [row_s, col_s + 2]
                self.match_color(r, l, [row_s, col_s+3])

                # Check Line Above
                r = [row_s-2, col_s]
                l = [row_s, col_s]
                self.match_color(r, l, [row_s-1, col_s])

                r = [row_s-2, col_s+1]
                l = [row_s, col_s+1]
                self.match_color(r, l, [row_s-1, col_s+1])

                r = [row_s-2, col_s+2]
                l = [row_s, col_s+2]
                self.match_color(r, l, [row_s-1, col_s+2])

                # Check Line Below
                r = [row_s+2, col_s]
                l = [row_s, col_s]
                self.match_color(r, l, [row_s+1, col_s])

                r = [row_s+2, col_s+1]
                l = [row_s, col_s+1]
                self.match_color(r, l, [row_s+1, col_s+1])

                r = [row_s+2, col_s+2]
                l = [row_s, col_s+2]
                self.match_color(r, l, [row_s+1, col_s+2])

                top_left = [row_s - 1, col_s - 1]
                bottom_left = [row_s + 1, col_s - 1]
                top_right = [row_s - 1, col_s + 3]
                bottom_right = [row_s + 1, col_s + 3]
                self.match_corner(top_left)
                self.match_corner(bottom_left)
                self.match_corner(top_right)
                self.match_corner(bottom_right)




    def match_corner(self, corner):
        above = [corner[0] - 1, corner[1]]
        below = [corner[0] + 1, corner[1]]
        left  = [corner[0], corner[1] - 1]
        right = [corner[0], corner[1] + 1]

        cells = [above, below, left, right]
        mods = [self.get_mod(*c) for c in cells]

        if any([m == None for m in mods]):
            return

        mod = mods[0]
        if any([m != mod for m in mods]):
            return

        # All mods the same
        letter = self.get_letter(*corner)
        self.update_value(corner[0], corner[1], letter, mod)


    def match_color(self, one, two, changed_cell):
        mod1 = self.get_mod(*one)
        mod2 = self.get_mod(*two)
        if mod1 == mod2:
            if mod1 != None:
                letter = self.get_letter(*changed_cell)
                self.update_value(changed_cell[0], changed_cell[1], letter, mod1)

    def get_letter(self, row, col):
        if row < len(self.data):
            if col < len(self.data[row]):
                return self.data[row][col][0]
        return None


    def get_mod(self, row, col):
        if row < len(self.data):
            if col < len(self.data[row]):
                return self.data[row][col][1]
        return None



    def prerefresh(self):
        super().prerefresh()
        if self.game_data:
            self.create_mini()

    def add_letter(self, letter):
        pass

    def enter(self):
        pass

    def backspace(self):
        pass

    def tab(self, reverse=False):
        pass

    def accept_char(self, num):
        char = chr(num)

        if not self.done:

            # CTRL + R
            if num == 18:
                self.clear_selection()

            if num == 353: # Shift Tab
                self.tab(reverse=True)

            if num == 9: # Tab
                self.tab()

            if num == 127: # Backspace
                self.backspace()

            if num == 10:
                self.enter()

            if char in 'abcdefghijklmnopqrstuvwxyz':
                self.add_letter(char.upper())

        self.refresh(self.stdscr, force=True)
