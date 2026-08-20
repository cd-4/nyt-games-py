import curses
import unittest
from unittest.mock import MagicMock, call, patch

from nyt_games_cli.connections import Connections
from nyt_games_cli.letterboxed import LetterBoxed
from nyt_games_cli.mini_crossword import Mini
from nyt_games_cli.nyt_data import parse_mini_data
from nyt_games_cli.spelling_bee import SpellingBee
from nyt_games_cli.strands import Strands
from nyt_games_cli.wordle import Wordle
from nyt_games_cli import __main__


class FakeColors:
    def get_color_id(self, foreground, background):
        return 0


class PuzzleDataTests(unittest.TestCase):
    @staticmethod
    def make_mini(size=3):
        game = object.__new__(Mini)
        game.box_size = size
        game.grid_data = [
            [
                {'letter': chr(65 + (row * size + col) % 26),
                 'clue': row * size + col + 1, 'found': False}
                for col in range(size)
            ]
            for row in range(size)
        ]
        game.horizontal_movements = [
            [row, col] for row in range(size) for col in range(size)
        ]
        game.vertical_movements = [
            [row, col] for col in range(size) for row in range(size)
        ]
        game.current_position = [0, 0]
        game.is_down = False
        game.done = False
        game.guesses = [[None] * size for _ in range(size)]
        game.solved = [[None] * size for _ in range(size)]
        game.clues = {
            'Across': {str(row * size + 1): f'Across {row}' for row in range(size)},
            'Down': {str(col + 1): f'Down {col}' for col in range(size)},
        }
        game.width = 80
        game.height = 30
        game.colors = FakeColors()
        game.stdscr = None
        game.refresh = lambda *args, **kwargs: None
        return game

    def test_mini_is_centered(self):
        game = self.make_mini(size=5)

        self.assertEqual(
            game.get_start_col(),
            (game.width - game.get_grid_total_width()) // 2,
        )
        content_height = (
            game.get_grid_total_height() + 1 + game.get_hints_height()
        )
        self.assertEqual(
            game.get_start_row(),
            (game.height - 1 - content_height) // 2,
        )

    def test_mini_shift_vim_navigation(self):
        game = self.make_mini()
        game.current_position = [1, 1]

        game.accept_char(ord('H'))
        self.assertEqual(game.current_position, [1, 0])
        game.accept_char(ord('J'))
        self.assertEqual(game.current_position, [2, 0])
        game.accept_char(ord('L'))
        self.assertEqual(game.current_position, [2, 1])
        game.accept_char(ord('K'))
        self.assertEqual(game.current_position, [1, 1])

    def test_mini_brackets_move_between_clues(self):
        game = self.make_mini()
        game.current_position = [1, 0]

        game.accept_char(ord('['))

        self.assertEqual(game.current_position, [0, 0])
        game.accept_char(ord(']'))
        self.assertEqual(game.current_position, [1, 0])

    def test_mini_enter_moves_to_next_clue(self):
        for enter_code in (10, 13, curses.KEY_ENTER):
            game = self.make_mini()
            game.current_position = [0, 0]

            game.accept_char(enter_code)

            self.assertEqual(game.current_position, [1, 0])

    def test_mini_highlights_active_clue(self):
        game = self.make_mini()
        game.colors.get_color_id = lambda *args: 64
        drawn = []
        game.draw_text = lambda text, row, col, mod: drawn.append((text, mod))

        game.draw_hints()

        active = [mod for text, mod in drawn if text == '  1: Across 0']
        inactive = [mod for text, mod in drawn if text == '  1: Down 0']
        self.assertEqual(active, [64 | curses.A_BOLD])
        self.assertEqual(inactive, [0])

    @patch.object(__main__.curses, 'endwin')
    @patch.object(__main__.curses, 'nl')
    @patch.object(__main__.curses, 'nocbreak')
    @patch.object(__main__.curses, 'echo')
    @patch.object(__main__, 'NYTGames')
    def test_ctrl_c_restores_terminal(
        self, nyt_games, echo, nocbreak, nl, endwin
    ):
        game = MagicMock()
        game.loop.side_effect = KeyboardInterrupt
        nyt_games.return_value = game

        status = __main__.main()

        self.assertEqual(status, 130)
        game.stdscr.keypad.assert_called_once_with(False)
        echo.assert_called_once_with()
        nocbreak.assert_called_once_with()
        nl.assert_called_once_with()
        endwin.assert_called_once_with()

    @patch.object(__main__.curses, 'endwin')
    @patch.object(__main__.curses, 'nl')
    @patch.object(__main__.curses, 'nocbreak')
    @patch.object(__main__.curses, 'echo')
    @patch.object(__main__, 'NYTGames', side_effect=RuntimeError('startup failed'))
    def test_startup_error_still_restores_terminal(
        self, nyt_games, echo, nocbreak, nl, endwin
    ):
        with self.assertRaisesRegex(RuntimeError, 'startup failed'):
            __main__.main()

        echo.assert_called_once_with()
        nocbreak.assert_called_once_with()
        nl.assert_called_once_with()
        endwin.assert_called_once_with()

    @staticmethod
    def make_strands(board):
        game = object.__new__(Strands)
        game.game_data = {
            'startingBoard': board,
            'themeCoords': {},
            'spangram': '',
            'spangramCoords': [],
        }
        game.grid_height = len(board)
        game.grid_width = len(board[0])
        game.current_word = []
        game.found_words = []
        game.found_spangram = False
        return game

    def test_strands_backtracks_when_current_letter_cannot_extend(self):
        game = self.make_strands([
            'AXAM',
            'XBXX',
        ])

        for letter in 'BA':
            game.add_letter(letter)
        self.assertEqual(game.current_word[-1][1], [0, 0])

        game.add_letter('M')

        self.assertEqual(
            [item[1] for item in game.current_word],
            [[1, 1], [0, 2], [0, 3]],
        )

    def test_strands_backtracks_the_entire_word_from_first_letter(self):
        game = self.make_strands([
            'AXAB',
            'XXXX',
            'ABCX',
        ])

        for letter in 'AB':
            game.add_letter(letter)
        self.assertEqual(
            [item[1] for item in game.current_word],
            [[0, 2], [0, 3]],
        )

        game.add_letter('C')

        self.assertEqual(
            [item[1] for item in game.current_word],
            [[2, 0], [2, 1], [2, 2]],
        )

    def test_strands_keeps_selection_when_no_path_matches(self):
        game = self.make_strands(['ABC'])
        for letter in 'AB':
            game.add_letter(letter)
        original = list(game.current_word)

        game.add_letter('Z')

        self.assertEqual(game.current_word, original)

    def test_letter_boxed_carries_last_letter_into_next_word(self):
        game = object.__new__(LetterBoxed)
        game.current_word = 'BADGE'
        game.valid_words = ['BADGE']
        game.words = []
        game.done = False
        game.letter_data = {letter: {} for letter in 'ABCDEFGHIJKL'}
        game.sides = ['ABC', 'DEF', 'GHI', 'JKL']

        game.enter()

        self.assertEqual(game.words, ['BADGE'])
        self.assertEqual(game.current_word, 'E')

    def test_wordle_rejects_a_broken_cached_dictionary(self):
        self.assertFalse(Wordle.is_valid_word_list(
            Wordle.parse_word_list('404: NOT FOUND')
        ))

    def test_wordle_keyboard_fades_absent_letters(self):
        game = object.__new__(Wordle)
        game.colors = MagicMock()
        game.colors.get_color_id.return_value = 64
        game.found_letters = []
        game.close_letters = []
        game.guessed_letters = ['X']

        self.assertEqual(game.get_keyboard_mod('X'), curses.A_DIM)
        self.assertEqual(game.get_keyboard_mod('Q'), curses.A_BOLD)

    def test_wordle_colored_keys_use_bold_white_text(self):
        game = object.__new__(Wordle)
        game.colors = MagicMock()
        game.colors.get_color_id.return_value = 64
        game.found_letters = ['G']
        game.close_letters = ['Y']
        game.guessed_letters = []

        game.get_keyboard_mod('G')
        game.colors.get_color_id.assert_called_with('Green', 'White')
        game.get_keyboard_mod('Y')
        game.colors.get_color_id.assert_called_with('Yellow', 'White')
        self.assertEqual(game.get_keyboard_mod('G'), 64 | curses.A_BOLD)
        self.assertEqual(game.get_keyboard_mod('Y'), 64 | curses.A_BOLD)

    @patch.object(curses, 'use_default_colors')
    @patch.object(curses, 'color_pair', return_value=128)
    @patch.object(curses, 'init_pair')
    def test_wordle_uses_default_foreground_when_supported(
        self, init_pair, color_pair, use_default_colors
    ):
        game = object.__new__(Wordle)
        game.colors = MagicMock()
        game.colors.get_color_id.return_value = 64

        with patch.object(curses, 'COLORS', 256, create=True), patch.object(
            curses, 'COLOR_PAIRS', 256, create=True
        ):
            mod = game.get_bold_white_mod('Green')

        use_default_colors.assert_called_once_with()
        init_pair.assert_called_once_with(65, -1, curses.COLOR_GREEN)
        color_pair.assert_called_once_with(65)
        self.assertEqual(mod, 128 | curses.A_BOLD)

    def test_wordle_colored_cells_use_bold_white_text(self):
        game = object.__new__(Wordle)
        game.colors = MagicMock()
        game.colors.get_color_id.side_effect = lambda background, foreground: {
            'Green': 64,
            'Yellow': 128,
        }[background]
        game.solution = 'AECXY'
        game.word_size = 5
        game.found_letters = []
        game.close_letters = []
        game.guessed_letters = []

        mods = game.get_colors('ABCDE')

        self.assertEqual(mods[0], 64 | curses.A_BOLD)
        self.assertEqual(mods[4], 128 | curses.A_BOLD)
        self.assertIn(call('Green', 'White'), game.colors.get_color_id.call_args_list)
        self.assertIn(call('Yellow', 'White'), game.colors.get_color_id.call_args_list)

    def test_wordle_submits_with_all_common_enter_codes(self):
        for enter_code in (10, 13, 343):
            game = object.__new__(Wordle)
            game.done = False
            game.current_word = 'CRANE'
            game.solution = 'OTHER'
            game.valid_words = {'CRANE', 'OTHER'}
            game.words = []
            game.num_attempts = 6
            game.message = ''
            game.refresh = lambda *args, **kwargs: None
            game.stdscr = None

            game.accept_char(enter_code)

            self.assertEqual(game.words, ['CRANE'])
            self.assertEqual(game.current_word, '')

    @patch('nyt_games_cli.nyt_data.get_json')
    def test_mini_loader_uses_public_auth_bypass_header(self, get_json):
        get_json.return_value = {
            'body': [{
                'clueLists': [],
                'clues': [],
                'cells': [{}],
            }]
        }

        from nyt_games_cli.nyt_data import load_mini_data

        load_mini_data()
        self.assertEqual(
            get_json.call_args.kwargs['headers'],
            {'X-Games-Auth-Bypass': 'true'},
        )

    def test_mini_api_data_is_accepted_by_game(self):
        api_data = {
            'body': [{
                'clueLists': [
                    {'name': 'Across', 'clues': [0]},
                    {'name': 'Down', 'clues': [1]},
                ],
                'clues': [
                    {'label': '1', 'text': [{'plain': 'Across clue'}]},
                    {'label': '1', 'text': [{'plain': 'Down clue'}]},
                ],
                'cells': [
                    {'answer': 'A', 'label': '1'},
                    {},
                    {'answer': 'B'},
                    {'answer': 'C'},
                ],
            }]
        }
        parsed = parse_mini_data(api_data)
        game = object.__new__(Mini)
        game.current_position = [0, 0]
        game.is_down = False
        game.update_data(parsed)

        self.assertEqual(game.box_size, 2)
        self.assertEqual(game.clues['Across']['1'], 'Across clue')
        self.assertEqual(game.grid_data[0][1]['letter'], None)

    def test_every_game_accepts_its_live_data_shape(self):
        wordle = object.__new__(Wordle)
        wordle.valid_words = set()
        wordle.update_data('crane')
        self.assertEqual(wordle.solution, 'CRANE')

        letter_boxed = object.__new__(LetterBoxed)
        letter_boxed.update_data({
            'sides': ['ABC', 'DEF', 'GHI', 'JKL'],
            'dictionary': ['BADGE'],
            'par': 4,
        })
        self.assertEqual(letter_boxed.par, 4)

        strands = object.__new__(Strands)
        strands.update_data({'startingBoard': ['ABCDEF'] * 8})
        self.assertEqual(len(strands.get_board_data()), 8)

        spelling_bee = object.__new__(SpellingBee)
        spelling_bee.update_data({
            'centerLetter': 'a',
            'outerLetters': list('bcdefg'),
            'answers': ['cafe'],
        })
        self.assertEqual(spelling_bee.valid_words, ['CAFE'])

        connections = object.__new__(Connections)
        connections.colors = FakeColors()
        categories = []
        for category_index in range(4):
            categories.append({
                'title': f'Category {category_index}',
                'cards': [
                    {'content': f'WORD{position}', 'position': position}
                    for position in range(category_index * 4, category_index * 4 + 4)
                ],
            })
        connections.update_data({'categories': categories})
        self.assertEqual(len(connections.all_cards), 16)
        self.assertEqual(len(connections.solutions), 4)


if __name__ == '__main__':
    unittest.main()
