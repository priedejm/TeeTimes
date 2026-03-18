# City configurations for muni tee time scraping
# Each city has its own domain, tokens, Discord webhook, and scrape parameters.

CITY_CONFIGS = {
    "charleston": {
        "name": "Charleston",
        "domain": "sccharlestonweb.myvscloud.com",
        "csrf_token": "Xf0R600W0Q0E2D481X2O2O5D604X6D57066Z4U5E4C0N5N5W5C4E71564Z6T4Z065Y4L466C6D674S6M6H0T5G4C5I6M19724R553Y0264566O50046D5R4S6K1P5M625G",
        "number_of_players": 1,
        "begin_time": "+7%3A00AM",
        "number_of_holes": 18,
        "discord_webhook": "https://discord.com/api/webhooks/1326397023171252255/dV5__1t-tiXcqnkGzNTayMFejrOAqwpPbP-L3_K9ulExLBfuKzAjr2eocLxJayVtXIRA",
        "scrape_days": ["Friday", "Saturday", "Sunday", "Thursday"],
        "file_prefix": "chs_muni",       # Prefix for cache files
        "counter_file": "chs_muniCount.txt",
        "bot_name": "Charleston Muni",
        "avatar_url": "https://i.imgur.com/kfjHRvR.jpeg",
    },
    "wilmington": {
        "name": "Wilmington",
        "domain": "ncwilmingtonweb.myvscloud.com",
        "csrf_token": "Vj0ag4tJh96C9GituXpvlbAjxNSIdEmBBTMD5rWU1p8CAQ4QLq2KDPJUKmLPAmeloLLVXhJAutDeByQ8NRc5GElz5bIo4INd",
        "number_of_players": 2,
        "begin_time": "+7%3A00+AM",
        "number_of_holes": 18,
        "discord_webhook": "https://discord.com/api/webhooks/1483854197467250709/2g1N0eduJdc5ZDFOTOU-rbHANJwlPq4PVME5DLjvlXezAiGpGN_ta_RLaiLwyQStEVma",
        "scrape_days": ["Saturday"],
        "file_prefix": "wilm_muni",      # Prefix for cache files
        "counter_file": "wilm_muniCount.txt",
        "bot_name": "Wilmington Muni",
        "avatar_url": "https://i.imgur.com/kfjHRvR.jpeg",
    },
}