'use client';

import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import Navbar from '@/components/Navbar';
import StockTicker from '@/components/StockTicker';
import './globals.css';

export default function RootLayout({ children }: { children: ReactNode }) {
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) setDarkMode(saved === 'true');
  }, []);

  const toggleDark = () => {
    setDarkMode((v) => {
      localStorage.setItem('darkMode', String(!v));
      return !v;
    });
  };

  return (
    <html lang="vi" className={darkMode ? 'dark' : ''}>
      <head>
        <title>Securities AI — Dự đoán cổ phiếu Việt Nam</title>
        <meta
          name="description"
          content="Phân tích và dự đoán cổ phiếu thị trường chứng khoán Việt Nam bằng trí tuệ nhân tạo"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body
        className={`min-h-screen flex flex-col transition-colors duration-300 ${
          darkMode
            ? 'bg-gray-950 text-white'
            : 'bg-gray-50 text-gray-900'
        }`}
      >
        <StockTicker />
        <Navbar darkMode={darkMode} toggleDark={toggleDark} />
        <main className="flex-1">{children}</main>
        <footer
          className={`border-t py-6 mt-8 ${
            darkMode
              ? 'border-gray-800 bg-gray-900'
              : 'border-gray-200 bg-white'
          }`}
        >
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              © 2024 Securities AI — Chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
