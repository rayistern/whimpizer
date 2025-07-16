import { useAuth as useClerkAuth } from '@clerk/clerk-react';
import { useEffect } from 'react';
import { setAuthToken } from '../services/api';

export const useAuth = () => {
  const { getToken, isSignedIn, isLoaded } = useClerkAuth();

  useEffect(() => {
    const updateToken = async () => {
      if (isLoaded) {
        if (isSignedIn) {
          try {
            const token = await getToken();
            setAuthToken(token);
          } catch (error) {
            console.error('Failed to get auth token:', error);
            setAuthToken(null);
          }
        } else {
          setAuthToken(null);
        }
      }
    };

    updateToken();
  }, [isSignedIn, isLoaded, getToken]);

  return {
    isSignedIn,
    isLoaded,
    getToken,
  };
};