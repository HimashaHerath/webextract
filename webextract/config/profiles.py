"""Pre-defined configuration profiles for common use cases."""

from .settings import ConfigBuilder


class ConfigProfiles:
    """Pre-defined configuration profiles for common use cases."""
    
    @staticmethod
    def news_scraping():
        """Optimized for news articles and blog posts."""
        return (ConfigBuilder()
                .with_model("gemma3:27b")
                .with_content_limit(8000)
                .with_custom_prompt("""
                Extract news information:
                - Headline and summary
                - Key people, organizations, locations
                - Important dates and events
                - Source attribution
                """)
                .build())
    
    @staticmethod
    def research_papers():
        """Optimized for academic papers and research."""
        return (ConfigBuilder()
                .with_model("gemma3:27b")
                .with_content_limit(15000)
                .with_custom_prompt("""
                Extract academic information:
                - Title, authors, abstract
                - Key findings and conclusions
                - Methodology
                - References and citations
                - Technical terms and definitions
                """)
                .with_timeout(90)
                .build())
    
    @staticmethod
    def ecommerce():
        """Optimized for product pages and reviews."""
        return (ConfigBuilder()
                .with_model("gemma3:8b")
                .with_content_limit(5000)
                .with_custom_prompt("""
                Extract product information:
                - Product name, price, description
                - Key features and specifications
                - Customer reviews and ratings
                - Availability and shipping
                """)
                .build())
    
    @staticmethod
    def documentation():
        """Optimized for technical documentation."""
        return (ConfigBuilder()
                .with_model("codellama:13b")
                .with_content_limit(10000)
                .with_custom_prompt("""
                Extract technical documentation:
                - API endpoints and parameters
                - Code examples and snippets
                - Installation and setup instructions
                - Configuration options
                - Troubleshooting information
                """)
                .build())
    
    @staticmethod
    def fast_extraction():
        """Fast extraction with smaller model."""
        return (ConfigBuilder()
                .with_model("gemma3:2b")
                .with_content_limit(2000)
                .with_timeout(15)
                .build())
    
    @staticmethod
    def accurate_extraction():
        """High accuracy extraction with larger model."""
        return (ConfigBuilder()
                .with_model("gemma3:27b")
                .with_content_limit(8000)
                .with_timeout(60)
                .build()) 