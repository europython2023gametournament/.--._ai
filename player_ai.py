# SPDX-License-Identifier: BSD-3-Clause

from math import atan2, pi, inf
import numpy as np
from supremacy.game_map import MapView

from supremacy.vehicles import Tank

# This is your team name
CREATOR = "dot dash dash dot"
PLANE_BIRTH_RATE = 0.6

class Pos:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y
    
    # @x.setter
    # def x(self, x):
    #     self.x = x

    # @y.setter
    # def y(self, y):
    #     self.y = y

D = 40
SCOUTING_OFFSETS = [Pos(0,0)]
for j in range(200):
    SCOUTING_OFFSETS.append(Pos((j+1)*D,-j*D))
    SCOUTING_OFFSETS.append(Pos((j+1)*D,(j+1)*D))
    SCOUTING_OFFSETS.append(Pos(-(j+1)*D,(j+1)*D))
    SCOUTING_OFFSETS.append(Pos(-(j+1)*D,-(j+1)*D))
                    # Pos(D,0),    Pos(D,D),     Pos(-D,D),     Pos(-D,-D),
                    # Pos(2*D,-D), Pos(2*D,2*D), Pos(-2*D,2*D), Pos(-2*D,-2*D)]

def calc_heading(current_pos, target_pos):
    return atan2(target_pos.y - current_pos[1], target_pos.x - current_pos[0]) * 180 / pi

def close(pos1, pos2):
    return abs(pos1[0]-pos2.x)+abs(pos1[1]-pos2.y) < 3

def extract_edges(view):
    edge_length = len(view)
    # print(len(view), len(view[0]))
    radius = (edge_length - 1)//2
    edge = {}
    for x in range(edge_length):
        edge[atan2(0-radius,x-radius)] = view[0][x]
        edge[atan2(edge_length-1-radius,x-radius)] = view[edge_length-1][x]
        edge[atan2(x-radius,0-radius)] = view[x][0]
        edge[atan2(x-radius,edge_length-1-radius)] = view[x][edge_length-1]
    # print(view)
    # print(edge)
    return sorted([(phi, value) for phi, value in edge.items()])
    # exit()

# This is the AI bot that will be instantiated for the competition
class PlayerAi:
    def __init__(self):
        self.team = CREATOR  # Mandatory attribute

        # Record the previous positions of all my vehicles
        self.previous_positions = {}
        # Record the number of tanks and ships I have at each base
        self.ntanks = {}
        self.nships = {}
        self.basetanks = {}
        self.baseships = {}
        self.main_base = None
        self.scout = None
        self.tank_scouts = {}
        self.targets_by_hunter = {}
        self.orphan_targets = set()
        self.bases_for_planes = set()
        self.base_max_mines = {}

    def run(self, t: float, dt: float, info: dict, game_map: np.ndarray):
        """
        This is the main function that will be called by the game engine.

        Parameters
        ----------
        t : float
            The current time in seconds.
        dt : float
            The time step in seconds.
        info : dict
            A dictionary containing all the information about the game.
            The structure is as follows:
            {
                "team_name_1": {
                    "bases": [base_1, base_2, ...],
                    "tanks": [tank_1, tank_2, ...],
                    "ships": [ship_1, ship_2, ...],
                    "jets": [jet_1, jet_2, ...],
                },
                "team_name_2": {
                    ...
                },
                ...
            }
        game_map : np.ndarray
            A 2D numpy array containing the game map.
            1 means land, 0 means water, -1 means no info.
        """

        # Get information about my team
        myinfo = info[self.team]
