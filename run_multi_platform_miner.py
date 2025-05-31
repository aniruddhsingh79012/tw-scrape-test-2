#!/usr/bin/env python3
"""
Quick setup and run script for Multi-Platform Bittensor Miner
Handles Reddit (60%), Twitter (40%), and YouTube scraping
"""

import os
import sys
import subprocess
import asyncio
import logging

def install_dependencies():
    """Install required packages for multi-platform scraping"""
    packages = [
        # Core packages
        "asyncio",
        "aiohttp", 
        "psycopg2-binary",
        "requests",
        "python-dotenv",
        
        # Reddit scraping
        "asyncpraw",
        
        # YouTube scraping  
        "google-api-python-client",
        "youtube-transcript-api",
        "isodate",
        
        # Additional utilities
        "schedule"
    ]
    
    print("🔧 Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def check_environment():
    """Check if environment variables are set"""
    print("\n🔍 Checking environment configuration...")
    
    # Check Reddit credentials (60% weight - CRITICAL)
    print("\nReddit (60% weight - CRITICAL):")
    reddit_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
    reddit_missing = []
    
    for var in reddit_vars:
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - MISSING")
            reddit_missing.append(var)
    
    # Check Twitter credentials (40% weight) - Use account files, not bearer token
    print("\nTwitter (40% weight):")
    if os.path.exists("twitteracc.txt"):
        with open("twitteracc.txt", 'r') as f:
            accounts = len([line for line in f if line.strip()])
        print(f"  ✅ Twitter accounts file ({accounts} accounts)")
        twitter_ok = accounts > 0
    else:
        print(f"  ❌ twitteracc.txt - MISSING")
        twitter_ok = False
    
    # Check YouTube credentials (Variable weight)
    print("\nYouTube (Variable weight):")
    youtube_ok = True
    if os.getenv("YOUTUBE_API_KEY"):
        print(f"  ✅ YOUTUBE_API_KEY")
    else:
        print(f"  ❌ YOUTUBE_API_KEY - MISSING (YouTube scraping will be skipped)")
        youtube_ok = False
    
    # Summary
    if reddit_missing:
        print(f"\n⚠️  Reddit setup incomplete - Missing: {reddit_missing}")
        print("📝 Reddit is 60% of subnet weight - CRITICAL to configure!")
        return False
    
    if not twitter_ok:
        print(f"\n⚠️  Twitter setup incomplete - Missing twitteracc.txt")
        print("📝 Twitter is 40% of subnet weight - Important to configure!")
        return False
    
    if not youtube_ok:
        print(f"\n⚠️  YouTube setup incomplete - Will skip YouTube scraping")
    
    print("\n✅ Core platforms configured! Ready to mine.")
    return True

def check_files():
    """Check if required files exist"""
    print("\n📁 Checking required files...")
    
    required_files = [
        "twitteracc.txt",
        "proxy.txt", 
        "data-universe-main/"
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            if os.path.isdir(file):
                print(f"✅ {file} (directory)")
            else:
                with open(file, 'r') as f:
                    lines = len(f.readlines())
                print(f"✅ {file} ({lines} entries)")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {missing_files}")
        return False
    
    print("\n✅ All required files present!")
    return True

def main():
    """Main setup and run function"""
    print("🚀 Multi-Platform Bittensor Miner Setup")
    print("=" * 50)
    print("Targets: Reddit (600K/day), Twitter (400K/day), YouTube (50K/day)")
    print("Total: 1,050,000+ daily scrapes for maximum subnet rewards!")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return False
    
    # Check files
    if not check_files():
        print("❌ File check failed")
        return False
    
    print("\n✅ Setup completed successfully!")
    
    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Run test (10 minutes) - Test all platforms")
    print("2. Start continuous mining - 1M+ daily scrapes")
    print("3. Exit")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🧪 Starting 10-minute test across all platforms...")
        print("This will test Reddit, Twitter, and YouTube scraping")
        
        # Run test
        os.system("python multi_platform_miner.py test 10")
        
    elif choice == "2":
        print("\n⛏️  Starting continuous multi-platform mining...")
        print("Target: 1,050,000+ daily scrapes")
        print("Reddit: 600K/day (60% weight)")
        print("Twitter: 400K/day (40% weight)")  
        print("YouTube: 50K/day (variable weight)")
        print("\nUse Ctrl+C to stop gracefully")
        
        # Run continuous
        os.system("python multi_platform_miner.py")
        
    elif choice == "3":
        print("👋 Goodbye!")
        
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
