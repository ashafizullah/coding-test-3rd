import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/lib/query-provider'
import Navigation from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Fund Performance Analysis System',
  description: 'AI-powered fund performance analysis and Q&A system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navigation />
            <main className="container mx-auto px-4 py-8 flex-1">
              {children}
            </main>
            <footer className="bg-white border-t border-gray-200 py-6 mt-auto">
              <div className="container mx-auto px-4">
                <p className="text-center text-gray-600 text-sm">
                  Coding Test - Adam Suchi Hafizullah
                </p>
              </div>
            </footer>
          </div>
        </QueryProvider>
      </body>
    </html>
  )
}
