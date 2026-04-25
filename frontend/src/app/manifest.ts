import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Bytloop POS",
    short_name: "Bytloop",
    description: "Multi-vertical POS platform for retail, food & beverage, hospitality, services, and specialty.",
    start_url: "/dashboard",
    display: "standalone",
    orientation: "landscape",
    background_color: "#0a0a0a",
    theme_color: "#6366f1",
    icons: [
      { src: "/brand/bytloop-mark.svg", type: "image/svg+xml", sizes: "any", purpose: "any" },
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/apple-touch-icon.png", sizes: "180x180", type: "image/png", purpose: "any" },
    ],
  };
}
