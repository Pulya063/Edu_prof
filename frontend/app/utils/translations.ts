import type { Lang } from "../context/LanguageContext";

export interface Translations {
  nav: {
    calculation: string;
    about: string;
    pricing: string;
    contact: string;
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
    ctaPrimary: string;
    ctaSecondary: string;
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
      calculation: "Calculation",
      about: "About",
      pricing: "Pricing",
      contact: "Contact",
    },
    header: {
      signIn: "Log in",
      signUp: "Sign up",
      pricing: "View pricing ↗",
    },
    hero: {
      eyebrow: "FOR STUDENTS, PARENTS AND CAREER CHANGERS",
      h1Line1: "Know when your",
      h1Line2: "degree",
      h1Line3: "pays you back.",
      infoCardP: "Tuition plus the salary you give up,\nagainst what the job market really pays.",
      infoCardExpand: "Real salaries for your country, your university's tuition and your own assumptions, turned into payback, ROI and a plan.",
      tagRoi: "Payback in months",
      tagCareer: "Live salary data",
      ctaPrimary: "Calculate my payback",
      ctaSecondary: "See how we calculate",
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
      calculation: "Калькуляція",
      about: "Про нас",
      pricing: "Тарифи",
      contact: "Контакти",
    },
    header: {
      signIn: "Увійти",
      signUp: "Реєстрація",
      pricing: "Переглянути ціни ↗",
    },
    hero: {
      eyebrow: "ДЛЯ АБІТУРІЄНТІВ, БАТЬКІВ І ТИХ, ХТО ЗМІНЮЄ КАР’ЄРУ",
      h1Line1: "Дізнайся, коли",
      h1Line2: "диплом",
      h1Line3: "окупиться.",
      infoCardP: "Навчання плюс зарплата, яку ти не заробиш,\nпроти того, скільки реально платить ринок.",
      infoCardExpand: "Реальні зарплати у твоїй країні, вартість навчання та твої припущення перетворюються на окупність, ROI і план дій.",
      tagRoi: "Окупність у місяцях",
      tagCareer: "Живі дані зарплат",
      ctaPrimary: "Порахувати окупність",
      ctaSecondary: "Як ми рахуємо",
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
      calculation: "Kalkulacja",
      about: "O nas",
      pricing: "Cennik",
      contact: "Kontakt",
    },
    header: {
      signIn: 'Zaloguj się',
      signUp: 'Rejestracja',
      pricing: 'Zobacz ceny ↗',
    },
    hero: {
      eyebrow: "DLA MATURZYSTÓW, RODZICÓW I OSÓB ZMIENIAJĄCYCH ZAWÓD",
      h1Line1: "Sprawdź, kiedy",
      h1Line2: "dyplom",
      h1Line3: "się zwróci.",
      infoCardP: "Czesne plus pensja, z której rezygnujesz,\nwobec tego, ile naprawdę płaci rynek.",
      infoCardExpand: "Prawdziwe pensje w Twoim kraju, czesne uczelni i Twoje założenia zamienione w czas zwrotu, ROI i plan działania.",
      tagRoi: "Zwrot w miesiącach",
      tagCareer: "Aktualne dane płacowe",
      ctaPrimary: "Policz mój zwrot",
      ctaSecondary: "Jak liczymy",
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



