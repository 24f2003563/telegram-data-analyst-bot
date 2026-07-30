# known_datasets.py
#
# A tiny local fallback for well-known public-data questions where fetching
# the live source is unreliable (MOSPI file paths change often, and
# data.gov.in actively blocks automated scraping). Each entry is:
#   - keywords: all of these substrings (lowercased) must appear in the
#     question for this dataset to be used
#   - rows: the actual data, as a list of dicts (becomes the DataFrame)
#   - source: where the numbers came from, for the log
#
# Add more entries here as you discover more questions that need a
# reliable, scrapable-proof answer.

KNOWN_DATASETS = [
    {
        "name": "maternal_mortality_ratio_srs_2018_20",
        "keywords": ["maternal mortality"],
        "source": (
            "Registrar General of India - Special Bulletin on Maternal "
            "Mortality in India, 2018-20 (SRS)"
        ),
        "rows": [
            {"state": "Assam", "mmr": 195},
            {"state": "Madhya Pradesh", "mmr": 173},
            {"state": "Uttar Pradesh", "mmr": 167},
            {"state": "Chhattisgarh", "mmr": 137},
            {"state": "Odisha", "mmr": 119},
            {"state": "Bihar", "mmr": 118},
            {"state": "Rajasthan", "mmr": 113},
            {"state": "Haryana", "mmr": 110},
            {"state": "Punjab", "mmr": 105},
            {"state": "West Bengal", "mmr": 103},
            {"state": "Uttarakhand", "mmr": 103},
            {"state": "Karnataka", "mmr": 69},
            {"state": "Jharkhand", "mmr": 56},
            {"state": "Gujarat", "mmr": 57},
            {"state": "Maharashtra", "mmr": 33},
            {"state": "Tamil Nadu", "mmr": 54},
            {"state": "Telangana", "mmr": 43},
            {"state": "Andhra Pradesh", "mmr": 45},
            {"state": "Kerala", "mmr": 19},
        ],
    },
]


def find_known_dataset(question_text):
    """
    Returns the matching entry from KNOWN_DATASETS for this question, or
    None if nothing matches. Simple all-keywords-present matching - good
    enough for a small, hand-picked list.
    """
    text = (question_text or "").lower()
    for entry in KNOWN_DATASETS:
        if all(kw in text for kw in entry["keywords"]):
            return entry
    return None
