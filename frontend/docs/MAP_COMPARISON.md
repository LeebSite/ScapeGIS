# 🗺️ Map Preview - Comparison Guide

## Current Implementation: OpenStreetMap (Free)

**File:** `components/gis/mapbox-map.tsx`

### ✅ Pros:
- 100% Gratis
- Tidak perlu token/registrasi
- Sudah berfungsi dengan baik
- Open source

### ❌ Cons:
- Style terbatas (hanya basic street map)
- Tidak ada satellite view
- Tidak ada dark mode
- Performa sedikit lebih lambat

---

## Alternative: Mapbox GL (Premium Styles)

**File:** `components/gis/mapbox-map-styled.tsx`

### ✅ Pros:
- **5 Style Options:**
  1. **Streets** - Modern & clean (recommended)
  2. **Satellite** - Aerial imagery
  3. **Dark** - Dark mode theme
  4. **Light** - Minimal design
  5. **Outdoors** - Topographic map
- Lebih cepat & smooth
- Lebih cantik & professional
- Vector tiles (scalable)

### ❌ Cons:
- Perlu daftar (gratis)
- Limit 50,000 map loads/bulan (cukup untuk development)

---

## 🚀 How to Switch to Mapbox Styled

### Step 1: Get Mapbox Token (FREE)

1. Buka: https://account.mapbox.com/auth/signup/
2. Daftar dengan email
3. Verify email
4. Copy **Access Token** dari dashboard

### Step 2: Update Code

Edit `components/gis/map-preview.tsx`:

```tsx
// GANTI DARI:
const MapboxMap = dynamic(() => import('./mapbox-map'), {
    ssr: false,
    loading: () => (...)
});

// MENJADI:
const MapboxMap = dynamic(() => import('./mapbox-map-styled'), {
    ssr: false,
    loading: () => (...)
});
```

### Step 3: Add Token

Edit `components/gis/mapbox-map-styled.tsx`:

```tsx
// Line 13 - GANTI:
const MAPBOX_TOKEN = 'YOUR_MAPBOX_TOKEN_HERE';

// DENGAN TOKEN ANDA:
const MAPBOX_TOKEN = 'pk.eyJ1IjoieW91cnVzZXJuYW1lIiwiYSI6ImNsZjR4...' // Token dari Mapbox
```

### Step 4: Choose Style (Optional)

Uncomment style yang Anda inginkan di line 67-78:

```tsx
// Default: Streets
mapStyle={`https://api.mapbox.com/styles/v1/mapbox/streets-v12?access_token=${MAPBOX_TOKEN}`}

// Atau pilih yang lain (uncomment salah satu):
// mapStyle={`https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12?access_token=${MAPBOX_TOKEN}`}
// mapStyle={`https://api.mapbox.com/styles/v1/mapbox/dark-v11?access_token=${MAPBOX_TOKEN}`}
```

### Step 5: Refresh Browser

Hard refresh: `Ctrl + Shift + R`

---

## 📊 Comparison Table

| Feature | OpenStreetMap | Mapbox Styled |
|---------|---------------|---------------|
| **Cost** | Free | Free (50k/mo) |
| **Setup** | ✅ Ready | Need token |
| **Styles** | 1 (basic) | 5 (premium) |
| **Satellite** | ❌ | ✅ |
| **Dark Mode** | ❌ | ✅ |
| **Performance** | Good | Excellent |
| **Professional Look** | Basic | Premium |

---

## 🎨 Style Preview

### 1. Streets (Default)
- Clean, modern street map
- Best for general use
- Shows roads, buildings, labels

### 2. Satellite
- Real aerial imagery
- Best for land analysis
- Shows actual terrain

### 3. Dark
- Dark theme
- Best for night mode
- Modern & sleek

### 4. Light
- Minimal design
- Best for data focus
- Clean & simple

### 5. Outdoors
- Topographic map
- Best for terrain analysis
- Shows elevation, trails

---

## 💡 Recommendation

**For Development:** Use **OpenStreetMap** (current) - sudah cukup bagus dan gratis total.

**For Production:** Use **Mapbox Styled** dengan style **Streets** atau **Satellite** - lebih professional dan user experience lebih baik.

**For Demo/Presentation:** Definitely use **Mapbox Satellite** - paling impressive!

---

## 🔄 Easy Switch Back

Jika ingin kembali ke OpenStreetMap:

```tsx
// Di map-preview.tsx, ganti kembali:
const MapboxMap = dynamic(() => import('./mapbox-map'), { // <- mapbox-map (tanpa -styled)
    ssr: false,
    loading: () => (...)
});
```

---

## 📝 Notes

- Kedua file tetap ada, jadi Anda bisa switch kapan saja
- Token Mapbox gratis selamanya untuk 50k loads/bulan
- Untuk production, bisa upgrade ke paid plan jika perlu
- OpenStreetMap tidak ada limit sama sekali

---

**Current Status:** ✅ Using OpenStreetMap (Free, No Token Required)

**To Try Mapbox:** Follow steps above and get your free token!
