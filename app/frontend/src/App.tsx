import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { LandingPage } from './pages/LandingPage';
import { ExplorePage } from './pages/ExplorePage';
import { GuidePage } from './pages/GuidePage';
import { ReviewPage } from './pages/ReviewPage';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Landing page has its own layout */}
          <Route path="/" element={<LandingPage />} />

          {/* App pages with shared layout */}
          <Route
            path="/explore"
            element={
              <Layout>
                <ExplorePage />
              </Layout>
            }
          />
          <Route
            path="/guide"
            element={
              <Layout>
                <GuidePage />
              </Layout>
            }
          />
          <Route
            path="/review"
            element={
              <Layout>
                <ReviewPage />
              </Layout>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
