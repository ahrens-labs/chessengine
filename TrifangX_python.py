import random
import sys
import time
import threading
from collections import defaultdict
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from multiprocessing import Pool
game_moves = []
app = Flask(__name__)
CORS(app)
@app.route('/move', methods=['POST'])
def get_move():
    data = request.get_json()
    move_notation = data.get('move')
    color = data.get('color', 'white')
    print(f"received: move = {move_notation}, color = {color}")
    if move_notation:
        if len(clean_move(move_notation)) == 4 and move_notation != '0-0-0':
            move_notation = convert_to_long_algebraic(move_notation, board, color[0])
            print('MN:', move_notation)
    return_move = None

    try:
        if color == 'white':
            if move_notation:
                if move_notation in {'0-0', 'O-O'}:
                    print('Castling: 0-0')
                    players_turn_white(board, '0-0')
                elif move_notation in {'0-0-0', 'O-O-O'}:
                    print('Castling: 0-0-0')
                    players_turn_white(board, '0-0-0')
                else:
                    next_move = move_notation.strip()
                    print('Player move (white):', next_move)
                    players_turn_white(board, next_move)
            return_move = best_move_black(board, 'false', 'false')
            if len(clean_move(return_move)) == 5:
                return_move = convert_long_move(return_move)
        else:
            if move_notation:
                if move_notation in {'0-0', 'O-O'}:
                    print('Castling: 0-0')
                    players_turn(board, '0-0')
                elif move_notation in {'0-0-0', 'O-O-O'}:
                    print('Castling: 0-0-0')
                    players_turn(board, '0-0-0')
                else:
                    next_move = move_notation.strip()
                    print('Player move (black):', next_move)
                    players_turn(board, next_move)
            return_move = best_move_function(board, 'false', 'false')
            if len(clean_move(return_move)) == 5 and return_move[0] != '0':
                return_move = convert_long_move(return_move)

        if return_move == '0-0':
            return jsonify({'move': 'O-O'})
        elif return_move == '0-0-0':
            return jsonify({'move': 'O-O-O'})

        if not return_move:
            print("Engine returned no move.")
            return jsonify({'error': 'Engine failed to generate move'}), 500

        print("Engine move:", return_move)
        return jsonify({'move': return_move})

    except Exception as e:
        print(f"ERROR in /move: {e}")
        return jsonify({'error': f'Exception: {str(e)}'}), 500


draws = 0
fifty_move_rule = 0
wins = 0
castled = False
castled_white = False
dragon = True
middlegame = False
opening = False
endgame = False
bots = False
fake_castled_black = False
edge_up_black_king = False
edge_down_black_king = False
edge_left_black_king = False
edge_right_black_king = False
edge_up_white_king = False
edge_down_white_king = False
edge_left_white_king = False
edge_right_white_king = False
number_of_moves = 0
king_move = 0
king_move_white = 0
position_history = defaultdict(int)

stop_event = threading.Event()
timer_thread = None

def start_timer():
    global timer_thread
    stop_event.clear()
    timer_thread = threading.Thread(target=countup_timer)
    timer_thread.start()

def stop_timer():
    if timer_thread and timer_thread.is_alive():
        stop_event.set()
        timer_thread.join()

def countup_timer():
    start_time = time.time()

    while not stop_event.is_set():
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        centiseconds = int((elapsed % 1) * 1000000000)
        timer = f'{mins:02d}:{secs:02d}.{centiseconds:02d}'
        time.sleep(0.000000001)


def score(board, turn):
    global castled
    global castled_white
    white_king_row, white_king_col = find_king(board, 'w')
    black_king_row, black_king_col = find_king(board, 'b')
    score = 0
    pieces = 0
    knight_squares = 0
    bishop_squares = 0
    queen_squares = 0
    rook_squares = 0
    bad_knight_squares = 0
    bad_bishop_squares = 0
    bad_queen_squares = 0
    bad_rook_squares = 0
    developement = False
    pawn_take_queen = False
    rook_placed = False
    rook_placed_row = False
    rook_placed_col = False
    fake_castled = False
    fake_castled_white = False
    passed_straight = False
    passed_left = False
    passed_right = False
    backwards_left = False
    backwards_right = False
    rook_open_file = False
    rook_open_file_black = False
    rook_7th_rank = False
    rook_7th_rank_black = False
    black_light_squared_bishop = False
    black_dark_squared_bishop = False
    white_light_squared_bishop = False
    white_dark_squared_bishop = False
    white_pieces = 0
    black_pieces = 0
    black_pawns = 0
    white_pawns = 0
    black_bishops = 0
    white_bishops = 0
    black_knights = 0
    white_knights = 0
    black_rooks = 0
    white_rooks = 0
    black_queens = 0
    white_queens = 0
    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
        if is_checkmate(board, 'b'):
            score = -1000
            return score
    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
        if is_checkmate(board, 'w'):
            score = 1000
            return score
    piece_values = {
        'p': 4, 'P': -4,
        'n': 12, 'N': -12,
        'b': 12, 'B': -12,
        'r': 20, 'R': -20,
        'q': 36, 'Q': -36,
        'k': 1000, 'K': -1000
    }

    for row in range(8):
        for col in range(8):
            if board[row][col] == 'k':
                if row == 0:
                    edge_up_black_king == True
                else:
                    edge_up_black_king == False
                if row == 7:
                    edge_down_black_king == True
                else:
                    edge_down_black_king == False
                if col == 0:
                    edge_left_black_king == True
                else:
                    edge_left_black_king == False
                if col == 7:
                    edge_right_black_king == True
                else:
                    edge_right_black_king == False
                if (row, col) == (7, 6)  and board[7][5] == 'r':
                    fake_castled = True
                if (row, col) == (7, 2)  and board[7][3] == 'r':
                    fake_castled = True
                if castled or fake_castled:
                    score += 1
            elif board[row][col] == 'K':
                if row == 0:
                    edge_up_white_king == True
                else:
                    edge_up_white_king == False
                if row == 7:
                    edge_down_white_king == True
                else:
                    edge_down_white_king == False
                if col == 0:
                    edge_left_white_king == True
                else:
                    edge_left_white_king == False
                if col == 7:
                    edge_right_white_king == True
                else:
                    edge_right_white_king == False
                if (row, col) == (0, 6)  and board[0][5] == 'r':
                    fake_castled_white = True
                if (row, col) == (0, 2)  and board[0][3] == 'r':
                    fake_castled_white = True
                if castled_white or fake_castled_white:
                    score -= 1
            if board[row][col] != '0':
                pieces += 1
            if board[row][col] in {'p', 'n', 'b', 'r', 'q', 'k'}:
                black_pieces += 1
            elif board[row][col] in {'P', 'N', 'B', 'R', 'Q', 'K'}:
                white_pieces += 1
            if board[row][col] == 'p':
                black_pawns += 1
            elif board[row][col] == 'P':
                white_pawns += 1
            elif board[row][col] == 'b':
                black_bishops += 1
                if is_light_square(row, col):
                    black_light_squared_bishop = True
                else:
                    black_dark_squared_bishop = True
            elif board[row][col] == 'B':
                white_bishops += 1
                if is_light_square(row, col):
                    white_light_squared_bishop = True
                else:
                    white_dark_squared_bishop = True
            elif board[row][col] == 'n':
                black_knights += 1
            elif board[row][col] == 'N':
                white_knights += 1
            elif board[row][col] == 'r':
                black_rooks += 1
            elif board[row][col] == 'r':
                black_rooks += 1
            elif board[row][col] == 'q':
                black_queens += 1
            elif board[row][col] == 'Q':
                white_queens += 1
            if (row, col) == (7, 7):
                if board[7][1] == '0' and board[7][2] == '0' and board[7][5] == '0' and board[7][6] == '0' and board[0][1] == '0' and board[0][2] == '0' and board[0][5] == '0' and board[0][6] == '0':
                    developement = True
                if pieces < 15:
                    endgame = True
                    opening = False
                    middlegame = False
                elif developement:
                    if castled or fake_castled or king_move == 1:
                        opening = False
                        middlegame = True
                        endgame = False
                    else:
                        middlegame = False
                        opening = True
                        endgame = False
                else:
                    middlegame = False
                    opening = True
                    endgame = False

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece in piece_values:
                score += piece_values[piece]
            if piece == 'p':
                if black_light_squared_bishop:
                    if not is_light_square(row, col):
                        score += 0.4
                if black_dark_squared_bishop:
                    if is_light_square(row, col):
                        score += 0.4
                if white_light_squared_bishop:
                    if not is_light_square(row, col):
                        score += 0.4
                if white_dark_squared_bishop:
                    if is_light_square(row, col):
                        score += 0.4
                if 0 <= col-1:
                    for number in range(1, 8):
                        if row-number >= 0:
                            if board[row-number][col-1] == 'P':
                                break
                            if row-number == 0:
                                passed_left = True
                else:
                    passed_left = True
                if 7 >= col+1:
                    if passed_left:
                        for number in range(1, 8):
                            if row-number >= 0:
                                if board[row-number][col+1] == 'P':
                                    break
                                if row-number == 0:
                                    passed_right = True
                else:
                    passed_right = True
                if passed_left and passed_right:
                    for number in range(1, 8):
                        if row-number >= 0:
                            if board[row-number][col] == 'P':
                                break
                            if row-number == 0:
                                passed_straight = True
                if passed_left and passed_right and passed_straight:
                    score += 0.7
                    score += (7-row)/12
                passed_left = False
                passed_right = False
                if 0 <= col-1:
                    for number in range(7):
                        if row+number <= 7:
                            if board[row+number][col-1] == 'p':
                                break
                            if row+number == 7:
                                backwards_left = True
                else:
                    backwards_left = True
                if 7 >= col+1:
                    if backwards_left:
                        for number in range(7):
                            if row+number <= 7:
                                if board[row+number][col+1] == 'p':
                                    break
                                if row+number == 7:
                                    backwards_right = True
                else:
                    backwards_right = True
                if backwards_left and backwards_right:
                    score -= 0.3
                    if board[row-1][col] == 'P':
                        score -= 0.6
                    if passed_straight:
                        score -= 0.9
                passed_straight = False
                backwards_left = False
                backwards_right = False
                for number in range(1, 8):
                    if row-number >= 0:
                        if board[row-number][col] == 'p':
                            score -= 0.6
                            break
                if (row, col) == (4, 3):
                    if board[4][4] == 'p':
                        score += 1
                if (row, col) in [(5, 2), (4, 2), (5, 5), (4, 5), (5, 3), (5, 4)]:
                    score += 0.6
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score += 0.8
                    if opening:
                        score += 0.8
                if (row, col) == (4, 4):
                    score += 0.3
                if not endgame:
                    if col < 7:
                        if board[row+1][col+1] == 'p':
                            score += 0.2
                        if board[row-1][col+1] == 'p':
                            score += 0.2
                    if col > 0:
                        if board[row-1][col-1] == 'p':
                            score += 0.2
                        if board[row+1][col-1] == 'p':
                            score += 0.2
                    if black_king_row == 7 and black_king_col not in {4, 5}:
                      if (row, col) in {(black_king_row-1, black_king_col), (black_king_row-1, black_king_col+1), (black_king_row-1, black_king_col-1)}:
                        score += 0.4
                    if col in {2, 3, 4, 5}:
                        score += (7-row)/20
                    else:
                        score += (7-row)/30
                    if board[7][5] == 'k' or board[7][6] == 'k' or board[7][7] == 'k':
                        if col in {5, 6, 7}:
                            score -= (7-row)/15
                    if col+1 <= 7:
                        if board[row-1][col+1] in {'N', 'B', 'R', 'Q', 'K'}:
                            score += 0.5
                    if col-1 >= 0:
                        if board[row-1][col-1] in {'N', 'B', 'R', 'Q', 'K'}:
                            score += 0.5

                else:
                    score += (7-row)**2/20
                    if 0 <= col-1:
                        for number in range(1, 8):
                            if row-number >= 0:
                                if board[row-number][col-1] == 'P':
                                    break
                                if row-number == 0:
                                    passed_left = True
                    else:
                        passed_left = True
                    if 7 >= col+1:
                        if passed_left:
                            for number in range(1, 8):
                                if row-number >= 0:
                                    if board[row-number][col+1] == 'P':
                                        break
                                    if row-number == 0:
                                        passed_right = True
                    else:
                        passed_right = True
                    if passed_left and passed_right:
                        for number in range(1, 8):
                            if row-number >= 0:
                                if board[row-number][col] == 'P':
                                    break
                                if row-number == 0:
                                    passed_straight = True
                    if passed_left and passed_right and passed_straight:
                        score += 0.7
                        score += (7-row)**2/35
                    passed_straight = False
                    passed_left = False
                    passed_right = False

            elif piece == 'P':
                if white_light_squared_bishop:
                    if not is_light_square(row, col):
                        score -= 0.4
                if white_dark_squared_bishop:
                    if is_light_square(row, col):
                        score -= 0.4
                if black_light_squared_bishop:
                    if not is_light_square(row, col):
                        score -= 0.4
                if black_dark_squared_bishop:
                    if is_light_square(row, col):
                        score -= 0.4
                if 0 <= col-1:
                        for number in range(1, 8):
                            if row+number <= 7:
                                if board[row+number][col-1] == 'p':
                                    break
                                if row+number == 7:
                                    passed_left = True
                else:
                    passed_left = True
                if 7 >= col+1:
                    if passed_left:
                        for number in range(1, 8):
                            if row+number <= 7:
                                if board[row+number][col+1] == 'p':
                                    break
                                if row+number == 7:
                                    passed_right = True
                else:
                    passed_right = True
                if passed_left and passed_right:
                    for number in range(1, 8):
                        if row+number <= 7:
                            if board[row+number][col] == 'p':
                                break
                            if row+number == 7:
                                passed_straight = True
                if passed_left and passed_right and passed_straight:
                    score -= 0.7
                    score -= row/12
                passed_left = False
                passed_right = False
                if 0 <= col-1:
                    for number in range(7):
                        if row-number >= 0:
                            if board[row-number][col-1] == 'P':
                                break
                            if row-number == 0:
                                backwards_left = True
                else:
                    backwards_left = True
                if 7 >= col+1:
                    if backwards_left:
                        for number in range(7):
                            if row-number >= 0:
                                if board[row-number][col+1] == 'P':
                                    break
                                if row-number == 0:
                                    backwards_right = True
                else:
                    backwards_right = True
                if backwards_left and backwards_right:
                    score += 0.3
                    if board[row+1][col] == 'p':
                        score += 0.6
                    if passed_straight:
                        score += 0.9
                backwards_left = False
                backwards_right = False
                passed_straight = False
                for number in range(1, 8):
                    if row+number <= 7:
                        if board[row+number][col] == 'P':
                            score += 0.6
                            break
                if (row, col) == (3, 3):
                    if board[3][4] == 'P':
                        score -= 1
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score -= 0.8
                    if opening:
                        score -= 0.8
                if (row, col) in [(2, 2), (3, 2), (2, 5), (3, 5), (2, 3), (2, 4)]:
                    score -= 0.6
                if not endgame:
                    if col < 7:
                      if board[row+1][col+1] == 'P':
                          score -= 0.2
                      if board[row-1][col+1] == 'P':
                          score -= 0.2
                    if col > 0:
                      if board[row+1][col-1] == 'P':
                          score -= 0.2
                      if board[row-1][col-1] == 'P':
                          score -= 0.2
                    if white_king_row == 0 and black_king_col not in {4, 5}:
                      if (row, col) in {(white_king_row+1, white_king_col), (white_king_row+1, white_king_col+1), (white_king_row+1, white_king_col-1)}:
                        score -= 0.4
                    if col in {2, 3, 4, 5}:
                        score -= row/20
                    else:
                        score -= row/30
                    if board[0][5] == 'K' or board[0][6] == 'K' or board[0][7] == 'K':
                            score -= row/15
                    if col+1 <= 7:
                        if board[row+1][col+1] in {'n', 'b', 'r', 'q', 'k'}:
                            score -= 0.5
                    if col-1 >= 0:
                        if board[row+1][col-1] in {'n', 'b', 'r', 'q', 'k'}:
                            score -= 0.5
                else:
                    score -= row**2/20
                    if 0 <= col-1:
                        for number in range(1, 8):
                            if row+number <= 7:
                                if board[row+number][col-1] == 'p':
                                    break
                                if row+number == 7:
                                    passed_left = True
                    else:
                        passed_left = True
                    if 7 >= col+1:
                        if passed_left:
                            for number in range(1, 8):
                                if row+number <= 7:
                                    if board[row+number][col+1] == 'p':
                                        break
                                    if row+number == 7:
                                        passed_right = True
                    else:
                        passed_right = True
                    if passed_left and passed_right:
                        for number in range(1, 8):
                            if row+number <= 7:
                                if board[row+number][col] == 'p':
                                    break
                                if row+number == 7:
                                    passed_straight = True
                    if passed_left and passed_right and passed_straight:
                        score -= 0.8
                        score -= row**2/35
                    passed_straight = False
                    passed_left = False
                    passed_right = False

            elif piece == 'b':
                if black_bishops == 2:
                    score += 0.5
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score += 0.3
                if not endgame:
                    if is_protected_pawn(board, row, col, 'p'):
                        score += 0.4
                    if (row, col) == (3, 6):
                        if board[2][5] == 'N' and board[0][3] == 'Q':
                            score += 0.7
                            if board[1][4] == 'B':
                              score -= 0.3
                    if not is_pinned_to_king(board, row, col, 'b'):
                        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                        for direction in directions:
                            for i in range(1, 8):
                                new_row = row + i * direction[0]
                                new_col = col + i * direction[1]
                                if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    bishop_squares += 1
                                    if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        break
                                else:
                                    break
                        score += bishop_squares/13
                if opening:
                    if (row, col) == (7, 2) or (row, col) == (7, 5):
                        score -= 1.3

            elif piece == 'B':
                if white_bishops == 2:
                    score -= 0.5
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score -= 0.3
                if not endgame:
                    if is_protected_pawn(board, row, col, 'P'):
                        score -= 0.4
                    if (row, col) == (4, 6):
                        if board[5][5] == 'n' and board[7][3] == 'q':
                            score -= 0.7
                            if board[6][4] == 'b':
                              score += 0.3
                    if not is_pinned_to_king(board, row, col, 'w'):
                        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                        for direction in directions:
                            for i in range(1, 8):
                                new_row = row + i * direction[0]
                                new_col = col + i * direction[1]
                                if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    bad_bishop_squares += 1
                                    if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        break
                                else:
                                    break
                        score -= bad_bishop_squares/13
                if opening:
                    if (row, col) == (0, 2) or (row, col) == (0, 5):
                        score += 1.3
            elif piece == 'n':
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score += 0.6
                elif (col) == 0 or (col) == 7:
                    score -= 0.2
                if (row) == 0 or (row) == 7:
                    score -= 0.2
                elif row in [5, 4, 3, 2]:
                    score += 0.2
                    if row in [3, 2]:
                        score += 0.3
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        threatened_piece = board[new_row][new_col]
                        if threatened_piece in {'P', 'N', 'B', 'R'}:
                            score += 0.3
                        if threatened_piece in {'Q', 'K'}:
                            score += 0.5
                if not endgame:
                    if is_protected_pawn(board, row, col, 'p'):
                        score += 0.4
                    if (row, col) == (5, 5) and board[4][4] == 'p':
                        score += 0.5
                    if not is_pinned_to_king(board, row, col, 'b'):
                        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                        for direction in directions:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                knight_squares += 1
                        score += knight_squares/8
                if opening:
                    if (row, col) == (7, 1) or (row, col) == (7, 6):
                        score -= 0.3
                    if (row, col) == (5, 5) and board[4][5] == 'p':
                        score += 0.5

            elif piece == 'N':
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score -= 0.6
                elif (col) == 0 or (col) == 7:
                    score += 0.2
                if (row) == 0 or (row) == 7:
                    score += 0.2
                elif row in [5, 4, 3, 2]:
                    score -= 0.2
                    if row in [4, 5]:
                        score -= 0.3
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        threatened_piece = board[new_row][new_col]
                        if threatened_piece in {'p', 'n', 'b', 'r'}:
                            score -= 0.3
                        if threatened_piece in {'q', 'k'}:
                            score -= 0.5
                if not endgame:
                    if (row, col) == (2, 2) and board[3][4] == 'P':
                        score -= 0.5
                    if is_protected_pawn(board, row, col, 'P'):
                        score -= 0.4
                    if not is_pinned_to_king(board, row, col, 'w'):
                        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                        for direction in directions:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                bad_knight_squares += 1
                        score -= bad_knight_squares/8
                if opening:
                    if (row, col) == (0, 1) or (row, col) == (0, 6):
                        score += 0.3
                    if (row, col) == (2, 5) and board[3][5] == 'P':
                        score -= 0.5

            elif piece == 'r':
                if board[0][6] == 'K':
                    if col in [5, 6, 7] and row == 5:
                        score += 0.6
                if open_file(board, col, 'b'):
                    score += 0.5
                    if open_file(board, col, 'w'):
                      score += 0.5
                      if rook_open_file:
                          score += 0.6
                      rook_open_file = True
                if not endgame:
                    if row == 1:
                        score += 0.5
                        if rook_7th_rank:
                            score += 0.8
                        rook_7th_rank = True
                    if not is_pinned_to_king(board, row, col, 'b'):
                        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                        for direction in directions:
                            for i in range(1, 8):
                                new_row = row + i * direction[0]
                                new_col = col + i * direction[1]
                                if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    rook_squares += 1
                                    if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        break
                                else:
                                    break
                        score += rook_squares/14
                if endgame:
                    if white_pieces == 1:
                        if black_rooks == 2:
                            if row + 1 == white_king_row or row -1 == white_king_row and not rook_placed_row and not rook_placed_col:
                              score += 3
                              rook_placed_row = True
                            if col + 1 == white_king_col or col - 1 == white_king_col and not rook_placed_row and not rook_placed_col:
                                score += 3
                                rook_placed_col = True
                            elif rook_placed_row:
                                if row == white_king_row:
                                    score += 3
                            elif rook_placed_col:
                                if col == white_king_col:
                                    score += 3

            elif piece == 'R':
                if board[7][6] == 'k':
                    if col in [5, 6, 7] and row == 2:
                        score -= 0.6
                if open_file(board, col, 'w'):
                    score -= 0.5
                    if open_file(board, col, 'b'):
                      score -= 0.5
                      if rook_open_file_black:
                          score -= 0.6
                      rook_open_file_black = True
                if not endgame:
                    if row == 6:
                        score -= 0.5
                        if rook_7th_rank_black:
                            score -= 0.8
                        rook_7th_rank_black = True
                    if not is_pinned_to_king(board, row, col, 'w'):
                        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                        for direction in directions:
                            for i in range(1, 8):
                                new_row = row + i * direction[0]
                                new_col = col + i * direction[1]
                                if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    bad_rook_squares += 1
                                    if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        break
                                else:
                                    break
                        score -= bad_rook_squares/14
                else:
                    if black_pieces == 1:
                        if white_rooks == 2:
                            if row + 1 == black_king_row or row -1 == black_king_row and not rook_placed_row_white and not rook_placed_col_white:
                              score -= 3
                              rook_placed_row_white = True
                            if col + 1 == black_king_col or col - 1 == black_king_col and not rook_placed_row_white and not rook_placed_col_white:
                                score -= 3
                                rook_placed_col_white = True
                            elif rook_placed_row_white:
                                if row == black_king_row:
                                    score -= 3
                            elif rook_placed_col_white:
                                if col == black_king_col:
                                    score -= 3
            elif piece == 'q':
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score += 0.4
                if board[0][6] == 'K':
                    if col in [5, 6, 7]:
                        score += 0.7
                if not endgame:
                    if open_file(board, col, 'b'):
                      score += 0.3
                    if open_file(board, col, 'w'):
                      score += 0.3
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                queen_squares += 1
                                if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                    break
                            else:
                                break
                    score += queen_squares/27
                else:
                    if black_pieces == 2 and white_pieces == 1:
                        if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            score -= 10
                        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                        for direction in directions:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] == 'K':
                                    score += 1.3
                if opening:
                    if (row, col) in [(6, 4), (6, 2), (6, 3), (7, 3)]:
                      score += 0.6
                    if (row, col) == (7, 3):
                      score += 1
            elif piece == 'Q':
                if (row, col) in [(4, 3), (4, 4), (3, 3), (3, 4)]:
                    score -= 0.4
                if board[7][6] == 'k':
                    if col in [5, 6, 7]:
                        score += 0.7
                if not endgame:
                    if open_file(board, col, 'w'):
                      score -= 0.3
                    if open_file(board, col, 'b'):
                      score -= 0.3
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                bad_queen_squares += 1
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break
                    score -= bad_queen_squares/27
                else:
                    if white_pieces == 2 and black_pieces == 1:
                        if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            score += 10
                        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                        for direction in directions:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] == 'k':
                                    score -= 1.3
                        directions = [(1, 3), (1, -3), (-1, 3), (-1, -3), (3, 1), (3, -1), (-3, 1), (-3, -1)]
                        for direction in directions:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if (new_row, new_col) in {(7, 7), (7, 0), (0, 0), (0, 7)}:
                                    if board[new_row][new_col] == 'k':
                                        score -= 1
                                        corner_queen_score = corner_queen_mate(board, new_row, new_col, 'w')
                                        score += corner_queen_score
                                    elif (row, col) == (7, 0):
                                        if board[6][0] == 'k' or board[7][1] == 'k':
                                            score -= 1
                                            corner_queen_score = corner_queen_mate(board, new_row, new_col, 'w')
                                            score += corner_queen_score
                                    elif (row, col) == (7, 7):
                                        if board[6][7] == 'k' or board[7][6] == 'k':
                                            score -= 1
                                            corner_queen_score = corner_queen_mate(board, new_row, new_col, 'w')
                                            score += corner_queen_score
                                    elif (row, col) == (0, 0):
                                        if board[0][1] == 'k' or board[1][0] == 'k':
                                            score -= 1
                                            corner_queen_score = corner_queen_mate(board, new_row, new_col, 'w')
                                            score += corner_queen_score
                                    elif (row, col) == (0, 7):
                                        if board[0][6] == 'k' or board[1][7] == 'k':
                                            score -= 1
                                            corner_queen_score = corner_queen_mate(board, new_row, new_col, 'w')
                                            score += corner_queen_score


                if opening:
                    if (row, col) in [(1, 4), (1, 2), (1, 3), (0, 3)]:
                        score -= 0.6
                    if (row, col) == [(0, 3)]:
                        score -= 1
            elif piece == 'k':
                if endgame:
                    if black_pieces == 1:
                        distance = abs(row - 3.5) + abs(col - 3.5)
                        score += 7-distance
                    if row in {7, 0} or col in {7, 0}:
                        score -= 0.5
                    if black_bishops + black_knights + black_rooks + black_queens == 0:
                        distance = abs(row - 3.5) + abs(col - 3.5)
                        score += (7-distance)/2
                        score += row/10
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] == 'P':
                                if not is_protected(board, new_row, new_col, 'b'):
                                    score += 1
                    if edge_up_white_king:
                        if board[row-2][col] == 'K':
                            score -= 1.5
                        score -= (7-row)/15
                    if edge_down_white_king:
                        if board[row+2][col] == 'K':
                            score -= 1.5
                        score -= row/15
                    if edge_right_white_king:
                        if board[row][col+2] == 'K':
                            score -= 1.5
                        score -= col/15
                    if edge_left_white_king:
                        if board[row][col-2] == 'K':
                            score -= 1.5
                        score -= (7-col)/15
                if board[7][4] != 'k' and not fake_castled and not castled:
                    score -= 1
            elif piece == 'K':
                if endgame:
                    if white_pieces == 1:
                        distance = abs(row - 3.5) + abs(col - 3.5)
                        score -= 7-distance
                    if row in {7, 0} or col in {7, 0}:
                        score += 0.5
                    if white_bishops + white_knights + white_rooks + white_queens == 0:
                        distance = abs(row - 3.5) + abs(col - 3.5)
                        score -= (7-distance)/2
                        score -= row/10
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] == 'p':
                                if not is_protected(board, new_row, new_col, 'w'):
                                    score -= 1
                    if edge_up_black_king:
                        if board[row-2][col] == 'k':
                            score -= 1.5
                        score -= (7-row)/15
                    if edge_down_black_king:
                        if board[row+2][col] == 'k':
                            score -= 1.5
                        score -= row/15
                    if edge_right_black_king:
                        if board[row][col+2] == 'k':
                            score -= 1.5
                        score -= col/15
                    if edge_left_black_king:
                        if board[row][col-2] == 'k':
                            score -= 1.5
                        score -= (7-col)/15
                if board[0][4] != 'K' and not fake_castled_white and not castled_white:
                    score += 1

            VALUES_white = {
                'n': -12, 'b': -12, 'r': -20, 'q': -36, 'p': -4,
            }

            VALUES_black = {
                'N': 12, 'B': 12, 'R': 20, 'Q': 36, 'P': 4
            }

            if (piece in VALUES_white and turn == 'w') or (piece in VALUES_black and turn == 'b'):
                  protected_color = 'w' if piece.isupper() else 'b'
                  threatened_color = 'b' if piece.isupper() else 'w'
                  threatened_by_enemy = is_protected(board, row, col, threatened_color)
                  if threatened_by_enemy:
                      not_protected_by_ally = is_protected(board, row, col, protected_color)
                      if not not_protected_by_ally:
                          if piece.isupper():
                              score += VALUES_black[piece]
                          else:
                              score += VALUES_white[piece]

            if turn == 'b' and piece in {'N', 'B', 'R', 'Q'}:
                directions = [(1, 1), (1, -1)]
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if piece == 'Q' and board[new_row][new_col] == 'p':
                            if is_protected(board, row, col, 'w'):
                                score += 34
                        elif piece == 'R' and board[new_row][new_col] == 'p':
                            if is_protected(board, row, col, 'w'):
                                score += 18
                        elif piece in {'N', 'B'} and board[new_row][new_col] == 'p':
                            if is_protected(board, row, col, 'w'):
                                score += 10

            if turn == 'w' and piece in {'n', 'b', 'r', 'q'}:
                directions = [(-1, 1), (-1, -1)]
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if piece == 'q' and board[new_row][new_col] == 'P' and pawn_take_queen == False and is_protected(board, row, col, 'b'):
                            score -= 34
                            pawn_take_queen = True
                        elif piece == 'r' and board[new_row][new_col] == 'P':
                            if is_protected(board, row, col, 'b'):
                                score -= 18
                        elif piece in {'n', 'b'} and board[new_row][new_col] == 'P':
                            if is_protected(board, row, col, 'b'):
                                score -= 10

            if turn == 'b' and piece in {'R', 'Q'}:
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if piece == 'Q' and board[new_row][new_col] == 'n':
                            if is_protected(board, row, col, 'w'):
                                score += 30
                        elif piece == 'R' and board[new_row][new_col] == 'n':
                            if is_protected(board, row, col, 'w'):
                                score += 13
            if turn == 'w' and piece in {'r', 'q'}:
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if piece == 'q' and board[new_row][new_col] == 'N':
                            if is_protected(board, row, col, 'b'):
                                score -= 30
                        elif piece == 'r' and board[new_row][new_col] == 'N':
                            if is_protected(board, row, col, 'b'):
                                score -= 13
            if turn == 'w' and piece in {'r', 'q'}:
                  directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                  for direction in directions:
                      for i in range(1, 8):
                          new_row = row + i * direction[0]
                          new_col = col + i * direction[1]
                          if 0 <= new_row < 8 and 0 <= new_col < 8:
                              if piece == 'q' and board[new_row][new_col] == 'B':
                                  if is_protected(board, row, col, 'b'):
                                      score -= 30
                              elif piece == 'r' and board[new_row][new_col] == 'B':
                                  if is_protected(board, row, col, 'b'):
                                      score -= 13
                              if board[new_row][new_col] != '0':
                                  break
                          else:
                              break
            if turn == 'b' and piece in {'R', 'Q'}:
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if piece == 'Q' and board[new_row][new_col] == 'b':
                                if is_protected(board, row, col, 'w'):
                                    score += 30
                            elif piece == 'R' and board[new_row][new_col] == 'b':
                                if is_protected(board, row, col, 'w'):
                                    score += 13
                            if board[new_row][new_col] != '0':
                                break
                        else:
                            break
            if turn == 'w' and piece == 'q':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] == 'R':
                                    if is_protected(board, row, col, 'b'):
                                        score -= 18
                                if board[new_row][new_col] != '0':
                                    break
                            else:
                                break
            if turn == 'b' and piece == 'Q':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] == 'r':
                                if is_protected(board, row, col, 'w'):
                                    score += 18
                            if board[new_row][new_col] != '0':
                                break
                        else:
                            break
    return score/4

