import type { Metadata } from "next";
import "./globals.css";
import "./simple.css";
export const metadata: Metadata = {
  title: "Brand Content Review",
  description:
    "A shared workspace for approved brand knowledge and human content review.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
