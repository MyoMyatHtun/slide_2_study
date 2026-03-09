import { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft, Sparkles, FileText, Loader2, Clock } from 'lucide-react';

export function Preview() {
  const location = useLocation();
  const navigate = useNavigate();
  const rawText = location.state?.text || '';
  const initialWordCount = location.state?.wordCount || 0;

  const [text, setText] = useState(rawText);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [secondsElapsed, setSecondsElapsed] = useState(0); 

  // Redirect back home if accessed without data
  useEffect(() => {
    if (!rawText) navigate('/');
  }, [rawText, navigate]);

  const handleGenerateNotes = async () => {
    setIsProcessing(true);
    setProgress(15);
    setSecondsElapsed(0); 

    try {
      // Fake progress bar logic (moves up to 85%)
      const progressInterval = setInterval(() => {
        setProgress((prev) => (prev < 85 ? prev + 10 : prev));
      }, 500);

      // Timer logic (counts up every 1 second)
      const timerInterval = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);

      // Send the text to the backend to generate the notes
      const response = await fetch('http://127.0.0.1:8000/generate-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text }),
      });

      // Stop the intervals when the backend responds
      clearInterval(progressInterval);
      clearInterval(timerInterval);
      setProgress(100); 

      if (!response.ok) throw new Error("Failed to generate");
      
      const result = await response.json();
      
      // Give the progress bar half a second to show 100% before navigating
      setTimeout(() => {
        navigate('/result', { state: { noteData: result } });
      }, 500);

    } catch (error) {
      console.error(error);
      alert("Error generating notes. Make sure backend is running.");
      setIsProcessing(false);
      setProgress(0);
      setSecondsElapsed(0);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/" className="flex items-center text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors">
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Upload
        </Link>
      </div>

      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-blue-900">Review Extracted Text</h1>
            <p className="text-gray-500 text-sm">Verify the text before our AI generates your study notes.</p>
          </div>
        </div>

        {/* Text Area */}
        <textarea 
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isProcessing}
          className="w-full h-80 p-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-100 outline-none resize-none text-gray-700 bg-gray-50 leading-relaxed"
        />

        {/* Status Bar: Word Count & Action */}
        <div className="flex justify-between items-center mt-4">
          <div className="text-sm font-semibold text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {text.split(/\s+/).filter((w: string) => w.length > 0).length} Words
          </div>

          <button 
            onClick={handleGenerateNotes}
            disabled={isProcessing}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg shadow transition-all disabled:opacity-70"
          >
            {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
            {isProcessing ? "Processing AI..." : "Generate Notes"}
          </button>
        </div>

        {/* Progress Bar & Timer */}
        {isProcessing && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
            <div className="flex justify-between items-end mb-2">
              <div className="flex flex-col">
                <span className="text-sm font-bold text-blue-900">Analyzing content...</span>
                <span className="text-xs text-blue-600 flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3" />
                  Elapsed time: {secondsElapsed} seconds
                </span>
              </div>
              <span className="text-sm font-bold text-blue-600">{progress}%</span>
            </div>
            
            {/* The Bar */}
            <div className="w-full bg-blue-200/50 rounded-full h-2.5 overflow-hidden">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}