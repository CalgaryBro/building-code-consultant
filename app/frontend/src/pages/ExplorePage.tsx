import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Search,
  BookOpen,
  FileText,
  ChevronRight,
  ChevronDown,
  Filter,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Ruler,
  X,
  Sparkles,
  Building2,
  Scale,
  FileCode,
  Lightbulb,
  Target,
  ArrowRight,
  ScrollText,
  ExternalLink,
  Calendar,
  Tag,
} from 'lucide-react';
import { exploreApi } from '../api/client';
import type { ArticleSearchResult, Requirement, Code, StandataSummary } from '../types';

const codeTypes = [
  { id: 'building', label: 'Building Code', apiValue: 'building', icon: Building2 },
  { id: 'fire', label: 'Fire Code', apiValue: 'fire', icon: FileCode },
  { id: 'zoning', label: 'Land Use Bylaw', apiValue: 'zoning', icon: Scale },
  { id: 'standata', label: 'STANDATA', apiValue: 'standata', icon: FileText },
];

const partNumbers = [
  { id: 3, label: 'Part 3 - Fire Protection', shortLabel: 'Part 3' },
  { id: 9, label: 'Part 9 - Housing & Small Buildings', shortLabel: 'Part 9' },
];

// Blueprint grid background component
function BlueprintBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-slate-50" />

      {/* Main grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Fine grid */}
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '8px 8px',
        }}
      />

      {/* Decorative elements */}
      <svg className="absolute top-20 right-20 w-48 h-48 text-slate-200/20" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="4 2" />
        <circle cx="50" cy="50" r="30" fill="none" stroke="currentColor" strokeWidth="0.5" />
      </svg>

      {/* Corner marks */}
      <div className="absolute top-6 left-6 w-12 h-12 border-l-2 border-t-2 border-slate-200/30" />
      <div className="absolute bottom-6 right-6 w-12 h-12 border-r-2 border-b-2 border-slate-200/30" />
    </div>
  );
}

// Animated search indicator
function SearchPulse({ isSearching }: { isSearching: boolean }) {
  if (!isSearching) return null;

  return (
    <div className="absolute inset-0 pointer-events-none">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: [0.5, 0], scale: [0.8, 1.2] }}
        transition={{ duration: 1.5, repeat: Infinity }}
        className="absolute inset-0 rounded-xl border-2 border-amber-400"
      />
    </div>
  );
}

