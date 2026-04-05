"""
app/agents/smart_router.py
══════════════════════════════════════════════════════════════════════
SMART ROUTER — 1 Head Agent + 20 Specialized Agents

HOW IT WORKS (beginner explanation):
─────────────────────────────────────
1. User picks a task card (e.g. "Build a Business Plan") OR types freely
2. HEAD ROUTER AGENT reads the request → decides which specialist to use
3. SPECIALIST AGENT executes the task with deep domain expertise
4. Returns a structured, professional output

THE 20 SPECIALISTS:
 1.  business_plan          → Build a Business Plan
 2.  pitch_deck             → Create Investor Pitch Deck
 3.  market_research        → Deep Market Research
 4.  competitor_analysis    → Competitor Analysis
 5.  product_launch         → Product Launch Plan
 6.  financial_projections  → Financial Projections
 7.  youtube_strategy       → YouTube Content Strategy
 8.  blog_newsletter        → Blog & Newsletter Planning
 9.  social_media           → Social Media Calendar
10.  study_plan             → Study Plan & Exam Prep
11.  career_planning        → Career Planning
12.  research_paper         → Research Paper Outline
13.  client_deliverables    → Client Deliverable Templates
14.  campaign_strategy      → Campaign Strategy
15.  proposal_pricing       → Proposal & Pricing
16.  life_organization      → Life Organization & Goals
17.  travel_planning        → Travel Planning
18.  cooking_planning       → Cooking & Recipe Planning
19.  brainstorm             → Brainstorm Ideas
20.  casual                 → Casual Conversations
"""

import os
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─── All valid agent type keys ────────────────────────────────────────────────
AGENT_TYPES = [
    "business_plan", "pitch_deck", "market_research", "competitor_analysis",
    "product_launch", "financial_projections", "youtube_strategy", "blog_newsletter",
    "social_media", "study_plan", "career_planning", "research_paper",
    "client_deliverables", "campaign_strategy", "proposal_pricing",
    "life_organization", "travel_planning", "cooking_planning", "brainstorm", "casual",
]

# Human-readable labels (used in API responses)
AGENT_LABELS = {
    "business_plan":         "Business Plan Specialist",
    "pitch_deck":            "Investor Pitch Deck Expert",
    "market_research":       "Market Research Analyst",
    "competitor_analysis":   "Competitive Intelligence Analyst",
    "product_launch":        "Product Launch Strategist",
    "financial_projections": "Financial Modeling Expert",
    "youtube_strategy":      "YouTube Content Strategist",
    "blog_newsletter":       "Content Editorial Planner",
    "social_media":          "Social Media Calendar Creator",
    "study_plan":            "Academic Study Planner",
    "career_planning":       "Career Development Coach",
    "research_paper":        "Research Paper Specialist",
    "client_deliverables":   "Agency Deliverables Architect",
    "campaign_strategy":     "Marketing Campaign Strategist",
    "proposal_pricing":      "Freelance Proposal Specialist",
    "life_organization":     "Life Coach & Organization Expert",
    "travel_planning":       "Travel Itinerary Planner",
    "cooking_planning":      "Meal Planning & Recipe Expert",
    "brainstorm":            "Creative Ideation Facilitator",
    "casual":                "Friendly General Assistant",
}


# ─────────────────────────────────────────────────────────────────────────────
# LLM FACTORIES
# ─────────────────────────────────────────────────────────────────────────────

