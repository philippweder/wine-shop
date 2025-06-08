"use client";

import React, { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import { Wine } from "@/types";
import WineCard from "@/components/WineCard";

const getWines = async (): Promise<Wine[]> => {
  try {
    const response = await fetch("http://localhost:8000/wines/");
    if (!response.ok) {
      console.error("[BrowseWinesPage - getWines] Network response was not ok. Status:", response.status, "StatusText:", response.statusText); // Log 3 - KEEP
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data: Wine[] = await response.json();
    return data;
  } catch (error) {
    console.error("[BrowseWinesPage - getWines] Error fetching or parsing wines:", error); // Log 5 - KEEP
    throw error;
  }
};

const BrowseWinesPage: React.FC = () => {
  const [allWines, setAllWines] = useState<Wine[]>([]);
  const [filteredWines, setFilteredWines] = useState<Wine[]>([]);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    const performFetch = async () => {
      if (!isLoading) {
        setIsLoading(true);
      }
      setFetchError(null);

      try {
        const winesData = await getWines();
        if (winesData) {
          setAllWines(winesData);
          setFilteredWines(winesData);
        } else {
          console.log("[BrowseWinesPage] useEffect - winesData is null or undefined after fetch."); // Log C.2 - KEEP
          setFetchError("Received no data from server (winesData was null/undefined).");
        }
      } catch (error) {
        console.error("[BrowseWinesPage] useEffect - Error caught from getWines():", error); // Log D - KEEP
        if (error instanceof Error) {
          setFetchError(`Failed to fetch wines: ${error.message}`);
        } else {
          setFetchError("Failed to fetch wines due to an unknown error.");
        }
        setAllWines([]);
        setFilteredWines([]);
      } finally {
        setIsLoading(false);
      }
    };

    performFetch();
  }, []);

  const handleFilterChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = event.target.value;
    console.log(`[BrowseWinesPage] Filter changed. Selected type: ${selectedType}`); // Log H - KEEP
    setTypeFilter(selectedType);
    if (selectedType === "") {
      setFilteredWines(allWines);
    } else {
      setFilteredWines(
        allWines.filter((wine) => wine.type.toLowerCase() === selectedType.toLowerCase())
      );
    }
  };

  const wineTypes = useMemo(() => {
    const types = new Set(allWines.map((wine) => wine.type));
    return Array.from(types);
  }, [allWines]);

  let winesToDisplay: Wine[] = [];
  if (typeFilter === "") {
    winesToDisplay = allWines;
  } else {
    winesToDisplay = filteredWines;
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-xl text-gray-700">Loading wines, please wait...</p>
        <div className="mt-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-xl text-red-600">Error: {fetchError}</p>
        <p className="text-gray-600 mt-2">
          We couldn&apos;t load the wines at this time. Please try again later.
        </p>
      </div>
    );
  }

  if (!allWines || allWines.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-xl text-gray-700">No wines available at the moment.</p>
        <p className="text-gray-600 mt-2">
          Please check back later or try adjusting your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-serif text-primary mb-8 text-center">
        Explore Our Wine Collection
      </h1>

      <div className="mb-8 flex justify-center">
        <select
          value={typeFilter}
          onChange={handleFilterChange}
          className="p-2 border border-secondary rounded-md shadow-sm focus:ring-primary focus:border-primary bg-card-background text-foreground"
        >
          <option value="">All Types</option>
          {wineTypes.map((type) => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {filteredWines.length === 0 && typeFilter !== "" ? (
        <p className="text-center text-gray-600">
          No wines match the selected filter &quot;{typeFilter}&quot;.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
          {(typeFilter === "" ? allWines : filteredWines).map((wine) => (
            <WineCard key={wine.id} wine={wine} />
          ))}
        </div>
      )}
    </div>
  );
};

export default BrowseWinesPage;
