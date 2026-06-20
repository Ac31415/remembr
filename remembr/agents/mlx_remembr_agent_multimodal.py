"""
MLX-powered ReMEmbR agent using Command-R (multimodal memory version)
Uses mlx-community/c4ai-command-r-v01-4bit for native Mac performance

Differences from mlx_remembr_agent.py:
- _create_prompt includes audio_caption alongside visual caption so the LLM
  can reason about audio observations (sirens, speech, etc.) stored in memory.
"""

import mlx.core as mx
from mlx_lm import load, generate
import json
import re
from typing import Optional, List, Dict, Any
from remembr.memory.memory_multimodal import MemoryItem
from remembr.agents.agent import Agent

class MLXReMEmbRAgent(Agent):
    """MLX-powered ReMEmbR agent with Command-R (multimodal memory)"""

    def __init__(self, model_backend="COMMAND_R", model_name=None):
        """
        Initialize MLX ReMEmbR agent with model backend choice

        Args:
            model_backend: "COMMAND_R" or "GEMMA"
            model_name: Custom model name (overrides backend choice)
        """
        self.model_backend = model_backend.upper()

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

        try:
            self.model, self.tokenizer = load(self.model_name)
            print(f"[MLX] ✓ {self.model_backend} model loaded successfully")
        except Exception as e:
            print(f"[MLX] ❌ Failed to load {self.model_name}: {e}")
            if self.model_backend == "GEMMA":
                print("[MLX] Trying Command-R as fallback...")
                self.model_name = "mlx-community/c4ai-command-r-v01-4bit"
                self.model_backend = "COMMAND_R"
                self.model, self.tokenizer = load(self.model_name)
                print("[MLX] ✓ Fallback to Command-R successful")
            else:
                raise

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

        try:
            relevant_memories = self.memory.search(question, limit=num_memories)

            if not relevant_memories:
                print(f"[MLX] No results for '{question}', trying keyword extraction...")
                keywords = self._extract_keywords(question)
                for keyword in keywords:
                    print(f"[MLX] Trying keyword: '{keyword}'")
                    relevant_memories = self.memory.search(keyword, limit=num_memories)
                    if relevant_memories:
                        print(f"[MLX] Found {len(relevant_memories)} memories with keyword '{keyword}'")
                        break

            print(f"[MLX] Retrieved {len(relevant_memories)} relevant memories")
        except Exception as e:
            print(f"[MLX] Memory search failed: {e}")
            relevant_memories = []

        prompt = self._create_prompt(question, relevant_memories)

        try:
            response_text = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                verbose=False,
                **self.generation_args
            )

            print(f"[MLX] Generated response: {response_text[:100]}...")

            parsed_response = self._parse_response(response_text, question, relevant_memories)

            print(f"[MLX] Parsed response: {parsed_response.text[:100]}...")

            return parsed_response

        except Exception as e:
            print(f"[MLX] Generation failed: {e}")
            return self._create_fallback_response(question)

    def _extract_keywords(self, question: str) -> List[str]:
        """Extract relevant keywords from the question for fallback search"""
        stop_words = {'a', 'an', 'the', 'to', 'where', 'you', 'me', 'take', 'go', 'find',
                      'heard', 'saw', 'there', 'is', 'was', 'were', 'have', 'had'}

        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        variations = []
        for keyword in keywords:
            variations.append(keyword)
            if keyword.endswith('s') and len(keyword) > 3:
                variations.append(keyword[:-1])
            elif not keyword.endswith('s'):
                variations.append(keyword + 's')

        return variations[:5]

    def _format_memory_entry(self, mem: MemoryItem) -> str:
        """Format a single memory item including both visual and audio captions."""
        entry = (
            f"Time {mem.time:.1f}s: At position ({mem.position[0]:.2f}, {mem.position[1]:.2f}), "
            f"facing {mem.theta:.2f} rad"
        )
        if mem.caption:
            entry += f" - Visual: {mem.caption}"
        if mem.audio_caption:
            entry += f" | Audio: {mem.audio_caption}"
        return entry

    def _create_prompt(self, question: str, memories: List[MemoryItem]) -> str:
        """Create a structured prompt including both visual and audio memory context."""

        if memories:
            memory_context = "\n".join([
                self._format_memory_entry(mem) for mem in memories[:10]
            ])
        else:
            memory_context = "No relevant memories found."

        if self.model_backend == "COMMAND_R":
            prompt = f"""<|START_OF_TURN_TOKEN|><|USER_TOKEN|>You are ReMEmbR, an AI assistant that helps robots navigate their environment based on memory.

            ## Robot Memory Context:
            {memory_context}

            ## User Question:
            {question}

            ## Instructions:
            1. If the user asks to go somewhere or find something, provide coordinates in [x, y] format
            2. Choose the most relevant position from the memories above
            3. Consider BOTH visual observations and audio observations when answering
            4. If multiple positions are mentioned, pick the most recent or most relevant one
            5. Your response must be valid JSON

            ## Response Format:
            {{
                "text": "Your helpful response here",
                "position": [x, y] or null,
                "heading": theta_value or null,
                "confidence": 0.0-1.0,
                "reasoning": "Why you chose this position and heading"
            }}

            Respond only with valid JSON.<|END_OF_TURN_TOKEN|><|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>"""

        elif self.model_backend == "GEMMA":
            if self.tokenizer.chat_template is not None:
                messages = [
                    {
                        "role": "user",
                        "content": f"""You are ReMEmbR, an AI assistant that helps robots navigate their environment based on memory.

                        ## Robot Memory Context:
                        {memory_context}

                        ## User Question:
                        {question}

                        ## Instructions:
                        1. If the user asks to go somewhere or find something, provide coordinates in [x, y] format
                        2. Choose the most relevant position from the memories above
                        3. Consider BOTH visual observations and audio observations when answering
                        4. If multiple positions are mentioned, pick the most recent or most relevant one
                        5. Your response must be valid JSON

                        ## Response Format:
                        {{
                            "text": "Your helpful response here",
                            "position": [x, y] or null,
                            "heading": theta_value or null,
                            "confidence": 0.0-1.0,
                            "reasoning": "Why you chose this position and heading"
                        }}

                        Respond only with valid JSON."""
                    }
                ]
                prompt = self.tokenizer.apply_chat_template(
                    messages, add_generation_prompt=True, tokenize=False
                )
            else:
                prompt = f"""You are ReMEmbR, an AI assistant that helps robots navigate their environment based on memory.

                            Robot Memory Context:
                            {memory_context}

                            User Question: {question}

                            Instructions:
                            1. If the user asks to go somewhere or find something, provide coordinates in [x, y] format
                            2. Choose the most relevant position from the memories above
                            3. Consider BOTH visual and audio observations when answering
                            4. Your response must be valid JSON

                            Response Format:
                            {{"text": "Your helpful response here", "position": [x, y] or null, "heading": theta_value or null, "confidence": 0.0-1.0, "reasoning": "Why you chose this position and heading"}}

                            JSON Response:"""

        return prompt

    def _parse_response(self, response_text: str, question: str, memories: List[MemoryItem]):
        """Parse the model's response with enhanced position extraction"""
        try:
            response_text = response_text.strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            try:
                parsed = json.loads(response_text)

                position = parsed.get("position")
                heading = parsed.get("heading")

                if position and isinstance(position, list) and len(position) >= 2:
                    if all(isinstance(x, (int, float)) and x is not None for x in position[:2]):
                        final_position = [float(position[0]), float(position[1])]
                    else:
                        final_position = self._extract_position_from_memories(question, memories)
                else:
                    final_position = self._extract_position_from_memories(question, memories)

                if heading is not None and isinstance(heading, (int, float)):
                    final_heading = float(heading)
                else:
                    final_heading = self._extract_heading_from_memories(question, memories)

                return AgentResponse(
                    text=parsed.get("text", response_text),
                    position=final_position,
                    heading=final_heading,
                    confidence=parsed.get("confidence", 0.7),
                    reasoning=parsed.get("reasoning", "MLX Command-R analysis")
                )

            except json.JSONDecodeError:
                print(f"[MLX] JSON decode failed, trying alternative parsing...")
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

    def _extract_heading_from_memories(self, question: str, memories: List[MemoryItem]):
        """Extract the most relevant heading from memories"""
        if not memories:
            return None
        best_memory = memories[0]
        return float(best_memory.theta) if best_memory.theta is not None else None

    def _extract_position_from_memories(self, question: str, memories: List[MemoryItem]):
        """Extract the most relevant position from memories based on the question"""
        if not memories:
            return None
        best_memory = memories[0]
        if best_memory.position and len(best_memory.position) >= 2:
            return [float(best_memory.position[0]), float(best_memory.position[1])]
        return None

    def _extract_position_from_text(self, text: str, memories: List[MemoryItem]):
        """Try to extract position coordinates from response text"""
        try:
            coord_patterns = [
                r'\[(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\]',
                r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)',
                r'position\s+(-?\d+\.?\d*),\s*(-?\d+\.?\d*)',
            ]

            for pattern in coord_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    x, y = matches[0]
                    return [float(x), float(y)]

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
    def __init__(self, text: str, position=None, heading=None, confidence: float = 0.5, reasoning: str = ""):
        self.text = text
        self.position = position
        self.heading = heading
        self.confidence = confidence
        self.reasoning = reasoning
        self.time = None
