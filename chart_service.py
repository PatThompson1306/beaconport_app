# chart_service.py - Service for generating charts and visualizations

import io
import time
from collections import Counter
from typing import List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from config import CHART_SIZE, MAP_SIZE, CHART_DPI, CHART_STYLE, COLORS, GEO_CONFIG


class ChartService:
    """Service class for generating charts and visualizations"""
    
    @staticmethod
    def create_chart_buffer() -> io.BytesIO:
        """Create a BytesIO buffer for chart output"""
        return io.BytesIO()
    
    @staticmethod
    def setup_chart(figsize: Tuple[int, int] = CHART_SIZE) -> Tuple[plt.Figure, plt.Axes]:
        """Set up a matplotlib figure and axis with consistent styling"""
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=figsize, dpi=CHART_DPI)
        return fig, ax
    
    @staticmethod
    def save_and_close(buf: io.BytesIO, fig: plt.Figure) -> io.BytesIO:
        """Save figure to buffer and clean up"""
        plt.tight_layout()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=CHART_DPI)
        plt.close(fig)
        buf.seek(0)
        return buf
    
    @staticmethod
    def create_no_data_chart(message: str = "No data available") -> io.BytesIO:
        """Create a simple chart indicating no data is available"""
        buf = ChartService.create_chart_buffer()
        fig, ax = ChartService.setup_chart((8, 4))
        
        ax.text(0.5, 0.5, message, ha='center', va='center', 
               fontsize=16, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return ChartService.save_and_close(buf, fig)
    
    @staticmethod
    def create_error_chart(error_msg: str) -> io.BytesIO:
        """Create a chart showing an error message"""
        return ChartService.create_no_data_chart(f"Error generating chart:\n{error_msg[:100]}...")
    
    @staticmethod
    def create_histogram(data: List[int], title: str, xlabel: str, ylabel: str) -> io.BytesIO:
        """Create a histogram chart"""
        if not data:
            return ChartService.create_no_data_chart()
        
        buf = ChartService.create_chart_buffer()
        fig, ax = ChartService.setup_chart()
        
        # Create bins for histogram
        min_val, max_val = min(data), max(data)
        bins = range(min_val, max_val + 2)
        
        counts, bin_edges, patches = ax.hist(
            data, bins=bins, 
            color=COLORS['histogram'], 
            alpha=CHART_STYLE['alpha'],
            edgecolor=CHART_STYLE['edge_color']
        )
        
        # Styling
        ax.set_title(title, fontsize=CHART_STYLE['title_size'], 
                    fontweight=CHART_STYLE['title_weight'])
        ax.set_xlabel(xlabel, fontsize=CHART_STYLE['label_size'])
        ax.set_ylabel(ylabel, fontsize=CHART_STYLE['label_size'])
        ax.tick_params(labelsize=CHART_STYLE['tick_size'])
        
        # Force integer y-axis
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Add count labels on bars
        for count, bin_left in zip(counts, bin_edges[:-1]):
            if count > 0:
                ax.text(bin_left + 0.5, count + 0.1, str(int(count)), 
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Center x-axis labels on bins
        bin_centers = [bin_left + 0.5 for bin_left in bin_edges[:-1]]
        ax.set_xticks(bin_centers)
        ax.set_xticklabels([str(int(center)) for center in bin_centers])
        
        ax.grid(True, alpha=CHART_STYLE['grid_alpha'])
        
        return ChartService.save_and_close(buf, fig)
    
    @staticmethod
    def create_bar_chart(data: List[str], title: str, xlabel: str, ylabel: str) -> io.BytesIO:
        """Create a bar chart from categorical data"""
        if not data:
            return ChartService.create_no_data_chart()
        
        buf = ChartService.create_chart_buffer()
        fig, ax = ChartService.setup_chart()
        
        # Count occurrences
        counts = Counter(data)
        categories = list(counts.keys())
        values = list(counts.values())
        
        # Create bars
        bars = ax.bar(categories, values, 
                     color=COLORS['primary'], 
                     alpha=CHART_STYLE['alpha'],
                     edgecolor=CHART_STYLE['edge_color'])
        
        # Styling
        ax.set_title(title, fontsize=CHART_STYLE['title_size'], 
                    fontweight=CHART_STYLE['title_weight'])
        ax.set_xlabel(xlabel, fontsize=CHART_STYLE['label_size'])
        ax.set_ylabel(ylabel, fontsize=CHART_STYLE['label_size'])
        ax.tick_params(labelsize=CHART_STYLE['tick_size'])
        
        # Rotate x-axis labels if needed
        if len(max(categories, key=len)) > 10:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   str(int(value)), ha='center', va='bottom', 
                   fontsize=9, fontweight='bold')
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(True, alpha=CHART_STYLE['grid_alpha'], axis='y')
        
        return ChartService.save_and_close(buf, fig)
    
    @staticmethod
    def create_scatter_plot(pairs: List[Tuple], title: str, xlabel: str, ylabel: str) -> io.BytesIO:
        """Create a scatter plot from paired data"""
        if not pairs:
            return ChartService.create_no_data_chart()
        
        buf = ChartService.create_chart_buffer()
        fig, ax = ChartService.setup_chart()
        
        x_vals = [pair[0] for pair in pairs]
        y_vals = [pair[1] for pair in pairs]
        
        # Create scatter plot
        ax.scatter(x_vals, y_vals, 
                  color=COLORS['secondary'], 
                  alpha=CHART_STYLE['alpha'],
                  s=60, edgecolor=CHART_STYLE['edge_color'])
        
        # Styling
        ax.set_title(title, fontsize=CHART_STYLE['title_size'], 
                    fontweight=CHART_STYLE['title_weight'])
        ax.set_xlabel(xlabel, fontsize=CHART_STYLE['label_size'])
        ax.set_ylabel(ylabel, fontsize=CHART_STYLE['label_size'])
        ax.tick_params(labelsize=CHART_STYLE['tick_size'])
        
        ax.grid(True, alpha=CHART_STYLE['grid_alpha'])
        
        return ChartService.save_and_close(buf, fig)
    
    @staticmethod
    def geocode_postcodes(postcodes: List[str]) -> Tuple[List[Tuple[float, float]], List[str]]:
        """Geocode postcodes to coordinates with error handling and caching."""
        import json
        import os
        cache_path = os.path.join(os.path.dirname(__file__), 'postcode_cache.json')
        # Load cache
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
        except Exception:
            cache = {}

        geolocator = Nominatim(
            user_agent=GEO_CONFIG['user_agent'],
            timeout=GEO_CONFIG['timeout']
        )

        coords = []
        failed_lookups = []
        updated = False

        for i, pc in enumerate(postcodes):
            pc_key = pc.strip().upper()
            if pc_key in cache:
                lon, lat = cache[pc_key]
                coords.append((lon, lat))
                continue
            try:
                location = geolocator.geocode(f"{pc}, UK")
                if location:
                    lon, lat = location.longitude, location.latitude
                    coords.append((lon, lat))
                    cache[pc_key] = [lon, lat]
                    updated = True
                else:
                    failed_lookups.append(pc)
                # Rate limiting
                if i < len(postcodes) - 1:
                    time.sleep(GEO_CONFIG['rate_limit_delay'])
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                failed_lookups.append(pc)
                print(f"Geocoding failed for {pc}: {e}")
                continue
            except Exception as e:
                failed_lookups.append(pc)
                print(f"Unexpected error geocoding {pc}: {e}")
                continue

        if updated:
            try:
                with open(cache_path, 'w') as f:
                    json.dump(cache, f)
            except Exception as e:
                print(f"Failed to update postcode cache: {e}")

        if failed_lookups:
            print(f"Failed to geocode {len(failed_lookups)}/{len(postcodes)} postcodes")

        return coords, failed_lookups
    
    @staticmethod
    def create_postcode_map(postcodes: List[str]) -> io.BytesIO:
        """Create a map visualization of postcodes"""
        if not postcodes:
            return ChartService.create_no_data_chart("No postcode data available")
        
        coords, failed_lookups = ChartService.geocode_postcodes(postcodes)
        
        buf = ChartService.create_chart_buffer()
        
        if not coords:
            return ChartService.create_no_data_chart("No coordinates could be obtained from postcodes")
        
        # Create map
        fig = plt.figure(figsize=MAP_SIZE, dpi=CHART_DPI)
        ax = plt.axes(projection=ccrs.Mercator())
        
        # Set extent to UK
        ax.set_extent(GEO_CONFIG['uk_bounds'], crs=ccrs.PlateCarree())
        
        # Add map features
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
        ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)
        
        # Plot points
        lons, lats = zip(*coords) if coords else ([], [])
        ax.scatter(lons, lats, 
                  color=COLORS['map_points'], 
                  s=50, alpha=0.8, 
                  transform=ccrs.PlateCarree(), 
                  zorder=5, edgecolor='darkred')
        
        # Add title with stats
        success_rate = len(coords) / len(postcodes) * 100 if postcodes else 0
        ax.set_title(f"Victim Home Postcodes at Time of Offence\n"
                    f"({len(coords)}/{len(postcodes)} postcodes mapped, {success_rate:.1f}%)",
                    fontsize=CHART_STYLE['title_size'], 
                    fontweight=CHART_STYLE['title_weight'])
        
        plt.tight_layout()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=CHART_DPI)
        plt.close(fig)
        buf.seek(0)
        
        return buf