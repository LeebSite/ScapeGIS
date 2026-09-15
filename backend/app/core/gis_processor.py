"""
GIS Processing Utilities
Handles ZIP extraction, file parsing, CRS transformation, and feature extraction
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import geopandas as gpd
from shapely.geometry import mapping
import json
from loguru import logger


class GISProcessor:
    """Process GIS files from ZIP uploads"""
    
    SUPPORTED_EXTENSIONS = {
        '.geojson': 'geojson',
        '.json': 'geojson',
        '.shp': 'shapefile',
        '.kml': 'kml',
        '.gpkg': 'geopackage'
    }
    
    def __init__(self, storage_path: str = "./storage/gis"):
        """
        Initialize GIS processor
        
        Args:
            storage_path: Base path for storing uploaded files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def extract_zip(self, zip_path: str) -> str:
        """
        Extract ZIP file to temporary directory
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            Path to extracted directory
        """
        temp_dir = tempfile.mkdtemp(prefix="gis_extract_")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            logger.info(f"Extracted ZIP to: {temp_dir}")
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError(f"Failed to extract ZIP: {str(e)}")
    
    def find_gis_files(self, directory: str) -> Dict[str, List[str]]:
        """
        Find all GIS files in directory
        
        Args:
            directory: Directory to search
            
        Returns:
            Dictionary mapping file types to file paths
        """
        gis_files = {
            'geojson': [],
            'shapefile': [],
            'kml': [],
            'geopackage': [],
            'qmd': []
        }
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                ext = Path(file).suffix.lower()
                
                if ext in ['.geojson', '.json']:
                    gis_files['geojson'].append(file_path)
                elif ext == '.shp':
                    gis_files['shapefile'].append(file_path)
                elif ext == '.kml':
                    gis_files['kml'].append(file_path)
                elif ext == '.gpkg':
                    gis_files['geopackage'].append(file_path)
                elif ext == '.qmd':
                    gis_files['qmd'].append(file_path)
        
        return gis_files
    
    def load_gis_file(self, file_path: str, file_type: str) -> gpd.GeoDataFrame:
        """
        Load GIS file into GeoDataFrame
        
        Args:
            file_path: Path to GIS file
            file_type: Type of file (geojson, shapefile, kml, geopackage)
            
        Returns:
            GeoDataFrame with loaded data
        """
        try:
            if file_type == 'geojson':
                gdf = gpd.read_file(file_path, driver='GeoJSON')
            elif file_type == 'shapefile':
                gdf = gpd.read_file(file_path)
            elif file_type == 'kml':
                gdf = gpd.read_file(file_path, driver='KML')
            elif file_type == 'geopackage':
                gdf = gpd.read_file(file_path, driver='GPKG')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            logger.info(f"Loaded {len(gdf)} features from {file_path}")
            return gdf
            
        except Exception as e:
            raise ValueError(f"Failed to load GIS file: {str(e)}")
    
    def transform_to_4326(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Transform GeoDataFrame to EPSG:4326 (WGS84)
        
        Args:
            gdf: Input GeoDataFrame
            
        Returns:
            GeoDataFrame in EPSG:4326
        """
        if gdf.crs is None:
            logger.warning("No CRS defined, assuming EPSG:4326")
            gdf.set_crs(epsg=4326, inplace=True)
            return gdf
        
        original_crs = gdf.crs.to_string()
        
        if gdf.crs.to_epsg() != 4326:
            logger.info(f"Transforming from {original_crs} to EPSG:4326")
            gdf = gdf.to_crs(epsg=4326)
        
        return gdf
    
    def extract_features(self, gdf: gpd.GeoDataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract features and metadata from GeoDataFrame
        
        Args:
            gdf: GeoDataFrame to process
            
        Returns:
            Tuple of (features_list, metadata)
        """
        features = []
        
        for idx, row in gdf.iterrows():
            try:
                # Force 2D geometry (strip Z coordinate if present)
                # This fixes: "Geometry has Z dimension but column does not"
                geom = row.geometry
                if geom.has_z:
                    from shapely import force_2d
                    geom = force_2d(geom)
                
                # Get geometry as WKT for PostGIS
                geom_wkt = geom.wkt
                
                # Get properties (all columns except geometry)
                properties = {}
                for col in gdf.columns:
                    if col != 'geometry':
                        val = row[col]
                        # Convert to JSON-serializable types
                        if pd.isna(val):
                            properties[col] = None
                        elif isinstance(val, (int, float, str, bool)):
                            properties[col] = val
                        else:
                            properties[col] = str(val)
                
                features.append({
                    'geom_wkt': geom_wkt,
                    'properties': properties
                })
            except Exception as e:
                logger.warning(f"Failed to process feature {idx}: {str(e)}")
                continue
        
        # Extract metadata
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        geometry_types = gdf.geometry.geom_type.unique().tolist()
        
        metadata = {
            'total_features': len(features),
            'geometry_types': geometry_types,
            'primary_geometry_type': geometry_types[0] if geometry_types else 'Unknown',
            'bbox': bounds.tolist() if len(bounds) == 4 else None,
            'crs': 'EPSG:4326',
            'properties_schema': self._extract_properties_schema(gdf)
        }
        
        return features, metadata
    
    def _extract_properties_schema(self, gdf: gpd.GeoDataFrame) -> Dict[str, str]:
        """Extract properties schema from GeoDataFrame"""
        schema = {}
        for col in gdf.columns:
            if col != 'geometry':
                dtype = str(gdf[col].dtype)
                schema[col] = dtype
        return schema
    
    def create_geojson_preview(self, gdf: gpd.GeoDataFrame, max_features: int = 1000) -> Dict[str, Any]:
        """
        Create a GeoJSON preview (limited features for performance)
        
        Args:
            gdf: GeoDataFrame to convert
            max_features: Maximum number of features to include
            
        Returns:
            GeoJSON dict
        """
        # Limit features for preview
        if len(gdf) > max_features:
            gdf_preview = gdf.head(max_features)
            logger.info(f"Limiting preview to {max_features} features (total: {len(gdf)})")
        else:
            gdf_preview = gdf
        
        # Convert to GeoJSON
        geojson_str = gdf_preview.to_json()
        geojson_dict = json.loads(geojson_str)
        
        return geojson_dict
    
    def process_zip_upload(self, zip_path: str) -> List[Tuple[str, str, gpd.GeoDataFrame]]:
        """
        Main processing pipeline for ZIP uploads - processes ALL GIS files
        
        Args:
            zip_path: Path to uploaded ZIP file
            
        Returns:
            List of tuples: (file_type, layer_name, GeoDataFrame) for each file
        """
        extract_dir = None
        
        try:
            # Step 1: Extract ZIP
            extract_dir = self.extract_zip(zip_path)
            
            # Step 2: Find GIS files
            gis_files = self.find_gis_files(extract_dir)
            
            # Step 3: Process ALL files (prioritize GeoJSON > Shapefile > others)
            results = []
            
            # Process all GeoJSON files
            for file_path in gis_files['geojson']:
                try:
                    layer_name = Path(file_path).stem
                    gdf = self.load_gis_file(file_path, 'geojson')
                    gdf = self.transform_to_4326(gdf)
                    results.append(('geojson', layer_name, gdf))
                    logger.info(f"Processed GeoJSON: {layer_name} ({len(gdf)} features)")
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {str(e)}")
                    continue
            
            # Process all Shapefiles
            for file_path in gis_files['shapefile']:
                try:
                    layer_name = Path(file_path).stem
                    gdf = self.load_gis_file(file_path, 'shapefile')
                    gdf = self.transform_to_4326(gdf)
                    results.append(('shapefile', layer_name, gdf))
                    logger.info(f"Processed Shapefile: {layer_name} ({len(gdf)} features)")
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {str(e)}")
                    continue
            
            # Process all GeoPackages
            for file_path in gis_files['geopackage']:
                try:
                    layer_name = Path(file_path).stem
                    gdf = self.load_gis_file(file_path, 'geopackage')
                    gdf = self.transform_to_4326(gdf)
                    results.append(('geopackage', layer_name, gdf))
                    logger.info(f"Processed GeoPackage: {layer_name} ({len(gdf)} features)")
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {str(e)}")
                    continue
            
            # Process all KML files
            for file_path in gis_files['kml']:
                try:
                    layer_name = Path(file_path).stem
                    gdf = self.load_gis_file(file_path, 'kml')
                    gdf = self.transform_to_4326(gdf)
                    results.append(('kml', layer_name, gdf))
                    logger.info(f"Processed KML: {layer_name} ({len(gdf)} features)")
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {str(e)}")
                    continue
            
            if not results:
                raise ValueError("No valid GIS file could be processed from ZIP")
            
            logger.info(f"Successfully processed {len(results)} layers from ZIP")
            return results
            
        finally:
            # Cleanup temp directory
            if extract_dir and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
    
    def cleanup_temp_file(self, file_path: str):
        """Remove temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")


# Fix missing import
import pandas as pd
