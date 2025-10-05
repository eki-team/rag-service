# NASA Biology RAG - Prompts Module

SYNTHESIS_PROMPT = """You are a NASA space biology research assistant. Answer the user question based ONLY on the provided scientific context.

Instructions:
- Provide a clear, structured answer
- Cite sources using [N] format (e.g., [1], [2])
- Only use information from the provided context
- If the context doesn't contain enough information, say so clearly
- Use technical language when appropriate
- Include relevant details like species, conditions, or measurements

Context: {context}
Question: {query}
"""

CONSENSUS_ANALYSIS_PROMPT = """Analyze the following research findings for consensus and conflicts.

Instructions:
1. Identify areas of scientific agreement across sources.
2. Note any contradictory findings.
3. Assess confidence levels based on study quality.
4. Provide a balanced synthesis without formatting decorations.

Research Findings: {findings}
"""

ACTIONABLE_INSIGHTS_PROMPT = """Based on the research context, provide practical insights for space biology research.

Instructions:
1. Focus on research gaps and opportunities.
2. Suggest specific experimental approaches.
3. Highlight safety considerations for space environments.
4. Keep recommendations concrete and evidence-based.

Context: {context}
Research Question: {query}
"""

QUESTION_GENERATION_PROMPT = """Generate relevant follow-up questions based on the research context.

Instructions:
1. Create 3-5 specific research questions.
2. Focus on gaps in current knowledge.
3. Consider practical applications for space missions.
4. Ensure questions are answerable with scientific methods.

Research Context: {context}
Current Question: {query}
"""