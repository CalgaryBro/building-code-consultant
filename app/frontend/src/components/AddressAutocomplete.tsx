import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Loader2, X, Building, ChevronDown } from 'lucide-react';
import { addressesApi, type AddressAutocompleteResult } from '../api/client';

interface AddressAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (result: AddressAutocompleteResult) => void;
  placeholder?: string;
  label?: string;
  hint?: string;
  required?: boolean;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export function AddressAutocomplete({
  value,
  onChange,
  onSelect,
  placeholder = 'Enter street address, e.g., 123 Main St NW',
  label,
  hint,
  required,
  error,
  disabled,
  className = '',
}: AddressAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<AddressAutocompleteResult[]>([]);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [hasSearched, setHasSearched] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced search function
  const searchAddresses = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      setHasSearched(false);
      return;
    }

    setIsLoading(true);
    setHasSearched(true);

    try {
      const results = await addressesApi.autocomplete(query, 10);
      setSuggestions(results);
      setHighlightedIndex(-1);
    } catch (err) {
      console.error('Address search error:', err);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle input change with debounce
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setIsOpen(true);

    // Clear existing timeout
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Set new debounce timeout (300ms)
    debounceRef.current = setTimeout(() => {
      searchAddresses(newValue);
    }, 300);
  };

  // Handle suggestion selection
  const handleSelect = (result: AddressAutocompleteResult) => {
    onChange(result.address);
    setSuggestions([]);
    setIsOpen(false);
    setHighlightedIndex(-1);
    onSelect?.(result);
    inputRef.current?.blur();
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === 'ArrowDown' && value.length >= 2) {
        setIsOpen(true);
        searchAddresses(value);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
          handleSelect(suggestions[highlightedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setHighlightedIndex(-1);
        inputRef.current?.blur();
        break;
      case 'Tab':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
    }
  };

  // Handle clear button
  const handleClear = () => {
    onChange('');
    setSuggestions([]);
    setIsOpen(false);
    setHasSearched(false);
    inputRef.current?.focus();
  };

  // Handle focus
  const handleFocus = () => {
    if (value.length >= 2 && suggestions.length > 0) {
      setIsOpen(true);
    }
  };

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && dropdownRef.current) {
      const highlightedElement = dropdownRef.current.querySelector(
        `[data-index="${highlightedIndex}"]`
      );
      highlightedElement?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  const showDropdown = isOpen && (isLoading || suggestions.length > 0 || (hasSearched && value.length >= 2));

  return (
    <div className={`relative ${className}`}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-slate-700 mb-2">
          {label}
          {required && <span className="text-rose-500 ml-1">*</span>}
        </label>
      )}

      {/* Input container */}
      <div className="relative">
        {/* Map pin icon */}
        <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />

        {/* Input field */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            w-full pl-12 pr-12 py-3 rounded-xl border-2
            bg-white text-slate-900 placeholder:text-slate-400
            focus:ring-4 outline-none transition-all duration-200
            ${error
              ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-100'
              : 'border-slate-200 focus:border-amber-500 focus:ring-amber-100'
            }
            ${disabled ? 'bg-slate-50 cursor-not-allowed' : ''}
          `}
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={showDropdown}
          aria-haspopup="listbox"
          role="combobox"
        />

        {/* Right side icons */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && (
            <Loader2 className="w-5 h-5 text-amber-500 animate-spin" />
          )}
          {!isLoading && value && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Clear address"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {!isLoading && !value && (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </div>

      {/* Hint text */}
      {hint && !error && (
        <p className="mt-2 text-sm text-slate-500 flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5" />
          {hint}
        </p>
      )}

      {/* Error text */}
      {error && (
        <p className="mt-2 text-sm text-rose-600">{error}</p>
      )}

      {/* Dropdown */}
      <AnimatePresence>
        {showDropdown && (
          <motion.div
            ref={dropdownRef}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 w-full mt-2 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden"
            role="listbox"
          >
            {/* Loading state */}
            {isLoading && (
              <div className="px-4 py-8 text-center">
                <Loader2 className="w-6 h-6 text-amber-500 animate-spin mx-auto mb-2" />
                <p className="text-sm text-slate-500">Searching addresses...</p>
              </div>
            )}

            {/* No results state */}
            {!isLoading && suggestions.length === 0 && hasSearched && (
              <div className="px-4 py-8 text-center">
                <MapPin className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-slate-600">No addresses found</p>
                <p className="text-xs text-slate-400 mt-1">
                  Try a different search term
                </p>
              </div>
            )}

            {/* Results list */}
            {!isLoading && suggestions.length > 0 && (
              <ul className="max-h-72 overflow-y-auto py-2">
                {suggestions.map((result, index) => (
                  <li
                    key={`${result.parcel_id || result.address}-${index}`}
                    data-index={index}
                    role="option"
                    aria-selected={highlightedIndex === index}
                    onClick={() => handleSelect(result)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`
                      px-4 py-3 cursor-pointer transition-colors
                      ${highlightedIndex === index
                        ? 'bg-amber-50'
                        : 'hover:bg-slate-50'
                      }
                    `}
                  >
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className={`
                        w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5
                        ${highlightedIndex === index
                          ? 'bg-amber-100 text-amber-600'
                          : 'bg-slate-100 text-slate-500'
                        }
                      `}>
                        <MapPin className="w-4 h-4" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <p className={`
                          font-medium truncate
                          ${highlightedIndex === index ? 'text-amber-900' : 'text-slate-900'}
                        `}>
                          {result.address}
                        </p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                          {result.community && (
                            <span className="flex items-center gap-1">
                              <Building className="w-3 h-3" />
                              {result.community}
                            </span>
                          )}
                          {result.zone_code && (
                            <span className={`
                              px-1.5 py-0.5 rounded text-xs font-medium
                              ${highlightedIndex === index
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-slate-100 text-slate-600'
                              }
                            `}>
                              {result.zone_code}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {/* Footer hint */}
            {!isLoading && suggestions.length > 0 && (
              <div className="px-4 py-2 bg-slate-50 border-t border-slate-100">
                <p className="text-xs text-slate-500">
                  Use <kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-200 font-mono text-[10px]">&#8593;</kbd>{' '}
                  <kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-200 font-mono text-[10px]">&#8595;</kbd>{' '}
                  to navigate, <kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-200 font-mono text-[10px]">Enter</kbd> to select,{' '}
                  <kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-200 font-mono text-[10px]">Esc</kbd> to close
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default AddressAutocomplete;
