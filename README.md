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

### Installing Stockfish on Windows

Use a package manager (this puts `stockfish` on your `PATH`):

```powershell
scoop install stockfish
# or
choco install stockfish
# or (if available in your winget catalog; check with `winget search stockfish`)
winget install Stockfish.Stockfish
```

Or install manually:

1. Download the Windows build from https://stockfishchess.org/download/ (pick the AVX2 build on any CPU from the last ~10 years, otherwise the plain x86-64 build).
2. Unzip it somewhere permanent, e.g. `C:\Tools\stockfish\`.
3. Either add that folder to your `PATH` (Settings → System → About → Advanced system settings → Environment Variables → Path), or pass the exe with `--engine`:

```powershell
python blindfold.py --engine C:\Tools\stockfish\stockfish-windows-x86-64-avx2.exe
```

Check it works by running `stockfish` in a new terminal; it should print a banner and wait for input (type `quit` to exit).

On Windows, create the venv with `python -m venv .venv` and run `.venv\Scripts\python blindfold.py` in place of `.venv/bin/python`.

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
