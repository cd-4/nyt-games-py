import unittest
from unittest.mock import MagicMock, patch

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