############33
        # print(self.scout)
        # if "jets" in myinfo:
        #     pass
        #     # print("jetids")
        #     # print([jet.uid for jet in myinfo["jets"]])
        # if ("jets" not in myinfo) or (self.scout not in [jet.uid for jet in myinfo["jets"]]):
        #     self.scout = None
        # if self.scout is not None:
        #     scout_jet = [jet for jet in myinfo["jets"] if jet.uid==self.scout][0]
        #     # print(scout_jet.position)
        #     if close(scout_jet.position, self.scout_positions[1]):
        #         self.scout_positions.pop(1)
        #         scout_jet.set_heading(calc_heading(scout_jet.position, self.scout_positions[1]))
        allmytanks = {tank.uid for tank in myinfo["tanks"]} if "tanks" in myinfo else set()
        for base in self.basetanks.keys():
            self.basetanks[base] = self.basetanks[base].intersection(allmytanks)
        allmyships = {ship.uid for ship in myinfo["ships"]} if "ships" in myinfo else set()
        for base in self.baseships.keys():
            self.baseships[base] = self.baseships[base].intersection(allmyships)
        alloppsbases = set()
        for team in info:
            if team != self.team:
                alloppsbases.update({base.uid for base in info[team]["bases"]} if "bases" in info[team] else set())
        allopsbasecoords = set()
        for team in info:
            if team != self.team and "bases" in info[team]:
                for base in info[team]["bases"]:
                    if base.uid in alloppsbases:
                        allopsbasecoords.add((base.x, base.y))
        self.orphan_targets = allopsbasecoords        
        # print("HERE"+"!"*30)
        # print(self.orphan_targets)
        # self.orphan_targets = self.orphan_targets.union(alloppsbases)
        # print(self.orphan_targets)
        if "tanks" in myinfo:
            for tank_scout_uid in self.tank_scouts.values():
                try:
                    tank_scout = [tank for tank in myinfo["tanks"] if tank.uid==tank_scout_uid][0]
                    # print(tank_scout_uid)
                    x,y = tank_scout._data['x'],tank_scout._data['y']
                    view_d = 7
                    # view_orig = MapView(game_map).view(x=x, y=y, dx=view_d, dy=view_d)
                    view = np.take(np.take(game_map, range(int(y)-view_d, int(y)+view_d+1), axis=0, mode='wrap'), range(int(x)-view_d, int(x)+view_d+1), axis=1, mode='wrap')
                    edges = extract_edges(view)
                    land_borders = []
                    for (phi1, cell1), (phi2, cell2) in zip(edges+edges[:1],edges[-1:]+edges):
                        if cell2==1 and cell1==0:
                            land_borders.append(phi2*180/pi)
                    current_heading = tank_scout._data['heading']
                    if len(land_borders) > 0:
                        optimal_landborder = None
                        optimal_angle_difference = inf
                        for land_border in land_borders:
                            a = 180-abs((land_border - current_heading)%360-180)
                            if a < optimal_angle_difference:
                                optimal_angle_difference = a
                                optimal_landborder = land_border
                            # print(a)
                        # exit()
                        tank_scout.set_heading((optimal_landborder-11.25)%360)
                except:
                    pass
        eliminated_scouts = set()
        for tank_scout in self.tank_scouts.items():
            tsk, tsv = tank_scout
            if ("tanks" not in myinfo) or (tsv not in [tank.uid for tank in myinfo["tanks"]]):
                eliminated_scouts.add(tsk)
        for tsk in eliminated_scouts:
            self.tank_scouts.pop(tsk)
            # print(view)
            # print(view[0])
            # print(view[-1])
            
            # exit()

