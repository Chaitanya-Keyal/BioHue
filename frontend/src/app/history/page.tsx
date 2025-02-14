"use client";

import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent } from "@/components/ui/card";
import { ImageData } from "@/types";
import { useToast } from "@/components/hooks/use-toast";

export default function Gallery() {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const { user } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  const [hash, setHash] = useState<string | null>(null);
  useEffect(() => {
    if (typeof window !== "undefined") {
      setHash(window.location.hash);
      window.addEventListener("hashchange", () => {
        setHash(window.location.hash);
      });
    }
  }, []);

  useEffect(() => {
    if (user === undefined) return;
    if (!user) {
      router.push("/auth");
      return;
    }
    setCheckingAuth(false);
    const fetchImages = async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/images`,
          {
            method: "GET",
            credentials: "include",
          },
        );
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Error fetching images");
        }
        const data = await res.json();
        setImages(data);
      } catch (err: any) {
        toast({
          title: "Error",
          description: err.message,
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchImages();
  }, [user, router, toast]);

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
  return (
    <div className="min-h-screen p-4 bg-gray-100 dark:bg-gray-900">
      <h1 className="text-3xl font-bold mb-6 text-center text-gray-900 dark:text-white">
        Your Uploaded Images
      </h1>
      {loading && (
        <div className="flex justify-center">
          <Loader2 className="animate-spin" />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ">
        {images.map((img) => (
          <Card
            key={img.id}
            id={`image-${img.id}`}
            className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md ${
              hash === `#image-${img.id}` ? "animate-flash" : ""
            }`}
          >
            <CardContent className="flex flex-col space-y-4 items-center">
              {img.original_image?.base64 ? (
                <Image
                  src={`data:image/png;base64,${img.original_image.base64}`}
                  alt="Uploaded"
                  width={500}
                  height={500}
                  className="max-w-full max-h-48 object-contain rounded-lg mb-4"
                />
              ) : (
                <p className="text-gray-500">No original image available.</p>
              )}

              <div className="flex flex-col md:flex-row md:space-x-6 items-center">
                {img.processed_image?.base64 ? (
                  <Image
                    src={`data:image/png;base64,${img.processed_image.base64}`}
                    alt="Processed"
                    width={
                      img.processed_image_area
                        ? img.processed_image_area * 5
                        : 250
                    }
                    height={
                      img.processed_image_area
                        ? img.processed_image_area * 5
                        : 250
                    }
                    className="object-contain rounded-lg mb-4 md:mb-0"
                  />
                ) : (
                  <p className="text-gray-500">No processed image available.</p>
                )}

                {img.analysis && (
                  <div className="text-center md:text-left">
                    <p className="font-bold text-lg text-gray-900 dark:text-white">
                      Result: {img.analysis.result}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      RG Ratio: {img.analysis.value.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      Substrate: {img.analysis.substrate}
                    </p>
                  </div>
                )}
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400">
                Uploaded: {new Date(img.created_at).toLocaleString()}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
