"use client";

import * as React from "react";
import { Search, X, Check, ChevronsUpDown, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SearchableSelectOption {
  value: string;
  label: string;
  sublabel?: string;
}

export interface SearchableSelectProps {
  label?: string;
  placeholder?: string;
  options: SearchableSelectOption[];
  value?: string;
  onChange: (value: string) => void;
  onSearch?: (query: string) => void;
  isLoading?: boolean;
  errorMessage?: string;
  disabled?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function SearchableSelect({
  label,
  placeholder = "Seçiniz...",
  options,
  value,
  onChange,
  onSearch,
  isLoading,
  errorMessage,
  disabled,
  emptyMessage = "Sonuç bulunamadı.",
  className,
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  const containerRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = React.useState(-1);

  // Debounce search query
  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);

    return () => {
      clearTimeout(handler);
    };
  }, [searchQuery]);

  // Call onSearch when debounced query changes
  React.useEffect(() => {
    if (onSearch && isOpen) {
      onSearch(debouncedQuery);
    }
  }, [debouncedQuery, onSearch, isOpen]);

  // Handle click outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const selectedOption = options.find((opt) => opt.value === value);

  const handleToggle = () => {
    if (disabled) return;
    setIsOpen(!isOpen);
    if (!isOpen) {
      setSearchQuery("");
      setActiveIndex(-1);
      // Focus input on next tick
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const handleSelect = (option: SearchableSelectOption) => {
    onChange(option.value);
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange("");
    setSearchQuery("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    if (!isOpen) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        handleToggle();
      }
      return;
    }

    switch (e.key) {
      case "Escape":
        setIsOpen(false);
        break;
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) => (prev < options.length - 1 ? prev + 1 : prev));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : 0));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < options.length) {
          handleSelect(options[activeIndex]);
        }
        break;
      case "Tab":
        setIsOpen(false);
        break;
    }
  };

  // Scroll active item into view
  React.useEffect(() => {
    if (activeIndex !== -1 && listRef.current) {
      const activeElement = listRef.current.children[activeIndex] as HTMLElement;
      if (activeElement) {
        activeElement.scrollIntoView({ block: "nearest" });
      }
    }
  }, [activeIndex]);

  return (
    <div className={cn("w-full space-y-2", className)} ref={containerRef}>
      {label && (
        <label
          className={cn(
            "text-sm font-medium leading-none",
            errorMessage ? "text-red-500" : "text-zinc-900 dark:text-zinc-100"
          )}
        >
          {label}
        </label>
      )}

      <div className="relative">
        <div
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-controls="options-list"
          aria-labelledby={label}
          onClick={handleToggle}
          onKeyDown={handleKeyDown}
          tabIndex={disabled ? -1 : 0}
          className={cn(
            "flex h-10 w-full items-center justify-between rounded-lg border bg-white dark:bg-zinc-950 px-3 py-2 text-sm ring-offset-white dark:ring-offset-zinc-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
            disabled ? "cursor-not-allowed opacity-50 bg-zinc-100 dark:bg-zinc-800" : "cursor-pointer",
            errorMessage ? "border-red-500" : "border-zinc-300 dark:border-zinc-700",
            isOpen && "ring-2 ring-blue-500 ring-offset-2"
          )}
        >
          <div className="flex-1 truncate">
            {selectedOption ? (
              <span className="text-zinc-900 dark:text-zinc-100">{selectedOption.label}</span>
            ) : (
              <span className="text-zinc-500 dark:text-zinc-400">{placeholder}</span>
            )}
          </div>

          <div className="flex items-center gap-1">
            {value && !disabled && (
              <button
                type="button"
                onClick={handleClear}
                className="rounded-full p-0.5 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                aria-label="Temizle"
              >
                <X className="h-3 w-3 text-zinc-500 dark:text-zinc-400" />
              </button>
            )}
            <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
          </div>
        </div>

        {isOpen && (
          <div className="absolute z-50 mt-1 w-full rounded-md border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 shadow-lg outline-none animate-in fade-in-0 zoom-in-95">
            <div className="flex items-center border-b border-zinc-200 dark:border-zinc-700 px-3">
              <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
              <input
                ref={inputRef}
                className="flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-zinc-500 dark:placeholder:text-zinc-400 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Ara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoComplete="off"
              />
              {isLoading && <Loader2 className="h-4 w-4 animate-spin opacity-50" />}
            </div>

            <div
              id="options-list"
              role="listbox"
              ref={listRef}
              className="max-h-[300px] overflow-y-auto overflow-x-hidden p-1"
            >
              {options.length === 0 ? (
                <div className="py-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  {isLoading ? "Yükleniyor..." : emptyMessage}
                </div>
              ) : (
                options.map((option, index) => (
                  <div
                    key={option.value}
                    role="option"
                    aria-selected={value === option.value}
                    onClick={() => handleSelect(option)}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors",
                      activeIndex === index ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100" : "text-zinc-900 dark:text-zinc-100",
                      value === option.value && "bg-blue-50 dark:bg-blue-900/20"
                    )}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4 text-blue-600",
                        value === option.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex flex-col">
                      <span className="font-medium">{option.label}</span>
                      {option.sublabel && (
                        <span className="text-xs text-zinc-500 dark:text-zinc-400">
                          {option.sublabel}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <p className="text-sm text-red-500">{errorMessage}</p>
      )}
    </div>
  );
}
