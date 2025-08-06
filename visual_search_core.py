"""
Core infrastructure for Google Lens-like visual search system
Provides base classes and data models for multi-engine reverse image search
"""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
import streamlit as st


class SearchEngineType(Enum):
    """Supported search engine types"""
    GOOGLE_IMAGES = "google_images"
    YANDEX_IMAGES = "yandex_images"
    TINEYE = "tineye"
    BING_VISUAL = "bing_visual"
    BAIDU_IMAGES = "baidu_images"


class LocationType(Enum):
    """Types of geographic references"""
    ADDRESS = "address"
    CITY = "city"
    COUNTRY = "country"
    LANDMARK = "landmark"
    COORDINATES = "coordinates"
    REGION = "region"
    POSTAL_CODE = "postal_code"


@dataclass
class Coordinate:
    """GPS coordinate with confidence"""
    latitude: float
    longitude: float
    confidence: float = 1.0
    source: str = ""
    
    def __post_init__(self):
        # Validate coordinates
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")


@dataclass
class GeographicReference:
    """Geographic location reference found in search results"""
    location_name: str
    location_type: LocationType
    coordinates: Optional[Coordinate] = None
    confidence_score: float = 0.0
    source_url: str = ""
    context: str = ""
    country: Optional[str] = None
    region: Optional[str] = None


@dataclass
class SimilarImage:
    """Similar image found in reverse search"""
    image_url: str
    thumbnail_url: str
    source_url: str
    title: str
    description: str = ""
    similarity_score: float = 0.0
    dimensions: Optional[Tuple[int, int]] = None
    file_size: Optional[int] = None
    publication_date: Optional[datetime] = None
    domain: str = ""
    engine_source: SearchEngineType = SearchEngineType.GOOGLE_IMAGES


@dataclass
class WebSource:
    """Web source where the image was found"""
    url: str
    title: str
    description: str
    publication_date: Optional[datetime] = None
    domain: str = ""
    language: str = ""
    geographic_mentions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0


@dataclass
class Landmark:
    """Identified landmark or point of interest"""
    name: str
    location: Optional[Coordinate] = None
    description: str = ""
    category: str = ""
    confidence_score: float = 0.0
    source_url: str = ""
    wikipedia_url: Optional[str] = None


@dataclass
class SearchMetadata:
    """Metadata about the search operation"""
    search_id: str
    query_image_hash: str
    search_timestamp: datetime
    total_engines_used: int
    successful_engines: int
    total_search_time: float
    engines_used: List[SearchEngineType] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class VisualSearchResults:
    """Complete results from visual search operation"""
    query_image_hash: str
    search_timestamp: datetime
    total_results: int
    similar_images: List[SimilarImage] = field(default_factory=list)
    geographic_references: List[GeographicReference] = field(default_factory=list)
    web_sources: List[WebSource] = field(default_factory=list)
    landmarks: List[Landmark] = field(default_factory=list)
    metadata: Optional[SearchMetadata] = None
    
    def get_top_locations(self, limit: int = 5) -> List[GeographicReference]:
        """Get top geographic references by confidence score"""
        return sorted(
            self.geographic_references, 
            key=lambda x: x.confidence_score, 
            reverse=True
        )[:limit]
    
    def get_similar_images_by_engine(self, engine: SearchEngineType) -> List[SimilarImage]:
        """Get similar images from specific search engine"""
        return [img for img in self.similar_images if img.engine_source == engine]
    
    def get_unique_domains(self) -> List[str]:
        """Get list of unique domains where image was found"""
        domains = set()
        for img in self.similar_images:
            if img.domain:
                domains.add(img.domain)
        for source in self.web_sources:
            if source.domain:
                domains.add(source.domain)
        return sorted(list(domains))


