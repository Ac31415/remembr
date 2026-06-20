"""
MLX-powered ReMEmbR agent using Command-R with full LangChain/LangGraph integration
Replicates the original remembr_agent.py framework structure
"""

import mlx.core as mx
from mlx_lm import load, generate
import json
import re
import sys
import os
import traceback
from typing import Annotated, Literal, Sequence, TypedDict, Optional, List, Dict, Any

# LangChain imports - matching original remembr_agent.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import ToolMessage, AIMessage, BaseMessage
from langgraph.graph.message import add_messages
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.utils.util import file_to_string
from remembr.tools.tools import *
from remembr.tools.functions_wrapper import FunctionsWrapper
from remembr.memory.memory import Memory, MemoryItem
from remembr.agents.agent import Agent, AgentOutput

def parse_json(string):
    """Parse JSON from string, handling markdown formatting"""
    try:
        parsed = re.search(r"```json(.*?)```", string, re.DOTALL| re.IGNORECASE).group(1).strip()
        return eval(parsed)
    except:
        return json.loads(string)

class AgentState(TypedDict):
    """State for LangGraph agent"""
    messages: Annotated[Sequence[BaseMessage], add_messages]

def should_continue(state: AgentState):
    """Determine whether to continue or end the agent execution"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"

def try_except_continue(state, func):
    """Wrapper to handle exceptions and retry"""
    while True:
        try:
            ret = func(state)
            return ret
        except Exception as e:
            print("I crashed trying to run:", func)
            print("Here is my error")
            print(e)
            traceback.print_exception(*sys.exc_info())
            continue

class MLXChatModel:
    """MLX wrapper that mimics LangChain chat model interface"""
    
    def __init__(self, model_name="mlx-community/c4ai-command-r-v01-4bit"):
        print(f"[MLX Chat Model] Loading {model_name}...")
        self.model, self.tokenizer = load(model_name)
        self.generation_args = {
            "max_tokens": 1024,
            "verbose": False
        }
        print("[MLX Chat Model] ✓ Model loaded successfully")
    
    def invoke(self, messages):
        """Generate response from messages"""
        try:
            # Convert messages to prompt
            if isinstance(messages, dict) and 'question' in messages:
                prompt = messages['question']
                chat_history = messages.get('chat_history', [])
                
                # Build full prompt with chat history
                full_prompt = ""
                for msg in chat_history:
                    if hasattr(msg, 'content'):
                        full_prompt += f"{msg.content}\n"
                
                full_prompt += f"\nQuestion: {prompt}\n\nResponse:"
                
            elif isinstance(messages, list):
                # Handle list of messages
                full_prompt = ""
                for msg in messages:
                    if hasattr(msg, 'content'):
                        full_prompt += f"{msg.content}\n"
            else:
                full_prompt = str(messages)
            
            # Generate response
            response_text = generate(
                self.model,
                self.tokenizer,
                prompt=full_prompt,
                **self.generation_args
            )
            
            # Return AIMessage-like object
            return MLXMessage(content=response_text)
            
        except Exception as e:
            print(f"[MLX Chat Model] Generation failed: {e}")
            return MLXMessage(content="I apologize, but I encountered an error processing your request.")

class MLXMessage:
    """MLX message wrapper that mimics LangChain AIMessage"""
    
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.id = "mlx_message"

class MLXReMEmbRAgent(Agent):
    """MLX-powered ReMEmbR agent with full LangChain/LangGraph integration"""
    
    def __init__(self, llm_type='mlx-command-r', num_ctx=8192, temperature=0):
        print(f"[MLX ReMEmbR Agent] Initializing with LangChain/LangGraph integration...")
        
        # Initialize MLX chat model
        self.chat_model = MLXChatModel()
        
        # Wrap in FunctionsWrapper for tool compatibility
        self.chat = MLXFunctionsWrapper(self.chat_model)
        
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.llm_type = llm_type
        
        # Load embeddings - matching original
        self.embeddings = HuggingFaceEmbeddings(model_name='mixedbread-ai/mxbai-embed-large-v1')
        
        # Load prompts from original files
        top_level_path = str(os.path.dirname(__file__)) + '/../'
        self.agent_prompt = file_to_string(top_level_path+'prompts/agent_system_prompt.txt')
        self.generate_prompt = file_to_string(top_level_path+'prompts/generate_system_prompt.txt')
        self.agent_gen_only_prompt = file_to_string(top_level_path+'prompts/agent_gen_system_prompt.txt')
        
        print("[MLX ReMEmbR Agent] ✓ Prompts loaded from original files")
        
        # Tool usage tracking - matching original
        self.previous_tool_requests = "These are the tools I have previously used so far: \n"
        self.agent_call_count = 0
        self.chat_history = ChatMessageHistory()
        
        print("[MLX ReMEmbR Agent] ✓ Agent initialized with LangChain/LangGraph integration")
    
    def set_memory(self, memory: Memory):
        """Set memory and create tools - matching original"""
        self.memory = memory
        self.create_tools(memory)
        self.build_graph()
        print("[MLX ReMEmbR Agent] ✓ Memory set and graph built")
    
    def create_tools(self, memory):
        """Create retrieval tools - exactly matching original remembr_agent.py"""
        
        class TextRetrieverInput(BaseModel):
            x: str = Field(description="The query that will be searched by the vector similarity-based retriever.\
                                Text embeddings of this description are used. There should always be text in here as a response! \
                                Based on the question and your context, decide what text to search for in the database. \
                                This query argument should be a phrase such as 'a crowd gathering' or 'a green car driving down the road'.\
                                The query will then search your memories for you.")

        self.retriever_tool = StructuredTool.from_function(
            func=lambda x: memory.search_by_text(x),
            name="retrieve_from_text",
            description="Search and return information from your video memory in the form of captions",
            args_schema=TextRetrieverInput
        )

        class PositionRetrieverInput(BaseModel):
            x: tuple = Field(description="The query that will be searched by finding the nearest memories at this (x,y,z) position.\
                                The query must be an (x,y,z) array with floating point values \
                                Based on the question and your context, decide what position to search for in the database. \
                                This query argument should be a position such as (0.5, 0.2, 0.1). They should NOT be a string. \
                                The query will then search your memories for you.")
        
        self.position_retriever_tool = StructuredTool.from_function(
            func=lambda x: memory.search_by_position(x),
            name="retrieve_from_position",
            description="Search and return information from your video memory by using a position array such as (x,y,z)",
            args_schema=PositionRetrieverInput
        )

        class TimeRetrieverInput(BaseModel):
            x: str = Field(description="The query that will be searched by finding the nearest memories at a specific time in H:M:S format.\
                                The query must be a string containing only time. \
                                Based on the question and your context, decide what time to search for in the database. \
                                This query argument should be an HMS time such as 08:02:03 with leading zeros. \
                                The query will then search your memories for you.")

        self.time_retriever_tool = StructuredTool.from_function(
            func=lambda x: memory.search_by_time(x),
            name="retrieve_from_time",
            description="Search and return information from your video memory by using an H:M:S time.",
            args_schema=TimeRetrieverInput
        )

        self.tool_list = [self.retriever_tool, self.position_retriever_tool, self.time_retriever_tool]
        self.tool_definitions = [convert_to_openai_function(t) for t in self.tool_list]
        
        print(f"[MLX ReMEmbR Agent] ✓ Created {len(self.tool_list)} retrieval tools")
    
    def agent(self, state):
        """Agent node - exactly matching original remembr_agent.py logic"""
        messages = state["messages"]
        model = self.chat

        # CRITICAL: Tool call limit matching original - limit to 3 tool calls
        if self.agent_call_count < 3:
            model = model.bind_tools(tools=self.tool_definitions)
            prompt = self.agent_prompt
        else:
            prompt = self.agent_gen_only_prompt

        agent_prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder("chat_history"),
            ("human", self.previous_tool_requests),
            ("ai", prompt),
            ("human", "{question}"),
        ])

        model = agent_prompt | model
        question = f"The question is: {messages[0]}"

        # Convert ToolMessages to AIMessages for MLX compatibility
        processed_messages = []
        for msg in messages:
            if type(msg) == ToolMessage:
                processed_messages.append(AIMessage(id=msg.id, content=msg.content))
            else:
                processed_messages.append(msg)

        response = model.invoke({"question": question, "chat_history": processed_messages[:]})

        # Track tool usage - matching original
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call['name'] != "__conversational_response":
                    args = re.sub("\{.*?\}", "", str(tool_call['args']))
                    self.previous_tool_requests += f"I previously used the {tool_call['name']} tool with the arguments: {args}.\n"

        self.agent_call_count += 1
        return {"messages": [response]}
    
    def generate(self, state):
        """Generate final answer - exactly matching original remembr_agent.py"""
        messages = state["messages"]
        question = messages[0].content + "\n Please responsed in the desired format."
        last_message = messages[-1]
        
        docs = last_message.content

        prompt = PromptTemplate(
            template=self.generate_prompt,
            input_variables=["context", "question"],
        )
        filled_prompt = prompt.invoke({'question': question})

        gen_prompt = ChatPromptTemplate.from_messages([
            ("system", filled_prompt.text),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])

        model = gen_prompt | self.chat

        # Enhanced debug logging
        print(f"[MLX Debug] Question: {question}")
        print(f"[MLX Debug] Context docs: {docs[:200]}...")
        
        response = model.invoke({"question": question, "chat_history": messages[1:]})
        response_text = ''.join(response.content.splitlines())
        
        # Enhanced response logging
        print(f"[MLX Debug] Raw LLM response length: {len(response_text)}")
        print(f"[MLX Debug] Raw LLM response (first 1000 chars): {response_text[:1000]}")
        
        # Parse and validate JSON response - matching original validation
        try:
            if '```json' not in response_text:
                parsed = json.loads(response_text)
            else:
                parsed = parse_json(response_text)

            # Validate required keys - matching original
            keys_to_check_for = ["time", "text", "binary", "position", "duration"]
            for key in keys_to_check_for:
                if key not in parsed:
                    raise ValueError("Missing all the required keys during generate. Retrying...")
                
            if type(parsed['position']) == str:
                parsed['position'] = eval(parsed['position'])
            
            if (parsed['position'] is not None) and len(parsed['position']) != 3:
                raise ValueError(f"Shape of position was incorrect. {parsed['position']}. Retrying...")

        except Exception as e:
            print(f"[MLX Debug] Parse error: {e}")
            raise ValueError("Generate call failed. Retrying...")

        # Reset counters - matching original
        self.previous_tool_requests = "These are the tools I have previously used so far: \n"
        self.agent_call_count = 0
        
        return {"messages": [str(parsed)]}
    
    def build_graph(self):
        """Build LangGraph workflow - exactly matching original remembr_agent.py"""
        from langgraph.graph import END, StateGraph
        from langgraph.prebuilt import ToolNode

        # Define a new graph
        workflow = StateGraph(AgentState)

        # Define nodes - matching original
        workflow.add_node("agent", lambda state: try_except_continue(state, self.agent))
        tool_node = ToolNode(self.tool_list)
        workflow.add_node("action", tool_node)
        workflow.add_node("generate", lambda state: try_except_continue(state, self.generate))

        # Set entry point
        workflow.set_entry_point("agent")

        # Conditional edges - matching original
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "action",
                "end": "generate",
            },
        )

        workflow.add_edge('action', 'agent')
        workflow.add_edge("generate", END)

        # Compile
        self.graph = workflow.compile()
        print("[MLX ReMEmbR Agent] ✓ LangGraph workflow compiled successfully")
    
    def query(self, question: str):
        """Query the agent - exactly matching original remembr_agent.py interface"""
        inputs = {
            "messages": [("user", question)]
        }

        print(f"[MLX Debug] Starting query with question: {question}")
        out = self.graph.invoke(inputs)
        
        print(f"[MLX Debug] Graph output keys: {list(out.keys())}")
        
        response = out['messages'][-1]
        response_text = ''.join(response.content.splitlines())
        
        print(f"[MLX Debug] Final response from graph: {response_text}")
        
        # Parse final response - matching original
        if '```json' not in response_text:
            parsed = eval(response_text) 
        else:
            parsed = parse_json(response_text)

        response = AgentOutput.from_dict(parsed)
        return response

class MLXFunctionsWrapper(FunctionsWrapper):
    """MLX-compatible functions wrapper"""
    
    def __init__(self, mlx_model):
        self.llm = mlx_model
        self.tool_system_prompt_template = FunctionsWrapper.tool_system_prompt_template
    
    def bind_tools(self, tools, **kwargs):
        """Bind tools to the model"""
        # Store tools for later use
        self.bound_tools = tools
        return self
    
    def invoke(self, messages):
        """Invoke the model with tool support"""
        try:
            # Extract the actual question/prompt
            if isinstance(messages, dict):
                question = messages.get('question', str(messages))
                chat_history = messages.get('chat_history', [])
            else:
                question = str(messages)
                chat_history = []
            
            # Generate response using MLX
            response_text = generate(
                self.llm.model,
                self.llm.tokenizer,
                prompt=question,
                max_tokens=1024,
                verbose=False
            )
            
            # Try to parse as JSON for tool calls
            try:
                if '```json' in response_text or '{' in response_text:
                    # Extract and parse JSON
                    if '```json' in response_text:
                        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1).strip()
                        else:
                            json_str = response_text
                    else:
                        json_str = response_text
                    
                    parsed = json.loads(json_str)
                    
                    # Check if this is a tool call
                    if isinstance(parsed, dict) and 'tool' in parsed:
                        tool_calls = [ToolCall(
                            name=parsed['tool'],
                            args=parsed.get('tool_input', {}),
                            id=f"call_{hash(response_text) % 1000000}"
                        )]
                        return MLXMessage(content="", tool_calls=tool_calls)
                    elif isinstance(parsed, list) and len(parsed) > 0 and 'tool' in parsed[0]:
                        tool_calls = []
                        for item in parsed:
                            tool_calls.append(ToolCall(
                                name=item['tool'],
                                args=item.get('tool_input', {}),
                                id=f"call_{hash(str(item)) % 1000000}"
                            ))
                        return MLXMessage(content="", tool_calls=tool_calls)
            
            except (json.JSONDecodeError, KeyError):
                pass
            
            # Return as regular message if no tool calls
            return MLXMessage(content=response_text)
            
        except Exception as e:
            print(f"[MLX Functions Wrapper] Error: {e}")
            return MLXMessage(content="I encountered an error processing your request.")

class ToolCall:
    """Tool call representation"""
    def __init__(self, name, args, id):
        self.name = name
        self.args = args
        self.id = id
    
    def __getitem__(self, key):
        return getattr(self, key)