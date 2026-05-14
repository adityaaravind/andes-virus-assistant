"""Hope Garden - News Sentiment Analysis for Plant Growth."""
from __future__ import annotations

from typing import Dict, List
import re
import logging
from datetime import datetime


class NewsSentimentAnalyzer:
    """Analyzes news content sentiment to drive Hope Garden growth."""

    def __init__(self):
        # Sentiment keyword patterns
        self.hopeful_patterns = [
            r'\b(?:recover|recovery|healing|cure|treatment|vaccine|improve|better|decline|stable|progress|hope|positive)\b',
            r'\b(?:survivors|success|breakthrough|effective|safe|contained|under control)\b',
            r'\b(?:reduce|reduced|improving|stabilizing|good news|promising|optimistic)\b'
        ]

        self.concerning_patterns = [
            r'\b(?:outbreak|spreading|surge|spike|emergency|crisis|death|deaths|died|fatal)\b',
            r'\b(?:worsen|worse|critical|severe|alarm|panic|fear|concern|rising|increasing)\b',
            r'\b(?:quarantine|lockdown|restrict|evacuate|threat|risk|danger|warning)\b'
        ]

        self.neutral_patterns = [
            r'\b(?:monitor|monitoring|investigate|investigation|report|update|conference|meeting)\b',
            r'\b(?:research|study|analysis|data|statistics|numbers|confirmed)\b'
        ]

    def analyze_news_chunk(self, text: str) -> Dict[str, any]:
        """Analyze a single news chunk for sentiment.

        Returns:
            {
                'sentiment_score': float (-1 to +1),
                'sentiment_type': str (HOPEFUL|NEUTRAL|CONCERNING),
                'keywords_found': list,
                'confidence': float
            }
        """
        if not text:
            return {'sentiment_score': 0, 'sentiment_type': 'NEUTRAL', 'keywords_found': [], 'confidence': 0.0}

        text_lower = text.lower()

        # Count pattern matches
        hopeful_count = sum(len(re.findall(pattern, text_lower)) for pattern in self.hopeful_patterns)
        concerning_count = sum(len(re.findall(pattern, text_lower)) for pattern in self.concerning_patterns)
        neutral_count = sum(len(re.findall(pattern, text_lower)) for pattern in self.neutral_patterns)

        # Extract keywords found
        keywords_found = []
        for pattern in self.hopeful_patterns:
            keywords_found.extend(re.findall(pattern, text_lower))
        for pattern in self.concerning_patterns:
            keywords_found.extend(re.findall(pattern, text_lower))

        # Calculate sentiment score with improved logic
        total_sentiment_words = hopeful_count + concerning_count
        if total_sentiment_words == 0:
            sentiment_score = 0
            sentiment_type = 'NEUTRAL'
            confidence = 0.1
        else:
            # Give more weight to hopeful words to balance against frequent concerning context
            weighted_hopeful = hopeful_count * 1.2  # Boost hopeful words
            net_sentiment = weighted_hopeful - concerning_count
            max_possible = max(weighted_hopeful, concerning_count)

            if max_possible > 0:
                sentiment_score = net_sentiment / max_possible
            else:
                sentiment_score = 0

            # Confidence based on total sentiment words and balance
            confidence = min(total_sentiment_words / 8.0, 1.0)

            # Classify type with adjusted thresholds
            if sentiment_score > 0.2:
                sentiment_type = 'HOPEFUL'
            elif sentiment_score < -0.3:
                sentiment_type = 'CONCERNING'
            else:
                sentiment_type = 'NEUTRAL'

        return {
            'sentiment_score': round(sentiment_score, 2),
            'sentiment_type': sentiment_type,
            'keywords_found': list(set(keywords_found))[:10],  # Limit to 10 unique keywords
            'confidence': round(confidence, 2),
            'hopeful_count': hopeful_count,
            'concerning_count': concerning_count,
            'neutral_count': neutral_count
        }

    def analyze_news_batch(self, chunks: List[Dict[str, any]]) -> Dict[str, any]:
        """Analyze a batch of news chunks and return overall sentiment.

        Args:
            chunks: List of news chunks with 'text' field

        Returns:
            {
                'overall_sentiment': float,
                'sentiment_type': str,
                'total_chunks': int,
                'hopeful_chunks': int,
                'concerning_chunks': int,
                'neutral_chunks': int,
                'confidence': float,
                'timestamp': str
            }
        """
        if not chunks:
            return {
                'overall_sentiment': 0,
                'sentiment_type': 'NEUTRAL',
                'total_chunks': 0,
                'hopeful_chunks': 0,
                'concerning_chunks': 0,
                'neutral_chunks': 0,
                'confidence': 0.0,
                'timestamp': datetime.utcnow().isoformat()
            }

        # Analyze each chunk
        chunk_results = []
        for chunk in chunks:
            text = chunk.get('text', '') or chunk.get('content', '')
            result = self.analyze_news_chunk(text)
            chunk_results.append(result)

        # Calculate overall metrics
        total_chunks = len(chunk_results)
        hopeful_chunks = sum(1 for r in chunk_results if r['sentiment_type'] == 'HOPEFUL')
        concerning_chunks = sum(1 for r in chunk_results if r['sentiment_type'] == 'CONCERNING')
        neutral_chunks = sum(1 for r in chunk_results if r['sentiment_type'] == 'NEUTRAL')

        # Overall sentiment (weighted average)
        total_sentiment = sum(r['sentiment_score'] for r in chunk_results)
        overall_sentiment = total_sentiment / total_chunks if total_chunks > 0 else 0

        # Overall confidence (average of individual confidences)
        overall_confidence = sum(r['confidence'] for r in chunk_results) / total_chunks if total_chunks > 0 else 0

        # Overall type
        if overall_sentiment > 0.1:
            overall_type = 'HOPEFUL'
        elif overall_sentiment < -0.1:
            overall_type = 'CONCERNING'
        else:
            overall_type = 'NEUTRAL'

        logging.info(f"News sentiment analysis: {overall_type} (score: {overall_sentiment:.2f}) from {total_chunks} chunks")

        return {
            'overall_sentiment': round(overall_sentiment, 2),
            'sentiment_type': overall_type,
            'total_chunks': total_chunks,
            'hopeful_chunks': hopeful_chunks,
            'concerning_chunks': concerning_chunks,
            'neutral_chunks': neutral_chunks,
            'confidence': round(overall_confidence, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'chunk_details': chunk_results[:5]  # Store first 5 for debugging
        }


# Singleton instance for use across the app
sentiment_analyzer = NewsSentimentAnalyzer()