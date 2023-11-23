#!/usr/bin/python3
# Set the path to your python3 above

"""
Go0 random Go player
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller
"""
from gtp_connection import GtpConnection
from board_base import DEFAULT_SIZE, GO_POINT, GO_COLOR, EMPTY
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine
import board_base
import random
import numpy as np

def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def play_move(board, move, color):
    board.play_move(move, color)

def game_result(board):
    winner = board.detect_five_in_a_row()
    moves = board.get_empty_points()
    board_full = (len(moves) == 0)
    if winner!=EMPTY:
    # return 1 if winner is board.current_player else -1
        return winner
    if board_full:
        return 'draw'
    return None

class NinukiSimulationPlayer(object):
    """
    For each move do `n_simualtions_per_move` playouts,
    then select the one with best win-rate.
    playout could be either random or rule_based (i.e., uses pre-defined patterns) 
    """
    def __init__(self, n_simualtions_per_move=10, playout_policy='random', board_size=7):
        assert(playout_policy in ['random', 'rule_based'])
        self.n_simualtions_per_move=n_simualtions_per_move
        self.board_size=board_size
        self.playout_policy=playout_policy

        #NOTE: pattern has preference, later pattern is ignored if an earlier pattern is found
        self.pattern_list=['Win', 'BlockWin', 'OpenFour', 'Capture', 'Random']

        self.name="Ninuki.py"
        self.version = 1.0
        self.best_move=None
    
    def set_playout_policy(self, playout_policy='random'):
        assert(playout_policy in ['random', 'rule_based'])
        self.playout_policy=playout_policy

    def _random_moves(self, board, color_to_play):
        return GoBoardUtil.generate_legal_moves(board,color_to_play)
    
    def policy_moves(self, board, color_to_play):
        if(self.playout_policy=='random'):
            return "Random", self._random_moves(board, color_to_play)
        else:
            assert(self.playout_policy=='rule_based')
            assert(isinstance(board, GoBoard))
            ret=board.get_pattern_moves()
            if ret is None:
                return "Random", self._random_moves(board, color_to_play)
            movetype_id, moves=ret
            return self.pattern_list[movetype_id], moves
    
    def _do_playout(self, board, color_to_play):
        res=game_result(board)
        simulation_moves=[]
        while(res is None):
            _ , candidate_moves = self.policy_moves(board, board.current_player)
            playout_move=random.choice(candidate_moves)
            play_move(board, playout_move, board.current_player)
            simulation_moves.append(playout_move)
            res=game_result(board)
        for m in simulation_moves[::-1]:
            undo(board, m)
        if res == color_to_play:
            return 1.0
        elif res == 'draw':
            return 0.0
        else:
            assert(res == board_base.opponent(color_to_play))
            return -1.0

    def get_move(self, board, color_to_play):
        """
        The genmove function called by gtp_connection
        """
        moves=GoBoardUtil.generate_random_moves(board)
        toplay=board.current_player

        best_result, best_move=-1.1, None
        best_move=moves[0]

        wins = np.zeros(len(moves))
        visits = np.zeros(len(moves))

        for i, move in enumerate(moves):
            play_move(board, move, toplay)
            res=game_result(board)
            if res == toplay:
                undo(board, move)
                    #This move is a immediate win
                self.best_move=move
                return move
            ret=self._do_playout(board, toplay)
            wins[i] += ret
            visits[i] += 1
            undo(board, move)
            win_rate = wins[i] / visits[i]
            if win_rate > best_result:
                best_result=win_rate
                best_move=move
                self.best_move=best_move
        return best_move if best_move is not None else 'pass'    


def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board: GoBoard = GoBoard(DEFAULT_SIZE)
    con: GtpConnection = GtpConnection(NinukiSimulationPlayer(), board)
    con.start_connection()


if __name__ == "__main__":
    run()
