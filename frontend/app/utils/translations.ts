import type { Lang } from "../context/LanguageContext";

export interface Translations {
  nav: {
    platform: string;
    howItWorks: string;
    opportunities: string;
    calculator: string;
  };
  header: {
    signIn: string;
    signUp: string;
    pricing: string;
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
      signIn: "Log in",
      signUp: "Sign up",
      pricing: "View pricing ↗",
    },
    hero: {
      eyebrow: "EDUCATION, CAREER, AND ROI — IN ONE VIEW",
      h1Line1: "See where your",
      h1Line2: "education",
      h1Line3: "can take you.",
      infoCardP: "Compare the cost,\ncareer outcome, and next move.",
      infoCardExpand: "Model tuition, scholarships, salary assumptions, and payback before you commit to a path.",
      tagRoi: "Cost and payback",
      tagCareer: "Career direction",
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
      signIn: "Увійти",
      signUp: "Реєстрація",
      pricing: "Переглянути ціни ↗",
    },
    hero: {
      eyebrow: "ОСВІТА, КАР’ЄРА ТА ROI — В ОДНОМУ ОГЛЯДІ",
      h1Line1: "Дізнайся, куди",
      h1Line2: "освіта",
      h1Line3: "може привести.",
      infoCardP: "Порівняй вартість,\nкар’єрний результат і наступний крок.",
      infoCardExpand: "Змоделюй вартість навчання, стипендії, припущення щодо зарплати та строк окупності, перш ніж обрати шлях.",
      tagRoi: "Вартість і окупність",
      tagCareer: "Кар’єрний напрям",
    },
    cta: {
      explorePaths: "Дослідити шляхи",
      buildForecast: "Створити прогноз",
      checkEligibility: "Перевірити відповідність",
      exploreYourPath: "Дослідити свій шлях",
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
      signIn: 'Zaloguj się',
      signUp: 'Rejestracja',
      pricing: 'Zobacz ceny ↗',
    },
    hero: {
      eyebrow: "EDUKACJA, KARIERA I ROI — W JEDNYM WIDOKU",
      h1Line1: "Zobacz, dokąd może",
      h1Line2: "zaprowadzić",
      h1Line3: "Cię edukacja.",
      infoCardP: "Porównaj koszt,\nwynik kariery i kolejny krok.",
      infoCardExpand: "Modeluj czesne, stypendia, założenia płacowe i czas zwrotu, zanim wybierzesz ścieżkę.",
      tagRoi: "Koszt i zwrot",
      tagCareer: "Kierunek kariery",
    },
    cta: {
      explorePaths: "Odkryj ścieżki",
      buildForecast: "Zbuduj prognozę",
      checkEligibility: "Sprawdź kwalifikacje",
      exploreYourPath: "Odkryj swoją ścieżkę",
    },
    langLabels: { en: "English", uk: "Українська", pl: "Polski" },
  },
};



