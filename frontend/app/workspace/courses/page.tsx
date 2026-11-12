import { redirect } from "next/navigation";

// Courses are hidden until Fence has course partners; the catalog component stays for later.
export default function CoursesPage() {
  redirect("/workspace/overview");
}
