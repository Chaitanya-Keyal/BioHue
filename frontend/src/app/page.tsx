"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { Camera, Loader2 } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { ImageData } from "@/types";

export default function HomePage() {
  const [image, setImage] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState<ImageData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    if (user === undefined) return;
    if (!user) {
      router.push("/auth");
    }
    setCheckingAuth(false);
  }, [user, router]);

  const shouldRender = useMemo(() => {
    return !checkingAuth && user;
  }, [checkingAuth, user]);

  if (!shouldRender) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin w-10 h-10 text-gray-600 dark:text-gray-300" />
      </div>
    );
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImage(file);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!image) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("image", image as unknown as Blob);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/images`,
        {
          method: "POST",
          body: formData,
          credentials: "include",
        },
      );

      const data = await response.json();
      if (!response.ok) {
        if (response.status === 409 && data.image_id) {
          router.push(`/history#image-${data.image_id}`);
          setTimeout(() => {
            const alertBox = document.createElement("div");
            alertBox.textContent = "Image already exists!";
            alertBox.className =
              "fixed top-5 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded shadow-lg opacity-0 transition-opacity duration-500 ease-in-out z-50";
            document.body.appendChild(alertBox);

            requestAnimationFrame(() => {
              alertBox.classList.remove("opacity-0");
              alertBox.classList.add("opacity-100");
            });

            setTimeout(() => {
              alertBox.classList.remove("opacity-100");
              alertBox.classList.add("opacity-0");

              setTimeout(() => {
                document.body.removeChild(alertBox);
              }, 500);
            }, 2000);
          }, 500);
        } else {
          throw new Error(data.detail || "Error uploading image");
        }
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors p-4">
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

          {result &&
            result.processed_image &&
            result.processed_image_area &&
            result.analysis && (
              <div className="flex flex-col md:flex-row items-center mt-4 space-y-4 md:space-y-0 md:space-x-4">
                <div className="mt-4 md:mt-0">
                  <Image
                    src={`data:image/png;base64,${result.processed_image.base64}`}
                    alt="Processed"
                    width={result.processed_image_area * 5}
                    height={result.processed_image_area * 5}
                    className="max-w-full object-contain rounded-lg"
                  />
                </div>
                <div className="text-center md:text-left">
                  <p className="font-bold text-lg text-gray-900 dark:text-white">
                    Result: {result.analysis.result}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    RG Ratio: {result.analysis.value.toFixed(2)}
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
