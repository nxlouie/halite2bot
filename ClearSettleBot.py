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
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("ClearSettleBot")
# Then we print our start message to the logs
logging.info("Starting my ClearSettleBot game!")


def main():
    while True:
        # TURN START
        # Update the map for the new turn and get the latest version
        game_map = game.update_map()

        # Here we define the set of commands to be sent to the Halite engine at the end of the turn
        command_queue = []
        # For every ship that I control
        for ship in game_map.get_me().all_ships():
            # If the ship is docked
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship
                continue
            command = settle(game_map, ship)
            if command:
                command_queue.append(command)

        # Send our set of commands to the Halite engine for this turn
        game.send_command_queue(command_queue)
        # TURN END
    # GAME END


# First phase of the bot
def settle(game_map, ship):
    # Determine entity distance
    entities_by_distance = game_map.nearby_entities_by_distance(ship)
    sorted_entities_by_distance = sorted(entities_by_distance)
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
