MOVE_LOOKUP = {"left":-1, "right": 1, "up": 1, "down":-1}

def get_next(current_head, next_move):
    """
    return the coordinate of the head if our snake goes that way
    """
    # Copy first
    future_head = current_head.copy()

    if next_move in ["left", "right"]:
        # X-axis
        future_head["x"] = current_head["x"] + MOVE_LOOKUP[next_move]
    elif next_move in ["up", "down"]:
        future_head["y"] = current_head["y"] + MOVE_LOOKUP[next_move]

    return future_head

def get_all_moves(coord):
    choices = ["left", "right", "up", "down"]
    return [get_next(coord, choice) for choice in choices]

def get_reverse(move):
    reverse_moves = {"left":"right","right":"left","up":"down","down":"up"}
    return reverse_moves[move]

def get_safe_moves(possible_moves, body, board, squadmates = None, my_snake = None):

    safe_moves = []
    
    for guess in possible_moves:
        guess_coord = get_next(body[0], guess)
        if avoid_walls(guess_coord, board["width"], board["height"]) and avoid_snakes(guess_coord, board["snakes"]): 
            safe_moves.append(guess)
        elif len(body) > 1 and guess_coord == body[-1] and guess_coord not in body[:-1]:
           # The tail is also a safe place to go... unless there is a non-tail segment there too
           safe_moves.append(guess)
        if squadmates and my_snake:
            for snake in squadmates:
                if guess_coord in snake["body"][1:] and guess_coord not in my_snake["body"][:-1]:
                    safe_moves.append(guess)
    return safe_moves

def avoid_walls(future_head, board_width, board_height):
    result = True

    x = int(future_head["x"])
    y = int(future_head["y"])

    if x < 0 or y < 0 or x >= board_width or y >= board_height:
        result = False

    return result

def avoid_gutter(future_head, board_width, board_height):
    result = True

    x = int(future_head["x"])
    y = int(future_head["y"])

    if x < 1 or y < 1 or x >= board_width - 1 or y >= board_height - 1:
        result = False
    return result

def avoid_snakes(future_head, snake_bodies):
    for snake in snake_bodies:
        if future_head in snake["body"][:-1]:
            return False
    return True

def avoid_consumption(future_head, snake_bodies, my_snake):
    if len(snake_bodies) < 2:
        return True

    my_length = my_snake["length"]
    for snake in snake_bodies:
        if snake == my_snake:
            continue
        if future_head in get_all_moves(snake["head"]) and future_head not in snake["body"][1:-1] and my_length <= snake["length"]:
            print(f'DANGER OF EATED {my_snake["head"]}->{future_head} by {snake["name"]}')
            return False
    return True

def avoid_food(future_head, food):
    return future_head not in food

def avoid_hazards(future_head, hazards):
    # Convenience method
    return not future_head in hazards

def get_minimum_moves(start_coord, targets):
    # This could probably be a lambda but I'm not that smart
    steps = []
    for coord in targets:
        steps.append(abs(coord["x"] - start_coord["x"]) + abs(coord["y"] - start_coord["y"]))
    return min(steps)

def get_closest_enemy_head_distance(head_coord, other_snakes):
    steps = [100]
    for snake in other_snakes:
        steps.append(abs(snake["head"]["x"] - head_coord["x"]) + abs(snake["head"]["y"] - head_coord["y"]))
    return min(steps)

def get_closest_enemy(head_coord, other_snakes):
    retval = []
    distance = get_closest_enemy_head_distance(head_coord, other_snakes)
    for snake in other_snakes:
        if abs(snake["head"]["x"] - head_coord["x"]) + abs(snake["head"]["y"] - head_coord["y"]) == distance:
            retval.append(snake)
    return retval

def get_body_segment_count(coord, move, snakes):
    retval = 0
    for snake in snakes:
        for segment in snake["body"]:
            if move == 'up' and segment['y'] > coord['y']:
                retval += 1
            elif move == 'down' and segment['y'] < coord['y']:
                retval += 1
            elif move == 'right' and segment['x'] > coord['x']:
                retval += 1
            elif move == 'left' and segment['x'] < coord['x']:
                retval += 1
    print(f'{move} body weight is {retval}')
    return retval

