import type { Translations } from "../utils/translations";

/** Public pages shared by the landing header, sub-page header and footer. */
export const SITE_NAV: ReadonlyArray<{ key: keyof Translations["nav"]; href: string }> = [
  { key: "calculation", href: "/calculation" },
  { key: "about", href: "/about" },
  { key: "pricing", href: "/pricing" },
  { key: "contact", href: "/contact" },
];
