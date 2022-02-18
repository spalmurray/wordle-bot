from typing import Tuple, List
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
                "win_rate": 0
            }

        player["scores"][wordle] = score
        player["count"] += 1
        player["win_count"] = player["win_count"] if score == 7 else player["win_count"] + 1
        player["average"] = player["average"] + (score - player["average"]) / (player["count"])
        player["win_rate"] = player["win_count"] / player["count"]

        self.db.players.replace_one({"_id": pid}, player, True)

        return True

    def get_player_stats(self, pid: int) -> Tuple[float, int, int, float, int, int]:
        """Return the stats of the player with provided id, given as a tuple in the form
        (average, count, win_count, win_rate, curr_streak, max_streak).
        """
        player = self.db.players.find_one({'_id': pid})

        if player is None:
            return 0.0, 0, 0, 0, 0, 0

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
        print(scores)
        # remove scores that are not wins
        for game in scores:
            if scores[game] != 7:
                wins.append(int(game))

        # sort these wins and return current streak
        wins.sort(reverse=True)
        print(wins)
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
        print(scores)
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

    def delete_player(self, pid: int) -> bool:
        """Return True iff the player with pid was successfully deleted."""
        result = self.db.players.delete_one({"_id": pid})
        if result.deleted_count != 0:
            return True
        return False
