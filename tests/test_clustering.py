import unittest

from search_engine.clustering.dataset import build_sample_dataset
from search_engine.clustering.text_clustering import fit_clustering_model, predict_cluster


class ClusteringTests(unittest.TestCase):
    def test_sample_dataset_has_required_size_and_categories(self):
        documents = build_sample_dataset()
        categories = {document["category"] for document in documents}

        self.assertGreaterEqual(len(documents), 100)
        self.assertEqual(categories, {"Economics", "Entertainment", "Politics"})

    def test_fit_clustering_model_returns_cluster_summaries(self):
        documents = build_sample_dataset()
        result = fit_clustering_model(documents, n_clusters=3)

        self.assertEqual(len(result.documents), len(documents))
        self.assertEqual(len(result.cluster_summaries), 3)
        self.assertEqual(len(result.labels), len(documents))
        self.assertGreater(len(result.vocabulary), 0)

    def test_predict_cluster_assigns_new_document(self):
        result = fit_clustering_model(build_sample_dataset(), n_clusters=3)
        prediction = predict_cluster(
            "The parliament debated tax policy and government spending.",
            result,
        )

        self.assertIsNotNone(prediction["cluster"])
        self.assertIn(
            prediction["majority_category"],
            {"Economics", "Entertainment", "Politics"},
        )


if __name__ == "__main__":
    unittest.main()
