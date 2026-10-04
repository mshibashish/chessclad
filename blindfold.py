#!/usr/bin/env python3
"""Blindfold chess against Stockfish: type moves, receive moves. No board."""

import argparse
import random
import shutil
from dataclasses import dataclass

import chess
import chess.engine

from helpers import (
    linger,
    move_list,
    parse_move,
    parse_toggle,
    render_board,
    result_message,
)

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


@dataclass
class Game:
    board: chess.Board
    human: chess.Color
    show_moves: bool
    autoclear: bool
    clear_delay: float
    colors: bool
    coords: bool
    flipped: bool = False

    def linger(self):
        """Wipe the screen after the delay, if autoclear is on."""
        if self.autoclear:
            linger(self.clear_delay)


def cmd_help(g, cmd, arg):
    print(HELP)


def cmd_autoclear(g, cmd, arg):
    try:
        if arg == "":
            g.autoclear = not g.autoclear
        elif arg in ("on", "off"):
            g.autoclear = arg == "on"
        else:
            g.clear_delay = max(0.0, float(arg))
            g.autoclear = True
    except ValueError:
        print("Usage: autoclear [on|off|SECONDS]")
        return
    print(f"Autoclear {f'on ({g.clear_delay:g}s)' if g.autoclear else 'off'}.")


def cmd_moves(g, cmd, arg):
    print(move_list(g.board))
    g.linger()


def cmd_show(g, cmd, arg):
    g.show_moves = True
    print("Move list shown.")


def cmd_hide(g, cmd, arg):
    g.show_moves = False
    print("Move list hidden.")


def cmd_board(g, cmd, arg):
    if cmd == "flip":
        g.flipped = not g.flipped
    # the player's color sits at the bottom unless flipped; "board flip" flips just this peek
    bottom = g.human != (g.flipped != (cmd == "board flip"))
    print(render_board(g.board, bottom, g.colors, g.coords))
    g.linger()


def cmd_toggle(g, cmd, arg):
    name = cmd.split()[0]
    new = parse_toggle(getattr(g, name), arg)
    if new is None:
        print(f"Usage: {name} [on|off]")
        return
    setattr(g, name, new)
    print(f"Board {name} {'on' if new else 'off'}.")


def cmd_undo(g, cmd, arg):
    if len(g.board.move_stack) < 2:
        print("Nothing to undo.")
    else:
        g.board.pop()
        g.board.pop()
        print(f"Took back. {move_list(g.board) if g.show_moves else ''}".rstrip())
        if g.show_moves:
            g.linger()


def cmd_resign(g, cmd, arg):
    print("You resigned.")
    return True  # ends the game


# whole-line commands, then commands that take an argument after the first word;
# a handler returns True to end the game
COMMANDS = {
    "help": cmd_help,
    "moves": cmd_moves,
    "show": cmd_show,
    "hide": cmd_hide,
    "board": cmd_board,
    "board flip": cmd_board,
    "flip": cmd_board,
    "undo": cmd_undo,
    "resign": cmd_resign,
}
ARG_COMMANDS = {
    "autoclear": cmd_autoclear,
    "colors": cmd_toggle,
    "coords": cmd_toggle,
}


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
    autoclear = args.autoclear is not None
    g = Game(
        board=chess.Board(),
        human=chess.WHITE if color == "white" else chess.BLACK,
        show_moves=args.show_moves,
        autoclear=autoclear,
        clear_delay=args.autoclear if autoclear else DEFAULT_CLEAR_DELAY,
        colors=args.colors,
        coords=args.coords,
    )
    board = g.board

    engine = chess.engine.SimpleEngine.popen_uci(args.engine)
    engine.configure({"Skill Level": max(0, min(20, args.level))})
    print(f"You play {color}. Level {args.level}. Type 'help' for commands.")

    try:
        while not board.is_game_over(claim_draw=True):
            if board.turn != g.human:
                move = engine.play(board, chess.engine.Limit(time=args.think)).move
                san = board.san(move)
                board.push(move)
                number = board.fullmove_number - (1 if board.turn == chess.WHITE else 0)
                print(f"engine: {number}.{'..' if g.human == chess.WHITE else ''} {san}")
                if g.show_moves:
                    print(move_list(board))
                if g.autoclear and not board.is_game_over(claim_draw=True):
                    linger(g.clear_delay)
                continue

            text = input("you: ").strip()
            cmd = text.lower()
            if not text:
                continue
            elif cmd in ("quit", "exit"):
                return

            handler = COMMANDS.get(cmd) or ARG_COMMANDS.get(cmd.split()[0])
            if handler:
                if handler(g, cmd, cmd.partition(" ")[2].strip()):
                    break
                continue
            move = parse_move(board, text)
            if move is None:
                print("Illegal or unrecognised move.")
                continue
            board.push(move)
        else:
            print(result_message(board, g.human))

        print(f"\nFinal moves: {move_list(board)}")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        engine.quit()


if __name__ == "__main__":
    main()
