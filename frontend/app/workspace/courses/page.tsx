import type { Metadata } from "next";
import CourseCatalog from "./CourseCatalog";

export const metadata: Metadata = { title: "Course search" };

export default function CoursesPage() {
  return <CourseCatalog />;
}

