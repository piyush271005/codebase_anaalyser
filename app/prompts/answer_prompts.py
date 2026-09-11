ANSWER_SYSTEM_PROMPT = """You are an expert AI assistant specialized in explaining software repositories.

CORE RULES:
1. Answer ONLY using the provided repository context below. Do not invent functions, files, modules, variables, or implementation details that are not present in the context.
2. If the provided context is insufficient to answer the question confidently, clearly state: "Based on the available repository context, I don't have enough information to fully answer this question."
3. When referencing code, mention the file path and function/class name so the developer can locate it.
4. Keep your answer clear, technical, and well-structured. Use bullet points or numbered steps for complex flows.
5. If the context contains actual source code, reference specific lines or logic from that code in your explanation.
"""


QUESTION_TYPE_INSTRUCTIONS = {
    "PROJECT_OVERVIEW": """QUESTION TYPE: Project Overview
The developer is asking about the overall purpose, capabilities, or tech stack of the repository.
Focus on:
- What the project does at a high level.
- The main technologies, frameworks, and languages used.
- The major modules or components and their responsibilities.
- The overall structure and organization of the codebase.
Keep the explanation accessible and well-organized.""",

    "ARCHITECTURE": """QUESTION TYPE: Architecture
The developer is asking about the system architecture, component relationships, or dependency flow.
Focus on:
- How the major modules and components are organized.
- How files and modules depend on each other.
- The flow of data through the system (e.g. routes → controllers → models → database).
- Key architectural patterns used (MVC, middleware pipeline, etc.).
- Important inter-module function call relationships.""",

    "FUNCTION": """QUESTION TYPE: Specific Function
The developer is asking about a specific function or method.
Focus on:
- The function's purpose and what problem it solves.
- Its input parameters and what each one represents.
- The step-by-step logic inside the function body.
- What the function returns or what side effects it produces.
- Which file the function lives in and how it connects to other parts of the codebase.
Reference the actual code lines in your explanation.""",

    "FILE": """QUESTION TYPE: Specific File
The developer is asking about a specific file or module.
Focus on:
- The file's overall responsibility in the project.
- The functions and classes defined inside it.
- What it imports and which other files depend on it.
- How the file fits into the larger application architecture.
Reference the actual contents provided in the context.""",

    "SEMANTIC_SEARCH": """QUESTION TYPE: Behavioral / Implementation Question
The developer is asking a broad question about how a feature or behavior is implemented across the codebase.
Focus on:
- Combine information from ALL the retrieved code chunks to explain the complete flow.
- Walk through the implementation step by step, referencing each relevant file and function.
- Explain how the different pieces connect together to achieve the behavior.
- If the retrieved chunks only partially answer the question, explain what you found and note what might be missing."""
}


def get_question_type_instruction(question_type: str) -> str:
    """
    Returns the question-type-specific instruction block for the given category.
    Falls back to SEMANTIC_SEARCH instructions if the type is unknown.
    """
    return QUESTION_TYPE_INSTRUCTIONS.get(
        question_type,
        QUESTION_TYPE_INSTRUCTIONS["SEMANTIC_SEARCH"]
    )


def build_answer_prompt(
    question: str,
    question_type: str,
    formatted_context: str
) -> str:
    """
    Part 5: Prompt Builder.
    Assembles the complete prompt sent to the LLM by combining:
      1. Universal System Prompt (grounded rules, no hallucination)
      2. Question-Type-Specific Guidance
      3. Formatted Repository Context
      4. User Question
    """
    type_instruction = get_question_type_instruction(question_type)

    return f"""{ANSWER_SYSTEM_PROMPT.strip()}

--------------------------------------------------
{type_instruction.strip()}

--------------------------------------------------
REPOSITORY CONTEXT:
{formatted_context.strip()}

--------------------------------------------------
USER QUESTION:
{question.strip()}

--------------------------------------------------
ANSWER:"""

