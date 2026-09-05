PROFILE_PAYLOAD = {
    "username": "tourist-lc",
    "name": "Example User",
    "avatar": "https://assets.leetcode.com/users/example/avatar.png",
    "ranking": 321,
    "reputation": 42,
    "country": "Bangladesh",
    "company": "Example Org",
    "school": "Example University",
}

PROBLEM_STATS_PAYLOAD = {
    "solvedProblem": 100,
    "easySolved": 50,
    "mediumSolved": 40,
    "hardSolved": 10,
}

CONTEST_STATS_PAYLOAD = {
    "contestAttend": 12,
    "contestRating": 1842.75,
    "contestGlobalRanking": 12345,
    "totalParticipants": 700000,
    "contestTopPercentage": 1.76,
}

RATING_HISTORY_PAYLOAD = {
    "contestHistory": [
        {
            "attended": True,
            "trendDirection": "UP",
            "problemsSolved": 3,
            "totalProblems": 4,
            "finishTimeInSeconds": 3600,
            "rating": 1725.5,
            "ranking": 456,
            "contest": {
                "title": "Weekly Contest 400",
                "startTime": 1710000000,
            },
        },
        {
            "attended": False,
            "trendDirection": "NONE",
            "problemsSolved": 0,
            "totalProblems": 4,
            "finishTimeInSeconds": 0,
            "rating": 0,
            "ranking": 0,
            "contest": {
                "title": "Weekly Contest 399",
                "startTime": 1709000000,
            },
        },
    ]
}

