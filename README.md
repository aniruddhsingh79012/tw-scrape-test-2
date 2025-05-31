# 🚀 Bittensor Twitter Mining System

A production-ready Twitter mining system designed for Bittensor subnet with PostgreSQL storage in exact data-universe-main format.

## 🎯 Features

### ✅ **Bittensor Compliance**
- **100% data-universe-main compatible** storage format
- **PostgreSQL backend** with exact Bittensor schema
- **DataSource.X (source=2)** for Twitter/X data
- **TimeBucket calculation** (hours since epoch)
- **Proper indexing** for validator compatibility

### ✅ **Production Ready**
- **Proxy rotation** with 500+ proxies
- **Account management** with 50+ Twitter accounts
- **Rate limiting protection** and ban recovery
- **Continuous mining** with configurable targets
- **Real-time monitoring** and statistics

### ✅ **High Performance**
- **Concurrent processing** with async operations
- **Smart proxy selection** and health monitoring
- **Automatic recovery** from bans and failures
- **Efficient storage** with PostgreSQL ACID compliance
- **No hanging issues** - direct database operations

## 📋 Requirements

### System Requirements
- **Python 3.8+**
- **PostgreSQL 12+**
- **Linux/Ubuntu** (recommended)
- **4GB+ RAM**
- **10GB+ storage**

### Python Dependencies
```bash
pip install asyncio aiohttp psycopg2-binary twscrape
```

### PostgreSQL Setup
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb bittensor_mining

# Set password
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# Test connection
psql -h localhost -U postgres -d bittensor_mining -c "SELECT version();"
```

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd twitter-mining-system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
# OR manually:
pip install asyncio aiohttp psycopg2-binary twscrape
```

### 3. Setup Configuration Files

#### **Twitter Accounts (twitteracc.txt)**
```
username1:password1:email1:email_password1:auth_token1
username2:password2:email2:email_password2:auth_token2
...
```

#### **Proxies (proxy.txt)**
```
host1:port1:username1:password1
host2:port2:username2:password2
...
```

### 4. Configure PostgreSQL
Update database credentials in `proxy_twitter_miner.py`:
```python
conn = psycopg2.connect(
    host="localhost",
    database="bittensor_mining",
    user="postgres",
    password="your_password_here"  # Change this
)
```

## 🚀 Usage

### **Continuous Mining (Production)**
```bash
# Mine 1667 tweets/hour (40K tweets/day)
python proxy_twitter_miner.py --continuous 1667

# Conservative mining (24K tweets/day)
python proxy_twitter_miner.py --continuous 1000

# High-volume mining (72K tweets/day)
python proxy_twitter_miner.py --continuous 3000
```

### **Test Mining**
```bash
# Test for 5 minutes
python proxy_twitter_miner.py --test 5

# Scrape specific number of tweets
python proxy_twitter_miner.py --scrape 100
```

### **System Monitoring**
```bash
# Show statistics
python proxy_twitter_miner.py --stats

# Show storage information
python proxy_twitter_miner.py --storage-info

# Test proxy health
python proxy_twitter_miner.py --test-proxies
```

## 📊 Data Storage

### **Bittensor Format (PostgreSQL)**

#### **Table Schema**
```sql
CREATE TABLE DataEntity (
    uri TEXT PRIMARY KEY,
    datetime TIMESTAMPTZ NOT NULL,
    timeBucketId INTEGER NOT NULL,
    source INTEGER NOT NULL,           -- 2 for Twitter/X
    label VARCHAR(32),                 -- Hashtag without #
    content BYTEA NOT NULL,            -- JSON tweet data
    contentSizeBytes INTEGER NOT NULL
);
```

#### **Indexes**
```sql
CREATE INDEX data_entity_bucket_index2
ON DataEntity (timeBucketId, source, label, contentSizeBytes);
```

#### **Data Format**
- **Source**: `2` (DataSource.X for Twitter/X)
- **TimeBucketId**: Hours since epoch (`timestamp // 3600`)
- **Label**: Hashtag without # prefix, lowercase
- **Content**: JSON bytes with complete tweet data
- **URI**: Twitter status URL as unique identifier

### **Content Structure**
```json
{
  "id": "1928930860486570137",
  "url": "https://x.com/user/status/1928930860486570137",
  "text": "Just bought more bitcoin! 🚀 #bitcoin #crypto",
  "author_username": "crypto_user",
  "author_display_name": "Crypto Enthusiast",
  "created_at": "2025-06-01T03:15:29+05:30",
  "like_count": 42,
  "retweet_count": 15,
  "reply_count": 3,
  "quote_count": 1,
  "hashtags": ["#bitcoin", "#crypto"],
  "media_urls": [],
  "is_retweet": false,
  "is_reply": false,
  "conversation_id": "1928930860486570137",
  "scraped_at": "2025-06-01T03:15:30+05:30"
}
```

## 🔍 Data Verification

### **PostgreSQL Queries**

#### **Basic Statistics**
```sql
-- Total tweets stored
SELECT COUNT(*) FROM DataEntity WHERE source = 2;

-- Storage size
SELECT 
    COUNT(*) as total_tweets,
    SUM(contentSizeBytes) as total_bytes,
    COUNT(DISTINCT timeBucketId) as time_buckets,
    COUNT(DISTINCT label) as unique_labels
FROM DataEntity WHERE source = 2;
```

#### **Recent Data**
```sql
-- Latest tweets
SELECT 
    datetime,
    label,
    convert_from(content, 'UTF8')::json->>'text' as tweet_text
FROM DataEntity 
WHERE source = 2 
ORDER BY datetime DESC 
LIMIT 10;
```

