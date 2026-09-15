"""
Test script to check if GISProcessor can find multiple files
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath('.'))

from app.core.gis_processor import GISProcessor
import tempfile
import zipfile

# Create a test ZIP with multiple GeoJSON files
test_zip = tempfile.mktemp(suffix='.zip')

with zipfile.ZipFile(test_zip, 'w') as zf:
    # Add 3 dummy GeoJSON files
    for i in range(3):
        geojson_content = f'''{{
  "type": "FeatureCollection",
  "features": [
    {{
      "type": "Feature",
      "geometry": {{
        "type": "Point",
        "coordinates": [100.{i}, 0.{i}]
      }},
      "properties": {{
        "name": "Test {i}"
      }}
    }}
  ]
}}'''
        zf.writestr(f'test_layer_{i}.geojson', geojson_content)

print(f"Created test ZIP: {test_zip}")

# Test processor
processor = GISProcessor()

try:
    # Extract and find files
    extract_dir = processor.extract_zip(test_zip)
    gis_files = processor.find_gis_files(extract_dir)
    
    print(f"\nFound GIS files:")
    for file_type, files in gis_files.items():
        if files:
            print(f"  {file_type}: {len(files)} files")
            for f in files:
                print(f"    - {f}")
    
    # Test process_zip_upload
    results = processor.process_zip_upload(test_zip)
    
    print(f"\nProcessed {len(results)} layers:")
    for file_type, layer_name, gdf in results:
        print(f"  - {layer_name} ({file_type}): {len(gdf)} features")
    
    print("\n✅ Multi-layer processing works!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    os.remove(test_zip)