export function ExplorePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedArticle, setSelectedArticle] = useState<ArticleSearchResult | null>(null);
  const [filters, setFilters] = useState<{
    codeTypes: string[];
    partNumbers: number[];
  }>({
    codeTypes: [],
    partNumbers: [],
  });
  const [showFilters, setShowFilters] = useState(false);

  // Fetch available codes for browsing
  const { data: codes } = useQuery({
    queryKey: ['codes'],
    queryFn: () => exploreApi.listCodes({ current_only: true }),
    staleTime: 10 * 60 * 1000,
  });

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: (query: string) =>
      exploreApi.search({
        query,
        code_types: filters.codeTypes.length > 0 ? filters.codeTypes : undefined,
        part_numbers: filters.partNumbers.length > 0 ? filters.partNumbers : undefined,
        limit: 20,
        use_semantic: true,
      }),
  });

  // Fetch requirements for selected article
  const { data: requirements, isLoading: loadingRequirements } = useQuery({
    queryKey: ['requirements', selectedArticle?.id],
    queryFn: () => selectedArticle ? exploreApi.getArticleRequirements(selectedArticle.id) : null,
    enabled: !!selectedArticle?.id,
  });

  // Fetch related Standata bulletins for selected article
  const { data: relatedStandata, isLoading: loadingStandata } = useQuery({
    queryKey: ['relatedStandata', selectedArticle?.article_number],
    queryFn: () => selectedArticle ? exploreApi.getRelatedStandata(selectedArticle.article_number) : null,
    enabled: !!selectedArticle?.article_number && selectedArticle?.code_short_name !== 'STANDATA',
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSelectedArticle(null);
    searchMutation.mutate(searchQuery);
  };

  const toggleCodeType = (id: string) => {
    setFilters((prev) => ({
      ...prev,
      codeTypes: prev.codeTypes.includes(id)
        ? prev.codeTypes.filter((t) => t !== id)
        : [...prev.codeTypes, id],
    }));
  };

  const togglePartNumber = (id: number) => {
    setFilters((prev) => ({
      ...prev,
      partNumbers: prev.partNumbers.includes(id)
        ? prev.partNumbers.filter((n) => n !== id)
        : [...prev.partNumbers, id],
    }));
  };

  const handleArticleClick = (article: ArticleSearchResult) => {
    setSelectedArticle(selectedArticle?.id === article.id ? null : article);
  };

  const codesByType = codes?.reduce((acc, code) => {
    const type = code.code_type;
    if (!acc[type]) acc[type] = [];
    acc[type].push(code);
    return acc;
  }, {} as Record<string, Code[]>) || {};

  const hasSearched = searchMutation.data !== undefined || searchMutation.isPending;
  const results = searchMutation.data?.results || [];
  const isSearching = searchMutation.isPending;
  const activeFilterCount = filters.codeTypes.length + filters.partNumbers.length;

  return (
    <div className="min-h-screen relative">
      <BlueprintBackground />

      <div className="relative p-8 max-w-7xl mx-auto">
        {/* Header with refined typography */}
        <motion.header
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center shadow-xl shadow-slate-900/20">
              <Search className="w-7 h-7 text-amber-400" />
            </div>
            <div>
              <h1 className="font-display text-4xl text-slate-900 mb-2 tracking-tight">
                Explore Building Codes
              </h1>
              <p className="text-slate-500 text-lg max-w-xl leading-relaxed">
                Search NBC(AE) 2023, Calgary Land Use Bylaw 1P2007, and STANDATA bulletins
                using natural language or exact code references.
              </p>
            </div>
          </div>
        </motion.header>

        {/* Search Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <form onSubmit={handleSearch}>
            <div className="relative">
              <SearchPulse isSearching={isSearching} />

              {/* Search input container */}
              <div className="relative bg-white rounded-xl border border-slate-200 shadow-lg shadow-slate-900/5 overflow-hidden transition-all duration-300 hover:shadow-xl hover:border-slate-300 focus-within:ring-2 focus-within:ring-amber-400 focus-within:border-amber-400">
                <div className="flex items-center">
                  <div className="pl-5 pr-3">
                    <Search className="w-5 h-5 text-slate-400" />
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for code requirements... (e.g., 'stair width residential' or '9.8.4.1')"
                    className="flex-1 py-5 px-2 text-lg text-slate-900 placeholder:text-slate-400 outline-none bg-transparent"
                  />
                  <div className="flex items-center gap-2 pr-3">
                    {searchQuery && (
                      <motion.button
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        type="button"
                        onClick={() => {
                          setSearchQuery('');
                          searchMutation.reset();
                          setSelectedArticle(null);
                        }}
                        className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </motion.button>
                    )}
                    <button
                      type="submit"
                      disabled={isSearching || !searchQuery.trim()}
                      className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                    >
                      {isSearching ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Searching</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          <span>Search</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </form>

          {/* Filter toggle */}
          <div className="mt-4 flex items-center gap-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                showFilters
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
              {activeFilterCount > 0 && (
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                  showFilters ? 'bg-amber-400 text-slate-900' : 'bg-amber-100 text-amber-700'
                }`}>
                  {activeFilterCount}
                </span>
              )}
            </button>

            {/* Active filter pills */}
            {activeFilterCount > 0 && !showFilters && (
              <div className="flex items-center gap-2">
                {filters.codeTypes.map((type) => (
                  <span
                    key={type}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-amber-50 text-amber-700 text-sm font-medium rounded-full border border-amber-200"
                  >
                    {codeTypes.find(t => t.apiValue === type)?.label}
                    <button
                      onClick={() => toggleCodeType(type)}
                      className="ml-1 hover:text-amber-900"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                {filters.partNumbers.map((num) => (
                  <span
                    key={num}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-slate-100 text-slate-700 text-sm font-medium rounded-full border border-slate-200"
                  >
                    {partNumbers.find(p => p.id === num)?.shortLabel}
                    <button
                      onClick={() => togglePartNumber(num)}
                      className="ml-1 hover:text-slate-900"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 overflow-hidden"
            >
              <div className="bg-white rounded-xl border border-slate-200 shadow-lg p-6">
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Code Types */}
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-amber-500" />
                      Code Type
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      {codeTypes.map((type) => {
                        const Icon = type.icon;
                        const isActive = filters.codeTypes.includes(type.apiValue);
                        return (
                          <button
                            key={type.id}
                            onClick={() => toggleCodeType(type.apiValue)}
                            className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all ${
                              isActive
                                ? 'border-amber-400 bg-amber-50 text-amber-900'
                                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                            }`}
                          >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-amber-500' : 'text-slate-400'}`} />
                            <span className="font-medium text-sm">{type.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Part Numbers */}
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-amber-500" />
                      Code Section
                    </h3>
                    <div className="space-y-3">
                      {partNumbers.map((part) => {
                        const isActive = filters.partNumbers.includes(part.id);
                        return (
                          <button
                            key={part.id}
                            onClick={() => togglePartNumber(part.id)}
                            className={`w-full flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left ${
                              isActive
                                ? 'border-amber-400 bg-amber-50 text-amber-900'
                                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                            }`}
                          >
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                              isActive ? 'bg-amber-400 text-white' : 'bg-slate-100 text-slate-500'
                            }`}>
                              {part.id}
                            </div>
                            <span className="font-medium text-sm">{part.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Clear filters */}
                {activeFilterCount > 0 && (
                  <div className="mt-6 pt-4 border-t border-slate-100">
                    <button
                      onClick={() => setFilters({ codeTypes: [], partNumbers: [] })}
                      className="text-sm text-slate-500 hover:text-slate-700 font-medium"
                    >
                      Clear all filters
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex gap-6">
          {/* Results Column */}
          <div className="flex-1 min-w-0">
            {/* Error State */}
            {searchMutation.isError && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-5 bg-rose-50 border border-rose-200 rounded-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center">
                    <AlertCircle className="w-5 h-5 text-rose-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-rose-800">Search Error</h3>
                    <p className="text-sm text-rose-600">
                      {searchMutation.error instanceof Error
                        ? searchMutation.error.message
                        : 'Failed to search. Please check if the backend is running.'}
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Results */}
            {hasSearched && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {/* Results header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    {isSearching ? (
                      <div className="flex items-center gap-2 text-slate-500">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Searching...</span>
                      </div>
                    ) : (
                      <>
                        <span className="text-slate-600">
                          Found <span className="font-semibold text-slate-900">{results.length}</span> results
                          for "<span className="font-semibold text-slate-900">{searchQuery}</span>"
                        </span>
                        {searchMutation.data?.search_type && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-teal-50 text-teal-700 text-xs font-medium rounded-md">
                            <Sparkles className="w-3 h-3" />
                            {searchMutation.data.search_type}
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Results list */}
                <div className="space-y-4">
                  <AnimatePresence mode="popLayout">
                    {results.map((result, index) => (
                      <motion.div
                        key={result.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ delay: index * 0.05 }}
                        layout
                      >
                        <button
                          onClick={() => handleArticleClick(result)}
                          className={`w-full text-left bg-white rounded-xl border-2 p-6 transition-all duration-200 ${
                            selectedArticle?.id === result.id
                              ? 'border-amber-400 shadow-xl shadow-amber-500/10'
                              : 'border-slate-200 shadow-md hover:shadow-lg hover:border-slate-300'
                          }`}
                        >
                          <div className="flex items-start gap-4">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-all ${
                              selectedArticle?.id === result.id
                                ? 'bg-gradient-to-br from-amber-400 to-amber-500'
                                : 'bg-slate-100'
                            }`}>
                              <FileText className={`w-6 h-6 ${
                                selectedArticle?.id === result.id
                                  ? 'text-white'
                                  : 'text-slate-500'
                              }`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="font-mono text-sm font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                                  {result.article_number}
                                </span>
                                <span className="text-xs text-slate-400 font-medium">
                                  {result.code_short_name} {result.code_version}
                                </span>
                                {result.relevance_score && result.relevance_score > 0.9 && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-teal-50 text-teal-700 text-xs font-medium rounded">
                                    <Target className="w-3 h-3" />
                                    High Match
                                  </span>
                                )}
                              </div>
                              <h3 className={`font-semibold text-lg mb-2 transition-colors ${
                                selectedArticle?.id === result.id
                                  ? 'text-amber-600'
                                  : 'text-slate-900'
                              }`}>
                                {result.title || 'Untitled Article'}
                              </h3>
                              <p className="text-slate-500 line-clamp-2 leading-relaxed">
                                {result.highlight || result.full_text}
                              </p>
                            </div>
                            <div className="flex-shrink-0">
                              {selectedArticle?.id === result.id ? (
                                <ChevronDown className="w-5 h-5 text-amber-500" />
                              ) : (
                                <ChevronRight className="w-5 h-5 text-slate-300" />
                              )}
                            </div>
                          </div>

                          {/* Expanded content */}
                          <AnimatePresence>
                            {selectedArticle?.id === result.id && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mt-5 pt-5 border-t border-slate-100"
                              >
                                <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                                  <FileText className="w-4 h-4 text-amber-500" />
                                  Full Text
                                </h4>
                                <p className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-100">
                                  {result.full_text}
                                </p>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>

                  {/* No results */}
                  {!isSearching && results.length === 0 && searchMutation.data && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-center py-16"
                    >
                      <div className="w-20 h-20 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-6">
                        <Search className="w-10 h-10 text-slate-300" />
                      </div>
                      <h3 className="text-xl font-semibold text-slate-700 mb-2">No results found</h3>
                      <p className="text-slate-500 max-w-md mx-auto">
                        Try adjusting your search terms or filters. You can also try natural language queries
                        like "stair width for residential" or exact code references like "9.8.4.1".
                      </p>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Empty state - Browse codes */}
            {!hasSearched && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-slate-500" />
                  </div>
                  <h2 className="font-display text-2xl text-slate-900">
                    Browse by Code
                  </h2>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {codeTypes.map((type, index) => {
                    const Icon = type.icon;
                    const codesOfType = codesByType[type.apiValue] || [];
                    return (
                      <motion.button
                        key={type.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 + index * 0.1 }}
                        onClick={() => {
                          setFilters(prev => ({
                            ...prev,
                            codeTypes: [type.apiValue]
                          }));
                          setSearchQuery('*');
                          searchMutation.mutate('*');
                        }}
                        className="group bg-white rounded-xl border-2 border-slate-200 p-6 text-left transition-all hover:border-amber-400 hover:shadow-xl shadow-md"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-14 h-14 rounded-xl bg-slate-100 flex items-center justify-center group-hover:bg-gradient-to-br group-hover:from-amber-400 group-hover:to-amber-500 transition-all">
                            <Icon className="w-7 h-7 text-slate-500 group-hover:text-white transition-colors" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg text-slate-900 group-hover:text-amber-600 transition-colors">
                              {type.label}
                            </h3>
                            <p className="text-sm text-slate-500">
                              {codesOfType.length > 0
                                ? `Version ${codesOfType[0].version}`
                                : 'Browse all articles'}
                            </p>
                          </div>
                          <ArrowRight className="w-5 h-5 text-slate-300 group-hover:text-amber-500 group-hover:translate-x-1 transition-all" />
                        </div>
                      </motion.button>
                    );
                  })}
                </div>

                {/* Example Questions */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="mt-8 bg-white rounded-xl border border-slate-200 shadow-md p-6"
                >
                  <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-amber-500" />
                    Try These Questions
                  </h3>
                  <div className="flex flex-wrap gap-3">
                    {[
                      { question: 'minimum ceiling height for bedrooms', tag: '9.5 Room Heights' },
                      { question: 'egress window requirements for basements', tag: '9.9 Egress' },
                      { question: 'minimum stair width residential', tag: '9.8 Stairs' },
                      { question: 'fire separation garage dwelling', tag: '9.10 Fire' },
                      { question: 'insulation requirements Zone 7A', tag: '9.36 Energy' },
                    ].map((item, index) => (
                      <motion.button
                        key={index}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.6 + index * 0.05 }}
                        onClick={() => {
                          setSearchQuery(item.question);
                          searchMutation.mutate(item.question);
                        }}
                        className="group flex items-center gap-2 px-4 py-2.5 bg-slate-50 hover:bg-amber-50 border border-slate-200 hover:border-amber-300 rounded-lg transition-all hover:shadow-md"
                      >
                        <span className="text-xs font-medium text-amber-600 bg-amber-100 px-2 py-0.5 rounded">
                          {item.tag}
                        </span>
                        <span className="text-sm text-slate-700 group-hover:text-amber-800 transition-colors">
                          {item.question}
                        </span>
                        <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-500 group-hover:translate-x-0.5 transition-all" />
                      </motion.button>
                    ))}
                  </div>
                </motion.div>

                {/* Search tips */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="mt-6 bg-gradient-to-br from-amber-50 to-amber-100/50 rounded-xl border border-amber-200 p-6"
                >
                  <h3 className="font-semibold text-amber-900 mb-4 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-amber-500" />
                    Search Tips
                  </h3>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="bg-white/80 rounded-lg p-4 border border-amber-200/50">
                      <h4 className="font-medium text-amber-800 mb-1 text-sm">Natural Language</h4>
                      <p className="text-sm text-amber-700">"stair width for residential buildings"</p>
                    </div>
                    <div className="bg-white/80 rounded-lg p-4 border border-amber-200/50">
                      <h4 className="font-medium text-amber-800 mb-1 text-sm">Code Reference</h4>
                      <p className="text-sm text-amber-700">"9.8.4.1" or "NBC 9.8"</p>
                    </div>
                    <div className="bg-white/80 rounded-lg p-4 border border-amber-200/50">
                      <h4 className="font-medium text-amber-800 mb-1 text-sm">By Element</h4>
                      <p className="text-sm text-amber-700">"fire separation" or "setback requirements"</p>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </div>

          {/* Requirements Panel */}
          <AnimatePresence>
            {selectedArticle && (
              <motion.aside
                initial={{ opacity: 0, x: 20, width: 0 }}
                animate={{ opacity: 1, x: 0, width: 400 }}
                exit={{ opacity: 0, x: 20, width: 0 }}
                className="flex-shrink-0"
              >
                <div className="bg-white rounded-xl border-2 border-slate-200 shadow-lg sticky top-4 overflow-hidden">
                  {/* Panel header */}
                  <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                          <Ruler className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-white">Requirements</h3>
                          <p className="text-xs text-slate-400">Dimensional specifications</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedArticle(null)}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Article info */}
                  <div className="p-4 bg-slate-50 border-b border-slate-200">
                    <span className="font-mono text-sm font-semibold text-amber-600">
                      {selectedArticle.article_number}
                    </span>
                    <p className="text-sm text-slate-600 mt-1">{selectedArticle.title}</p>
                  </div>

                  {/* Requirements list */}
                  <div className="p-4 max-h-[60vh] overflow-y-auto">
                    {loadingRequirements ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
                      </div>
                    ) : requirements && requirements.length > 0 ? (
                      <div className="space-y-4">
                        {requirements.map((req) => (
                          <RequirementCard key={req.id} requirement={req} />
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                          <Ruler className="w-6 h-6 text-slate-300" />
                        </div>
                        <h4 className="font-medium text-slate-700 mb-1 text-sm">No dimensional requirements</h4>
                        <p className="text-xs text-slate-500">
                          This article may contain general provisions
                        </p>
                      </div>
                    )}

                    {/* Related Standata Section */}
                    {selectedArticle?.code_short_name !== 'STANDATA' && (
                      <div className="mt-6 pt-4 border-t border-slate-200">
                        <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                          <ScrollText className="w-4 h-4 text-amber-500" />
                          Related Interpretations
                        </h4>

                        {loadingStandata ? (
                          <div className="flex items-center justify-center py-6">
                            <Loader2 className="w-5 h-5 animate-spin text-amber-500" />
                          </div>
                        ) : relatedStandata && relatedStandata.bulletins.length > 0 ? (
                          <div className="space-y-3">
                            {relatedStandata.bulletins.map((bulletin) => (
                              <StandataCard key={bulletin.id} bulletin={bulletin} />
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-6 bg-slate-50 rounded-lg">
                            <p className="text-xs text-slate-500">
                              No STANDATA bulletins reference this article
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </motion.aside>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// Requirement Card Component
function RequirementCard({ requirement }: { requirement: Requirement }) {
  const getValue = () => {
    if (requirement.exact_value) return requirement.exact_value;
    if (requirement.min_value !== null && requirement.max_value !== null) {
      return `${requirement.min_value} - ${requirement.max_value}`;
    }
    if (requirement.min_value !== null) return `≥ ${requirement.min_value}`;
    if (requirement.max_value !== null) return `≤ ${requirement.max_value}`;
    return 'See code text';
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-white rounded-xl border border-slate-200 p-4 hover:border-amber-200 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-3">
        <span className={`px-2 py-1 text-xs font-semibold rounded uppercase tracking-wide ${
          requirement.requirement_type === 'dimensional'
            ? 'bg-blue-50 text-blue-700'
            : requirement.requirement_type === 'prescriptive'
            ? 'bg-teal-50 text-teal-700'
            : 'bg-slate-100 text-slate-600'
        }`}>
          {requirement.requirement_type}
        </span>
        {requirement.is_verified && (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-teal-50 text-teal-700 text-xs font-medium rounded">
            <CheckCircle2 className="w-3 h-3" />
            Verified
          </span>
        )}
      </div>

      <h4 className="font-semibold text-slate-900 mb-2 capitalize">
        {requirement.element.replace(/_/g, ' ')}
      </h4>

      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-3xl font-bold text-amber-600">
          {getValue()}
        </span>
        {requirement.unit && (
          <span className="text-sm font-medium text-slate-500">{requirement.unit}</span>
        )}
      </div>

      {requirement.description && (
        <p className="text-sm text-slate-500 mb-3 leading-relaxed">
          {requirement.description}
        </p>
      )}

      {requirement.exact_quote && (
        <div className="text-xs text-slate-600 italic bg-amber-50 p-3 rounded-lg border-l-2 border-amber-400">
          "{requirement.exact_quote.substring(0, 150)}
          {requirement.exact_quote.length > 150 ? '...' : ''}"
        </div>
      )}

      <div className="flex items-center gap-2 mt-3 flex-wrap">
        {requirement.applies_to_part_9 && (
          <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded">
            Part 9
          </span>
        )}
        {requirement.applies_to_part_3 && (
          <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded">
            Part 3
          </span>
        )}
        {requirement.is_mandatory && (
          <span className="px-2 py-1 bg-rose-50 text-rose-600 text-xs font-medium rounded">
            Mandatory
          </span>
        )}
      </div>
    </div>
  );
}

// Standata Card Component
function StandataCard({ bulletin }: { bulletin: StandataSummary }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'BCI':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'BCB':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'FCB':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'PCB':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'BCI':
        return 'Building Code Interpretation';
      case 'BCB':
        return 'Building Code Bulletin';
      case 'FCB':
        return 'Fire Code Bulletin';
      case 'PCB':
        return 'Plumbing Code Bulletin';
      default:
        return category;
    }
  };

  return (
    <motion.div
      layout
      className="bg-gradient-to-br from-amber-50/50 to-white rounded-lg border border-amber-200/50 overflow-hidden hover:border-amber-300 transition-all cursor-pointer"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="p-3">
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${getCategoryColor(bulletin.category)}`}>
            {bulletin.category}
          </span>
          <span className="font-mono text-xs text-amber-600 bg-amber-100/50 px-1.5 py-0.5 rounded">
            {bulletin.bulletin_number}
          </span>
        </div>

        <h5 className="font-medium text-sm text-slate-900 leading-snug mb-2">
          {bulletin.title}
        </h5>

        {bulletin.effective_date && (
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <Calendar className="w-3 h-3" />
            <span>
              {new Date(bulletin.effective_date).toLocaleDateString('en-CA', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </span>
          </div>
        )}

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 pt-3 border-t border-amber-200/50"
            >
              {bulletin.summary && (
                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  {bulletin.summary}
                </p>
              )}

              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-400">
                  {getCategoryLabel(bulletin.category)}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Could open a modal or navigate to full bulletin
                  }}
                  className="flex items-center gap-1 text-xs text-amber-600 hover:text-amber-700 font-medium"
                >
                  View Full Bulletin
                  <ExternalLink className="w-3 h-3" />
                </button>
              </div>

              {bulletin.code_references && bulletin.code_references.length > 0 && (
                <div className="mt-2 pt-2 border-t border-amber-200/30">
                  <div className="flex items-center gap-1 mb-1">
                    <Tag className="w-3 h-3 text-slate-400" />
                    <span className="text-[10px] text-slate-500">References:</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {bulletin.code_references.slice(0, 5).map((ref, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-[10px] font-mono rounded"
                      >
                        {ref}
                      </span>
                    ))}
                    {bulletin.code_references.length > 5 && (
                      <span className="px-1.5 py-0.5 text-slate-500 text-[10px]">
                        +{bulletin.code_references.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
