import os
from datetime import datetime
from database.repository import DatabaseManager
from model.News import News


def runDatabaseTest():
    print("Database test started...\n")


    BASE_DIR = os.path.dirname(_file_)
    db_path = os.path.join(BASE_DIR, "test_news.db")

    db = DatabaseManager(db_path)

    # Test verileri
    news1 = News(
        title="Test News 1",
        url="https://test.com/1",
        source="TestSource",
        sentiment=0.4,
        date=datetime.now()
    )

    news2 = News(
        title="Test News 2",
        url="https://test.com/2",
        source="TestSource",
        sentiment=-0.2,
        date=datetime.now()
    )

    # Insert test
    print("Inserting articles")
    result = db.dbInsertArticlesBulk([news1, news2])
    print("Insert result:", result, "\n")

    # Select test
    print("Fetching all articles...")
    df = db.dbGetAllArticles()
    print(df, "\n")

    # Statistics test
    print("Statistics:")
    stats = db.dbGetStatistics()
    print(stats, "\n")

    # Search test
    print("Search result for 'Test':")
    search_df = db.dbSearchArticles("Test")
    print(search_df, "\n")

    # Cleanup
    print("Cleaning test database")
    db.dbDeleteAllArticles()

    print("\nDatabase test finished.")


if _name_ == "_main_":
    runDatabaseTest()