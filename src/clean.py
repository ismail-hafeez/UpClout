import pandas as pd
import json

DATA_OUTPUT="../data"

with open("../data/insta_data.json", "r", encoding="utf-8") as file:
    data=json.load(file)

df=pd.DataFrame(data)

print(df.head())