import ast

import requests
from typing import List, Dict, Any
from util import calculate_llm_answer


class InternetSearchEngine:

    def __init__(self, harbor_name):
        self.harbor_name = harbor_name

        self.google_api_key = 'AIzaSyDu_5CcrQtVjY1voUwDNukeDl3S0iwaf1U'
        self.costum_search_engine_id = '57050f029801a41f1'

        self.visited_websites = []

    def add_visited_website(self, url):
        self.visited_websites.append(url)

    def is_website_already_visited(self, url):
        return url in self.visited_websites

    def get_search_results(self, query: str, num_results: int = 8) -> List[Dict[str, str]]:
        """
        Retrieve search results including URLs and snippet descriptions.

        Args:
            query: Search query
            num_results: Number of results to retrieve

        Returns:
            List of dictionaries containing URL and snippet
        """
        url = (
            f"https://www.googleapis.com/customsearch/v1?q={query}"
            f"&key={self.google_api_key}&cx={self.costum_search_engine_id}"
        )
        response = requests.get(url)
        data = response.json()
        results = []
        for item in data.get("items", [])[:num_results]:
            results.append({
                "url": item.get("link"),
                "snippet": item.get("snippet")
            })
        return results

    def get_first_sources(self, num_results: int = 8) -> List[Dict[str, str]]:
        print(f"Searching for the best sources for harbor: {self.harbor_name}")
        query1 = f"{self.harbor_name} harbor terminals"
        query2 = f"{self.harbor_name} harbor list of all terminals"

        results1 = self.get_best_sources(query1)
        results2 = self.get_best_sources(query2)

        return results1 + results2

    def get_best_sources(self, query: str, num_results: int = 10) -> List:
        """
        Searches for the best sources for a given port by executing three queries
        and aggregating all unique URLs with their snippet descriptions.

        Args:
            port_name: Name of the port
            num_results: Number of results to retrieve per query

        Returns:
            List of dictionaries containing URL and snippet
        """

        search_results = self.get_search_results(query, num_results=num_results)

        new_sources = []
        for result in search_results:
            url = result['url']
            if url not in self.visited_websites:
                new_sources.append(result)

        filtered_search_results = self.filter_best_urls_by_snippet(query, new_sources)

        print(f"Identified relevant sources: {filtered_search_results}")

        self.visited_websites += filtered_search_results

        return filtered_search_results

    def filter_best_urls_by_snippet(self, question: str, results: List[Dict[str, str]]) -> List[str]:
        """
        Uses the LLM to select, from the given search results (with snippets),
        the URLs most likely to contain the answer to the provided question.

        Args:
            question: Question to answer
            results: List of search results

        Returns:
            List of selected URLs
        """
        system_prompt = "You help in selecting the best URLs that can answer a question based on their description."
        user_prompt = f"I have the following question: '{question}'\n\n"
        user_prompt += "Here are the search results with their descriptions:\n\n"
        for result in results:
            user_prompt += f"URL: {result['url']}\nDescription: {result['snippet']}\n\n"

        user_prompt += """Please select the URLs that are most likely to contain the answer to the question.
                        As an output, you are only allowed to answer in a python list in the following format: ['url1', ... ].
                        Make sure you answer with nothing but the python list.""""""

        response = calculate_llm_answer(system_prompt, user_prompt)

        most_fitting_urls = ast.literal_eval(response)

        return most_fitting_urls