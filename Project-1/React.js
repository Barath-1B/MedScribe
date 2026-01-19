// src/App.jsx
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Menu, Bell } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white/10 backdrop-blur-lg border-r border-white/20 p-6 hidden md:block">
        <h1 className="text-2xl font-bold mb-8">Dashboard</h1>
        <nav className="flex flex-col gap-4">
          <a href="#" className="hover:text-blue-400">Overview</a>
          <a href="#" className="hover:text-blue-400">Analytics</a>
          <a href="#" className="hover:text-blue-400">Reports</a>
          <a href="#" className="hover:text-blue-400">Settings</a>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex justify-between items-center p-4 border-b border-white/20 bg-white/5 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu />
            </Button>
            <h2 className="text-xl font-semibold">Welcome Back, [User]</h2>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon"><Bell /></Button>
            <div className="w-10 h-10 rounded-full bg-white/20"></div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="flex-1 p-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Card 1 */}
          <Card className="bg-white/10 border-white/20 backdrop-blur-md hover:scale-[1.02] transition-all">
            <CardHeader>
              <CardTitle>Statistic 1</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">--</p>
              <p className="text-sm text-gray-400">Description</p>
            </CardContent>
          </Card>

          {/* Card 2 */}
          <Card className="bg-white/10 border-white/20 backdrop-blur-md hover:scale-[1.02] transition-all">
            <CardHeader>
              <CardTitle>Statistic 2</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">--</p>
              <p className="text-sm text-gray-400">Description</p>
            </CardContent>
          </Card>

          {/* Card 3 */}
          <Card className="bg-white/10 border-white/20 backdrop-blur-md hover:scale-[1.02] transition-all">
            <CardHeader>
              <CardTitle>Statistic 3</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">--</p>
              <p className="text-sm text-gray-400">Description</p>
            </CardContent>
          </Card>

          {/* Chart Placeholder */}
          <Card className="col-span-full bg-white/10 border-white/20 backdrop-blur-md h-72 flex items-center justify-center">
            <p className="text-gray-400">[Chart Placeholder]</p>
          </Card>

          {/* Table Placeholder */}
          <Card className="col-span-full bg-white/10 border-white/20 backdrop-blur-md h-80 flex items-center justify-center">
            <p className="text-gray-400">[Data Table Placeholder]</p>
          </Card>
        </main>
      </div>
    </div>
  );
}
