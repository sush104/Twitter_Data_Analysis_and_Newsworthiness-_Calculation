from debugpy import listen
import tweepy
import spacy
import json
import traceback
from contentProcessing import Filter, newsWorthiness
import traceback

consumer_key = "RcgL9w7X8ZWHcF8F4IwHKPUVd"
consumer_secret ="dBnOPJvmM8pHPREIrbd6ToxcurGYHtsU3icdftehNuMNhR2zST"
access_token ="1220453124-QiwmRtAeoXJ5flWqjLKIUW9owc4jZN1qW6h630O"
access_token_secret ="R4927q3E2Yy9FOo7weIsVwf83Z5M0gRtLU0eE5uCn4aSn"
tweet=""
nlp = spacy.load('en_core_web_sm')#instantiate spacy nlp

# Filter.generatecorpus()

auth = tweepy.OAuthHandler(consumer_key, consumer_secret )
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
if (not api):
    print('Can\'t authenticate')
    print('failed cosumeer id ----------: ', consumer_key )

class StreamListener(tweepy.StreamListener):

    # def __init__(self):
        # You need to replace these with your own values that you get after creating an app on Twitter's developer portal.

    #This is a class provided by tweepy to access the Twitter Streaming API.
    def on_connect(self):
        # Called initially to connect to the Streaming API
        print("You are now connected to the streaming API.")

    def on_error(self, status_code):
        # On error - if an error occurs, display the error / status code
        print('An Error has occured: ' + repr(status_code))
        return False

    def on_data(self, data):
        #This is the meat of the script...it connects to your mongoDB and stores the tweet
        #print(data)
        try:
            # print(data)
            tweet = json.loads(data)
            #cal desp weight
            print("Desp Weight::",newsWorthiness.descriptionWeight(tweet))

            #cal account age weight
            print("Account age weight::",newsWorthiness.accountAgeWeight(tweet['user']))
        
            #cal follower count weight    
            print("Followers count weight::",newsWorthiness.followersCount(tweet['user']))

            #cal verified account weight
            print("verified account weight::",newsWorthiness.verifiedUser(tweet['user']))
            
            #cal default profile image weight
            print("default profile image weight::",newsWorthiness.defaultProfile(tweet['user']))
        
            #cal newsworthieness score
            newsworthieness_score = newsWorthiness.calculate_newsworthy_score(tweet, Filter.create_doc())
            
            #break when newsworthy doc found
            if newsworthieness_score > 0:
                return False
        except Exception as e:
            traceback.print_exc()
            return False

Loc_UK = [-10.392627, 49.681847, 1.055039, 61.122019] # UK and Ireland
Words_UK =["Boris", "Prime Minister", "Tories", "UK", "London", "England", "Manchester", "Sheffield", "York", "Southampton", \
    "Wales", "Cardiff", "Swansea" ,"Banff", "Bristol", "Oxford", "Birmingham" ,"Scotland", "Glasgow", "Edinburgh", "Dundee", "Aberdeen", "Highlands" \
    "Inverness", "Perth", "St Andrews", "Dumfries", "Ayr" \
    "Ireland", "Dublin", "Cork", "Limerick", "Galway", "Belfast"," Derry", "Armagh" \
    "BoJo", "Labour", "Liberal Democrats", "SNP", "Conservatives", "First Minister", "Surgeon", "Chancelor" \
    "Boris Johnson", "BoJo", "Keith Stramer"]

print("Tracking: " + str(Words_UK))
print(Words_UK)
listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True))
streamer = tweepy.Stream(auth=auth, listener=listener)
streamer.filter(locations= Loc_UK, track = Words_UK, languages = ['en'], is_async=True, stall_warnings=True)

