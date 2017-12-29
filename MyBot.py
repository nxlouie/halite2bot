"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
import hlt  # Halite starter kit
import logging
import time

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("ClearForever")
# Then we print our start message to the logs
logging.info("Starting my ClearForever Bot!")


def main():
    # Stores ships that will never dock, but instead always fight
    hunt_mode_set = set()

    while True:
        # TURN START
        # Update the map for the new turn and get the latest version
        game_map = game.update_map()

        # Here we define the set of commands to be sent to the Halite engine at the end of the turn
        command_queue = []

        # Timer to make sure we don't time out
        start_time = time.time()

        # For every ship that I control
        for ship in game_map.get_me().all_ships():
            # make sure we aren't near the end of 2 second timeout
            cur_time = time.time()
            if cur_time - start_time > 1.8:
                break

            # If the ship is docked, skip the ship
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                continue

            # Determine entity distance
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            sorted_entities_by_distance = sorted(entities_by_distance)

            # Check for hunt mode
            if ship.id in hunt_mode_set:
                command = hunt(game_map, ship, entities_by_distance, sorted_entities_by_distance)
                if command:
                    command_queue.append(command)
                continue

            # If first non team entity seen is an enemy ship, put ship in hunt mode
            if check_to_hunt(game_map, entities_by_distance, sorted_entities_by_distance):
                hunt_mode_set.add(ship.id)
                command = hunt(game_map, ship, entities_by_distance, sorted_entities_by_distance)
                if command:
                    command_queue.append(command)
                continue

            # Settle to nearest planet
            command = settle(game_map, ship, entities_by_distance, sorted_entities_by_distance)
            if command:
                command_queue.append(command)

        # Send our set of commands to the Halite engine for this turn
        game.send_command_queue(command_queue)
        # TURN END
    # GAME END


# forever finds next enemy to kill
def hunt(game_map, ship, entities_by_distance, sorted_entities_by_distance):
    for distance in sorted_entities_by_distance:
        nearest_enemy_ship = next((next_ship for next_ship in entities_by_distance[distance]
                                   if isinstance(next_ship, hlt.entity.Ship)
                                   and next_ship.get_owner_id() != game_map.my_id), None)
        if nearest_enemy_ship:
            navigate_command = ship.navigate(
                ship.closest_point_to(nearest_enemy_ship),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False,
                max_corrections=90,
                angular_step=2,
            )
            return navigate_command
    return None


# Checks to see if the ship qualifies to turn into hunt mode
def check_to_hunt(game_map, entities_by_distance, sorted_entities_by_distance):
    for distance in sorted_entities_by_distance:
        next_entity = next((next_entity for next_entity in entities_by_distance[distance]
                            if next_entity.get_owner_id() != game_map.my_id), None)
        if next_entity:
            logging.info(str(next_entity.get_owner_id()) + ' ' + str(game_map.my_id))
            if isinstance(next_entity, hlt.entity.Ship):
                logging.info("check to hunt true")
                return True
            return False


# First phase of the bot
def settle(game_map, ship, entities_by_distance, sorted_entities_by_distance):
    for distance in sorted_entities_by_distance:
        nearest_planet = next((nearest_entity for nearest_entity in entities_by_distance[distance] if
                               isinstance(nearest_entity, hlt.entity.Planet)), None)
        if nearest_planet:
            # Disqualify planet if its my full planet
            if nearest_planet.get_owner_id() == game_map.my_id and nearest_planet.is_full():
                # Skip planet
                continue
            # If we can dock, We either sweep or dock
            if ship.can_dock(nearest_planet):
                if nearest_planet.get_owner_id() == game_map.my_id or not nearest_planet.is_owned():
                    return ship.dock(nearest_planet)
                else:
                    return attack_docked(game_map, ship, nearest_planet)

            else:
                # If we can't dock, we move towards the closest empty point near this planet
                # (by using closest_point_to) with constant speed.
                navigate_command = ship.navigate(
                    ship.closest_point_to(nearest_planet),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )
                return navigate_command
    return None


# navigate to planet's enemy
def attack_docked(game_map, ship, planet):
    all_ships = planet.all_docked_ships()
    target_ship = next(iter(all_ships or []), None)
    navigate_command = ship.navigate(
        ship.closest_point_to(target_ship),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False,
    )
    return navigate_command


main()
