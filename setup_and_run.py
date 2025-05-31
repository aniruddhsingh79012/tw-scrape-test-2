#!/usr/bin/env python3
"""
Setup and Run Script for Bittensor-Optimized Twitter Scraper
Handles installation, configuration, and execution
"""

import os
import sys
import subprocess
import json
import asyncio
import logging
from pathlib import Path

def install_requirements():
    """Install required Python packages"""
    requirements = [
        "asyncio",
        "aiohttp",
        "psycopg2-binary",
        "requests",
        "schedule",
        "python-dotenv"
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False
    
    return True

def setup_postgresql():
    """Setup PostgreSQL database"""
    print("\n=== PostgreSQL Setup ===")
    print("Please ensure PostgreSQL is installed and running.")
    print("Default configuration:")
    print("  Database: postgres")
    print("  User: postgres")
    print("  Password: postgres")
    print("  Host: localhost")
    print("  Port: 5432")
    
    # Test connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres", 
            password="postgres",
            host="localhost",
            port=5432
        )
        conn.close()
        print("✓ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("Please check your PostgreSQL installation and configuration.")
        return False

def verify_account_files():
    """Verify account and proxy files exist"""
    print("\n=== Account Files Verification ===")
    
    required_files = ["twitteracc.txt", "proxy.txt"]
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                lines = len(f.readlines())
            print(f"✓ {file} found ({lines} entries)")
        else:
            print(f"✗ {file} not found")
            missing_files.append(file)
    
    if missing_files:
        print(f"\nMissing files: {missing_files}")
        print("Please ensure these files exist in the current directory.")
        return False
    
    return True

def create_config_file():
    """Create configuration file"""
    config = {
        "postgres": {
            "dbname": "postgres",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": 5432
        },
        "scraping": {
            "target_tweets_per_day": 1000000,
            "max_concurrent_requests": 20,
            "account_cooldown_minutes": 15,
            "proxy_cooldown_minutes": 5
        },
        "storage": {
            "max_db_size_gb": 250,
            "batch_size": 1000,
            "cleanup_days": 30
        }
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✓ Created config.json")
    return True

def run_system_check():
    """Run comprehensive system check"""
    print("=== System Check ===")
    
    checks = [
        ("Python version", sys.version_info >= (3, 8)),
        ("Required files", verify_account_files()),
        ("PostgreSQL", setup_postgresql()),
        ("Configuration", create_config_file())
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

async def run_test_scrape():
    """Run a test scraping session"""
    print("\n=== Running Test Scrape ===")
    
    try:
        from bittensor_optimized_miner import BittensorOptimizedMiner
        
        postgres_config = {
            "dbname": "postgres",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": 5432
        }
        
        miner = BittensorOptimizedMiner(postgres_config)
        
        # Run 5-minute test
        test_report = await miner.run_test(5)
        
        print("Test Results:")
        print(json.dumps(test_report, indent=2))
        
        return test_report["success_rate"] > 50  # At least 50% success rate
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def main():
    """Main setup and run function"""
    print("🚀 Bittensor-Optimized Twitter Scraper Setup")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return False
    
    # Run system check
    if not run_system_check():
        print("❌ System check failed")
        return False
    
    print("\n✅ Setup completed successfully!")
    
    # Ask user what to do next
    print("\nWhat would you like to do?")
    print("1. Run test scrape (5 minutes)")
    print("2. Start continuous scraping")
    print("3. Exit")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        print("\nStarting test scrape...")
        success = asyncio.run(run_test_scrape())
        if success:
            print("✅ Test completed successfully!")
        else:
            print("❌ Test failed")
    
    elif choice == "2":
        print("\nStarting continuous scraping...")
        print("Use Ctrl+C to stop gracefully")
        
        try:
            from bittensor_optimized_miner import main as run_miner
            asyncio.run(run_miner())
        except KeyboardInterrupt:
            print("\n✅ Scraping stopped gracefully")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif choice == "3":
        print("👋 Goodbye!")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
