import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import HomePage from './components/HomePage';
import JobStatus from './components/JobStatus';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'status'>('home');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const handleJobSubmitted = (jobId: string) => {
    setCurrentJobId(jobId);
    setCurrentView('status');
  };

  const handleBackToHome = () => {
    setCurrentView('home');
    setCurrentJobId(null);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <Layout currentPage={currentView === 'home' ? 'home' : 'status'}>
        {currentView === 'home' ? (
          <HomePage onJobSubmitted={handleJobSubmitted} />
        ) : currentJobId ? (
          <div className="space-y-6">
            {/* Back to home button */}
            <div className="flex items-center justify-between">
              <button
                onClick={handleBackToHome}
                className="btn-secondary flex items-center space-x-2"
              >
                <span>←</span>
                <span>Create Another Story</span>
              </button>
              
              <div className="text-sm text-gray-600">
                Tip: Bookmark this page to check your job later!
              </div>
            </div>
            
            <JobStatus jobId={currentJobId} />
          </div>
        ) : (
          <div className="text-center">
            <p className="text-gray-600">No job selected.</p>
            <button onClick={handleBackToHome} className="btn-primary mt-4">
              Go Home
            </button>
          </div>
        )}
      </Layout>
    </QueryClientProvider>
  );
}

export default App;
