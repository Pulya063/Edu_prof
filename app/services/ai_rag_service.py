import logging
import os
from decimal import Decimal

from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

MINCER_GROWTH_RATES = {
    range(1, 4):   Decimal("0.08"),
    range(4, 7):   Decimal("0.05"),
    range(7, 11):  Decimal("0.03"),
}
MINCER_PLATEAU = Decimal("0.02")


class AIRAGService:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        try:
            self.embeddings = OllamaEmbeddings(model=self.model_name)
            self.llm = Ollama(model=self.model_name, temperature=0.2)
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            logger.info(f"AIRAGService initialized successfully with model {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize AIRAGService: {e}")

    def add_texts_to_kb(self, texts: list[str], metadatas: list[dict] = None):
        """Додає тексти до векторної бази."""
        try:
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            logger.info(f"Added {len(texts)} chunks to Chroma DB.")
        except Exception as e:
            logger.error(f"Error adding texts to KB: {e}")

    def predict_career_prospects(self, profession: str, country: str) -> dict:
        """
        Шукає дані у векторній базі та формує прогноз зарплати і розвитку 
        для конкретної професії та країни.
        """
        try:
            # 1. Пошук контексту
            query = f"Salary and career prospects for {profession} in {country}"
            docs = self.retriever.get_relevant_documents(query)
            context = "\n\n".join(doc.page_content for doc in docs)

            # 2. Промпт для генерації JSON
            parser = JsonOutputParser()
            
            prompt_template = """
            You are an expert career counselor and labor market analyst.
            Based on the following context, predict the career prospects for the profession "{profession}" in "{country}".
            
            Context:
            {context}
            
            If the context does not contain enough information, make a highly educated guess based on typical global trends.
            
            Return ONLY a valid JSON object with the following keys and types:
            - "expected_start_salary": (float) estimated starting salary in USD per year.
            - "average_salary": (float) estimated average salary in USD per year.
            - "forecast_growth_percent": (float) expected annual salary growth rate (e.g. 5.5 for 5.5%).
            - "demand_score": (int) 0 to 100, representing current market demand.
            - "ai_risk_score": (int) 0 to 100, representing the risk of automation by AI.
            
            Do not include markdown blocks like ```json in the output.
            """
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["profession", "country", "context"],
            )
            
            # 3. Виклик LLM
            chain = prompt | self.llm | parser
            result = chain.invoke({
                "profession": profession,
                "country": country,
                "context": context
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for {profession}: {e}")
            # Fallback значення, якщо LLM або Chroma не доступні
            return {
                "expected_start_salary": 45000.0,
                "average_salary": 60000.0,
                "forecast_growth_percent": 3.0,
                "demand_score": 70,
                "ai_risk_score": 30
            }

    def generate_qualitative_insights(self, stats: dict) -> dict:
        """
        Takes statistical ROI data and uses LLM to generate qualitative insights.
        """
        try:
            parser = JsonOutputParser()
            
            prompt_template = """
            You are an expert career counselor and education investment analyst.
            You are provided with the following calculated statistical data for a student's education and career plan:
            
            Profession: {profession}
            Country: {country}
            Start Salary: {start_salary}
            Average Salary: {average_salary}
            Total Education Investment: {investment_min} to {investment_max}
            Payback Time (Months): {payback_low} to {payback_high}
            First Year ROI (%): {first_year_low} to {first_year_high}
            AI Risk Score: {ai_risk}
            Demand Score: {demand}
            Official O*NET Required Skills: {real_skills_from_onet}
            
            Based on this data, provide qualitative insights for their career roadmap.
            
            Return ONLY a valid JSON object with the following structure:
            {{
                "skills_to_learn_outside_university": ["skill 1", "skill 2", "skill 3"],
                "recommended_strategy": {{
                    "year_1": "string (what to focus on in year 1)",
                    "year_2": "string (what to focus on in year 2)",
                    "year_3": "string (what to focus on in year 3)",
                    "final_stage": "string (final transition into job)"
                }},
                "biggest_risk": {{
                    "risk": "string (e.g., High AI automation risk for junior tasks)",
                    "result": "string (e.g., Focus on soft skills and complex system design to mitigate)"
                }},
                "verdict": "string (a 2-3 sentence final recommendation on whether this is a good investment)"
            }}
            
            Write all text values in Ukrainian.
            Do not include markdown blocks like ```json in the output.
            """
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=[
                    "profession", "country", "start_salary", "average_salary", 
                    "investment_min", "investment_max", "payback_low", "payback_high", 
                    "first_year_low", "first_year_high", "ai_risk", "demand", "real_skills_from_onet"
                ],
            )
            
            chain = prompt | self.llm | parser
            result = chain.invoke(stats)
            
            return result
            
        except Exception as e:
            logger.error(f"Qualitative insights generation failed: {e}")
            return {
                "skills_to_learn_outside_university": ["Soft skills", "English B2+", "Networking"],
                "recommended_strategy": {
                    "year_1": "Опануйте базові навички та інструменти.",
                    "year_2": "Знайдіть перше стажування або фріланс-проєкти.",
                    "year_3": "Сфокусуйтесь на портфоліо та практичних кейсах.",
                    "final_stage": "Активний пошук роботи на позицію Junior."
                },
                "biggest_risk": {
                    "risk": "Висока конкуренція серед початківців.",
                    "result": "Необхідно мати сильне портфоліо для виділення серед кандидатів."
                },
                "verdict": "Це хороша інвестиція, якщо ви готові активно вчитися поза університетською програмою."
            }
