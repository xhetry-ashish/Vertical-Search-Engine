import unittest

from search_engine.crawler.parsers import parse_publication_page, parse_publication_summaries
from search_engine.models import Author, Publication


BASE_URL = (
    "https://pureportal.coventry.ac.uk/en/organisations/"
    "centre-for-healthcare-and-community-transformation/"
)


class ParserTests(unittest.TestCase):
    def test_parse_publication_summary(self):
        html = """
        <html>
          <body>
            <ul>
              <li>
                <h3>
                  <a href="/en/publications/example-health-paper">
                    Example Health Paper
                  </a>
                </h3>
                <p>
                  <a href="/en/persons/jane-smith">Jane Smith</a>,
                  <a href="/en/persons/alan-jones">Alan Jones</a>,
                  May 2026
                </p>
                <p>Research output: Contribution to journal - Article</p>
              </li>
            </ul>
          </body>
        </html>
        """

        publications = parse_publication_summaries(html, BASE_URL)

        self.assertEqual(len(publications), 1)
        self.assertEqual(publications[0].title, "Example Health Paper")
        self.assertEqual(publications[0].publication_year, 2026)
        self.assertEqual([author.name for author in publications[0].authors], ["Jane Smith", "Alan Jones"])

    def test_parse_publication_detail_page(self):
        html = """
        <html>
          <head>
            <meta name="citation_title" content="A Study of Community Health">
            <meta name="citation_author" content="Jane Smith">
            <meta name="citation_publication_date" content="2025/06/12">
            <meta name="citation_journal_title" content="Health Science Reports">
          </head>
          <body>
            <h1>A Study of Community Health</h1>
            <p><a href="/en/persons/jane-smith">Jane Smith</a></p>
            <p>Research output: Contribution to journal - Article - peer-review</p>
            <h2>Abstract</h2>
            <p>This paper discusses healthcare transformation.</p>
            <h2>Fingerprint</h2>
          </body>
        </html>
        """

        publication = parse_publication_page(
            html,
            "https://pureportal.coventry.ac.uk/en/publications/a-study-of-community-health",
        )

        self.assertEqual(publication.title, "A Study of Community Health")
        self.assertEqual(publication.publication_year, 2025)
        self.assertEqual(publication.source, "Health Science Reports")
        self.assertEqual(publication.abstract, "This paper discusses healthcare transformation.")
        self.assertEqual(publication.authors[0].name, "Jane Smith")


class ModelTests(unittest.TestCase):
    def test_publication_to_mongo_contains_searchable_text_and_author_keys(self):
        publication = Publication(
            title="Example Health Paper",
            publication_url="https://pureportal.coventry.ac.uk/en/publications/example-health-paper",
            authors=[Author(name="Jane Smith", profile_url="https://pureportal.coventry.ac.uk/en/persons/jane-smith")],
            publication_year=2026,
            source="Health Science Reports",
        )

        document = publication.to_mongo()

        self.assertIn("publication_key", document)
        self.assertIn("author_keys", document)
        self.assertIn("Example Health Paper", document["searchable_text"])
        self.assertIn("Jane Smith", document["searchable_text"])


if __name__ == "__main__":
    unittest.main()
