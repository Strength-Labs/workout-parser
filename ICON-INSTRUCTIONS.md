# App Icon Creation Guide

## Quick Icon Creation

To add a custom icon to your app:

### 1. Create the Icon Image
- Create a **1024x1024 PNG** image with your desired icon design
- Ensure it looks good at small sizes (64x64, 32x32)
- Use simple, recognizable shapes and colors
- Consider gym/fitness/coaching themes

### 2. Convert to ICNS Format

**Option A: Using Icon Converter Online**
1. Go to https://iconverticons.com/online/
2. Upload your 1024x1024 PNG
3. Download the `.icns` file
4. Rename it to `app-icon.icns`
5. Place it in the workout-parser directory

**Option B: Using macOS Command Line**
```bash
# Create iconset folder
mkdir app-icon.iconset

# Create different sizes (you can automate this with sips)
sips -z 16 16 icon-1024.png --out app-icon.iconset/icon_16x16.png
sips -z 32 32 icon-1024.png --out app-icon.iconset/icon_16x16@2x.png
sips -z 32 32 icon-1024.png --out app-icon.iconset/icon_32x32.png
sips -z 64 64 icon-1024.png --out app-icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon-1024.png --out app-icon.iconset/icon_128x128.png
sips -z 256 256 icon-1024.png --out app-icon.iconset/icon_128x128@2x.png
sips -z 256 256 icon-1024.png --out app-icon.iconset/icon_256x256.png
sips -z 512 512 icon-1024.png --out app-icon.iconset/icon_256x256@2x.png
sips -z 512 512 icon-1024.png --out app-icon.iconset/icon_512x512.png
sips -z 1024 1024 icon-1024.png --out app-icon.iconset/icon_512x512@2x.png

# Convert to icns
iconutil -c icns app-icon.iconset
```

### 3. Suggested Icon Design Ideas
- **Barbell or dumbbell** with modern flat design
- **Coach whistle** combined with fitness elements
- **Letter "T"** stylized for "Turnkey" with athletic elements
- **Dashboard/chart** representing coaching analytics
- **Strong, bold colors** like blue, orange, or red

### 4. Test Your Icon
After creating `app-icon.icns`:
1. Run `./build-macos-oneclick.sh`
2. The icon should appear in the Applications folder
3. Test by opening Finder → Applications

## Icon Specifications

The ICNS file should contain these sizes:
- 16x16, 32x32, 128x128, 256x256, 512x512, 1024x1024
- Both standard and @2x (retina) versions
- PNG format within the ICNS container

## Current Status

- ⚠️ **No icon file found** - Create `app-icon.icns` to add custom icon
- ✅ **Icon support ready** - Build script will automatically include it

Place your `app-icon.icns` file in the same directory as this file, then run the build script!