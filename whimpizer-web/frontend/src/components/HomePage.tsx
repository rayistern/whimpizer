import React, { useState } from 'react';
import { Plus, Trash2, Globe, Wand2, Settings, AlertCircle } from 'lucide-react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { whimpizerAPI, type JobSubmissionRequest } from '../services/api';

interface HomePageProps {
  onJobSubmitted?: (jobId: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onJobSubmitted }) => {
  const [urls, setUrls] = useState<string[]>(['']);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [config, setConfig] = useState({
    ai_provider: 'openai' as const,
    ai_model: 'gpt-4',
    pdf_style: 'handwritten',
    combine_by_group: true,
    temperature: 0.7,
  });

  // Fetch available providers
  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: () => whimpizerAPI.listProviders(),
  });

  // Job submission mutation
  const submitJobMutation = useMutation({
    mutationFn: (data: JobSubmissionRequest) => whimpizerAPI.submitJob(data),
    onSuccess: (response) => {
      const jobId = response.data.job_id;
      onJobSubmitted?.(jobId);
      // Reset form
      setUrls(['']);
      alert(`Job submitted successfully! Job ID: ${jobId}`);
    },
    onError: (error) => {
      console.error('Job submission failed:', error);
      alert('Failed to submit job. Please try again.');
    },
  });

  const addUrl = () => {
    setUrls([...urls, '']);
  };

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const validUrls = urls.filter(url => url.trim() !== '');
    
    if (validUrls.length === 0) {
      alert('Please add at least one URL');
      return;
    }

    // Validate URLs
    const urlPattern = /^https?:\/\/.+/i;
    const invalidUrls = validUrls.filter(url => !urlPattern.test(url));
    
    if (invalidUrls.length > 0) {
      alert('Please enter valid URLs (must start with http:// or https://)');
      return;
    }

    submitJobMutation.mutate({
      urls: validUrls,
      config,
    });
  };

  const getCurrentProviderModels = () => {
    const provider = providers?.data.find(p => p.name === config.ai_provider);
    return provider?.models || [];
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="inline-block p-4 bg-wimpy-yellow rounded-full rotate-slightly">
          <Wand2 className="h-12 w-12 text-wimpy-blue" />
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 comic-style">
          Turn Any Website Into a 
          <span className="text-wimpy-blue"> Wimpy Kid Story!</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Paste in some URLs, pick your AI wizard, and watch as boring websites 
          transform into hilarious diary entries that would make Greg Heffley proud! 📚✨
        </p>
      </div>

      {/* Main Form */}
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL Input Section */}
          <div className="card notebook-paper">
            <div className="flex items-center space-x-3 mb-6">
              <Globe className="h-6 w-6 text-wimpy-blue" />
              <h2 className="text-2xl font-semibold text-gray-900">
                🌐 Add Your Websites
              </h2>
            </div>
            
            <div className="space-y-4">
              {urls.map((url, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => updateUrl(index, e.target.value)}
                    placeholder="https://example.com/awesome-article"
                    className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-wimpy-blue focus:ring-wimpy-blue focus:ring-2 focus:ring-opacity-20 transition-all duration-200"
                  />
                  {urls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeUrl(index)}
                      className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  )}
                </div>
              ))}
              
              <button
                type="button"
                onClick={addUrl}
                className="flex items-center space-x-2 px-4 py-2 text-wimpy-blue hover:bg-blue-50 rounded-lg transition-colors doodle-border"
              >
                <Plus className="h-5 w-5" />
                <span>Add Another URL</span>
              </button>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="card">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-3 w-full text-left"
            >
              <Settings className="h-6 w-6 text-wimpy-blue" />
              <h2 className="text-2xl font-semibold text-gray-900">
                ⚙️ Advanced Settings
              </h2>
              <span className="text-sm text-gray-500">
                ({showAdvanced ? 'Hide' : 'Show'})
              </span>
            </button>

            {showAdvanced && (
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* AI Provider */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    AI Provider
                  </label>
                  <select
                    value={config.ai_provider}
                    onChange={(e) => setConfig({ ...config, ai_provider: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-wimpy-blue focus:ring-wimpy-blue"
                  >
                    {providers?.data.map(provider => (
                      <option key={provider.name} value={provider.name}>
                        {provider.display_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* AI Model */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    AI Model
                  </label>
                  <select
                    value={config.ai_model}
                    onChange={(e) => setConfig({ ...config, ai_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-wimpy-blue focus:ring-wimpy-blue"
                  >
                    {getCurrentProviderModels().map(model => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                </div>

                {/* PDF Style */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    PDF Style
                  </label>
                  <select
                    value={config.pdf_style}
                    onChange={(e) => setConfig({ ...config, pdf_style: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-wimpy-blue focus:ring-wimpy-blue"
                  >
                    <option value="handwritten">Handwritten Style</option>
                    <option value="typed">Typed Style</option>
                  </select>
                </div>

                {/* Temperature */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Creativity Level: {config.temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.temperature}
                    onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>More Focused</span>
                    <span>More Creative</span>
                  </div>
                </div>

                {/* Combine Content */}
                <div className="md:col-span-2">
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={config.combine_by_group}
                      onChange={(e) => setConfig({ ...config, combine_by_group: e.target.checked })}
                      className="w-4 h-4 text-wimpy-blue border-gray-300 rounded focus:ring-wimpy-blue"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Combine all URLs into one epic story
                    </span>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="text-center">
            <button
              type="submit"
              disabled={submitJobMutation.isPending}
              className={`btn-primary text-lg px-8 py-4 ${
                submitJobMutation.isPending 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'hover:scale-105 transform transition-all duration-200'
              }`}
            >
              {submitJobMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white inline-block mr-2"></div>
                  Creating Your Story...
                </>
              ) : (
                <>
                  <Wand2 className="h-6 w-6 inline-block mr-2" />
                  Transform Into Wimpy Kid Magic! ✨
                </>
              )}
            </button>
            
            {submitJobMutation.isPending && (
              <p className="text-sm text-gray-600 mt-2">
                This might take a few minutes while our AI does its magic... 🎭
              </p>
            )}
          </div>
        </form>
      </div>

      {/* Info Section */}
      <div className="max-w-4xl mx-auto">
        <div className="bg-blue-50 border-l-4 border-wimpy-blue p-6 rounded-lg">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-6 w-6 text-wimpy-blue flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                How it works:
              </h3>
              <ol className="text-blue-800 space-y-1 text-sm">
                <li>1. 📖 We download and read your website content</li>
                <li>2. 🤖 Our AI transforms it into Greg Heffley's voice</li>
                <li>3. 📚 We create a beautiful PDF that looks like a real diary</li>
                <li>4. 📥 You download your personalized Wimpy Kid story!</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;