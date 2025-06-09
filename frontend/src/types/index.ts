export interface Wine {
  id: number;
  name: string;
  type: string | null; // Can be null from martel_wines.json
  varietal: string | null; // Can be null
  price: number;
  vintage?: number | string | null; // Scraped vintage is string, model is Int
  region?: string | null;
  country?: string | null;
  description?: string | null;
  image_url?: string | null;
  producer?: string | null; // New field (from brandName)
  sub_region?: string | null; // New field
  food_pairing?: string | null; // New field
  drinking_window?: string | null; // New field
  body_type?: string | null; // New field
  product_url?: string | null; // New field
  size?: string | null; // New field
  source?: string | null; // New field
}