#### **Top Hashtags**
```sql
-- Most popular labels
SELECT 
    label, 
    COUNT(*) as count 
FROM DataEntity 
WHERE source = 2 AND label IS NOT NULL 
GROUP BY label 
ORDER BY count DESC 
LIMIT 20;
```

#### **Hourly Distribution**
```sql
-- Tweets per hour
SELECT 
    DATE_TRUNC('hour', datetime) as hour,
    COUNT(*) as tweets
FROM DataEntity 
WHERE source = 2 
GROUP BY DATE_TRUNC('hour', datetime)
ORDER BY hour DESC
LIMIT 24;
```

### **Bittensor Compliance Check**
```sql
-- Verify schema compliance
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'dataentity'
ORDER BY ordinal_position;

-- Verify data source
SELECT DISTINCT source FROM DataEntity;

-- Verify time bucket calculation
SELECT 
    datetime,
    timebucketid,
    EXTRACT(EPOCH FROM datetime)::bigint / 3600 as calculated_bucket
FROM DataEntity 
WHERE source = 2 
LIMIT 5;
```

## 📈 Performance Monitoring

### **Real-time Dashboard**
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "🐘 Bittensor Mining Dashboard - $(date)"
    echo "=================================="
    
    psql -h localhost -U postgres -d bittensor_mining -c "
    SELECT 
        'Total Tweets' as metric,
        COUNT(*)::text as value
    FROM DataEntity WHERE source = 2
    UNION ALL
    SELECT 
        'Last Hour',
        COUNT(*)::text
    FROM DataEntity 
    WHERE source = 2 AND datetime > NOW() - INTERVAL '1 hour'
    UNION ALL
    SELECT 
        'Storage (MB)',
        ROUND(SUM(contentSizeBytes)/1024.0/1024.0, 2)::text
    FROM DataEntity WHERE source = 2;
    "
    
    sleep 30
done
EOF

chmod +x monitor.sh
./monitor.sh
```

### **System Health Metrics**
- **Working Proxies**: Active proxy count
- **Working Accounts**: Available Twitter accounts
- **Success Rate**: Request success percentage
- **Auto Recoveries**: Automatic ban recoveries
- **Storage Growth**: Real-time data accumulation

## 🎯 Target Hashtags

The system targets crypto and blockchain related content:

### **Primary Targets**
- `#bitcoin`, `#btc`, `#cryptocurrency`, `#crypto`
- `#ethereum`, `#solana`, `#cardano`, `#polkadot`
- `#defi`, `#web3`, `#blockchain`
- `#bittensor`, `#tao`, `#ai`, `#artificialintelligence`

### **Extended Targets**
- `#bitcoinmining`, `#bitcoinnews`, `#bitcoinprice`
- `#bitcointrading`, `#bitcointechnology`, `#bitcoincharts`
- `#decentralizedfinance`, `#smartcontracts`

## 🔧 Configuration

### **Mining Parameters**
```python
# Batch configuration
batch_size = tweets_per_hour // 12  # 12 batches per hour
batch_delay = 300  # 5 minutes between batches

# Proxy settings
max_concurrent = 5  # Concurrent requests
proxy_timeout = 8   # Proxy test timeout

# Account settings
account_cooldown = 5  # Minutes between account usage
success_threshold = 0.3  # Minimum success rate
```

### **Database Configuration**
```python
# PostgreSQL settings
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "bittensor_mining"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# Connection pool
MAX_CONNECTIONS = 20
CONNECTION_TIMEOUT = 30
```

## 🚨 Troubleshooting

### **Common Issues**

#### **PostgreSQL Connection Failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check connection
psql -h localhost -U postgres -d bittensor_mining
```

#### **Proxy Issues**
```bash
# Test proxies
python proxy_twitter_miner.py --test-proxies

# Check proxy file format
head -5 proxy.txt
```

#### **Account Bans**
```bash
# Check account status
python proxy_twitter_miner.py --stats

# Reset banned accounts (edit accounts manually)
```

#### **Storage Issues**
```bash
# Check database size
du -h /var/lib/postgresql/

# Check table status
psql -h localhost -U postgres -d bittensor_mining -c "\dt+"
```

### **Performance Optimization**

#### **Database Optimization**
```sql
-- Analyze table statistics
ANALYZE DataEntity;

-- Reindex for performance
REINDEX TABLE DataEntity;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename = 'dataentity';
```

#### **System Optimization**
```bash
# Increase file descriptors
ulimit -n 65536

# Monitor system resources
htop
iotop
```

## 📊 Production Metrics

### **Expected Performance**
- **1,667 tweets/hour**: 40,008 tweets/day
- **Storage growth**: ~50MB per 10K tweets
- **Success rate**: 85-95% with good proxies
- **Uptime**: 99%+ with proper monitoring

### **Scaling Guidelines**
- **Small scale**: 1,000 tweets/hour (24K/day)
- **Medium scale**: 2,000 tweets/hour (48K/day)
- **Large scale**: 3,000+ tweets/hour (72K+/day)

## 🔐 Security

### **Best Practices**
- Use dedicated server for mining
- Rotate proxy credentials regularly
- Monitor for unusual activity
- Keep Twitter accounts diverse
- Use VPN for additional protection

### **Data Protection**
- PostgreSQL with proper authentication
- Regular database backups
- Encrypted connections (SSL)
- Access logging and monitoring

## 📝 License

This project is for educational and research purposes. Ensure compliance with Twitter's Terms of Service and applicable laws.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 Support

For issues and questions:
- Check troubleshooting section
- Review PostgreSQL logs
- Monitor system resources
- Verify proxy and account health

---

**🎉 Happy Mining! Your Bittensor-compliant Twitter mining system is ready for production use.**
