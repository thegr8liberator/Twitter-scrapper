import tweepy
import time
import json
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

class TwitterMonitor:
    def __init__(self):
        load_dotenv()  # Load environment variables
        
        # Twitter API credentials
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        self.search_phrase = "Listed on Robinhood"
        self.output_file = "robinhood_listings.json"
        self.last_tweet_id = None
    
    def load_previous_tweets(self):
        """Load previously saved tweets to avoid duplicates"""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                data = json.load(f)
                if data and len(data) > 0:
                    self.last_tweet_id = data[0].get('id')
        
    def save_tweets(self, tweets):
        """Save new tweets to JSON file"""
        existing_tweets = []
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                existing_tweets = json.load(f)
        
        # Combine new tweets with existing ones
        all_tweets = tweets + existing_tweets
        
        with open(self.output_file, 'w') as f:
            json.dump(all_tweets, f, indent=2)
    
    def search_twitter(self):
        """Search for tweets containing the phrase"""
        try:
            query = f'"{self.search_phrase}" -is:retweet'
            
            # Search tweets
            response = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['created_at', 'author_id', 'text'],
                max_results=100,
                since_id=self.last_tweet_id
            )
            
            if not response.data:
                print(f"No new tweets found at {datetime.now()}")
                return []
            
            # Process tweets
            tweets = []
            for tweet in response.data:
                tweet_data = {
                    'id': tweet.id,
                    'created_at': tweet.created_at.isoformat(),
                    'author_id': tweet.author_id,
                    'text': tweet.text
                }
                tweets.append(tweet_data)
            
            print(f"Found {len(tweets)} new tweets at {datetime.now()}")
            return tweets
            
        except Exception as e:
            print(f"Error searching Twitter: {str(e)}")
            return []
    
    def send_to_telegram(self):
        """Send the log file to a Telegram bot."""
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendDocument"
        try:
            with open(self.output_file, 'rb') as file:
                response = requests.post(
                    url, 
                    data={'chat_id': os.getenv('TELEGRAM_CHAT_ID')}, 
                    files={'document': file}
                )
            if response.status_code == 200:
                print("Log file sent to Telegram successfully.")
            else:
                print("Failed to send log file to Telegram:", response.text)
        except Exception as e:
            print(f"Error sending to Telegram: {str(e)}")
    
    def monitor(self, interval_minutes=5):
        """Continuously monitor Twitter with specified interval"""
        print(f"Starting Twitter monitor for phrase: '{self.search_phrase}'")
        self.load_previous_tweets()
        
        while True:
            new_tweets = self.search_twitter()
            if new_tweets:
                self.save_tweets(new_tweets)
                self.last_tweet_id = new_tweets[0]['id']
                self.send_to_telegram()
            
            # Wait for the specified interval
            time.sleep(interval_minutes * 60)

def main():
    monitor = TwitterMonitor()
    monitor.monitor(interval_minutes=5)  # Change to 720 for 12-hour interval in production

if __name__ == "__main__":
    main()
