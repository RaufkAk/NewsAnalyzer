
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class News:
    title: str
    url: str
    source: str
    sentiment: float
    date: datetime = field(default_factory=datetime.now)
    sentiment_type: str | None = None

    def sentimentCategorizer(self) -> None:

        if self.sentiment > 0.1:
            self.sentiment_type = "Positive"
        elif self.sentiment < -0.1:
            self.sentiment_type = "Negative"
        else:
            self.sentiment_type = "Neutral"

    def dictConverter(self) -> dict:

        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "sentiment": self.sentiment,
            "date": self.date,
            "sentimentType": self.sentiment_type
        }

    def __str__(self) -> str:
        return (
            f"News(title='{self.title[:30]}...', "
            f"source='{self.source}', "
            f"sentiment={self.sentiment:.2f})"
        )