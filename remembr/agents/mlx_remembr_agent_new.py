"""
MLX-powered ReMEmbR agent using Command-R
Uses mlx-community/c4ai-command-r-v01-4bit for native Mac performance
"""

import mlx.core as mx
from mlx_lm import load, generate
import json
import re
from typing import Optional, List, Dict, Any
from remembr.memory.memory import MemoryItem
from remembr.agents.agent import Agent

class MLXReMEmbRAgent(Agent):
    """MLX-powered ReMEmbR agent with Command-R"""
    
    def __init__(self, model_name="mlx-community/c4ai-command-r-v01-4bit"):
        print(f"[MLX] Initializing ReMEmbR agent with model: {model_name}")
        
        # Load the MLX model
        self.model, self.tokenizer = load(model_name)
        print("[MLX] ✓ Command-R model loaded successfully")
        
        # Set generation parameters
        self.generation_args = {
            "max_tokens": 1024,
        }
        
        self.memory = None
    
    def set_memory(self, memory):
        """Set the memory instance for the agent"""
        self.memory = memory
        print(f"[MLX] Memory set: {type(memory).__name__}")
    
    def query(self, question: str, num_memories: int = 10):
        """Query the agent with a question"""
        if not self.memory:
            raise ValueError("Memory not set. Call set_memory() first.")
        
        print(f"[MLX] Processing query: {question}")
        
        # Retrieve relevant memories
        try:
            relevant_memories = self.memory.search(question, limit=num_memories)
            print(f"[MLX] Retrieved {len(relevant_memories)} relevant memories")
        except Exception as e:
            print(f"[MLX] Memory search failed: {e}")
            relevant_memories = []
        
        # Create the prompt for Command-R
        prompt = self._create_prompt(question, relevant_memories)
        
        # Generate response
        try:
            response_text = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                verbose=False,
                **self.generation_args
            )
            
            print(f"[MLX] Generated response: {response_text[:100]}...")
            
            # Parse the response
            parsed_response = self._parse_response(response_text, question, relevant_memories)
            
            print(f"[MLX] Parsed response: {parsed_response.text[:100]}...")
            
            return parsed_response
            
        except Exception as e:
            print(f"[MLX] Generation failed: {e}")
            return self._create_fallback_response(question)
    
    def _create_prompt(self, question: str, memories: List[MemoryItem]) -> str:
        """Create a structured prompt for Command-R with multimodal memory"""
        
        # Format memories with both visual and audio information
        memory_context = ""
        if memories:
            memory_entries = []
            for mem in memories[:10]:
                entry = f"Time {mem.time:.1f}s: At position ({mem.position[0]:.2f}, {mem.position[1]:.2f}), facing {mem.theta:.2f} rad"
                
                # Add visual caption
                if mem.caption and mem.caption.strip():
                    entry += f" - Visual: {mem.caption}"
                
                # Add audio caption if available
                if hasattr(mem, 'audio_caption') and mem.audio_caption and mem.audio_caption.strip():
                    entry += f" - Audio: {mem.audio_caption}"
                
                memory_entries.append(entry)
            
            memory_context = "\n".join(memory_entries)
        else:
            memory_context = "No relevant memories found."
        
        prompt = f"""<|START_OF_TURN_TOKEN|><|USER_TOKEN|>You are ReMEmbR, an AI assistant that helps robots navigate their environment based on multimodal memory (visual and audio). 

## Robot Multimodal Memory Context:
{memory_context}

## User Question:
{question}

## Instructions:
1. Consider both visual and audio information from the robot's memory
2. If the user asks to go somewhere or find something, provide coordinates in [x, y] format
3. Choose the most relevant position from the memories above
4. If multiple positions are mentioned, pick the most recent or most relevant one
5. Use both visual and audio cues to make better decisions
6. Your response must be valid JSON

## Response Format:
{{
    "text": "Your helpful response here, incorporating both visual and audio information",
    "position": [x, y] or null,
    "confidence": 0.0-1.0,
    "reasoning": "Why you chose this position, mentioning both visual and audio cues"
}}

Respond only with valid JSON.<|END_OF_TURN_TOKEN|><|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>"""

        return prompt
    
    def _parse_response(self, response_text: str, question: str, memories: List[MemoryItem]):
        """Parse the model's response with enhanced position extraction"""
        try:
            # Clean up the response
            response_text = response_text.strip()
            
            # Remove any markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Try to parse JSON first
            try:
                parsed = json.loads(response_text)
                
                # Validate and extract position
                position = parsed.get("position")
                if position and isinstance(position, list) and len(position) >= 2:
                    # Ensure we have valid numbers
                    if all(isinstance(x, (int, float)) and x is not None for x in position[:2]):
                        final_position = [float(position[0]), float(position[1])]
                    else:
                        final_position = self._extract_position_from_memories(question, memories)
                else:
                    final_position = self._extract_position_from_memories(question, memories)
                
                return AgentResponse(
                    text=parsed.get("text", response_text),
                    position=final_position,
                    confidence=parsed.get("confidence", 0.7),
                    reasoning=parsed.get("reasoning", "MLX Command-R multimodal analysis")
                )
                
            except json.JSONDecodeError:
                print(f"[MLX] JSON decode failed, trying alternative parsing...")
                # Try to extract position from text
                position = self._extract_position_from_text(response_text, memories)
                
                return AgentResponse(
                    text=response_text,
                    position=position,
                    confidence=0.6,
                    reasoning="Extracted from text response"
                )
                
        except Exception as e:
            print(f"[MLX] Response parsing failed: {e}")
            return self._create_fallback_response(question)
    
    def _extract_position_from_memories(self, question: str, memories: List[MemoryItem]):
        """Extract the most relevant position from memories based on the question"""
        if not memories:
            return None
        
        # Simple heuristic: return the position of the most recent relevant memory
        # In a more sophisticated implementation, you could use semantic similarity
        
        # For navigation requests, prefer the first (most relevant) memory
        best_memory = memories[0]
        
        if best_memory.position and len(best_memory.position) >= 2:
            return [float(best_memory.position[0]), float(best_memory.position[1])]
        
        return None
    
    def _extract_position_from_text(self, text: str, memories: List[MemoryItem]):
        """Try to extract position coordinates from response text"""
        try:
            # Look for coordinate patterns like [x, y] or (x, y)
            coord_patterns = [
                r'\[(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\]',  # [x, y]
                r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)',   # (x, y)
                r'position\s+(-?\d+\.?\d*),\s*(-?\d+\.?\d*)',  # position x, y
            ]
            
            for pattern in coord_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    x, y = matches[0]
                    return [float(x), float(y)]
            
            # If no coordinates found in text, fall back to memory extraction
            return self._extract_position_from_memories("", memories)
            
        except Exception as e:
            print(f"[MLX] Position extraction from text failed: {e}")
            return self._extract_position_from_memories("", memories)
    
    def _create_fallback_response(self, question: str):
        """Create a fallback response when generation fails"""
        return AgentResponse(
            text=f"I understand you're asking about: {question}. However, I'm having difficulty processing your request right now. Could you try rephrasing your question?",
            position=None,
            confidence=0.3,
            reasoning="Fallback response due to processing error"
        )

class AgentResponse:
    """Response object for agent queries"""
    def __init__(self, text: str, position=None, confidence: float = 0.5, reasoning: str = ""):
        self.text = text
        self.position = position
        self.confidence = confidence
        self.reasoning = reasoning
        self.time = None