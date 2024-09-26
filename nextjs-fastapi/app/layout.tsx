import "./globals.css";
import { Inter } from "next/font/google";
import { ThemeProvider as NextThemesProvider } from "next-themes";


const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Sentimenet Analysis",
  description: "Sentimenet analysis of customer reviews",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <NextThemesProvider attribute="class" defaultTheme="dark">
          {children}
        </NextThemesProvider>
      </body>
    </html>
  );
}
