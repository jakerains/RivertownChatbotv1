import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'RiverTown Ball Company Chat',
  description: 'Chat with our AI assistant about RiverTown Ball Company products',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
} 