def is_light_square(row, col):
    return (row + col) % 2 == 0

def pos_to_indices(pos):
    col = ord(pos[0]) - ord('a')
    row = 8 - int(pos[1])
    return row, col

def pos_to_indices_col(pos):
    col = ord(pos[0]) - ord('a')
    return col

def indices_to_pos(row, col):
    col_pos = chr(col + ord('a'))
    row_pos = str(8 - row)
    return col_pos + row_pos

def indices_to_pos_col(col):
    col_pos = chr(col + ord('a'))
    return col_pos

def indices_to_pos_row(row):
    row_pos = str(8 - row)
    return row_pos

def find_king(board, king_color):
    king_symbol = 'K' if king_color == 'w' else 'k'
    for row in range(8):
        for col in range(8):
            if board[row][col] == king_symbol:
                return row, col
    print('here')
    print_board(board)
    return None
def check_defenders_lower(board, row, col):
    defenders = 0
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for direction in directions:
        for i in range(1, 8):
            new_row = row + i * direction[0]
            new_col = col + i * direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] in {'r', 'q'}:
                    if not is_pinned_to_king(board, new_row, new_col, 'b'):
                      defenders += 1
                if board[new_row][new_col] not in ['0', 'r', 'q', 'R', 'Q']:
                    break
            else:
                break

    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for direction in directions:
        for i in range(1, 8):
            new_row = row + i * direction[0]
            new_col = col + i * direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] in {'b', 'q'}:
                    if not is_pinned_to_king(board, new_row, new_col, 'b'):
                      defenders += 1
                if board[new_row][new_col] not in ['0', 'b', 'q', 'B', 'Q']:
                    break
            else:
                break

    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
    for direction in directions:
        new_row = row + direction[0]
        new_col = col + direction[1]
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row][new_col] == 'n':
                if not is_pinned_to_king(board, new_row, new_col, 'b'):
                  defenders += 1

    pawn_attacks = [(1, 1), (1, -1)]
    for attack in pawn_attacks:
        new_row = row + attack[0]
        new_col = col + attack[1]
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row][new_col] == 'p':
                defenders += 1
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for direction in directions:
        new_row = row + direction[0]
        new_col = col + direction[1]
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row][new_col] == 'k':
                defenders += 1

    return defenders
def check_defenders_upper(board, row, col):
    defenders = 0
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for direction in directions:
        for i in range(1, 8):
            new_row = row + i * direction[0]
            new_col = col + i * direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] in {'R', 'Q'}:
                    if not is_pinned_to_king(board, new_row, new_col, 'w'):
                      defenders += 1
                if board[new_row][new_col] not in ['0', 'r', 'q', 'R', 'Q']:
                    break
            else:
                break

    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for direction in directions:
        for i in range(1, 8):
            new_row = row + i * direction[0]
            new_col = col + i * direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] in {'B', 'Q'}:
                    if not is_pinned_to_king(board, new_row, new_col, 'w'):
                      defenders += 1
                if board[new_row][new_col] not in ['0', 'b', 'q', 'B', 'Q']:
                    break
            else:
                break

    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
    for direction in directions:
        new_row = row + direction[0]
        new_col = col + direction[1]
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row][new_col] == 'N':
                if not is_pinned_to_king(board, new_row, new_col, 'w'):
                    defenders += 1

    pawn_attacks = [(-1, 1), (-1, -1)]
    for attack in pawn_attacks:
        new_row = row + attack[0]
        new_col = col + attack[1]
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row][new_col] == 'P':
                defenders += 1
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for direction in directions:
        new_row = row + direction[0]
        new_col = col + direction[1]
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row][new_col] == 'K':
                defenders += 1
    return defenders
def open_file(board, col, turn):
    if turn == 'w':
        for row in range(8):
            if board[row][col] == 'P':
                return False
    elif turn == 'b':
        for row in range(8):
            if board[row][col] == 'p':
                return False
    return True

def convert_long_move(move):
    if move[2] == move[4]:
        return (move[:2] + move[3:])
    elif move[1] == move[3]:
        return (move[:1] + move[2:])
    else:
        return (move[:2] + move[3:])
