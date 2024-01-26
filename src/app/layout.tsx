import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "./_components/Header";
import { Footer } from "./_components/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Portfolio Optimization",
  description: "Using the kelly criterion to optimize a portfolio",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex flex-col min-h-screen max-w-[1080px] mx-auto">
          <Header />
          <main className="flex-1 mx-auto">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
