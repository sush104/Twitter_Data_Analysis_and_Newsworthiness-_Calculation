import re, emoji
from datetime import datetime
import string
from nltk.corpus import stopwords
from collections import Counter
import json, math
import spacy



MIN_TWEET_LENGTH = 3
MIN_TOKEN_LENGTH = 7
tweet = ""
nlp = spacy.load('en_core_web_sm')


class Filter():
    # pattern = re.compile('[\W_]+')
    def is_valid_token(token):
        # we may need to add more contsraints
        # print(token, '   ', type(token))
        try:
            return((token not in stopwords) and(token != '&amp;') and (len(token) > MIN_TOKEN_LENGTH) )
        except Exception as e:
            return False

    def is_retweet(text):
        return text.startswith("RT @")

    def strip_emoji(text):
        new_text = re.sub(emoji.get_emoji_regexp(), r"", text)
        return new_text

    def cleanList(text):
        text = Filter.strip_emoji(text)
        text.encode("ascii", errors="ignore").decode()
        return text

    def normalize(token):
        if(token.startswith('#') or token.startswith('@') or token.startswith('$') or token.startswith('https')):
            return token
        if(token.startswith('T&amp')):
            return None
        s = token.lower()

        exclude = set(string.punctuation)
        s = ''.join(ch for ch in s if ch not in exclude)

        return s

    def tokenize(text):
        if(text is None):
            return None
        set1 = set()

        try:
            for i in text.split():
                # normalize first
                i = Filter.normalize(i)
                if(i is not None and Filter.is_valid_token(i) == True):
                    set1.add(i)
        except Exception as e:
            print(e)
            print(type(text))
        if(len(set1) > MIN_TWEET_LENGTH):
            return sorted(set1)
        else:
            return None

    def filterProcess(tweet):
        text = tweet['text']

        text1= Filter.cleanList(text)
        x= Filter.tokenize(text1)

        # print(x)
        return x

    def process_tweet_text(text):
        if text == None:
            return []
        temp = text.lower()
        temp = re.sub("[^a-z0-9]"," ", temp)
        temp = str.replace("'", "", temp)
        temp = str.replace('T&amp','',temp)
        temp = re.sub('[()!?]', ' ', temp)
        temp = re.sub('\[.*?\]',' ', temp)
        temp = emoji.replace_emoji(temp, replace='')
        
        doc = nlp(temp)
        for token in doc:
            if not token.is_stop:
                temp = token.lemma_
        return temp

    def term_freq(file):
        doc_freq = 0.0
        f_read = open(file, encoding="utf8") 
        model_terms_freq = None
        
        for line in f_read.readlines():
            tweet = json.loads(line)
            text = tweet["text"]
            counter = Counter(Filter.process_tweet_text(text))
            if model_terms_freq == None:
                model_terms_freq = counter
            else:
                model_terms_freq += counter

        doc_freq= sum(model_terms_freq.values())
        return (model_terms_freq,doc_freq)
    
    def term_freq_text(text):
        counter = Counter(Filter.process_tweet_text(text))
        return dict(counter),sum(counter.values())

    def create_doc():
        print("Creating document...")
        hq_file = "./data/highFileFeb"
        lq_file = "./data/lowFileFeb"

        hq_doc,hq_doc_frequency = Filter.term_freq(hq_file)
        lq_doc,lq_doc_frequency = Filter.term_freq(lq_file)
            
        return [hq_doc,hq_doc_frequency, lq_doc,lq_doc_frequency]