def convert_to_long_algebraic(move, board, color):
    print('converting')
    piece_letter = move[0]
    disambig_file = move[1]
    target_square = move[2:]

    target_row, target_col = pos_to_indices(target_square)

    direction = -1 if color == 'w' else 1
    candidate_piece = piece_letter.lower() if color == 'w' else piece_letter.upper()
    print('CP:', candidate_piece, 'C:', color)
    if disambig_file in {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'}:
        for row in range(8):
            col = ord(disambig_file) - ord('a')
            if board[row][col] == candidate_piece:
                from_square = indices_to_pos(row, col)
                return piece_letter + from_square + target_square
    else:
        for col in range(8):
            print('number')
            row = 7 - (int(disambig_file) - 1)
            if board[row][col] == candidate_piece:
                from_square = indices_to_pos(row, col)
                return piece_letter + from_square + target_square

    return None




def print_piece_move(board, best_piece, best_row, best_col, target_row, target_col, piece, color):
    if color == 'b':
        if best_piece == 'p' and target_row == 0:
            if piece in {'P', 'N', 'B', 'R', 'Q'}:
                move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '=Q'
            else:
                move_played = indices_to_pos(target_row, target_col) + '=Q'
        else:
            if is_protected_piece(board, target_row, target_col, best_piece):
                if piece in {'P', 'N', 'B', 'R', 'Q'}:
                  move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + 'x' + indices_to_pos(target_row, target_col)
                else:
                  move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + indices_to_pos(target_row, target_col)
            else:
                if best_piece != 'p':
                      if piece in {'P', 'N', 'B', 'R', 'Q'}:
                        move_played = best_piece.upper() + 'x' + indices_to_pos(target_row, target_col)
                      else:
                        move_played = best_piece.upper() + indices_to_pos(target_row, target_col)
                else:
                      if piece in {'P', 'N', 'B', 'R', 'Q'}:
                        move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                      else:
                        move_played = indices_to_pos(target_row, target_col)
    elif color == 'w':
        if best_piece == 'P' and target_row == 7:
            if piece in {'p', 'n', 'b', 'r', 'q'}:
                move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '=Q'
            else:
                move_played = indices_to_pos(target_row, target_col) + '=Q'
        else:
            if is_protected_piece(board, target_row, target_col, best_piece):
                if piece in {'p', 'n', 'b', 'r', 'q'}:
                  move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + 'x' + indices_to_pos(target_row, target_col)
                else:
                  move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + indices_to_pos(target_row, target_col)
            else:
                if best_piece != 'P':
                      if piece in {'p', 'n', 'b', 'r', 'q'}:
                        move_played = best_piece.upper() + 'x' + indices_to_pos(target_row, target_col)
                      else:
                        move_played = best_piece.upper() + indices_to_pos(target_row, target_col)
                else:
                      if piece in {'p', 'n', 'b', 'r', 'q'}:
                        move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                      else:
                        move_played = indices_to_pos(target_row, target_col)
    return move_played

def print_moves(last_move, number_of_moves, game_moves):
    opening_moves = ""
    move_number = 0
    if last_move == 'b':
        for number in range(len(game_moves) // 2):
            if move_number < len(game_moves):
                opening_moves += str(number + 1) + '. ' + game_moves[move_number] + ' '
                move_number += 1
                if move_number < len(game_moves):
                    opening_moves += game_moves[move_number] + ' '
                    move_number += 1
            else:
                break
    else:
        for number in range(len(game_moves) // 2 + 1):
            if number == len(game_moves) // 2:
                opening_moves += str(number + 1) + '. ' + game_moves[move_number] + ' '
                break
            if move_number < len(game_moves):
                opening_moves += str(number + 1) + '. ' + game_moves[move_number] + ' '
                move_number += 1
                if move_number < len(game_moves):
                    opening_moves += game_moves[move_number] + ' '
                    move_number += 1
            else:
                break
    return opening_moves.strip()



def is_checkmate(board, player):
    white_king_row, white_king_col = find_king(board, 'w')
    black_king_row, black_king_col = find_king(board, 'b')
    rows = list(range(8))
    cols = list(range(8))

    for row in rows:
        for col in cols:
            piece = board[row][col]
            if player == 'b':
                if piece == 'p':
                    directions = [1, 2, 3, 4]
                    random.shuffle(directions)
                    for direction in directions:
                        if direction == 1 and row == 6 and board[row-2][col] == '0' and board[row-1][col] == '0':
                            board[row][col] = '0'
                            board[row-2][col] = 'p'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                board[row][col] = 'p'
                                board[row-2][col] = '0'
                                return False
                            board[row][col] = 'p'
                            board[row-2][col] = '0'

                        elif direction == 2 and row < 7 and board[row-1][col] == '0':
                            board[row][col] = '0'
                            board[row-1][col] = 'p'
                            if row-1 == 0:
                                board[row-1][col] = 'q'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                board[row][col] = 'p'
                                board[row-1][col] = '0'
                                return False
                            board[row][col] = 'p'
                            board[row-1][col] = '0'

                        elif direction == 3 and row < 7 and col > 0 and board[row-1][col-1] in {'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[row-1][col-1]
                            board[row][col] = '0'
                            board[row-1][col-1] = 'p'
                            if row-1 == 0:
                                board[row-1][col-1] = 'q'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                board[row][col] = 'p'
                                board[row-1][col-1] = captured_piece
                                return False
                            board[row][col] = 'p'
                            board[row-1][col-1] = captured_piece

                        elif direction == 4 and row > 0 and col < 7 and board[row-1][col+1] in {'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[row-1][col+1]
                            board[row][col] = '0'
                            board[row-1][col+1] = 'p'
                            if row-1 == 0:
                                board[row-1][col+1] = 'q'
                                promotion = True
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                board[row][col] = 'p'
                                board[row-1][col+1] = captured_piece
                                return False
                            board[row][col] = 'p'
                            board[row-1][col+1] = captured_piece

                elif piece == 'n':
                    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'n'
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    board[row][col] = 'n'
                                    board[new_row][new_col] = captured_piece
                                    return False
                                board[row][col] = 'n'
                                board[new_row][new_col] = captured_piece

                elif piece == 'b':
                    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'b'
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        board[row][col] = 'b'
                                        board[new_row][new_col] = captured_piece
                                        return False
                                    board[row][col] = 'b'
                                    board[new_row][new_col] = captured_piece
                                else:
                                    break
                                if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                    break
                            else:
                                break

                elif piece == 'r':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'r'
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        board[row][col] = 'r'
                                        board[new_row][new_col] = captured_piece
                                        return False
                                    board[row][col] = 'r'
                                    board[new_row][new_col] = captured_piece
                                else:
                                    break
                                if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                    break
                            else:
                                break

                elif piece == 'q':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'q'
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        board[row][col] = 'q'
                                        board[new_row][new_col] = captured_piece
                                        return False
                                    board[row][col] = 'q'
                                    board[new_row][new_col] = captured_piece
                                else:
                                    break
                                if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                    break
                            else:
                                break

                elif piece == 'k':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'k'
                                black_king_row, black_king_col = find_king(board, 'b')
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    board[row][col] = 'k'
                                    board[new_row][new_col] = captured_piece
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    return False
                                board[row][col] = 'k'
                                board[new_row][new_col] = captured_piece
                                black_king_row, black_king_col = find_king(board, 'b')
            else:
                if piece == 'P':
                    directions = [1, 2, 3, 4]
                    random.shuffle(directions)
                    for direction in directions:
                        if direction == 1 and row == 1 and board[row+2][col] == '0' and board[row+1][col] == '0':
                            board[row][col] = '0'
                            board[row+2][col] = 'P'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                board[row][col] = 'P'
                                board[row+2][col] = '0'
                                return False
                            board[row][col] = 'P'
                            board[row+2][col] = '0'

                        elif direction == 2 and row < 7 and board[row+1][col] == '0':
                            board[row][col] = '0'
                            board[row+1][col] = 'P'
                            if row+1 == 7:
                                board[row+1][col] = 'Q'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                board[row][col] = 'P'
                                board[row+1][col] = '0'
                                return False
                            board[row][col] = 'P'
                            board[row+1][col] = '0'

                        elif direction == 3 and row < 7 and col > 0 and board[row+1][col-1] in {'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[row+1][col-1]
                            board[row][col] = '0'
                            board[row+1][col-1] = 'P'
                            if row+1 == 7:
                                board[row+1][col-1] = 'Q'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                board[row][col] = 'P'
                                board[row+1][col-1] = captured_piece
                                return False
                            board[row][col] = 'P'
                            board[row+1][col-1] = captured_piece

                        elif direction == 4 and row < 7 and col < 7 and board[row+1][col+1] in {'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[row+1][col+1]
                            board[row][col] = '0'
                            board[row+1][col+1] = 'P'
                            if row+1 == 7:
                                board[row+1][col+1] = 'Q'
                                promotion = True
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                board[row][col] = 'P'
                                board[row+1][col+1] = captured_piece
                                return False
                            board[row][col] = 'P'
                            board[row+1][col+1] = captured_piece

                elif piece == 'N':
                    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'N'
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    board[row][col] = 'N'
                                    board[new_row][new_col] = captured_piece
                                    return False
                                board[row][col] = 'N'
                                board[new_row][new_col] = captured_piece

                elif piece == 'B':
                    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'B'
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        board[row][col] = 'B'
                                        board[new_row][new_col] = captured_piece
                                        return False
                                    board[row][col] = 'B'
                                    board[new_row][new_col] = captured_piece
                                else:
                                    break
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break

                elif piece == 'R':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'R'
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        board[row][col] = 'R'
                                        board[new_row][new_col] = captured_piece
                                        return False
                                    board[row][col] = 'R'
                                    board[new_row][new_col] = captured_piece
                                else:
                                    break
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break

                elif piece == 'Q':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'Q'
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        board[row][col] = 'Q'
                                        board[new_row][new_col] = captured_piece
                                        return False
                                    board[row][col] = 'Q'
                                    board[new_row][new_col] = captured_piece
                                else:
                                    break
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break

                elif piece == 'K':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'K'
                                white_king_row, white_king_col = find_king(board, 'w')
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    board[row][col] = 'K'
                                    board[new_row][new_col] = captured_piece
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    return False
                                board[row][col] = 'K'
                                board[new_row][new_col] = captured_piece
                                white_king_row, white_king_col = find_king(board, 'w')

    return True


def is_king_in_check(board, king_row, king_col, player):
    opponent = 'b' if player == 'w' else 'w'

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != '0' and                 ((piece.islower() and player == 'w') or (piece.isupper() and player == 'b')):

                if piece.lower() == 'b' or piece.lower() == 'q':
                    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if new_row == king_row and new_col == king_col:
                                    return True
                                if board[new_row][new_col] != '0':
                                    break
                            else:
                                break

                if piece.lower() == 'r' or piece.lower() == 'q':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if new_row == king_row and new_col == king_col:
                                    return True
                                if board[new_row][new_col] != '0':
                                    break
                            else:
                                break

                elif piece.lower() == 'n':
                    knight_moves = [(1, 2), (1, -2), (-1, 2), (-1, -2),
                                    (2, 1), (2, -1), (-2, 1), (-2, -1)]
                    for move in knight_moves:
                        new_row = row + move[0]
                        new_col = col + move[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if new_row == king_row and new_col == king_col:
                                return True

                elif piece.lower() == 'p':
                    if player == 'b':
                        pawn_attacks = [(1, 1), (1, -1)]
                    else:
                        pawn_attacks = [(-1, 1), (-1, -1)]

                    for attack in pawn_attacks:
                        new_row = row + attack[0]
                        new_col = col + attack[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if new_row == king_row and new_col == king_col:
                                return True
                elif piece.lower() == 'k':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    for move in directions:
                        new_row = row + move[0]
                        new_col = col + move[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if new_row == king_row and new_col == king_col:
                                return True

    return False

def is_pinned_to_king(board, row, col, player):
    threat = False
    king = False
    piece = board[row][col]
    opponent = 'b' if player == 'w' else 'w'
    if player == 'b':
        if piece in {'b', 'n'}:
            directions = [(1, 0), (-1, 0)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'R', 'Q'}:
                            threat = True
                        if board[new_row][new_col] == 'k':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break

            threat = False
            king = False
            directions = [(0, 1), (0, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'R', 'Q'}:
                            threat = True
                        if board[new_row][new_col] == 'k':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        if piece in {'n', 'r'}:
            threat = False
            king = False
            directions = [(1, 1), (-1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'B', 'Q'}:
                            threat = True
                        if board[new_row][new_col] == 'k':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break

            threat = False
            king = False
            directions = [(-1, 1), (1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'B', 'Q'}:
                            threat = True
                        if board[new_row][new_col] == 'k':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break

    elif player == 'w':
        if piece in {'B', 'N'}:
            threat = False
            king = False
            directions = [(0, 1), (0, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'r', 'q'}:
                            threat = True
                        if board[new_row][new_col] == 'K':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break

            threat = False
            king = False
            directions = [(1, 0), (-1, 0)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'r', 'q'}:
                            threat = True
                        if board[new_row][new_col] == 'K':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        if piece in {'N', 'R'}:
            threat = False
            king = False
            directions = [(1, 1), (-1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'b', 'q'}:
                            threat = True
                        if board[new_row][new_col] == 'K':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break

            threat = False
            king = False
            directions = [(-1, 1), (1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'b', 'q'}:
                            threat = True
                        if board[new_row][new_col] == 'K':
                            king = True
                        if threat and king:
                          return True
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break

    return False

def is_protected(board, row, col, player):
    opponent = 'b' if player == 'w' else 'w'
    if player == 'b':
        defenders = check_defenders_lower(board, row, col)
        attackers = check_defenders_upper(board, row, col)
        if defenders >= attackers:
            return True
        else:
            return False

    elif player == 'w':
        defenders = check_defenders_upper(board, row, col)
        attackers = check_defenders_lower(board, row, col)
        if defenders >= attackers:
            return True
        else:
            return False


def is_draw(board):
    pieces = 0
    black_pieces = 0
    white_pieces = 0
    black_knights = 0
    white_knights = 0
    black_bishops = 0
    white_bishops = 0
    for row in range(8):
        for col in range(8):
            if board[row][col] != '0':
                pieces += 1
            if board[row][col] in {'p', 'n', 'b', 'r', 'q', 'k'}:
                black_pieces += 1
            elif board[row][col] in {'P', 'N', 'B', 'R', 'Q', 'K'}:
                white_pieces += 1
            elif board[row][col] == 'b':
                black_bishops += 1
            elif board[row][col] == 'B':
                white_bishops += 1
            elif board[row][col] == 'n':
                black_knights += 1
            elif board[row][col] == 'N':
                white_knights += 1
    if pieces == 2:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 3 and white_knights == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 3 and black_knights == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 4 and black_knights == 1 and white_knights == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 4 and black_bishops == 1 and white_bishops == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 4 and black_bishops == 1 and white_knights == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 4 and black_knights == 1 and white_bishops == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 3 and black_bishops == 1:
        print('Draw by insuffiecient material')
        sys.exit()
    if pieces == 3 and white_bishops == 1:
        print('Draw by insuffiecient material')
        sys.exit()

def is_protected_piece(board, row, col, piece):
    if piece in {'r', 'q', 'R', 'Q'}:
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for direction in directions:
            for i in range(1, 8):
                new_row = row + i * direction[0]
                new_col = col + i * direction[1]
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board[new_row][new_col] == piece:
                        return True
                    if board[new_row][new_col] != '0':
                        break
                else:
                    break
    if piece in {'b', 'q', 'B', 'Q'}:
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for direction in directions:
            for i in range(1, 8):
                new_row = row + i * direction[0]
                new_col = col + i * direction[1]
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board[new_row][new_col] == piece:
                        return True
                    if board[new_row][new_col] != '0':
                        break
                else:
                    break
    elif piece in {'n', 'N'}:
        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
        for direction in directions:
            new_row = row + direction[0]
            new_col = col + direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] == piece:
                    return True
    return False
def is_protected_pawn(board, row, col, piece):
    if piece == 'p':
        directions = [(1, 1), (1, -1)]
        for direction in directions:
            new_row = row + direction[0]
            new_col = col + direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] == piece:
                    return True
    elif piece == 'P':
        directions = [(-1, 1), (-1, -1)]
        for direction in directions:
            new_row = row + direction[0]
            new_col = col + direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board[new_row][new_col] == piece:
                    return True
    return False
def open_file(board, col, turn):
    if turn == 'w':
        for row in range(8):
            if board[row][col] == 'P':
                return False
    elif turn == 'b':
        for row in range(8):
            if board[row][col] == 'p':
                return False
    return True

def corner_queen_mate(board, target_row, target_col, winner):
    print('yolo')
    score = 0
    if winner == 'w':
        for row in range(8):
            for col in range(8):
                if board[row][col] == 'K':
                    distance = abs(row - target_row) + abs(col - target_col)
                    score -= (7 - distance)*10
    elif winner == 'b':
        for row in range(8):
            for col in range(8):
                if board[row][col] == 'k':
                    distance = abs(row - target_row) + abs(col - target_col)
                    score += (7 - distance)*10
    return score
def parse_move(move):
    move = move.lower()
    pattern = r'^([kqrnb])?([a-h])([1-8])'
    match = re.match(pattern, move)
    if match:
        piece = match.group(1) if match.group(1) else 'P'  # If no piece letter, it's a pawn
        col = match.group(2)
        row = int(match.group(3))
        return piece.upper(), col, row
    else:
        return None, None, None

def extract_long_algebraic(move):
    if len(move) != 5:
        raise ValueError("Move must be exactly 5 characters long (e.g., 'Nb8c6')")

    piece = move[0]          # 'N'
    from_square = move[1:3]  # 'b8'
    to_square = move[3:5]    # 'c6'

    from_col = from_square[0]
    from_row = from_square[1]
    to_col = to_square[0]
    to_row = to_square[1]

    return piece, from_row, from_col, to_row, to_col

def normalize_pgn(pgn_str):
    return ' '.join(pgn_str.strip().split())

def clean_move(move):
    move = re.sub(r'[x+#]', '', move)
    move = re.sub(r'=.', '', move)
    return move

def is_pawn_capture(move):
    return bool(re.match(r'^[a-h]x[a-h][1-8](=?[QRNB])?[\+#]?$', move))


def convert_move(board, to_row, to_col, piece, color):
    if color == 'b':
        if piece == 'n':
            directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
            for direction in directions:
                new_row = to_row + direction[0]
                new_col = to_col + direction[1]
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board[new_row][new_col] == 'n':
                        return new_row, new_col
        elif piece == 'b':
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = to_row + i * direction[0]
                    new_col = to_col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] == 'b':
                            return new_row, new_col
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        elif piece == 'r':
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = to_row + i * direction[0]
                    new_col = to_col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] == 'r':
                            return new_row, new_col
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        elif piece == 'q':
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = to_row + i * direction[0]
                    new_col = to_col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] == 'q':
                            return new_row, new_col
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        elif piece == 'p':
            if to_row == 4:
                if board[to_row+1][to_col] == 'p':
                    return to_row+1, to_col
                else:
                    return to_row+2, to_col
            else:
                return to_row+1, to_col
        elif piece == 'k':
              directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
              for direction in directions:
                  new_row = to_row + direction[0]
                  new_col = to_col + direction[1]
                  if 0 <= new_row < 8 and 0 <= new_col < 8:
                      if board[new_row][new_col] == 'k':
                          return new_row, new_col
    elif color == 'w':
        if piece == 'n':
            directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
            for direction in directions:
                new_row = to_row + direction[0]
                new_col = to_col + direction[1]
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board[new_row][new_col] == 'N':
                        print(new_row, new_col)
                        return new_row, new_col
        elif piece == 'b':
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = to_row + i * direction[0]
                    new_col = to_col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] == 'B':
                            return new_row, new_col
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        elif piece == 'r':
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = to_row + i * direction[0]
                    new_col = to_col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] == 'R':
                            return new_row, new_col
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        elif piece == 'q':
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for direction in directions:
                for i in range(1, 8):
                    new_row = to_row + i * direction[0]
                    new_col = to_col + i * direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] == 'Q':
                            return new_row, new_col
                        if board[new_row][new_col] != '0':
                            break
                    else:
                        break
        elif piece == 'p':
            if to_row == 3:
                if board[to_row-1][to_col] == 'P':
                    return to_row-1, to_col
                else:
                    return to_row-2, to_col
            else:
                return to_row-1, to_col
        elif piece == 'k':
              directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
              for direction in directions:
                  new_row = to_row + direction[0]
                  new_col = to_col + direction[1]
                  if 0 <= new_row < 8 and 0 <= new_col < 8:
                      if board[new_row][new_col] == 'K':
                          return new_row, new_col

def extract_moves(pgn_str):
    pattern = r'\b(?:0-0-0|0-0|[a-hRNBQK][a-h1-8x=+#]*)\b'
    return re.findall(pattern, pgn_str)


def players_turn(board, next_move):
    global number_of_moves
    blind = 'flase'
    if next_move == '0-0':
      en_passant = 'false'
      move_played = '0-0'
      board[0][4] = '0'
      board[0][6] = 'K'
      board[0][7] = '0'
      board[0][5] = 'R'
      if blind != 'y':
          print_board(board)
          print()
      start_timer()
    elif next_move == '0-0-0':
      en_passant = 'false'
      move_played = '0-0-0'
      board[0][4] = '0'
      board[0][2] = 'K'
      board[0][0] = '0'
      board[0][3] = 'R'
      if blind != 'y':
          print_board(board)
          print()
      start_timer()
    elif next_move in {'en', 'en_passant', 'passant'}:
      en_passant = 'false'
      from_square = input("From what square: ").strip().lower()
      to_square = input("To what square: ").strip().lower()
      from_row, from_col = pos_to_indices(from_square)
      to_row, to_col = pos_to_indices(to_square)
      board[from_row][from_col] = '0'
      board[from_row][to_col] = '0'
      board[to_row][to_col] = 'P'
      black_king_row, black_king_col = find_king(board, 'b')
      if is_king_in_check(board, black_king_row, black_king_col, 'b'):
          move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '+'
      else:
          move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col)
      if blind != 'y':
          print_board(board)
          print()
      start_timer()
    else:
        if next_move in {'0-0', 'O-O'}:
            best_move = ['0-0']
        elif next_move in {'0-0-0', 'O-O-O'}:
            best_move = ['0-0-0']
        elif len(clean_move(next_move)) == 5:
            next_move = clean_move(next_move)
            piece, from_row, from_col, to_row, to_col = extract_long_algebraic(next_move)
            pos = str(from_col) + str(from_row)
            row, col = pos_to_indices(pos)
            pos = str(to_col) + str(to_row)
            target_row, target_col = pos_to_indices(pos)
            best_move = [row, col, target_row, target_col]
        elif is_pawn_capture(next_move):
            col, row = next_move[2], next_move[3]
            from_col = pos_to_indices_col(next_move[0])
            pos = str(col) + str(row)
            print(pos)
            to_row, to_col = pos_to_indices(pos)
            best_move = [to_row-1, from_col, to_row, to_col]
        else:
            next_move = clean_move(next_move)
            piece, to_col, to_row = parse_move(next_move)
            pos = str(to_col) + str(to_row)
            row, col = pos_to_indices(pos)
            from_row, from_col = convert_move(board, row, col, piece.lower(), 'w')
            best_move = [from_row, from_col, row, col]
        from_row, from_col, to_row, to_col = best_move[0], best_move[1], best_move[2], best_move[3]
        s = board[to_row][to_col]
        if board[from_row][from_col] != '0' and s != 'P' and s != 'R' and s != 'N' and s != 'B' and s != 'K' and s != 'Q':
            piece = board[from_row][from_col]
            captured = board[to_row][to_col]
            black_king_row, black_king_col = find_king(board, 'b')
            if piece == 'P' and to_row == 7:
                board[from_row][from_col] = '0'
                board[to_row][to_col] = 'Q'
                if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                    if captured in {'p', 'n', 'b', 'r', 'q'}:
                        move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '=Q' + '+'
                    else:
                        move_played = indices_to_pos(to_row, to_col) + '=Q' + '+'
                else:
                    if captured in {'p', 'n', 'b', 'r', 'q'}:
                        move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '=Q'
                    else:
                        move_played = indices_to_pos(to_row, to_col) + '=Q'
                en_passant = 'false'
            else:
                board[from_row][from_col] = '0'
                board[to_row][to_col] = piece
                if is_protected_piece(board, to_row, to_col, piece):
                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                        if captured in {'p', 'n', 'b', 'r', 'q'}:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + 'x' + indices_to_pos(to_row, to_col) + '+'
                        else:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + indices_to_pos(to_row, to_col) + '+'
                    else:
                        if captured in {'p', 'n', 'b', 'r', 'q'}:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + 'x' + indices_to_pos(to_row, to_col)
                        else:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + indices_to_pos(to_row, to_col)
                    en_passant = 'false'
                else:
                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                        if piece != 'P':
                            if captured in {'p', 'n', 'b', 'r', 'q'}:
                              move_played = piece.upper() + 'x' + indices_to_pos(to_row, to_col) + '+'
                            else:
                              move_played = piece.upper() + indices_to_pos(to_row, to_col) + '+'
                        else:
                            if captured in {'p', 'n', 'b', 'r', 'q'}:
                              move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '+'
                            else:
                              move_played = indices_to_pos(to_row, to_col) + '+'
                    else:
                        if piece != 'P':
                            if captured in {'p', 'n', 'b', 'r', 'q'}:
                              move_played = piece.upper() + 'x' + indices_to_pos(to_row, to_col)
                            else:
                              move_played = piece.upper() + indices_to_pos(to_row, to_col)
                        else:
                            if captured in {'p', 'n', 'b', 'r', 'q'}:
                              move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col)
                            else:
                              move_played = indices_to_pos(to_row, to_col)
            if piece == 'P' and from_row == 1 and to_row == 3:
                en_passant = from_col
            else:
                en_passant = 'false'
            if blind != 'y':
                print_board(board)
                print()
            if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                if is_checkmate(board, 'b'):
                    print('CHECKMATE! You win!')
                    sys.exit()

            start_timer()
    is_draw(board)
    number_of_moves += 1
    game_moves.append(move_played)
    output = print_moves('b', number_of_moves, game_moves)
    print(output)
def players_turn_white(board, next_move):
    global number_of_moves
    if next_move == '0-0':
      en_passant = 'false'
      move_played = '0-0'
      board[7][4] = '0'
      board[7][6] = 'k'
      board[7][7] = '0'
      board[7][5] = 'r'
      print_board(board)
      print()
    elif next_move == '0-0-0':
      en_passant = 'false'
      move_played = '0-0-0'
      board[7][4] = '0'
      board[7][2] = 'k'
      board[7][0] = '0'
      board[7][3] = 'r'
      print_board(board)
      print()
    elif next_move in {'en', 'en_passant', 'passant'}:
      en_passant = 'false'
      from_square = input("From what square: ").strip().lower()
      to_square = input("To what square: ").strip().lower()
      from_row, from_col = pos_to_indices(from_square)
      to_row, to_col = pos_to_indices(to_square)
      board[from_row][from_col] = '0'
      board[from_row][to_col] = '0'
      board[to_row][to_col] = 'p'
      white_king_row, white_king_col = find_king(board, 'w')
      if is_king_in_check(board, white_king_row, white_king_col, 'w'):
          move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '+'
      else:
          move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col)
      print_board(board)
      print()
      start_timer()
    else:
        if next_move in {'0-0', 'O-O'}:
            best_move = ['0-0']
        elif next_move in {'0-0-0', 'O-O-O'}:
            best_move = ['0-0-0']
        elif len(clean_move(next_move)) == 5:
            next_move = clean_move(next_move)
            piece, from_row, from_col, to_row, to_col = extract_long_algebraic(next_move)
            pos = str(from_col) + str(from_row)
            row, col = pos_to_indices(pos)
            pos = str(to_col) + str(to_row)
            target_row, target_col = pos_to_indices(pos)
            best_move = [row, col, target_row, target_col]
        elif is_pawn_capture(next_move):
            col, row = next_move[2], next_move[3]
            from_col = pos_to_indices_col(next_move[0])
            pos = str(col) + str(row)
            to_row, to_col = pos_to_indices(pos)
            best_move = [to_row+1, from_col, to_row, to_col]
        else:
            next_move = clean_move(next_move)
            piece, to_col, to_row = parse_move(next_move)
            pos = str(to_col) + str(to_row)
            row, col = pos_to_indices(pos)
            from_row, from_col = convert_move(board, row, col, piece.lower(), 'b')
            best_move = [from_row, from_col, row, col]
        from_row, from_col, to_row, to_col = best_move[0], best_move[1], best_move[2], best_move[3]
        s = board[to_row][to_col]
        if board[from_row][from_col] not in {'0', 'P', 'N', 'B', 'R', 'Q'} and s not in {'p', 'n', 'b', 'r', 'q'}:
            piece = board[from_row][from_col]
            captured = board[to_row][to_col]
            white_king_row, white_king_col = find_king(board, 'w')
            if piece == 'p' and to_row == 0:
                board[from_row][from_col] = '0'
                board[to_row][to_col] = 'q'
                if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                    if captured in {'P', 'N', 'B', 'R', 'Q'}:
                        move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '=Q' + '+'
                    else:
                        move_played = indices_to_pos(to_row, to_col) + '=Q' + '+'
                else:
                    if captured in {'P', 'N', 'B', 'R', 'Q'}:
                        move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '=Q'
                    else:
                        move_played = indices_to_pos(to_row, to_col) + '=Q'
                en_passant = 'false'
            else:
                board[from_row][from_col] = '0'
                board[to_row][to_col] = piece
                if is_protected_piece(board, to_row, to_col, piece):
                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                        if captured in {'P', 'N', 'B', 'R', 'Q'}:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + 'x' + indices_to_pos(to_row, to_col) + '+'
                        else:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + indices_to_pos(to_row, to_col) + '+'
                    else:
                        if captured in {'P', 'N', 'B', 'R', 'Q'}:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + 'x' + indices_to_pos(to_row, to_col)
                        else:
                          move_played = piece.upper() + indices_to_pos(from_row, from_col) + indices_to_pos(to_row, to_col)
                    en_passant = 'false'
                else:
                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                        if piece != 'p':
                            if captured in {'P', 'N', 'B', 'R', 'Q'}:
                              move_played = piece.upper() + 'x' + indices_to_pos(to_row, to_col) + '+'
                            else:
                              move_played = piece.upper() + indices_to_pos(to_row, to_col) + '+'
                        else:
                            if captured in {'P', 'N', 'B', 'R', 'Q'}:
                              move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col) + '+'
                            else:
                              move_played = indices_to_pos(to_row, to_col) + '+'
                    else:
                        if piece != 'p':
                            if captured in {'P', 'N', 'B', 'R', 'Q'}:
                              move_played = piece.upper() + 'x' + indices_to_pos(to_row, to_col)
                            else:
                              move_played = piece.upper() + indices_to_pos(to_row, to_col)
                        else:
                            if captured in {'P', 'N', 'B', 'R', 'Q'}:
                              move_played = indices_to_pos_col(from_col) + 'x' + indices_to_pos(to_row, to_col)
                            else:
                              move_played = indices_to_pos(to_row, to_col)
                    if piece == 'p' and from_row == 6 and to_row == 4:
                        en_passant = from_col
                    else:
                        en_passant = 'false'
            print_board(board)
            print()
            if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                if is_checkmate(board, 'w'):
                    print('CHECKMATE! You win!')
                    sys.exit()
            start_timer()
    is_draw(board)
    number_of_moves += 1
    game_moves.append(move_played)
    output = print_moves('w', number_of_moves, game_moves)
    print(output)

def initialize_board():
    answer = 'the'
    if answer.lower() in {'e', 'b', 'edited', 'edited board'}:
        board = [[' ' for _ in range(8)] for _ in range(8)]
        board[0] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[1] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[2] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[3] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[4] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[5] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[6] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[7] = ['0', '0', '0', '0', '0', '0', '0', '0']
        return board
    if answer.lower() in {'set', 's', 'make', 'set board'}:
        board = [[' ' for _ in range(8)] for _ in range(8)]
        board[0] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[1] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[2] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[3] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[4] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[5] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[6] = ['0', '0', '0', '0', '0', '0', '0', '0']
        board[7] = ['0', '0', '0', '0', '0', '0', '0', '0']
        end = False
        while end == False:
            full_pos = input('What piece on what square (e.g. a1R or d4p)?')
            if full_pos.lower() == 'end':
                end = True
            else:
                pos = full_pos[0] + full_pos[1]
                row, col = pos_to_indices(pos)
                board[row][col] = full_pos[2]
        return board
    if answer.lower() in {'paste', 'p'}:
        board = [[' ' for _ in range(8)] for _ in range(8)]
        paste_board = input('what is the board?').replace(" ", "")
        board = []
        for i in range(8):
            row = []
            for j in range(8):
                row.append(paste_board[i * 8 + j])
            board.append(row)
        print_board(board)
        return board

    else:
        board = [[' ' for _ in range(8)] for _ in range(8)]
        board[0] = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        board[1] = ['P'] * 8
        board[2] = ['0'] * 8
        board[3] = ['0'] * 8
        board[4] = ['0'] * 8
        board[5] = ['0'] * 8
        board[6] = ['p'] * 8
        board[7] = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        return board

def print_board(board):
    for row in board:
        print(' '.join(str(cell) for cell in row))


def pick_random_square(board):
    while True:
        row = random.randint(0, 7)
        col = random.randint(0, 7)
        s = board[row][col]
        if s == 'p' or s == 'r' or s == 'n' or s == 'b' or s == 'k' or s == 'q':
            return row, col

board = initialize_board()

def best_move_function(board, bots, en_passant):
    global blind
    global king_move
    global number_of_moves
    global draws
    global wins
    global fifty_move_rule
    blind = 'false'
    black_king_row, black_king_col = find_king(board, 'b')
    checkmate = False
    checkmate2 = False
    bad_checkmate = False
    stalemate = False
    promotion = False
    good_left = False
    good_right = False
    previous_score = -6000
    best_moves = []
    rows = list(range(8))
    cols = list(range(8))
    if board[0][0].lower() == 'r':
      start = True
    else:
      start = False
    opening_moves = ""
    move_number = 0
    print('GM:', game_moves)
    for number in range(len(game_moves) // 2):
        if move_number < len(game_moves):
            opening_moves += str(number + 1) + '. ' + game_moves[move_number] + ' '
            move_number += 1
            if move_number < len(game_moves):
                opening_moves += game_moves[move_number] + ' '
                move_number += 1
        else:
            break
    print('OM:', opening_moves)

    good_moves = [(6, 4, 4, 4, 'p', '0'), (6, 3, 4, 3, 'p', '0'), (7, 6, 5, 5, 'n', '0'), (7, 6, 5, 5, 'n', '0'), (5, 3, 1, 7, 'b', 'P'), (7, 5, 4, 2, 'b', '0'), (5, 5, 4, 3, 'n', 'P'), (4, 4, 3, 3, 'p', 'P')]
    openings = ['1. e4 e5 2. Nf3 Nc6 3. d4 exd4 4. c3 dxc3 5. Nxc3 Bb4 6. Bc4 Nf6 7. e5 Ne4 8. Qd5',
                '1. e4 e5 2. Nf3 Nc6 3. d4 exd4 4. c3 dxc3 5. Nxc3 Bb4 6. Bc4 d6 7. Qb3 Bxc3+ 8. bxc3 Qe7 9. 0-0 Nf6 10. e5 Nxe5 11. Nxe5 dxe5 12. Ba3 c5 13. Bb5+ Bd7 14. Bxd7+ Qxd7 15. Bxc5 Ne4 16. Be3 0-0 17. Rf1d1',
                '1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. 0-0 Nxe4 5. Re1 Nd6 6. Bf1 f6 7. d4 Nf7 8. dxe5 fxe5 9. Nc3',
                '1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6 5. 0-0 Qf6 6. d4 exd4 7. Bg5 Qd6 8. Nxd4 Be7 9. Be3 Nf6 10. f3',
                '1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. 0-0 Nxe4 5. Re1 Nd6 6. Nxe5 Nxe5 7. Rxe5+ Be7 8. Bf1 0-0 9. d4 Bf6 10. Re1 Nf5 11. d5 d6 12. Nc3 h6 13. Ne4 Be5 14. c3 Bd7 15. a4 a5 16. Bd2 c6 17. dxc6 Bxc6 18. Bb5 Bxb5 19. axb5 Re8 20. Ng3 Nxg3 21. hxg3 Bf6 22. Qa4 Qd7 23. Rxe8+ Rxe8 24. Be3 Re5 25. Qxa5 Rxb5 26. Qa8+ Kh7 27. Qa4 Qf5 28. g4 Qe5 29. Ra2 Rd5 30. Qc2+ g6 31. Ra4 Qe6 32. Qb3 Bg5 33. Bxg5 b5 34. Ra7 hxg5 35. Kf1 Qe4 36. Rxf7+ Kh6 37. Re7 Qd3+ 38. Re2 b4 39. f3 Qd1+ 40. Qxd1 Rxd1+ 41. Re1 Rxe1+ 42. Kxe1 b3 43. Ke2 Kg7 44. Ke3 Kf6 45. Kd4 Ke6 46. Kc4 d5+ 47. Kxb3 Ke5 48. Kc2 d4 49. c4 Kd6 50. b4 Ke5 51. Kd3 Kf6  52. Kxd4 Kf7 53. b5 Ke6 54. Kc5 Ke7 55. b6 Ke6 56. b7',
                '1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 g6 6. Be3 Bg7 7. f3 0-0 8. Qd2 Nc6 9. Bc4 Bd7 10. 0-0-0 Ne5 11. Bb3 Rc8 12. Kb1 Nc4 13. Bxc4 Rxc4 14. g4 Qa5 15. g5 Nh5 16. Nd5',
                '1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 g6 6. Be3 Bg7 7. f3 0-0 8. Qd2 Nc6 9. Bc4 Bd7 10. 0-0-0 Ne5 11. Bb3 Qa5 12. Kb1 Rf8c8 13. g4 b5 14. h4 b4 15. Nc3e2 Nc4 16. Bxc4 Rxc4 17. Bh6 Bxh6 18. Qxh6 Qe5 19. h5 g5 20. Nf5 Bxf5 21. Qxg5+ Bg6 22. Qxe5 dxe5 23. hxg6 fxg6 24. g5 Nh5 25. Rd7',
                '1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 g6 6. Be3 Bg7 7. f3 0-0 8. Qd2 Nc6 9. Bc4 Bd7 10. 0-0-0 Ne5 11. Bb3 Qa5 12. Kb1 Rf8c8 13. g4 b5 14. h4 b4 15. Nc3e2 Nc4 16. Bxc4 Rxc4 17. Bh6 Bxh6 18. Qxh6 Qe5 19. h5 g5 20. Nf5 Bxf5 21. Qxg5+ Bg6 22. Qxe5 dxe5 23. hxg6 hxg6 24. Nc1',
                '1. e4 d5 2. exd5 Nf6 3. d4 Bg4 4. f3 Bf5 5. c4 e6 6. dxe6 Nc6 7. exf7+ Kxf7 8. Ne2 Bb4+ 9. Nb1c3 Re8 10. Kf2',
                '1. e4 Nf6 2. e5 Nd5 3. d4 d6 4. c4 Nb6 5. f4 dxe5 6. fxe5 Nc6 7. Be3 Bf5 8. Nc3',
                '1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Be2 0-0 6. h3 a5 7. Bg5 h6 8. Be3 e5 9. d5 Na6 10. Qc1 Nc5 11. Bxc5 dxc5 12. Qe3 b6 13. a4 ',
                '1. d4 d5 2. c4 c6 3. Nf3 Nf6 4. Nc3 dxc4 5. a4 Bf5 6. Ne5',
                '1. e4 e6 2. d4 d5 3. Nc3 Nf6 4. e5 Nf6d7 5. f4 c5 6. Nf3 Nc6 7. Be3 cxd4 8. Nxd4 Bc5 9. Qd2 Bxd4 10. Bxd4 Nxd4 11. Qxd4 Qb6 12. Nb5',
                '1. e4 f5 2. exf5 d5 3. Qh5+ g6 4. fxg6 Kd7 5. Qxd5+',
                '1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Bf5 5. Ng3 Bg6 6. h4 h6 7. Nf3',
                '1. e4 d6 2. d4 Nf6 3. Nc3 g6 4.f4'
    ]
    if opening_moves != 'none':
        for opening in openings:
            normalized_opening = normalize_pgn(opening)
            normalized_input = normalize_pgn(opening_moves)
            if normalized_input in normalized_opening:
                to_play_list = extract_moves(opening)
                played_list = extract_moves(opening_moves)
                next_index = len(played_list)
                if next_index < len(to_play_list):
                    next_move = to_play_list[next_index]
                    if next_move in {'0-0', 'O-O'}:
                        best_moves = [('0-0')]
                        previous_score = score(board, 'w')
                    elif next_move in {'0-0-0', 'O-O-O'}:
                        best_moves = [('0-0-0')]
                        previous_score = score(board, 'w')
                    elif len(clean_move(next_move)) == 5:
                        piece, from_row, from_col, to_row, to_col = extract_long_algebraic(next_move)
                        pos = str(from_col) + str(from_row)
                        row, col = pos_to_indices(pos)
                        pos = str(to_col) + str(to_row)
                        target_row, target_col = pos_to_indices(pos)
                        best_moves = [(row, col, target_row, target_col, piece.lower())]
                        previous_score = score(board, 'w')
                    elif is_pawn_capture(next_move):
                        col, row = next_move[2], next_move[3]
                        from_col = pos_to_indices_col(next_move[0])
                        pos = str(col) + str(row)
                        to_row, to_col = pos_to_indices(pos)
                        best_moves = [(to_row+1, from_col, to_row, to_col, 'p')]
                        previous_score = score(board, 'w')
                    else:
                        next_move = clean_move(next_move)
                        piece, to_col, to_row = parse_move(next_move)
                        pos = str(to_col) + str(to_row)
                        row, col = pos_to_indices(pos)
                        from_row, from_col = convert_move(board, row, col, piece.lower(), 'b')
                        best_moves = [(from_row, from_col, row, col, piece.lower())]
                        previous_score = score(board, 'w')
    elif start:
        best_options = [(6, 4, 4, 4, 'p')]
        best_moves = [random.choice(best_options)]
        previous_score = score(board, 'b')

    if not best_moves:
        for row in rows:
            for col in cols:
                piece = board[row][col]
                if piece == 'p':
                    directions = [1, 2, 3, 4]
                    random.shuffle(directions)
                    for direction in directions:
                        if direction == 1 and row == 6 and board[row-2][col] == '0' and board[row-1][col] == '0':
                            good_right = False
                            good_left = False
                            if col > 0:
                                if board[row-2][col-1] != 'P':
                                    good_left = True
                            else:
                                good_left = True
                            if col < 7:
                                if board[row-2][col+1] != 'P':
                                    good_right = True
                            else:
                                good_right = True
                            if good_right and good_left:
                                print(indices_to_pos(row-2, col))
                                board[row][col] = '0'
                                board[row-2][col] = 'p'
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                    if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                        white_king_row, white_king_col = find_king(board, 'w')
                                        if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            checkmate = True
                                        else:
                                            stalemate = True
                                    elif best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                        bad_checkmate = True
                                    if not checkmate and not bad_checkmate and not stalemate:
                                        if best_piece != 'P':
                                          if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                            print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                          else:
                                            print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                        else:
                                            if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                            else:
                                              print(indices_to_pos(target_row, target_col))
                                        board[best_row][best_col] = '0'
                                        board[target_row][target_col] = best_piece
                                        if target_row == 7 and best_piece == 'P':
                                            board[target_row][target_col] = 'Q'
                                        best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                            checkmate2 = True
                                        if not checkmate2:
                                            if best_piece2 != 'p':
                                                if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                  print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                else:
                                                  print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                            else:
                                                if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                  print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                else:
                                                  print(indices_to_pos(target_row2, target_col2))
                                            board[best_row2][best_col2] = '0'
                                            board[target_row2][target_col2] = best_piece2
                                            if target_row2 == 0 and best_piece2 == 'p':
                                                board[target_row2][target_col2] = 'q'
                                            current_score = score(board, 'w')
                                            for move in good_moves:
                                                if (row, col, row-2, col, 'p', '0') == move:
                                                    current_score += 0.5
                                            print(current_score)
                                            print()
                                            board[best_row2][best_col2] = best_piece2
                                            board[target_row2][target_col2] = captured2
                                            board[best_row][best_col] = best_piece
                                            board[target_row][target_col] = captured
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, row-2, col, 'p')]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, row-2, col, 'p'))
                                    elif checkmate:
                                        print_board(board)
                                        print('CHECKMATE! you lose')
                                        output = print_moves('b', number_of_moves, game_moves)
                                        print(output.rstrip(' '), end='')
                                        next_move = print_piece_move(board, piece, row, col, row-2, col, '0', 'b')
                                        print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                        return next_move
                                        sys.exit()
                                    elif bad_checkmate:
                                        current_score = -1000
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row-2, col, 'p')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row-2, col, 'p'))
                                board[row][col] = 'p'
                                board[row-2][col] = '0'
                                checkmate = False
                                checkmate2 = False
                                bad_checkmate = False
                                stalemate = False

                        elif direction == 2 and row > 0 and board[row-1][col] == '0':
                            print(indices_to_pos(row-1, col))
                            board[row][col] = '0'
                            board[row-1][col] = 'p'
                            if row-1 == 0:
                                board[row-1][col] = 'q'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                  bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 7 and best_piece == 'P':
                                        board[target_row][target_col] = 'Q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'p':
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 0 and best_piece2 == 'p':
                                            board[target_row2][target_col2] = 'q'
                                        current_score = score(board, 'w')
                                        for move in good_moves:
                                            if (row, col, row-1, col, 'p', '0') == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row-1, col, 'p')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row-1, col, 'p'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('b', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row-1, col, '0', 'b')
                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = -1000
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row-1, col, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row-1, col, 'p'))
                            board[row][col] = 'p'
                            board[row-1][col] = '0'
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 3 and row > 0 and col > 0 and board[row-1][col-1] in {'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[row-1][col-1]
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row-1, col-1))
                            board[row][col] = '0'
                            board[row-1][col-1] = 'p'
                            if row-1 == 0:
                                board[row-1][col-1] = 'q'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 7 and best_piece == 'P':
                                        board[target_row][target_col] = 'Q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'p':
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 0 and best_piece2 == 'p':
                                            board[target_row2][target_col2] = 'q'
                                        current_score = score(board, 'w')
                                        for move in good_moves:
                                            if (row, col, row-1, col-1, 'p', captured_piece) == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row-1, col-1, 'p')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row-1, col-1, 'p'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('b', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row-1, col-1, captured_piece, 'b')
                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = -1000
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row-1, col-1, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row-1, col-1, 'p'))
                            board[row][col] = 'p'
                            board[row-1][col-1] = captured_piece
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 3 and row == 3 and col > 0 and board[row][col-1] == 'P' and en_passant == col-1:
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row-1, col-1))
                            board[row][col-1] = '0'
                            board[row][col] = '0'
                            board[row-1][col-1] = 'p'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 7 and best_piece == 'P':
                                        board[target_row][target_col] = 'Q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'p':
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 0 and best_piece2 == 'p':
                                            board[target_row2][target_col2] = 'q'
                                        current_score = score(board, 'w')
                                        for move in good_moves:
                                            if (row, col, row-1, col-1, 'p', 'P') == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row-1, col-1, 'en_passant_minus')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row-1, col-1, 'en_passant_minus'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('b', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row-1, col-1, 'P', 'b')
                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = -1000
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row-1, col-1, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row-1, col-1, 'p'))
                            board[row][col] = 'p'
                            board[row][col-1] = 'P'
                            board[row-1][col-1] = '0'
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 4 and row > 0 and col < 7 and board[row-1][col+1] in {'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[row-1][col+1]
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row-1, col+1))
                            board[row][col] = '0'
                            board[row-1][col+1] = 'p'
                            if row-1 == 0:
                                board[row-1][col+1] = 'q'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 7 and best_piece == 'P':
                                        board[target_row][target_col] = 'Q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'p':
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 0 and best_piece2 == 'p':
                                            board[target_row2][target_col2] = 'q'
                                        current_score = score(board, 'w')
                                        for move in good_moves:
                                            if (row, col, row-1, col+1, 'p', captured_piece) == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row-1, col+1, 'p')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row-1, col+1, 'p'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('b', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row-1, col+1, captured_piece, 'b')
                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = -1000
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row-1, col+1, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row-1, col+1, 'p'))
                            board[row][col] = 'p'
                            board[row-1][col+1] = captured_piece
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 4 and row == 3 and col < 7 and board[row][col+1] == 'P' and en_passant == col+1:
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row-1, col+1))
                            board[row][col+1] = '0'
                            board[row][col] = '0'
                            board[row-1][col+1] = 'p'
                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 7 and best_piece == 'P':
                                        board[target_row][target_col] = 'Q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'p':
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 0 and best_piece2 == 'p':
                                            board[target_row2][target_col2] = 'q'
                                        current_score = score(board, 'w')
                                        for move in good_moves:
                                            if (row, col, row-1, col+1, 'p', 'P') == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row-1, col+1, 'en_passant_plus')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row-1, col+1, 'en_passant_plus'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('b', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row-1, col+1, 'P', 'b')
                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = -1000
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row-1, col+1, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row-1, col+1, 'p'))
                            board[row][col] = 'p'
                            board[row][col+1] = 'P'
                            board[row-1][col+1] = '0'
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False


                elif piece == 'n':
                    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                  print('N' + 'x' + indices_to_pos(new_row, new_col))
                                else:
                                  print('N' + indices_to_pos(new_row, new_col))
                                board[row][col] = '0'
                                board[new_row][new_col] = 'n'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, 'n')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, 'n'))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                        if draw:
                                            current_score = -5
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                white_king_row, white_king_col = find_king(board, 'w')
                                                if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                    checkmate = True
                                                else:
                                                    stalemate = True
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                bad_checkmate = True
                                            if not checkmate and not bad_checkmate and not stalemate:
                                                if best_piece != 'P':
                                                  if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                    print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                  else:
                                                    print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                else:
                                                  if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                    print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                  else:
                                                    print(indices_to_pos(target_row, target_col))
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 7 and best_piece == 'P':
                                                    board[target_row][target_col] = 'Q'
                                                best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                if draw2:
                                                    current_score = -5
                                                    if current_score > previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, piece)]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, piece))
                                                else:
                                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                        checkmate2 = True
                                                    if not checkmate2:
                                                        if best_piece2 != 'p':
                                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                        else:
                                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(indices_to_pos(target_row2, target_col2))
                                                        board[best_row2][best_col2] = '0'
                                                        board[target_row2][target_col2] = best_piece2
                                                        if target_row2 == 0 and best_piece2 == 'p':
                                                            board[target_row2][target_col2] = 'q'
                                                        current_score = score(board, 'w')
                                                        for move in good_moves:
                                                            if (row, col, new_row, new_col, 'n', captured_piece) == move:
                                                                current_score += 0.5
                                                        print(current_score)
                                                        print()
                                                        board[best_row2][best_col2] = best_piece2
                                                        board[target_row2][target_col2] = captured2
                                                        board[best_row][best_col] = best_piece
                                                        board[target_row][target_col] = captured
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, 'n')]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, 'n'))
                                            elif checkmate:
                                                print_board(board)
                                                print('CHECKMATE! you lose')
                                                output = print_moves('b', number_of_moves, game_moves)
                                                print(output.rstrip(' '), end='')
                                                next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'b')
                                                print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                return next_move
                                                sys.exit()
                                            elif bad_checkmate:
                                                current_score = -1000
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'n')]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'n'))
                                board[row][col] = 'n'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                checkmate2 = False
                                bad_checkmate = False
                                stalemate = False
                                position_history[pos_hash] -= 1


                elif piece == 'b':
                    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                      print('B' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('B' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'b'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = -5
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'b')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'b'))
                                    else:
                                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                            if draw:
                                                current_score = -5
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, row-2, col, 'p')]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, row-2, col, 'p'))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    white_king_row, white_king_col = find_king(board, 'w')
                                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 7 and best_piece == 'P':
                                                        board[target_row][target_col] = 'Q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                    if draw2:
                                                        current_score = -5
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'p':
                                                              if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 0 and best_piece2 == 'p':
                                                                board[target_row2][target_col2] = 'q'
                                                            current_score = score(board, 'w')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'b', captured_piece) == move:
                                                                    current_score += 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score > previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'b')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'b'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('b', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'b')
                                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = -1000
                                                    if current_score > previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'b')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'b'))
                                    board[row][col] = 'b'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    position_history[pos_hash] -= 1

                                else:
                                    break
                                if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                    break
                            else:
                                break

                elif piece == 'r':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                      print('R' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('R' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'r'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = -5
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'r')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'r'))
                                    else:
                                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                            if draw:
                                                current_score = -5
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, row-2, col, 'p')]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, row-2, col, 'p'))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    white_king_row, white_king_col = find_king(board, 'w')
                                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 7 and best_piece == 'P':
                                                        board[target_row][target_col] = 'Q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                    if draw2:
                                                        current_score = -5
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'p':
                                                              if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 0 and best_piece2 == 'p':
                                                                board[target_row2][target_col2] = 'q'
                                                            current_score = score(board, 'w')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'r', captured_piece) == move:
                                                                    current_score += 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score > previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'r')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'r'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('b', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'b')
                                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = -1000
                                                    if current_score > previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'r')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'r'))
                                    board[row][col] = 'r'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    position_history[pos_hash] -= 1

                                else:
                                    break
                                if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                    break
                            else:
                                break

                elif piece == 'q':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                      print('Q' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('Q' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'q'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = -5
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'q')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'q'))
                                    else:
                                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                            if draw:
                                                current_score = -5
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, row-2, col, 'p')]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, row-2, col, 'p'))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    white_king_row, white_king_col = find_king(board, 'w')
                                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 7 and best_piece == 'P':
                                                        board[target_row][target_col] = 'Q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                    if draw2:
                                                        current_score = -5
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'p':
                                                              if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 0 and best_piece2 == 'p':
                                                                board[target_row2][target_col2] = 'q'
                                                            current_score = score(board, 'w')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'q', captured_piece) == move:
                                                                    current_score += 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score > previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'q')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'q'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('b', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'b')
                                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = -1000
                                                    if current_score > previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'q')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'q'))
                                    board[row][col] = 'q'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    position_history[pos_hash] -= 1

                                else:
                                    break
                                if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                    break
                            else:
                                break

                elif piece == 'k':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1), '0-0', '0-0-0']
                    random.shuffle(directions)
                    for direction in directions:
                        if direction not in {'0-0', '0-0-0'}:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                      print('K' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('K' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'k'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = -5
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'k')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'k'))
                                    else:
                                        black_king_row, black_king_col = find_king(board, 'b')
                                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                            if draw:
                                                current_score = -5
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, row-2, col, 'p')]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, row-2, col, 'p'))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    white_king_row, white_king_col = find_king(board, 'w')
                                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                        else:
                                                          print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 7 and best_piece == 'P':
                                                        board[target_row][target_col] = 'Q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                    if draw2:
                                                        current_score = -5
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'p':
                                                                if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                  print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                                else:
                                                                  print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                                if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                                  print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                                else:
                                                                  print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 0 and best_piece2 == 'p':
                                                                board[target_row2][target_col2] = 'q'
                                                            current_score = score(board, 'w')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'k', captured_piece) == move:
                                                                    current_score += 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score > previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'k')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'k'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('b', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'b')
                                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = -1000
                                                    if current_score > previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'k')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'k'))
                                    board[row][col] = 'k'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    position_history[pos_hash] -= 1
                        else:
                            if direction == '0-0':
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    if board[7][4] == 'k' and board[7][7] == 'r' and king_move == 0 and board[7][5] == '0' and board[7][6] == '0':
                                        board[7][5] = 'k'
                                        board[7][4] = '0'
                                        black_king_row, black_king_col = find_king(board, 'b')
                                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            board[7][6] = 'k'
                                            board[7][5] = '0'
                                            black_king_row, black_king_col = find_king(board, 'b')
                                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                                print('0-0')
                                                board[7][7] = '0'
                                                board[7][5] = 'r'
                                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 1:
                                                    checkmate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 2:
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate:
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                        else:
                                                          print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                        checkmate2 = True
                                                    if not checkmate2:
                                                        if best_piece2 != 'p':
                                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                        else:
                                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(indices_to_pos(target_row2, target_col2))
                                                        board[best_row2][best_col2] = '0'
                                                        board[target_row2][target_col2] = best_piece2
                                                        current_score = score(board, 'w')
                                                        print(current_score)
                                                        print()
                                                        board[best_row2][best_col2] = best_piece2
                                                        board[target_row2][target_col2] = captured2
                                                        board[best_row][best_col] = best_piece
                                                        board[target_row][target_col] = captured
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [('0-0')]
                                                        elif current_score == previous_score:
                                                            best_moves.append(('0-0'))
                                                        board[7][6] = '0'
                                                        board[7][4] = 'k'
                                                        board[7][6] = '0'
                                                        board[7][7] = 'r'
                                                        board[7][5] = '0'
                                                        checkmate = False
                                                        checkmate2 = False
                                                        black_king_row, black_king_col = find_king(board, 'b')
                                                elif checkmate:
                                                        print_board(board)
                                                        print('CHECKMATE! you lose')
                                                        output = print_moves('b', number_of_moves, game_moves)
                                                        print(output.rstrip(' '), end='')
                                                        next_move = '0-0'
                                                        print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                        return next_move
                                                        sys.exit()
                                            else:
                                                board[7][4] = 'k'
                                                board[7][6] = '0'
                                                black_king_row, black_king_col = find_king(board, 'b')
                                        else:
                                            board[7][4] = 'k'
                                            board[7][5] = '0'
                                            black_king_row, black_king_col = find_king(board, 'b')

                            elif direction == '0-0-0':
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    if board[7][4] == 'k' and board[7][0] == 'r' and king_move == 0 and board[7][1] == '0' and board[7][2] == '0' and board[7][3] == '0':
                                        board[7][3] = 'k'
                                        board[7][4] = '0'
                                        black_king_row, black_king_col = find_king(board, 'b')
                                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            board[7][2] = 'k'
                                            board[7][3] = '0'
                                            black_king_row, black_king_col = find_king(board, 'b')
                                            if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                                print('0-0-0')
                                                board[7][0] = '0'
                                                board[7][3] = 'r'
                                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player(board)
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 1:
                                                    checkmate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 2:
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate:
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                        else:
                                                          print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2(board)
                                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                        checkmate2 = True
                                                    if not checkmate2:
                                                        if best_piece2 != 'p':
                                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                        else:
                                                            if board[target_row2][target_col2] in {'P', 'N', 'B', 'R', 'Q'}:
                                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(indices_to_pos(target_row2, target_col2))
                                                        board[best_row2][best_col2] = '0'
                                                        board[target_row2][target_col2] = best_piece2
                                                        current_score = score(board, 'w')
                                                        print(current_score)
                                                        print()
                                                        board[best_row2][best_col2] = best_piece2
                                                        board[target_row2][target_col2] = captured2
                                                        board[best_row][best_col] = best_piece
                                                        board[target_row][target_col] = captured
                                                        if current_score > previous_score:
                                                            previous_score = current_score
                                                            best_moves = [('0-0-0')]
                                                        elif current_score == previous_score:
                                                            best_moves.append(('0-0-0'))
                                                        board[7][4] = 'k'
                                                        board[7][2] = '0'
                                                        board[7][0] = 'r'
                                                        board[7][3] = '0'

                                                        checkmate = False
                                                        checkmate2 = False
                                                        black_king_row, black_king_col = find_king(board, 'b')
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('b', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = '0-0-0'
                                                    print(' ' + str(number_of_moves+1) + '. ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                            else:
                                                board[7][4] = 'k'
                                                board[7][2] = '0'
                                                black_king_row, black_king_col = find_king(board, 'b')
                                        else:
                                            board[7][4] = 'k'
                                            board[7][3] = '0'
                                            black_king_row, black_king_col = find_king(board, 'b')

    if best_moves:
        best_move = random.choice(best_moves)
        if best_move != '0-0' and best_move != '0-0-0':
            best_row, best_col, target_row, target_col, best_piece = best_move
            if best_piece == 'en_passant_minus':
                board[target_row][target_col] = 'p'
                board[best_row][best_col] = '0'
                board[best_row][best_col-1] = '0'
                if blind != 'y':
                    print_board(board)
                    print()
                    print(str(number_of_moves+1) + '. ', end='')
                move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                print(move_played)
            elif best_piece == 'en_passant_plus':
                board[target_row][target_col] = 'p'
                board[best_row][best_col] = '0'
                board[best_row][best_col+1] = '0'
                if blind != 'y':
                    print_board(board)
                    print()
                    print(str(number_of_moves+1) + '. ', end='')
                move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                print(move_played)
            else:
                captured_piece = board[target_row][target_col]
                piece = board[target_row][target_col]
                board[best_row][best_col] = '0'
                board[target_row][target_col] = best_piece
                if blind != 'y':
                    print_board(board)
                    print()
                    print(str(number_of_moves+1) + '. ', end='')
                if best_piece == 'k':
                    king_move = 1
                white_king_row, white_king_col = find_king(board, 'w')
                if best_piece == 'p' and target_row == 0:
                    board[target_row][target_col] = 'q'
                    if blind != 'y':
                        print_board(board)
                        print()
                        print(str(number_of_moves+1) + '. ', end='')
                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                        if piece in {'P', 'N', 'B', 'R', 'Q'}:
                            move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '=Q' + '+'
                            print(move_played)
                        else:
                            move_played = indices_to_pos(target_row, target_col) + '=Q' + '+'
                            print(move_played)
                    else:
                        if piece in {'P', 'N', 'B', 'R', 'Q'}:
                            move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '=Q'
                            print(move_played)
                        else:
                            move_played = indices_to_pos(target_row, target_col) + '=Q'
                            print(move_played)
                    en_passant = 'false'
                else:
                    if is_protected_piece(board, target_row, target_col, best_piece):
                        if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            if piece in {'P', 'N', 'B', 'R', 'Q'}:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + 'x' + indices_to_pos(target_row, target_col) + '+'
                              print(move_played)
                            else:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + indices_to_pos(target_row, target_col) + '+'
                              print(move_played)
                        else:
                            if piece in {'P', 'N', 'B', 'R', 'Q'}:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + 'x' + indices_to_pos(target_row, target_col)
                              print(move_played)
                            else:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + indices_to_pos(target_row, target_col)
                              print(move_played)
                        en_passant = 'false'
                    else:
                        if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            if best_piece != 'p':
                                  if piece in {'P', 'N', 'B', 'R', 'Q'}:
                                    move_played = best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                                  else:
                                    move_played = best_piece.upper() + indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                            else:
                                  if piece in {'P', 'N', 'B', 'R', 'Q'}:
                                    move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                                  else:
                                    move_played = indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                        else:
                            if best_piece != 'p':
                                  if piece in {'P', 'N', 'B', 'R', 'Q'}:
                                    move_played = best_piece.upper() + 'x' + indices_to_pos(target_row, target_col)
                                    print(move_played)
                                  else:
                                    move_played = best_piece.upper() + indices_to_pos(target_row, target_col)
                                    print(move_played)
                            else:
                                  if piece in {'P', 'N', 'B', 'R', 'Q'}:
                                    move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                                    print(move_played)
                                  else:
                                    move_played = indices_to_pos(target_row, target_col)
                                    print(move_played)
                        if best_piece == 'p' and best_row == 6 and target_row == 4:
                            en_passant = best_col
                        else:
                            en_passant = 'false'
        if best_move == '0-0':
            en_passant = 'false'
            castled = True
            move_played = '0-0'
            king_move = 1
            board[7][4] = '0'
            board[7][7] = '0'
            board[7][6] = 'k'
            board[7][5] = 'r'
            if blind != 'y':
                print_board(board)
                print()
                print(str(number_of_moves+1) + '. ', end='')
            print('0-0')
        elif best_move == '0-0-0':
            en_passant = 'false'
            castled = True
            king_move = 1
            move_played = '0-0-0'
            board[7][4] = '0'
            board[7][0] = '0'
            board[7][2] = 'k'
            board[7][3] = 'r'
            if blind != 'y':
                print_board(board)
                print()
                print(str(number_of_moves+1) + '. ', end='')
            print('0-0-0')
        if blind != 'y':
            print(previous_score)
            print()
        game_moves.append(move_played)
        number_of_moves += 1
        output = print_moves('w', number_of_moves, game_moves)
        if blind != 'y':
            print(output)
        is_draw(board)
        pos_hash = ''.join(''.join(row) for row in board)
        position_history[pos_hash] += 1
        if position_history[pos_hash] >= 3:
            print('Draw by Repetition')
            sys.exit()
        fifty_move_rule += 1
        if best_move not in {'0-0-0', '0-0'}:
            if best_piece in {'p', 'en_passant_minus', 'en_passant_plus'} or 'x' in move_played:
                fifty_move_rule = 0
        if fifty_move_rule >= 50:
            print('Draw by 50-Move Rule')
            sys.exit()
        print('MP:', move_played)
        return move_played


def best_move_player(board):
    white_king_row, white_king_col = find_king(board, 'w')
    checkmate = False
    promotion = False
    previous_score = 6000
    best_moves = []
    rows = list(range(8))
    cols = list(range(8))

    for row in rows:
        for col in cols:
            piece = board[row][col]
            if piece == 'P':
                directions = [1, 2, 3, 4]
                random.shuffle(directions)
                for direction in directions:
                    if direction == 1 and row == 1 and board[row+2][col] == '0' and board[row+1][col] == '0':
                        board[row][col] = '0'
                        board[row+2][col] = 'P'
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 0 and best_piece == 'p':
                                    board[target_row][target_col] = 'q'
                                current_score = score(board, 'w')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row+2, col, 'P')]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row+2, col, 'P'))
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                            else:
                                board[row][col] = 'P'
                                board[row+2][col] = '0'
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'P'
                        board[row+2][col] = '0'
                        checkmate = False

                    elif direction == 2 and row < 7 and board[row+1][col] == '0':
                        board[row][col] = '0'
                        board[row+1][col] = 'P'
                        if row+1 == 7:
                            board[row+1][col] = 'Q'
                            promotion = True
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha2')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 0 and best_piece == 'p':
                                    board[target_row][target_col] = 'q'
                                current_score = score(board, 'w')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row+1, col, 'P')]
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row+1, col, 'P'))
                            else:
                                board[row][col] = 'P'
                                board[row+1][col] = '0'
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'P'
                        board[row+1][col] = '0'
                        checkmate = False

                    elif direction == 3 and row < 7 and col > 0 and board[row+1][col-1] in {'p', 'n', 'b', 'r', 'q'}:
                        captured_piece = board[row+1][col-1]
                        board[row][col] = '0'
                        board[row+1][col-1] = 'P'
                        if row+1 == 7:
                            board[row+1][col-1] = 'Q'
                            promotion = True
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha3')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 0 and best_piece == 'p':
                                    board[target_row][target_col] = 'q'
                                current_score = score(board, 'w')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row+1, col-1, 'P')]
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row+1, col-1, 'P'))
                            else:
                                board[row][col] = 'P'
                                board[row+1][col-1] = captured_piece
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'P'
                        board[row+1][col-1] = captured_piece
                        checkmate = False

                    elif direction == 4 and row > 0 and col < 7 and board[row+1][col+1] in {'p', 'n', 'b', 'r', 'q'}:
                        captured_piece = board[row+1][col+1]
                        board[row][col] = '0'
                        board[row+1][col+1] = 'P'
                        if row+1 == 7:
                            board[row+1][col+1] = 'Q'
                            promotion = True
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha4')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 0 and best_piece == 'p':
                                    board[target_row][target_col] = 'q'
                                current_score = score(board, 'w')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row+1, col+1, 'P')]
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row+1, col+1, 'P'))
                            else:
                                board[row][col] = 'P'
                                board[row+1][col+1] = captured_piece
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'P'
                        board[row+1][col+1] = captured_piece
                        checkmate = False

            elif piece == 'N':
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'N'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = 5
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                                    if draw:
                                        current_score = 5
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, piece)]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, piece))
                                    else:
                                        if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                            checkmate = True
                                            print('hahaha N')
                                        if not checkmate:
                                            board[best_row][best_col] = '0'
                                            board[target_row][target_col] = best_piece
                                            if target_row == 0 and best_piece == 'p':
                                                board[target_row][target_col] = 'q'
                                            current_score = score(board, 'w')
                                            board[best_row][best_col] = best_piece
                                            board[target_row][target_col] = captured
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, 'N')]
                                                if best_piece != 'p':
                                                  if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                    analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                  else:
                                                    analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                else:
                                                    if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                      analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                      analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, 'N'))
                                        else:
                                            board[row][col] = 'N'
                                            board[new_row][new_col] = captured_piece
                                            checkmate = False
                                            return '2', '2', '2', '2', '2', '2', False
                            board[row][col] = 'N'
                            board[new_row][new_col] = captured_piece
                            checkmate = False
                            position_history[pos_hash] -= 1

            elif piece == 'B':
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'B'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                                        if draw:
                                            current_score = 5
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                checkmate = True
                                                print('hahaha B')
                                            if not checkmate:
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 0 and best_piece == 'p':
                                                    board[target_row][target_col] = 'q'
                                                current_score = score(board, 'w')
                                                board[best_row][best_col] = best_piece
                                                board[target_row][target_col] = captured
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'B')]
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                      else:
                                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                        else:
                                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'B'))
                                            else:
                                                board[row][col] = 'B'
                                                board[new_row][new_col] = captured_piece
                                                checkmate = False
                                                return '2', '2', '2', '2', '2', '2', False
                                board[row][col] = 'B'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                position_history[pos_hash] -= 1

                            else:
                                break
                            if board[new_row][new_col] == 'p' or board[new_row][new_col] == 'n' or board[new_row][new_col] == 'b' or board[new_row][new_col] == 'r' or board[new_row][new_col] == 'q':
                                break
                        else:
                            break

            elif piece == 'R':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'R'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                                        if draw:
                                            current_score = 5
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                checkmate = True
                                                print('hahaha R')
                                            if not checkmate:
                                                if best_piece != 'p':
                                                  if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                    analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                  else:
                                                    analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                else:
                                                    if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                      analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                      analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 0 and best_piece == 'p':
                                                    board[target_row][target_col] = 'q'
                                                current_score = score(board, 'w')
                                                board[best_row][best_col] = best_piece
                                                board[target_row][target_col] = captured
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'R')]
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                      else:
                                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                        else:
                                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'R'))
                                            else:
                                                board[row][col] = 'R'
                                                board[new_row][new_col] = captured_piece
                                                checkmate = False
                                                return '2', '2', '2', '2', '2', '2', False
                                board[row][col] = 'R'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] == 'p' or board[new_row][new_col] == 'n' or board[new_row][new_col] == 'b' or board[new_row][new_col] == 'r' or board[new_row][new_col] == 'q':
                                break
                        else:
                            break

            elif piece == 'Q':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'Q'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                                        if draw:
                                            current_score = 5
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                checkmate = True
                                                print('hahaha Q')
                                            if not checkmate:
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 0 and best_piece == 'p':
                                                    board[target_row][target_col] = 'q'
                                                current_score = score(board, 'w')
                                                board[best_row][best_col] = best_piece
                                                board[target_row][target_col] = captured
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'Q')]
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                      else:
                                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                        else:
                                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'Q'))
                                            else:
                                                board[row][col] = 'Q'
                                                board[new_row][new_col] = captured_piece
                                                checkmate = False
                                                return '2', '2', '2', '2', '2', '2', False
                                board[row][col] = 'Q'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] == 'p' or board[new_row][new_col] == 'n' or board[new_row][new_col] == 'b' or board[new_row][new_col] == 'r' or board[new_row][new_col] == 'q':
                                break
                        else:
                            break

            elif piece == 'K':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'K'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = 5
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                white_king_row, white_king_col = find_king(board, 'w')
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2(board)
                                    if draw:
                                        current_score = 5
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, piece)]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, piece))
                                    else:
                                        if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                            checkmate = True
                                        if not checkmate:
                                            board[best_row][best_col] = '0'
                                            board[target_row][target_col] = best_piece
                                            if target_row == 0 and best_piece == 'p':
                                                board[target_row][target_col] = 'q'
                                            current_score = score(board, 'w')
                                            board[best_row][best_col] = best_piece
                                            board[target_row][target_col] = captured
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, 'K')]
                                                if best_piece != 'p':
                                                  if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                    analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                  else:
                                                    analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                else:
                                                    if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                      analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                      analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, 'K'))
                                        else:
                                            board[row][col] = 'K'
                                            board[new_row][new_col] = captured_piece
                                            checkmate = False
                                            white_king_row, white_king_col = find_king(board, 'w')
                                            return '2', '2', '2', '2', '2', '2', False
                            board[row][col] = 'K'
                            board[new_row][new_col] = captured_piece
                            checkmate = False
                            white_king_row, white_king_col = find_king(board, 'w')
                            position_history[pos_hash] -= 1

    if best_moves:
        best_move = random.choice(best_moves)
        best_row, best_col, target_row, target_col, best_piece = best_move
        captured_piece = board[target_row][target_col]
        pos_hash = ''.join(''.join(row) for row in board)
        position_history[pos_hash] += 1
        if position_history[pos_hash] >= 3:
            draw = True
        else:
            draw = False
        position_history[pos_hash] -= 1
        return best_row, best_col, target_row, target_col, best_piece, captured_piece, draw
    else:
        return '1', '1', '1', '1', '1', '1', False

