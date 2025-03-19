import json
import openai
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

class TerminalInfoExtractor:

    def __init__(self, openai_client, harbor_name):
        self.client = openai_client
        self.harbor_name = harbor_name
    
    def extract_terminal_info(self, content: str, url: str) -> List[Dict[str, str]]:
        """
        Extract terminal information from content for a specific harbor.
        
        Args:
            content: Text or HTML content from the website
            url: Source URL for reference
            
        Returns:
            List of dictionaries containing terminal information
        """
        # Check if content appears to be HTML
        is_html = '<html' in content.lower() or '<body' in content.lower() or '<div' in content.lower()
        
        # Extract text content if it's HTML
        if is_html:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                # Remove unnecessary elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                    element.decompose()
                text_content = ' '.join(soup.stripped_strings)
            except Exception as e:
                print(f"Error parsing HTML: {e}")
                text_content = content
        else:
            # Already text content
            text_content = content
        
        # Check content length and chunk if necessary
        max_token_length = 4000  # Maximum tokens for GPT-4o-mini
        # Approximate token count (1 token ≈ 4 chars in English)
        approx_tokens = len(text_content) / 4
        
        if approx_tokens > max_token_length:
            print(f"Content too large ({int(approx_tokens)} estimated tokens), chunking...")
            return self._process_large_content(text_content, url, max_token_length)
        
        # Process content normally if small enough
        # Prepare prompt for the LLM
        prompt = self._create_extraction_prompt(text_content)
        
        # Get response from Azure OpenAI
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract terminal information from text and return in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # Use low temperature for consistent, factual responses
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure the result is in the expected format
            terminals = []
            if isinstance(result, dict) and "terminals" in result:
                terminals = result["terminals"]
            elif isinstance(result, list):
                terminals = result
            
            # Add source URL to each terminal
            for terminal in terminals:
                terminal["source_url"] = url
                
            return terminals
                
        except Exception as e:
            print(f"Error extracting terminal information: {e}")
            return []
    
    def _process_large_content(self, text_content: str, url: str, max_tokens: int) -> List[Dict[str, str]]:
        """Process large content by chunking it and extracting from each chunk"""
        # Approximate chars per token
        chars_per_token = 4
        max_chars = max_tokens * chars_per_token * 0.8  # 80% to be safe
        
        # Split content into chunks
        chunks = []
        words = text_content.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for the space
            if current_length + word_length > max_chars:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        print(f"Split content into {len(chunks)} chunks")
        
        # Process each chunk
        all_terminals = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            prompt = self._create_extraction_prompt(chunk)
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Extract terminal information from this text chunk and return in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
                # Extract terminals
                chunk_terminals = []
                if isinstance(result, dict) and "terminals" in result:
                    chunk_terminals = result["terminals"]
                elif isinstance(result, list):
                    chunk_terminals = result
                
                # Add source URL to each terminal
                for terminal in chunk_terminals:
                    terminal["source_url"] = url
                    # Add chunk info for debugging
                    terminal["chunk_index"] = i
                
                all_terminals.extend(chunk_terminals)
                
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
        
        # Deduplicate terminals by name
        deduplicated = {}
        for terminal in all_terminals:
            name = terminal.get("terminal_name", "").lower()
            if name and name not in deduplicated:
                deduplicated[name] = terminal
            elif name in deduplicated:
                # Merge any additional information
                existing = deduplicated[name]
                for key, value in terminal.items():
                    if key not in existing or not existing[key]:
                        existing[key] = value
        
        return list(deduplicated.values())
    
    def _create_extraction_prompt(self, text_content: str) -> str:
        """
        Create a prompt for the LLM to extract terminal information.
        
        Args:
            text_content: Text content from the website
            
        Returns:
            Prompt string for the LLM
        """
        return f"""
        Extract terminal information from the text for {self.harbor_name} harbour.
        For each terminal, extract:
        1. terminal_name: The name of the terminal
        2. category: The category/type (Container, Bulk, Cruise, etc.)
        3. url: Any URL associated with the terminal
        
        If information is not available, use empty strings.
        
        Return in JSON format:
        {{
            "terminals": [
                {{
                    "terminal_name": "Terminal Name",
                    "category": "Category",
                    "url": "URL"
                }}
            ]
        }}
        
        Text:
        {text_content}
        """
    
    def save_to_json(self, terminals: List[Dict[str, str]], output_path: str = "terminal_data.json") -> bool:
        """
        Save the extracted terminal information to a JSON file.
        
        Args:
            terminals: List of dictionaries containing terminal information
            output_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(terminals, f, ensure_ascii=False, indent=2)
            print(f"Terminal information saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving terminal information to file: {e}")
            return False