##############

        # Controlling my bases =================================================

        # Description of information available on bases:
        #
        # This is read-only information that all the bases (enemy and your own) have.
        # We define base = info[team_name_1]["bases"][0]. Then:
        #
        # base.x (float): the x position of the base
        # base.y (float): the y position of the base
        # base.position (np.ndarray): the (x, y) position as a numpy array
        # base.team (str): the name of the team the base belongs to, e.g. ‘John’
        # base.number (int): the player number
        # base.mines (int): the number of mines inside the base
        # base.crystal (int): the amount of crystal the base has in stock
        #     (crystal is per base, not shared globally)
        # base.uid (str): unique id for the base
        #
        # Description of base methods:
        #
        # If the base is your own, the object will also have the following methods:
        #
        # base.cost("mine"): get the cost of an object.
        #     Possible types are: "mine", "tank", "ship", "jet"
        # base.build_mine(): build a mine
        # base.build_tank(): build a tank
        # base.build_ship(): build a ship
        # base.build_jet(): build a jet
        if self.main_base is None:
            self.main_base = myinfo["bases"][0]
            self.scout_positions = [Pos(self.main_base.x+offset.x,self.main_base.y+offset.y) for offset in SCOUTING_OFFSETS]
        # Iterate through all my bases (vehicles belong to bases)
        for base in myinfo["bases"]:
            # If this is a new base, initialize the tank & ship counters
            if base.uid not in self.ntanks:
                self.ntanks[base.uid] = 0
                self.basetanks[base.uid] = set()
            if base.uid not in self.nships:
                self.nships[base.uid] = 0
                self.baseships[base.uid] = set()
            if base.uid not in self.base_max_mines:
                self.base_max_mines[base.uid] = np.random.randint(2,4)
            # Firstly, each base should build a mine if it has less than 3 mines
            if base.mines < self.base_max_mines[base.uid]:
                if base.crystal > base.cost("mine"):
                    base.build_mine()
            elif base.uid not in self.tank_scouts:
                if base.crystal > base.cost("tank") and (base.uid not in self.tank_scouts or len(self.tank_scouts[base.uid]) < 1):# and ("tanks" not in myinfo or len(myinfo["tanks"])<1):
                    tank_uid = base.build_tank(heading=360 * np.random.random())
                    self.tank_scouts[base.uid] = tank_uid
                    self.ntanks[base.uid] += 1
                    self.basetanks[base.uid].add(tank_uid)
            elif base.crystal > base.cost("tank") and self.ntanks[base.uid] < (3 if base.uid == self.main_base.uid else 2):# and ("tanks" not in myinfo or len(myinfo["tanks"])<1):
                tank_uid = base.build_tank(heading=360 * np.random.random())
                self.basetanks[base.uid].add(tank_uid)
                self.ntanks[base.uid] += 1
            # elif self.scout is None:
            #     if base.crystal > base.cost("jet"):
            #         jet_uid = base.build_jet(heading=calc_heading((base.x, base.y), self.scout_positions[1]))
            #         self.scout = jet_uid
            #         print("new scout", jet_uid, self.scout_positions[1].x, self.scout_positions[1].y)

            # Secondly, each base should build a tank if it has less than 5 tank
            # elif base.crystal > base.cost("tank") and self.ntanks[base.uid] < 5:
            #     # build_tank() returns the uid of the tank that was built
            #     tank_uid = base.build_tank(heading=360 * np.random.random())
            #     # Add 1 to the tank counter for this base
            #     self.ntanks[base.uid] += 1
            # # Thirdly, each base should build a ship if it has less than 3 ships
            elif base.crystal > base.cost("ship") and (base.uid not in self.bases_for_planes) and ((base.uid == self.main_base.uid) or (len(self.baseships[base.uid]) < 0 and self.nships[base.uid] < 2 and ("ships" not in myinfo or len(myinfo["ships"])<4))):
                # build_ship() returns the uid of the ship that was built
                ship_uid = base.build_ship(heading=360 * np.random.random())
                # Add 1 to the ship counter for this base
                self.baseships[base.uid].add(ship_uid)
                if np.random.random() < PLANE_BIRTH_RATE:
                    self.bases_for_planes.add(base.uid)
            # # If everything else is satisfied, build a jet
            # elif base.mines < 3:
            #     if base.crystal > base.cost("mine"):
            #         base.build_mine()
            elif base.crystal > base.cost("jet"):
                # build_jet() returns the uid of the jet that was built
                jet_uid = base.build_jet(heading=360 * np.random.random())
                self.bases_for_planes.discard(base.uid)



        # Try to find an enemy target
        target = None
        # If there are multiple teams in the info, find the first team that is not mine
        if len(info) > 1:
            for name in info:
                if name != self.team:
                    # Target only bases
                    if "bases" in info[name]:
                        # Simply target the first base
                        t = info[name]["bases"][0]
                        target = (t.x, t.y)
                        if target not in self.orphan_targets and target not in self.targets_by_hunter.values():
                            self.orphan_targets.add(target)

        # Controlling my vehicles ==============================================

        # Description of information available on vehicles
        # (same info for tanks, ships, and jets):
        #
        # This is read-only information that all the vehicles (enemy and your own) have.
        # We define tank = info[team_name_1]["tanks"][0]. Then:
        #
        # tank.x (float): the x position of the tank
        # tank.y (float): the y position of the tank
        # tank.team (str): the name of the team the tank belongs to, e.g. ‘John’
        # tank.number (int): the player number
        # tank.speed (int): vehicle speed
        # tank.health (int): current health
        # tank.attack (int): vehicle attack force (how much damage it deals to enemy
        #     vehicles and bases)
        # tank.stopped (bool): True if the vehicle has been told to stop
        # tank.heading (float): the heading angle (in degrees) of the direction in
        #     which the vehicle will advance (0 = east, 90 = north, 180 = west,
        #     270 = south)
        # tank.vector (np.ndarray): the heading of the vehicle as a vector
        #     (basically equal to (cos(heading), sin(heading))
        # tank.position (np.ndarray): the (x, y) position as a numpy array
        # tank.uid (str): unique id for the tank
        #
        # Description of vehicle methods:
        #
        # If the vehicle is your own, the object will also have the following methods:
        #
        # tank.get_position(): returns current np.array([x, y])
        # tank.get_heading(): returns current heading in degrees
        # tank.set_heading(angle): set the heading angle (in degrees)
        # tank.get_vector(): returns np.array([cos(heading), sin(heading)])
        # tank.set_vector(np.array([vx, vy])): set the heading vector
        # tank.goto(x, y): go towards the (x, y) position
        # tank.stop(): halts the vehicle
        # tank.start(): starts the vehicle if it has stopped
        # tank.get_distance(x, y): get the distance between the current vehicle
        #     position and the given point (x, y) on the map
        # ship.convert_to_base(): convert the ship to a new base (only for ships).
        #     This only succeeds if there is land close to the ship.
        #
        # Note that by default, the goto() and get_distance() methods will use the
        # shortest path on the map (i.e. they may go through the map boundaries).

        # Iterate through all my tanks
        if "tanks" in myinfo:
            for tank in myinfo["tanks"]:
                if (tank in self.tank_scouts):
                    pass
                else:
                    closest_orphan_target = None
                    closest_target_distance = inf
                    for orphan_target in self.orphan_targets:
                        dd = tank.get_distance(*orphan_target)
                        if dd < closest_target_distance:
                            closest_orphan_target = orphan_target
                            closest_target_distance = dd
                    if closest_target_distance <= 50:
                        tank.goto(*closest_orphan_target)
                    if (tank.uid in self.previous_positions) and (not tank.stopped):
                        # If the tank position is the same as the previous position,
                        # set a random heading
                        if all(tank.position == self.previous_positions[tank.uid]):
                            tank.set_heading(np.random.random() * 360.0)
                        # Else, if there is a target, go to the target
                        # elif target is not None:
                        #     tank.goto(*target)
                    # Store the previous position of this tank for the next time step
                    self.previous_positions[tank.uid] = tank.position

        # Iterate through all my ships
        if "ships" in myinfo:
            for ship in myinfo["ships"]:
                if ship.uid in self.previous_positions:
                    # If the ship position is the same as the previous position,
                    # convert the ship to a base if it is far from the owning base,
                    # set a random heading otherwise
                    if all(ship.position == self.previous_positions[ship.uid]):
                        # if ship.get_distance(ship.owner.x, ship.owner.y) > 20:
                        if all(ship.get_distance(base.x, base.y) > 30 for base in myinfo["bases"]):
                            ship.convert_to_base()
                        else:
                            ship.set_heading(np.random.random() * 360.0)
                # Store the previous position of this ship for the next time step
                self.previous_positions[ship.uid] = ship.position

        # Iterate through all my jets
        if "jets" in myinfo:
            for jet in myinfo["jets"]:
                # Jets simply go to the target if there is one, they never get stuck
                # if target is not None:
                #     jet.goto(*target)
                # if jet.uid not in self.targets_by_hunter:
                    closest_orphan_target = None
                    closest_target_distance = inf
                    for target_candidate in self.orphan_targets:
                        candidate_distance = jet.get_distance(*target_candidate)
                        if candidate_distance < closest_target_distance:
                            closest_target_distance = candidate_distance
                            closest_orphan_target = target_candidate
                    if closest_orphan_target is not None:
                        # self.orphan_targets.discard(closest_orphan_target)
                        self.targets_by_hunter[jet.uid] = list(closest_orphan_target)
                        jet.goto(*closest_orphan_target)