def best_move2(board):
    black_king_row, black_king_col = find_king(board, 'b')
    promotion = False
    previous_score = -6000
    best_moves = []
    rows = list(range(8))
    cols = list(range(8))

    for row in rows:
        for col in cols:
            piece = board[row][col]
            if piece == 'p':
                directions = [1, 2, 3, 4]
                random.shuffle(directions)
                for direction in directions:
                    if direction == 1 and row == 6 and board[row-2][col] == '0' and board[row-1][col] == '0':
                        board[row][col] = '0'
                        board[row-2][col] = 'p'
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            current_score = score(board, 'w')
                            if current_score > previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row-2, col, 'p')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row-2, col, 'p'))
                        board[row][col] = 'p'
                        board[row-2][col] = '0'

                    elif direction == 2 and row < 7 and board[row-1][col] == '0':
                        board[row][col] = '0'
                        board[row-1][col] = 'p'
                        if row-1 == 0:
                            board[row-1][col] = 'q'
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            current_score = score(board, 'w')
                            if current_score > previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row-1, col, 'p')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row-1, col, 'p'))
                        board[row][col] = 'p'
                        board[row-1][col] = '0'

                    elif direction == 3 and row < 7 and col > 0 and board[row-1][col-1] in {'P', 'N', 'B', 'R', 'Q'}:
                        captured_piece = board[row-1][col-1]
                        board[row][col] = '0'
                        board[row-1][col-1] = 'p'
                        if row-1 == 0:
                            board[row-1][col-1] = 'q'
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            current_score = score(board, 'w')
                            if current_score > previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row-1, col-1, 'p')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row-1, col-1, 'p'))
                        board[row][col] = 'p'
                        board[row-1][col-1] = captured_piece

                    elif direction == 4 and row > 0 and col < 7 and board[row-1][col+1] in {'P', 'N', 'B', 'R', 'Q'}:
                        captured_piece = board[row-1][col+1]
                        board[row][col] = '0'
                        board[row-1][col+1] = 'p'
                        if row-1 == 0:
                            board[row-1][col+1] = 'q'
                            promotion = True
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            current_score = score(board, 'w')
                            if current_score > previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row-1, col+1, 'p')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row-1, col+1, 'p'))
                        board[row][col] = 'p'
                        board[row-1][col+1] = captured_piece

            elif piece == 'n':
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'n'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = -5
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    current_score = score(board, 'w')
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, 'n')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, 'n'))
                            board[row][col] = 'n'
                            board[new_row][new_col] = captured_piece
                            position_history[pos_hash] -= 1


            elif piece == 'b':
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'b'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        current_score = score(board, 'w')
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'b')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'b'))
                                board[row][col] = 'b'
                                board[new_row][new_col] = captured_piece
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                break
                        else:
                            break

            elif piece == 'r':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'r'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        current_score = score(board, 'w')
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'r')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'r'))
                                board[row][col] = 'r'
                                board[new_row][new_col] = captured_piece
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                break
                        else:
                            break

            elif piece == 'q':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'q'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        current_score = score(board, 'w')
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'q')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'q'))
                                board[row][col] = 'q'
                                board[new_row][new_col] = captured_piece
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] == 'P' or board[new_row][new_col] == 'N' or board[new_row][new_col] == 'B' or board[new_row][new_col] == 'R' or board[new_row][new_col] == 'Q':
                                break
                        else:
                            break

            elif piece == 'k':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'k'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = -5
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                black_king_row, black_king_col = find_king(board, 'b')
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    current_score = score(board, 'w')
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, 'k')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, 'k'))
                            board[row][col] = 'k'
                            board[new_row][new_col] = captured_piece
                            black_king_row, black_king_col = find_king(board, 'b')
                            position_history[pos_hash] -= 1

    if best_moves:
        best_move = random.choice(best_moves)
        best_row2, best_col2, target_row2, target_col2, best_piece2 = best_move
        captured_piece2 = board[target_row2][target_col2]
        board[best_row2][best_col2] = '0'
        board[target_row2][target_col2] = best_piece2
        pos_hash = ''.join(''.join(row) for row in board)
        position_history[pos_hash] += 1
        if position_history[pos_hash] >= 3:
            draw = True
        else:
            draw = False
        position_history[pos_hash] -= 1
        return best_row2, best_col2, target_row2, target_col2, best_piece2, captured_piece2, draw
    else:
        return '1', '1', '1', '1', '1', '1', False