def get_future_head_positions(body, turns, board):
    turn = 0
    explores = {}
    explores[0] = [body[0]]
    while turn < turns:
        turn += 1
        explores[turn] = []
        for test in explores[turn-1]:
            next_paths = get_safe_moves(["left","right","up","down"],[test],board)
            for path in next_paths:
                explores[turn].append(get_next(test, path))

    return explores[turns]

def should_choose(moves, squad):
    if squad:
        return len(moves) >= 2
    else:
        return len(moves) == 2

def line_to_safety(direction, start, board):
    # either straight into a wall or into the safe zone
    retval = 0
    next_coord = get_next(start, direction)
    while next_coord in board["hazards"] and avoid_walls(next_coord, board["width"], board["height"]):
        next_coord = get_next(next_coord, direction)
        retval += 1
    if not avoid_walls(next_coord, board["width"], board["height"]):
        retval += max([board["width"], board["height"]]) + 1
    return retval

def steps_to_safety(direction, start, board):
    # Trace a path to safety
    escape_route = [get_next(start, direction)]
    next_coord = escape_route[0]
    extra_cost = 0
    while next_coord in board["hazards"] and avoid_walls(next_coord, board["width"], board["height"]) and extra_cost == 0 and len(escape_route) < 100:
        costs = {}
        # Really need to choose a new direction now
        for choice in get_safe_moves([move for move in ["up", "down", "left", "right"] if move != get_reverse(direction)], escape_route, board):
            costs[choice] = line_to_safety(choice, get_next(next_coord, choice), board)
        if costs:
            bestway = min(costs.values())
            for choice in costs.keys():
                if costs[choice] == bestway:
                    direction = choice
        next_coord = get_next(next_coord, direction)
        if next_coord in escape_route:
            extra_cost += len(escape_route)
        else:
            escape_route.insert(0, next_coord)
    if not avoid_walls(next_coord, board["width"], board["height"]):
        extra_cost += max([board["width"], board["height"]])
#    print(f'in hazard, overhead to explore {direction} is {extra_cost}, path is {escape_route}')
    return len(escape_route) + extra_cost

def at_wall(coord, board):
    return coord["x"] == 0 or coord["y"] == 0 or coord["x"] == board["width"] - 1 or coord["y"] == board["height"] - 1

def first_three_segments_straight(body):
    return body[0]['x'] == body[2]['x'] or body[0]['y'] == body[2]['y']

def avoid_crowd(moves, enemy_snakes, my_snake):
    crowd_cost = {}
    
    # Perhaps there's a clever way to create a dictionary of functions, but I want to be able to read this tomorrow
    if 'up' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['y'] > my_snake['head']['y']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['up'] = len(others) + (len(threats) * 3)
    if 'down' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['y'] < my_snake['head']['y']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['down'] = len(others) + (len(threats) * 3)
    if 'left' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['x'] < my_snake['head']['x']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['left'] = len(others) + (len(threats) * 3)
    if 'right' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['x'] > my_snake['head']['x']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['right'] = len(others) + (len(threats) * 3)
    
    print(f'Crowd control: {crowd_cost}')
    return [move for move in moves if crowd_cost[move] == min(crowd_cost.values())]

def is_drafting(my_snake, other_snake):
    neck = my_snake["body"][1]
    if abs(other_snake["head"]["x"] - my_snake["head"]["x"]) > 1:
        return False
    if abs(other_snake["head"]["y"] - my_snake["head"]["y"]) > 1:
        return False
    return other_snake["head"]["x"] == neck["x"] or other_snake["head"]["y"] == neck["y"]

