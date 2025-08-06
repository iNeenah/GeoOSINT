"""
Visual Search UI Components for Google Lens-like interface
Provides Streamlit components for displaying search results in a visual format
"""

import streamlit as st
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import requests
from io import BytesIO

from visual_search_core import (
    VisualSearchResults, SimilarImage, GeographicReference, 
    WebSource, Landmark, SearchEngineType
)


class VisualSearchUI:
    """Main UI class for displaying visual search results"""
    
    def __init__(self):
        self.results_per_page = 20
        self.thumbnail_size = (150, 150)
        
    def display_search_results(self, results: VisualSearchResults):
        """Display complete visual search results in Google Lens style"""
        if not results or results.total_results == 0:
            self._display_no_results()
            return
        
        # Display search summary
        self._display_search_summary(results)
        
        # Create tabs for different result types
        tabs = st.tabs([
            f"Similar Images ({len(results.similar_images)})",
            f"Locations ({len(results.geographic_references)})",
            f"Web Sources ({len(results.web_sources)})",
            f"Landmarks ({len(results.landmarks)})"
        ])
        
        with tabs[0]:
            self._display_similar_images_grid(results.similar_images)
        
        with tabs[1]:
            self._display_geographic_references(results.geographic_references)
        
        with tabs[2]:
            self._display_web_sources(results.web_sources)
        
        with tabs[3]:
            self._display_landmarks(results.landmarks)
    
    def _display_search_summary(self, results: VisualSearchResults):
        """Display search summary statistics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Results", 
                results.total_results,
                help="Total number of similar images found"
            )
        
        with col2:
            unique_domains = len(results.get_unique_domains())
            st.metric(
                "Unique Sources", 
                unique_domains,
                help="Number of different websites where image was found"
            )
        
        with col3:
            search_time = results.metadata.total_search_time if results.metadata else 0
            st.metric(
                "Search Time", 
                f"{search_time:.1f}s",
                help="Time taken to complete the search"
            )
        
        with col4:
            success_rate = 0
            if results.metadata:
                total = results.metadata.total_engines_used
                successful = results.metadata.successful_engines
                success_rate = (successful / total * 100) if total > 0 else 0
            
            st.metric(
                "Success Rate", 
                f"{success_rate:.0f}%",
                help="Percentage of search engines that returned results"
            )
        
        # Display search metadata if available
        if results.metadata and results.metadata.errors:
            with st.expander("Search Details", expanded=False):
                st.write(f"**Search ID:** {results.metadata.search_id}")
                st.write(f"**Engines Used:** {', '.join([e.value for e in results.metadata.engines_used])}")
                
                if results.metadata.errors:
                    st.write("**Errors:**")
                    for error in results.metadata.errors:
                        st.write(f"- {error}")
    
    def _display_similar_images_grid(self, images: List[SimilarImage]):
        """Display similar images in a grid layout like Google Lens"""
        if not images:
            st.info("No similar images found")
            return
        
        # Add search controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_filter = st.selectbox(
                "Filter by source:",
                ["All Sources"] + [engine.value.replace('_', ' ').title() for engine in SearchEngineType],
                key="image_filter"
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort by:",
                ["Similarity", "Domain", "Title"],
                key="image_sort"
            )
        
        with col3:
            show_details = st.checkbox("Show Details", value=False, key="show_image_details")
        
        # Filter images
        filtered_images = self._filter_images(images, search_filter)
        
        # Sort images
        sorted_images = self._sort_images(filtered_images, sort_by)
        
        # Display images in grid
        self._render_images_grid(sorted_images, show_details)
    
    def _filter_images(self, images: List[SimilarImage], filter_type: str) -> List[SimilarImage]:
        """Filter images by source type"""
        if filter_type == "All Sources":
            return images
        
        # Convert filter type back to enum
        filter_engine = None
        for engine in SearchEngineType:
            if engine.value.replace('_', ' ').title() == filter_type:
                filter_engine = engine
                break
        
        if filter_engine:
            return [img for img in images if img.engine_source == filter_engine]
        
        return images
    
    def _sort_images(self, images: List[SimilarImage], sort_by: str) -> List[SimilarImage]:
        """Sort images by specified criteria"""
        if sort_by == "Similarity":
            return sorted(images, key=lambda x: x.similarity_score, reverse=True)
        elif sort_by == "Domain":
            return sorted(images, key=lambda x: x.domain.lower())
        elif sort_by == "Title":
            return sorted(images, key=lambda x: x.title.lower())
        
        return images
    
    def _render_images_grid(self, images: List[SimilarImage], show_details: bool):
        """Render images in a responsive grid layout"""
        # Calculate number of columns based on screen size
        cols_per_row = 4
        
        # Pagination
        total_pages = (len(images) - 1) // self.results_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox(
                f"Page (showing {len(images)} results):",
                range(1, total_pages + 1),
                key="image_page"
            ) - 1
        else:
            page = 0
        
        start_idx = page * self.results_per_page
        end_idx = min(start_idx + self.results_per_page, len(images))
        page_images = images[start_idx:end_idx]
        
        # Render grid
        for i in range(0, len(page_images), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(page_images):
                    image = page_images[i + j]
                    with col:
                        self._render_image_card(image, show_details)
    
    def _render_image_card(self, image: SimilarImage, show_details: bool):
        """Render individual image card"""
        try:
            # Create card container
            with st.container():
                # Display thumbnail
                if image.thumbnail_url:
                    try:
                        # Try to display image
                        st.image(
                            image.thumbnail_url,
                            caption=image.title[:50] + "..." if len(image.title) > 50 else image.title,
                            use_column_width=True
                        )
                    except Exception:
                        # Fallback to placeholder
                        st.write("🖼️ Image")
                        st.caption(image.title[:50] + "..." if len(image.title) > 50 else image.title)
                else:
                    st.write("🖼️ Image")
                    st.caption(image.title[:50] + "..." if len(image.title) > 50 else image.title)
                
                # Display basic info
                if image.domain:
                    st.caption(f"📍 {image.domain}")
                
                if image.similarity_score > 0:
                    similarity_color = "green" if image.similarity_score > 0.8 else "orange" if image.similarity_score > 0.5 else "red"
                    st.caption(f":{similarity_color}[Match: {image.similarity_score:.1%}]")
                
                # Source link
                if image.source_url:
                    st.link_button(
                        "View Source",
                        image.source_url,
                        use_container_width=True
                    )
                
                # Show details if requested
                if show_details:
                    with st.expander("Details", expanded=False):
                        if image.description:
                            st.write(f"**Description:** {image.description[:200]}...")
                        
                        if image.dimensions:
                            st.write(f"**Size:** {image.dimensions[0]}×{image.dimensions[1]}")
                        
                        if image.publication_date:
                            st.write(f"**Published:** {image.publication_date.strftime('%Y-%m-%d')}")
                        
                        st.write(f"**Engine:** {image.engine_source.value.replace('_', ' ').title()}")
                        
                        if image.image_url != image.source_url:
                            st.write(f"**Image URL:** {image.image_url[:50]}...")
        
        except Exception as e:
            st.error(f"Error displaying image: {str(e)}")
    
    def _display_geographic_references(self, references: List[GeographicReference]):
        """Display geographic references found in search results"""
        if not references:
            st.info("No geographic references found")
            return
        
        st.write(f"Found {len(references)} geographic references:")
        
        # Group references by type
        by_type = {}
        for ref in references:
            type_name = ref.location_type.value.replace('_', ' ').title()
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(ref)
        
        # Display by type
        for type_name, type_refs in by_type.items():
            with st.expander(f"{type_name} ({len(type_refs)})", expanded=True):
                for ref in sorted(type_refs, key=lambda x: x.confidence_score, reverse=True):
                    self._render_geographic_reference(ref)
    
    def _render_geographic_reference(self, ref: GeographicReference):
        """Render individual geographic reference"""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{ref.location_name}**")
            if ref.context:
                st.caption(ref.context[:100] + "..." if len(ref.context) > 100 else ref.context)
        
        with col2:
            confidence_color = "green" if ref.confidence_score > 0.7 else "orange" if ref.confidence_score > 0.4 else "red"
            st.write(f":{confidence_color}[{ref.confidence_score:.1%}]")
        
        with col3:
            if ref.source_url:
                st.link_button("Source", ref.source_url, use_container_width=True)
        
        # Show coordinates if available
        if ref.coordinates:
            st.caption(f"📍 {ref.coordinates.latitude:.6f}, {ref.coordinates.longitude:.6f}")
        
        st.divider()
    
    def _display_web_sources(self, sources: List[WebSource]):
        """Display web sources where the image was found"""
        if not sources:
            st.info("No web sources found")
            return
        
        st.write(f"Found on {len(sources)} websites:")
        
        # Sort by confidence score
        sorted_sources = sorted(sources, key=lambda x: x.confidence_score, reverse=True)
        
        for source in sorted_sources:
            self._render_web_source(source)
    
    def _render_web_source(self, source: WebSource):
        """Render individual web source"""
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Title and description
                st.write(f"**{source.title}**")
                if source.description:
                    st.write(source.description[:200] + "..." if len(source.description) > 200 else source.description)
                
                # Domain and metadata
                domain_info = source.domain
                if source.language:
                    domain_info += f" • {source.language.upper()}"
                if source.publication_date:
                    domain_info += f" • {source.publication_date.strftime('%Y-%m-%d')}"
                
                st.caption(domain_info)
                
                # Geographic mentions
                if source.geographic_mentions:
                    st.caption(f"🌍 Mentions: {', '.join(source.geographic_mentions[:3])}")
            
            with col2:
                # Confidence score
                if source.confidence_score > 0:
                    confidence_color = "green" if source.confidence_score > 0.8 else "orange" if source.confidence_score > 0.5 else "red"
                    st.write(f":{confidence_color}[{source.confidence_score:.1%}]")
                
                # Visit button
                st.link_button("Visit", source.url, use_container_width=True)
            
            st.divider()
    
    def _display_landmarks(self, landmarks: List[Landmark]):
        """Display identified landmarks"""
        if not landmarks:
            st.info("No landmarks identified")
            return
        
        st.write(f"Identified {len(landmarks)} potential landmarks:")
        
        # Sort by confidence score
        sorted_landmarks = sorted(landmarks, key=lambda x: x.confidence_score, reverse=True)
        
        for landmark in sorted_landmarks:
            self._render_landmark(landmark)
    
    def _render_landmark(self, landmark: Landmark):
        """Render individual landmark"""
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{landmark.name}**")
                
                if landmark.description:
                    st.write(landmark.description[:150] + "..." if len(landmark.description) > 150 else landmark.description)
                
                if landmark.category:
                    st.caption(f"Category: {landmark.category.title()}")
                
                if landmark.location:
                    st.caption(f"📍 {landmark.location.latitude:.6f}, {landmark.location.longitude:.6f}")
            
            with col2:
                # Confidence score
                confidence_color = "green" if landmark.confidence_score > 0.7 else "orange" if landmark.confidence_score > 0.4 else "red"
                st.write(f":{confidence_color}[{landmark.confidence_score:.1%}]")
                
                # Links
                if landmark.source_url:
                    st.link_button("Source", landmark.source_url, use_container_width=True)
                
                if landmark.wikipedia_url:
                    st.link_button("Wikipedia", landmark.wikipedia_url, use_container_width=True)
            
            st.divider()
    
    def _display_no_results(self):
        """Display message when no results are found"""
        st.info("🔍 No similar images found")
        st.write("""
        **Possible reasons:**
        - The image is unique or very rare
        - The image is not indexed by search engines
        - The image quality is too low for matching
        - Search engines are temporarily unavailable
        
        **Try:**
        - Using a different image
        - Cropping to focus on specific elements
        - Using higher quality images
        """)
    
    def display_search_progress(self, status_text: str, progress: float = None):
        """Display search progress indicator"""
        if progress is not None:
            st.progress(progress, text=status_text)
        else:
            with st.spinner(status_text):
                pass
    
    def create_export_section(self, results: VisualSearchResults):
        """Create export options for search results"""
        if not results or results.total_results == 0:
            return
        
        st.subheader("Export Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export as JSON", use_container_width=True):
                json_data = self._export_to_json(results)
                st.download_button(
                    "Download JSON",
                    json_data,
                    file_name=f"visual_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Export as CSV", use_container_width=True):
                csv_data = self._export_to_csv(results)
                st.download_button(
                    "Download CSV",
                    csv_data,
                    file_name=f"visual_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("Export Report", use_container_width=True):
                report_data = self._export_to_report(results)
                st.download_button(
                    "Download Report",
                    report_data,
                    file_name=f"visual_search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    def _export_to_json(self, results: VisualSearchResults) -> str:
        """Export results to JSON format"""
        import json
        from dataclasses import asdict
        
        # Convert dataclasses to dictionaries
        export_data = {
            'search_metadata': {
                'query_image_hash': results.query_image_hash,
                'search_timestamp': results.search_timestamp.isoformat(),
                'total_results': results.total_results
            },
            'similar_images': [
                {
                    'image_url': img.image_url,
                    'source_url': img.source_url,
                    'title': img.title,
                    'description': img.description,
                    'similarity_score': img.similarity_score,
                    'domain': img.domain,
                    'engine_source': img.engine_source.value
                }
                for img in results.similar_images
            ],
            'geographic_references': [
                {
                    'location_name': ref.location_name,
                    'location_type': ref.location_type.value,
                    'confidence_score': ref.confidence_score,
                    'source_url': ref.source_url,
                    'coordinates': {
                        'latitude': ref.coordinates.latitude,
                        'longitude': ref.coordinates.longitude
                    } if ref.coordinates else None
                }
                for ref in results.geographic_references
            ],
            'web_sources': [
                {
                    'url': source.url,
                    'title': source.title,
                    'description': source.description,
                    'domain': source.domain,
                    'confidence_score': source.confidence_score
                }
                for source in results.web_sources
            ]
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_to_csv(self, results: VisualSearchResults) -> str:
        """Export results to CSV format"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write similar images
        writer.writerow(['Type', 'Title', 'URL', 'Domain', 'Similarity', 'Engine'])
        
        for img in results.similar_images:
            writer.writerow([
                'Similar Image',
                img.title,
                img.source_url,
                img.domain,
                f"{img.similarity_score:.2%}",
                img.engine_source.value
            ])
        
        # Write geographic references
        for ref in results.geographic_references:
            writer.writerow([
                'Geographic Reference',
                ref.location_name,
                ref.source_url,
                '',
                f"{ref.confidence_score:.2%}",
                ref.location_type.value
            ])
        
        return output.getvalue()
    
    def _export_to_report(self, results: VisualSearchResults) -> str:
        """Export results to text report format"""
        report = []
        report.append("VISUAL SEARCH RESULTS REPORT")
        report.append("=" * 50)
        report.append(f"Search Date: {results.search_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Image Hash: {results.query_image_hash}")
        report.append(f"Total Results: {results.total_results}")
        report.append("")
        
        # Similar Images
        if results.similar_images:
            report.append("SIMILAR IMAGES FOUND:")
            report.append("-" * 30)
            for i, img in enumerate(results.similar_images[:20], 1):
                report.append(f"{i}. {img.title}")
                report.append(f"   Source: {img.source_url}")
                report.append(f"   Domain: {img.domain}")
                report.append(f"   Similarity: {img.similarity_score:.1%}")
                report.append("")
        
        # Geographic References
        if results.geographic_references:
            report.append("GEOGRAPHIC REFERENCES:")
            report.append("-" * 30)
            for ref in results.geographic_references:
                report.append(f"• {ref.location_name} ({ref.location_type.value})")
                report.append(f"  Confidence: {ref.confidence_score:.1%}")
                if ref.coordinates:
                    report.append(f"  Coordinates: {ref.coordinates.latitude:.6f}, {ref.coordinates.longitude:.6f}")
                report.append("")
        
        # Web Sources
        if results.web_sources:
            report.append("WEB SOURCES:")
            report.append("-" * 30)
            for source in results.web_sources:
                report.append(f"• {source.title}")
                report.append(f"  URL: {source.url}")
                report.append(f"  Domain: {source.domain}")
                report.append("")
        
        return "\n".join(report)


# Utility functions for UI components
def create_image_thumbnail_html(image_url: str, title: str, max_width: int = 150) -> str:
    """Create HTML for image thumbnail with fallback"""
    return f"""
    <div style="text-align: center; margin: 10px;">
        <img src="{image_url}" 
             alt="{title}" 
             style="max-width: {max_width}px; max-height: {max_width}px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
        <div style="display: none; width: {max_width}px; height: {max_width}px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
            <span style="color: #666;">🖼️</span>
        </div>
        <p style="margin-top: 5px; font-size: 12px; color: #666;">{title[:30]}...</p>
    </div>
    """


def format_similarity_score(score: float) -> str:
    """Format similarity score with color coding"""
    if score > 0.8:
        return f"🟢 {score:.1%}"
    elif score > 0.5:
        return f"🟡 {score:.1%}"
    else:
        return f"🔴 {score:.1%}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."