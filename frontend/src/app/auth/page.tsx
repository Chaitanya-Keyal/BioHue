"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Eye, EyeOff } from "lucide-react";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const { user, login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) {
      router.push("/");
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    const endpoint = isLogin
      ? `${backendUrl}/api/users/login`
      : `${backendUrl}/api/users/register`;

    const request = async () => {
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
          credentials: "include",
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail);
        }

        login({ username });
        router.push("/");
      } catch (err: any) {
        if (err.message === "Failed to fetch") {
          console.warn("Retrying login due to fetch failure...");
          return request(); // Retry once
        }
        setError(err.message);
      }
    };

    request();
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md p-8 shadow-lg bg-white dark:bg-gray-800 rounded-xl transform transition-transform hover:scale-105">
        <CardContent>
          <h2 className="text-3xl font-bold mb-6 text-center text-gray-900 dark:text-gray-100">
            {isLogin ? "Login" : "Register"}
          </h2>
          {error && <p className="text-red-500 mb-4 text-center">{error}</p>}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block mb-2 text-gray-700 dark:text-gray-300">
                Username:
              </label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block mb-2 text-gray-700 dark:text-gray-300">
                Password:
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 dark:text-gray-300"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff /> : <Eye />}
                </button>
              </div>
            </div>
            <Button
              type="submit"
              className={`w-full py-3 ${isLogin ? "bg-blue-600" : "bg-green-600"} text-white rounded-lg hover:${isLogin ? "bg-blue-700" : "bg-green-700"}`}
            >
              {isLogin ? "Login" : "Register"}
            </Button>
          </form>
          <div className="mt-6 text-center text-gray-700 dark:text-gray-300">
            {isLogin ? (
              <>
                <p>New user?</p>
                <Button
                  variant="link"
                  onClick={() => setIsLogin(false)}
                  className="text-blue-600 dark:text-blue-400"
                >
                  Sign up here
                </Button>
              </>
            ) : (
              <>
                <p>Already have an account?</p>
                <Button
                  variant="link"
                  onClick={() => setIsLogin(true)}
                  className="text-blue-600 dark:text-blue-400"
                >
                  Login here
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
