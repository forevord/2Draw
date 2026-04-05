# Architecture

## Agent Pipeline

```
Image Upload
    └── Image Agent (k-means segmentation)
            └── ColorMatch Agent (delta-E CIE76)
                    ├── Search Agent (marketplace URLs)
                    └── Manual Agent (Claude painting guide)
                            └── PDF Agent (ReportLab → R2)
```

## Screens

1. Landing + Upload
2. Settings (style, zones, brands, language)
3. Processing (live pipeline view)
4. Preview (canvas + palette)
5. Stripe Checkout
6. Success + PDF Download

## Regions & Marketplaces

| Region | Marketplace |
|--------|-------------|
| PL     | Allegro     |
| DE     | Amazon.de   |
| RU     | Wildberries |
| EN     | Amazon.com  |

## Paint Brands

- Winsor & Newton
- Liquitex
