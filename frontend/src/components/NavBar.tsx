"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import DarkModeToggle from "@/components/DarkModeToggle";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-gray-200 dark:bg-gray-800 p-4 flex justify-between items-center fixed top-0 w-full z-50">
      <div className="flex items-center space-x-4">
        <Link href="/" className="text-lg font-bold">
          Home
        </Link>
        {user && (
          <Link href="/history" className="text-lg">
            History
          </Link>
        )}
      </div>
      <div className="flex items-center space-x-4">
        <DarkModeToggle />
        {user ? (
          <Button onClick={logout} variant="outline">
            Logout
          </Button>
        ) : (
          <Link href="/auth" className="text-lg">
            Login/Register
          </Link>
        )}
      </div>
    </nav>
  );
}
