import { ClerkProvider as ClerkReactProvider } from '@clerk/clerk-react';
import { type ReactNode } from 'react';

interface ClerkProviderProps {
  children: ReactNode;
}

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

const ClerkProvider = ({ children }: ClerkProviderProps) => {
  // If no Clerk key is provided, render children without authentication
  if (!CLERK_PUBLISHABLE_KEY) {
    return <>{children}</>;
  }

  return (
    <ClerkReactProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      {children}
    </ClerkReactProvider>
  );
};

export default ClerkProvider;