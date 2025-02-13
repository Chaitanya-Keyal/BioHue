"use client";

import { useState, useEffect, ChangeEvent } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Moon, Sun, Camera } from "lucide-react";

interface ClassificationResult {
  result: string;
  rg_ratio: number;
  circle: string;
  area: number;
}

export default function ImageClassifier() {
  const [darkMode, setDarkMode] = useState(false);

  const [image, setImage] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDarkMode(true);
    document.documentElement.classList.add("dark");
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    document.documentElement.classList.toggle("dark", newDarkMode);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImage(file);
    }
  };

  const handleUpload = async () => {
    if (!image) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("image", image);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/classify`,
        {
          method: "POST",
          body: formData,
        },
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Error classifying image");
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors p-4">
      <Button
        onClick={toggleDarkMode}
        className="absolute top-4 right-4 p-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-full shadow-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-all"
      >
        {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </Button>

      <Card className="w-full max-w-lg p-6 shadow-lg bg-white dark:bg-gray-800 rounded-xl transform transition-transform hover:scale-105">
        <CardContent className="flex flex-col items-center space-y-6">
          <label className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg cursor-pointer hover:bg-blue-500 dark:hover:bg-blue-600 transition-colors">
            <Camera className="w-6 h-6 mr-2" />
            <span className="text-lg">Upload an Image</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
              capture="environment"
            />
          </label>

          {image && (
            <div className="w-full flex justify-center mt-4">
              <Image
                src={URL.createObjectURL(image)}
                alt="Thumbnail"
                width={500}
                height={500}
                className="max-w-full max-h-48 object-contain rounded-lg"
              />
            </div>
          )}

          <Button
            onClick={handleUpload}
            disabled={loading || !image}
            className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors mt-4 text-lg"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Classify"}
          </Button>

          {result && (
            <div className="flex flex-col md:flex-row items-center mt-4 space-y-4 md:space-y-0 md:space-x-4">
              <div className="mt-4 md:mt-0">
                <Image
                  src={`data:image/png;base64,${result.circle}`}
                  alt="Circle"
                  width={(result.area / 100) * 500}
                  height={(result.area / 100) * 500}
                  className="max-w-full object-contain rounded-lg"
                />
              </div>
              <div className="text-center md:text-left">
                <p className="font-bold text-lg text-gray-900 dark:text-white">
                  Result: {result.result}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  RG Ratio: {result.rg_ratio.toFixed(2)}
                </p>
              </div>
            </div>
          )}

          {error && <p className="text-red-500 mt-2">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
