import unittest

from search_engine.indexer.inverted_index import build_publication_index
from search_engine.indexer.preprocessing import preprocess_text
from search_engine.indexer.ranking import rank_document_vectors


class PreprocessingTests(unittest.TestCase):
    def test_preprocess_text_lowercases_removes_stop_words_and_stems(self):
        tokens = preprocess_text("The researchers studied digital interventions in healthcare.")

        self.assertNotIn("the", tokens)
        self.assertIn("researcher", tokens)
        self.assertIn("digital", tokens)
        self.assertIn("intervention", tokens)
        self.assertIn("healthcare", tokens)


class IndexingAndRankingTests(unittest.TestCase):
    def setUp(self):
        self.publications = [
            {
                "publication_key": "P1",
                "title": "Digital health intervention for student mental wellbeing",
                "publication_url": "https://example.test/p1",
                "publication_year": 2026,
                "authors": [{"name": "Jane Smith"}],
                "source": "Health Journal",
                "publication_type": "Article",
                "abstract": "Mental health and stress intervention study.",
                "searchable_text": "Digital health intervention for student mental wellbeing",
            },
            {
                "publication_key": "P2",
                "title": "Gross motor development in children",
                "publication_url": "https://example.test/p2",
                "publication_year": 2026,
                "authors": [{"name": "Alan Jones"}],
                "source": "Movement Journal",
                "publication_type": "Article",
                "abstract": "Motor development and children movement study.",
                "searchable_text": "Gross motor development in children",
            },
        ]

    def test_build_publication_index_creates_terms_postings_and_vectors(self):
        result = build_publication_index(self.publications)

        self.assertEqual(result.document_count, 2)
        self.assertIn("mental", result.inverted_index)
        self.assertEqual(result.inverted_index["mental"]["document_frequency"], 1)
        self.assertEqual(len(result.document_vectors), 2)
        self.assertIn("vector", result.document_vectors[0])

    def test_rank_document_vectors_returns_relevant_document_first(self):
        result = build_publication_index(self.publications)
        ranked = rank_document_vectors(
            "mental health stress",
            result.document_vectors,
            result.idf_weights,
            limit=2,
        )

        self.assertEqual(ranked[0]["publication_key"], "P1")
        self.assertGreater(ranked[0]["score"], 0)
        self.assertIn("mental", ranked[0]["matched_terms"])


if __name__ == "__main__":
    unittest.main()
