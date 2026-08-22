import type { Metadata } from 'next';
import 'bootstrap/dist/css/bootstrap.min.css';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';

export const metadata: Metadata = {
  title: 'IntelliDesk — Intelligent Helpdesk & Automated Workforce Assignment Platform',
  description: 'Clean, modern, scalable full-stack multi-organization platform with automated workforce assignment and ML ranking.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-light text-dark antialiased min-vh-100">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
