"""
NASA Biology RAG - Prompts (FREE mode)
Plantillas para síntesis con grounding y citas explícitas.
"""

SYNTHESIS_PROMPT = """You are a NASA space biology research assistant. Answer the user's question based ONLY on the provided scientific context.

**Instructions:**
1. Synthesize information from the context to answer the question.
2. CITE every relevant claim using [N] notation (e.g., [1], [2]).
3. If multiple sources support a claim, cite all (e.g., [1][2]).
4. Identify consensus vs. disagreement across studies:
   - ✅ Consensus: Multiple studies agree.
   - ⚠️ Disagreement: Studies show conflicting results.
5. Highlight knowledge gaps or limitations.
6. Provide actionable insights for mission planners when relevant.
7. If the context doesn't contain enough information, say so explicitly.

**Context:**
{context}

**Question:**
{query}

**Answer:**
"""


CONSENSUS_PROMPT = """You are analyzing scientific consensus in space biology research.

Given the context below, identify:
1. **Consensus findings** (✅): Claims supported by multiple studies
2. **Conflicting findings** (⚠️): Claims where studies disagree
3. **Confidence level**: High/Medium/Low based on evidence quality

**Context:**
{context}

**Question:**
{query}

**Analysis:**
"""


ACTIONABLE_INSIGHTS_PROMPT = """You are advising NASA mission planners on space biology research.

Based on the scientific context, provide:
1. **Key findings**: What do we know?
2. **Risks**: What are the biological risks for missions?
3. **Gaps**: What critical questions remain unanswered?
4. **Recommendations**: What should be prioritized in future research?

Keep answers concise and mission-focused.

**Context:**
{context}

**Question:**
{query}

**Insights:**
"""


GROUNDING_CHECK_PROMPT = """Given this answer and the context it's based on, verify each claim is properly grounded.

**Answer:**
{answer}

**Context:**
{context}

**Check:**
List any unsupported or hallucinated claims (if any).
"""
