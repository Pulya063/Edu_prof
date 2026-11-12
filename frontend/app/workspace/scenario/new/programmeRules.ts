import type { StudyProgrammeItem } from "@/lib/api/generated";

/**
 * Careers that a field of study leads to. Matched on the programme name (Polish, Ukrainian or English),
 * so a Computer Science programme offers IT roles and a pedagogy programme offers Teacher.
 */
const FIELD_CAREERS: { pattern: RegExp; roles: string[] }[] = [
  { pattern: /informat|computer|software|programow|cyber|sztuczn|artificial|teleinformat|інформат|комп.ютер|програм|кібер/i,
    roles: ["Frontend Developer", "Java Developer", "Python Backend Developer", "QA Engineer", "Data Analyst"] },
  { pattern: /data science|analiz[a-y]? danych|big data|matemat|statyst|ekonometr|mathemat|statist|математ|статист/i,
    roles: ["Data Analyst", "Python Backend Developer", "QA Engineer"] },
  { pattern: /automaty|robot|elektron|mechatron|telekom|electronic|automation|автоматиз|електрон|мехатрон|телеком/i,
    roles: ["QA Engineer", "Python Backend Developer", "Java Developer", "Data Analyst"] },
  { pattern: /rachunk|finans|ekonom|bankow|podatk|accounting|financ|econom|облік|фінанс|економ|банк/i,
    roles: ["Accountant", "Data Analyst", "Marketing Specialist"] },
  { pattern: /marketing|zarządz|logistyk|komunikac|dziennik|media|management|business|менеджм|маркетинг|журналіст|бізнес/i,
    roles: ["Marketing Specialist", "Data Analyst", "Accountant"] },
  { pattern: /prawo|praw[an]|administrac|kryminolog|\blaw\b|право|юрид|правозн/i, roles: ["Lawyer"] },
  { pattern: /lekarsk|medycyn|medicine|лікар|медицин/i, roles: ["Doctor"] },
  { pattern: /pielęgn|położn|ratownict|nursing|медсест|сестринськ/i, roles: ["Nurse"] },
  { pattern: /farmac|pharma|фармац/i, roles: ["Pharmacist"] },
  { pattern: /psycholog|психолог/i, roles: ["Psychologist"] },
  { pattern: /pedagog|nauczyc|edukac|filolog|wczesnoszk|teacher|education|педагог|філолог|вчител|учител|освіт/i, roles: ["Teacher"] },
  { pattern: /budown|architekt|inżynieria lądow|civil engineering|geodez|будівн|архітект/i, roles: ["Civil Engineer"] },
];

/** Roles that fit the chosen programme, in list order; empty when the programme name gives no clue. */
export function careersForProgramme(programme: string, roles: string[]): string[] {
  const name = programme.trim();
  if (!name) return [];
  const wanted = new Set(FIELD_CAREERS.filter((field) => field.pattern.test(name)).flatMap((field) => field.roles));
  return roles.filter((role) => wanted.has(role));
}

/**
 * Standard length of a Polish programme by its level (Law on Higher Education: first cycle 6 semesters,
 * 7 for engineering degrees; second cycle 4; long-cycle 10, medicine 12). Null when the level is unknown.
 */
export function standardStudyYears(item: Pick<StudyProgrammeItem, "name" | "level">, university = ""): number | null {
  const name = item.name.toLowerCase();
  // First-cycle degrees at universities of technology are engineering degrees (7 semesters).
  const technical = /technolog|politechn|polytechn|\bagh\b/i.test(university);
  if (item.level === "first cycle") return name.includes("inżynier") || technical ? 3.5 : 3;
  if (item.level === "second cycle") return 2;
  if (item.level === "long-cycle master's") return /lekarski(?!-?\s*dent)/.test(name) && !name.includes("dentyst") ? 6 : 5;
  return null;
}
