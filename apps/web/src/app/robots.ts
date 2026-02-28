import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: ["/", "/vitrin/"],
      disallow: ["/dashboard/", "/tg/", "/api/"],
    },
    sitemap: "https://emlakplatform.com/sitemap.xml",
  };
}
