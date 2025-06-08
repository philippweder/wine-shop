export interface Wine {
  id: number;
  name: string;
  type: string;
  varietal: string;
  price: number;
  vintage?: number | null;
  region?: string | null;
  country?: string | null;
  description?: string | null;
  image_url?: string | null;
}
