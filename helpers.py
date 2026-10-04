"""Supporting functions for blindfold.py: board rendering, terminal colors/clearing, move parsing."""

import os
import sys
import time
from functools import cache

import chess


def move_list(board):
    """Render the game so far as numbered SAN, e.g. '1. e4 c5 2. Nf3'."""
    return chess.Board().variation_san(board.move_stack) if board.move_stack else "(no moves yet)"


# faint background shades for a dark / light terminal
SHADE_DARK_TERM, SHADE_LIGHT_TERM = 238, 252


@cache
def light_terminal():
    """Guess whether the terminal background is light, from COLORFGBG ('fg;bg'); dark if unknown."""
    try:
        bg = int(os.environ.get("COLORFGBG", "").split(";")[-1])
    except ValueError:
        return False
    return bg in (7, 15)


def piece_style(piece):
    """(glyph, 256-color fg) for a plain-board piece so white and black read right on this theme."""
    if light_terminal():
        # hollow = white, solid = black; both drawn in black ink
        return piece.unicode_symbol(), 16
    # on a dark background hollow glyphs are dark inside, so they stand for black
    if piece.color == chess.WHITE:
        return chess.UNICODE_PIECE_SYMBOLS[piece.symbol().lower()], 231
    return chess.UNICODE_PIECE_SYMBOLS[piece.symbol().upper()], 245


def is_shaded(square):
    """Unshaded squares show the terminal background, so shade the squares that should look lighter
    on a dark terminal and the ones that should look darker on a light one."""
    dark = (chess.square_file(square) + chess.square_rank(square)) % 2 == 0
    return dark == light_terminal()


def render_square(piece, square, colors):
    """One piece/dot cell; with colors on, shaded squares get a background behind it."""
    glyph, fg = piece_style(piece) if piece else ("·", None)
    if not colors:
        if not piece:
            return glyph
        if not sys.stdout.isatty():
            return piece.unicode_symbol()
        # explicit foreground only (no backdrop): the glyph shape is the fill, its color the edge
        return f"\033[38;5;{fg}m{glyph}\033[0m"
    shade = f"\033[48;5;{shade_color()}m" if is_shaded(square) else ""
    ink = f"\033[38;5;{fg}m" if fg is not None else ""
    return f"{shade}{ink}{glyph}\033[0m"


@cache
def shade_color():
    return SHADE_LIGHT_TERM if light_terminal() else SHADE_DARK_TERM


def edge(shaded_left, shaded_right):
    """Half-block cell on the line between two squares: shade only the half belonging to the shaded one."""
    if shaded_left == shaded_right:
        return " "
    return f"\033[38;5;{shade_color()}m{'▌' if shaded_left else '▐'}\033[0m"


def render_board(board, orientation, colors=False, coords=False):
    """Render the board with `orientation` at the bottom.

    With colors on, each square is one piece cell plus a shared half-cell edge on either side, so
    the shading is centred on the piece and squares touch while the board stays two cells per file.
    """
    white_bottom = orientation == chess.WHITE
    ranks = range(7, -1, -1) if white_bottom else range(8)
    files = range(8) if white_bottom else range(7, -1, -1)
    lines = []
    for rank in ranks:
        squares = [chess.square(f, rank) for f in files]
        cells = [render_square(board.piece_at(sq), sq, colors) for sq in squares]
        if colors:
            shaded = [is_shaded(sq) for sq in squares]
            row = edge(False, shaded[0])
            for i, cell in enumerate(cells):
                row += cell + edge(shaded[i], shaded[i + 1] if i < 7 else False)
        else:
            row = " ".join(cells)
        lines.append(f"{rank + 1} {row}" if coords else row)
    if coords:
        labels = [chess.FILE_NAMES[f] for f in files]
        lines.append("  " + (" " + " ".join(labels) if colors else " ".join(labels)))
    return "\n".join(lines)


def parse_toggle(current, arg):
    """Resolve '', 'on' or 'off' to the new state; None if the argument is invalid."""
    if arg == "":
        return not current
    return {"on": True, "off": False}.get(arg)


def clear_screen():
    """Wipe the screen and scrollback so earlier moves and boards can't be read."""
    if sys.stdout.isatty():
        print("\033[2J\033[3J\033[H", end="", flush=True)


def linger(seconds):
    """Leave the output on screen for a while, then wipe it."""
    time.sleep(seconds)
    clear_screen()


def parse_move(board, text):
    try:
        return board.parse_san(text)
    except ValueError:
        pass
    try:
        move = chess.Move.from_uci(text.lower())
    except ValueError:
        return None
    return move if move in board.legal_moves else None


def result_message(board, human):
    outcome = board.outcome(claim_draw=True)
    if outcome.winner is None:
        return f"Draw ({outcome.termination.name.lower().replace('_', ' ')})."
    who = "You win" if outcome.winner == human else "Engine wins"
    return f"{who} by {outcome.termination.name.lower()}."
