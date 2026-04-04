"""Runner for the recommender package.

This is a thin CLI that instantiates the OOP recommender and writes
recommendations to `similarity_matches.json`.
"""

from recommender import Recommender


def main():
    r = Recommender()
    print("Running recommender... this may take a few minutes.")
    results = r.run()
    print("Results saved to similarity_matches.json")


if __name__ == "__main__":
    main()
