import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Sparkles, Loader2, File as FileIcon } from 'lucide-react';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export function Home() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'text' | 'pdf'>('text');
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Handle file selection from click
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
      } else {
        alert('Please upload a valid PDF file.');
      }
    }
  };

  // Handle file drag and drop
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
      } else {
        alert('Please drop a valid PDF file.');
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  // The generation logic that routes to the Preview Page in LOWERCASE
  const handleGenerate = async () => {
    setIsLoading(true);
    
    try {
      // CASE 1: TEXT INPUT
      if (activeTab === 'text') {
        if (!inputText.trim()) {
          alert("Please enter some text.");
          setIsLoading(false);
          return;
        }
        
        // Convert input text to lowercase right here
        const lowerCaseText = inputText.toLowerCase();
        const wordCount = lowerCaseText.split(/\s+/).filter(w => w.length > 0).length;
        
        // Go directly to preview with lowercase text
        navigate('/preview', { state: { text: lowerCaseText, wordCount: wordCount } });

      // CASE 2: FILE UPLOAD (PDF)
      } else {
        if (!selectedFile) {
          alert("Please select a PDF file.");
          setIsLoading(false);
          return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        // Fetch ONLY the text from the endpoint
        const response = await fetch(`${API_BASE_URL}/extract-pdf`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to extract text from PDF");
        }

        const result = await response.json();
        
        // Convert the backend PDF text to lowercase right here
        const lowerCasePdfText = result.text.toLowerCase();
        
        // Go to preview page with the lowercase text
        navigate('/preview', { state: { text: lowerCasePdfText, wordCount: result.wordCount } });
      }

    } catch (error) {
      console.error(error);
      alert("Failed to connect to the backend. Is your Python server running?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Header Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-blue-900 mb-4">
          Transform Lectures into <span className="text-blue-600">Smart Notes</span>
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload your PDF materials or paste your lecture text below. Our AI will extract the text, let you review it, and generate structured study guides.
        </p>
      </div>

      {/* Main Input Card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        
        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('text')}
            className={`flex-1 py-4 text-center font-semibold transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'text' 
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' 
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <FileText className="w-5 h-5" />
            Paste Text
          </button>
          <button
            onClick={() => setActiveTab('pdf')}
            className={`flex-1 py-4 text-center font-semibold transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'pdf' 
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' 
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Upload className="w-5 h-5" />
            Upload PDF
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-8">
          {activeTab === 'text' ? (
            <div>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Paste your lecture notes or text here..."
                className="w-full h-64 p-4 text-gray-700 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-100 focus:border-blue-500 outline-none resize-none transition-all leading-relaxed"
              />
            </div>
          ) : (
            <div 
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:bg-gray-50 transition-colors flex flex-col items-center justify-center min-h-[16rem]"
            >
              {!selectedFile ? (
                <>
                  <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
                    <Upload className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">Drag & Drop your PDF here</h3>
                  <p className="text-gray-500 mb-6">or click the button below to browse</p>
                  <label className="cursor-pointer bg-white border border-gray-300 text-gray-700 font-semibold py-2 px-6 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
                    Browse Files
                    <input 
                      type="file" 
                      accept="application/pdf" 
                      className="hidden" 
                      onChange={handleFileChange} 
                    />
                  </label>
                </>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
                    <FileIcon className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-1">{selectedFile.name}</h3>
                  <p className="text-sm text-gray-500 mb-6">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <button 
                    onClick={() => setSelectedFile(null)}
                    className="text-red-500 hover:text-red-700 text-sm font-medium transition-colors"
                  >
                    Remove File
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Footer */}
        <div className="bg-gray-50 p-6 border-t border-gray-200 flex justify-end">
          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl shadow-md transition-all disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Sparkles className="w-5 h-5" />
            )}
            {isLoading ? 'Extracting Text...' : 'Extract & Preview'}
          </button>
        </div>
      </div>
    </div>
  );
}