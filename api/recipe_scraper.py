#!/usr/bin/env python3
"""
Lightweight recipe scraper using requests + beautifulsoup4, with optional
recipe-scrapers integration for higher-quality site-specific parsing.
"""

import re
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

try:
    from recipe_scrapers import scrape_html
    RECIPE_SCRAPERS_AVAILABLE = True
except ImportError:
    RECIPE_SCRAPERS_AVAILABLE = False


RECIPE_SCRAPERS_HOSTS = {
    'cooking.nytimes.com',
    'allrecipes.com',
    'seriouseats.com',
    'bonappetit.com',
}


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, dict):
        text = value.get('text') or value.get('name')
        return _coerce_list(text)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        # Split on common separators
        if '\n' in raw:
            return [line.strip() for line in raw.split('\n') if line.strip()]
        if '•' in raw:
            return [line.strip() for line in raw.split('•') if line.strip()]
        if ';' in raw:
            return [line.strip() for line in raw.split(';') if line.strip()]
        return [raw]
    return []


def _find_recipe_in_json_ld(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    def iter_candidates(obj):
        if isinstance(obj, list):
            for item in obj:
                yield from iter_candidates(item)
        elif isinstance(obj, dict):
            if '@graph' in obj:
                yield from iter_candidates(obj['@graph'])
            obj_type = obj.get('@type') or obj.get('type')
            if isinstance(obj_type, list):
                if any(t == 'Recipe' for t in obj_type):
                    yield obj
            elif isinstance(obj_type, str) and obj_type == 'Recipe':
                yield obj
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    yield from iter_candidates(value)

    scripts = soup.select('script[type="application/ld+json"]')
    for script in scripts:
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Some sites embed multiple JSON objects; try to salvage first/last block.
            continue
        for candidate in iter_candidates(data):
            return candidate
    return None


def _extract_from_json_ld(data: Dict[str, Any]) -> Dict[str, Any]:
    recipe: Dict[str, Any] = {}
    recipe['title'] = data.get('name') or data.get('headline') or data.get('title')

    ingredients = data.get('recipeIngredient') or data.get('ingredients')
    recipe['ingredients'] = _coerce_list(ingredients)

    instructions = data.get('recipeInstructions') or data.get('instructions')
    if isinstance(instructions, list):
        steps = []
        for step in instructions:
            if isinstance(step, str):
                steps.append(step.strip())
            elif isinstance(step, dict):
                text = step.get('text') or step.get('name')
                if text:
                    steps.append(text.strip())
                elif 'itemListElement' in step:
                    steps.extend(_coerce_list(step.get('itemListElement')))
        recipe['directions'] = [s for s in steps if s]
    else:
        recipe['directions'] = _coerce_list(instructions)

    image = data.get('image')
    if isinstance(image, list) and image:
        image = image[0]
    if isinstance(image, dict):
        image = image.get('url')
    if isinstance(image, str):
        recipe['image'] = image

    total_time = data.get('totalTime') or data.get('cookTime') or data.get('prepTime')
    if total_time:
        recipe['total_time'] = total_time

    yields = data.get('recipeYield') or data.get('yield')
    if yields:
        recipe['yields'] = yields

    return recipe


def _try_recipe_scrapers(html: str, url: str) -> Optional[Dict[str, Any]]:
    if not RECIPE_SCRAPERS_AVAILABLE:
        return None
    
    host = urlparse(url).netloc.lower()
    if host.startswith('www.'):
        host = host[4:]
    
    if host not in RECIPE_SCRAPERS_HOSTS:
        return None
    
    try:
        scraper = scrape_html(html, url)
        recipe: Dict[str, Any] = {}
        
        try:
            title = scraper.title()
            if title:
                recipe['title'] = title
        except Exception:
            pass
        
        try:
            ingredients = scraper.ingredients()
            if ingredients:
                recipe['ingredients'] = ingredients
        except Exception:
            pass
        
        try:
            instructions = scraper.instructions()
            if instructions:
                recipe['directions'] = [step.strip() for step in instructions.split('\n') if step.strip()]
        except Exception:
            pass
        
        try:
            image = scraper.image()
            if image:
                recipe['image'] = image
        except Exception:
            pass
        
        try:
            yields = scraper.yields()
            if yields:
                recipe['yields'] = yields
        except Exception:
            pass
        
        try:
            total_time = scraper.total_time()
            if total_time:
                recipe['total_time'] = total_time
        except Exception:
            pass
        
        return recipe if recipe else None
    except Exception:
        return None


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
        
        html = response.text
        soup = BeautifulSoup(response.content, 'html.parser')
        
        recipe: Dict[str, Any] = _try_recipe_scrapers(html, url) or {}
        
        # Extract title - try multiple common patterns
        if not recipe.get('title'):
            title = None
            for selector in ['h1', '[itemprop="name"]', '.recipe-title', '.entry-title', 'title']:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    if title and len(title) > 3:
                        break
            
            recipe['title'] = title or 'Untitled Recipe'

        # Prefer JSON-LD Recipe schema when available
        json_ld_recipe = _find_recipe_in_json_ld(soup)
        if json_ld_recipe:
            json_ld_data = _extract_from_json_ld(json_ld_recipe)
            for key, value in json_ld_data.items():
                if value and not recipe.get(key):
                    recipe[key] = value
            if recipe.get('image') and recipe['image'].startswith('/'):
                parsed = urlparse(url)
                recipe['image'] = f"{parsed.scheme}://{parsed.netloc}{recipe['image']}"
            # If JSON-LD produced reasonable ingredients/directions, return early.
            if recipe.get('ingredients') and recipe.get('directions'):
                return recipe
        
        # Extract ingredients - try multiple common patterns
        if not recipe.get('ingredients'):
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
        if not recipe.get('directions'):
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
