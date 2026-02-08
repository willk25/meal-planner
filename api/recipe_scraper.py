#!/usr/bin/env python3
"""
Lightweight recipe scraper using only requests and beautifulsoup4.
This is much smaller than recipe-scrapers library.
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False


def scrape_recipe(url: str) -> Dict[str, Any]:
    """
    Lightweight recipe scraper that extracts basic recipe information.
    Returns a dictionary with title, ingredients, directions, etc.
    """
    if not SCRAPING_AVAILABLE:
        raise ImportError("requests and beautifulsoup4 are required for scraping")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        recipe = {}
        
        # Extract title - try multiple common patterns
        title = None
        for selector in ['h1', '[itemprop="name"]', '.recipe-title', '.entry-title', 'title']:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 3:
                    break
        
        recipe['title'] = title or 'Untitled Recipe'
        
        # Extract ingredients - try multiple common patterns
        ingredients = []
        for selector in [
            '[itemprop="recipeIngredient"]',
            '.ingredient',
            '.recipe-ingredient',
            'li[itemprop="recipeIngredient"]',
            '.ingredients li',
            '[class*="ingredient"]'
        ]:
            elements = soup.select(selector)
            if elements:
                ingredients = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
                if ingredients:
                    break
        
        recipe['ingredients'] = ingredients
        
        # Extract instructions - try multiple common patterns
        directions = []
        for selector in [
            '[itemprop="recipeInstructions"]',
            '.instruction',
            '.recipe-instruction',
            '.directions li',
            '.steps li',
            '[class*="instruction"]',
            '[class*="step"]'
        ]:
            elements = soup.select(selector)
            if elements:
                directions = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
                if directions:
                    break
        
        # If no structured instructions found, try to find paragraphs
        if not directions:
            instruction_containers = soup.select('[class*="instruction"], [class*="direction"], [class*="step"]')
            for container in instruction_containers:
                paragraphs = container.find_all(['p', 'li'])
                if paragraphs:
                    directions = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                    break
        
        recipe['directions'] = directions
        
        # Extract image
        image = None
        for selector in ['[itemprop="image"]', '.recipe-image img', 'meta[property="og:image"]']:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    image = element.get('content')
                else:
                    image = element.get('src') or element.get('data-src')
                if image:
                    # Make absolute URL if relative
                    if image.startswith('/'):
                        parsed = urlparse(url)
                        image = f"{parsed.scheme}://{parsed.netloc}{image}"
                    break
        
        if image:
            recipe['image'] = image
        
        # Extract total time if available
        time_element = soup.select_one('[itemprop="totalTime"], [itemprop="prepTime"], .total-time, .cook-time')
        if time_element:
            recipe['total_time'] = time_element.get_text(strip=True)
        
        # Extract yields/servings if available
        yield_element = soup.select_one('[itemprop="recipeYield"], .yield, .servings')
        if yield_element:
            recipe['yields'] = yield_element.get_text(strip=True)
        
        return recipe
        
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to parse recipe: {str(e)}")
