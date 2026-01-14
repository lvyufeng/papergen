"""Brainstorm module for generating novel research ideas using multiple LLMs."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from ..ai.claude_client import ClaudeClient
from ..ai.multi_llm import MultiLLMManager, LLMConfig, LLMResponse
from ..core.logging_config import get_logger


@dataclass
class BrainstormReport:
    """Report from a single LLM's brainstorming."""
    provider: str
    model: str
    ideas: List[Dict[str, Any]]
    raw_response: str


class IdeaGenerator:
    """Generates and evaluates novel research ideas using multiple LLMs."""

    def __init__(self, use_multi_llm: bool = False):
        """Initialize idea generator."""
        self.logger = get_logger()
        self.use_multi_llm = use_multi_llm
        self.client = ClaudeClient()
        self.multi_llm: Optional[MultiLLMManager] = None
        self.ideas: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.reports: List[BrainstormReport] = []
        self.summary: Dict[str, Any] = {}

        if use_multi_llm:
            self.multi_llm = MultiLLMManager.from_env()

    def set_context(
        self,
        topic: str,
        research_gaps: List[Dict],
        paper_weaknesses: List[str],
        future_directions: List[Dict]
    ):
        """Set research context for brainstorming."""
        self.context = {
            "topic": topic,
            "gaps": research_gaps,
            "weaknesses": paper_weaknesses,
            "directions": future_directions
        }

    def generate_ideas(self, num_ideas: int = 5) -> List[Dict[str, Any]]:
        """
        Generate novel research ideas based on context.

        Args:
            num_ideas: Number of ideas to generate per LLM

        Returns:
            List of research ideas with details
        """
        if self.use_multi_llm and self.multi_llm:
            return self._generate_multi_llm(num_ideas)
        else:
            return self._generate_single_llm(num_ideas)

    def _get_brainstorm_system(self) -> str:
        """Get system prompt for brainstorming."""
        return """You are a brilliant research advisor at a top university, helping a postgraduate student brainstorm novel research ideas for top-tier AI conferences (ACL, EMNLP, NeurIPS, ICML, AAAI, IJCAI).

Your ideas should be:
1. NOVEL - Not just incremental improvements
2. FEASIBLE - Achievable by a master's student in 6-12 months
3. IMPACTFUL - Address real problems with clear contributions
4. PUBLISHABLE - Suitable for top venues

Think creatively! Combine ideas from different areas, challenge assumptions, find overlooked problems."""

    def _build_brainstorm_prompt(self, num_ideas: int) -> str:
        """Build brainstorming prompt."""
        gaps_text = "\n".join([f"- {g.get('gap', g)}" for g in self.context.get('gaps', [])])
        weaknesses_text = "\n".join([f"- {w}" for w in self.context.get('weaknesses', [])])
        directions_text = "\n".join([f"- {d.get('direction', d)}" for d in self.context.get('directions', [])])

        return f"""Research Topic: {self.context.get('topic', 'AI Research')}

Research Gaps Identified:
{gaps_text}

Weaknesses in Current Methods:
{weaknesses_text}

Promising Future Directions:
{directions_text}

Generate {num_ideas} novel research ideas. For each idea, provide JSON:
{{
    "ideas": [
        {{
            "title": "Catchy paper title",
            "one_sentence": "One sentence summary",
            "problem": "What problem does it solve?",
            "novelty": "What's new about this approach?",
            "method_sketch": "Brief method description",
            "expected_contribution": "What will this contribute?",
            "feasibility": "high/medium/low",
            "required_resources": ["GPU", "dataset", etc.],
            "potential_venues": ["ACL", "NeurIPS", etc.],
            "risks": ["risk1", "risk2"],
            "first_steps": ["step1", "step2", "step3"]
        }}
    ]
}}"""

    def _parse_ideas(self, response: str) -> List[Dict[str, Any]]:
        """Parse ideas from AI response."""
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("ideas", [data])
            return []
        except json.JSONDecodeError:
            return [{"raw_response": response}]

    def evaluate_idea(self, idea_index: int) -> Dict[str, Any]:
        """Evaluate feasibility of a specific idea."""
        if idea_index >= len(self.ideas):
            return {"error": "Invalid idea index"}

        idea = self.ideas[idea_index]
        prompt = f"""Evaluate this research idea critically:

Title: {idea.get('title')}
Problem: {idea.get('problem')}
Method: {idea.get('method_sketch')}

Provide evaluation:
1. Novelty score (1-10)
2. Feasibility score (1-10)
3. Impact score (1-10)
4. Main challenges
5. Suggestions to strengthen"""

        response = self.client.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.3
        )
        return {"idea": idea, "evaluation": response}

    def _generate_single_llm(self, num_ideas: int) -> List[Dict[str, Any]]:
        """Generate ideas using single LLM."""
        self.logger.info(f"Generating {num_ideas} ideas with single LLM")

        prompt = self._build_brainstorm_prompt(num_ideas)
        system = self._get_brainstorm_system()

        response = self.client.generate(
            prompt=prompt,
            system=system,
            max_tokens=8000,
            temperature=0.8
        )

        self.ideas = self._parse_ideas(response)
        return self.ideas

    def _generate_multi_llm(self, num_ideas: int) -> List[Dict[str, Any]]:
        """Generate ideas using multiple LLMs in parallel."""
        self.logger.info(f"Generating ideas with multiple LLMs")

        prompt = self._build_brainstorm_prompt(num_ideas)
        system = self._get_brainstorm_system()

        # Generate from all LLMs
        responses = self.multi_llm.generate_parallel(
            prompt=prompt,
            system=system,
            max_tokens=8000,
            temperature=0.8
        )

        # Process each response
        self.reports = []
        all_ideas = []

        for resp in responses:
            if resp.success:
                ideas = self._parse_ideas(resp.content)
                report = BrainstormReport(
                    provider=resp.provider,
                    model=resp.model,
                    ideas=ideas,
                    raw_response=resp.content
                )
                self.reports.append(report)
                all_ideas.extend(ideas)

        # Summarize all ideas
        self.summary = self._summarize_ideas(all_ideas)
        self.ideas = self.summary.get("unique_ideas", all_ideas)

        return self.ideas

    def _summarize_ideas(self, all_ideas: List[Dict]) -> Dict[str, Any]:
        """Summarize and deduplicate ideas from multiple LLMs."""
        if not all_ideas:
            return {"unique_ideas": [], "summary": "No ideas generated"}

        # Build summary prompt
        ideas_text = json.dumps(all_ideas, indent=2, ensure_ascii=False)
        prompt = f"""Analyze these research ideas from multiple AI models:

{ideas_text}

Tasks:
1. Identify unique ideas (remove duplicates/similar ones)
2. Rank by novelty and feasibility
3. Highlight consensus ideas (mentioned by multiple models)
4. Note unique perspectives from each model

Output JSON:
{{
    "unique_ideas": [...],
    "consensus_themes": [...],
    "top_recommendations": [...],
    "summary": "Brief analysis"
}}"""

        response = self.client.generate(
            prompt=prompt,
            system="You are a research advisor summarizing ideas.",
            max_tokens=8000,
            temperature=0.3
        )

        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        return {"unique_ideas": all_ideas, "summary": response}

    def get_reports(self) -> List[BrainstormReport]:
        """Get individual reports from each LLM."""
        return self.reports

    def get_summary(self) -> Dict[str, Any]:
        """Get the summarized ideas."""
        return self.summary
