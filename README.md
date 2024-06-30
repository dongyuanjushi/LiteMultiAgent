# MultiAgent


## 06/29, Saturday
* one agent
  * understand langchain agent design
  * change tavily_search to return the complete result for the first page
* multi agents
  * evaluation metrics: effectiveness, efficiency
    * for example, if we pass more tools to one agent, that agents could finish a lot of tasks, but it is very costly since there are too many prompt tokens
  * one super agent, check opendevin [todo]
    * delegation
      * https://github.com/OpenDevin/OpenDevin/blob/874b4c90753f5297512c7cf28b82da7b7aa14edd/agenthub/delegator_agent/agent.py#L14
      * study
      * coder
      * verifier
* different settings
  * use case specific agent:
    * define workflow for specific scenario, different agents work for different part of the work
      * example: one research agent, one production agent
      * use case: very specific use case
  * general agent:
    * a general agent chooses workflow, in each workflow there are different agents working together
      * the general agent is essentially doing the planning
        * but instead of planning by itself, it chooses from existing workflows
          * in each flow, the tool interaction is perfectly defined already!
        * currently if you ask LLM to make a plan, it couldn't utilize existing tools efficently in the planning stage
          * so sometimes, it's plan is not that good, takes more time and money
        * if it's really common-sense, maybe LLM can already do that
      * memory and tool
        * for each task, the general agent
          * only takes the final output of each step
          * if there are multiple steps
            * no need to append each step to the message list of the general agent
          * if in each step, the agent is calling multiple tools
            * no need to use the toolcall and toolresponse message
    * a general agent, whose use a list of agents as tools
      * example: one research agent that research different sources
      * memory and tool