class SearchEngine(ABC):
    """Abstract base class for reverse image search engines"""
    
    def __init__(self, name: str, engine_type: SearchEngineType):
        self.name = name
        self.engine_type = engine_type
        self.session = None
        self.rate_limit_delay = 1.0  # seconds between requests
        self.timeout = 30.0  # request timeout
        self.max_retries = 3
        
    async def __aenter__(self):
        """Async context manager entry"""
        if AIOHTTP_AVAILABLE:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
        else:
            # Fallback to requests
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session and AIOHTTP_AVAILABLE:
            await self.session.close()
    
    @abstractmethod
    async def reverse_search(self, image_data: bytes) -> List[SimilarImage]:
        """
        Perform reverse image search
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            List of similar images found
        """
        pass
    
    @abstractmethod
    def get_engine_name(self) -> str:
        """Return human-readable engine name"""
        pass
    
    def get_engine_type(self) -> SearchEngineType:
        """Return engine type enum"""
        return self.engine_type
    
    async def _make_request(self, url: str, **kwargs):
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if self.session is None:
                    raise RuntimeError("Session not initialized. Use async context manager.")
                
                # Rate limiting
                if attempt > 0:
                    await asyncio.sleep(self.rate_limit_delay * (2 ** attempt))
                
                if AIOHTTP_AVAILABLE:
                    async with self.session.get(url, **kwargs) as response:
                        if response.status == 200:
                            return response
                        elif response.status == 429:  # Rate limited
                            await asyncio.sleep(self.rate_limit_delay * 2)
                            continue
                        else:
                            response.raise_for_status()
                else:
                    # Fallback to synchronous requests
                    response = self.session.get(url, **kwargs)
                    if response.status_code == 200:
                        return response
                    elif response.status_code == 429:
                        await asyncio.sleep(self.rate_limit_delay * 2)
                        continue
                    else:
                        response.raise_for_status()
                        
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise
                continue
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                continue
        
        raise Exception(f"Failed to make request after {self.max_retries} attempts")


