import { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft, Sparkles, FileText, Loader2, Clock, Hash } from 'lucide-react';

export function Preview() {
  const location = useLocation();
  const navigate = useNavigate();
  const rawText = location.state?.text || '';

  const [text, setText] = useState(rawText);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  // Methodology: 4-step sequence (lower case, filter symbols, split by space)
  const tokens = useMemo(() => {
    return text
      .toLowerCase() // 1. Case Normalization
      .replace(/['\-,]/g, '') // 2. Character Filtering (', -, ,)
      .split(/\s+/) // 3. String Segmentation
      .filter((t: string) => t.length > 0); // 4. Clean empty strings
  }, [text]);

  useEffect(() => {
    if (!rawText) navigate('/');
  }, [rawText, navigate]);

  const handleGenerateNotes = async () => {
    setIsProcessing(true);
    setProgress(15);
    setSecondsElapsed(0);

    try {
      const progressInterval = setInterval(() => {
        setProgress((prev) => (prev < 85 ? prev + 10 : prev));
      }, 500);

      const timerInterval = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);

      const response = await fetch('http://127.0.0.1:8000/generate-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text }),
      });

      clearInterval(progressInterval);
      clearInterval(timerInterval);
      setProgress(100);

      if (!response.ok) throw new Error("Failed to generate");
      
      const result = await response.json();
      
      setTimeout(() => {
        navigate('/result', { state: { noteData: result } });
      }, 500);

    } catch (error) {
      console.error(error);
      alert("Error generating notes. Make sure backend is running.");
      setIsProcessing(false);
      setProgress(0);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/" className="flex items-center text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors">
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Upload
        </Link>
      </div>

      {/* Two-Column Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: Review Extracted Text */}
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 h-fit">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-blue-900">Review Extracted Text</h1>
              <p className="text-gray-500 text-sm">Verify the raw content before processing.</p>
            </div>
          </div>

          <textarea 
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={isProcessing}
            className="w-full h-96 p-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-100 outline-none resize-none text-gray-700 bg-gray-50 leading-relaxed text-sm"
          />

          <div className="flex justify-between items-center mt-4">
            <div className="text-xs font-semibold text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              {text.split(/\s+/).filter((w: string) => w.length > 0).length} Words
            </div>

            <button 
              onClick={handleGenerateNotes}
              disabled={isProcessing}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg shadow transition-all disabled:opacity-70 text-sm"
            >
              {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
              {isProcessing ? "Processing..." : "Generate Notes"}
            </button>
          </div>
        </div>

        {/* Right Column: Tokenization Visualization */}
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Hash className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-indigo-900">Token Visualization</h1>
              <p className="text-gray-500 text-sm">Live preview of filtered NLP tokens.</p>
            </div>
          </div>

          {/* Token Display Area */}
          <div className="flex-grow p-4 bg-gray-50 border border-gray-200 rounded-lg overflow-y-auto h-96">
            <div className="flex flex-wrap gap-2">
              {tokens.length > 0 ? (
                tokens.map((token: string, index: number) => (
                  <span 
                    key={index} 
                    className="px-2 py-1 bg-white text-indigo-600 border border-indigo-100 rounded md text-xs font-medium shadow-sm"
                  >
                    {token}
                  </span>
                ))
              ) : (
                <span className="text-gray-400 italic text-sm">Waiting for input...</span>
              )}
            </div>
          </div>

          <div className="mt-4 flex justify-between items-center text-xs font-semibold text-indigo-500">
             <span>Methodology: Case Normalization + Filter</span>
             <span className="bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
               {tokens.length} Tokens
             </span>
          </div>
        </div>
      </div>

      {/* Progress Bar (Full Width Below) */}
      {isProcessing && (
        <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-100 max-w-4xl mx-auto w-full">
          <div className="flex justify-between items-end mb-3">
            <div className="flex flex-col">
              <span className="text-sm font-bold text-blue-900">Fine-tuning BART-Large-CNN...</span>
              <span className="text-xs text-blue-600 flex items-center gap-1 mt-1">
                <Clock className="w-3 h-3" />
                Elapsed: {secondsElapsed}s
              </span>
            </div>
            <span className="text-sm font-bold text-blue-600">{progress}%</span>
          </div>
          <div className="w-full bg-blue-200/50 rounded-full h-3 overflow-hidden">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}