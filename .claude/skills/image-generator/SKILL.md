---
name: image-generator
description: Apply this skill when generating mockups, UI screenshots, marketing assets, or visual design prompts for the boxing app. Contains the brand identity (colors, typography, style) and prompt templates. Trigger on: "generate image", "mockup", "app screenshot", "marketing asset", "visual design", "brand", "UI design", "create image prompt", "design the screen".
---

# Image Generator — mobile-boxing-app (gymshock)

## Brand Identity

### Colors
| Name | Hex | Usage |
|------|-----|-------|
| Primary Green | `#0F6E56` | CTAs, active states, brand elements |
| Dark Background | `#1A1A1A` | App background (dark mode default) |
| Light Text | `#F5F5F5` | Primary text on dark background |
| Accent Gold | `#D4A017` | Score indicators, achievements |
| Error Red | `#E53E3E` | Error states, warnings |
| Surface Dark | `#2D2D2D` | Cards, surfaces above background |

### Typography
- Headlines: Bold, uppercase or mixed case, clean sans-serif
- Body: Regular weight, high contrast on dark background
- Data/scores: Monospace or tabular figures

### Visual style
- Dark mode first (boxing gym aesthetic)
- Minimal, athletic, data-forward
- Green accents on dark backgrounds (not neon, subdued professional)
- Real boxing photography or silhouettes (not cartoons)

## UI Mockup Prompt Templates

### App home screen
```
Dark mobile app screen for boxing training app "gymshock". 
Dark background #1A1A1A, green accent color #0F6E56.
Shows: today's training progress (circular progress ring in green),
recent session score badge, bottom tab navigation with icons.
Clean athletic design, professional fitness app aesthetic.
No text needed, show layout only. iOS-style rounded corners.
```

### Real-time analysis screen
```
Mobile boxing app real-time camera screen. Dark UI overlay on camera feed.
Shows: skeleton pose overlay with green joint points connected by lines,
circular score indicator top-right showing "87" in green,
bottom feedback banner "Extiende el jab" in white text on dark background.
Athletic HUD design, green accent #0F6E56 on dark #1A1A1A overlays.
Portrait orientation, modern fitness app style.
```

### Session results screen  
```
Post-session results screen for boxing training app.
Dark background #1A1A1A. Shows: large score circle "84/100" in green #0F6E56,
bar chart showing jab/cross/hook scores, session duration and punch count stats.
Gold accent #D4A017 for personal best indicator.
Clean data visualization, dark athletic design.
```

### Onboarding consent screen
```
Trust-building mobile onboarding screen for fitness app.
Clean dark design #1A1A1A, green accent #0F6E56.
Shows: shield/lock icon at top, simple bullet points about data privacy,
two buttons: "Acepto" (green primary) and "Leer más" (text only).
Minimal, professional, reassuring aesthetic.
```

## Marketing Asset Prompts

### App store screenshot (portrait)
```
Professional app store screenshot for boxing training app gymshock.
Shows phone mockup with app interface, dark theme, green accents.
Text overlay: "Analiza tu técnica en tiempo real" in bold white text.
Green gradient background, athletic photography of boxer silhouette.
Clean, modern sports app aesthetic. 1242x2688 pixel dimensions.
```

### Social media post (square)
```
Square social media post for boxing training app announcement.
Dark background #1A1A1A, green diagonal accent stripe #0F6E56.
Phone mockup showing score screen, bold headline "Mejora tu jab" in white.
Gymshock logo, minimal design, sports brand aesthetic.
1080x1080 pixels.
```

## Figma/Excalidraw component conventions
When describing UI for diagrams:
- Buttons: rounded corners 8px, green fill for primary, outlined for secondary
- Cards: dark surface `#2D2D2D`, 12px corner radius, subtle border
- Icons: outline style, 24px, white or green
- Spacing: 16px base unit (4px grid)