def best_move_black(board, bots, en_passant):
    global blind
    global draws
    global wins
    global king_move_white
    global number_of_moves
    global fifty_move_rule
    blind = 'false'
    white_king_row, white_king_col = find_king(board, 'w')
    checkmate = False
    checkmate2 = False
    bad_checkmate = False
    stalemate = False
    promotion = False
    good_left = False
    good_right = False
    previous_score = 6000
    best_moves = []
    rows = list(range(8))
    cols = list(range(8))
    good_moves = [(0, 1, 2, 2, 'N', '0')]
    opening_moves = ""
    move_number = 0
    for number in range(number_of_moves):
        opening_moves += str(number + 1) + '. ' + game_moves[move_number] + ' '
        move_number += 1
        if number != number_of_moves - 1:
            opening_moves += game_moves[move_number] + ' '
        else:
            opening_moves += ' '
        move_number += 1
    openings = ['1. e4 e5 2. Nf3 Nc6 3. d4 exd4 4. c3 dxc3 5. Nxc3 Bb4 6. Bc4 d6 7. Qb3 Bxc3+ 8. bxc3 Qe7 9. 0-0 Nf6 10. e5 Nxe5 11. Nxe5 dxe5 12. Ba3 c5 13. Bb5+ Bd7 14. Bxd7+ Qxd7 15. Bxc5 Ne4 16. Be3 0-0 17. Rf1d1 Qc6',
                '1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6 5. 0-0 Qf6 6. d4 exd4 7. Bg5 Qd6 8. Nxd4 Be7 9. Be3 Nf6 10. f3 c5 11. Nb3 b6',
                '1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. 0-0 Nxe4 5. Re1 Nd6 6. Nxe5 Nxe5 7. Rxe5+ Be7 8. Bf1 0-0 9. d4 Bf6',
                '1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 g6 6. Be3 Bg7 7. f3 0-0 8. Qd2 Nc6 9. Bc4 Bd7 10. 0-0-0 Ne5 11. Bb3 Qa5 12. Kb1 Rf8c8 13. g4 b5 14. h4 b4 15. Nc3e2 Nc4 16. Bxc4 Rxc4 17. Bh6 Bxh6 18. Qxh6 Qe5 19. h5 g5 20. Nf5 Bxf5 21. Qxg5+ Bg6 22. Qxe5 dxe5 23. hxg6 hxg6',
                '1. e4 d5 2. exd5 Nf6 3. d4 Bg4 4. f3 Bf5 5. c4 e6 6. dxe6 Nc6 7. exf7+ Kxf7 8. Be3 Bb4+ 9. Kf2 Re8 10. Nc3 Rxe3 11. Kxe3 Nxd4 12. Kf2 Bc5 13. Na4 Bc2 14. Nxc5 Bxd1',
                '1. e4 d5 2. exd5 Nf6 3. d4 Bg4 4. f3 Bf5 5. c4 e6 6. dxe6 Nc6 7. exf7+ Kxf7 8. Ne2 Bb4+',
                '1. e4 d5 2. exd5 Nf6 3. d4 Bg4 4. f3 Bf5 5. c4 e6 6. dxe6 Nc6 7. exf7+ Kxf7 8. Be3 Bb4+ 9. Kf2 Re8 10. Nc3 Rxe3 11. Kxe3 Nxd4 12. Qxd4 Qe7+ 13. Kf4 Nh5+ 14. Kxf5 Qe6+ 15. Kg5 Be7+ 16. Kxh5',
                '1. e4 Nf6 2. e5 Nd5 3. d4 d6 4. c4 Nb6 5. f4 dxe5 6. fxe5 Nc6 7. Be3 Bf5 8. Nc3 e6 9. Nf3 Bb4 10. Be2 0-0',
                '1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Be2 0-0 6. h3 a5 7. Bg5 h6 8. Be3 e5 9. d5 Na6 10. Qc1 Nc5 11. Bxc5 dxc5 12. Qe3 b6 13. a4 Ne8',
                '1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. Nc3 b5 6. Bb3 Be7 7. a4 b4 8. Nd5 0-0 9. Nxf6+ Bxf6',
                '1. e4 e6 2. d4 d5 3. Nc3 Nf6 4. e5 Nf6d7 5. f4 c5 6. Nf3 Nc6 7. Be3 cxd4 8. Nxd4 Bc5 9. Qd2 Bxd4 10. Bxd4 Nxd4 11. Qxd4 Qb6 12. Qd2 Qxb2 13. Rb1 Qa3 14. Nb5 Qxa2 15. Nd6+ Ke7 16. Rc1',
                '1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Bf5 5. Ng3 Bg6 6. h4 h6',
                '1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 6. cxd4 Bb4+ 7. Bd2 Nxe4 8. Bxb4 Nxb4 9. Bxf7+ Kxf7 10. Qb3+ d5 11. Ne5+ Ke6 12. Qxb4 Qf8 13. Qxf8 Rxf8 14. f3 Nd6',
                '1. e4 d6 2. d4 Nf6 3. Nc3 g6 4.f4 Bg7',
                '1. e4 d6 2. d4 Nf6 3. Nc3 g6 4.Nf3 Bg7 5. Bc4 0-0',
                '1. h4 Nc6 2. Rh3 d5 3. Rg3 Nf6 4. a4 Ne4 5. Rg3a3 e5 6. Ra3a2 Qxh4',
                ]
    normalized_opening = normalize_pgn(opening_moves)
    if normalized_opening == '1. e4':
        best_options = [(1, 4, 3, 4, 'P'), (1, 2, 3, 2, 'P'), (1, 3, 3, 3, 'P'), (1, 4, 2, 4, 'P'), (1, 2, 2, 2, 'P')]
        best_option = random.choice(best_options)
        best_moves = [best_option]
        previous_score = score(board, 'b')
    elif opening_moves != 'none':
        random.shuffle(openings)
        for opening in openings:
            normalized_opening = normalize_pgn(opening)
            normalized_input = normalize_pgn(opening_moves)
            if normalized_input in normalized_opening:
                to_play_list = extract_moves(opening)
                played_list = extract_moves(opening_moves)
                next_index = len(played_list)
                if next_index < len(to_play_list):
                    next_move = to_play_list[next_index]
                    if next_move in {'0-0', 'O-O'}:
                        best_moves = [('0-0')]
                        previous_score = score(board, 'b')
                    elif next_move in {'0-0-0', 'O-O-O'}:
                        best_moves = [('0-0-0')]
                        previous_score = score(board, 'b')
                    elif len(clean_move(next_move)) == 5:
                        piece, from_row, from_col, to_row, to_col = extract_long_algebraic(next_move)
                        pos = str(from_col) + str(from_row)
                        row, col = pos_to_indices(pos)
                        pos = str(to_col) + str(to_row)
                        target_row, target_col = pos_to_indices(pos)
                        best_moves = [(row, col, target_row, target_col, piece)]
                        previous_score = score(board, 'b')
                    elif is_pawn_capture(next_move):
                        col, row = next_move[2], next_move[3]
                        from_col = pos_to_indices_col(next_move[0])
                        pos = str(col) + str(row)
                        to_row, to_col = pos_to_indices(pos)
                        best_moves = [(to_row-1, from_col, to_row, to_col, 'P')]
                        previous_score = score(board, 'b')
                    else:
                        next_move = clean_move(next_move)
                        piece, to_col, to_row = parse_move(next_move)
                        pos = str(to_col) + str(to_row)
                        row, col = pos_to_indices(pos)
                        from_row, from_col = convert_move(board, row, col, piece.lower(), 'w')
                        best_moves = [(from_row, from_col, row, col, piece)]
                        previous_score = score(board, 'b')
    if not best_moves:
        for row in rows:
            for col in cols:
                piece = board[row][col]
                if piece == 'P':
                    directions = [1, 2, 3, 4]
                    random.shuffle(directions)
                    for direction in directions:
                        if direction == 1 and row == 1 and board[row+2][col] == '0' and board[row+1][col] == '0':
                            good_right = False
                            good_left = False
                            if col > 0:
                                if board[row+2][col-1] != 'p':
                                    good_left = True
                            else:
                                good_left = True
                            if col < 7:
                                if board[row+2][col+1] != 'p':
                                    good_right = True
                            else:
                                good_right = True
                            if good_right and good_left:
                                print(indices_to_pos(row+2, col))
                                board[row][col] = '0'
                                board[row+2][col] = 'P'
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                    if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                        black_king_row, black_king_col = find_king(board, 'w')
                                        if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                            checkmate = True
                                        else:
                                            stalemate = True
                                    elif best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                        bad_checkmate = True
                                    if not checkmate and not bad_checkmate and not stalemate:
                                        if best_piece != 'p':
                                          if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                            print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                          else:
                                            print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                        else:
                                            if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                              print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                            else:
                                              print(indices_to_pos(target_row, target_col))
                                        board[best_row][best_col] = '0'
                                        board[target_row][target_col] = best_piece
                                        if target_row == 0 and best_piece == 'p':
                                            board[target_row][target_col] = 'q'
                                        best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                            checkmate2 = True
                                        if not checkmate2:
                                            if best_piece2 != 'P':
                                                if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                  print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                else:
                                                  print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                            else:
                                                if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                  print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                else:
                                                  print(indices_to_pos(target_row2, target_col2))
                                            board[best_row2][best_col2] = '0'
                                            board[target_row2][target_col2] = best_piece2
                                            if target_row2 == 7 and best_piece2 == 'P':
                                                board[target_row2][target_col2] = 'Q'
                                            current_score = score(board, 'b')
                                            for move in good_moves:
                                                if (row, col, row+2, col, 'P', '0') == move:
                                                    current_score -= 0.5
                                            print(current_score)
                                            print()
                                            board[best_row2][best_col2] = best_piece2
                                            board[target_row2][target_col2] = captured2
                                            board[best_row][best_col] = best_piece
                                            board[target_row][target_col] = captured
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, row+2, col, 'P')]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, row+2, col, 'P'))
                                    elif checkmate:
                                        print_board(board)
                                        print('CHECKMATE! you lose')
                                        output = print_moves('w', number_of_moves, game_moves)
                                        print(output.rstrip(' '), end='')
                                        next_move = print_piece_move(board, piece, row, col, row+2, col, '0', 'w')
                                        print(' ' + next_move + '#')
                                        return next_move
                                        sys.exit()
                                    elif bad_checkmate:
                                        current_score = 1000
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row+2, col, 'P')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row+2, col, 'P'))
                                board[row][col] = 'P'
                                board[row+2][col] = '0'
                                checkmate = False
                                checkmate2 = False
                                bad_checkmate = False
                                stalemate = False

                        elif direction == 2 and row < 7 and board[row+1][col] == '0':
                            print(indices_to_pos(row+1, col))
                            board[row][col] = '0'
                            board[row+1][col] = 'P'
                            if row+1 == 7:
                                board[row+1][col] = 'Q'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                  bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 0 and best_piece == 'p':
                                        board[target_row][target_col] = 'q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'P':
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 7 and best_piece2 == 'P':
                                            board[target_row2][target_col2] = 'Q'
                                        current_score = score(board, 'b')
                                        for move in good_moves:
                                            if (row, col, row+1, col, 'P', '0') == move:
                                                current_score -= 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row+1, col, 'P')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row+1, col, 'P'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('w', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row+1, col, '0', 'w')
                                    print(' ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = 1000
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row+1, col, 'P')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row+1, col, 'P'))
                            board[row][col] = 'P'
                            board[row+1][col] = '0'
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 3 and row < 7 and col > 0 and board[row+1][col-1] in {'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[row+1][col-1]
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row+1, col-1))
                            board[row][col] = '0'
                            board[row+1][col-1] = 'P'
                            if row+1 == 7:
                                board[row+1][col-1] = 'Q'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 0 and best_piece == 'p':
                                        board[target_row][target_col] = 'q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'P':
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 7 and best_piece2 == 'P':
                                            board[target_row2][target_col2] = 'Q'
                                        current_score = score(board, 'b')
                                        for move in good_moves:
                                            if (row, col, row+1, col-1, 'P', captured_piece) == move:
                                                current_score -= 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row+1, col-1, 'P')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row+1, col-1, 'P'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('w', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row+1, col-1, captured_piece, 'w')
                                    print(' ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = 1000
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row+1, col-1, 'P')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row+1, col-1, 'P'))
                            board[row][col] = 'P'
                            board[row+1][col-1] = captured_piece
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 3 and row == 4 and col > 0 and board[row][col-1] == 'p' and en_passant == col-1:
                            print('en_passant')
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row+1, col-1))
                            board[row][col-1] = '0'
                            board[row][col] = '0'
                            board[row+1][col-1] = 'P'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 0 and best_piece == 'p':
                                        board[target_row][target_col] = 'q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'P':
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 7 and best_piece2 == 'P':
                                            board[target_row2][target_col2] = 'Q'
                                        current_score = score(board, 'b')
                                        for move in good_moves:
                                            if (row, col, row+1, col-1, 'p', 'P') == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row+1, col-1, 'en_passant_minus')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row+1, col-1, 'en_passant_minus'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('w', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row+1, col-1, 'p', 'w')
                                    print(' ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = 1000
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row+1, col-1, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row+1, col-1, 'p'))
                            board[row][col] = 'P'
                            board[row][col-1] = 'p'
                            board[row+1][col-1] = '0'
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 4 and row < 7 and col < 7 and board[row+1][col+1] in {'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[row+1][col+1]
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row+1, col+1))
                            board[row][col] = '0'
                            board[row+1][col+1] = 'P'
                            if row+1 == 7:
                                board[row+1][col+1] = 'Q'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 0 and best_piece == 'p':
                                        board[target_row][target_col] = 'q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'P':
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 7 and best_piece2 == 'P':
                                            board[target_row2][target_col2] = 'Q'
                                        current_score = score(board, 'b')
                                        for move in good_moves:
                                            if (row, col, row+1, col+1, 'P', captured_piece) == move:
                                                current_score -= 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row+1, col+1, 'P')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row+1, col+1, 'P'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('w', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row+1, col+1, captured_piece, 'w')
                                    print(' ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = 1000
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row+1, col+1, 'P')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row+1, col+1, 'P'))
                            board[row][col] = 'P'
                            board[row+1][col+1] = captured_piece
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False

                        elif direction == 4 and row == 4 and col < 7 and board[row][col+1] == 'p' and en_passant == col+1:
                            print('en_passant')
                            print(indices_to_pos_col(col) + 'x' + indices_to_pos(row+1, col+1))
                            board[row][col+1] = '0'
                            board[row][col] = '0'
                            board[row+1][col+1] = 'P'
                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                    black_king_row, black_king_col = find_king(board, 'b')
                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        checkmate = True
                                    else:
                                        stalemate = True
                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                    bad_checkmate = True
                                if not checkmate and not bad_checkmate and not stalemate:
                                    if best_piece != 'p':
                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                      else:
                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                    else:
                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                        else:
                                          print(indices_to_pos(target_row, target_col))
                                    board[best_row][best_col] = '0'
                                    board[target_row][target_col] = best_piece
                                    if target_row == 0 and best_piece == 'p':
                                        board[target_row][target_col] = 'q'
                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                        checkmate2 = True
                                    if not checkmate2:
                                        if best_piece2 != 'P':
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                        else:
                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                            else:
                                              print(indices_to_pos(target_row2, target_col2))
                                        board[best_row2][best_col2] = '0'
                                        board[target_row2][target_col2] = best_piece2
                                        if target_row2 == 7 and best_piece2 == 'P':
                                            board[target_row2][target_col2] = 'Q'
                                        current_score = score(board, 'b')
                                        for move in good_moves:
                                            if (row, col, row+1, col+1, 'p', 'P') == move:
                                                current_score += 0.5
                                        print(current_score)
                                        print()
                                        board[best_row2][best_col2] = best_piece2
                                        board[target_row2][target_col2] = captured2
                                        board[best_row][best_col] = best_piece
                                        board[target_row][target_col] = captured
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, row+1, col+1, 'en_passant_plus')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, row+1, col+1, 'en_passant_plus'))
                                elif checkmate:
                                    print_board(board)
                                    print('CHECKMATE! you lose')
                                    output = print_moves('w', number_of_moves, game_moves)
                                    print(output.rstrip(' '), end='')
                                    next_move = print_piece_move(board, piece, row, col, row+1, col+1, 'p', 'w')
                                    print(' ' + next_move + '#')
                                    return next_move
                                    sys.exit()
                                elif bad_checkmate:
                                    current_score = 1000
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, row+1, col+1, 'p')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, row+1, col+1, 'p'))
                            board[row][col] = 'P'
                            board[row][col+1] = 'p'
                            board[row+1][col+1] = '0'
                            checkmate = False
                            checkmate2 = False
                            bad_checkmate = False
                            stalemate = False


                elif piece == 'N':
                    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                  print('N' + 'x' + indices_to_pos(new_row, new_col))
                                else:
                                  print('N' + indices_to_pos(new_row, new_col))
                                board[row][col] = '0'
                                board[new_row][new_col] = 'N'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, 'N')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, 'N'))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                        if draw:
                                            current_score = 5
                                            if current_score < previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                black_king_row, black_king_col = find_king(board, 'b')
                                                if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                                    checkmate = True
                                                else:
                                                    stalemate = True
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                bad_checkmate = True
                                            if not checkmate and not bad_checkmate and not stalemate:
                                                if best_piece != 'p':
                                                  if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                    print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                  else:
                                                    print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                else:
                                                  if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                    print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                  else:
                                                    print(indices_to_pos(target_row, target_col))
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 0 and best_piece == 'p':
                                                    board[target_row][target_col] = 'q'
                                                best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                if draw2:
                                                    current_score = 5
                                                    if current_score < previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, piece)]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, piece))
                                                else:
                                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                        checkmate2 = True
                                                    if not checkmate2:
                                                        if best_piece2 != 'P':
                                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                        else:
                                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(indices_to_pos(target_row2, target_col2))
                                                        board[best_row2][best_col2] = '0'
                                                        board[target_row2][target_col2] = best_piece2
                                                        if target_row2 == 7 and best_piece2 == 'P':
                                                            board[target_row2][target_col2] = 'Q'
                                                        current_score = score(board, 'b')
                                                        for move in good_moves:
                                                            if (row, col, new_row, new_col, 'N', captured_piece) == move:
                                                                current_score -= 0.5
                                                        print(current_score)
                                                        print()
                                                        board[best_row2][best_col2] = best_piece2
                                                        board[target_row2][target_col2] = captured2
                                                        board[best_row][best_col] = best_piece
                                                        board[target_row][target_col] = captured
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, 'N')]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, 'N'))
                                            elif checkmate:
                                                print_board(board)
                                                print('CHECKMATE! you lose')
                                                output = print_moves('w', number_of_moves, game_moves)
                                                print(output.rstrip(' '), end='')
                                                next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'w')
                                                print(' ' + next_move + '#')
                                                return next_move
                                                sys.exit()
                                            elif bad_checkmate:
                                                current_score = 1000
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'N')]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'N'))
                                board[row][col] = 'N'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                checkmate2 = False
                                bad_checkmate = False
                                stalemate = False
                                position_history[pos_hash] -= 1

                elif piece == 'B':
                    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                      print('B' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('B' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'B'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = 5
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'B')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'B'))
                                    else:
                                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                            if draw:
                                                current_score = 5
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, piece)]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, piece))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    black_king_row, black_king_col = find_king(board, 'b')
                                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 0 and best_piece == 'p':
                                                        board[target_row][target_col] = 'q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                    if draw2:
                                                        current_score = 5
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'P':
                                                              if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 7 and best_piece2 == 'P':
                                                                board[target_row2][target_col2] = 'Q'
                                                            current_score = score(board, 'b')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'B', captured_piece) == move:
                                                                    current_score -= 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score < previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'B')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'B'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('w', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'w')
                                                    print(' ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = 1000
                                                    if current_score < previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'B')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'B'))
                                    board[row][col] = 'B'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    position_history[pos_hash] -= 1

                                else:
                                    break
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break

                elif piece == 'R':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                      print('R' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('R' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'R'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = 5
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'R')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'R'))
                                    else:
                                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                            if draw:
                                                current_score = 5
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, piece)]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, piece))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    black_king_row, black_king_col = find_king(board, 'b')
                                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 0 and best_piece == 'p':
                                                        board[target_row][target_col] = 'q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                    if draw2:
                                                        current_score = 5
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'P':
                                                              if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 7 and best_piece2 == 'P':
                                                                board[target_row2][target_col2] = 'Q'
                                                            current_score = score(board, 'b')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'R', captured_piece) == move:
                                                                    current_score -= 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score < previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'R')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'R'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('w', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'w')
                                                    print(' ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = 1000
                                                    if current_score < previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'R')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'R'))
                                    board[row][col] = 'R'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    position_history[pos_hash] -= 1

                                else:
                                    break
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break

                elif piece == 'Q':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                    random.shuffle(directions)
                    for direction in directions:
                        for i in range(1, 8):
                            new_row = row + i * direction[0]
                            new_col = col + i * direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                      print('Q' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('Q' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'Q'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = 5
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'Q')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'Q'))
                                    else:
                                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                            if draw:
                                                current_score = 5
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, piece)]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, piece))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    black_king_row, black_king_col = find_king(board, 'b')
                                                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 0 and best_piece == 'p':
                                                        board[target_row][target_col] = 'q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                    if draw2:
                                                        current_score = 5
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'P':
                                                              if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                              else:
                                                                print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 7 and best_piece2 == 'P':
                                                                board[target_row2][target_col2] = 'Q'
                                                            current_score = score(board, 'b')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'Q', captured_piece) == move:
                                                                    current_score -= 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score < previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'Q')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'Q'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('w', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'w')
                                                    print(' ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = 1000
                                                    if current_score < previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'Q')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'Q'))
                                    board[row][col] = 'Q'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    position_history[pos_hash] -= 1

                                else:
                                    break
                                if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                    break
                            else:
                                break

                elif piece == 'K':
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1), '0-0', '0-0-0']
                    random.shuffle(directions)
                    for direction in directions:
                        if direction not in {'0-0', '0-0-0'}:
                            new_row = row + direction[0]
                            new_col = col + direction[1]
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                    captured_piece = board[new_row][new_col]
                                    if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                      print('K' + 'x' + indices_to_pos(new_row, new_col))
                                    else:
                                      print('K' + indices_to_pos(new_row, new_col))
                                    board[row][col] = '0'
                                    board[new_row][new_col] = 'K'
                                    pos_hash = ''.join(''.join(row) for row in board)
                                    position_history[pos_hash] += 1
                                    if position_history[pos_hash] >= 3:
                                        current_score = 5
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'K')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'K'))
                                    else:
                                        white_king_row, white_king_col = find_king(board, 'w')
                                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                            if draw:
                                                current_score = 5
                                                if current_score < previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, piece)]
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, piece))
                                            else:
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                    black_king_row, black_king_col = find_king(board, 'b')
                                                    if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                        checkmate = True
                                                    else:
                                                        stalemate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == '2':
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate and not stalemate:
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                        else:
                                                          print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    if target_row == 0 and best_piece == 'p':
                                                        board[target_row][target_col] = 'q'
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                    if draw2:
                                                        current_score = 5
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [(row, col, new_row, new_col, piece)]
                                                        elif current_score == previous_score:
                                                            best_moves.append((row, col, new_row, new_col, piece))
                                                    else:
                                                        if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                            checkmate2 = True
                                                        if not checkmate2:
                                                            if best_piece2 != 'P':
                                                                if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                  print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                                else:
                                                                  print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                                if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                                  print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                                else:
                                                                  print(indices_to_pos(target_row2, target_col2))
                                                            board[best_row2][best_col2] = '0'
                                                            board[target_row2][target_col2] = best_piece2
                                                            if target_row2 == 7 and best_piece2 == 'P':
                                                                board[target_row2][target_col2] = 'Q'
                                                            current_score = score(board, 'b')
                                                            for move in good_moves:
                                                                if (row, col, new_row, new_col, 'K', captured_piece) == move:
                                                                    current_score -= 0.5
                                                            print(current_score)
                                                            print()
                                                            board[best_row2][best_col2] = best_piece2
                                                            board[target_row2][target_col2] = captured2
                                                            board[best_row][best_col] = best_piece
                                                            board[target_row][target_col] = captured
                                                            if current_score < previous_score:
                                                                previous_score = current_score
                                                                best_moves = [(row, col, new_row, new_col, 'K')]
                                                            elif current_score == previous_score:
                                                                best_moves.append((row, col, new_row, new_col, 'K'))
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('w', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    next_move = print_piece_move(board, piece, row, col, new_row, new_col, captured_piece, 'w')
                                                    print(' ' + next_move + '#')
                                                    return next_move
                                                    sys.exit()
                                                elif bad_checkmate:
                                                    current_score = 1000
                                                    if current_score < previous_score:
                                                        previous_score = current_score
                                                        best_moves = [(row, col, new_row, new_col, 'K')]
                                                    elif current_score == previous_score:
                                                        best_moves.append((row, col, new_row, new_col, 'K'))
                                    board[row][col] = 'K'
                                    board[new_row][new_col] = captured_piece
                                    checkmate = False
                                    checkmate2 = False
                                    bad_checkmate = False
                                    stalemate = False
                                    white_king_row, white_king_col = find_king(board, 'w')
                                    position_history[pos_hash] -= 1
                        else:
                            if direction == '0-0':
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    if board[0][4] == 'K' and board[0][7] == 'R' and king_move_white == 0 and board[0][5] == '0' and board[0][6] == '0':
                                        board[0][5] = 'K'
                                        board[0][4] = '0'
                                        white_king_row, white_king_col = find_king(board, 'w')
                                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            board[0][6] = 'K'
                                            board[0][5] = '0'
                                            white_king_row, white_king_col = find_king(board, 'w')
                                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                print('0-0')
                                                board[0][7] = '0'
                                                board[0][5] = 'R'
                                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 1:
                                                    checkmate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 2:
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate:
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                        else:
                                                          print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                        checkmate2 = True
                                                    if not checkmate2:
                                                        if best_piece2 != 'P':
                                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                        else:
                                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(indices_to_pos(target_row2, target_col2))
                                                        board[best_row2][best_col2] = '0'
                                                        board[target_row2][target_col2] = best_piece2
                                                        current_score = score(board, 'b')
                                                        print(current_score)
                                                        print()
                                                        board[best_row2][best_col2] = best_piece2
                                                        board[target_row2][target_col2] = captured2
                                                        board[best_row][best_col] = best_piece
                                                        board[target_row][target_col] = captured
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [('0-0')]
                                                        elif current_score == previous_score:
                                                            best_moves.append(('0-0'))
                                                        board[0][6] = '0'
                                                        board[0][4] = 'K'
                                                        board[0][6] = '0'
                                                        board[0][7] = 'R'
                                                        board[0][5] = '0'
                                                        checkmate = False
                                                        checkmate2 = False
                                                        black_king_row, black_king_col = find_king(board, 'b')
                                                elif checkmate:
                                                        print_board(board)
                                                        print('CHECKMATE! you lose')
                                                        output = print_moves('w', number_of_moves, game_moves)
                                                        print(output.rstrip(' '), end='')
                                                        print(' 0-0' + '#')
                                                        return next_move
                                                        sys.exit()
                                            else:
                                                board[0][4] = 'K'
                                                board[0][6] = '0'
                                                white_king_row, white_king_col = find_king(board, 'w')
                                        else:
                                            board[0][4] = 'K'
                                            board[0][5] = '0'
                                            white_king_row, white_king_col = find_king(board, 'w')

                            elif direction == '0-0-0':
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    if board[0][4] == 'K' and board[0][0] == 'R' and king_move_white == 0 and board[0][1] == '0' and board[0][2] == '0' and board[0][3] == '0':
                                        board[0][3] = 'K'
                                        board[0][4] = '0'
                                        white_king_row, white_king_col = find_king(board, 'w')
                                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                            board[0][2] = 'K'
                                            board[0][3] = '0'
                                            white_king_row, white_king_col = find_king(board, 'w')
                                            if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                                print('0-0-0')
                                                board[0][0] = '0'
                                                board[0][3] = 'R'
                                                best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move_player_black(board)
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 1:
                                                    checkmate = True
                                                if best_row == best_col == target_row == target_col == best_piece == captured == 2:
                                                    bad_checkmate = True
                                                if not checkmate and not bad_checkmate:
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                        print(best_piece.upper() + 'x' + indices_to_pos(target_row, target_col))
                                                      else:
                                                        print(best_piece.upper() + indices_to_pos(target_row, target_col))
                                                    else:
                                                        if board[target_row][target_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                                          print(indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col))
                                                        else:
                                                          print(indices_to_pos(target_row, target_col))
                                                    board[best_row][best_col] = '0'
                                                    board[target_row][target_col] = best_piece
                                                    best_row2, best_col2, target_row2, target_col2, best_piece2, captured2, draw2 = best_move2_black(board)
                                                    if best_row2 == best_col2 == target_row2 == target_col2 == best_piece2 == captured2 == '1':
                                                        checkmate2 = True
                                                    if not checkmate2:
                                                        if best_piece2 != 'P':
                                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                              print(best_piece2.upper() + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(best_piece2.upper() + indices_to_pos(target_row2, target_col2))
                                                        else:
                                                            if board[target_row2][target_col2] in {'p', 'n', 'b', 'r', 'q'}:
                                                              print(indices_to_pos_col(best_col2) + 'x' + indices_to_pos(target_row2, target_col2))
                                                            else:
                                                              print(indices_to_pos(target_row2, target_col2))
                                                        board[best_row2][best_col2] = '0'
                                                        board[target_row2][target_col2] = best_piece2
                                                        current_score = score(board, 'b')
                                                        print(current_score)
                                                        print()
                                                        board[best_row2][best_col2] = best_piece2
                                                        board[target_row2][target_col2] = captured2
                                                        board[best_row][best_col] = best_piece
                                                        board[target_row][target_col] = captured
                                                        if current_score < previous_score:
                                                            previous_score = current_score
                                                            best_moves = [('0-0-0')]
                                                        elif current_score == previous_score:
                                                            best_moves.append(('0-0-0'))
                                                        board[0][4] = 'K'
                                                        board[0][2] = '0'
                                                        board[0][0] = 'R'
                                                        board[0][3] = '0'

                                                        checkmate = False
                                                        checkmate2 = False
                                                        white_king_row, white_king_col = find_king(board, 'b')
                                                elif checkmate:
                                                    print_board(board)
                                                    print('CHECKMATE! you lose')
                                                    output = print_moves('w', number_of_moves, game_moves)
                                                    print(output.rstrip(' '), end='')
                                                    print(' 0-0-0' + '#')
                                                    return next_move
                                                    sys.exit()
                                            else:
                                                board[0][4] = 'K'
                                                board[0][2] = '0'
                                                white_king_row, white_king_col = find_king(board, 'w')
                                        else:
                                            board[0][4] = 'K'
                                            board[0][3] = '0'
                                            white_king_row, white_king_col = find_king(board, 'w')

    if best_moves:
        best_move = random.choice(best_moves)
        if best_move != '0-0' and best_move != '0-0-0':
            best_row, best_col, target_row, target_col, best_piece = best_move
            if best_piece == 'en_passant_minus':
                en_passant = 'false'
                board[target_row][target_col] = 'P'
                board[best_row][best_col] = '0'
                board[best_row][best_col-1] = '0'
                if blind != 'y':
                    print_board(board)
                    print()
                    print(str(number_of_moves) + '...', end='')
                move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                print(move_played)
            elif best_piece == 'en_passant_plus':
                en_passant = 'false'
                board[target_row][target_col] = 'P'
                board[best_row][best_col] = '0'
                board[best_row][best_col+1] = '0'
                if blind != 'y':
                    print_board(board)
                    print()
                    print(str(number_of_moves) + '...', end='')
                move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                print(move_played)
            else:
                captured_piece = board[target_row][target_col]
                piece = board[target_row][target_col]
                board[best_row][best_col] = '0'
                board[target_row][target_col] = best_piece
                if blind != 'y':
                    print_board(board)
                    print()
                    print(str(number_of_moves) + '...', end='')
                if best_piece == 'K':
                    king_move_white = 1
                black_king_row, black_king_col = find_king(board, 'b')
                if best_piece == 'P' and target_row == 7:
                    board[target_row][target_col] = 'Q'
                    if blind != 'y':
                        print_board(board)
                        print()
                        print(str(number_of_moves) + '...', end='')
                    if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                        if piece in {'p', 'n', 'b', 'r', 'q'}:
                            move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '=Q' + '+'
                            print(move_played)
                        else:
                            move_played = indices_to_pos(target_row, target_col) + '=Q' + '+'
                            print(move_played)
                    else:
                        if piece in {'p', 'n', 'b', 'r', 'q'}:
                            move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '=Q'
                            print(move_played)
                        else:
                            move_played = indices_to_pos(target_row, target_col) + '=Q'
                            print(move_played)
                    en_passant = 'false'
                else:
                    if is_protected_piece(board, target_row, target_col, best_piece):
                        if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            if piece in {'p', 'n', 'b', 'r', 'q'}:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + 'x' + indices_to_pos(target_row, target_col) + '+'
                              print(move_played)
                            else:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + indices_to_pos(target_row, target_col) + '+'
                              print(move_played)
                        else:
                            if piece in {'p', 'n', 'b', 'r', 'q'}:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + 'x' + indices_to_pos(target_row, target_col)
                              print(move_played)
                            else:
                              move_played = best_piece.upper() + indices_to_pos(best_row, best_col) + indices_to_pos(target_row, target_col)
                              print(move_played)
                        en_passant = 'false'
                    else:
                        if is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            if best_piece != 'P':
                                  if piece in {'p', 'n', 'b', 'r', 'q'}:
                                    move_played = best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                                  else:
                                    move_played = best_piece.upper() + indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                            else:
                                  if piece in {'p', 'n', 'b', 'r', 'q'}:
                                    move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                                  else:
                                    move_played = indices_to_pos(target_row, target_col) + '+'
                                    print(move_played)
                        else:
                            if best_piece != 'P':
                                  if piece in {'p', 'n', 'b', 'r', 'q'}:
                                    move_played = best_piece.upper() + 'x' + indices_to_pos(target_row, target_col)
                                    print(move_played)
                                  else:
                                    move_played = best_piece.upper() + indices_to_pos(target_row, target_col)
                                    print(move_played)
                            else:
                                  if piece in {'p', 'n', 'b', 'r', 'q'}:
                                    move_played = indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col)
                                    print(move_played)
                                  else:
                                    move_played = indices_to_pos(target_row, target_col)
                                    print(move_played)
                        if best_piece == 'P' and best_row == 1 and target_row == 3:
                            en_passant = best_col
                        else:
                            en_passant = 'false'
        if best_move == '0-0':
            en_passant = 'false'
            castled_white = True
            move_played = '0-0'
            king_move_white = 1
            board[0][4] = '0'
            board[0][7] = '0'
            board[0][6] = 'K'
            board[0][5] = 'R'
            if blind != 'y':
                print_board(board)
                print()
                print(str(number_of_moves) + '...', end='')
            print('0-0')
        elif best_move == '0-0-0':
            en_passant = 'false'
            castled_white = True
            king_move_white = 1
            move_played = '0-0-0'
            board[0][4] = '0'
            board[0][0] = '0'
            board[0][2] = 'K'
            board[0][3] = 'R'
            if blind != 'y':
                print_board(board)
                print()
                print(str(number_of_moves) + '...', end='')
            print('0-0-0')
        if blind != 'y':
            print(previous_score)
            print()
        game_moves.append(move_played)
        output = print_moves('b', number_of_moves, game_moves)
        if blind != 'y':
            print(output)
        is_draw(board)
        pos_hash = ''.join(''.join(row) for row in board)
        position_history[pos_hash] += 1
        if position_history[pos_hash] >= 3:
            print('Draw by Repetition')
            sys.exit()
        if best_move not in {'0-0-0', '0-0'}:
            if best_piece in {'P', 'en_passant_minus', 'en_passant_plus'} or 'x' in move_played:
                fifty_move_rule = 0
        return move_played

def best_move_player_black(board):
    black_king_row, black_king_col = find_king(board, 'b')
    checkmate = False
    promotion = False
    previous_score = -6000
    best_moves = []
    rows = list(range(8))
    cols = list(range(8))

    for row in rows:
        for col in cols:
            piece = board[row][col]
            if piece == 'p':
                directions = [1, 2, 3, 4]
                random.shuffle(directions)
                for direction in directions:
                    if direction == 1 and row == 7 and board[row-2][col] == '0' and board[row-1][col] == '0':
                        board[row][col] = '0'
                        board[row-2][col] = 'p'
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 7 and best_piece == 'P':
                                    board[target_row][target_col] = 'Q'
                                current_score = score(board, 'b')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row-2, col, 'p')]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row-2, col, 'p'))
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                            else:
                                board[row][col] = 'p'
                                board[row-2][col] = '0'
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'p'
                        board[row-2][col] = '0'
                        checkmate = False

                    elif direction == 2 and row > 0 and board[row-1][col] == '0':
                        board[row][col] = '0'
                        board[row-1][col] = 'p'
                        if row-1 == 0:
                            board[row-1][col] = 'q'
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha2')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 7 and best_piece == 'P':
                                    board[target_row][target_col] = 'Q'
                                current_score = score(board, 'b')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row-1, col, 'p')]
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row-1, col, 'p'))
                            else:
                                board[row][col] = 'p'
                                board[row-1][col] = '0'
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'p'
                        board[row-1][col] = '0'
                        checkmate = False

                    elif direction == 3 and row > 0 and col > 0 and board[row-1][col-1] in {'P', 'N', 'B', 'R', 'Q'}:
                        captured_piece = board[row-1][col-1]
                        board[row][col] = '0'
                        board[row-1][col-1] = 'p'
                        if row-1 == 0:
                            board[row-1][col-1] = 'q'
                            promotion = True
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha3')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 7 and best_piece == 'P':
                                    board[target_row][target_col] = 'Q'
                                current_score = score(board, 'b')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row-1, col-1, 'p')]
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row-1, col-1, 'p'))
                            else:
                                board[row][col] = 'p'
                                board[row-1][col-1] = captured_piece
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'p'
                        board[row-1][col-1] = captured_piece
                        checkmate = False

                    elif direction == 4 and row > 0 and col < 7 and board[row-1][col+1] in {'P', 'N', 'B', 'R', 'Q'}:
                        captured_piece = board[row-1][col+1]
                        board[row][col] = '0'
                        board[row-1][col+1] = 'p'
                        if row-1 == 0:
                            board[row-1][col+1] = 'q'
                            promotion = True
                        if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                            best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                checkmate = True
                                print('hahaha4')
                            if not checkmate:
                                board[best_row][best_col] = '0'
                                board[target_row][target_col] = best_piece
                                if target_row == 7 and best_piece == 'P':
                                    board[target_row][target_col] = 'Q'
                                current_score = score(board, 'b')
                                board[best_row][best_col] = best_piece
                                board[target_row][target_col] = captured
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, row-1, col+1, 'p')]
                                    if best_piece != 'P':
                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                      else:
                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                    else:
                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                        else:
                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                elif current_score == previous_score:
                                    best_moves.append((row, col, row-1, col+1, 'p'))
                            else:
                                board[row][col] = 'p'
                                board[row-1][col+1] = captured_piece
                                checkmate = False
                                return '2', '2', '2', '2', '2', '2', False
                        board[row][col] = 'p'
                        board[row-1][col+1] = captured_piece
                        checkmate = False

            elif piece == 'n':
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'n'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = -5
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                                    if draw:
                                        current_score = -5
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, piece)]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, piece))
                                    else:
                                        if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                            checkmate = True
                                            print('hahaha N')
                                        if not checkmate:
                                            board[best_row][best_col] = '0'
                                            board[target_row][target_col] = best_piece
                                            if target_row == 7 and best_piece == 'P':
                                                board[target_row][target_col] = 'Q'
                                            current_score = score(board, 'b')
                                            board[best_row][best_col] = best_piece
                                            board[target_row][target_col] = captured
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, 'n')]
                                                if best_piece != 'P':
                                                  if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                    analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                  else:
                                                    analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                else:
                                                    if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                      analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                      analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, 'n'))
                                        else:
                                            board[row][col] = 'n'
                                            board[new_row][new_col] = captured_piece
                                            checkmate = False
                                            return '2', '2', '2', '2', '2', '2', False
                            board[row][col] = 'n'
                            board[new_row][new_col] = captured_piece
                            checkmate = False
                            position_history[pos_hash] -= 1

            elif piece == 'b':
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'b'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                                        if draw:
                                            current_score = -5
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                checkmate = True
                                                print('hahaha B')
                                            if not checkmate:
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 7 and best_piece == 'P':
                                                    board[target_row][target_col] = 'Q'
                                                current_score = score(board, 'b')
                                                board[best_row][best_col] = best_piece
                                                board[target_row][target_col] = captured
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'b')]
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                      else:
                                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                        else:
                                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'b'))
                                            else:
                                                board[row][col] = 'b'
                                                board[new_row][new_col] = captured_piece
                                                checkmate = False
                                                return '2', '2', '2', '2', '2', '2', False
                                board[row][col] = 'b'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                break
                        else:
                            break

            elif piece == 'r':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'r'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                                        if draw:
                                            current_score = -5
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                checkmate = True
                                                print('hahaha R')
                                            if not checkmate:
                                                if best_piece != 'P':
                                                  if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                    analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                  else:
                                                    analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                else:
                                                    if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                      analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                      analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 7 and best_piece == 'P':
                                                    board[target_row][target_col] = 'Q'
                                                current_score = score(board, 'b')
                                                board[best_row][best_col] = best_piece
                                                board[target_row][target_col] = captured
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'r')]
                                                    if best_piece != 'p':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                      else:
                                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                        else:
                                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'r'))
                                            else:
                                                board[row][col] = 'r'
                                                board[new_row][new_col] = captured_piece
                                                checkmate = False
                                                return '2', '2', '2', '2', '2', '2', False
                                board[row][col] = 'r'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                break
                        else:
                            break

            elif piece == 'q':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'q'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = -5
                                    if current_score > previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                        best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                                        if draw:
                                            current_score = -5
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, piece)]
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, piece))
                                        else:
                                            if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                                checkmate = True
                                                print('hahaha Q')
                                            if not checkmate:
                                                board[best_row][best_col] = '0'
                                                board[target_row][target_col] = best_piece
                                                if target_row == 7 and best_piece == 'P':
                                                    board[target_row][target_col] = 'Q'
                                                current_score = score(board, 'b')
                                                board[best_row][best_col] = best_piece
                                                board[target_row][target_col] = captured
                                                if current_score > previous_score:
                                                    previous_score = current_score
                                                    best_moves = [(row, col, new_row, new_col, 'q')]
                                                    if best_piece != 'P':
                                                      if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                        analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                      else:
                                                        analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                        if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                          analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                        else:
                                                          analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                                elif current_score == previous_score:
                                                    best_moves.append((row, col, new_row, new_col, 'q'))
                                            else:
                                                board[row][col] = 'q'
                                                board[new_row][new_col] = captured_piece
                                                checkmate = False
                                                return '2', '2', '2', '2', '2', '2', False
                                board[row][col] = 'q'
                                board[new_row][new_col] = captured_piece
                                checkmate = False
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] in {'P', 'N', 'B', 'R', 'Q'}:
                                break
                        else:
                            break

            elif piece == 'k':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'P', 'N', 'B', 'R', 'Q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'k'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = -5
                                if current_score > previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                black_king_row, black_king_col = find_king(board, 'b')
                                if not is_king_in_check(board, black_king_row, black_king_col, 'b'):
                                    best_row, best_col, target_row, target_col, best_piece, captured, draw = best_move2_black(board)
                                    if draw:
                                        current_score = -5
                                        if current_score > previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, piece)]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, piece))
                                    else:
                                        if best_row == best_col == target_row == target_col == best_piece == captured == '1':
                                            checkmate = True
                                        if not checkmate:
                                            board[best_row][best_col] = '0'
                                            board[target_row][target_col] = best_piece
                                            if target_row == 7 and best_piece == 'P':
                                                board[target_row][target_col] = 'Q'
                                            current_score = score(board, 'b')
                                            board[best_row][best_col] = best_piece
                                            board[target_row][target_col] = captured
                                            if current_score > previous_score:
                                                previous_score = current_score
                                                best_moves = [(row, col, new_row, new_col, 'k')]
                                                if best_piece != 'P':
                                                  if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                    analized = ('(' + best_piece.upper() + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                  else:
                                                    analized = ('(' + best_piece.upper() + indices_to_pos(target_row, target_col) + ')')
                                                else:
                                                    if board[target_row][target_col] in {'p', 'n', 'b', 'r', 'q'}:
                                                      analized = ('(' + indices_to_pos_col(best_col) + 'x' + indices_to_pos(target_row, target_col) + ')')
                                                    else:
                                                      analized = ('(' + indices_to_pos(target_row, target_col) + ')')
                                            elif current_score == previous_score:
                                                best_moves.append((row, col, new_row, new_col, 'k'))
                                        else:
                                            board[row][col] = 'k'
                                            board[new_row][new_col] = captured_piece
                                            checkmate = False
                                            black_king_row, black_king_col = find_king(board, 'b')
                                            return '2', '2', '2', '2', '2', '2', False
                            board[row][col] = 'k'
                            board[new_row][new_col] = captured_piece
                            checkmate = False
                            black_king_row, black_king_col = find_king(board, 'b')
                            position_history[pos_hash] -= 1

    if best_moves:
        best_move = random.choice(best_moves)
        best_row, best_col, target_row, target_col, best_piece = best_move
        captured_piece = board[target_row][target_col]
        pos_hash = ''.join(''.join(row) for row in board)
        position_history[pos_hash] += 1
        if position_history[pos_hash] >= 3:
            draw = True
        else:
            draw = False
        position_history[pos_hash] -= 1
        return best_row, best_col, target_row, target_col, best_piece, captured_piece, draw
    else:
        return '1', '1', '1', '1', '1', '1', False

def best_move2_black(board):
    white_king_row, white_king_col = find_king(board, 'w')
    promotion = False
    previous_score = 6000
    best_moves = []
    rows = list(range(8))
    cols = list(range(8))

    for row in rows:
        for col in cols:
            piece = board[row][col]
            if piece == 'P':
                directions = [1, 2, 3, 4]
                random.shuffle(directions)
                for direction in directions:
                    if direction == 1 and row == 1 and board[row+2][col] == '0' and board[row+1][col] == '0':
                        board[row][col] = '0'
                        board[row+2][col] = 'P'
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            current_score = score(board, 'b')
                            if current_score < previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row+2, col, 'P')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row+2, col, 'P'))
                        board[row][col] = 'P'
                        board[row+2][col] = '0'

                    elif direction == 2 and row < 7 and board[row+1][col] == '0':
                        board[row][col] = '0'
                        board[row+1][col] = 'P'
                        if row+1 == 7:
                            board[row+1][col] = 'Q'
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            current_score = score(board, 'b')
                            if current_score < previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row+1, col, 'P')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row+1, col, 'P'))
                        board[row][col] = 'P'
                        board[row+1][col] = '0'

                    elif direction == 3 and row < 7 and col > 0 and board[row+1][col-1] in {'p', 'n', 'b', 'r', 'q'}:
                        captured_piece = board[row+1][col-1]
                        board[row][col] = '0'
                        board[row+1][col-1] = 'P'
                        if row+1 == 7:
                            board[row+1][col-1] = 'Q'
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            current_score = score(board, 'b')
                            if current_score < previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row+1, col-1, 'P')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row+1, col-1, 'P'))
                        board[row][col] = 'P'
                        board[row+1][col-1] = captured_piece

                    elif direction == 4 and row < 7 and col < 7 and board[row+1][col+1] in {'p', 'n', 'b', 'r', 'q'}:
                        captured_piece = board[row+1][col+1]
                        board[row][col] = '0'
                        board[row+1][col+1] = 'P'
                        if row+1 == 7:
                            board[row+1][col+1] = 'Q'
                            promotion = True
                        if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                            current_score = score(board, 'b')
                            if current_score < previous_score:
                                previous_score = current_score
                                best_moves = [(row, col, row+1, col+1, 'P')]
                            elif current_score == previous_score:
                                best_moves.append((row, col, row+1, col+1, 'P'))
                        board[row][col] = 'P'
                        board[row+1][col+1] = captured_piece

            elif piece == 'N':
                directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'N'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = 5
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    current_score = score(board, 'b')
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, 'N')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, 'N'))
                            board[row][col] = 'N'
                            board[new_row][new_col] = captured_piece
                            position_history[pos_hash] -= 1

            elif piece == 'B':
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'B'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        current_score = score(board, 'b')
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'B')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'B'))
                                board[row][col] = 'B'
                                board[new_row][new_col] = captured_piece
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                break
                        else:
                            break

            elif piece == 'R':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'R'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        current_score = score(board, 'b')
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'R')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'R'))
                                board[row][col] = 'R'
                                board[new_row][new_col] = captured_piece
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                break
                        else:
                            break

            elif piece == 'Q':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    for i in range(1, 8):
                        new_row = row + i * direction[0]
                        new_col = col + i * direction[1]
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                                captured_piece = board[new_row][new_col]
                                board[row][col] = '0'
                                board[new_row][new_col] = 'Q'
                                pos_hash = ''.join(''.join(row) for row in board)
                                position_history[pos_hash] += 1
                                if position_history[pos_hash] >= 3:
                                    current_score = 5
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, piece)]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, piece))
                                else:
                                    if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                        current_score = score(board, 'b')
                                        if current_score < previous_score:
                                            previous_score = current_score
                                            best_moves = [(row, col, new_row, new_col, 'Q')]
                                        elif current_score == previous_score:
                                            best_moves.append((row, col, new_row, new_col, 'Q'))
                                board[row][col] = 'Q'
                                board[new_row][new_col] = captured_piece
                                position_history[pos_hash] -= 1
                            else:
                                break
                            if board[new_row][new_col] in {'p', 'n', 'b', 'r', 'q'}:
                                break
                        else:
                            break

            elif piece == 'K':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board[new_row][new_col] in {'0', 'p', 'n', 'b', 'r', 'q'}:
                            captured_piece = board[new_row][new_col]
                            board[row][col] = '0'
                            board[new_row][new_col] = 'K'
                            pos_hash = ''.join(''.join(row) for row in board)
                            position_history[pos_hash] += 1
                            if position_history[pos_hash] >= 3:
                                current_score = 5
                                if current_score < previous_score:
                                    previous_score = current_score
                                    best_moves = [(row, col, new_row, new_col, piece)]
                                elif current_score == previous_score:
                                    best_moves.append((row, col, new_row, new_col, piece))
                            else:
                                white_king_row, white_king_col = find_king(board, 'w')
                                if not is_king_in_check(board, white_king_row, white_king_col, 'w'):
                                    current_score = score(board, 'b')
                                    if current_score < previous_score:
                                        previous_score = current_score
                                        best_moves = [(row, col, new_row, new_col, 'K')]
                                    elif current_score == previous_score:
                                        best_moves.append((row, col, new_row, new_col, 'K'))
                            board[row][col] = 'K'
                            board[new_row][new_col] = captured_piece
                            white_king_row, white_king_col = find_king(board, 'w')
                            position_history[pos_hash] -= 1

    if best_moves:
        best_move = random.choice(best_moves)
        best_row2, best_col2, target_row2, target_col2, best_piece2 = best_move
        captured_piece2 = board[target_row2][target_col2]
        pos_hash = ''.join(''.join(row) for row in board)
        position_history[pos_hash] += 1
        if position_history[pos_hash] >= 3:
            draw = True
        else:
            draw = False
        position_history[pos_hash] -= 1
        return best_row2, best_col2, target_row2, target_col2, best_piece2, captured_piece2, draw
    else:
        return '1', '1', '1', '1', '1', '1', False

