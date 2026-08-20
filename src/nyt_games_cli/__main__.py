import curses

from nyt_games_cli.main import NYTGames


def restore_terminal(game=None):
    """Best-effort restoration, including when initialization only partly ran."""
    operations = []
    if game is not None and getattr(game, 'stdscr', None) is not None:
        operations.append(lambda: game.stdscr.keypad(False))
    operations.extend((curses.echo, curses.nocbreak, curses.nl, curses.endwin))

    for operation in operations:
        try:
            operation()
        except curses.error:
            pass


def main():
    game = None
    try:
        game = NYTGames()
        game.loop()
    except KeyboardInterrupt:
        return 130
    finally:
        restore_terminal(game)


if __name__ == '__main__':
    main()