class newsWorthiness():
    
    def calculate_newsworthy_score(tweet, doc):
        print('Calculating newsworthy score...')
        text = tweet['text']
        termsfrequency,totalfrequency = Filter.term_freq_text(text)
        RHQ = 0.0
        RLQ = 0.0
        SHQ = 0.0
        SLQ = 0.0
        
        hq_doc = doc[0]
        hq_doc_frequency = doc[1]
        lq_doc = doc[2]
        lq_doc_frequency = doc[3]

        for i in Filter.process_tweet_text(text):
            rhq_upper = hq_doc[i]/hq_doc_frequency
            rhq_lower = termsfrequency[i]/totalfrequency
            rlq_upper = lq_doc[i]/lq_doc_frequency
            rlq_lower = termsfrequency[i]/totalfrequency

            RHQ = rhq_upper/rhq_lower
            RLQ = rlq_upper/rlq_lower
            
            if RHQ >= 0.3:
                SHQ += RHQ
            else:
                SHQ += 0.0

            if RLQ >= 0.6:
                SLQ += RLQ
            else:
                SLQ += 0.0
        
        score = math.log2((1+SHQ)/(1+SLQ))
        print(SHQ,SLQ)
        print("Final score::",score)
        if score > 0:
            print("Above Tweet is newsworthy. <STOPPING>")
        else:
            print("Above Tweet is not newsworthy. <MOVING TO NEXT TWEET>")
        
        return score

    def descriptionWeight(tweet):
        text = tweet['text']
        print("Current Tweet: ")
        print(text)
        listTerms =  ['news', 'report', 'journal', 'write', 'editor', 'analyst', 'analysis','media', 'updates', 'stories', 'trader', 'investor', 'forex', 'stock', 'finance', 'market']
        listSpam = ['celebrity','ebay', 'review', 'shopping', 'deal','sale', 'sales','link', 'click', 'marketing', 'promote', 'discount', 'products', 'store', 'diet', \
        'weight', 'porn', 'followback', 'follow back', 'lucky', 'winners', 'prize', 'hiring']
        termsWeight =.1
        maxWeight = 1
        x= Filter.tokenize(text) # x is set
        if(x):
            # print(x)
            for i in x:
                maxWeight += 3
                if i in listTerms:
                    # print('in list terms : ', i)
                    termsWeight += 3
                    # print('termsWeight : ', termsWeight)
                elif i in listSpam:
                    termsWeight += 0.1
                    # print('termsWeight : ', termsWeight)
                else:
                    termsWeight += 1
            # if(termsWeight ==1):
            #         termsWeight = .1
            termsWeight = termsWeight/maxWeight
            # print('termsWeight : ', termsWeight)
        return termsWeight

    def accountAgeWeight(User):
        weight = 0
        date = datetime.today().date()

        created_at =  User['created_at']
        created_at = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')


        # datetime.strptime('Thu Apr 23 13:38:19 +0000 2009','%a %b %d %H:%M:%S %z %Y');
        daysSince = (date - created_at.date()).days
        #
        # print(daysSince)
        if daysSince < 1:
            weight = 0.05
        elif daysSince < 30:
            weight = 0.10
        elif daysSince < 90:
            weight = 0.25
        elif    daysSince > 90:
                weight = 1.0
        return weight

    def followersCount(User):
        followersCount =   User['followers_count']
        # print(followersCount)

        if followersCount < 50:
            weight = 0.5
        elif followersCount < 5000:
            weight = 1.0
        elif followersCount < 10000:
            weight = 1.5
        elif    followersCount < 100000:
            weight = 2.0
        elif    followersCount < 200000:
            weight = 2.5
        elif    followersCount > 200000:
            weight = 3.0
        return weight/3

    def verifiedUser(User):
        if (User['verified']):
            weight = 1.5
        else:
            weight = 1.0
        return weight/1.5

    def defaultProfile(User):
        weight =1
        if(User['default_profile_image']):
            weight =0.5
        return weight

    def qualityScore(User, text, hq_file , lq_file):

        # if(Filter.is_retweet(text)):
        #     return None
        qualityScore = 0
        profileWeight = newsWorthiness.defaultProfile(User)
        verifiedWeight = newsWorthiness.verifiedUser(User)
        followersWeight = newsWorthiness.followersCount(User)
        accountAgeWeight = newsWorthiness.accountAgeWeight(User)
        descriptionWeight = newsWorthiness.descriptionWeight(User['description'])
        contentWeight = newsWorthiness.descriptionWeight(text)

        qualityScore = (profileWeight + verifiedWeight + followersWeight + accountAgeWeight +  descriptionWeight +contentWeight)/6
        if(qualityScore>.5):
            print(qualityScore, '  ', profileWeight , '  ', verifiedWeight, '  ',followersWeight, '  ', accountAgeWeight , '  ',descriptionWeight, '   ', contentWeight)
        try:
            if (qualityScore > .79):
                hq_file.write(User['screen_name'] + '   ' + User['description'] +'\n')
                hq_file.write(str(text))
                hq_file.write(str(qualityScore)+ '  '+ str(profileWeight) + '  '+ str(verifiedWeight) + '  ' +str(followersWeight)+ '  '+ str(accountAgeWeight) + '  ' + str(descriptionWeight)+'\n')
            elif qualityScore < .48:
                lq_file.write(User['screen_name'] + '   ' + User['description']  +'\n')
                lq_file.write(str(text))
                lq_file.write(str(qualityScore)+ '  '+ str(profileWeight) + '  '+ str(verifiedWeight) + '  ' +str(followersWeight)+ '  '+ str(accountAgeWeight) + '  ' + str(descriptionWeight)+'\n')
        except Exception as e:
            print(e)
        return qualityScore
