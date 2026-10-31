import type { Metadata } from "next";
import "./globals.css";
import "./simple.css";
import "./refinement.css";
import "./controls.css";
export const metadata: Metadata = {
  title: "Brand Content Review",
  description:
    "A shared workspace for approved brand knowledge and human content review.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=null;try{t=localStorage.getItem('brandgate-theme')}catch(e){}var dark=t==='dark'||(t!=='light'&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.dataset.theme=dark?'dark':'light'})()`,
          }}
        />
        {children}
      </body>
    </html>
  );
}