def _fast_llm(temperature: float = 0.0):
    """Cheap & fast — used by the head router for classification only."""
    from crewai import LLM
    return LLM(
        model="openrouter/anthropic/claude-3-haiku",
        temperature=temperature,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def _smart_llm(temperature: float = 0.6):
    """Capable model — used by all specialist agents."""
    from crewai import LLM
    return LLM(
        model="openrouter/anthropic/claude-3-5-sonnet",
        temperature=temperature,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# HEAD ROUTER AGENT
# Its ONLY job: read the task → output one category word
# ─────────────────────────────────────────────────────────────────────────────

def build_head_router_agent():
    from crewai import Agent
    return Agent(
        role="Head AI Agent / Task Router",
        goal=(
            "Analyse the user's request and classify it into exactly ONE of these 20 categories: "
            + ", ".join(AGENT_TYPES) +
            ". Output ONLY the category word — nothing else."
        ),
        backstory=(
            "You are the head orchestrator of a team of 20 AI specialists. "
            "Your only job is to read a user request and instantly identify which specialist "
            "should handle it. You never answer the question — you only route."
        ),
        llm=_fast_llm(temperature=0.0),
        verbose=True,
        allow_delegation=False,
        max_iter=1,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 20 SPECIALIZED AGENTS
# ─────────────────────────────────────────────────────────────────────────────

def build_business_plan_agent():
    from crewai import Agent
    return Agent(
        role="Business Plan Specialist",
        goal=(
            "Create comprehensive, investor-ready business plans covering: executive summary, "
            "problem & solution, market analysis, business model, go-to-market strategy, "
            "financial projections, team, and funding ask. Produce a complete business plan document."
        ),
        backstory=(
            "You are a serial entrepreneur and MBA professor with 15 years building and advising "
            "startups across SaaS, fintech, and consumer sectors. You have written hundreds of "
            "business plans that secured millions in funding from top VCs."
        ),
        llm=_smart_llm(0.6),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_pitch_deck_agent():
    from crewai import Agent
    return Agent(
        role="Investor Pitch Deck Expert",
        goal=(
            "Structure compelling investor pitch decks with: problem, solution, market size (TAM/SAM/SOM), "
            "business model, traction, team, competitive advantage, financials, and ask slides. "
            "Produce pitch deck outline and slide-by-slide content."
        ),
        backstory=(
            "You are a former VC partner turned startup advisor who has reviewed 10,000+ pitch decks "
            "and helped 200+ startups raise Series A and beyond. You know exactly what Sequoia, a16z, "
            "and YC look for."
        ),
        llm=_smart_llm(0.7),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_market_research_agent():
    from crewai import Agent
    return Agent(
        role="Market Research Analyst",
        goal=(
            "Conduct thorough market research covering: market size, growth trends, customer segments, "
            "buying behaviour, key players, regulatory landscape, and opportunity gaps. "
            "Produce a structured research report with actionable insights."
        ),
        backstory=(
            "You are a senior market research analyst with 12 years at top strategy consultancies. "
            "You specialise in TAM/SAM/SOM analysis, primary/secondary research synthesis, "
            "and identifying white-space opportunities across industries."
        ),
        llm=_smart_llm(0.4),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_competitor_analysis_agent():
    from crewai import Agent
    return Agent(
        role="Competitive Intelligence Analyst",
        goal=(
            "Analyse competitors across: features, pricing, positioning, target audience, marketing "
            "channels, strengths, weaknesses, and market share. Produce a comprehensive competitive "
            "intelligence report with strategic recommendations."
        ),
        backstory=(
            "You are a competitive intelligence expert who has built battle cards and competitive "
            "landscapes for Fortune 500 companies and high-growth startups. You use SWOT, Porter's "
            "Five Forces, and positioning maps to deliver sharp, actionable intelligence."
        ),
        llm=_smart_llm(0.4),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_product_launch_agent():
    from crewai import Agent
    return Agent(
        role="Product Launch Strategist",
        goal=(
            "Create comprehensive product launch plans covering: launch goals, target audience, "
            "messaging framework, channel strategy, pre-launch / launch / post-launch timeline, "
            "success metrics, and team checklist. Produce a launch playbook and checklist."
        ),
        backstory=(
            "You are a senior product marketing manager who has launched 50+ products at Apple, "
            "Google, and fast-growing SaaS startups. You turn complex features into compelling "
            "stories and coordinate cross-functional launches flawlessly."
        ),
        llm=_smart_llm(0.6),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_financial_projections_agent():
    from crewai import Agent
    return Agent(
        role="Financial Modeling Expert",
        goal=(
            "Build structured financial models covering: revenue streams, pricing assumptions, "
            "unit economics (CAC, LTV, payback), cost structure, P&L, cash flow, break-even "
            "analysis, and 3-year projections. Produce a financial model structure with key metrics."
        ),
        backstory=(
            "You are a CFA-certified financial analyst specialising in startup financial modelling "
            "and investor-grade projections. You have built models for 100+ companies ranging from "
            "pre-revenue startups to $50M ARR scale-ups."
        ),
        llm=_smart_llm(0.2),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_youtube_strategy_agent():
    from crewai import Agent
    return Agent(
        role="YouTube Content Strategist",
        goal=(
            "Plan YouTube channels with: niche positioning, content pillars, 30-day video calendar, "
            "SEO-optimised titles and descriptions, thumbnail concepts, script outlines, "
            "and growth tactics. Produce a video production pipeline."
        ),
        backstory=(
            "You are a YouTube growth expert who has taken creators from 0 to 1M subscribers. "
            "You understand the algorithm deeply, audience psychology, thumbnail psychology, "
            "and the content formats that convert viewers into loyal subscribers."
        ),
        llm=_smart_llm(0.8),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_blog_newsletter_agent():
    from crewai import Agent
    return Agent(
        role="Content Editorial Planner",
        goal=(
            "Develop editorial calendars for blogs and newsletters covering: content pillars, "
            "audience personas, 30-day topic calendar, article outlines, SEO keywords, "
            "distribution strategy, and growth tactics. Produce an editorial calendar."
        ),
        backstory=(
            "You are a content marketing director who built high-traffic blogs and newsletters "
            "with 100K+ subscribers. You combine SEO strategy, audience psychology, and "
            "storytelling to create content that ranks and retains readers."
        ),
        llm=_smart_llm(0.7),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_social_media_agent():
    from crewai import Agent
    return Agent(
        role="Social Media Calendar Creator",
        goal=(
            "Generate a full month of social media content for Instagram, LinkedIn, Twitter/X, "
            "and TikTok. Cover: post themes, captions, hashtag strategy, optimal posting times, "
            "engagement tactics, and stories/reels ideas. Produce a social media schedule."
        ),
        backstory=(
            "You are a social media strategist managing accounts with 5M+ followers across "
            "multiple brands. You know each platform's algorithm, content formats, and the "
            "viral patterns that drive explosive organic growth."
        ),
        llm=_smart_llm(0.8),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_study_plan_agent():
    from crewai import Agent
    return Agent(
        role="Academic Study Planner",
        goal=(
            "Break down syllabuses into structured daily study plans using: spaced repetition, "
            "active recall, Pomodoro technique, topic prioritisation, revision schedules, "
            "and exam-day strategy. Produce a structured study schedule."
        ),
        backstory=(
            "You are an educational psychologist and academic coach who uses evidence-based "
            "learning science to help students maximise retention and exam performance. "
            "You have helped 500+ students improve grades significantly."
        ),
        llm=_smart_llm(0.5),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_career_planning_agent():
    from crewai import Agent
    return Agent(
        role="Career Development Coach",
        goal=(
            "Map out career paths covering: current skills assessment, target role analysis, "
            "skill gap identification, 90-day action plan, resume optimisation tips, "
            "LinkedIn strategy, and interview preparation. Produce a career action plan."
        ),
        backstory=(
            "You are a career coach with 15 years helping graduates and mid-career professionals "
            "land roles at Google, McKinsey, Goldman Sachs, and top startups. You combine "
            "industry knowledge with personal branding expertise."
        ),
        llm=_smart_llm(0.6),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_research_paper_agent():
    from crewai import Agent
    return Agent(
        role="Academic Research Paper Specialist",
        goal=(
            "Structure academic papers covering: research question, thesis statement, "
            "literature review framework, methodology section, results structure, "
            "discussion points, and citation strategy. Produce an academic paper framework."
        ),
        backstory=(
            "You are a published researcher and academic writing coach who has supervised "
            "200+ dissertations, journal articles, and conference papers across STEM, "
            "social sciences, and humanities."
        ),
        llm=_smart_llm(0.4),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_client_deliverables_agent():
    from crewai import Agent
    return Agent(
        role="Agency Deliverables Architect",
        goal=(
            "Build standardized client-facing documents including: audit templates, strategy decks, "
            "monthly report structures, SOW templates, onboarding checklists, and delivery SOPs "
            "to scale agency services. Produce standardized SOPs."
        ),
        backstory=(
            "You are an agency operations expert who has scaled delivery systems for digital "
            "marketing, design, and consulting agencies from 5 to 100+ clients without "
            "proportionally scaling headcount."
        ),
        llm=_smart_llm(0.5),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_campaign_strategy_agent():
    from crewai import Agent
    return Agent(
        role="Marketing Campaign Strategist",
        goal=(
            "Develop full-funnel marketing campaigns covering: campaign objectives, audience targeting, "
            "messaging hierarchy, channel mix (paid/organic/email/social), creative briefs, "
            "budget allocation, and measurement framework. Produce a campaign strategy document."
        ),
        backstory=(
            "You are a senior integrated marketing strategist with experience running $10M+ "
            "campaigns for B2B and B2C brands across Google Ads, Meta, LinkedIn, "
            "email, and influencer channels."
        ),
        llm=_smart_llm(0.6),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_proposal_pricing_agent():
    from crewai import Agent
    return Agent(
        role="Freelance Proposal Specialist",
        goal=(
            "Draft compelling client proposals covering: executive summary, problem statement, "
            "proposed solution, scope of work, timeline, deliverables, tiered pricing options, "
            "terms, and call to action. Produce a client proposal document."
        ),
        backstory=(
            "You are a 6-figure freelancer who has crafted 300+ winning proposals across "
            "design, development, consulting, and copywriting. You know how to communicate "
            "value clearly, handle price objections, and close deals."
        ),
        llm=_smart_llm(0.6),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_life_organization_agent():
    from crewai import Agent
    return Agent(
        role="Life Coach & Organization Expert",
        goal=(
            "Create structured personal development systems covering: goal setting (OKRs / SMART goals), "
            "daily routines, weekly reviews, habit stacks, priority frameworks, and "
            "accountability systems. Produce a personal planning system."
        ),
        backstory=(
            "You are a certified life coach and productivity expert blending psychology, "
            "habit science (James Clear, BJ Fogg), and Stoic philosophy to help people "
            "design purposeful, high-performance lives."
        ),
        llm=_smart_llm(0.7),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_travel_planning_agent():
    from crewai import Agent
    return Agent(
        role="Travel Itinerary Planner",
        goal=(
            "Build detailed travel plans covering: day-by-day itinerary, accommodation suggestions, "
            "transportation logistics, must-see + hidden gem experiences, dining recommendations, "
            "packing list, budget breakdown, and safety tips. Produce a complete travel itinerary."
        ),
        backstory=(
            "You are a seasoned travel expert who has visited 80+ countries across 6 continents. "
            "You craft optimised itineraries that perfectly balance landmarks, local culture, "
            "food, and budget for every type of traveller."
        ),
        llm=_smart_llm(0.7),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_cooking_planning_agent():
    from crewai import Agent
    return Agent(
        role="Meal Planning & Recipe Expert",
        goal=(
            "Plan weekly meals based on dietary preferences, allergies, and goals. Cover: "
            "7-day meal plan (breakfast/lunch/dinner/snacks), full grocery list with quantities, "
            "meal prep schedule, nutrition overview, and recipe instructions. "
            "Produce a meal plan and grocery list."
        ),
        backstory=(
            "You are a nutritionist and professional chef who creates delicious, balanced meal plans "
            "for clients ranging from athletes to busy families, tailored to dietary needs "
            "(keto, vegan, Mediterranean, etc.) and budget."
        ),
        llm=_smart_llm(0.7),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_brainstorm_agent():
    from crewai import Agent
    return Agent(
        role="Creative Ideation Facilitator",
        goal=(
            "Generate and validate ideas using structured frameworks: SCAMPER, mind mapping, "
            "lateral thinking, reverse brainstorming, and feasibility scoring. "
            "Produce a validated idea framework with prioritized concepts."
        ),
        backstory=(
            "You are a design thinking expert and innovation consultant who has facilitated "
            "brainstorming sessions for Google, IDEO, and 100+ startups. You generate "
            "both wild creative ideas and practical, implementable concepts."
        ),
        llm=_smart_llm(0.9),
        verbose=True, allow_delegation=False, max_iter=5,
    )


def build_casual_agent():
    from crewai import Agent
    return Agent(
        role="Friendly General Assistant",
        goal=(
            "Have thoughtful conversations, provide quick accurate answers, help think through "
            "everyday decisions, and give honest balanced opinions. Provide clear, concise answers."
        ),
        backstory=(
            "You are a knowledgeable, warm, and witty conversationalist with broad expertise. "
            "You give honest, balanced answers on any topic and admit uncertainty clearly "
            "rather than making things up."
        ),
        llm=_smart_llm(0.8),
        verbose=True, allow_delegation=False, max_iter=3,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGENT REGISTRY — maps agent_type key → builder function
# ─────────────────────────────────────────────────────────────────────────────

AGENT_REGISTRY = {
    "business_plan":         build_business_plan_agent,
    "pitch_deck":            build_pitch_deck_agent,
    "market_research":       build_market_research_agent,
    "competitor_analysis":   build_competitor_analysis_agent,
    "product_launch":        build_product_launch_agent,
    "financial_projections": build_financial_projections_agent,
    "youtube_strategy":      build_youtube_strategy_agent,
    "blog_newsletter":       build_blog_newsletter_agent,
    "social_media":          build_social_media_agent,
    "study_plan":            build_study_plan_agent,
    "career_planning":       build_career_planning_agent,
    "research_paper":        build_research_paper_agent,
    "client_deliverables":   build_client_deliverables_agent,
    "campaign_strategy":     build_campaign_strategy_agent,
    "proposal_pricing":      build_proposal_pricing_agent,
    "life_organization":     build_life_organization_agent,
    "travel_planning":       build_travel_planning_agent,
    "cooking_planning":      build_cooking_planning_agent,
    "brainstorm":            build_brainstorm_agent,
    "casual":                build_casual_agent,
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — called by background task executor
# ─────────────────────────────────────────────────────────────────────────────

def run_smart_router(task: str, agent_type: Optional[str] = None) -> dict:
    """
    STEP-BY-STEP (what happens when you call this):

    Step 1 → If agent_type is provided and valid → skip routing, use it directly
    Step 2 → Otherwise → Head Router Agent reads the task and classifies it
    Step 3 → The chosen Specialist Agent executes the task
    Step 4 → Returns { task, agent_type, agent_label, result }

    Args:
        task       : The user's natural-language task description
        agent_type : Optional. One of AGENT_TYPES. If provided, skips head router.

    Returns:
        dict with keys: task, agent_type, agent_label, result
    """
    from crewai import Crew, Process, Task

    logger.info("smart_router_start", task=task[:120], agent_type=agent_type)

    # ── Step 1: Determine which specialist to use ─────────────────────────
    if agent_type and agent_type in AGENT_REGISTRY:
        chosen_type = agent_type
        logger.info("agent_type_direct", chosen_type=chosen_type)
    else:
        # Run Head Router Agent for classification
        router = build_head_router_agent()
        classify_task = Task(
            description=(
                f"Classify the following user request into exactly ONE category.\n\n"
                f"Valid categories: {', '.join(AGENT_TYPES)}\n\n"
                f"User request:\n{task}\n\n"
                "Rules:\n"
                "- Output ONLY the category name\n"
                "- No explanation, no punctuation, no extra words\n"
                "- If unsure, output: casual"
            ),
            expected_output=f"Exactly one word from: {', '.join(AGENT_TYPES)}",
            agent=router,
        )
        classify_crew = Crew(
            agents=[router],
            tasks=[classify_task],
            process=Process.sequential,
            verbose=True,
        )
        classify_result = classify_crew.kickoff()
        raw = str(classify_result).strip().lower().split()[0].rstrip(".,;:")
        chosen_type = raw if raw in AGENT_REGISTRY else "casual"
        logger.info("classified", chosen_type=chosen_type)

    # ── Step 2: Run the chosen Specialist Agent ───────────────────────────
    specialist = AGENT_REGISTRY[chosen_type]()
    answer_task = Task(
        description=(
            f"Complete the following task thoroughly and professionally.\n\n"
            f"TASK:\n{task}\n\n"
            "Guidelines:\n"
            "- Be detailed and actionable\n"
            "- Use headers, bullet points, and structure for clarity\n"
            "- Tailor your response to your specialist domain\n"
            "- Provide concrete examples and next steps where relevant"
        ),
        expected_output=(
            "A comprehensive, well-structured, actionable response that fully "
            "addresses the user's request with practical detail."
        ),
        agent=specialist,
    )
    answer_crew = Crew(
        agents=[specialist],
        tasks=[answer_task],
        process=Process.sequential,
        verbose=True,
    )
    result = answer_crew.kickoff()

    logger.info("smart_router_done", agent_type=chosen_type)
    return {
        "task":        task,
        "agent_type":  chosen_type,
        "agent_label": AGENT_LABELS.get(chosen_type, chosen_type),
        "result":      str(result),
    }
