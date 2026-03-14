import { Download, ChevronLeft, BookOpen } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

export function Result() {
  const location = useLocation();
  const noteData = location.state?.noteData;

  // If no data reached this page, show an error message
  if (!noteData) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          No data received
        </h2>
        <Link to="/" className="text-blue-600 hover:underline">
          Return to Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Top Navigation */}
      <div className="flex justify-between items-center mb-8">
        <Link
          to="/"
          className="flex items-center text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Upload
        </Link>
        <button className="flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg shadow-sm transition-colors">
          <Download className="w-4 h-4" />
          Export PDF
        </button>
      </div>

      {/* Main Content Card */}
      <div className="bg-white p-8 md:p-12 rounded-2xl shadow-sm border border-gray-200">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-xs font-bold uppercase tracking-wider mb-6">
          <BookOpen className="w-3 h-3" /> Study Note
        </div>
        <span className="text-sm text-gray-400 font-medium">
          {noteData.wordCount} words
        </span>
        <h1 className="text-3xl font-bold text-gray-900 mb-6 tracking-tight">
          AI Generated Summary
        </h1>

        <div className="prose prose-blue max-w-none">
          {/* NOTICE: noteData.summary matches the key from your Python backend */}
          <p className="text-gray-700 leading-relaxed text-lg whitespace-pre-wrap italic">
            {noteData.summary || "No summary text generated."}
          </p>
        </div>
      </div>

      {/* Optional: Add a subtle footer or credits here */}
      <p className="text-center text-gray-400 text-sm mt-8">
        Processed by Slide 2 Study AI Engine
      </p>
    </div>
  );
}
