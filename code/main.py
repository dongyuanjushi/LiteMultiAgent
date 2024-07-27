import logging
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from typing import Any
from pydantic import BaseModel, validator
import sys
from logging.handlers import RotatingFileHandler
import requests
import os
import json
_ = load_dotenv()
from supabase import create_client, Client
from typing import Any, List, Dict
import time
import argparse
import concurrent.futures


url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

# Create a logger
logger = logging.getLogger(__name__)

from utils import *


# from web_search_agent import use_web_search_agent
from io_agent import use_io_agent
from exec_agent import use_exec_agent
# from db_retrieval_agent import use_db_retrieval_agent
from retrieval_agent import use_retrieval_search_agent
# from login_agent import use_login_agent

def scan_folder(folder_path, depth=2):
    ignore_patterns = [".*", "__pycache__"]
    file_paths = []
    for subdir, dirs, files in os.walk(folder_path):
        dirs[:] = [
            d for d in dirs
            if not any(
                d.startswith(pattern) or d == pattern for pattern in ignore_patterns
            )
        ]
        if subdir.count(os.sep) - folder_path.count(os.sep) >= depth:
            del dirs[:]
            continue
        for file in files:
            file_paths.append(os.path.join(subdir, file))
    return file_paths



tools = [
    {
        "type": "function",
        "function": {
            "name": "use_io_agent",
            "description": "Read or write content from/to a file, or generate and save an image using text input",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The task description detailing what to read, write, or generate. This can include file operations or image generation requests."
                    }
                },
                "required": [
                    "description"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "use_exec_agent",
            "description": "Execute some script in a subprocess, either run a bash script, or run a python script ",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The task description describing what to execute in the subprocess.",
                    }
                },
                "required": [
                    "query"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_folder",
            "description": "Scan a directory recursively for files with path with depth 2. You can also use this function to understand the folder structure in a given folder path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "The folder path to scan."
                    }
                },
                "required": [
                    "folder_path"
                ]
            },
            "return_type": "list: A list of file paths str with the given extension, or all files if no extension is specified."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "use_retrieval_search_agent",
            "description": "Use a smart research assistant to look up information using multiple sources including web search, database retrieval, and local file retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "The task description specifying the information source (web search, database, local file) and the question to be answered. specify this in natural language"
                    }
                },
                "required": [
                    "query"
                ]
            }
        }
    },
]

from config import agent_to_model

agent_name = "main_agent"
model_name = agent_to_model[agent_name]["model_name"]

available_tools = {
            "scan_folder": scan_folder,
            "use_retrieval_search_agent": use_retrieval_search_agent,
            "use_io_agent": use_io_agent,
            "use_exec_agent": use_exec_agent,
        }


def execute_task(query: str, task_id: int, use_sub_workers_parallel: bool) -> Dict[str, Any]:
    messages = [{"role": "system", "content": "You are a smart research assistant. Use the search engine to look up information. \
    You are allowed to make multiple calls (either together or in sequence). \
    Only look up information when you are sure of what you want. \
    If you need to look up some information before asking a follow up question, you are allowed to do that!"}]

    start_time = time.time()

    # Execute the function
    result = send_prompt("main_agent", messages, query, tools, available_tools)

    end_time = time.time()
    elapsed_time = end_time - start_time

    return {
        "task_id": task_id,
        "query": query,
        "result": result,
        "elapsed_time": elapsed_time
    }


def main(queries: List[str], use_main_workers_parallel: bool, use_sub_workers_parallel: bool, write_to_db: bool):
    total_start_time = time.time()

    task_results = []

    if use_main_workers_parallel:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_query = {executor.submit(execute_task, query, idx, use_sub_workers_parallel): idx for idx, query in enumerate(queries)}

            for future in concurrent.futures.as_completed(future_to_query):
                task_id = future_to_query[future]
                try:
                    result = future.result()
                    task_results.append(result)
                    print(f"Task {task_id}: {result['query']}")
                    print(f"Execution time: {result['elapsed_time']:.2f} seconds")
                    print("---")
                except Exception as exc:
                    print(f"Task {task_id} generated an exception: {exc}")
    else:
        for idx, query in enumerate(queries):
            try:
                result = execute_task(query, idx, use_sub_workers_parallel)
                task_results.append(result)
                print(f"Task {idx}: {result['query']}")
                print(f"Execution time: {result['elapsed_time']:.2f} seconds")
                print("---")
            except Exception as exc:
                print(f"Task {idx} generated an exception: {exc}")

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time

    print(f"Total execution time for all tasks: {total_elapsed_time:.2f} seconds")

    # Write results to Supabase if specified
    if write_to_db:
        write_to_supabase(task_results)
    else:
        print("Results not written to database as per configuration.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run agent tasks with configurable parallelism.")
    parser.add_argument("--main-workers-parallel", action="store_true", help="Enable parallel execution for main workers")
    parser.add_argument("--sub-workers-parallel", action="store_true", help="Enable parallel execution for sub-workers")
    parser.add_argument("--write-to-db", action="store_true", help="Write results to Supabase")
    args = parser.parse_args()

    queries = [
        "write aaa to 1.txt, bbb to 2.txt, ccc to 3.txt",
        "browse google.com to check the brands of dining table and summarize the results in a table, save the table as a readme file",
        "generate a image of a ginger cat and save it as ginger_cat.png",
    ]

    main(queries, args.main_workers_parallel, args.sub_workers_parallel, args.write_to_db)