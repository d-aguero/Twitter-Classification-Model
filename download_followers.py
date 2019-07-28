# -*- coding: utf-8 -*-

#!/usr/bin/python
# -*- coding: utf-8 -*-

import tweepy
import csv
import json
import re

# load Twitter API credentials
with open('twitter_credentials.json') as cred_data:
    info = json.load(cred_data)
    consumer_key = info['CONSUMER_KEY']
    consumer_secret = info['CONSUMER_SECRET']
    access_key = info['ACCESS_KEY']
    access_secret = info['ACCESS_SECRET']

# ----------------------------------------------------------------------------------------------

# These are a bunch of functions I'm using
# Main method is at the bottom

def get_follower_ids(screen_name):
    
    # Authorization and initialization
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    # Downloads up to 5000 followers.
    followers = api.followers_ids(screen_name=screen_name)

    print ('...%s followers downloaded' % len(followers))
    return followers


def get_user_objects(follower_ids):
    
    # Authorization and initialization
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    # Twitter only lets you download 100 user objects at a time, so this goes through a loop to get more than 100
    batch_len = 100
    batches = (follower_ids[i:i+batch_len] for i in range(0, len(follower_ids), batch_len))
    all_data = []
    for batch_count, batch in enumerate(batches):
        users_list = api.lookup_users(user_ids=batch)
        users_json = (map(lambda t: t._json, users_list))
        all_data += users_json
    return all_data

def get_potential_viable_users(user_objects):
    
    viable_users = []
    
    valid = re.compile(r".*(\d{2}|\d{4}).*")
    
    for user in user_objects:
        
        if len(viable_users) >= 600: # Not really necessary, but my computer has been chugging
            break
        
        elif valid.match(user["description"]):
            viable_users.append(user)
        
    return viable_users

def determine_ages_manually(users):
    
    final_users = []
    
    for user in users:
        if len(final_users) > 300:
            break        
        try:
            user_age = int(input(print(user["description"])))
        except:
            user_age = 0
            
        if user_age > 0:
                final_users.append([user_age, user["screen_name"]])
        
    return final_users
        
# Helper function for downloading tweets of a given user.
# This doesn't download every single tweet a user has made, 
# just the most recent 3240, since that's where twitter caps the cumulative request.
def download_tweets(screen_name):
    
    # Authorization and initialization
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    # List for holding tweets
    tweets = []
    
    # We will get the tweets with multiple requests of 200 tweets each,
    # since individual requests get capped at 200 tweets.
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    
    # saving the most recent tweets
    tweets.extend(new_tweets)
    
    # save id of 1 less than the oldest tweet
    try:
        oldest_tweet = tweets[-1].id - 1
        iteration = 1
    except:
        iteration = 5
    
    # grabbing tweets till none are left.
    # Also capping the total amount of tweets at around 1000, since there's a limit
    # on how many followers you can request in a given amount of time,
    # and if I hit that limit, then the code continues but doesn't download anything...
    while (len(new_tweets) > 0 and iteration < 5):
        
        # The max_id param will be used subsequently to prevent duplicates
        try:
            new_tweets = api.user_timeline(screen_name=screen_name,count=200, max_id=oldest_tweet)
            # save most recent tweets
            tweets.extend(new_tweets)
            # id is updated to oldest tweet - 1 to keep track
            try:
                oldest_tweet = tweets[-1].id - 1
                print ('...%s tweets have been downloaded so far' % len(tweets))
            except:
                iteration = 4
        except:
            break
        
        iteration += 1
    
    # This gets rid of retweets, which always begin with "RT"
    tweets_str = []
    valid = re.compile(r"^RT")
    for tweet in tweets:
        if not valid.match(tweet.text):
            tweets_str.append(tweet.text)
    
    # Join all tweets together into one string
    all_tweets = " ".join(tweets_str)
    
    return all_tweets
    

# ---------------------------------------------------------------------------------------------------------------

# To simulate this with a specific twitter handle, enter the handle in the argument of the first method below.
# Then everything should work as intended afterwards, resulting in a csv file
# ... though you still have to manually go through users to extract their age.
    
if __name__ == '__main__':
    
    screen_name = "bbcdoctorwho"
    
    # Get follower IDs of a specified user's followers
    follower_ids = get_follower_ids(screen_name)
    
    # Get user objects of each follower ID; user objects contain all data about a user, including bio and info for accessing tweets.
    follower_objects = get_user_objects(follower_ids)
    
    # Start process to go through each follower and download their tweets,
    # if their bio has some substring resembling an age in it (13, 45, 1997, ...)
    viable_followers = get_potential_viable_users(follower_objects)
    
    # Manually determine ages of followers.
    # This is done to avoid marking data erroneously,
    # e.g. if bio says "I love the 49ers!", it could mark their age as 49
    parsed_followers = determine_ages_manually(viable_followers)
    
    # Downloads tweets, removes retweets, and concatenates results.
    # Then makes a list of lists, where each row is in the format [age, tweets]
    final_users = []
    for user in parsed_followers:
        try:
            final_users.append([user[0], download_tweets(user[1])])
        except:
            pass # This is to avoid locked accounts, since twitter throws an exception if Python tries to access them
    
    
    # Finally, write everything to a csv file
    with open(screen_name + '_tweets.csv', 'w', encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerow(['age', 'tweets'])
        writer.writerows(final_users)
    