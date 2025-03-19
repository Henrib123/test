from InternetSearchgEngine import InternetSearchEngine
from WebsiteProcessor import WebsiteProcessor
from terminal_info_extractor import TerminalInfoExtractor
from util import openai_client


class TerminalRetrievalAgent:

    def __init__(self, harbor_name):
        self.harbor_name = harbor_name
        self.search_engine = InternetSearchEngine(self.harbor_name)
        self.openai_client = openai_client
        
    def start(self):
        best_sources = self.search_engine.get_first_sources()

        for source in best_sources:

            source_information = WebsiteProcessor(self.harbor_name, source)


            # Updated to match the required parameters
            terminal_info_extractor = TerminalInfoExtractor(self.openai_client, self.harbor_name)
            
            # Get HTML content from the scraped data
            scraped_data = source_information.scrape_website(source)
            html_content = scraped_data.get('html', '') if scraped_data else ""
            
            # Pass the required arguments
            terminals = terminal_info_extractor.extract_terminal_info(html_content, source)

            print(terminals)
            