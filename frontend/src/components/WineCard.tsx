"use client";

import Image from "next/image";
import { Wine } from "@/types";

interface WineCardProps {
  wine: Wine;
}

export default function WineCard({ wine }: WineCardProps) {
  return (
    <div
      key={wine.id}
      className="group rounded-xl border border-border-color bg-card shadow-lg overflow-hidden transition-all duration-300 ease-in-out hover:shadow-2xl hover:border-primary/50 flex flex-col"
    >
      {wine.image_url ? (
        <div className="w-full h-64 bg-gray-200 dark:bg-gray-700 relative overflow-hidden">
          <Image
            src={wine.image_url}
            alt={wine.name}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw" // Basic responsive sizes, adjust as needed
            className="object-contain transition-transform duration-500 group-hover:scale-105" // Use Tailwind for object-fit
          />
        </div>
      ) : (
        <div className="w-full h-64 bg-secondary/20 flex items-center justify-center text-primary/50">
          <span className="text-sm">No Image</span>
        </div>
      )}

      <div className="p-5 flex flex-col flex-grow">
        <h2 className="mb-2 text-xl font-semibold font-serif text-primary group-hover:text-primary/80">
          {wine.name}
        </h2>
        <p className="text-sm text-accent font-sans">
          {wine.type} - {wine.varietal}
        </p>
        <p className="text-xs text-secondary/80 font-sans mb-2">
          {wine.region || "Region N/A"}, {wine.country || "Country N/A"} {wine.vintage ? `(${wine.vintage})` : "(N/V)"}
        </p>

        {wine.description && (
          <p className="mb-3 text-xs text-foreground/70 font-sans leading-relaxed flex-grow">
            {wine.description}
          </p>
        )}

        <p className="mt-auto mb-3 text-2xl font-bold font-serif text-primary">
          ${wine.price.toFixed(2)}
        </p>

        <button
          className="mt-2 w-full py-2 px-4 bg-primary/10 text-primary border border-primary/30 rounded-lg text-xs font-sans transition-colors hover:bg-primary/20 hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-card"
          onClick={() => console.log(`Chat about ${wine.name}`)}
        >
          Discuss this Wine
        </button>
      </div>
    </div>
  );
}
