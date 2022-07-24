import spacy
import json, math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from contentProcessing import newsWorthiness, Filter


nlp = spacy.load('en_core_web_sm')#instantiate spacy nlp

filename = './data/geoLondonJan'
worthy_tweets = []

with open(filename, encoding="utf8") as f:

    doc = Filter.create_doc()

    for line in f:
        print("Current line as a tweet from geoLondonJan file: ")
        tweet = json.loads(line)
        print(tweet["text"])
        newsworthieness_score = newsWorthiness.calculate_newsworthy_score(tweet, doc)
        if newsworthieness_score > 0:
            worthy_tweets.append(json.loads(line))
        

f.close()

worthy_tweet = len(worthy_tweets)
not_worthy_tweet = 4142 - worthy_tweet #4142 length of given dataset

print("Count of Worthy tweets: ",worthy_tweet)
print("Count of non Worthy tweets: ",not_worthy_tweet)


loc_df = pd.DataFrame(worthy_tweets)
cord_df = pd.DataFrame(loc_df['coordinates'].to_list())
lat_long_df = pd.DataFrame(cord_df['coordinates'].tolist(),columns=['lat','long'],dtype=np.float64)
new_tweet_df = pd.concat([loc_df,cord_df['type'],lat_long_df],axis=1)

boundingCoordinates = [-0.563, 51.261318, 0.28036, 51.686031]

def computeDistance(long2, lat2):
    R = 6373.0
    lat1 = boundingCoordinates[1]
    long1 = boundingCoordinates[0]
    
    phi1 = lat1 * (math.pi /180)
    phi2 = lat2 * (math.pi /180)    

    #phi
    delta1 = (lat2 - lat1) * (math.pi / 180)
    #lambda
    delta2 = (long2 - long1) * (math.pi / 180)

    a = math.sin(delta1 / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta2/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c

    return d


rows = int(np.ceil(computeDistance(boundingCoordinates[2], boundingCoordinates[1])))

columns = int(np.ceil(computeDistance(boundingCoordinates[0], boundingCoordinates[3])))

noofGrids = int(rows * columns)

rowPoints = []
colPoints = []

colPoints = np.linspace(boundingCoordinates[1], boundingCoordinates[3], num=columns)
rowPoints = np.linspace(boundingCoordinates[0], boundingCoordinates[2], num=rows)

new_tweet_df['col'] = np.searchsorted(colPoints, new_tweet_df['long'])
new_tweet_df['row'] = np.searchsorted(rowPoints, new_tweet_df['lat'])
new_tweet_df['id'] = new_tweet_df.groupby(by=["col","row"]).ngroup()

heatmap, xedges, yedges = np.histogram2d(new_tweet_df['col'], new_tweet_df['row'], bins=50)

ax = sns.heatmap(heatmap)
ax.invert_yaxis()
plt.show()

fig, ax1 = plt.subplots()
count=new_tweet_df.groupby(by=["id"])['id'].value_counts()

sns.histplot(count)
ax1.set(xlabel='Grid ID', ylabel='Tweet Count')
plt.show()

