"""
Design Agent Module for InterioOS AI.

This module forms the Design Agent component of the InterioOS AI multi-agent interior design system.
It takes client design requirements and communicates with the Claude API (Anthropic) to produce
structured, professional interior design concepts.

Author: InterioOS AI Team (Member 1 - Design Agent)
"""

import logging
import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import anthropic

# Configure module logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Automatically load environment variables from .env if available
load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


class DesignAgent:
    """
    DesignAgent encapsulates state and logic for generating interior design concepts via Claude API.

    Attributes:
        api_key (Optional[str]): Anthropic API key used for authentication.
        model (str): Model name for the Claude API request.
        latest_concept (Optional[str]): The most recently generated interior design concept text.
        last_requirement (Optional[str]): The requirement prompt passed during the last generation.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        """
        Initialize the DesignAgent with optional API key and model selection.

        Args:
            api_key: Optional API key. If not provided, resolves from ANTHROPIC_API_KEY env var.
            model: Anthropic model identifier. Defaults to ANTHROPIC_MODEL env var or claude-3-5-sonnet-20241022.
        """
        self.api_key: Optional[str] = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model: str = model
        self.latest_concept: Optional[str] = None
        self.last_requirement: Optional[str] = None
        self._client: Optional[anthropic.Anthropic] = None

        if self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        else:
            logger.warning(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "API calls will require explicit key initialization or set env variable."
            )

    def _get_client(self) -> anthropic.Anthropic:
        """
        Retrieve or initialize the Anthropic client, checking for API key presence.

        Returns:
            anthropic.Anthropic: Configured client instance.

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set or accessible.
        """
        if self._client:
            return self._client

        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY missing. Please set ANTHROPIC_API_KEY in your environment or .env file."
            )

        self.api_key = api_key
        self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _construct_prompt(self, requirement: str) -> tuple[str, str]:
        """
        Construct system and user messages tailored for an interior design expert.

        Args:
            requirement: Raw client requirement text.

        Returns:
            Tuple containing (system_prompt, user_prompt).
        """
        system_prompt = (
            "You are an expert Lead Interior Designer for InterioOS AI, a multi-agent interior design platform. "
            "Your objective is to craft comprehensive, inspirational, and architecturally sound interior design concepts "
            "tailored to client requirements.\n\n"
            "Structure your output cleanly using clear Markdown formatting with the following sections:\n"
            "1. **Concept Summary & Visual Theme**: Architectural style, mood, aesthetic direction.\n"
            "2. **Color Palette & Material Specification**: Walls, floors, accents, textures, fabrics.\n"
            "3. **Spatial Layout & Functionality**: Zoning, traffic flow, ergonomics, furniture arrangement.\n"
            "4. **Lighting Strategy**: Natural lighting optimization, ambient, task, and accent fixtures.\n"
            "5. **Key Furniture & Statement Pieces**: Custom built-ins, loose furniture, accent items.\n"
            "6. **Decor & Styling Details**: Art, greenery, drapery, hardware finishes.\n"
            "7. **Practical & Technical Notes**: Sustainability, acoustics, storage solutions, durability.\n"
        )

        user_prompt = (
            f"Client Design Requirement:\n"
            f"\"\"\"\n{requirement.strip()}\n\"\"\"\n\n"
            "Please generate a complete, highly detailed interior design concept based on the requirements above."
        )

        return system_prompt, user_prompt

    def generate_design_concept(self, requirement: str) -> str:
        """
        Generate an interior design concept based on user requirements.

        Args:
            requirement: User input specifying interior design needs, preferences, and constraints.

        Returns:
            str: Generated design concept output from Claude.

        Raises:
            ValueError: If input requirement is blank or API key is missing.
            RuntimeError: If API communication fails or error occurs during processing.
        """
        if not requirement or not requirement.strip():
            raise ValueError("Requirement string cannot be empty or whitespace.")

        client = self._get_client()
        system_prompt, user_prompt = self._construct_prompt(requirement)

        logger.info("Initiating request to Claude API for design concept generation...")

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract response text content blocks
            concept_parts = []
            for block in response.content:
                if block.type == "text":
                    concept_parts.append(block.text)

            generated_concept = "".join(concept_parts).strip()

            # Save in internal agent state for downstream inter-agent access
            self.last_requirement = requirement
            self.latest_concept = generated_concept

            logger.info("Successfully received and stored design concept from Claude API.")
            return generated_concept

        except anthropic.APIConnectionError as e:
            logger.error(f"Failed to connect to Anthropic API: {e}")
            raise RuntimeError(f"Connection error to Claude API: {e}") from e
        except anthropic.APIStatusError as e:
            logger.error(f"Anthropic API returned error status [{e.status_code}]: {e.response}")
            raise RuntimeError(f"Claude API HTTP Error {e.status_code}: {e.message}") from e
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Claude API error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error generating design concept: {e}")
            raise RuntimeError(f"An unexpected error occurred: {e}") from e

    def get_state(self) -> Dict[str, Any]:
        """
        Retrieve current agent state dictionary for integration with other InterioOS AI agents.

        Returns:
            Dict containing requirement, latest_concept, and model info.
        """
        return {
            "last_requirement": self.last_requirement,
            "latest_concept": self.latest_concept,
            "model": self.model,
            "is_ready": self.latest_concept is not None,
        }


# Module-level singleton agent instance for standard functional access
_agent_instance: Optional[DesignAgent] = None


def generate_design_concept(requirement: str) -> str:
    """
    Top-level module function to generate an interior design concept.

    Convenience wrapper around DesignAgent.generate_design_concept.
    Maintains persistent agent state in module scope for downstream inter-agent use.

    Args:
        requirement: The user's interior design requirement description.

    Returns:
        str: Generated interior design concept.
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = DesignAgent()

    return _agent_instance.generate_design_concept(requirement)


if __name__ == "__main__":
    import sys

    print("InterioOS AI - Design Agent Test Run")
    test_req = (
        "Modern Japandi style living room for a 300 sq ft space with high ceilings. "
        "Needs neutral tones, natural wood accents, warm indirect lighting, and a cozy reading nook."
    )

    api_key_env = os.getenv("ANTHROPIC_API_KEY")
    if not api_key_env:
        print("[WARNING] ANTHROPIC_API_KEY not found in environment or .env file.")
        print("Please configure ANTHROPIC_API_KEY in .env before executing live API requests.")
        sys.exit(1)

    try:
        print(f"\nGenerating design concept for test requirement:\n'{test_req}'\n")
        concept = generate_design_concept(test_req)
        print("--- Generated Design Concept ---")
        print(concept)
    except Exception as err:
        print(f"[ERROR] Design concept generation failed: {err}")
