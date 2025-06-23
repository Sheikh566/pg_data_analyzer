import os
from .tools import get_database_schema, validate_select_query, execute_query
from google.adk.agents import LlmAgent, SequentialAgent

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_GEMINI_2_5_FLASH", "gemini-2.0-flash")

query_generator_agent = LlmAgent(
    name="QueryGenerator",
    model=MODEL_NAME,
    description="Generates SQL SELECT queries based on user input",
    instruction="""You are a SQL query generator. Your task is to create valid SQL SELECT queries based on user input.
        The queries must only contain SELECT statements and should not modify the database in any way.
        Use get_database_schema() tool to understand the database structure first.
        Ensure that SQL dialect is PostgreSQL compatible.
        The generated query should cast all numeric values to TEXT""",
    tools=[get_database_schema],
    output_key="generated_query",
)

query_executor_agent = LlmAgent(
    name="QueryExecutor",
    model=MODEL_NAME,
    description="Executes SQL queries against the database",
    instruction="""You are a SQL query executor. Your task is to execute the provided SQL SELECT query
        in {generated_query} against the database and return the results.
        Ensure that the query is valid and does not modify the database.
        Use validate_select_query(query) to check if the query is a valid SELECT statement.""",
    tools=[validate_select_query, execute_query],
    output_key="query_result",
)

data_analyzer_agent = SequentialAgent(
    name="DataAnalyzer",
    sub_agents=[query_generator_agent, query_executor_agent],
    description="Analyzes data by generating and executing SQL queries"
)

root_agent = data_analyzer_agent