def train(board):
    good_moves = []
    while True:
        piece = input('What piece: ')
        from_square = input('From what square: ').strip().lower()
        to_square = input('To what square: ').strip().lower()
        captured_piece = input('Capturing what piece: ')
        from_row, from_col = pos_to_indices(from_square)
        to_row, to_col = pos_to_indices(to_square)
        good_moves.append((from_row, from_col, to_row, to_col, piece, captured_piece))
        if input('Continue or end? ') == 'end':
            break
    print(good_moves)

def game_loop():
    answer = input('Play or Score? ')
    if answer.lower() in {'t', 'train', 'not play'}:
        good_moves = train(board)
    elif answer.lower() in {'score', 's'}:
        print_board(board)
        current_score = score(board, 'w')
        print(current_score)
    elif answer == 'k':
        game_moves = ['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6']
        output = print_moves('b', 3, game_moves)
        output = output.strip(' ')
        print('[' + output + ']')
    else:
        answer2 = input('Do you want to play as white, black, or bots?')
        start_timer()
        if answer2 in {'random', 'r'}:
            number = random.randint(1, 2)
            if number == 2:
                answer2 = 'w'
        if answer2 in {'white', 'w'}:
            print_board(board)
            for _ in range(300):
                white_king_row, white_king_col = find_king(board, 'w')
                black_king_row, black_king_col = find_king(board, 'b')
                if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                    print("White king is in check!")
                    best_move_black(board, 'False', 'false')
                elif is_king_in_check(board, black_king_row, black_king_col, 'b'):
                    print("Black king is in check!")
                    players_turn_white(board)
                else:
                    players_turn_white(board)
        elif answer2 in {'bots', 'bot', 'b'}:
            for _ in range(300):
                white_king_row, white_king_col = find_king(board, 'w')
                black_king_row, black_king_col = find_king(board, 'b')
                if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                    print("White king is in check!")
                elif is_king_in_check(board, black_king_row, black_king_col, 'b'):
                    print("Black king is in check!")
                    best_move_function(board, 'True', 'none', 'false')
                else:
                    best_move_function(board, 'True', 'none', 'false')
        else:
            for _ in range(300):
                white_king_row, white_king_col = find_king(board, 'w')
                black_king_row, black_king_col = find_king(board, 'b')
                if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                    print("White king is in check!")
                    players_turn(board)
                elif is_king_in_check(board, black_king_row, black_king_col, 'b'):
                    print("Black king is in check!")
                    best_move_function(board, 'False', 'none', 'false')
                else:
                    best_move_function(board, 'False', 'none', 'false')
def game_loop2():
    answer2 = 'w'
    start_timer()
    if answer2 in {'random', 'r'}:
        number = random.randint(1, 2)
        if number == 2:
            answer2 = 'w'
    if answer2 in {'white', 'w'}:
        print_board(board)
        for _ in range(300):
            white_king_row, white_king_col = find_king(board, 'w')
            black_king_row, black_king_col = find_king(board, 'b')
            if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                print("White king is in check!")
                best_move_black(board, 'False', 'false')
            elif is_king_in_check(board, black_king_row, black_king_col, 'b'):
                print("Black king is in check!")
                players_turn_white(board)
            else:
                players_turn_white(board)
    else:
        for _ in range(300):
            white_king_row, white_king_col = find_king(board, 'w')
            black_king_row, black_king_col = find_king(board, 'b')
            if is_king_in_check(board, white_king_row, white_king_col, 'w'):
                print("White king is in check!")
                players_turn(board)
            elif is_king_in_check(board, black_king_row, black_king_col, 'b'):
                print("Black king is in check!")
                best_move_function(board, 'False', 'none', 'false')
            else:
                best_move_function(board, 'False', 'none', 'false')
initialize_board()