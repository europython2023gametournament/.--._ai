# Player AI bot for game tournament
Implementation of 'EuroPython 2023 AI Game Tournament' champion bot by the one-man-team .--. (dot dash dash dot).

## Main (high level) ideas
Each base (both the starting one and those that are converted from ships) will get upgraded to either level 2 or level 3 (50-50% chance) before spawning any vehicles.

The starting base has different spawning rules then all the other bases. If anytime during the game the starting base gets destroyed, one of the remaining bases will take over its role (and its spawning rules).

Each base first spawns a tank that is travelling along the coastline (or at least attempts to - some literal corner cases may cause smaller problems). Whenever this tank gets destroyed, the base it came from (if still in play) will spawn another one doing the same.

Then a few other tanks are spawned, which are just randomly bouncing from coast to coast on the land. The original number of such tanks is 2 for the starting base, 1 for any other. These tanks might do detours if there is a base of an opponent _very_ close by - this might make them stuck if that base is actually on the other side of a small body of water. They don't have replacements being spawned if killed. 

In general the number of tanks is kept low, so the precious crystals can be spent on more valuable vehicles.

Whether to spawn a ship or a jet once there are enough crystals, is based on random drawing. The starting base tends to spawn more ships (to create new bases, increasing the survival chances), while the other bases have a distribution that favors jets (which is the ultimate weapon considering its speed and all-terrain compatibility that allows easy control).

Ships also go on a straight line coast to coast, starting in a random direction. If they land close to another base of the team, they don't convert to base, but bounce back to a new random direction.

Jets start in a random direction too. If there are any of opponents' bases on the visible part of the map, each plane flies on a straight line to the one closest to it.

## Hic sunt dracones
Obviously this is not production level code quality - it is a result of trial and error approach during two sleepless nights. In order to find the Ballmer peak, some Czech beer might have been also consumed before these coding sessions, further improving the willingness to experiment - and the spaghetti architecture.

Some ideas, which did not make into the final model still have some traces. Although I would love to refactor the code, this task may easily and quickly sink on my to-do list.
