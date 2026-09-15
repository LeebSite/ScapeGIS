# GIS Dataset Management Feature

## 📁 File Structure

```
app/dashboard/admin/gis-datasets/
├── page.tsx                    # Dataset list page
├── upload/
│   └── page.tsx               # Upload form page
└── [id]/
    └── page.tsx               # Dataset detail & map preview page

components/gis/
├── index.ts                   # Component exports
├── upload-form.tsx            # File upload component
├── dataset-list.tsx          # Datasets table with search
├── dataset-detail.tsx         # Dataset metadata display
└── map-preview.tsx            # Leaflet map with GeoJSON

lib/
├── api/
│   └── GISService.ts         # API service for GIS endpoints
├── hooks/
│   └── useGISDatasets.ts     # React Query hooks
└── types/
    └── gis.ts                # TypeScript types
```

## 🚀 Features Implemented

### 1. Upload GIS Files
- **Page:** `/dashboard/admin/gis-datasets/upload`
- Upload ZIP files containing GIS data (GeoJSON, Shapefile, KML, GeoPackage)
- Form validation with Zod schema
- Upload progress indicator
- File size validation (max 50MB)
- Automatic redirect to dataset detail after upload

### 2. Dataset List
- **Page:** `/dashboard/admin/gis-datasets`
- Table view with all datasets
- Search/filter functionality
- Status badges (completed, processing, failed, pending)
- File type badges with icons
- Feature count and layer count
- Delete confirmation dialog
- Empty state when no datasets exist

### 3. Map Preview
- **Page:** `/dashboard/admin/gis-datasets/[id]`
- Interactive Leaflet map with OpenStreetMap tiles
- Auto-zoom to fit layer bounds
- Feature popups showing properties
- Hover effects for better UX
- Different styles for Point, LineString, and Polygon geometries
- Support for multiple layers with tabs
- Dynamic loading (SSR-safe)

### 4. Dataset Management
- View dataset metadata (file type, status, features, layers, CRS, etc.)
- Delete datasets with confirmation
- View processing errors
- Show layer information

## 🔌 API Integration

All components are integrated with the backend API at `/api/v1/gis/`:

- `POST /gis/upload` - Upload ZIP file
- `GET /gis/datasets` - Get all datasets
- `GET /gis/datasets/{id}` - Get dataset detail
- `DELETE /gis/datasets/{id}` - Delete dataset
- `GET /gis/layers/{layer_id}/geojson` - Get GeoJSON for map

Authentication is handled automatically via the `apiClient` with Bearer tokens.

## 📦 Dependencies Installed

- `leaflet@^1.9.4` - Map library
- `react-leaflet@^4.2.1` - React bindings for Leaflet
- `@types/leaflet` - TypeScript definitions
- `@radix-ui/react-alert-dialog` - Alert dialog component
- `@radix-ui/react-tabs` - Tabs component

## 🎨 UI Components Used

- shadcn/ui components (Button, Card, Input, Textarea, Badge, etc.)
- Custom GIS components
- Leaflet for maps
- Lucide React icons

## 🔐 Access Control

All GIS pages are protected by the `/dashboard/admin` layout which enforces admin-only access via `ProtectedRoute`.

## 🗺️ Map Features

- **Base Layer:** OpenStreetMap
- **GeoJSON Rendering:** Dynamic styles based on geometry type
  - Points: Red circle markers
  - Lines: Blue polylines
  - Polygons: Blue polygons with fill
- **Interactions:**
  - Click features to view properties in popup
  - Hover for highlight effect
  - Auto-zoom to fit all features
- **Marker Icons:** Fixed for Leaflet SSR compatibility

## 📝 Type Safety

All components are fully typed with TypeScript:
- `GISDataset` - Dataset structure
- `GISLayer` - Layer structure
- `GeoJSONFeatureCollection` - GeoJSON format
- `FileType`, `DatasetStatus`, `GeometryType` - Enums

## 🎯 Usage

### For Admin Users:

1. **Navigate to GIS Datasets:**
   - Click "GIS Datasets" in the sidebar
   - Or visit `/dashboard/admin/gis-datasets`

2. **Upload Dataset:**
   - Click "Upload Dataset" button
   - Select a ZIP file containing GIS data
   - Fill in name and optional description
   - Click "Upload Dataset"

3. **View Dataset:**
   - Click "View" icon on any dataset in the list
   - See metadata and map preview
   - Click features on map to see properties

4. **Delete Dataset:**
   - Click "Delete" icon on dataset list or detail page
   - Confirm deletion in dialog

## 🐛 Known Issues & Solutions

### Issue: Leaflet map not rendering
**Solution:** Map is loaded dynamically with `dynamic()` to avoid SSR issues.

### Issue: Marker icons missing
**Solution:** CDN URLs configured for marker icons in `map-preview.tsx`.

### Issue: TypeScript errors with GeoJSON types
**Solution:** Using `as any` type assertion for compatibility between our types and Leaflet's expected types.

## 🔄 Future Enhancements

- [ ] Drag & drop file upload
- [ ] Layer styling customization
- [ ] Export GeoJSON functionality
- [ ] Batch upload
- [ ] Dataset sharing
- [ ] Layer visibility toggles
- [ ] Advanced map controls (measure, draw, etc.)

## 📚 Related Documentation

- Leaflet: https://leafletjs.com/
- React Leaflet: https://react-leaflet.js.org/
- Backend API: See `FRONTEND_IMPLEMENTATION_PROMPT.md`
