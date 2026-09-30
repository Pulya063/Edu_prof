import type { Lang } from "../context/LanguageContext";

export interface Translations {
  nav: {
    platform: string;
    howItWorks: string;
    opportunities: string;
    calculator: string;
  };
  header: {
    logIn: string;
    getStarted: string;
  };
  hero: {
    eyebrow: string;
    h1Line1: string;
    h1Line2: string;
    h1Line3: string;
    infoCardP: string;
    infoCardExpand: string;
    tagRoi: string;
    tagCareer: string;
  };
  cta: {
    explorePaths: string;
    buildForecast: string;
    checkEligibility: string;
    exploreYourPath: string;
  };
  langLabels: Record<Lang, string>;
}

export const translations: Record<Lang, Translations> = {
  en: {
    nav: {
      platform: "Platform",
      howItWorks: "How it works",
      opportunities: "Opportunities",
      calculator: "Calculator",
    },
    header: {
      logIn: "Log in",
      getStarted: "Get started ↗",
    },
    hero: {
      eyebrow: "EDUCATION ROI, MADE CLEAR",
      h1Line1: "Make a smarter",
      h1Line2: "education",
      h1Line3: "decision.",
      infoCardP: "Tuition, payback,\nfuture paths.",
      infoCardExpand: "A single view of the costs, return, and next steps behind your education decision.",
      tagRoi: "ROI clarity",
      tagCareer: "Career fit",
    },
    cta: {
      explorePaths: "Explore their paths",
      buildForecast: "Build my forecast",
      checkEligibility: "Check eligibility",
      exploreYourPath: "Explore your path",
    },
    langLabels: { en: "English", uk: "Українська", pl: "Polski" },
  },

  uk: {
    nav: {
      platform: "Платформа",
      howItWorks: "Як це працює",
      opportunities: "Можливості",
      calculator: "Калькулятор",
    },
    header: {
      logIn: "Увійти",
      getStarted: "Почати ↗",
    },
    hero: {
      eyebrow: "ROI ОСВІТИ — ЗРОЗУМІЛО",
      h1Line1: "Зроби розумніший",
      h1Line2: "освітній",
      h1Line3: "вибір.",
      infoCardP: "Вартість навчання,\nповернення, майбутнє.",
      infoCardExpand: "Єдиний огляд витрат, прибутку та наступних кроків у вашому освітньому рішенні.",
      tagRoi: "Чіткий ROI",
      tagCareer: "Відповідність кар'єрі",
    },
    cta: {
      explorePaths: "Дослідити шляхи",
      buildForecast: "Створити прогноз",
      checkEligibility: "Перевірити право",
      exploreYourPath: "Ваш шлях",
    },
    langLabels: { en: "English", uk: "Українська", pl: "Polski" },
  },

  pl: {
    nav: {
      platform: "Platforma",
      howItWorks: "Jak to działa",
      opportunities: "Możliwości",
      calculator: "Kalkulator",
    },
    header: {
      logIn: "Zaloguj się",
      getStarted: "Zacznij ↗",
    },
    hero: {
      eyebrow: "ROI EDUKACJI — JASNO",
      h1Line1: "Podejmij mądrzejszą",
      h1Line2: "decyzję",
      h1Line3: "edukacyjną.",
      infoCardP: "Czesne, zwrot,\nprzyszłe ścieżki.",
      infoCardExpand: "Jeden widok kosztów, zwrotu i kolejnych kroków Twojej decyzji edukacyjnej.",
      tagRoi: "Jasny ROI",
      tagCareer: "Dopasowanie kariery",
    },
    cta: {
      explorePaths: "Odkryj ścieżki",
      buildForecast: "Zbuduj prognozę",
      checkEligibility: "Sprawdź kwalifikacje",
      exploreYourPath: "Twoja ścieżka",
    },
    langLabels: { en: "English", uk: "Українська", pl: "Polski" },
  },
};
