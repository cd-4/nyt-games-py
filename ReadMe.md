# NYT Games CLI

## 📢 Do you want to play the NYT daily games at work?

## 📢 Do you not want to be seen on your phone at your desk?

Play the New York Times daily word games from an interactive command-line
interface. The application downloads the current puzzles when it starts and
uses number keys to switch between games.

## Available games

| Key | Game |
| --- | --- |
| `1` | Wordle |
| `2` | Connections |
| `3` | Strands |
| `4` | Mini Crossword |
| `5` | Letter Boxed |
| `6` | Spelling Bee |

Each game displays its controls at the bottom of the terminal.

## Installation

Install the latest release from PyPI:

```console
python -m pip install nyt-games-cli
```

It is recommended to install command-line applications in an isolated
environment with `pipx`:

```console
pipx install nyt-games-cli
```

To install a local checkout for development:

```console
git clone https://github.com/cd-4/nyt-games-py.git
cd nyt-games-py
python -m pip install -e .
```

## Running

Launch the installed command:

```console
nyt-games-cli
```

Alternatively, run the Python module directly:

```console
python -m nyt_games_cli
```

The application must run in an interactive terminal and requires an internet
connection to download the daily puzzle data. Press `Ctrl-C` to exit.

## Disclaimer

This is an unofficial command-line client and is not affiliated with or
endorsed by The New York Times Company.
