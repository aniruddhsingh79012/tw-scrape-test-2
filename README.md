# Bittensor-Optimized Twitter Scraper

A high-performance, ban-resistant Twitter scraping system optimized for Bittensor Subnet 13 (Data Universe) with support for 1M+ daily scrapes using 50 accounts and 500 proxies.

## 🚀 Features

### Core Capabilities
- **1M+ Daily Scrapes**: Optimized for high-volume data collection
- **50 Account Management**: Intelligent rotation with ban prevention
- **500 Proxy Rotation**: Distributed load across proxy pool
- **Bittensor Subnet Optimization**: Aligned with subnet scoring mechanisms
- **Dual Database Storage**: PostgreSQL + SQLite (Bittensor compatible)
- **Real-time Monitoring**: Comprehensive statistics and reporting

### Ban Prevention & Robustness
- **Smart Account Rotation**: 15-minute cooldowns between uses
- **Proxy Load Balancing**: 5-minute cooldowns with failure tracking
- **Ban Detection**: Automatic detection and 24-hour recovery
- **Rate Limiting**: Configurable request limits per account/proxy
- **Error Recovery**: Automatic retry with exponential backoff

### Bittensor Subnet Alignment
- **Data Freshness Priority**: Recent tweets score higher
- **Desirability Tracking**: Focus on trending and valuable content
- **Quality Filtering**: Engagement-based content selection
- **Label Optimization**: Hashtag-based categorization
- **Time Bucket Organization**: Hourly data grouping

## 📁 Project Structure

```
├── enhanced_account_manager.py     # Account & proxy management
├── enhanced_twitter_scraper.py     # High-performance scraper
├── optimized_data_storage.py       # Dual database storage
├── bittensor_optimized_miner.py    # Main orchestrator
├── setup_and_run.py               # Setup & execution script
├── twitteracc.txt                 # Twitter accounts (50 accounts)
├── proxy.txt                      # Proxy list (500 proxies)
├── config.json                    # Configuration file
└── README.md                      # This file
```

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- 50 Twitter accounts with auth tokens
- 500 working proxies

### Quick Start

1. **Clone and Setup**
```bash
git clone <repository>
cd twitter-scraper
python setup_and_run.py
```

2. **Account Format** (twitteracc.txt)
```
username:password:email:email_password:auth_token
```

3. **Proxy Format** (proxy.txt)
```
ip:port:username:password
```

### Manual Installation

1. **Install Dependencies**
```bash
pip install aiohttp psycopg2-binary requests schedule python-dotenv
```

2. **Setup PostgreSQL**
```bash
# Create database
createdb postgres
# Update credentials in config.json
```

3. **Run System**
```bash
# Test mode (5 minutes)
python bittensor_optimized_miner.py test 5

# Continuous mode
python bittensor_optimized_miner.py
```

## ⚙️ Configuration

### Database Configuration
```json
{
  "postgres": {
    "dbname": "postgres",
    "user": "postgres", 
    "password": "your_password",
    "host": "localhost",
    "port": 5432
  }
}
```

### Performance Tuning
```json
{
  "scraping": {
    "target_tweets_per_day": 1000000,
    "max_concurrent_requests": 20,
    "account_cooldown_minutes": 15,
    "proxy_cooldown_minutes": 5
  }
}
```

## 📊 Performance Targets

| Metric | Target | Actual Performance |
|--------|--------|-------------------|
| Daily Tweets | 1,000,000+ | Optimized for target |
| Hourly Tweets | ~42,000 | 6 batches of ~7K |
| Per Minute | ~700 | Distributed load |
| Account Utilization | 50 accounts | Smart rotation |
| Proxy Utilization | 500 proxies | Load balanced |
| Ban Rate | <1% | Robust prevention |

## 🎯 Bittensor Subnet Optimization

### Scoring Factors
1. **Data Freshness (40%)**: Recent tweets score higher
2. **Engagement Quality (30%)**: Likes, retweets, replies
3. **Content Quality (20%)**: Length, media, originality
4. **Desirability (10%)**: Relevant hashtags and topics

