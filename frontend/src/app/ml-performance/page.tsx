'use client';

import { useState, useEffect } from 'react';
import { useML } from '../../hooks/useML';
import { EvaluationRequest } from '../../services/mlService';

export default function MLPerformanceDashboard() {
  const { models, loading, error, evaluateModel, deployModel } = useML();
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [testData, setTestData] = useState('');

  const handleEvaluate = async () => {
    if (!selectedModel || !testData) return;

    setEvaluating(true);
    try {
      const testSamples = JSON.parse(testData);
      const request: EvaluationRequest = { test_data: testSamples };
      const result = await evaluateModel(selectedModel, request);
      setEvaluationResult(result);
    } catch (err: any) {
      alert(err.message || 'Evaluation failed');
    } finally {
      setEvaluating(false);
    }
  };

  const handleDeploy = async (modelId: string) => {
    try {
      await deployModel(modelId);
      alert('Model deployed successfully');
    } catch (err: any) {
      alert(err.message || 'Deployment failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-800 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">ML Performance Dashboard</h1>

        {error && (
          <div className="bg-red-100 dark:bg-red-900/40 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Models List */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">ML Models</h2>
            {loading ? (
              <div>Loading...</div>
            ) : models.length === 0 ? (
              <div className="text-gray-500 dark:text-gray-400">No models found</div>
            ) : (
              <div className="space-y-4">
                {models.map((model) => (
                  <div
                    key={model.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedModel === model.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30' : 'border-gray-200 dark:border-gray-700'
                    }`}
                    onClick={() => setSelectedModel(model.id)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">{model.name}</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{model.provider} - {model.model_name}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Type: {model.model_type}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {model.is_active && (
                          <span className="px-2 py-1 text-xs font-medium text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/40 rounded">
                            Active
                          </span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeploy(model.id);
                          }}
                          className="px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/40 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
                        >
                          Deploy
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                      Created: {new Date(model.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Evaluation Panel */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Model Evaluation</h2>
            
            {!selectedModel ? (
              <div className="text-gray-500 dark:text-gray-400">Select a model to evaluate</div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                    Test Data (JSON array)
                  </label>
                  <textarea
                    value={testData}
                    onChange={(e) => setTestData(e.target.value)}
                    placeholder='[{"text": "sample text", "intent": "sample_intent"}]'
                    rows={10}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 font-mono text-sm"
                  />
                </div>
                <button
                  onClick={handleEvaluate}
                  disabled={evaluating}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {evaluating ? 'Evaluating...' : 'Evaluate Model'}
                </button>

                {evaluationResult && (
                  <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Evaluation Results</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Accuracy</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {(evaluationResult.accuracy * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Precision</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {(evaluationResult.precision * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Recall</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {(evaluationResult.recall * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">F1 Score</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {(evaluationResult.f1_score * 100).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
                      Test samples: {evaluationResult.test_samples}
                    </p>
                    {evaluationResult.classification_report && (
                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm font-medium text-blue-700 dark:text-blue-300">
                          Classification Report
                        </summary>
                        <pre className="mt-2 text-xs bg-white dark:bg-gray-800 p-2 rounded border overflow-auto">
                          {evaluationResult.classification_report}
                        </pre>
                      </details>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
