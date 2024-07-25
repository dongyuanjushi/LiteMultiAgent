agent_to_model = {
    "main_agent":
        {
            "model_name" : "openai/gpt-4o-mini",
            "tool_choice" : "auto",
         },
    "io_agent": {
            "model_name" : "google/gemini-flash-1.5",
            "tool_choice" : "required",
         },
    "retrieval_agent": {
            "model_name" : "openai/gpt-4o-mini",
            "tool_choice" : "auto",
         },
    "web_search_agent":{
            "model_name" : "openai/gpt-4o-mini",
            "tool_choice" : "auto",
         },
    "db_retrieval_agent":{
            "model_name" : "openai/gpt-4o-mini",
            "tool_choice" : "auto",
         },
    "exec_agent":{
            "model_name" : "openai/gpt-4o-mini",
            "tool_choice" : "auto",
         },
   "local_retrieval_agent":{
            "model_name" : "openai/gpt-4o-mini",
            "tool_choice" : "required",
         },
}