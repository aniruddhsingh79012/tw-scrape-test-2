import asyncio
import asyncpraw
import json
import time
import random
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import threading
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class RedditPost:
    id: str
    url: str
    title: str
    text: str
    author: str
    subreddit: str
    created_at: datetime
    score: int
    num_comments: int
    is_self: bool
    permalink: str
    raw_data: Dict[str, Any]

class EnhancedRedditScraper:
    """
    High-performance Reddit scraper optimized for Bittensor Subnet 13
    Targets 600K+ posts daily (60% of subnet scoring weight)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Reddit API credentials from environment
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        self.user_agent = f"BittensorMiner:v1.0 (by /u/{self.username})"
        
        # Performance settings for 600K daily posts
        self.max_concurrent_requests = 10
        self.request_delay_range = (1, 2)  # Respect Reddit rate limits
        self.max_retries = 3
        
        # Bittensor subnet high-value subreddits (1.0 weight)
        self.target_subreddits = [
            "Bitcoin", "BitcoinCash", "Bittensor_", "btc", 
            "CryptoCurrency", "CryptoMarkets", "EthereumClassic",
            "ethtrader", "Filecoin", "Monero", "Polkadot", 
            "solana", "wallstreetbets"
        ]
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "posts_scraped": 0,
            "comments_scraped": 0
        }
        
        self.stats_lock = threading.Lock()

    async def get_reddit_session(self) -> asyncpraw.Reddit:
        """Create authenticated Reddit session"""
        return asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            user_agent=self.user_agent
        )

    async def scrape_subreddit_posts(self, subreddit_name: str, limit: int = 100, 
                                   sort_type: str = "new") -> List[RedditPost]:
        """Scrape posts from a specific subreddit"""
        posts = []
        
        try:
            async with await self.get_reddit_session() as reddit:
                subreddit = await reddit.subreddit(subreddit_name)
                
                # Get posts based on sort type
                if sort_type == "new":
                    submissions = subreddit.new(limit=limit)
                elif sort_type == "hot":
                    submissions = subreddit.hot(limit=limit)
                elif sort_type == "top":
                    submissions = subreddit.top(limit=limit, time_filter="day")
                else:
                    submissions = subreddit.new(limit=limit)
                
                async for submission in submissions:
                    try:
                        # Parse submission data
                        post = await self._parse_submission(submission, subreddit_name)
                        if post:
                            posts.append(post)
                            
                    except Exception as e:
                        self.logger.error(f"Error parsing submission: {e}")
                        continue
                
                # Update statistics
                with self.stats_lock:
                    self.stats["total_requests"] += 1
                    self.stats["successful_requests"] += 1
                    self.stats["posts_scraped"] += len(posts)
                
        except Exception as e:
            self.logger.error(f"Error scraping subreddit {subreddit_name}: {e}")
            with self.stats_lock:
                self.stats["total_requests"] += 1
                self.stats["failed_requests"] += 1
        
        return posts

    async def scrape_subreddit_comments(self, subreddit_name: str, limit: int = 100) -> List[RedditPost]:
        """Scrape recent comments from a subreddit"""
        comments = []
        
        try:
            async with await self.get_reddit_session() as reddit:
                subreddit = await reddit.subreddit(subreddit_name)
                
                async for comment in subreddit.comments(limit=limit):
                    try:
                        # Parse comment data
                        comment_post = await self._parse_comment(comment, subreddit_name)
                        if comment_post:
                            comments.append(comment_post)
                            
                    except Exception as e:
                        self.logger.error(f"Error parsing comment: {e}")
                        continue
                
                # Update statistics
                with self.stats_lock:
                    self.stats["comments_scraped"] += len(comments)
                
        except Exception as e:
            self.logger.error(f"Error scraping comments from {subreddit_name}: {e}")
        
        return comments

    async def _parse_submission(self, submission, subreddit_name: str) -> Optional[RedditPost]:
        """Parse Reddit submission into RedditPost object"""
        try:
            # Get author name safely
            author_name = submission.author.name if submission.author else "[deleted]"
            
            # Create post object
            post = RedditPost(
                id=submission.id,
                url=f"https://www.reddit.com{submission.permalink}",
                title=submission.title,
                text=submission.selftext or "",
                author=author_name,
                subreddit=f"r/{subreddit_name}",
                created_at=datetime.fromtimestamp(submission.created_utc),
                score=submission.score,
                num_comments=submission.num_comments,
                is_self=submission.is_self,
                permalink=submission.permalink,
                raw_data={
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "author": author_name,
                    "subreddit": f"r/{subreddit_name}",
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "url": submission.url,
                    "permalink": submission.permalink,
                    "is_self": submission.is_self
                }
            )
            
            return post
            
        except Exception as e:
            self.logger.error(f"Error parsing submission: {e}")
            return None

    async def _parse_comment(self, comment, subreddit_name: str) -> Optional[RedditPost]:
        """Parse Reddit comment into RedditPost object"""
        try:
            # Get author name safely
            author_name = comment.author.name if comment.author else "[deleted]"
            
            # Create comment as post object
            post = RedditPost(
                id=comment.id,
                url=f"https://www.reddit.com{comment.permalink}",
                title="",  # Comments don't have titles
                text=comment.body,
                author=author_name,
                subreddit=f"r/{subreddit_name}",
                created_at=datetime.fromtimestamp(comment.created_utc),
                score=comment.score,
                num_comments=0,  # Comments don't have sub-comments in this context
                is_self=False,
                permalink=comment.permalink,
                raw_data={
                    "id": comment.id,
                    "body": comment.body,
                    "author": author_name,
                    "subreddit": f"r/{subreddit_name}",
                    "created_utc": comment.created_utc,
                    "score": comment.score,
                    "permalink": comment.permalink,
                    "parent_id": comment.parent_id
                }
            )
            
            return post
            
        except Exception as e:
            self.logger.error(f"Error parsing comment: {e}")
            return None

    async def scrape_batch_optimized(self, target_posts: int) -> List[RedditPost]:
        """Scrape Reddit posts optimized for Bittensor subnet scoring"""
        all_posts = []
        
        # Calculate posts per subreddit
        posts_per_subreddit = max(50, target_posts // len(self.target_subreddits))
        
        self.logger.info(f"Starting Reddit scrape for {target_posts} posts across {len(self.target_subreddits)} subreddits")
        
        # Create semaphore for concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def scrape_single_subreddit(subreddit: str) -> List[RedditPost]:
            async with semaphore:
                # Random delay to avoid overwhelming Reddit
                delay = random.uniform(*self.request_delay_range)
                await asyncio.sleep(delay)
                
                # Scrape both posts and comments for maximum data
                posts = await self.scrape_subreddit_posts(subreddit, posts_per_subreddit // 2, "new")
                comments = await self.scrape_subreddit_comments(subreddit, posts_per_subreddit // 2)
                
                return posts + comments
        
        # Execute all subreddit scrapes concurrently
        tasks = [scrape_single_subreddit(subreddit) for subreddit in self.target_subreddits]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        for result in results:
            if isinstance(result, list):
                all_posts.extend(result)
            else:
                self.logger.error(f"Subreddit scrape failed: {result}")
        
        # Filter for quality and recency (last 24 hours)
        filtered_posts = self.filter_posts_for_subnet(all_posts)
        
        self.logger.info(f"Reddit scrape completed: {len(all_posts)} total, {len(filtered_posts)} after filtering")
        
        return filtered_posts

    def filter_posts_for_subnet(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Filter Reddit posts for maximum Bittensor subnet scoring"""
        
        if not posts:
            return posts
        
        # Sort by subnet scoring criteria
        def subnet_score(post: RedditPost) -> float:
            score = 0.0
            
            # Freshness score (newer = higher)
            age_hours = (datetime.now() - post.created_at).total_seconds() / 3600
            freshness_score = max(0, 1.0 - (age_hours / 24))  # Linear decay over 24 hours
            score += freshness_score * 0.4
            
            # Engagement score (higher score = higher value)
            engagement_score = min(1.0, max(0, post.score) / 100)  # Normalize to 0-1
            score += engagement_score * 0.3
            
            # Content quality score
            quality_score = 0.0
            if len(post.text) > 50:  # Substantial content
                quality_score += 0.4
            if post.title and len(post.title) > 10:  # Good title
                quality_score += 0.3
            if not post.author == "[deleted]":  # Valid author
                quality_score += 0.3
            
            score += quality_score * 0.2
            
            # Subreddit value (all our target subreddits are high-value)
            score += 0.1  # Bonus for being in target subreddit
            
            return score
        
        # Sort by subnet score and take top posts
        scored_posts = [(post, subnet_score(post)) for post in posts]
        scored_posts.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 80% of posts by score
        top_count = int(len(scored_posts) * 0.8)
        filtered_posts = [post for post, score in scored_posts[:top_count]]
        
        return filtered_posts

    async def scrape_for_target(self, target_posts: int = 25000) -> List[RedditPost]:
        """Scrape Reddit posts to reach a target number"""
        self.logger.info(f"Starting Reddit scrape for {target_posts} posts")
        
        # Scrape in batches to manage memory and rate limits
        batch_size = 5000
        all_posts = []
        
        for i in range(0, target_posts, batch_size):
            batch_target = min(batch_size, target_posts - len(all_posts))
            
            self.logger.info(f"Processing batch {i//batch_size + 1}, target: {batch_target}")
            
            batch_posts = await self.scrape_batch_optimized(batch_target)
            all_posts.extend(batch_posts)
            
            self.logger.info(f"Batch completed. Total posts: {len(all_posts)}")
            
            # Check if we've reached our target
            if len(all_posts) >= target_posts:
                break
            
            # Small delay between batches
            await asyncio.sleep(2)
        
        # Remove duplicates based on post ID
        unique_posts = {}
        for post in all_posts:
            unique_posts[post.id] = post
        
        final_posts = list(unique_posts.values())
        
        self.logger.info(f"Reddit scraping completed. Total unique posts: {len(final_posts)}")
        
        return final_posts

    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        with self.stats_lock:
            return self.stats.copy()

# Example usage
async def main():
    # Initialize Reddit scraper
    scraper = EnhancedRedditScraper()
    
    # Test scraping
    posts = await scraper.scrape_for_target(1000)  # Test with 1000 posts
    
    print(f"Scraped {len(posts)} Reddit posts")
    
    # Print some sample posts
    for i, post in enumerate(posts[:5]):
        print(f"\nPost {i+1}:")
        print(f"  Subreddit: {post.subreddit}")
        print(f"  Title: {post.title[:100]}...")
        print(f"  Author: {post.author}")
        print(f"  Score: {post.score}")
        print(f"  Comments: {post.num_comments}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
