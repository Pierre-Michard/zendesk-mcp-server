from typing import Any, Dict


class KnowledgeBaseMixin:
    def get_all_articles(self) -> Dict[str, Any]:
        try:
            sections = self.client.help_center.sections()
            kb = {}
            for section in sections:
                articles = self.client.help_center.sections.articles(section.id)
                kb[section.name] = {
                    "section_id": section.id,
                    "description": section.description,
                    "articles": [
                        {
                            "id": article.id,
                            "title": article.title,
                            "body": article.body,
                            "updated_at": str(article.updated_at),
                            "url": article.html_url,
                        }
                        for article in articles
                    ],
                }
            return kb
        except Exception as e:
            raise Exception(f"Failed to fetch knowledge base: {str(e)}")