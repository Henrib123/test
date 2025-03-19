import requests
from bs4 import BeautifulSoup


class WebsiteProcessor:

    def __init__(self, harbor_name, url):
        self.harbor_name = harbor_name
        self.main_url = url
        self.interesting_text_snippets = []
        self.interesting_sub_urls = []

        scraped_website = self.scrape_website(url)
        if scraped_website:
            self.interesting_text_snippets.append(scraped_website['content'])

    def scrape_website(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script, style, and other non-content elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe', 'noscript']):
                element.decompose()

            # Get all links
            all_links = soup.find_all('a')

            # Separate regular links and file links
            regular_links = []
            file_links = []

            for link in all_links:
                href = link.get('href')
                if href:
                    # Check if the link points to a file (pdf, doc, xlsx, etc)
                    if href.lower().endswith(('.pdf', '.doc', '.docx', '.xlsx', '.xls', '.csv')):
                        file_links.append(href)
                    else:
                        regular_links.append(href)

            # Extract text content
            text_content = ' '.join(soup.stripped_strings)
            # Clean up excessive whitespace
            text_content = ' '.join(text_content.split())

            # Try to find the main content
            main_content = None
            for tag in ['main', 'article', 'div[role="main"]', '.main-content', '#content', '#main']:
                main_content = soup.select_one(tag)
                if main_content:
                    break
            
            # If we found main content section, prioritize its text
            if main_content:
                main_text = ' '.join(main_content.stripped_strings)
                main_text = ' '.join(main_text.split())
                
                # Use the extracted text instead of full HTML to reduce token size
                extracted_html = str(main_content)
            else:
                # If no main content found, use a smaller subset of the page
                # Identify and extract only sections that likely contain terminal information
                content_sections = []
                # Look for sections with keywords related to terminals
                terminal_keywords = ['terminal', 'port', 'dock', 'berth', 'quay', 'cargo', 'container', 'shipping']
                
                for keyword in terminal_keywords:
                    # Look for headers or paragraphs containing these keywords
                    elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p'], 
                                           string=lambda text: keyword.lower() in text.lower() if text else False)
                    for element in elements:
                        # Get the parent section or div
                        parent = element.find_parent(['section', 'div', 'article'])
                        if parent and parent not in content_sections:
                            content_sections.append(parent)
                
                # If we found relevant sections
                if content_sections:
                    extracted_html = ''.join(str(section) for section in content_sections)
                    main_text = ' '.join(' '.join(section.stripped_strings) for section in content_sections)
                    main_text = ' '.join(main_text.split())
                else:
                    # Fallback to using a limited portion of the HTML
                    extracted_html = str(soup)
                    main_text = text_content

            return {
                'regular_links': regular_links,
                'file_links': file_links,
                'html': extracted_html,  # Using targeted content instead of full HTML
                'content': main_text     # Using more focused text content
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None