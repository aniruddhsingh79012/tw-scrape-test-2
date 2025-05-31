import asyncio
import logging
import threading
import time
import json
import sys
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import signal

# Import existing scrapers from data-universe-main
sys.path.append('data-universe-main')
from scraping.reddit.reddit_custom_scraper import RedditCustomScraper
from scraping.youtube.youtube_custom_scraper import YouTubeTranscriptScraper
from scraping.scraper import ScrapeConfig
from common.data import DataLabel, DataSource
from common.date_range import DateRange

# Import our custom components
from enhanced_account_manager import EnhancedAccountManager
from enhanced_twitter_scraper import EnhancedTwitterScraper, TweetData
from optimized_data_storage import OptimizedDataStorage

class MultiPlatformMiner:
    """
    Complete multi-platform miner for Bittensor Subnet 13
    Integrates Twitter (40%), Reddit (60%), and YouTube scrapers
    Targets 1M+ daily scrapes across all platforms
    """
    
    def __init__(self, postgres_config: Dict[str, str]):
        self.postgres_config = postgres_config
        
        # Initialize platform scrapers
        self.account_manager = EnhancedAccountManager()
        self.twitter_scraper = EnhancedTwitterScraper(self.account_manager)
        self.reddit_scraper = RedditCustomScraper()
        self.youtube_scraper = YouTubeTranscriptScraper()
        self.storage = OptimizedDataStorage(postgres_config)
        
        # Platform targets based on subnet weights
        self.daily_targets = {
            "reddit": 600_000,    # 60% weight - HIGHEST PRIORITY
            "twitter": 400_000,   # 40% weight
            "youtube": 50_000     # Variable weight
        }
        
        # Hourly targets
        self.hourly_targets = {
            "reddit": self.daily_targets["reddit"] // 24,    # ~25K/hour
            "twitter": self.daily_targets["twitter"] // 24,  # ~16.7K/hour  
            "youtube": self.daily_targets["youtube"] // 24   # ~2K/hour
        }
        
        # Platform scheduling (prioritize Reddit due to 60% weight)
        self.platform_schedule = [
            {"platform": "reddit", "weight": 0.6, "priority": 1},
            {"platform": "twitter", "weight": 0.4, "priority": 2}, 
            {"platform": "youtube", "weight": 0.1, "priority": 3}
        ]
        
        # Statistics
        self.stats = {
            "total_scraped": 0,
            "total_stored": 0,
            "reddit_scraped": 0,
            "twitter_scraped": 0,
            "youtube_scraped": 0,
            "hourly_targets_met": 0,
            "daily_targets_met": 0,
            "uptime_hours": 0,
            "errors": 0
        }
        
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.should_stop = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True

    async def scrape_reddit_batch(self, target_posts: int) -> int:
        """Scrape Reddit posts using data-universe-main scraper"""
        try:
            self.logger.info(f"Starting Reddit scrape for {target_posts} posts")
            
            # High-value subreddits from subnet config
            reddit_labels = [
                "r/Bitcoin", "r/BitcoinCash", "r/Bittensor_", "r/btc",
                "r/Cryptocurrency", "r/Cryptomarkets", "r/EthereumClassic", 
                "r/ethtrader", "r/Filecoin", "r/Monero", "r/Polkadot",
                "r/solana", "r/wallstreetbets"
            ]
            
            all_entities = []
            posts_per_subreddit = max(50, target_posts // len(reddit_labels))
            
            # Scrape each subreddit
            for subreddit in reddit_labels:
                if self.should_stop:
                    break
                
                try:
                    # Create scrape config for recent data (last 24 hours)
                    scrape_config = ScrapeConfig(
                        entity_limit=posts_per_subreddit,
                        date_range=DateRange(
                            start=datetime.now() - timedelta(hours=24),
                            end=datetime.now()
                        ),
                        labels=[DataLabel(value=subreddit)]
                    )
                    
                    # Scrape subreddit
                    entities = await self.reddit_scraper.scrape(scrape_config)
                    all_entities.extend(entities)
                    
                    self.logger.info(f"Scraped {len(entities)} posts from {subreddit}")
                    
                    # Small delay between subreddits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping {subreddit}: {e}")
                    continue
            
            # Store Reddit data
            stored_count = 0
            if all_entities:
                # Convert to our storage format and store
                stored_count = await self.store_reddit_entities(all_entities)
            
            # Update statistics
            self.stats["reddit_scraped"] += len(all_entities)
            self.stats["total_scraped"] += len(all_entities)
            self.stats["total_stored"] += stored_count
            
            self.logger.info(f"Reddit batch completed: {len(all_entities)} scraped, {stored_count} stored")
            return stored_count
            
        except Exception as e:
            self.logger.error(f"Error in Reddit batch scrape: {e}")
            self.stats["errors"] += 1
            return 0

    async def scrape_youtube_batch(self, target_videos: int) -> int:
        """Scrape YouTube videos using data-universe-main scraper"""
        try:
            self.logger.info(f"Starting YouTube scrape for {target_videos} videos")
            
            # High-value YouTube channels from subnet config
            youtube_labels = [
                "#ytc_c_UCAuUUnT6oDeKwE6v1NGQxug",  # TED
                "#ytc_c_UCYO_jab_esuFRV4b17AJtAw",  # 3Blue1Brown
                "#ytc_c_UCsXVk37bltHxD1rDPwtNM8Q",  # Kurzgesagt
                "#ytc_c_UCSHZKyawb77ixDdsGog4iWA",  # Lex Fridman
                "#ytc_c_UCR93yACeNzxMSk6Y1cHM2pA",  # Coin Bureau
                "#ytc_c_UCbLhGKVY-bJPcawebgtNfbw"   # Digital Asset News
            ]
            
            all_entities = []
            videos_per_channel = max(10, target_videos // len(youtube_labels))
            
            # Scrape each channel
            for channel_label in youtube_labels:
                if self.should_stop:
                    break
                
                try:
                    # Create scrape config for recent videos (last 30 days)
                    scrape_config = ScrapeConfig(
                        entity_limit=videos_per_channel,
                        date_range=DateRange(
                            start=datetime.now() - timedelta(days=30),
                            end=datetime.now()
                        ),
                        labels=[DataLabel(value=channel_label)]
                    )
                    
                    # Scrape channel
                    entities = await self.youtube_scraper.scrape(scrape_config)
                    all_entities.extend(entities)
                    
                    self.logger.info(f"Scraped {len(entities)} videos from {channel_label}")
                    
                    # Longer delay for YouTube API limits
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping {channel_label}: {e}")
                    continue
            
            # Store YouTube data
            stored_count = 0
            if all_entities:
                stored_count = await self.store_youtube_entities(all_entities)
            
            # Update statistics
            self.stats["youtube_scraped"] += len(all_entities)
            self.stats["total_scraped"] += len(all_entities)
            self.stats["total_stored"] += stored_count
            
            self.logger.info(f"YouTube batch completed: {len(all_entities)} scraped, {stored_count} stored")
            return stored_count
            
        except Exception as e:
            self.logger.error(f"Error in YouTube batch scrape: {e}")
            self.stats["errors"] += 1
            return 0

    async def scrape_twitter_batch(self, target_tweets: int) -> int:
        """Scrape Twitter using our enhanced scraper"""
        try:
            self.logger.info(f"Starting Twitter scrape for {target_tweets} tweets")
            
            # Use our existing Twitter scraper
            tweets = await self.twitter_scraper.scrape_for_target(target_tweets)
            
            # Store Twitter data
            stored_count = 0
            if tweets:
                stored_count = await self.store_twitter_tweets(tweets)
            
            # Update statistics
            self.stats["twitter_scraped"] += len(tweets)
            self.stats["total_scraped"] += len(tweets)
            self.stats["total_stored"] += stored_count
            
            self.logger.info(f"Twitter batch completed: {len(tweets)} scraped, {stored_count} stored")
            return stored_count
            
        except Exception as e:
            self.logger.error(f"Error in Twitter batch scrape: {e}")
            self.stats["errors"] += 1
            return 0

    async def store_reddit_entities(self, entities: List) -> int:
        """Store Reddit entities in our optimized storage"""
        try:
            # Convert Reddit entities to our TweetData format for unified storage
            converted_tweets = []
            
            for entity in entities:
                # Parse Reddit content from entity
                content_str = entity.content.decode('utf-8')
                content_data = json.loads(content_str)
                
                # Create TweetData-like object for Reddit posts
                tweet_data = TweetData(
                    id=content_data.get("id", ""),
                    url=entity.uri,
                    text=content_data.get("body", "") or content_data.get("title", ""),
                    author_username=content_data.get("username", ""),
                    author_display_name=content_data.get("username", ""),
                    created_at=entity.datetime,
                    like_count=0,  # Reddit doesn't have likes
                    retweet_count=0,
                    reply_count=0,
                    quote_count=0,
                    hashtags=[entity.label.value] if entity.label else [],
                    media_urls=[],
                    is_retweet=False,
                    is_reply=content_data.get("parentId") is not None,
                    conversation_id=content_data.get("id", ""),
                    raw_data=content_data
                )
                
                converted_tweets.append(tweet_data)
            
            # Store using our optimized storage
            return self.storage.store_tweets_batch(converted_tweets)
            
        except Exception as e:
            self.logger.error(f"Error storing Reddit entities: {e}")
            return 0

    async def store_youtube_entities(self, entities: List) -> int:
        """Store YouTube entities in our optimized storage"""
        try:
            # Convert YouTube entities to our TweetData format for unified storage
            converted_tweets = []
            
            for entity in entities:
                # Parse YouTube content from entity
                content_str = entity.content.decode('utf-8')
                content_data = json.loads(content_str)
                
                # Create TweetData-like object for YouTube videos
                tweet_data = TweetData(
                    id=content_data.get("video_id", ""),
                    url=entity.uri,
                    text=content_data.get("transcript", "")[:1000],  # Truncate for storage
                    author_username=content_data.get("channel_name", ""),
                    author_display_name=content_data.get("channel_name", ""),
                    created_at=entity.datetime,
                    like_count=0,
                    retweet_count=0,
                    reply_count=0,
                    quote_count=0,
                    hashtags=[entity.label.value] if entity.label else [],
                    media_urls=[entity.uri],
                    is_retweet=False,
                    is_reply=False,
                    conversation_id=content_data.get("video_id", ""),
                    raw_data=content_data
                )
                
                converted_tweets.append(tweet_data)
            
            # Store using our optimized storage
            return self.storage.store_tweets_batch(converted_tweets)
            
        except Exception as e:
            self.logger.error(f"Error storing YouTube entities: {e}")
            return 0

    async def store_twitter_tweets(self, tweets: List[TweetData]) -> int:
        """Store Twitter tweets using our optimized storage"""
        try:
            return self.storage.store_tweets_batch(tweets)
        except Exception as e:
            self.logger.error(f"Error storing Twitter tweets: {e}")
            return 0

    async def hourly_multi_platform_cycle(self) -> Dict[str, Any]:
        """Execute one hour of multi-platform scraping"""
        
        cycle_start = time.time()
        self.logger.info("Starting hourly multi-platform scrape cycle")
        
        # Reset banned accounts
        self.account_manager.reset_banned_accounts()
        
        total_scraped = 0
        total_stored = 0
        
        # Platform scraping in priority order
        platform_results = {}
        
        # 1. Reddit (60% weight - HIGHEST PRIORITY)
        reddit_target = self.hourly_targets["reddit"]
        self.logger.info(f"Phase 1: Reddit scraping - Target: {reddit_target}")
        reddit_stored = await self.scrape_reddit_batch(reddit_target)
        platform_results["reddit"] = reddit_stored
        total_stored += reddit_stored
        
        # 2. Twitter (40% weight)
        twitter_target = self.hourly_targets["twitter"]
        self.logger.info(f"Phase 2: Twitter scraping - Target: {twitter_target}")
        twitter_stored = await self.scrape_twitter_batch(twitter_target)
        platform_results["twitter"] = twitter_stored
        total_stored += twitter_stored
        
        # 3. YouTube (Variable weight)
        youtube_target = self.hourly_targets["youtube"]
        self.logger.info(f"Phase 3: YouTube scraping - Target: {youtube_target}")
        youtube_stored = await self.scrape_youtube_batch(youtube_target)
        platform_results["youtube"] = youtube_stored
        total_stored += youtube_stored
        
        cycle_time = time.time() - cycle_start
        
        # Check if hourly target was met (80% threshold)
        total_target = sum(self.hourly_targets.values())
        target_met = total_stored >= total_target * 0.8
        
        if target_met:
            self.stats["hourly_targets_met"] += 1
        
        cycle_stats = {
            "total_stored": total_stored,
            "platform_results": platform_results,
            "cycle_time_seconds": cycle_time,
            "target_met": target_met,
            "items_per_second": total_stored / cycle_time if cycle_time > 0 else 0
        }
        
        self.logger.info(f"Hourly cycle completed: {json.dumps(cycle_stats, indent=2)}")
        
        return cycle_stats

    async def daily_monitoring_report(self):
        """Generate daily monitoring report"""
        
        # Get comprehensive statistics
        storage_stats = self.storage.get_storage_stats()
        account_stats = self.account_manager.get_account_stats()
        
        # Calculate performance metrics
        daily_scraped = self.stats["total_scraped"]
        daily_target = sum(self.daily_targets.values())
        daily_target_met = daily_scraped >= daily_target * 0.8
        
        if daily_target_met:
            self.stats["daily_targets_met"] += 1
        
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "performance": {
                "total_scraped_24h": daily_scraped,
                "reddit_scraped_24h": self.stats["reddit_scraped"],
                "twitter_scraped_24h": self.stats["twitter_scraped"],
                "youtube_scraped_24h": self.stats["youtube_scraped"],
                "daily_target": daily_target,
                "target_achievement": (daily_scraped / daily_target) * 100,
                "target_met": daily_target_met
            },
            "platform_breakdown": {
                "reddit": {
                    "scraped": self.stats["reddit_scraped"],
                    "target": self.daily_targets["reddit"],
                    "weight": "60%"
                },
                "twitter": {
                    "scraped": self.stats["twitter_scraped"],
                    "target": self.daily_targets["twitter"],
                    "weight": "40%"
                },
                "youtube": {
                    "scraped": self.stats["youtube_scraped"],
                    "target": self.daily_targets["youtube"],
                    "weight": "Variable"
                }
            },
            "accounts": account_stats,
            "storage": storage_stats,
            "system": {
                "uptime_hours": self.stats["uptime_hours"],
                "errors": self.stats["errors"],
                "hourly_targets_met": self.stats["hourly_targets_met"]
            }
        }
        
        self.logger.info(f"Daily Report: {json.dumps(report, indent=2, default=str)}")
        
        # Save report to file
        report_file = f"multi_platform_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report

    async def run_continuous(self):
        """Run continuous multi-platform scraping"""
        
        self.logger.info("Starting multi-platform continuous scraping")
        self.logger.info(f"Daily targets: Reddit={self.daily_targets['reddit']:,}, Twitter={self.daily_targets['twitter']:,}, YouTube={self.daily_targets['youtube']:,}")
        
        self.is_running = True
        start_time = time.time()
        last_daily_report = datetime.now().date()
        
        try:
            while not self.should_stop:
                hour_start = time.time()
                
                # Execute hourly multi-platform cycle
                cycle_stats = await self.hourly_multi_platform_cycle()
                
                # Update uptime
                self.stats["uptime_hours"] = (time.time() - start_time) / 3600
                
                # Generate daily report if it's a new day
                current_date = datetime.now().date()
                if current_date > last_daily_report:
                    await self.daily_monitoring_report()
                    last_daily_report = current_date
                    
                    # Reset daily statistics
                    self.stats["total_scraped"] = 0
                    self.stats["reddit_scraped"] = 0
                    self.stats["twitter_scraped"] = 0
                    self.stats["youtube_scraped"] = 0
                
                # Wait for the rest of the hour
                hour_elapsed = time.time() - hour_start
                remaining_time = 3600 - hour_elapsed
                
                if remaining_time > 0:
                    self.logger.info(f"Hour completed in {hour_elapsed:.2f}s. Waiting {remaining_time:.2f}s until next hour")
                    await asyncio.sleep(remaining_time)
                
        except Exception as e:
            self.logger.error(f"Critical error in continuous scraping: {e}")
            self.stats["errors"] += 1
        
        finally:
            self.is_running = False
            self.logger.info("Multi-platform scraping stopped")

    async def run_test(self, duration_minutes: int = 10):
        """Run a test multi-platform session"""
        
        self.logger.info(f"Starting {duration_minutes}-minute multi-platform test")
        
        # Calculate test targets
        test_targets = {
            "reddit": (self.hourly_targets["reddit"] * duration_minutes) // 60,
            "twitter": (self.hourly_targets["twitter"] * duration_minutes) // 60,
            "youtube": (self.hourly_targets["youtube"] * duration_minutes) // 60
        }
        
        self.logger.info(f"Test targets: {test_targets}")
        
        start_time = time.time()
        
        # Run test scraping for each platform
        reddit_stored = await self.scrape_reddit_batch(test_targets["reddit"])
        twitter_stored = await self.scrape_twitter_batch(test_targets["twitter"])
        youtube_stored = await self.scrape_youtube_batch(test_targets["youtube"])
        
        elapsed_time = time.time() - start_time
        total_stored = reddit_stored + twitter_stored + youtube_stored
        total_target = sum(test_targets.values())
        
        # Generate test report
        test_report = {
            "duration_minutes": duration_minutes,
            "targets": test_targets,
            "results": {
                "reddit_stored": reddit_stored,
                "twitter_stored": twitter_stored,
                "youtube_stored": youtube_stored,
                "total_stored": total_stored
            },
            "elapsed_time_seconds": elapsed_time,
            "items_per_minute": total_stored / (elapsed_time / 60),
            "success_rate": (total_stored / total_target) * 100 if total_target > 0 else 0
        }
        
        self.logger.info(f"Multi-platform test completed: {json.dumps(test_report, indent=2)}")
        
        return test_report

# Main execution
async def main():
    # PostgreSQL configuration
    postgres_config = {
        "dbname": "postgres",
        "user": "postgres",
        "password": "postgres",  # Change this to your password
        "host": "localhost",
        "port": 5432
    }
    
    # Initialize the multi-platform miner
    miner = MultiPlatformMiner(postgres_config)
    
    # Choose operation mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run test mode
        test_duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        await miner.run_test(test_duration)
    else:
        # Run continuous mode
        await miner.run_continuous()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('multi_platform_miner.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Run the multi-platform miner
    asyncio.run(main())
