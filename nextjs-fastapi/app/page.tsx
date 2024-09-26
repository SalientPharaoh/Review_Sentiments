'use client'

import React, { useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { FiMoon, FiSun, FiUploadCloud } from 'react-icons/fi'
import { useTheme } from 'next-themes'
import { Button } from "@/components/ui/button"
import { Navbar, NavbarBrand, NavbarItems } from "@/components/ui/navbar"

type SentimentType = 'positive' | 'negative' | 'neutral'

interface Results {
  positive: number
  negative: number
  neutral: number
  top_positive: string[]
  top_negative: string[]
  top_neutral: string[]
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [textInput, setTextInput] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [results, setResults] = useState<Results | null>(null)
  const [showLoader, setShowLoader] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    if (isAnalyzing) {
      setShowLoader(true)
    } else {
      const timer = setTimeout(() => setShowLoader(false), 300)
      return () => clearTimeout(timer)
    }
  }, [isAnalyzing])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    onDrop: (acceptedFiles) => {
      setFile(acceptedFiles[0])
    },
    multiple: false
  })

  const analyzeData = async () => {
    setIsAnalyzing(true)
    setError(null)

    try {
      let response;

      if (file) {
        const formData = new FormData()
        formData.append('file', file)

        response = await fetch('/api/py/analyze_file', {
          method: 'POST',
          body: formData,
        })
      } else if (textInput.trim()) {
        const reviews = textInput.split('\n').filter(r => r.trim())

        response = await fetch('/api/py/analyze_batch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ reviews }),
        })
      } else {
        throw new Error('Please upload a file or enter reviews')
      }

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`)
      }

      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const chartData = results ? [
    { name: 'Positive', value: results.positive },
    { name: 'Negative', value: results.negative },
    { name: 'Neutral', value: results.neutral }
  ] : []

  if(isAnalyzing) {
    return (
      <div className="flex items-center bg-white dark:bg-black justify-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    )
  }else{
  return (
    <div className='h-screen dark:bg-black bg-white'>
      <div className={`bg-gradient-to-b ${theme === 'dark' ? 'from-gray-900 to-gray-800' : 'from-gray-100 to-white'} transition-colors duration-200`}>
        <Navbar className="px-4 sm:px-6 lg:px-8">
          <NavbarBrand>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
              Sentiment Analysis
            </span>
          </NavbarBrand>
          <NavbarItems>
            <Button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <FiSun className="h-5 w-5 text-white" /> : <FiMoon className="h-5 w-5 text-black" />}
            </Button>
          </NavbarItems>
        </Navbar>

        <main className="py-12 px-4 sm:px-6 lg:px-8 bg-white dark:bg-black">
          <div className="max-w-7xl mx-auto bg-white dark:bg-black">
            <div className={`bg-white dark:bg-black shadow-xl rounded-lg overflow-hidden transition-colors duration-200`}>
              <div className="p-6">
                <h2 className="text-2xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-500">Upload Reviews</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div
                      {...getRootProps()}
                      className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md cursor-pointer transition-colors duration-200 ${isDragActive ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900' : 'border-gray-300 dark:border-gray-700'
                        }`}
                    >
                      <div className="space-y-1 text-center">
                        <FiUploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                        <div className="flex text-sm text-gray-600 dark:text-gray-400">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
                          >
                            <span>{file ? file.name : 'Upload a file'}</span>
                            <input {...getInputProps()} />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">CSV or XLSX up to 10MB</p>
                      </div>
                    </div>
                  </div>
                  <div className='flex space-x-4'>
                    <label htmlFor="text-input" className="flex text-lg font-bold text-gray-700 dark:text-gray-300 justify-center items-center">
                      Or
                    </label>
                    <textarea
                      id="text-input"
                      rows={4}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-600 dark:text-white pt-2 pl-2 text-black"
                      placeholder="Enter your reviews here (one per line)"
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                    ></textarea>
                  </div>
                </div>
                <div className='flex justify-center items-center'>
                  <div className=' mt-6 border rounded-2xl w-1/2 bg-gray-700 dark:bg-gray-800'>
                    <Button
                      onClick={analyzeData}
                      disabled={isAnalyzing}
                      className="w-full h-ful; font-bold gradient-button rounded-2xl"
                    >
                      {isAnalyzing ? 'Analyzing...' : 'Analyze Sentiment'}
                    </Button>
                  </div>
                </div>
              </div>

              {error && (
                <div className="p-4 bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 rounded">
                  {error}
                </div>
              )}

              <div className={`absolute inset-0 flex items-center justify-center dark:bg-black bg-opacity-50 transition-opacity duration-300 ${showLoader ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
                <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-indigo-500"></div>
              </div>

              {results && (
                <div className="p-6 m-6 bg-gray-50 dark:bg-black">
                  <h2 className="text-2xl font-semibold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-blue-500">Results</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className='text-black'>
                      <h3 className="text-lg font-medium mb-4 bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 to-orange-500">Sentiment Distribution</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="value" fill="url(#colorGradient)" />
                          <defs>
                            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#4F46E5" stopOpacity={0.8} />
                              <stop offset="100%" stopColor="#818CF8" stopOpacity={0.8} />
                            </linearGradient>
                          </defs>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className='flex flex-col '>
                      <h3 className="text-lg font-medium mb-4 bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-purple-500">Top Comments</h3>
                      <div className="space-y-4">
                        {(['positive', 'negative', 'neutral'] as const).map((sentiment) => (
                          <div key={sentiment} className="bg-white dark:bg-gray-900 border rounded-2xl shadow overflow-hidden sm:rounded-lg">
                            <div className="px-4 py-5 sm:px-6">
                              <h3 className="text-lg leading-6 font-medium capitalize bg-clip-text text-transparent bg-gradient-to-r from-cyan-500 to-blue-500">{sentiment}</h3>
                            </div>
                            <div className="border-t border-gray-200 dark:border-gray-700">
                              <dl>
                                {results[`top_${sentiment}`].map((comment, index) => (
                                  <div key={index} className="bg-gray-50 dark:bg-black px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Comment {index + 1}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 sm:mt-0 sm:col-span-2">{comment}</dd>
                                  </div>
                                ))}
                              </dl>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
}