class VisualSearchManager:
    """
    Main manager class that orchestrates visual search across multiple engines
    """
    
    def __init__(self):
        self.search_engines: List[SearchEngine] = []
        self.max_concurrent_searches = 3
        self.search_timeout = 60.0  # Total search timeout
        
    def add_search_engine(self, engine: SearchEngine):
        """Add a search engine to the manager"""
        self.search_engines.append(engine)
        
    def remove_search_engine(self, engine_type: SearchEngineType):
        """Remove search engine by type"""
        self.search_engines = [
            engine for engine in self.search_engines 
            if engine.get_engine_type() != engine_type
        ]
    
    def get_image_hash(self, image_data: bytes) -> str:
        """Generate hash for image data"""
        return hashlib.sha256(image_data).hexdigest()[:16]
    
    async def search_image(self, image_data: bytes, progress_callback=None) -> VisualSearchResults:
        """
        Perform comprehensive visual search across all engines
        
        Args:
            image_data: Raw image bytes
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete search results
        """
        search_start_time = time.time()
        search_id = f"search_{int(search_start_time)}"
        image_hash = self.get_image_hash(image_data)
        
        # Initialize results
        results = VisualSearchResults(
            query_image_hash=image_hash,
            search_timestamp=datetime.now(),
            total_results=0
        )
        
        # Initialize metadata
        metadata = SearchMetadata(
            search_id=search_id,
            query_image_hash=image_hash,
            search_timestamp=datetime.now(),
            total_engines_used=len(self.search_engines),
            successful_engines=0,
            total_search_time=0.0,
            engines_used=[engine.get_engine_type() for engine in self.search_engines]
        )
        
        if not self.search_engines:
            metadata.errors.append("No search engines configured")
            results.metadata = metadata
            return results
        
        # Create semaphore for concurrent searches
        semaphore = asyncio.Semaphore(self.max_concurrent_searches)
        
        async def search_with_engine(engine: SearchEngine) -> Tuple[SearchEngine, List[SimilarImage], Optional[str]]:
            """Search with a single engine"""
            async with semaphore:
                try:
                    if progress_callback:
                        progress_callback(f"Searching with {engine.get_engine_name()}...")
                    
                    async with engine:
                        similar_images = await engine.reverse_search(image_data)
                        return engine, similar_images, None
                        
                except Exception as e:
                    error_msg = f"{engine.get_engine_name()}: {str(e)}"
                    return engine, [], error_msg
        
        # Execute searches concurrently
        try:
            search_tasks = [search_with_engine(engine) for engine in self.search_engines]
            
            # Wait for all searches with timeout
            search_results = await asyncio.wait_for(
                asyncio.gather(*search_tasks, return_exceptions=True),
                timeout=self.search_timeout
            )
            
            # Process results
            all_similar_images = []
            
            for result in search_results:
                if isinstance(result, Exception):
                    metadata.errors.append(f"Search task failed: {str(result)}")
                    continue
                
                engine, similar_images, error = result
                
                if error:
                    metadata.errors.append(error)
                else:
                    metadata.successful_engines += 1
                    all_similar_images.extend(similar_images)
                    
                    if progress_callback:
                        progress_callback(f"Found {len(similar_images)} results from {engine.get_engine_name()}")
            
            # Deduplicate and sort results
            results.similar_images = self._deduplicate_images(all_similar_images)
            results.total_results = len(results.similar_images)
            
            # Extract additional data from results
            results.web_sources = self._extract_web_sources(results.similar_images)
            results.geographic_references = self._extract_geographic_references(results.similar_images)
            results.landmarks = self._extract_landmarks(results.similar_images)
            
        except asyncio.TimeoutError:
            metadata.errors.append(f"Search timed out after {self.search_timeout} seconds")
        except Exception as e:
            metadata.errors.append(f"Search failed: {str(e)}")
        
        # Finalize metadata
        metadata.total_search_time = time.time() - search_start_time
        results.metadata = metadata
        
        if progress_callback:
            progress_callback(f"Search completed: {results.total_results} results found")
        
        return results
    
    def _deduplicate_images(self, images: List[SimilarImage]) -> List[SimilarImage]:
        """Remove duplicate images based on URL"""
        seen_urls = set()
        unique_images = []
        
        # Sort by similarity score first
        sorted_images = sorted(images, key=lambda x: x.similarity_score, reverse=True)
        
        for image in sorted_images:
            if image.image_url not in seen_urls:
                seen_urls.add(image.image_url)
                unique_images.append(image)
        
        return unique_images
    
    def _extract_web_sources(self, images: List[SimilarImage]) -> List[WebSource]:
        """Extract unique web sources from similar images"""
        sources = {}
        
        for image in images:
            if image.source_url and image.source_url not in sources:
                sources[image.source_url] = WebSource(
                    url=image.source_url,
                    title=image.title,
                    description=image.description,
                    publication_date=image.publication_date,
                    domain=image.domain,
                    confidence_score=image.similarity_score
                )
        
        return list(sources.values())
    
    def _extract_geographic_references(self, images: List[SimilarImage]) -> List[GeographicReference]:
        """Extract geographic references from image titles and descriptions"""
        # This is a placeholder - will be implemented in geographic intelligence module
        references = []
        
        # Basic pattern matching for now
        import re
        location_patterns = [
            (r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b', LocationType.CITY),
            (r'\b[A-Z][a-z]+\s+Street\b', LocationType.ADDRESS),
            (r'\b\d+\.\d+,\s*-?\d+\.\d+\b', LocationType.COORDINATES),
        ]
        
        for image in images:
            text = f"{image.title} {image.description}"
            
            for pattern, location_type in location_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    references.append(GeographicReference(
                        location_name=match,
                        location_type=location_type,
                        confidence_score=0.5,
                        source_url=image.source_url,
                        context=text[:100]
                    ))
        
        return references
    
    def _extract_landmarks(self, images: List[SimilarImage]) -> List[Landmark]:
        """Extract landmarks from image data"""
        # This is a placeholder - will be implemented in landmark detection module
        landmarks = []
        
        # Basic keyword matching for now
        landmark_keywords = [
            'tower', 'bridge', 'cathedral', 'church', 'museum', 'monument',
            'palace', 'castle', 'temple', 'statue', 'building', 'hall'
        ]
        
        for image in images:
            text = f"{image.title} {image.description}".lower()
            
            for keyword in landmark_keywords:
                if keyword in text:
                    landmarks.append(Landmark(
                        name=image.title,
                        description=image.description,
                        category=keyword,
                        confidence_score=0.3,
                        source_url=image.source_url
                    ))
                    break  # Only add one landmark per image
        
        return landmarks
    
    def get_results_summary(self, results: VisualSearchResults) -> Dict[str, Any]:
        """Get summary statistics for search results"""
        return {
            'total_results': results.total_results,
            'similar_images': len(results.similar_images),
            'geographic_references': len(results.geographic_references),
            'web_sources': len(results.web_sources),
            'landmarks': len(results.landmarks),
            'unique_domains': len(results.get_unique_domains()),
            'search_time': results.metadata.total_search_time if results.metadata else 0,
            'successful_engines': results.metadata.successful_engines if results.metadata else 0,
            'total_engines': results.metadata.total_engines_used if results.metadata else 0,
            'errors': len(results.metadata.errors) if results.metadata else 0
        }


# Utility functions for image processing
def optimize_image_for_search(image_data: bytes, max_size: int = 1024) -> bytes:
    """
    Optimize image for reverse search by resizing and compressing
    
    Args:
        image_data: Raw image bytes
        max_size: Maximum dimension in pixels
        
    Returns:
        Optimized image bytes
    """
    try:
        from PIL import Image
        import io
        
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large
        if image.size[0] > max_size or image.size[1] > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save optimized image
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        # Return original if optimization fails
        return image_data


def create_image_thumbnail(image_data: bytes, size: Tuple[int, int] = (150, 150)) -> bytes:
    """
    Create thumbnail from image data
    
    Args:
        image_data: Raw image bytes
        size: Thumbnail size (width, height)
        
    Returns:
        Thumbnail image bytes
    """
    try:
        from PIL import Image
        import io
        
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create thumbnail
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save thumbnail
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=80)
        return output.getvalue()
        
    except Exception as e:
        # Return original if thumbnail creation fails
        return image_data