### Target Keywords
```python
HIGH_VALUE_KEYWORDS = [
    "#bitcoin", "#bittensor", "#tao", "#crypto", "#ai",
    "#blockchain", "#defi", "#web3", "#ethereum"
]
```

### Time Optimization
- **Current Hour**: Maximum freshness score
- **Last 6 Hours**: High freshness score  
- **Last 24 Hours**: Moderate freshness score
- **Older**: Minimal score

## 📈 Monitoring & Analytics

### Real-time Statistics
- Tweets scraped per second
- Account/proxy utilization
- Success/failure rates
- Ban incidents
- Storage efficiency

### Daily Reports
```json
{
  "date": "2025-01-31",
  "performance": {
    "tweets_scraped_24h": 1050000,
    "target_achievement": 105.0,
    "target_met": true
  },
  "accounts": {
    "active_accounts": 49,
    "banned_accounts": 1,
    "success_rate_24h": 98.5
  }
}
```

### Log Files
- `bittensor_miner.log`: Main application logs
- `daily_report_YYYYMMDD.json`: Daily performance reports
- `enhanced_accounts.db`: Account management database

## 🔧 Advanced Usage

### Custom Scraping Targets
```python
# Modify target keywords in bittensor_optimized_miner.py
base_keywords = [
    "#your_custom_hashtag",
    "#trending_topic"
]
```

### Database Queries
```sql
-- Get recent tweets
SELECT * FROM data_entities 
WHERE datetime > NOW() - INTERVAL '1 hour'
ORDER BY datetime DESC;

-- Get tweets by hashtag
SELECT * FROM data_entities 
WHERE '#bitcoin' = ANY(hashtags);
```

### Account Management
```python
# Check account status
from enhanced_account_manager import EnhancedAccountManager
manager = EnhancedAccountManager()
stats = manager.get_account_stats()
print(stats)
```

## 🚨 Troubleshooting

### Common Issues

1. **No Available Accounts**
   - Check account ban status
   - Verify ct0 tokens are valid
   - Reduce request frequency

2. **Proxy Failures**
   - Test proxy connectivity
   - Check proxy credentials
   - Rotate to different proxy pool

3. **Database Errors**
   - Verify PostgreSQL is running
   - Check connection credentials
   - Ensure sufficient disk space

4. **Low Scraping Rate**
   - Increase concurrent requests
   - Reduce cooldown times
   - Add more accounts/proxies

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python bittensor_optimized_miner.py
```

## 📋 API Reference

### Main Classes

#### `EnhancedAccountManager`
- Manages 50 Twitter accounts and 500 proxies
- Handles rotation, cooldowns, and ban detection
- Provides account-proxy pairing

#### `EnhancedTwitterScraper`
- High-performance async scraping
- GraphQL API integration
- Concurrent request management

#### `OptimizedDataStorage`
- Dual database storage (PostgreSQL + SQLite)
- Batch processing for efficiency
- Bittensor format compatibility

#### `BittensorOptimizedMiner`
- Main orchestrator
- Subnet scoring optimization
- Performance monitoring

## 🔐 Security & Compliance

### Data Protection
- Compressed storage to minimize space
- Automatic cleanup of old data
- No personal data retention beyond necessary

### Rate Limiting
- Account-level rate limiting
- Proxy-level rate limiting
- Global request throttling

### Error Handling
- Graceful degradation
- Automatic recovery
- Comprehensive logging

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📞 Support

For issues and questions:
- Create GitHub issue
- Check troubleshooting section
- Review logs for error details

## 🎯 Roadmap

### Upcoming Features
- [ ] Machine learning for ban prediction
- [ ] Dynamic proxy acquisition
- [ ] Real-time trending topic detection
- [ ] Advanced content filtering
- [ ] Multi-platform support (Reddit, YouTube)

### Performance Improvements
- [ ] GPU acceleration for processing
- [ ] Distributed scraping across multiple servers
- [ ] Advanced caching mechanisms
- [ ] Real-time data streaming

---

**Built for Bittensor Subnet 13 - Optimized for 1M+ daily scrapes with maximum ban resistance**
