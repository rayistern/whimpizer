import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Clock, 
  Download, 
  Globe, 
  Brain, 
  FileText, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { whimpizerAPI, downloadFile } from '../services/api';

interface JobStatusProps {
  jobId: string;
  onClose?: () => void;
}

const JobStatus: React.FC<JobStatusProps> = ({ jobId, onClose }) => {
  // Fetch job status with polling
  const { data: jobData, isLoading, error, refetch } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => whimpizerAPI.getJobStatus(jobId),
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
  });

  const job = jobData?.data;

  const handleDownload = async () => {
    if (!job || job.status !== 'completed') return;
    
    try {
      const response = await whimpizerAPI.downloadPDF(jobId);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      downloadFile(blob, `whimpizer-${jobId}.pdf`);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download PDF. Please try again.');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-6 w-6 text-gray-500" />;
      case 'downloading':
        return <Globe className="h-6 w-6 text-blue-500 animate-pulse" />;
      case 'processing':
        return <Brain className="h-6 w-6 text-purple-500 animate-pulse" />;
      case 'generating_pdf':
        return <FileText className="h-6 w-6 text-orange-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-500" />;
      case 'cancelled':
        return <AlertTriangle className="h-6 w-6 text-yellow-500" />;
      default:
        return <Clock className="h-6 w-6 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Waiting in line...';
      case 'downloading':
        return 'Downloading your websites 📥';
      case 'processing':
        return 'AI is working its magic 🎭';
      case 'generating_pdf':
        return 'Creating your beautiful PDF 📚';
      case 'completed':
        return 'Your story is ready! 🎉';
      case 'failed':
        return 'Oops! Something went wrong 😞';
      case 'cancelled':
        return 'Job was cancelled';
      default:
        return 'Unknown status';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 border-green-200';
      case 'failed':
        return 'bg-red-100 border-red-200';
      case 'cancelled':
        return 'bg-yellow-100 border-yellow-200';
      default:
        return 'bg-blue-100 border-blue-200';
    }
  };

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-2 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card bg-red-50 border-red-200">
        <div className="flex items-center space-x-3">
          <XCircle className="h-6 w-6 text-red-500" />
          <div>
            <h3 className="text-lg font-semibold text-red-900">
              Failed to Load Job Status
            </h3>
            <p className="text-red-700">
              Unable to fetch status for job {jobId}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-2 btn-secondary text-sm"
            >
              <RefreshCw className="h-4 w-4 inline-block mr-1" />
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="card">
        <p className="text-gray-600">Job not found.</p>
      </div>
    );
  }

  return (
    <div className={`card ${getStatusColor(job.status)}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center space-x-3">
          {getStatusIcon(job.status)}
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Job {jobId.slice(-8)}
            </h2>
            <p className="text-gray-600">
              {getStatusText(job.status)}
            </p>
          </div>
        </div>
        
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span>{job.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-wimpy-blue h-3 rounded-full transition-all duration-500"
            style={{ width: `${job.progress}%` }}
          ></div>
        </div>
      </div>

      {/* Job Details */}
      <div className="space-y-4">
        {/* URLs */}
        <div>
          <h4 className="font-medium text-gray-900 mb-2">
            📝 Processing {job.urls.length} URL{job.urls.length > 1 ? 's' : ''}:
          </h4>
          <ul className="text-sm text-gray-600 space-y-1">
            {job.urls.slice(0, 3).map((url, index) => (
              <li key={index} className="truncate">
                • {url}
              </li>
            ))}
            {job.urls.length > 3 && (
              <li className="text-gray-500">
                ... and {job.urls.length - 3} more
              </li>
            )}
          </ul>
        </div>

        {/* Configuration */}
        <div>
          <h4 className="font-medium text-gray-900 mb-2">⚙️ Settings:</h4>
          <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
            <div>AI: {job.config.ai_provider} ({job.config.ai_model})</div>
            <div>Style: {job.config.pdf_style}</div>
          </div>
        </div>

        {/* Timestamps */}
        <div className="text-xs text-gray-500">
          <div>Created: {new Date(job.created_at).toLocaleString()}</div>
          {job.started_at && (
            <div>Started: {new Date(job.started_at).toLocaleString()}</div>
          )}
          {job.completed_at && (
            <div>Completed: {new Date(job.completed_at).toLocaleString()}</div>
          )}
        </div>

        {/* Error Message */}
        {job.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <h4 className="font-medium text-red-900 mb-1">Error Details:</h4>
            <p className="text-sm text-red-700">{job.error_message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex space-x-3 pt-4">
          {job.status === 'completed' && (
            <button
              onClick={handleDownload}
              className="btn-primary flex items-center space-x-2"
            >
              <Download className="h-5 w-5" />
              <span>Download Your Story! 📖</span>
            </button>
          )}
          
          {['pending', 'downloading', 'processing', 'generating_pdf'].includes(job.status) && (
            <button
              onClick={() => refetch()}
              className="btn-secondary flex items-center space-x-2"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh Status</span>
            </button>
          )}

          {job.status === 'failed' && (
            <button
              onClick={() => window.location.reload()}
              className="btn-secondary"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobStatus;