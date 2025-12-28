import pandas as pd
from analyzer.sentiment import NewsAnalyzer

def run_tests():
    analyzer = NewsAnalyzer()

    print("=" * 50)
    print("NEWS ANALYZER TESTS")
    print("=" * 50)

    # --- Sentiment testi ---
    texts = [
        "Great economic growth announced today",
        "Terrible disaster strikes the region",
        "Officials held a meeting"
    ]

    print("\n[1] Sentiment Scores")
    for text in texts:
        result = analyzer.analyze_sentiment(text)
        print(f"- {text}")
        print(f"  score={result['score']} label={result['label']}")

    # --- DataFrame testi ---
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'title': texts,
        'sentiment': [0.7, -0.6, 0.0],
        'source': ['BBC', 'CNN', 'BBC']
    })

    print("\n[2] Batch Sentiment Labeling")
    df = analyzer.analyze_batch(df)
    print(df[['title', 'sentiment_label']])

    # --- Keyword testi ---
    print("\n[3] Keyword Extraction")
    keywords = analyzer.get_trending_topics(df, top_n=5)
    for word, count in keywords:
        print(f"{word}: {count}")

    # --- Kaynak bazlı analiz ---
    print("\n[4] Sentiment by Source")
    print(analyzer.sentiment_by_source(df))

    # --- Dağılım testi ---
    print("\n[5] Sentiment Distribution")
    print(analyzer.get_sentiment_distribution(df))

    # --- Filtreleme testi ---
    print("\n[6] Positive News Filter")
    print(analyzer.filter_by_sentiment(df, 'Positive')[['title', 'sentiment']])

    # --- En pozitif / negatif ---
    print("\n[7] Top Positive News")
    print(analyzer.get_top_positive_news(df, n=1)[['title', 'sentiment']])

    print("\n[8] Top Negative News")
    print(analyzer.get_top_negative_news(df, n=1)[['title', 'sentiment']])

    print("\n✅ All tests executed successfully.")


if __name__ == "__main__":
    run_tests()