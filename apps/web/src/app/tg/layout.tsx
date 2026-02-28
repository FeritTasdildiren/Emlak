import type { Metadata } from "next";
import TGLayoutClient from "./layout-client";

export const metadata: Metadata = {
  title: "Telegram Mini App",
  robots: {
    index: false,
    follow: false,
  },
};

export default function TGLayout({ children }: { children: React.ReactNode }) {
  return <TGLayoutClient>{children}</TGLayoutClient>;
}
