import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Loader2,
  FileText,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Lock,
  Zap,
  BookOpen,
  Shield,
  ArrowRight,
} from 'lucide-react';
import { publicApi } from '../../api/client';
import type { ArticleSearchResult } from '../../types';

interface ExploreWidgetProps {
  className?: string;
}

interface SearchResponse {
  query: string;
  total_results: number;
  results: ArticleSearchResult[];
  search_type: string;
  is_limited: boolean;
  results_shown: number;
  total_available: number;
  upgrade_message?: string;
  queriesRemaining: number | null;
  dailyLimit: number | null;
  error: boolean;
  rateLimitExceeded: boolean;
  message?: string;
  upgradeUrl?: string;
}

const sampleQuestions = [
  { text: 'Minimum ceiling height for bedrooms?', short: 'Ceiling height' },
  { text: 'Egress window requirements?', short: 'Egress windows' },
  { text: 'Maximum height for R-C1 zone?', short: 'R-C1 height' },
  { text: 'Fire separation for garage?', short: 'Garage fire sep' },
  { text: 'Secondary suite requirements?', short: 'Secondary suites' },
];

export function ExploreWidget({ className = '' }: ExploreWidgetProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [queriesRemaining, setQueriesRemaining] = useState<number | null>(null);
  const [rateLimitExceeded, setRateLimitExceeded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial rate limit status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await publicApi.getRateLimitStatus();
        setQueriesRemaining(status.queries_remaining);
        setRateLimitExceeded(status.queries_remaining <= 0);
      } catch {
        // Silently handle - will show full count as fallback
        setQueriesRemaining(5);
      }
    };
    fetchStatus();
  }, []);

  const handleSearch = async (query: string) => {
    if (!query.trim() || isSearching) return;

    setIsSearching(true);
    setError(null);
    setSearchQuery(query);

    try {
      const result = await publicApi.search({
        query: query.trim(),
        limit: 10,
        use_semantic: true,
      }) as SearchResponse;

      if (result.rateLimitExceeded) {
        setRateLimitExceeded(true);
        setQueriesRemaining(0);
        setSearchResult(null);
      } else {
        setSearchResult(result);
        if (result.queriesRemaining !== null) {
          setQueriesRemaining(result.queriesRemaining);
          setRateLimitExceeded(result.queriesRemaining <= 0);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(searchQuery);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className={`bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <Search className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Try Explore Mode</h3>
              <p className="text-xs text-slate-400">Search Calgary building codes</p>
            </div>
          </div>

          {/* Query counter */}
          <div className="flex items-center gap-2">
            {queriesRemaining !== null && (
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                queriesRemaining > 2
                  ? 'bg-teal-500/20 text-teal-300'
                  : queriesRemaining > 0
                  ? 'bg-amber-500/20 text-amber-300'
                  : 'bg-rose-500/20 text-rose-300'
              }`}>
                {queriesRemaining} {queriesRemaining === 1 ? 'query' : 'queries'} remaining
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Search Form */}
      <div className="p-6">
        <form onSubmit={handleSubmit} className="mb-4">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask about building codes..."
              disabled={rateLimitExceeded}
              className={`w-full px-4 py-3 pl-11 rounded-xl border-2 transition-all outline-none ${
                rateLimitExceeded
                  ? 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed'
                  : 'border-slate-200 hover:border-slate-300 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/20'
              }`}
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            {isSearching && (
              <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-amber-500 animate-spin" />
            )}
          </div>
        </form>

        {/* Sample Questions */}
        {!searchResult && !rateLimitExceeded && (
          <div className="mb-4">
            <p className="text-xs font-medium text-slate-500 mb-2">Try these questions:</p>
            <div className="flex flex-wrap gap-2">
              {sampleQuestions.map((q) => (
                <button
                  key={q.text}
                  onClick={() => handleSearch(q.text)}
                  disabled={isSearching}
                  className="px-3 py-1.5 text-xs font-medium rounded-full bg-slate-100 text-slate-600 hover:bg-amber-50 hover:text-amber-700 hover:border-amber-200 border border-transparent transition-all disabled:opacity-50"
                >
                  {q.short}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl"
          >
            <div className="flex items-center gap-2 text-rose-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          </motion.div>
        )}

        {/* Rate Limit Exceeded */}
        <AnimatePresence>
          {rateLimitExceeded && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="text-center py-6"
            >
              <div className="w-16 h-16 rounded-2xl bg-amber-100 flex items-center justify-center mx-auto mb-4">
                <Lock className="w-8 h-8 text-amber-600" />
              </div>
              <h4 className="font-semibold text-slate-900 mb-2">Daily limit reached</h4>
              <p className="text-sm text-slate-500 mb-4">
                You've used all 5 free searches today.
                <br />
                Sign up for unlimited access!
              </p>
              <Link
                to="/signup"
                className="inline-flex items-center gap-2 px-6 py-3 bg-amber-400 text-slate-900 font-semibold rounded-xl hover:bg-amber-500 transition-all shadow-lg shadow-amber-500/20"
              >
                Sign Up Free
                <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search Results */}
        <AnimatePresence>
          {searchResult && !rateLimitExceeded && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Results header */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-slate-500">
                  Showing <span className="font-semibold text-slate-700">{searchResult.results_shown}</span> of{' '}
                  <span className="font-semibold text-slate-700">{searchResult.total_available}</span> results
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-teal-50 text-teal-700 text-xs font-medium rounded">
                  <Sparkles className="w-3 h-3" />
                  {searchResult.search_type}
                </span>
              </div>

              {/* Result cards */}
              <div className="space-y-3 mb-4">
                {searchResult.results.map((result, index) => (
                  <motion.div
                    key={result.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-slate-50 rounded-xl border border-slate-200 hover:border-amber-200 hover:bg-amber-50/30 transition-all"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center flex-shrink-0">
                        <FileText className="w-5 h-5 text-slate-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-xs font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                            {result.article_number}
                          </span>
                          <span className="text-xs text-slate-400">
                            {result.code_short_name} {result.code_version}
                          </span>
                        </div>
                        <h4 className="font-medium text-slate-900 text-sm mb-1 line-clamp-1">
                          {result.title || 'Code Article'}
                        </h4>
                        <p className="text-xs text-slate-500 line-clamp-2">
                          {result.full_text}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0" />
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* See more CTA */}
              {searchResult.total_available > searchResult.results_shown && (
                <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100/50 rounded-xl border border-amber-200">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-amber-400 flex items-center justify-center flex-shrink-0">
                      <Zap className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-900 mb-1">
                        {searchResult.total_available - searchResult.results_shown} more results available
                      </h4>
                      <p className="text-sm text-slate-600">
                        Sign up free to see all results and get unlimited searches
                      </p>
                    </div>
                    <Link
                      to="/signup"
                      className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white font-semibold rounded-lg hover:bg-slate-800 transition-all text-sm whitespace-nowrap"
                    >
                      Sign Up
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Benefits section */}
        {!searchResult && !rateLimitExceeded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-4 pt-4 border-t border-slate-100"
          >
            <p className="text-xs font-medium text-slate-500 mb-3">Why sign up?</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { icon: Search, text: 'Unlimited searches' },
                { icon: BookOpen, text: 'Save projects' },
                { icon: FileText, text: 'Document review' },
                { icon: Shield, text: 'Compliance checks' },
              ].map((item) => (
                <div
                  key={item.text}
                  className="flex items-center gap-2 p-2 rounded-lg bg-slate-50"
                >
                  <item.icon className="w-4 h-4 text-teal-500" />
                  <span className="text-xs text-slate-600">{item.text}</span>
                </div>
              ))}
            </div>
            <Link
              to="/signup"
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 text-white font-semibold rounded-xl hover:bg-slate-800 transition-all"
            >
              <CheckCircle2 className="w-4 h-4" />
              Start Free Trial
            </Link>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

export default ExploreWidget;
