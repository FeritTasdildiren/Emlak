"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Search, Loader2, X } from "lucide-react";
import { useSearchSuggestions } from "@/hooks/use-search";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: (value: string) => void;
}

export function SearchBar({ value, onChange, onSearch }: SearchBarProps) {
  const [inputValue, setInputValue] = useState(value);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: suggestions, isLoading } = useSearchSuggestions(inputValue);

  const showDropdown = isOpen && inputValue.length >= 2 && (isLoading || (suggestions && suggestions.length > 0));

  // Sync external value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectSuggestion = useCallback(
    (suggestion: string) => {
      setInputValue(suggestion);
      onChange(suggestion);
      onSearch(suggestion);
      setIsOpen(false);
      setActiveIndex(-1);
      inputRef.current?.blur();
    },
    [onChange, onSearch]
  );

  const submitSearch = useCallback(() => {
    onChange(inputValue);
    onSearch(inputValue);
    setIsOpen(false);
    setActiveIndex(-1);
  }, [inputValue, onChange, onSearch]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showDropdown) {
      if (e.key === "Enter") {
        e.preventDefault();
        submitSearch();
      }
      return;
    }

    const items = suggestions || [];

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) =>
          prev < items.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) =>
          prev > 0 ? prev - 1 : items.length - 1
        );
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && items[activeIndex]) {
          selectSuggestion(items[activeIndex]);
        } else {
          submitSearch();
        }
        break;
      case "Escape":
        setIsOpen(false);
        setActiveIndex(-1);
        break;
    }
  }

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const item = listRef.current.children[activeIndex] as HTMLElement;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setInputValue(val);
    setIsOpen(true);
    setActiveIndex(-1);
    onChange(val);
  }

  function handleClear() {
    setInputValue("");
    onChange("");
    onSearch("");
    setIsOpen(false);
    inputRef.current?.focus();
  }

  return (
    <div ref={containerRef} className="relative flex-1">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 pointer-events-none" />
      <input
        ref={inputRef}
        type="text"
        placeholder="İlan ara... (ilçe, tür, özellik)"
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 pl-10 pr-9 text-sm outline-none transition-colors placeholder:text-gray-400 focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100"
        role="combobox"
        aria-expanded={showDropdown}
        aria-autocomplete="list"
        aria-controls="search-suggestions"
        aria-activedescendant={
          activeIndex >= 0 ? `suggestion-${activeIndex}` : undefined
        }
      />

      {/* Clear button */}
      {inputValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          aria-label="Aramayı temizle"
        >
          <X className="h-4 w-4" />
        </button>
      )}

      {/* Autocomplete dropdown */}
      {showDropdown && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
          {isLoading ? (
            <div className="flex items-center gap-2 px-4 py-3 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Aranıyor...
            </div>
          ) : (
            <ul
              ref={listRef}
              id="search-suggestions"
              role="listbox"
              className="max-h-60 overflow-auto py-1"
            >
              {suggestions?.map((suggestion, index) => (
                <li
                  key={suggestion}
                  id={`suggestion-${index}`}
                  role="option"
                  aria-selected={index === activeIndex}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 px-4 py-2.5 text-sm transition-colors",
                    index === activeIndex
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-50"
                  )}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    selectSuggestion(suggestion);
                  }}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <Search className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                  <span className="truncate">{suggestion}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
