import "./globals.css";

export const metadata = {
  title: "My AI Chat",
  description: "A ChatGPT-style chat app with RAG capabilities",
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