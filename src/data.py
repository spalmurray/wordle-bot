import math
from typing import Tuple, List
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient


class Client:
    """Data access interface for MongoDB database for use with wordle-bot.

    The database has collections this collection:

    players:
        - _id
        - scores (Dictionary with Wordle number keys and score values)
        - count (number of scores)
        - win_count (number of scores that are not 7, for average computation)
        - average
    """

    def __init__(self):
        """Initialize a new Client connected to the local MongoDB instance."""
        self.mongo = MongoClient()
        self.db = self.mongo.wordle

    def add_score(self, pid: int, wordle: str, score: int) -> bool:
        """Adds a score to the relevant player in the database. If a score already exists, return False."""
        player = self.db.players.find_one({'_id': pid})
        if player is not None and wordle in player["scores"]:
            return False

        if player is None:
            # make a new one!
            player = {
                "_id": pid,
                "scores": {},
                "count": 0,
                "win_count": 0,
                "average": 0,
                "win_rate": 0,
                "last_updated": datetime.now()
            }

        player["scores"][wordle] = score
        player["count"] += 1
        player["win_count"] = player["win_count"] if score == 7 else player["win_count"] + 1
        player["average"] = player["average"] + (score - player["average"]) / (player["count"])
        player["win_rate"] = player["win_count"] / player["count"]
        player["last_updated"]: datetime.now()

        self.db.players.replace_one({"_id": pid}, player, True)

        return True

    def get_player_stats(self, pid: int) -> Tuple[float, int, int, float, int, int]:
        """Return the stats of the player with provided id, given as a tuple in the form
        (average, count, win_count, win_rate, curr_streak, max_streak).
        """
        player = self.db.players.find_one({'_id': pid})

        if player is None:
            return 0.0, 0, 0, 0, 0, 0

        # If performance optimization becomes necessary, remove streak calculations from this.
        # Additionally, if program complexity grows sufficiently, you may consider making
        # a Player class to handle stats.

        return (
            player["average"],
            player["count"],
            player["win_count"],
            player["win_rate"],
            self.get_current_streak(pid),
            self.get_max_streak(pid)
        )

    def get_current_streak(self, pid: int) -> int:
        """Return the length of the player's current win streak."""
        player = self.db.players.find_one({'_id': pid})

        if player is None:
            return 0

        scores = player['scores']
        wins = []
        most_recent_loss = -math.inf

        # extract winning scores and track most recent loss
        for game in scores:
            if scores[game] != 7:
                wins.append(int(game))
            elif int(game) > most_recent_loss:
                most_recent_loss = int(game)

        # sort the wins
        wins.sort(reverse=True)

        # check whether most recent game was a loss
        if most_recent_loss > wins[0]:
            return 0

        # return current streak
        i = 1
        previous = int(wins[0])
        while i != len(wins) and int(wins[i]) == int(previous - 1):
            previous = int(wins[i])
            i += 1
        return i

    def get_max_streak(self, pid: int) -> int:
        """Return the length of the player's maximum win streak."""
        player = self.db.players.find_one({'_id': pid})

        if player is None:
            return 0

        scores = player['scores']
        wins = []
        # remove scores that are not wins
        for game in scores:
            if scores[game] != 7:
                wins.append(int(game))

        # sort these wins and return max streak
        wins.sort(reverse=True)
        max_streak = 0
        i = 0
        while i != len(wins):
            curr_streak = 1
            previous = int(wins[i])
            i += 1
            while i != len(wins) and int(wins[i]) == (previous - 1):
                curr_streak += 1
                previous = int(wins[i])
                i += 1
            max_streak = (curr_streak if curr_streak > max_streak else max_streak)
        return max_streak

    def get_missing_scores(self, pid: int) -> List[int]:
        """Return a list of Wordle game numbers that user with pid has not submitted to wordle-bot which are after the
        player's lowest game number submission and before the player's highest game number submission.
        """
        player = self.db.players.find_one({'_id': pid})

        if player is None:
            return []

        # get the player's submitted game numbers and sort them in non-decreasing order
        games = sorted(player['scores'], key=lambda y: int(y))

        # we'll accumulate the missing scores here.
        missing = []

        # iterate through the list of games adding missing numbers to the missing list as we go
        prev = int(games[0])
        for game in games[1:]:
            game = int(game)
            if game != prev + 1:
                for x in range(prev + 1, game):
                    missing.append(x)
            prev = game

        return missing

    def delete_player(self, pid: int) -> bool:
        """Return True iff the player with pid was successfully deleted."""
        result = self.db.players.delete_one({"_id": pid})
        if result.deleted_count != 0:
            return True
        return False

    def get_nearing_expiry(self) -> List[Tuple[int, int]]:
        """Return a list containing a tuple for each user who has not submitted a score in the last 15-29 days. Each
        tuple is of the form (Discord user id, days since last submitted score).
        """
        nearing_expiry = []
        cursor = self.db.players.find({})

        for player in cursor:
            if timedelta(days=15) < (datetime.now() - player["last_updated"]) < timedelta(days=30):
                nearing_expiry.append((player["_id"], (datetime.now() - player["last_updated"]).days))

        return nearing_expiry

    def get_expired(self) -> List[int]:
        """Return a list of user ids for each user who has not submitted a score in the last 30 days."""
        expired = []
        cursor = self.db.players.find({})

        for player in cursor:
            if timedelta(days=30) < (datetime.now() - player["last_updated"]):
                expired.append(player["_id"])
                self.delete_player(player["_id"])

        return expired
