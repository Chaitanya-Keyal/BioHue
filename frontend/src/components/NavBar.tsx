"use client";

import DarkModeToggle from "@/components/DarkModeToggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="backdrop-blur-md bg-white/75 dark:bg-gray-900/75 border-b border-gray-300 dark:border-gray-700 fixed top-0 w-full z-50 shadow-md">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <Link
            href="/"
            className="text-xl font-bold text-gray-800 dark:text-gray-100 hover:text-gray-600 transition-colors"
          >
            Home
          </Link>
          {user && (
            <Link
              href="/history"
              className="text-xl text-gray-800 dark:text-gray-100 hover:text-gray-600 transition-colors"
            >
              History
            </Link>
          )}
        </div>
        <div className="flex items-center space-x-6">
          <DarkModeToggle />
          {user ? (
            <Button
              onClick={logout}
              variant="outline"
              className="text-base text-gray-800 dark:text-gray-100 border-gray-800 dark:border-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              Logout
            </Button>
          ) : (
            <Button
              asChild
              variant="outline"
              className="text-base text-gray-800 dark:text-gray-100 border-gray-800 dark:border-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <Link href="/auth">Login</Link>
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
}
