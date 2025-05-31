#!/usr/bin/env python3
"""
Modern Twitter Miner using twscrape library
- Uses up-to-date Twitter API endpoints
- Handles authentication properly
- Integrates with existing account management
- Optimized for Bittensor subnet requirements
"""

import asyncio
import json
import time
import random
import sqlite3
import sys
import os
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import threading

# Add twscrape to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'twscrape'))

try:
    from twscrape import API, gather
    from twscrape.models import Tweet, User
    TWSCRAPE_AVAILABLE = True
except ImportError:
    print("❌ twscrape not available. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "./twscrape"])
    from twscrape import API, gather
    from twscrape.models import Tweet, User
    TWSCRAPE_AVAILABLE = True

@dataclass
class TwitterAccount:
    username: str
    password: str
    email: str
    email_password: str
    auth_token: str
    ct0_token: Optional[str] = None
    cookies: Optional[str] = None
    last_used: Optional[datetime] = None
    request_count: int = 0
    is_banned: bool = False
    ban_until: Optional[datetime] = None
    success_rate: float = 1.0

@dataclass
class TweetData:
    id: str
    url: str
    text: str
    author_username: str
    author_display_name: str
    created_at: datetime
    like_count: int
    retweet_count: int
    reply_count: int
    quote_count: int
    hashtags: List[str]
    media_urls: List[str]
    is_retweet: bool
    is_reply: bool
    conversation_id: str
    raw_data: Dict[str, Any]

class ModernTwitterMiner:
    """
    Modern Twitter mining system using twscrape library
    """
    
    def __init__(self, db_path: str = "enhanced_accounts.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.lock = threading.RLock()
        
        # Setup database
        self.setup_database()
        
        # Initialize twscrape API
        self.api = API()
        
        # Load accounts into twscrape
        self.setup_twscrape_accounts()
        
        # Target hashtags for Bittensor subnet
        self.target_hashtags = [
            "#bitcoin", "#bitcoincharts", "#bitcoiner", "#bitcoinexchange",
            "#bitcoinmining", "#bitcoinnews", "#bitcoinprice", "#bitcointechnology",
            "#bitcointrading", "#bittensor", "#btc", "#cryptocurrency", "#crypto",
            "#defi", "#decentralizedfinance", "#tao", "#ai", "#artificialintelligence",
            "#blockchain", "#web3", "#ethereum", "#solana", "#cardano", "#polkadot"
        ]
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "tweets_scraped": 0,
            "accounts_used": 0
        }

    def setup_database(self):
        """Setup database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL,
                    email_password TEXT NOT NULL,
                    auth_token TEXT NOT NULL,
                    ct0_token TEXT,
                    cookies TEXT,
                    last_used TIMESTAMP,
                    request_count INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_until TIMESTAMP,
                    success_rate REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Request logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_username TEXT,
                    query TEXT,
                    tweets_found INTEGER,
                    status TEXT,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migrate existing database if needed
            self.migrate_database(cursor)
            
            conn.commit()
    
    def migrate_database(self, cursor):
        """Migrate existing database to add missing columns"""
        try:
            # Check if success_rate column exists in accounts table
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'success_rate' not in columns:
                self.logger.info("Adding success_rate column to accounts table")
                cursor.execute("ALTER TABLE accounts ADD COLUMN success_rate REAL DEFAULT 1.0")
                
        except Exception as e:
            self.logger.error(f"Error during database migration: {e}")

    def load_accounts_from_file(self):
        """Load accounts from twitteracc.txt"""
        accounts = []
        try:
            with open("twitteracc.txt", "r") as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split(":")
                if len(parts) == 5:
                    username, password, email, email_password, auth_token = parts
                    accounts.append(TwitterAccount(
                        username=username,
                        password=password,
                        email=email,
                        email_password=email_password,
                        auth_token=auth_token
                    ))
            
            self.logger.info(f"Loaded {len(accounts)} accounts from twitteracc.txt")
            return accounts
                
        except FileNotFoundError:
            self.logger.error("twitteracc.txt not found")
            return []

    async def setup_twscrape_accounts(self):
        """Setup accounts in twscrape"""
        accounts = self.load_accounts_from_file()
        
        self.logger.info("Setting up accounts in twscrape...")
        
        for account in accounts[:10]:  # Use first 10 accounts for testing
            try:
                # Add account to twscrape
                await self.api.pool.add_account(
                    username=account.username,
                    password=account.password,
                    email=account.email,
                    email_password=account.email_password,
                    auth_token=account.auth_token
                )
                
                self.logger.info(f"Added account {account.username} to twscrape")
                
            except Exception as e:
                self.logger.warning(f"Failed to add account {account.username}: {e}")
        
        # Login accounts
        self.logger.info("Logging in accounts...")
        try:
            await self.api.pool.login_all()
            self.logger.info("Successfully logged in accounts")
        except Exception as e:
            self.logger.warning(f"Some accounts failed to login: {e}")

    def convert_tweet_to_data(self, tweet: Tweet) -> TweetData:
        """Convert twscrape Tweet object to our TweetData format"""
        # Extract hashtags from text
        hashtags = []
        if hasattr(tweet, 'hashtags') and tweet.hashtags:
            hashtags = [f"#{tag}" for tag in tweet.hashtags]
        else:
            # Extract hashtags from text manually
            import re
            hashtag_pattern = r'#\w+'
            hashtags = re.findall(hashtag_pattern, tweet.rawContent)
        
        # Extract media URLs
        media_urls = []
        if hasattr(tweet, 'media') and tweet.media:
            media_urls = [media.url for media in tweet.media if hasattr(media, 'url')]
        
        return TweetData(
            id=str(tweet.id),
            url=tweet.url,
            text=tweet.rawContent,
            author_username=tweet.user.username,
            author_display_name=tweet.user.displayname,
            created_at=tweet.date,
            like_count=tweet.likeCount or 0,
            retweet_count=tweet.retweetCount or 0,
            reply_count=tweet.replyCount or 0,
            quote_count=tweet.quoteCount or 0,
            hashtags=hashtags,
            media_urls=media_urls,
            is_retweet=hasattr(tweet, 'retweetedTweet') and tweet.retweetedTweet is not None,
            is_reply=hasattr(tweet, 'inReplyToTweetId') and tweet.inReplyToTweetId is not None,
            conversation_id=str(tweet.conversationId) if hasattr(tweet, 'conversationId') else str(tweet.id),
            raw_data=tweet.dict() if hasattr(tweet, 'dict') else {}
        )

    async def search_tweets(self, query: str, limit: int = 100) -> List[TweetData]:
        """Search for tweets using twscrape"""
        tweets = []
        
        try:
            self.logger.info(f"Searching for: {query} (limit: {limit})")
            
            # Use twscrape to search
            search_results = await gather(self.api.search(query, limit=limit))
            
            for tweet in search_results:
                try:
                    tweet_data = self.convert_tweet_to_data(tweet)
                    tweets.append(tweet_data)
                except Exception as e:
                    self.logger.warning(f"Error converting tweet: {e}")
                    continue
            
            self.logger.info(f"Found {len(tweets)} tweets for query: {query}")
            
            # Log request
            self.log_request(query, len(tweets), "success")
            
            self.stats["successful_requests"] += 1
            self.stats["tweets_scraped"] += len(tweets)
            
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {e}")
            self.log_request(query, 0, "error", str(e))
            self.stats["failed_requests"] += 1
        
        self.stats["total_requests"] += 1
        return tweets

    def log_request(self, query: str, tweets_found: int, status: str, error_message: str = None):
        """Log request details"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO request_logs 
                (query, tweets_found, status, error_message)
                VALUES (?, ?, ?, ?)
            """, (query, tweets_found, status, error_message))
            conn.commit()

    async def scrape_tweets(self, target_count: int = 1000) -> List[TweetData]:
        """Scrape tweets with modern methods"""
        all_tweets = []
        
        self.logger.info(f"Starting modern scrape for {target_count} tweets")
        
        # Generate search queries
        queries = []
        
        # Basic hashtag queries
        for hashtag in self.target_hashtags:
            queries.append(hashtag)
            queries.append(f"{hashtag} -filter:retweets")  # Original tweets only
            queries.append(f"{hashtag} filter:verified")   # Verified accounts
        
        # Time-based queries for freshness
        now = datetime.now()
        time_queries = [
            f"since:{now.strftime('%Y-%m-%d')}",
            f"since:{(now - timedelta(hours=12)).strftime('%Y-%m-%d')}",
            f"since:{(now - timedelta(days=1)).strftime('%Y-%m-%d')}"
        ]
        
        # Combine hashtags with time filters
        for time_q in time_queries:
            for hashtag in self.target_hashtags[:10]:  # Top 10 hashtags
                queries.append(f"{hashtag} {time_q}")
        
        # Popular crypto terms
        crypto_terms = [
            "bitcoin price", "crypto news", "blockchain technology",
            "DeFi protocol", "NFT marketplace", "Web3 development",
            "cryptocurrency trading", "digital assets", "smart contracts"
        ]
        
        for term in crypto_terms:
            queries.append(f'"{term}"')
            queries.append(f'"{term}" -filter:retweets')
        
        # Shuffle queries for better distribution
        random.shuffle(queries)
        
        # Calculate tweets per query
        tweets_per_query = max(20, target_count // len(queries))
        
        self.logger.info(f"Using {len(queries)} queries, {tweets_per_query} tweets per query")
        
        # Process queries
        for i, query in enumerate(queries):
            if len(all_tweets) >= target_count:
                break
            
            self.logger.info(f"Processing query {i+1}/{len(queries)}: {query}")
            
            try:
                # Search for tweets
                tweets = await self.search_tweets(query, tweets_per_query)
                all_tweets.extend(tweets)
                
                self.logger.info(f"Got {len(tweets)} tweets. Total: {len(all_tweets)}")
                
                # Random delay between requests
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error processing query '{query}': {e}")
                continue
        
        # Remove duplicates
        unique_tweets = {}
        for tweet in all_tweets:
            unique_tweets[tweet.id] = tweet
        
        final_tweets = list(unique_tweets.values())
        
        self.logger.info(f"Scraping completed. Unique tweets: {len(final_tweets)}")
        return final_tweets

    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Request stats
            cursor.execute("SELECT COUNT(*) FROM request_logs WHERE status = 'success' AND timestamp > datetime('now', '-24 hours')")
            successful_requests_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM request_logs WHERE timestamp > datetime('now', '-24 hours')")
            total_requests_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(tweets_found) FROM request_logs WHERE status = 'success' AND timestamp > datetime('now', '-24 hours')")
            tweets_scraped_24h = cursor.fetchone()[0] or 0
            
            stats = {
                "successful_requests_24h": successful_requests_24h,
                "total_requests_24h": total_requests_24h,
                "tweets_scraped_24h": tweets_scraped_24h,
                "success_rate_24h": (successful_requests_24h / total_requests_24h * 100) if total_requests_24h > 0 else 0,
                **self.stats
            }
            
            return stats

# CLI interface
async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Modern Twitter Miner")
    parser.add_argument("--scrape", type=int, default=1000, help="Number of tweets to scrape")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--test", type=int, help="Test scraping for N minutes")
    parser.add_argument("--setup", action="store_true", help="Setup accounts in twscrape")
    parser.add_argument("--continuous", action="store_true", help="Run continuous mining")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize miner
    miner = ModernTwitterMiner()
    
    if args.setup:
        print("🔧 Setting up accounts in twscrape...")
        await miner.setup_twscrape_accounts()
        print("✅ Account setup completed!")
        
    elif args.stats:
        print("📊 Modern Twitter Miner Statistics:")
        stats = miner.get_stats()
        print(json.dumps(stats, indent=2))
        
    elif args.test:
        print(f"🧪 Testing modern Twitter miner for {args.test} minutes...")
        
        # Setup accounts first
        await miner.setup_twscrape_accounts()
        
        # Calculate target tweets for test period
        target_tweets = args.test * 30  # 30 tweets per minute target
        
        start_time = time.time()
        tweets = await miner.scrape_tweets(target_tweets)
        elapsed_time = time.time() - start_time
        
        print(f"\n🎯 Test Results:")
        print(f"   Duration: {elapsed_time:.2f} seconds")
        print(f"   Tweets scraped: {len(tweets)}")
        print(f"   Rate: {len(tweets) / (elapsed_time / 60):.1f} tweets/minute")
        
        # Show sample tweets
        if tweets:
            print(f"\n📝 Sample tweets:")
            for i, tweet in enumerate(tweets[:5]):
                print(f"  {i+1}. @{tweet.author_username}: {tweet.text[:100]}...")
                print(f"     Created: {tweet.created_at}")
                print(f"     Hashtags: {tweet.hashtags}")
                print(f"     Engagement: {tweet.like_count} likes, {tweet.retweet_count} retweets")
        
        # Show final stats
        stats = miner.get_stats()
        print(f"\n📊 Final Statistics:")
        print(f"   Success rate: {stats.get('success_rate_24h', 0):.1f}%")
        print(f"   Total requests: {stats.get('total_requests', 0)}")
        print(f"   Successful requests: {stats.get('successful_requests', 0)}")
        
    elif args.continuous:
        print("⛏️  Starting continuous modern Twitter mining...")
        print("Target: 400,000 tweets per day (40% of subnet weight)")
        print("Use Ctrl+C to stop gracefully")
        
        # Setup accounts first
        await miner.setup_twscrape_accounts()
        
        try:
            while True:
                # Target: 400K tweets per day = ~16,667 tweets per hour
                hourly_target = 16667
                
                hour_start = time.time()
                tweets = await miner.scrape_tweets(hourly_target)
                hour_elapsed = time.time() - hour_start
                
                print(f"\n⏰ Hour completed:")
                print(f"   Tweets scraped: {len(tweets)}")
                print(f"   Time taken: {hour_elapsed:.2f} seconds")
                print(f"   Rate: {len(tweets) / (hour_elapsed / 60):.1f} tweets/minute")
                
                # Show stats
                stats = miner.get_stats()
                print(f"   Success rate: {stats.get('success_rate_24h', 0):.1f}%")
                print(f"   Total requests: {stats.get('total_requests', 0)}")
                
                # Wait for rest of hour
                remaining_time = 3600 - hour_elapsed
                if remaining_time > 0:
                    print(f"   Waiting {remaining_time:.0f} seconds until next hour...")
                    await asyncio.sleep(remaining_time)
                    
        except KeyboardInterrupt:
            print("\n👋 Stopping gracefully...")
            stats = miner.get_stats()
            print(f"Final stats: {json.dumps(stats, indent=2)}")
            
    else:
        print(f"🐦 Scraping {args.scrape} tweets using modern methods...")
        
        # Setup accounts first
        await miner.setup_twscrape_accounts()
        
        start_time = time.time()
        tweets = await miner.scrape_tweets(args.scrape)
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Scraping completed:")
        print(f"   Tweets scraped: {len(tweets)}")
        print(f"   Time taken: {elapsed_time:.2f} seconds")
        print(f"   Rate: {len(tweets) / (elapsed_time / 60):.1f} tweets/minute")
        
        # Show sample tweets
        if tweets:
            print(f"\n📝 Sample tweets:")
            for i, tweet in enumerate(tweets[:5]):
                print(f"  {i+1}. @{tweet.author_username}: {tweet.text[:100]}...")
                print(f"     Created: {tweet.created_at}")
                print(f"     Hashtags: {tweet.hashtags}")
                print(f"     Engagement: {tweet.like_count} likes, {tweet.retweet_count} retweets")
        
        # Show final stats
        stats = miner.get_stats()
        print(f"\n📊 Final Statistics:")
        print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
