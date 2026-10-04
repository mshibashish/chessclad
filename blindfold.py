#!/usr/bin/env python3
"""Blindfold chess against Stockfish: type moves, receive moves. No board."""

import argparse
import os
import random
import shutil
import sys
import time

import chess
import chess.engine

DEFAULT_CLEAR_DELAY = 3.0

HELP = """Commands:
  <move>      a move in SAN (Nf3, exd5, O-O, e8=Q) or UCI (g1f3)
  moves       print the move list once
  show        show the move list after every move
  hide        stop showing the move list after every move
  board       peek at the board (board flip: peek from the other side)
  flip        toggle which side is at the bottom when peeking
  colors      toggle colored squares on the board (colors on / off)
  coords      toggle file/rank coordinates on the board (coords on / off)
  autoclear   toggle wiping the screen a few seconds after the engine moves
              (autoclear on / off, or autoclear <seconds> to set the delay)
  undo        take back your last move (and the engine's reply)
  resign      resign the game
  help        show this help
  quit        exit"""


def move_list(board):
    """Render the game so far as numbered SAN, e.g. '1. e4 c5 2. Nf3'."""
    return chess.Board().variation_san(board.move_stack) if board.move_stack else "(no moves yet)"


# faint background shades for a dark / light terminal
SHADE_DARK_TERM, SHADE_LIGHT_TERM = 238, 252


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--color", choices=["white", "black", "random"], default="random")
    parser.add_argument("--level", type=int, default=5, help="Stockfish skill level 0-20 (default 5)")
    parser.add_argument("--think", type=float, default=0.5, help="engine seconds per move (default 0.5)")
    parser.add_argument("--show-moves", action="store_true", help="start with the move list shown")
    parser.add_argument("--autoclear", nargs="?", const=DEFAULT_CLEAR_DELAY, type=float, metavar="SECONDS",
                        help="wipe the screen SECONDS after each engine move or board/move-list peek "
                             f"(default {DEFAULT_CLEAR_DELAY:g}s when given without a value)")
    parser.add_argument("--colors", action="store_true", help="draw the board with colored squares")
    parser.add_argument("--coords", action="store_true", help="draw file/rank coordinates around the board")
    parser.add_argument("--engine", default=shutil.which("stockfish"), help="path to a UCI engine")
    args = parser.parse_args()

    if not args.engine:
        parser.error("Stockfish not found; install it (brew install stockfish) or pass --engine")

    color = random.choice(["white", "black"]) if args.color == "random" else args.color
    human = chess.WHITE if color == "white" else chess.BLACK
    show_moves = args.show_moves
    autoclear = args.autoclear is not None
    clear_delay = args.autoclear if autoclear else DEFAULT_CLEAR_DELAY
    colors = args.colors
    coords = args.coords
    flipped = False
    board = chess.Board()

    engine = chess.engine.SimpleEngine.popen_uci(args.engine)
    engine.configure({"Skill Level": max(0, min(20, args.level))})
    print(f"You play {color}. Level {args.level}. Type 'help' for commands.")

    try:
        while not board.is_game_over(claim_draw=True):
            if board.turn != human:
                move = engine.play(board, chess.engine.Limit(time=args.think)).move
                san = board.san(move)
                board.push(move)
                number = board.fullmove_number - (1 if board.turn == chess.WHITE else 0)
                print(f"engine: {number}.{'..' if human == chess.WHITE else ''} {san}")
                if show_moves:
                    print(move_list(board))
                if autoclear and not board.is_game_over(claim_draw=True):
                    linger(clear_delay)
                continue

            text = input("you: ").strip()
            cmd = text.lower()
            if not text:
                continue
            elif cmd in ("quit", "exit"):
                return

            if cmd == "help":
                print(HELP)
            elif cmd.split()[0] == "autoclear":
                arg = cmd.partition(" ")[2].strip()
                try:
                    if arg == "":
                        autoclear = not autoclear
                    elif arg in ("on", "off"):
                        autoclear = arg == "on"
                    else:
                        clear_delay = max(0.0, float(arg))
                        autoclear = True
                except ValueError:
                    print("Usage: autoclear [on|off|SECONDS]")
                    continue
                print(f"Autoclear {f'on ({clear_delay:g}s)' if autoclear else 'off'}.")
            elif cmd == "moves":
                print(move_list(board))
                if autoclear:
                    linger(clear_delay)
            elif cmd == "show":
                show_moves = True
                print("Move list shown.")
            elif cmd == "hide":
                show_moves = False
                print("Move list hidden.")
            elif cmd in ("board", "board flip", "flip"):
                if cmd == "flip":
                    flipped = not flipped
                # the player's color sits at the bottom unless flipped; "board flip" flips just this peek
                bottom = human != (flipped != (cmd == "board flip"))
                print(render_board(board, bottom, colors, coords))
                if autoclear:
                    linger(clear_delay)
            elif cmd.split()[0] in ("colors", "coords"):
                name = cmd.split()[0]
                new = parse_toggle(colors if name == "colors" else coords, cmd.partition(" ")[2].strip())
                if new is None:
                    print(f"Usage: {name} [on|off]")
                    continue
                if name == "colors":
                    colors = new
                else:
                    coords = new
                print(f"Board {name} {'on' if new else 'off'}.")
            elif cmd == "undo":
                if len(board.move_stack) < 2:
                    print("Nothing to undo.")
                else:
                    board.pop()
                    board.pop()
                    print(f"Took back. {move_list(board) if show_moves else ''}".rstrip())
                    if autoclear and show_moves:
                        linger(clear_delay)
            elif cmd == "resign":
                print("You resigned.")
                break
            else:
                move = parse_move(board, text)
                if move is None:
                    print("Illegal or unrecognised move.")
                    continue
                board.push(move)
        else:
            print(result_message(board, human))

        print(f"\nFinal moves: {move_list(board)}")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        engine.quit()


if __name__ == "__main__":
    main()