def continue_draft(moves, my_snake, other_snake):
    retval = []
    neck = my_snake["body"][1]
    if other_snake["head"]["x"] < my_snake["head"]["x"] and neck["x"] == other_snake["head"]["x"]:
        retval.append("right")
    if other_snake["head"]["x"] > my_snake["head"]["x"] and neck["x"] == other_snake["head"]["x"]:
        retval.append("left")
    if other_snake["head"]["y"] < my_snake["head"]["y"] and neck["y"] == other_snake["head"]["y"]:
        retval.append("up")
    if other_snake["head"]["y"] > my_snake["head"]["y"] and neck["y"] == other_snake["head"]["y"]:
        retval.append("down")
    return [move for move in moves if move in retval]

def get_excluded_path(path, moves, origin):
    # return cells that are blocked if a snake at the origin moves in any of the specified directions
    retval = []
    for coord in path:
        # is this coordinate not blocked by the other movement?
        if "up" in moves and coord['y'] < origin['y']:
            retval.append(coord)
        if "down" in moves and coord['y'] > origin['y'] and coord not in retval:
            retval.append(coord)
        if "right" in moves and coord['x'] < origin['x'] and coord not in retval:
            retval.append(coord)
        if "left" in moves and coord['x'] > origin['x'] and coord not in retval:
            retval.append(coord)
    return retval

def retrace_path(path, origin):
    # Ensure that we have a contiguous path through a set of cells
    retval = []
    next_moves = [move for move in get_all_moves(origin) if move in path]
    while next_moves:
        step = []
        for coord in next_moves:
            retval.append(coord)
            step += [move for move in get_all_moves(coord) if move in path and move not in step and move not in retval]
        next_moves = step
    return retval

def get_moves_toward(start_coord, end_coord):
    """ Return an array of snake moves that will direct something at start_coord towards end_coord. """
    retval = []
    if end_coord['x'] > start_coord['x']:
        retval.append('right')
    if end_coord['x'] < start_coord['x']:
        retval.append('left')
    if end_coord['y'] > start_coord['y']:
        retval.append('up')
    if end_coord['y'] < start_coord['y']:
        retval.append('down')
    return retval

