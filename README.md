# chessclad

Blindfold chess in the terminal. You type a move, the engine types one back. No board is drawn unless you ask to peek.

```
You play white. Level 5. Type 'help' for commands.
you: e4
engine: 1... c5
you: Nf3
engine: 2... d6
```

## Setup

Requires Python 3 and [Stockfish](https://stockfishchess.org/).

```bash
brew install stockfish
python3 -m venv .venv
.venv/bin/pip install chess
```

## Play

```bash
.venv/bin/python blindfold.py
```

### Options

| Option | Default                    | Description |
| --- |----------------------------| --- |
| `--color white\|black\|random` | `random`                   | Which side you play |
| `--level 0-20` | `5`                        | Stockfish skill level |
| `--think SECONDS` | `0.5`                      | Engine thinking time per move |
| `--show-moves` | off                        | Start with the move list shown after every move |
| `--autoclear [SECONDS]` | off (3s if no value given) | Wipe the screen (and scrollback) SECONDS after each engine move, board peek or move-list peek, taking your own move with it |
| `--colors` | off                        | Draw the board with colored squares |
| `--coords` | off                        | Draw file/rank coordinates around the board |
| `--engine PATH` | `stockfish` on your PATH   | Use a different UCI engine |

Example:

```bash
.venv/bin/python blindfold.py --color black --level 2
```

### Entering moves

Use SAN (`Nf3`, `exd5`, `O-O`, `e8=Q`) or UCI (`g1f3`, `e7e8q`). Illegal or unrecognised moves are rejected and you can try again.

### Commands

| Command | What it does |
| --- | --- |
| `moves` | Print the move list once |
| `show` | Print the move list after every engine move |
| `hide` | Stop printing the move list (the default) |
| `board` | Peek at the board (your color at the bottom) |
| `board flip` | Peek once from the other side |
| `flip` | Toggle which side is at the bottom for this and later peeks |
| `colors [on\|off]` | Toggle colored squares (no argument flips it) |
| `coords [on\|off]` | Toggle file/rank coordinates (no argument flips it) |
| `autoclear [on\|off\|SECONDS]` | Toggle auto-clearing, or set the delay in seconds (no argument flips it) |
| `undo` | Take back your last move and the engine's reply |
| `resign` | Resign the game |
| `help` | List commands |
| `quit` | Exit |

When the game ends, the full move list is printed.
