import math
import curses
import textwrap
from pycurses.window import Window

from nyt_games_cli import utils


SHIFT_VIM_MOVEMENTS = {
    'H': ('horizontal', -1),
    'J': ('vertical', 1),
    'K': ('vertical', -1),
    'L': ('horizontal', 1),
}


class Mini(Window):

    def __init__(self, *args, **kwargs):
        self.game_data = {}
        super().__init__(*args, **kwargs)
        self.set_title('Mini')
        self.done = False
        self.current_position = [0, 0]
        self.is_down = False

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

        self.horizontal_movements = []

        for row_ind in range(self.box_size):
            for col_ind in range(self.box_size):
                cell = self.grid_data[row_ind][col_ind]
                if cell['letter']:
                    self.horizontal_movements.append([row_ind, col_ind])

        self.vertical_movements = []

        for col_ind in range(self.box_size):
            for row_ind in range(self.box_size):
                cell = self.grid_data[row_ind][col_ind]
                if cell['letter']:
                    self.vertical_movements.append([row_ind, col_ind])

        self.guesses = [[None for i in range(self.box_size)] for x in range(self.box_size)]
        self.solved = [[None for i in range(self.box_size)] for x in range(self.box_size)]

        self.current_position = self.horizontal_movements[0]

    def create_mini(self):
        self.clear_page()
        self.draw_completion_text()
        self.draw_board()
        self.draw_hints()
        self.draw_help()

    def draw_help(self):
        lines = (
            'A-Z: Letter | Tab: Direction | Enter/]: Next | [: Previous',
            'Arrow Keys or Shift-H/J/K/L: Move',
        )
        for offset, text in enumerate(lines):
            start_col = max(0, (self.width - len(text)) // 2)
            self.draw_text(
                text[:self.width], self.height - 2 + offset, start_col, 0
            )

    def clear_page(self):
        for row in range(self.height):
            for col in range(self.width):
                self.update_value(row, col, ' ', 0)

    def has_letter(self, row, col):
        if row < 0 or row >= self.box_size:
            return False
        if col < 0 or col >= self.box_size:
            return False
        return self.grid_data[row][col]['letter'] != None

    def get_current_word_cells(self):
        pos = self.current_position
        highlighted_cells = []
        if self.is_down:
            col = pos[1]
            sections = []
            new_section = []
            for row in range(self.box_size):
                if self.has_letter(row, col):
                    new_section.append([row, col])
                else:
                    sections.append(new_section)
                    new_section = []
            sections.append(new_section)
            for section in sections:
                if pos in section:
                    return section
        else:
            row = pos[0]
            sections = []
            new_section = []
            for col in range(self.box_size):
                if self.has_letter(row, col):
                    new_section.append([row, col])
                else:
                    sections.append(new_section)
                    new_section = []
            sections.append(new_section)
            for section in sections:
                if pos in section:
                    return section
        return []

    def get_start_col(self):
        return max(0, (self.width - self.get_grid_total_width()) // 2)

    def get_start_row(self):
        content_height = (
            self.get_grid_total_height() + 1 + self.get_hints_height()
        )
        return max(1, (self.height - 1 - content_height) // 2)

    def get_hor_gap_size(self):
        return 3

    def get_grid_total_width(self):
        hor_gap_size = self.get_hor_gap_size()
        return self.box_size * hor_gap_size + self.box_size + 1

    def get_grid_total_height(self):
        return self.box_size * 2 + 1

    def get_hints_height(self):
        return max((len(lines) for lines in self.get_clue_columns()), default=0)

    def get_clue_column_width(self):
        gap = 4
        num_columns = max(1, len(self.clues))
        return max(1, (self.width - gap * (num_columns - 1)) // num_columns)

    def get_clue_columns(self):
        current_clue = self.get_current_clue()
        column_width = self.get_clue_column_width()
        clue_columns = []

        for direction, direction_clues in self.clues.items():
            lines = [(direction + ':', curses.A_BOLD)]
            for number, clue_text in direction_clues.items():
                is_active = (
                    int(number) == current_clue
                    and self.is_down == (direction == 'Down')
                )
                if is_active:
                    mod = (
                        self.colors.get_color_id('Cyan', 'Black')
                        | curses.A_BOLD
                    )
                else:
                    mod = 0

                prefix = f'  {number}: '
                available_width = max(1, column_width - len(prefix))
                wrapped = textwrap.wrap(
                    clue_text,
                    width=available_width,
                    break_long_words=True,
                    break_on_hyphens=False,
                ) or ['']
                continuation_prefix = ' ' * len(prefix)
                for index, clue_line in enumerate(wrapped):
                    line_prefix = prefix if index == 0 else continuation_prefix
                    lines.append((line_prefix + clue_line, mod))
            clue_columns.append(lines)

        return clue_columns

    def get_current_clue(self):
        pos = self.get_word_start()
        clue = self.grid_data[pos[0]][pos[1]]['clue']
        return int(clue)

    def get_word_start(self):
        pos = self.current_position
        if self.is_down:
            while self.has_letter(pos[0]-1, pos[1]) and pos[0]-1 >= 0:
                pos = [pos[0]-1, pos[1]]
        else:
            while self.has_letter(pos[0], pos[1]-1) and pos[1]-1 >= 0:
                pos = [pos[0], pos[1]-1]
        return pos

    def switch_axis(self):
        self.is_down = not self.is_down

    def draw_completion_text(self):
        if not self.done:
            return

        start_row = self.get_start_row()
        start_col = self.get_start_col()

        self.draw_text("You Win!", start_row - 2, start_col, curses.A_BOLD)
            

    def draw_board(self):
        hor_gap_size = self.get_hor_gap_size()

        total_width = self.get_grid_total_width()
        total_height = self.get_grid_total_height()

        start_col = self.get_start_col()
        start_row = self.get_start_row()

        white = self.colors.get_color_id('White', 'Black')
        word_cells = self.get_current_word_cells()

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

                row = start_row + 1 + row_ind * 2
                col = start_col + 1 + col_ind * 4

                if letter:
                    text = ' {} '.format(letter)
                    foreground = 'Black'
                    background = 'White'
                    if self.current_position == [row_ind, col_ind]:
                        background = 'Yellow'
                    elif [row_ind, col_ind] in word_cells:
                        background = 'Cyan'

                    guess = self.guesses[row_ind][col_ind]
                    if guess:
                        if self.solved[row_ind][col_ind]:
                            foreground = 'Blue'
                        color = self.colors.get_color_id(background, foreground)
                        self.draw_text(' {} '.format(guess), row, col, color)
                    else:
                        color = self.colors.get_color_id(background, foreground)
                        self.draw_text('   '.format(guess), row, col, color)

                    if clue:
                        self.draw_text(str(clue), row-1, col-1, white)

                else:
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

    def draw_hints(self):
        total_height = self.get_grid_total_height()

        start_row = self.get_start_row()

        clue_columns = self.get_clue_columns()
        column_width = self.get_clue_column_width()
        total_width = (
            len(clue_columns) * column_width
            + max(0, len(clue_columns) - 1) * 4
        )
        column_start = max(0, (self.width - total_width) // 2)
        hint_row = start_row + total_height + 1
        for lines in clue_columns:
            for row_offset, (text, mod) in enumerate(lines):
                self.draw_text(
                    text[:column_width],
                    hint_row + row_offset,
                    column_start,
                    mod,
                )
            column_start += column_width + 4


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

        yellow = self.colors.get_color_id('Yellow', 'Black')
        cyan = self.colors.get_color_id('Cyan', 'Black')

        solved_yellow = self.colors.get_color_id('Yellow', 'Blue')
        solved_cyan = self.colors.get_color_id('Cyan', 'Blue')

        matched_colors = [yellow, cyan, solved_yellow, solved_cyan]

        if mod1 == mod2:
            if mod1 != None:
                letter = self.get_letter(*changed_cell)
                self.update_value(changed_cell[0], changed_cell[1], letter, mod1)
        elif mod1 in matched_colors and mod2 in matched_colors:
                letter = self.get_letter(*changed_cell)
                self.update_value(changed_cell[0], changed_cell[1], letter, cyan)


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

    def go_to_previous_letter(self):
        if self.is_down:
            self.move_down(-1)
        else:
            self.move_right(-1)

    def go_to_next_letter(self):
        if self.is_down:
            self.move_down(1)
        else:
            self.move_right(1)

    def get_word_starts(self):
        movements = (
            self.vertical_movements if self.is_down else self.horizontal_movements
        )
        starts = []
        for position in movements:
            row, col = position
            previous = [row - 1, col] if self.is_down else [row, col - 1]
            if not self.has_letter(*previous):
                starts.append(position)
        return starts

    def move_word(self, amount):
        starts = self.get_word_starts()
        if not starts:
            return
        current_start = self.get_word_start()
        current_index = starts.index(current_start)
        self.current_position = starts[(current_index + amount) % len(starts)]

    def go_to_next_word(self):
        self.move_word(1)

    def go_to_previous_word(self):
        self.move_word(-1)

    def add_letter(self, letter):
        pos = self.current_position
        if not self.solved[pos[0]][pos[1]]:
            self.guesses[pos[0]][pos[1]] = letter
        self.go_to_next_letter()
        self.check_if_complete()

    def is_puzzle_solved(self):
        for row in range(self.box_size):
            for col in range(self.box_size):
                letter = self.grid_data[row][col]['letter']
                guess = self.guesses[row][col]
                if letter:
                    if guess is None:
                        return False
                    if letter != self.guesses[row][col]:
                        return False
        return True

    def check_if_complete(self):
        if self.is_puzzle_solved():
            self.done = True

    def enter(self):
        self.go_to_next_word()

    def backspace(self):
        pos = self.current_position
        self.guesses[pos[0]][pos[1]] = None
        self.go_to_previous_letter()
        pos = self.current_position
        self.guesses[pos[0]][pos[1]] = None

    def tab(self, reverse=False):
        self.switch_axis()

    def move_right(self, amount):
        if self.current_position not in self.horizontal_movements:
            return
        index = self.horizontal_movements.index(self.current_position)
        new_ind = (index + amount) % len(self.horizontal_movements)
        self.current_position = self.horizontal_movements[new_ind]

    def move_down(self, amount):
        index = self.vertical_movements.index(self.current_position)
        new_ind = (index + amount) % len(self.vertical_movements)
        self.current_position = self.vertical_movements[new_ind]

    def check_puzzle(self):
        for r in range(self.box_size):
            for c in range(self.box_size):
                guessed = self.guesses[r][c]
                correct = self.grid_data[r][c]['letter']
                if guessed == correct:
                    self.solved[r][c] = True

    def accept_char(self, num):
        char = chr(num)

        if not self.done:

            if char in SHIFT_VIM_MOVEMENTS:
                axis, amount = SHIFT_VIM_MOVEMENTS[char]
                if axis == 'vertical':
                    self.move_down(amount)
                else:
                    self.move_right(amount)
                self.refresh(self.stdscr, force=True)
                return

            if num == 258 or char == 'S': # Down Arrow
                self.move_down(1)
            if num == 259 or char == 'W': # Up Arrow
                self.move_down(-1)
            if num == 260 or char == 'A': # Left Arrow
                self.move_right(-1)
            if num == 261 or char == 'D': # Right Arrow
                self.move_right(1)

            # CTRL + R
            if num == 18:
                self.clear_selection()

            if num == 353: # Shift Tab
                self.tab(reverse=True)

            if num == 9: # Tab
                self.tab()

            if num == curses.KEY_BACKSPACE:
                self.backspace()

            if char == '[':
                self.go_to_previous_word()

            elif char == ']':
                self.go_to_next_word()

            elif num in (curses.KEY_ENTER, 10, 13):
                self.enter()

            if char in 'abcdefghijklmnopqrstuvwxyz':
                self.add_letter(char.upper())

            if num == 63: # '?'
                self.check_puzzle()

        self.refresh(self.stdscr, force=True)
