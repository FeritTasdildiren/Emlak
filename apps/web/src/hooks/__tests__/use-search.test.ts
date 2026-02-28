import { describe, it, expect } from "vitest";
import { getDefaultSearchFilters } from "../use-search";

describe("getDefaultSearchFilters", () => {
  it("varsayılan filtre değerlerini döndürür", () => {
    const filters = getDefaultSearchFilters();

    expect(filters).toEqual({
      q: "",
      city: "",
      district: "",
      property_type: "all",
      listing_type: "all",
      status: "all",
      min_price: undefined,
      max_price: undefined,
      min_area: undefined,
      max_area: undefined,
      sort: "newest",
      page: 1,
      per_page: 10,
    });
  });

  it("her çağrıda yeni bir obje döndürür (referans eşitliği yok)", () => {
    const filters1 = getDefaultSearchFilters();
    const filters2 = getDefaultSearchFilters();

    expect(filters1).not.toBe(filters2);
    expect(filters1).toEqual(filters2);
  });

  it("varsayılan sıralama 'newest' olmalı", () => {
    const filters = getDefaultSearchFilters();
    expect(filters.sort).toBe("newest");
  });

  it("varsayılan sayfa numarası 1, sayfa boyutu 10 olmalı", () => {
    const filters = getDefaultSearchFilters();
    expect(filters.page).toBe(1);
    expect(filters.per_page).toBe(10);
  });

  it("fiyat ve alan filtreleri undefined olmalı (filtrelenmemiş)", () => {
    const filters = getDefaultSearchFilters();
    expect(filters.min_price).toBeUndefined();
    expect(filters.max_price).toBeUndefined();
    expect(filters.min_area).toBeUndefined();
    expect(filters.max_area).toBeUndefined();
  });
});
