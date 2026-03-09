import { Download, ChevronLeft, BookOpen, Lightbulb, List } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Result() {
  // DUMMY DATA: 'summary' is now an array to support bullet points
  const noteData = {
    
    summaryPoints: [
      "Neural networks are a subset of machine learning and are at the heart of deep learning algorithms.",
      "Their name and structure are inspired by the human brain, mimicking the way that biological neurons signal to one another."
    ],
    keyConcepts: [
      "Artificial Neurons",
      "Activation Functions",
      "Backpropagation",
      "Gradient Descent",
      "Hidden Layers"
    ],
    definitions: [
      { term: "Perceptron", definition: "The simplest type of feedforward neural network, consisting of a single layer of output nodes." },
      { term: "Epoch", definition: "One complete pass of the training dataset through the algorithm." },
      { term: "Learning Rate", definition: "A tuning parameter in an optimization algorithm that determines the step size at each iteration." }
    ]
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      
      {/* Top Controls */}
      <div className="flex justify-between items-center mb-8">
        <Link to="/" className="flex items-center text-sm font-medium text-gray-500 hover:text-brand-blue-600 transition-colors">
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Upload
        </Link>
        <button className="flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors">
          <Download className="w-4 h-4" />
          Export PDF
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN: Combined Card (Summary + Definitions) */}
        <div className="lg:col-span-2 bg-white p-8 rounded-xl shadow-sm border border-gray-200 h-fit">
          
          {/* Part 1: Title & Summary (Bullet Points) */}
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-blue-50 text-brand-blue-600 text-xs font-bold uppercase tracking-wider mb-4">
              <BookOpen className="w-3 h-3" /> Study Note
            </div>
          
            
            {/* Summary List */}
            <ul className="list-disc list-outside ml-5 space-y-2">
              {noteData.summaryPoints.map((point, idx) => (
                <li key={idx} className="text-gray-600 leading-relaxed text-lg">
                  {point}
                </li>
              ))}
            </ul>
          </div>

          

          {/* Part 2: Definitions (Bullet Points) */}
          <div>
        
            
            {/* Definitions List */}
            <ul className="list-disc list-outside ml-5 space-y-4">
              {noteData.definitions.map((item, idx) => (
                <li key={idx} className="text-black-600 leading-relaxed">
                  <span className="font-bold text-brand-black-900">{item.term}</span>
                  <span className="mx-1">-</span>
                  {item.definition}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* RIGHT COLUMN: Key Concepts (Blue Box - Unchanged) */}
        <div className="space-y-6">
          <div className="bg-white-900 text-black p-6 rounded-xl shadow-lg sticky top-24">
            <h2 className="flex items-center gap-2 text-lg font-bold mb-4">
              <Lightbulb className="w-5 h-5 text-black-400" />
              Key Concepts
            </h2>
            <ul className="space-y-3">
              {noteData.keyConcepts.map((concept, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="min-w-[6px] h-[6px] rounded-full bg-white-400 mt-2" />
                  <span className="text-black-100 font-medium">{concept}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}