def get_smart_moves(possible_moves, body, board, my_snake):
    # the main function of the snake - choose the best move based on the information available
    smart_moves = []
    food_avoid = []
    enemy_snakes = []
    squadmates = []
    all_moves = ["up", "down", "left", "right"]
    other_snakes = [snake for snake in board["snakes"] if snake["id"] != my_snake["id"]]
    if my_snake.get("squad"):
        enemy_snakes = [snake for snake in other_snakes if snake["squad"] != my_snake["squad"]]
        squadmates = [snake for snake in other_snakes if snake["squad"] == my_snake["squad"]]
    else:
        enemy_snakes = other_snakes
    safe_moves = get_safe_moves(possible_moves, body, board, squadmates, my_snake)

    tron_mode = len(board['food']) + sum([snake['length'] for snake in board['snakes']]) >= board['width'] * board['height']

    # enemy_threats = [snake for snake in other_snakes if snake["length"] >= my_sname["length"]]
    eating_snakes = []
    gutter_snakes = []
    gutter_food = []
    safe_coords = {}
    head_distance = {}
    next_coords = {}
    choke_moves = {}
    squeeze_offset = {}
    collision_threats = []
    collision_targets = {}

    hunger_threshold = 35
    enemy_offset = {}

    for snake in enemy_snakes:
        if any(eat_coord in get_all_moves(snake['head']) for eat_coord in board['food']):
            print(f"{snake['name']} could eat")
            enemy_offset[snake['id']] = 1
        else:
            enemy_offset[snake['id']] = 0

    # We know these directions are safe... for now
    for guess in safe_moves:
        safe_coords[guess] = []
        guess_coord = get_next(body[0], guess)
        next_coords[guess] = guess_coord
        explore_edge = [guess_coord]
        all_coords = [guess_coord]
        next_explore = []
        # start at 1 because snakes move forward
        explore_step = 1
        eating_offset = 0
        squeeze_offset[guess] = 0

        for segments in body[:-1]:
            next_explore.clear()
            explore_step += 1
            if len(explore_edge) == 1 and explore_step > 1:
                squeeze_offset[guess] += 1
            print(f"Step {explore_step} exploring {explore_edge}")
            for explore in explore_edge:
                if explore in board['food']:
                    eating_offset += 1
                safe = get_safe_moves(all_moves, [explore], board, squadmates, my_snake)
                for safe_move in safe:
                    guess_coord_next = get_next(explore, safe_move)
                    if guess_coord_next not in all_coords:
                        next_explore.append(guess_coord_next)
                
                if not tron_mode:
                    # Consider how other snakes move
                    # TODO: Handle when other snakes could eat
                    snake_collide = [coord for coord in get_all_moves(explore) if not avoid_snakes(coord, enemy_snakes)]
                    if snake_collide:
                        for coord in snake_collide:
                            for snake in enemy_snakes:
                                if coord in snake["body"] and snake["body"].index(coord) + explore_step >= len(snake["body"]) + enemy_offset[snake['id']]:
                                    start_segment = snake["body"].index(coord)
                                    print(f'we intersect with {snake["name"]} at position {start_segment} step {explore_step}')
                                    all_coords += snake["body"][start_segment:]
                                elif coord == snake['head']: # and snake['length'] >= my_snake['length']:
                                    print(f"Bumping heads with {snake['name']} at step {explore_step} {explore_edge}")
                                    if snake['length'] >= my_snake['length']:
                                        collision_threats.append(snake['id'])
                                    elif snake['id'] not in collision_targets:
                                        collision_targets[snake['id']] = explore_step
                                    elif collision_targets[snake['id']] > explore_step:
                                        collision_targets[snake['id']] = explore_step

                                    unexplored = [coord for coord in explore_edge if coord not in all_coords]
                                    print(f"safe: {safe} {next_explore}")
                                    if explore_step > 2 and (len(explore_edge) == 1 or len(next_explore) <= 1) and not guess in choke_moves.keys():
                                        print(f"{guess} leads to a possible choke point")
                                        choke_moves[guess] = explore_step

                    self_collide = [coord for coord in get_all_moves(explore) if not avoid_snakes(coord, [my_snake])]
                    if self_collide:
                        for coord in self_collide:
                            print(f"I collide with myself at {coord}, segment {my_snake['body'].index(coord)}")
                            if coord in my_snake['body'] and my_snake['body'].index(coord) + explore_step >= len(my_snake['body']) + eating_offset:
                                start_segment = my_snake["body"].index(coord)
                                all_coords += my_snake['body'][start_segment:]
                all_coords += next_explore.copy() 
                all_coords.append(explore)
            explore_edge = next_explore.copy()

        safe_coords[guess] += list(map(dict, frozenset(frozenset(i.items()) for i in all_coords)))

    for path in safe_coords.keys():
        guess_coord = get_next(body[0], path)
        print(f'considering {path}, {len(safe_coords[path])} safe coords, {len(body)} body length, consumption {avoid_consumption(guess_coord, board["snakes"], my_snake)} hazards {avoid_hazards(guess_coord, board["hazards"])}')
        #print(f"{safe_coords[path]}")
        # TODO: if this gives us one run-away move, consider the opposite, unpredictable move
        if ((len(safe_coords[path]) >= len(body) or 
                any(snake["body"][-1] in safe_coords[path] for snake in board["snakes"])) and 
                avoid_consumption(guess_coord, board["snakes"], my_snake) and
                avoid_hazards(guess_coord, board["hazards"])
            ):
            print(f"{path} is a first choice smart move")
            smart_moves.append(path)
    
    # check if other snakes are being forced to move into a square we can occupy.  
    # We don't need to determine if this is a safe move since we can use the freed-up
    # space for future moves
    for snake in other_snakes:
        enemy_options = get_safe_moves(all_moves, snake['body'], board)
        if len(enemy_options) == 1:
            enemy_must = get_next(snake['body'][0], enemy_options[0])
            if snake['length'] < my_snake['length'] and enemy_must in next_coords.values():
                for move, coord in next_coords.items():
                    if coord == enemy_must:
                        print(f'Eating {snake["name"]} by going {move} to {coord}')
                        eating_snakes.append(move)
            elif avoid_gutter(enemy_must, board['width'], board['height']):
                gutter_snakes.append(snake)
        elif len(enemy_options) == 2:
            # TODO: consider if this will corner us - do what-if when enemy chooses to avoid us
            print(f'{snake["name"]} has two exits {enemy_options}')
            for enemy_move in enemy_options:
                enemy_may = get_next(snake['body'][0], enemy_move)
                if snake['length'] < my_snake['length'] and enemy_may in next_coords.values():
                    for move, coord in next_coords.items():
                        if move in smart_moves and coord == enemy_may and len(get_safe_moves(all_moves, [coord], board)) > 0 and not at_wall(coord, board) and len(safe_coords[move]) > my_snake['length']:
                            print(f'Trying to eat {snake["name"]} by going {move}')
                            eating_snakes.append(move)
        if not eating_snakes and snake['id'] in collision_targets:
            print(f'{snake["name"]} could be def-eated, they are {collision_targets[snake["id"]]} away')
            collisions = {}
            min_turns = collision_targets[snake['id']] / 2
            steps_towards_enemy = get_moves_toward(my_snake['head'], snake['head'])
            if min_turns <= 4:
                enemy_possible_positions = get_future_head_positions(snake['body'], min_turns, board)
                for move, coord in next_coords.items():
                    move_targets = get_future_head_positions([coord], min_turns - 1, board)
                    collisions[move] = [coord for coord in move_targets if coord in enemy_possible_positions]
                print(f'collisions: {collisions}')
                best_approach = max(collisions, key= lambda x: len(collisions[x]))
                most_hits = max(len(collisions[x]) for x in collisions.keys())
                all_attack_moves = [x for x in collisions.keys() if len(collisions[x]) == most_hits]
                if len(all_attack_moves) > 1:
                    enemy_options = get_safe_moves(all_moves, snake['body'], board)
                    print(f"we go {all_attack_moves} they go {enemy_options}")
                    no_run = [move for move in all_attack_moves if move not in enemy_options]
                    if len(no_run) == 1:
                        best_approach = no_run[0]

                available_space = retrace_path(get_excluded_path(safe_coords[best_approach], steps_towards_enemy, snake['head']), get_next(my_snake['head'], best_approach))
                
                if best_approach in smart_moves:
                    if min_turns > 1 or (len(available_space) < my_snake['length'] and my_snake['body'][-1] not in available_space):
                        print(f'avoiding collision with {snake["name"]}')
                        print(f'{available_space}')
                        choke_moves[best_approach] = min_turns
                    elif best_approach not in choke_moves.keys():
                        print(f'attacking {snake["name"]} by going {best_approach}, next turn to collide.  fleeing means I squeeze into {len(available_space)} cells')
                        eating_snakes.append(best_approach)
                
    # reverse course in one special case
    if len(smart_moves) == 1 and collision_threats:
        for enemy_snake in [snake for snake in other_snakes if snake['id'] in collision_threats]:
            enemy_possible_positions = get_future_head_positions(enemy_snake['body'], 1, board)
            my_possible_positions = get_future_head_positions(my_snake['body'], 1, board)
            my_best = [coord for coord in my_possible_positions if coord not in enemy_possible_positions]
            shared = [coord for coord in my_possible_positions if coord in enemy_possible_positions]
            exclusion_zone = [move for move in get_safe_moves(all_moves, my_snake['body'], board) if move != get_reverse(smart_moves[0])]
            available_space = retrace_path(get_excluded_path(safe_coords[smart_moves[0]], exclusion_zone, enemy_snake['head']), get_next(my_snake['head'], smart_moves[0]))
            print(f"safe space: {len(safe_coords[smart_moves[0]])} available_space: {len(available_space)} exclusion zone: {exclusion_zone}")
            if len(shared) > 1 and len(my_best) == 1 and len(available_space) < my_snake['length'] and my_snake['body'][-1] not in available_space and my_best[0] == get_next(my_snake['head'], smart_moves[0]):
                print("run away!!")
                flee = get_reverse(smart_moves[0])
                if flee in safe_coords.keys() and (len(safe_coords[flee]) >= my_snake['length'] or any(snake['body'][:-1] in safe_coords[flee] for snake in board['snakes'])):
                    print(f'going {flee}!')
                    smart_moves = [flee]



    if choke_moves and smart_moves and len(smart_moves) > 1:
        print(f"choke avoid smart: {smart_moves}")
        print(f"choke avoid choke: {choke_moves}")
        print(f"choke avoid squeeze: {squeeze_offset}")
        # if it's more than half our body away, we can turn around before we get cut off
        # subtract two because both snakes could move closer together
        temp_chokes = [move for move in choke_moves.keys() if choke_moves[move] - squeeze_offset[move] < my_snake['length'] / 2]
        temp_moves = [move for move in smart_moves if move not in temp_chokes]
        if temp_moves:
            smart_moves = temp_moves
            print(f"Avoiding choke moves: {choke_moves}, now considering {smart_moves}")

    if not smart_moves and my_snake['head'] not in board['hazards']:
        # What if we try to chase our tail
        tail_neighbors = []
        tail_safe = get_safe_moves(all_moves, [body[-1]], board)
        for tail_safe_direction in tail_safe:
            tail_neighbors.append(get_next(body[-1], tail_safe_direction))

        for path in safe_coords.keys():
            if any(coord in safe_coords[path] for coord in tail_neighbors) or body[-1] in safe_coords[path]:
                print(f"Chasing tail {path}!")
                smart_moves.append(path)
        if not smart_moves:
            # tail might be right beside head
            for move in all_moves:
                test_move = get_next(body[0], move)
                if test_move == body[-1] and test_move not in body[:-1]:
                    smart_moves.append(move)
        if not smart_moves:
            # maybe an enemy tail?
            for move in safe_coords.keys():
                test_move = get_next(body[0], move)
                for snake in other_snakes:
                    if test_move == snake["body"][-1] and test_move not in body[:-1] and not any(coord in board["food"] for coord in get_all_moves(snake["body"][0])):
                        smart_moves.append(move)

    # Early hunger check to determine if the closest food is in a dangerous place
    if board['food'] and (my_snake["health"] < hunger_threshold or any(snake["length"] >= my_snake["length"] for snake in enemy_snakes)):
        gutter_food = [food for food in board['food'] if not avoid_gutter(food, board['width'], board['height']) and get_minimum_moves(my_snake['head'], [food]) < 2]

    # Avoid the gutter when we're longer than the board width
    if smart_moves and not gutter_snakes and not gutter_food and my_snake["length"] >= board["width"] - 2:
        gutter_avoid = [move for move in smart_moves if avoid_gutter(get_next(body[0], move), board["width"], board["height"])]
        if gutter_avoid:
            print(f"Avoiding gutter by going {gutter_avoid} instead of {smart_moves}")
            smart_moves = gutter_avoid
        
    # No clear path, try to fit ourselves in the longest one
    if safe_coords and not smart_moves and my_snake['head'] not in board ['hazards']:
        if other_snakes:
            # consider enemies
            escape_plan = {}
            for snake in other_snakes:
                # TODO: skip this is there's no path joining snakes
                if abs(my_snake['head']['x'] - snake['head']['x']) <= 2 and abs(my_snake['head']['y'] - snake['head']['y']) <= 2:
                    for move in safe_coords.keys():
                        escape_plan[move] = len(get_safe_moves(all_moves, [get_next(my_snake['head'], move)], board))
            if escape_plan:
                for move in escape_plan.keys():
                    if escape_plan[move] == max(escape_plan.values()) and move not in smart_moves:
                        print(f'going {move}, there are {escape_plan[move]} options')
                        smart_moves.append(move)
        if not smart_moves:
            # TODO: find the longest contiguous path in the safe zones to decide which way to squeeze
            squeeze_move = max(safe_coords, key= lambda x: len(safe_coords[x]))
            if len(safe_coords[squeeze_move]) > 2 and avoid_consumption(get_next(body[0], squeeze_move), board["snakes"], my_snake):
                print(f'squeezing into {squeeze_move} {safe_coords}')
                smart_moves.append(squeeze_move)



    # Seek food if there are other snakes porentially larger than us, or if health is low
    if len(smart_moves) > 1 and board['food'] and not eating_snakes and (my_snake["health"] < hunger_threshold or any(snake["length"] + len(board['food']) >= my_snake["length"] for snake in enemy_snakes)):
        print("Hungry!")
        food_choices = smart_moves 
        food_moves = {}
        closest_food = []
        greed_moves = []
        avoid_moves = []
        food_targets = [food for food in board["food"] if food not in board["hazards"]]
        print(f'food is {food_targets}')
        if not food_targets:
            food_targets = board["food"]
            print (f'no food outside hazards, now considering {food_targets}')

        if my_snake['health'] < hunger_threshold or my_snake["length"] < board['width']:
            food_choices = safe_coords.keys()

        for path in food_choices:
            if any(food in safe_coords[path] for food in food_targets):
                food_moves[path] = get_minimum_moves(get_next(body[0], path), [food for food in food_targets if food in safe_coords[path]])

        if food_moves:
            closest_food_distance = min(food_moves.values())
            food_considerations = other_snakes
            if squadmates and my_snake['name'] == min([snake['name'] for snake in board['snakes'] if snake['squad'] == my_snake['squad']]):
                print("short snake takes the food")
                food_considerations = enemy_snakes
            for path in food_moves.keys():
                if food_moves[path] <= closest_food_distance:
                    print(f"safe food towards {path} is {closest_food_distance} or less")
                    closest_food.append(path)
                    # see if we're the closest to the food
                    minimum_moves_threshold = 4
                    if not first_three_segments_straight(my_snake['body']):
                        minimum_moves_threshold = 6
                    for food in food_targets:
                        test_coord = get_next(my_snake["head"], path)
                        distance_to_me = get_minimum_moves(food, [test_coord])
                        if distance_to_me == food_moves[path]:
                            for snake in food_considerations:
                                if get_minimum_moves(food, [snake["head"]]) <= distance_to_me + 1 and get_minimum_moves(snake["head"], [test_coord]) < minimum_moves_threshold and snake["length"] > my_snake["length"]:
                                    # Don't
                                    print(f'Avoiding food towards {path} because {snake["name"]} is {get_minimum_moves(snake["head"], [test_coord])} away')
                                    avoid_moves.append(path)
                    print(f"avoid_moves {avoid_moves} smart_moves {smart_moves}")
                    if not (path in avoid_moves) and (path in smart_moves):
                        greed_moves.append(path)
        else:
            for path in food_choices:
                food_moves[path] = get_minimum_moves(get_next(body[0], path), food_targets)
            if food_moves:
                closest_food_distance = min(food_moves.values())
                for path in food_moves.keys():
                    if food_moves[path] <= closest_food_distance:
                        print(f"unsafe food towards {path} is {closest_food_distance} or less")
                        closest_food.append(path)
        
        if closest_food:

            if my_snake["health"] < hunger_threshold or greed_moves:
                print("Blinded by hunger or greed")
                hazard_avoid = [move for move in closest_food if get_next(body[0], move) not in board['hazards']]
                if hazard_avoid:
                    if greed_moves:
                        # should probably intersect hazard_avoid and greed_moves
                        print(f"choosing greed: {greed_moves}")
                        smart_moves = greed_moves
                    else:
                        print("but staying safe")
                        smart_moves = hazard_avoid
                else:
                    smart_moves = closest_food
            else:
                food_intersect = [move for move in smart_moves if move in closest_food and move not in avoid_moves] 
                print(f'Smart food is {food_intersect}')
                if food_intersect:
                    smart_moves = food_intersect
                elif avoid_moves:
                    smart_moves = [move for move in smart_moves if move not in avoid_moves]
                elif min(food_moves.values()) * 16 < my_snake["health"]: #and if path in hazard
                    # we're gonna make it, chief
                    hazard_pay = [move for move in closest_food if get_next(body[0], move) in board['hazards']]
                    if hazard_pay:
                        print('Diving into danger!')
                        smart_moves = hazard_pay
    else:
        # avoid food if it's there to avoid
        if len(smart_moves) > 1 and board["food"]:
            food_avoid = [move for move in smart_moves if get_next(body[0], move) not in board["food"]]
            print(f'Not hungry, avoiding food! moves are {food_avoid}')

    if board["hazards"] and my_snake["head"] in board["hazards"]:
        # Choose the path that takes us out of hazard
        if not smart_moves:
            print(f'no moves, using {safe_coords.keys()}')
            smart_moves = list(safe_coords.keys())
        if smart_moves and len(smart_moves) > 1:
            shortest_path = min([steps_to_safety(move, my_snake["head"], board) for move in smart_moves])
            smart_moves = [move for move in smart_moves if steps_to_safety(move, my_snake["head"], board) == shortest_path]
            print(f'smartly going {shortest_path} {smart_moves} steps to escape hazards')
    elif eating_snakes:
        smart_moves = eating_snakes
    elif food_avoid:
        smart_moves = food_avoid

    # tiebreakers when there are two paths, three in squads.  Skip if begin of game and we're short
    # TODO: add alternate branch if we're beside food and that food would make us larger than nearest threat
    if not eating_snakes and len(board['snakes']) > 1 and should_choose(smart_moves, my_snake.get("squad")) and my_snake['length'] > 3:
        body_weight = {}
        for move in smart_moves:
            next_coord = get_next(body[0], move)
            head_distance[move] = get_closest_enemy_head_distance(next_coord, [snake for snake in enemy_snakes if snake['length'] >= my_snake['length']])
            body_weight[move] = get_body_segment_count(next_coord, move, board['snakes'])

        if min(head_distance.values()) <= 3:
            if at_wall(my_snake["head"], board) and not at_wall(my_snake["body"][1], board):
                if board["hazards"]:
                    hazard_avoid = [move for move in smart_moves if not any(coord in board["hazards"] for coord in safe_coords[move])]
                    if hazard_avoid:
                        smart_moves = hazard_avoid
                        print(f'avoiding hazards {hazard_avoid}')
                if len(smart_moves) > 1:
                    smart_moves = avoid_crowd(smart_moves, enemy_snakes, my_snake)
            else:
                enemy_threats = get_closest_enemy(my_snake["head"], [snake for snake in other_snakes if snake['length'] > my_snake['length']])
                if len(enemy_threats) == 1 and is_drafting(my_snake, enemy_threats[0]):
                    # Try to push enemy into wall, hopefully corner
                    eating_snakes = continue_draft(smart_moves, my_snake, enemy_threats[0])
                    print(f'Drafting {enemy_threats[0]["name"]} {smart_moves}')
                elif any(snake['id'] in collision_threats for snake in enemy_threats):
                    print(f"enemy threats: {enemy_threats}")
                    if len(smart_moves) > 1:
                        smart_moves = [move for move in smart_moves if head_distance[move] == max(head_distance.values())]
                        print(f'choosing {smart_moves} to avoid heads {head_distance}')
                    if len(smart_moves) > 1 and at_wall(my_snake["head"], board):
                        smart_moves = [move for move in smart_moves if not at_wall(get_next(body[0], move), board)]
                        print(f'choosing {smart_moves} to bump self off wall')
                    if len(smart_moves) > 1:
                        escape_plan = {}
                        for move in smart_moves:
                            escape_plan[move] = len(get_safe_moves(all_moves, [get_next(my_snake['head'], move)], board))
                        smart_moves = [move for move in escape_plan.keys() if escape_plan[move] == max(escape_plan.values())]
                        print(f'choosing {smart_moves} because there are {max(escape_plan.values())} ways out')
                    if len(smart_moves) > 1:
                        smart_moves = [move for move in smart_moves if body_weight[move] == min(body_weight.values())]
                        print(f'choosing {smart_moves} to avoid bodies {body_weight}')


    return smart_moves

