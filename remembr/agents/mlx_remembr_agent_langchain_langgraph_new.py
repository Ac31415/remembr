"""
MLX-powered ReMEmbR agent using Command-R
Uses mlx-community/c4ai-command-r-v01-4bit for native Mac performance
Enhanced to match remembr_agent.py features with LangChain/LangGraph integration
"""

from typing import Annotated, Literal, Sequence, TypedDict, Optional, List, Dict, Any
import sys
import os
import json
import re
import traceback
from pathlib import Path

# Try MLX imports with error handling
try:
    import mlx.core as mx
    from mlx_lm import load, generate
    MLX_AVAILABLE = True
    print("[MLX] ✓ MLX libraries loaded successfully")
except ImportError as e:
    print(f"[MLX] ❌ MLX imports failed: {e}")
    print("[MLX] Please install MLX: pip install mlx mlx-lm")
    MLX_AVAILABLE = False
    # Create dummy functions to prevent crashes
    def load(*args, **kwargs):
        raise RuntimeError("MLX not available")
    def generate(*args, **kwargs):
        raise RuntimeError("MLX not available")

# LangChain imports
from langchain_core.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage, AIMessage, BaseMessage
from langgraph.graph.message import add_messages
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.runnables import Runnable, RunnableConfig

from langchain.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

# Add path for tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.append(sys.path[0] + '/..')

from remembr.utils.util import file_to_string
# Import specific tools to avoid langchain_openai dependency
from remembr.memory.memory_multimodal import MemoryItem
from remembr.agents.agent import Agent, AgentOutput

### State for LangGraph
class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]

### Print out state of the system
def inspect(state):
    """Print the state passed between Runnables in a langchain and pass it on"""
    for k,v in state.items():
        if type(v) == str:
            print(f"{k}: {v[:100]}...")
        elif type(v) == list:
            print(f"{k}: List with {len(v)} elements")
            for i, item in enumerate(v[:3]):  # Show first 3 items
                print(f"  [{i}]: {str(item)[:100]}...")
        else:
            print(f"{k}: {type(v)}")
    return state

def parse_json(string):
    parsed = re.search(r"```json(.*?)```", string, re.DOTALL| re.IGNORECASE).group(1).strip()
    return eval(parsed)

# Define the function that determines whether to continue or not
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"

def try_except_continue(state, func):
    while True:
        try:
            return func(state)
        except Exception as e:
            print("Here is my error")
            print(e)
            traceback.print_exception(*sys.exc_info())
            continue

class MLXFunctionsWrapper(Runnable):
    """Wrapper to make MLX compatible with FunctionsWrapper interface"""
    
    def __init__(self, model, tokenizer, generation_args):
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer 
        self.generation_args = generation_args
        self.tools = []
        
    def bind_tools(self, tools, **kwargs):
        """Bind tools (for compatibility with LangChain interface)"""
        self.tools = tools
        return self
        
    def invoke(self, messages, config: Optional[RunnableConfig] = None, **kwargs):
        """Generate response using MLX"""
        # Convert messages to prompt
        if isinstance(messages, dict) and 'messages' in messages:
            messages = messages['messages']
            
        if isinstance(messages, list):
            # Extract the last user message
            prompt = str(messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1]))
        else:
            prompt = str(messages)
            
        # Generate using MLX
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            **self.generation_args
        )
        
        # Return as AIMessage for compatibility
        return AIMessage(content=response)

