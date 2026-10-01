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
      pricing: "View pricing в†—",
    },
    hero: {
      eyebrow: "EDUCATION, CAREER, AND ROI вЂ” IN ONE VIEW",
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
    langLabels: { en: "English", uk: "РЈРєСЂР°С—РЅСЃСЊРєР°", pl: "Polski" },
  },

  uk: {
    nav: {
      platform: "РџР»Р°С‚С„РѕСЂРјР°",
      howItWorks: "РЇРє С†Рµ РїСЂР°С†СЋС”",
      opportunities: "РњРѕР¶Р»РёРІРѕСЃС‚С–",
      calculator: "РљР°Р»СЊРєСѓР»СЏС‚РѕСЂ",
    },
    header: {
      signIn: "РЈРІС–Р№С‚Рё",
      signUp: "Р РµС”СЃС‚СЂР°С†С–СЏ",
      pricing: "РџРµСЂРµРіР»СЏРЅСѓС‚Рё С†С–РЅРё в†—",
    },
    hero: {
      eyebrow: "РћРЎР’Р†РўРђ, РљРђР 'Р„Р Рђ РўРђ ROI вЂ” Р’ РћР”РќРћРњРЈ РћР“Р›РЇР”Р†",
      h1Line1: "Р”С–Р·РЅР°Р№СЃСЏ, РєСѓРґРё",
      h1Line2: "РѕСЃРІС–С‚Р°",
      h1Line3: "РјРѕР¶Рµ РїСЂРёРІРµСЃС‚Рё.",
      infoCardP: "РџРѕСЂС–РІРЅСЏР№ РІР°СЂС‚С–СЃС‚СЊ,\nРєР°СЂ'С”СЂРЅРёР№ СЂРµР·СѓР»СЊС‚Р°С‚ С– РЅР°СЃС‚СѓРїРЅРёР№ РєСЂРѕРє.",
      infoCardExpand: "Р—РјРѕРґРµР»СЋР№ РѕРїР»Р°С‚Сѓ РЅР°РІС‡Р°РЅРЅСЏ, СЃС‚РёРїРµРЅРґС–С—, Р·Р°СЂРїР»Р°С‚РЅС– РїСЂРёРїСѓС‰РµРЅРЅСЏ С‚Р° СЃС‚СЂРѕРє РѕРєСѓРїРЅРѕСЃС‚С– РґРѕ РѕСЃС‚Р°С‚РѕС‡РЅРѕРіРѕ РІРёР±РѕСЂСѓ.",
      tagRoi: "Р’Р°СЂС‚С–СЃС‚СЊ С– РѕРєСѓРїРЅС–СЃС‚СЊ",
      tagCareer: "РљР°СЂ'С”СЂРЅРёР№ РЅР°РїСЂСЏРј",
    },
    cta: {
      explorePaths: "Р”РѕСЃР»С–РґРёС‚Рё С€Р»СЏС…Рё",
      buildForecast: "РЎС‚РІРѕСЂРёС‚Рё РїСЂРѕРіРЅРѕР·",
      checkEligibility: "РџРµСЂРµРІС–СЂРёС‚Рё РїСЂР°РІРѕ",
      exploreYourPath: "Р’Р°С€ С€Р»СЏС…",
    },
    langLabels: { en: "English", uk: "РЈРєСЂР°С—РЅСЃСЊРєР°", pl: "Polski" },
  },

  pl: {
    nav: {
      platform: "Platforma",
      howItWorks: "Jak to dziaЕ‚a",
      opportunities: "MoЕјliwoЕ›ci",
      calculator: "Kalkulator",
    },
    header: {
      signIn: 'Zaloguj się',
      signUp: 'Rejestracja',
      pricing: 'Zobacz ceny ↗',
    },
    hero: {
      eyebrow: "EDUKACJA, KARIERA I ROI вЂ” W JEDNYM WIDOKU",
      h1Line1: "Zobacz, dokД…d moЕјe",
      h1Line2: "zaprowadziД‡",
      h1Line3: "CiД™ edukacja.",
      infoCardP: "PorГіwnaj koszt,\nwynik kariery i kolejny krok.",
      infoCardExpand: "Modeluj czesne, stypendia, zaЕ‚oЕјenia pЕ‚acowe i czas zwrotu, zanim wybierzesz Е›cieЕјkД™.",
      tagRoi: "Koszt i zwrot",
      tagCareer: "Kierunek kariery",
    },
    cta: {
      explorePaths: "Odkryj Е›cieЕјki",
      buildForecast: "Zbuduj prognozД™",
      checkEligibility: "SprawdЕє kwalifikacje",
      exploreYourPath: "Twoja Е›cieЕјka",
    },
    langLabels: { en: "English", uk: "РЈРєСЂР°С—РЅСЃСЊРєР°", pl: "Polski" },
  },
};