class MLXReMEmbRAgent(Agent):
    """MLX-powered ReMEmbR agent with Command-R, enhanced with full remembr_agent features"""
    
    def __init__(self, llm_type='command-r-mlx', num_ctx=8192, temperature=0, model_backend="COMMAND_R", model_name=None):
        """
        Initialize MLX ReMEmbR agent with model backend choice
        
        Args:
            llm_type: Type of language model (for compatibility)
            num_ctx: Context window size
            temperature: Generation temperature
            model_backend: "COMMAND_R" or "GEMMA" 
            model_name: Custom model name (overrides backend choice)
        """
        # Check MLX availability first
        if not MLX_AVAILABLE:
            raise RuntimeError("MLX libraries not available. Please install: pip install mlx mlx-lm")
            
        self.llm_type = llm_type
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.model_backend = model_backend.upper()
        
        # Set model name based on backend choice
        if model_name:
            self.model_name = model_name
            print(f"[MLX] Using custom model: {model_name}")
        elif self.model_backend == "COMMAND_R":
            self.model_name = "mlx-community/c4ai-command-r-v01-4bit"
            print(f"[MLX] Using Command-R backend")
        elif self.model_backend == "GEMMA":
            self.model_name = "mlx-community/gemma-3n-E2B-it-lm-4bit"
            print(f"[MLX] Using Gemma backend")
        else:
            raise ValueError(f"Unknown model backend: {model_backend}")
        
        print(f"[MLX] Initializing ReMEmbR agent with model: {self.model_name}")
        
        # Load the MLX model with error handling
        try:
            self.model, self.tokenizer = load(self.model_name)
            print(f"[MLX] ✓ {self.model_backend} model loaded successfully")
        except Exception as e:
            print(f"[MLX] ❌ Failed to load {self.model_name}: {e}")
            # Try fallback model
            if self.model_backend == "GEMMA":
                print("[MLX] Trying Command-R as fallback...")
                self.model_name = "mlx-community/c4ai-command-r-v01-4bit"
                self.model_backend = "COMMAND_R"
                self.model, self.tokenizer = load(self.model_name)
                print("[MLX] ✓ Fallback to Command-R successful")
            else:
                raise
        
        # Set generation parameters (MLX generate() accepts verbose, formatter, kwargs)
        # Temperature needs to be passed differently via kwargs
        self.generation_args = {
            "max_tokens": 1024,
            "verbose": False,
        }
        
        # Store temperature separately for manual handling if needed
        self.temp_value = self.temperature
        
        # Initialize chat wrapper (MLX adapter for FunctionsWrapper interface)
        self.chat = MLXFunctionsWrapper(self.model, self.tokenizer, self.generation_args)
        
        # Load system prompts from files
        self._load_system_prompts()
        
        # Initialize tracking variables like original remembr_agent
        self.previous_tool_requests = "These are the tools I have previously used so far: \n"
        self.agent_call_count = 0
        self.chat_history = ChatMessageHistory()
        
        # Memory will be set later
        self.memory = None
        
        print("[MLX] ✓ ReMEmbR agent initialized with enhanced features")
    
    def _load_system_prompts(self):
        """Load system prompts from files like original remembr_agent"""
        top_level_path = str(os.path.dirname(__file__)) + '/../'
        
        try:
            self.agent_prompt = file_to_string(top_level_path+'prompts/agent_system_prompt.txt')
            print("[MLX] ✓ Loaded agent system prompt")
        except Exception as e:
            print(f"[MLX] ⚠️  Could not load agent_system_prompt.txt: {e}")
            self.agent_prompt = "You are ReMEmbR, an AI assistant that helps robots navigate based on memory."
            
        try:
            self.generate_prompt = file_to_string(top_level_path+'prompts/generate_system_prompt.txt')
            print("[MLX] ✓ Loaded generate system prompt")
        except Exception as e:
            print(f"[MLX] ⚠️  Could not load generate_system_prompt.txt: {e}")
            self.generate_prompt = "Generate helpful responses based on robot memory."
            
        try:
            self.agent_gen_only_prompt = file_to_string(top_level_path+'prompts/agent_gen_system_prompt.txt')
            print("[MLX] ✓ Loaded agent gen only prompt")
        except Exception as e:
            print(f"[MLX] ⚠️  Could not load agent_gen_system_prompt.txt: {e}")
            self.agent_gen_only_prompt = "Generate responses without tool usage."
    
    def set_memory(self, memory):
        """Set the memory instance and create tools and graph like original remembr_agent"""
        self.memory = memory
        self.create_tools(memory)
        self.build_graph()
        print(f"[MLX] Memory set and tools created: {type(memory).__name__}")
    
    def create_tools(self, memory):
        """Create LangChain tools for memory retrieval like original remembr_agent"""
        
        template = "At time={{time}} seconds, the robot was at an average position of {{position}} with an average orientation of {{theta}} radians. "
        template += "The robot saw the following: {{page_content}}"

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
        
        print(f"[MLX] ✓ Created {len(self.tool_list)} tools for memory retrieval")
    
    ### Nodes for LangGraph (like original remembr_agent)
    
    def agent(self, state):
        """
        Invokes the agent model to generate a response based on the current state. Given
        the question, it will decide to retrieve using the retriever tool, or simply end.

        Args:
            state (messages): The current state

        Returns:
            dict: The updated state with the agent response appended to messages
        """
        print(f"[MLX] Agent node processing {len(state['messages'])} messages")
        
        messages = state["messages"]
        
        # Create the prompt using the agent system prompt
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", self.agent_prompt),
            MessagesPlaceholder("messages"),
        ])
        
        # Add tool history tracking
        self.agent_call_count += 1
        tool_tracking = f"\nAgent call #{self.agent_call_count}. {self.previous_tool_requests}"
        
        # Format the prompt with tool tracking
        formatted_messages = messages + [AIMessage(content=tool_tracking)]
        
        # Build prompt with tool descriptions for MLX
        # MLX doesn't natively support tool calling, so we need to instruct it in the prompt
        tool_descriptions = "\n\nAvailable tools:\n"
        for tool in self.tool_list:
            tool_descriptions += f"- {tool.name}: {tool.description}\n"
            tool_descriptions += f"  Args: {tool.args}\n"
        
        tool_instruction = """
To use a tool, respond ONLY with JSON in this exact format:
{
    "tool": "tool_name",
    "tool_input": {"x": "search_value"}
}

For queries about hearing sounds (e.g., "car honking", "screaming", "bells"):
- Use: retrieve_from_text
- Example: {"tool": "retrieve_from_text", "tool_input": {"x": "car honking"}}

For queries about specific positions:
- Use: retrieve_from_position
- Example: {"tool": "retrieve_from_position", "tool_input": {"x": [10, 20, 0]}}

For queries about specific times:
- Use: retrieve_from_time  
- Example: {"tool": "retrieve_from_time", "tool_input": {"x": "12:30:00"}}

CRITICAL: For ANY navigation query like "Go to where I heard X", you MUST:
1. First call retrieve_from_text with the sound description
2. Use the retrieved position to answer
3. Do NOT respond without calling a tool first

Respond with ONLY the JSON tool call, no other text.
"""
        
        # Create enhanced prompt for MLX
        system_with_tools = self.agent_prompt + tool_descriptions + tool_instruction
        
        try:
            # Format messages for MLX
            prompt_text = system_with_tools + "\n\n"
            for msg in formatted_messages:
                if hasattr(msg, 'content'):
                    prompt_text += f"{msg.content}\n"
            
            # Generate using MLX
            response_text = generate(
                self.model,
                self.tokenizer,
                prompt=prompt_text,
                **self.generation_args
            )
            
            print(f"[MLX] Agent raw response: {response_text[:200]}...")
            
            # Parse response to detect tool calls
            tool_calls = []
            try:
                # Try to extract JSON tool call - look for tool usage patterns
                import re
                
                # Try multiple patterns to find tool usage
                patterns = [
                    r'\{[^{}]*"tool"[^{}]*"tool_input"[^{}]*\}',  # Standard format
                    r'```json\s*(\{[^`]*\})\s*```',  # JSON code block
                    r'\{[^{}]*"name"[^{}]*"args"[^{}]*\}',  # Alternative format
                ]
                
                tool_json = None
                for pattern in patterns:
                    match = re.search(pattern, response_text, re.DOTALL)
                    if match:
                        try:
                            json_str = match.group(1) if match.lastindex else match.group(0)
                            tool_json = json.loads(json_str)
                            break
                        except:
                            continue
                
                # Also try to detect tool name from text directly
                if not tool_json:
                    # Extract question from messages
                    question_text = messages[0].content if messages else ""
                    
                    # Look for explicit tool mentions in natural language
                    if 'retrieve_from_text' in response_text.lower():
                        # Extract potential search term from the query
                        query_lower = question_text.lower()
                        search_term = ""
                        
                        # Extract keywords for common queries
                        if 'honking' in query_lower or 'horn' in query_lower:
                            search_term = "car honking"
                        elif 'scream' in query_lower:
                            search_term = "screaming"
                        elif 'bell' in query_lower:
                            search_term = "bell"
                        elif 'siren' in query_lower:
                            search_term = "siren"
                        else:
                            # Extract nouns from query as search term
                            words = query_lower.split()
                            search_term = ' '.join([w for w in words if len(w) > 3])[:50]
                        
                        if search_term:
                            tool_json = {
                                'tool': 'retrieve_from_text',
                                'tool_input': {'x': search_term}
                            }
                            print(f"[MLX] Inferred tool call from response text: retrieve_from_text('{search_term}')")
                
                if tool_json:
                    tool_name = tool_json.get('tool') or tool_json.get('name')
                    tool_input = tool_json.get('tool_input') or tool_json.get('args', {})
                    
                    # Validate tool name
                    if tool_name in ['retrieve_from_text', 'retrieve_from_position', 'retrieve_from_time']:
                        # Create tool call in LangChain format
                        tool_calls = [{
                            'name': tool_name,
                            'args': tool_input,
                            'id': f'call_{self.agent_call_count}'
                        }]
                        
                        self.previous_tool_requests += f"- {tool_name}: {tool_input}\n"
                        print(f"[MLX] Detected tool call: {tool_name} with args {tool_input}")
                    else:
                        print(f"[MLX] Invalid tool name: {tool_name}")
                        
            except Exception as parse_err:
                print(f"[MLX] Tool call parsing error: {parse_err}")
                import traceback
                traceback.print_exc()
            
            # Create AIMessage with tool calls if detected
            response = AIMessage(content=response_text, tool_calls=tool_calls)
            print(f"[MLX] Agent response with {len(tool_calls)} tool calls")
            
        except Exception as e:
            print(f"[MLX] Agent processing failed: {e}")
            import traceback
            traceback.print_exc()
            # Create fallback response
            response = AIMessage(content=f"I encountered an error processing your request: {str(e)}")
        
        # Add response to state
        return {"messages": [response]}
    
    def generate(self, state):
        """
        Generate a final response based on retrieved documents and context.
        
        Args:
            state (messages): The current state

        Returns:
            dict: The updated state with the generation response appended to messages
        """
        print(f"[MLX] Generate node processing {len(state['messages'])} messages")
        
        messages = state["messages"]
        question = messages[0].content if messages else "No question provided"
        
        # Extract retrieved context from tool messages
        retrieved_context = ""
        for message in messages:
            if isinstance(message, ToolMessage):
                retrieved_context += f"\n{message.content}"
        
        # Create the generation prompt
        generation_prompt = self.generate_prompt.format(question=question)
        
        # Build full context
        full_context = f"{generation_prompt}\n\nRetrieved Context:{retrieved_context}\n\nQuestion: {question}"
        
        try:
            # Generate using MLX directly
            response_text = generate(
                self.model,
                self.tokenizer,
                prompt=full_context,
                **self.generation_args
            )
            
            print(f"[MLX] Generated response: {response_text[:100]}...")
            
            # Parse response to extract structured output
            parsed_response = self._parse_generate_response(response_text, question)
            
            response = AIMessage(content=json.dumps(parsed_response))
            
        except Exception as e:
            print(f"[MLX] Generation failed: {e}")
            # Create fallback response
            fallback = {
                "tool": "__conversational_response",
                "tool_input": {
                    "response": {
                        "type": "text",
                        "text": f"I encountered an error: {str(e)}",
                        "binary": "no",
                        "position": None,
                        "orientation": None,
                        "duration": None,
                        "time": None
                    }
                }
            }
            response = AIMessage(content=json.dumps(fallback))
        
        return {"messages": [response]}
    
    def build_graph(self):
        """Build the LangGraph workflow like original remembr_agent"""
        try:
            from langgraph.graph import END, StateGraph
            from langgraph.prebuilt import ToolNode
            
            # Define a new graph
            workflow = StateGraph(AgentState)

            # Define the nodes we will cycle between
            workflow.add_node("agent", lambda state: try_except_continue(state, self.agent))
            
            # Tool node for handling tool calls
            tool_node = ToolNode(self.tool_list)
            workflow.add_node("action", tool_node)
            
            # Generation node
            workflow.add_node("generate", lambda state: try_except_continue(state, self.generate))

            # Set entry point
            workflow.set_entry_point("agent")

            # Add conditional edges
            workflow.add_conditional_edges(
                "agent",
                should_continue,
                {
                    "continue": "action",
                    "end": "generate",
                },
            )

            # Add edges
            workflow.add_edge('action', 'agent')
            workflow.add_edge("generate", END)

            # Compile
            self.graph = workflow.compile()
            
            print("[MLX] ✓ Graph compiled successfully")
            
        except ImportError as e:
            print(f"[MLX] ⚠️  LangGraph not available: {e}")
            self.graph = None
    
    def _parse_generate_response(self, response_text: str, question: str):
        """Parse generation response into structured format"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                
                # Fix common JSON formatting issues from MLX models
                # Replace double curly braces with single braces
                json_str = json_str.replace('{{', '{').replace('}}', '}')
                
                # Try to parse
                try:
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError as je:
                    print(f"[MLX] JSON decode error after cleanup: {je}")
                    print(f"[MLX] Attempted to parse: {json_str[:200]}...")
            
            # Try to parse as direct JSON
            try:
                parsed = json.loads(response_text)
                return parsed
            except:
                pass
            
            # Fallback: create structured response
            return {
                "tool": "__conversational_response",
                "tool_input": {
                    "response": {
                        "type_reasoning": "Parsed from plain text response",
                        "type": "text",
                        "answer_reasoning": "MLX generation",
                        "text": response_text.strip(),
                        "binary": "no",
                        "position": None,
                        "orientation": None,
                        "duration": None,
                        "time": None
                    }
                }
            }
            
        except Exception as e:
            print(f"[MLX] Response parsing failed: {e}")
            print(f"[MLX] Response text: {response_text[:300]}...")
            return {
                "tool": "__conversational_response",
                "tool_input": {
                    "response": {
                        "type": "text",
                        "text": f"Error parsing response: {str(e)}",
                        "binary": "no",
                        "position": None,
                        "orientation": None,
                        "duration": None,
                        "time": None
                    }
                }
            }
    
    def query(self, question: str):
        """Main query method that uses the graph like original remembr_agent"""
        if not self.memory:
            raise ValueError("Memory not set. Call set_memory() first.")
            
        if not self.graph:
            print("[MLX] ⚠️  Graph not available, using fallback method")
            return self._query_fallback(question)
        
        print(f"[MLX] Processing query: {question}")
        
        try:
            # Create initial state
            initial_state = {
                "messages": [AIMessage(content=question)]
            }
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Extract final response
            final_message = final_state["messages"][-1]
            response_content = final_message.content
            
            print(f"[MLX] Final response content (first 500 chars): {response_content[:500]}...")
            
            # Parse the structured response using the enhanced parser
            # This handles MLX-specific formatting issues like double curly braces
            if isinstance(response_content, str):
                try:
                    # Use _parse_generate_response to handle MLX formatting quirks
                    parsed_response = self._parse_generate_response(response_content, question)
                    tool_input = parsed_response.get("tool_input", {})
                    response_data = tool_input.get("response", {})
                    
                    # Debug output to verify parsed data
                    print(f"[MLX] Parsed response data keys: {response_data.keys()}")
                    print(f"[MLX] Position (raw): {response_data.get('position')}")
                    print(f"[MLX] Text: {response_data.get('text', '')[:100]}...")
                    
                    # Convert position from string to list if needed
                    position = response_data.get("position", [])
                    if isinstance(position, str):
                        try:
                            # Parse string representation of list: "[11.54,11.14,0.0]"
                            position = json.loads(position)
                            print(f"[MLX] Position converted from string to list: {position}")
                        except:
                            # If JSON parsing fails, try eval (less safe but handles Python list syntax)
                            try:
                                position = eval(position)
                                print(f"[MLX] Position converted using eval: {position}")
                            except:
                                print(f"[MLX] ⚠️  Could not convert position string: {position}")
                                position = []
                    
                    # Convert orientation from string to float if needed
                    orientation = response_data.get("orientation", 0.0)
                    if isinstance(orientation, str):
                        try:
                            # Try to parse as JSON list first
                            orientation_list = json.loads(orientation)
                            if isinstance(orientation_list, list) and len(orientation_list) > 0:
                                # If it's a list, take first element or compute angle
                                orientation = float(orientation_list[0])
                                print(f"[MLX] Orientation converted from list: {orientation}")
                        except:
                            try:
                                orientation = float(orientation)
                            except:
                                print(f"[MLX] ⚠️  Could not convert orientation: {orientation}")
                                orientation = 0.0
                    
                    # Create AgentOutput
                    agent_output = AgentOutput(
                        type=response_data.get("type", "text"),
                        text=response_data.get("text", response_content),
                        binary=response_data.get("binary", "no"),
                        position=position,
                        orientation=orientation,
                        duration=response_data.get("duration", 0.0),
                        time=response_data.get("time", 0.0)
                    )
                    
                    print(f"[MLX] Created AgentOutput with position: {agent_output.position}")
                    return agent_output
                    
                except Exception as e:
                    # Fallback to plain text response
                    print(f"[MLX] Failed to parse response in query(): {e}")
                    return AgentOutput(
                        type="text",
                        text=response_content if isinstance(response_content, str) else str(response_content),
                        binary="no",
                        position=[],
                        orientation=0.0,
                        duration=0.0,
                        time=0.0
                    )
            
            return AgentOutput(
                type="text",
                text=str(response_content),
                binary="no",
                position=[],
                orientation=0.0,
                duration=0.0,
                time=0.0
            )
            
        except Exception as e:
            print(f"[MLX] Query processing failed: {e}")
            return self._create_error_response(question, str(e))
    
    def _query_fallback(self, question: str):
        """Fallback query method when graph is not available"""
        try:
            # Simple direct generation
            prompt = f"{self.agent_gen_only_prompt}\n\nQuestion: {question}\n\nResponse:"
            
            response_text = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                **self.generation_args
            )
            
            return AgentOutput(
                type="text",
                text=response_text.strip(),
                binary="no",
                position=[],
                orientation=0.0,
                duration=0.0,
                time=0.0
            )
            
        except Exception as e:
            return self._create_error_response(question, str(e))
    
    def _create_error_response(self, question: str, error: str):
        """Create error response in AgentOutput format"""
        return AgentOutput(
            type="text",
            text=f"I encountered an error processing '{question}': {error}",
            binary="no",
            position=[],
            orientation=0.0,
            duration=0.0,
            time=0.0
        )

# Example usage and main function
if __name__ == "__main__":
    """Example usage of the enhanced MLX ReMEmbR Agent"""
    
    print("🚀 MLX ReMEmbR Agent - Enhanced Version")
    print("=" * 50)
    
    try:
        # Test agent creation
        agent = MLXReMEmbRAgent(
            llm_type='command-r-mlx',
            model_backend="COMMAND_R",
            temperature=0.1
        )
        
        print("✅ Agent created successfully!")
        
        # Note: Memory needs to be set before querying
        print("\n📝 To use this agent:")
        print("1. Set memory: agent.set_memory(your_memory_instance)")
        print("2. Query: result = agent.query('your question')")
        print("3. Access results: result.text, result.position, etc.")
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        print("💡 Make sure MLX is installed: pip install mlx mlx-lm")