"""Seed graph generator.

Builds app/data/graph.json from hand-curated extractions taken from twenty
starter-pack artifacts (eighteen podcasts and two newsletters). Each concept
and trust edge is grounded in a verbatim quote observed in the source text.

We use this so the demo renders a real, dense graph before the LLM extraction
has been wired up against an actual ANTHROPIC_API_KEY. Once
`python -m extraction.run` runs against the full starter pack on a key, this
seed output is replaced.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .build_graph import build_graph, write_graph
from .types import (
    Artifact,
    ArtifactType,
    Concept,
    ConceptMention,
    TrustEdge,
)


# -- Artifacts -------------------------------------------------------------

ARTIFACTS: list[Artifact] = [
    Artifact(
        id="cat-wu",
        title="How Anthropic's product team moves faster than anyone else",
        filename="podcasts/cat-wu.md",
        type=ArtifactType.PODCAST,
        date="2026-04-23",
        word_count=16271,
        guest="Cat Wu",
        tags=["leadership", "ai", "product-management"],
    ),
    Artifact(
        id="nikhyl-singhal-2",
        title="Why half of product managers are in trouble",
        filename="podcasts/nikhyl-singhal-2.md",
        type=ArtifactType.PODCAST,
        date="2026-04-19",
        word_count=17206,
        guest="Nikhyl Singhal",
        tags=["product-management", "career", "ai"],
    ),
    Artifact(
        id="amol-avasare",
        title="How Claude became the fastest-growing AI product in history",
        filename="podcasts/amol-avasare.md",
        type=ArtifactType.PODCAST,
        date="2026-04-05",
        word_count=22125,
        guest="Amol Avasare",
        tags=["growth", "ai", "pricing"],
    ),
    Artifact(
        id="evan-spiegel",
        title="Why distribution has become the most important moat",
        filename="podcasts/evan-spiegel.md",
        type=ArtifactType.PODCAST,
        date="2026-04-26",
        word_count=14177,
        guest="Evan Spiegel",
        tags=["b2c", "strategy", "go-to-market"],
    ),
    Artifact(
        id="lazar-jovanovic",
        title="The rise of the professional vibe coder",
        filename="podcasts/lazar-jovanovic.md",
        type=ArtifactType.PODCAST,
        date="2026-02-08",
        word_count=18493,
        guest="Lazar Jovanovic",
        tags=["ai", "engineering", "career"],
    ),
    Artifact(
        id="simon-willison",
        title="An AI state of the union: passed the inflection point",
        filename="podcasts/simon-willison.md",
        type=ArtifactType.PODCAST,
        date="2026-04-02",
        word_count=21276,
        guest="Simon Willison",
        tags=["ai", "engineering"],
    ),
    Artifact(
        id="marc-andreessen",
        title="The real AI boom hasn't even started yet",
        filename="podcasts/marc-andreessen.md",
        type=ArtifactType.PODCAST,
        date="2026-01-29",
        word_count=23012,
        guest="Marc Andreessen",
        tags=["ai", "startups", "leadership"],
    ),
    Artifact(
        id="zevi-arnovitz",
        title="The non-technical PM's guide to building with Cursor",
        filename="podcasts/zevi-arnovitz.md",
        type=ArtifactType.PODCAST,
        date="2026-01-18",
        word_count=15000,
        guest="Zevi Arnovitz",
        tags=["ai", "product-management"],
    ),
    Artifact(
        id="hamel-husain--shreya-shankar",
        title="Why AI evals are the hottest new skill for product builders",
        filename="podcasts/hamel-husain--shreya-shankar.md",
        type=ArtifactType.PODCAST,
        date="2025-09-25",
        word_count=19671,
        guest="Hamel Husain & Shreya Shankar",
        tags=["ai", "analytics"],
    ),
    Artifact(
        id="brendan-foody",
        title="Why experts writing AI evals is creating the fastest-growing companies",
        filename="podcasts/brendan-foody.md",
        type=ArtifactType.PODCAST,
        date="2025-09-18",
        word_count=12143,
        guest="Brendan Foody",
        tags=["ai", "strategy"],
    ),
    Artifact(
        id="aishwarya--kiriti",
        title="Building an actionable feedback loop for AI products",
        filename="podcasts/aishwarya-naresh-reganti--kiriti-badam.md",
        type=ArtifactType.PODCAST,
        date="2026-01-11",
        word_count=16521,
        guest="Aishwarya Naresh Reganti & Kiriti Badam",
        tags=["ai", "design", "engineering"],
    ),
    Artifact(
        id="chip-huyen",
        title="AI Engineering 101",
        filename="podcasts/chip-huyen.md",
        type=ArtifactType.PODCAST,
        date="2025-10-23",
        word_count=15252,
        guest="Chip Huyen",
        tags=["ai", "engineering", "analytics"],
    ),
    Artifact(
        id="howie-liu",
        title="How we restructured Airtable's entire org for AI",
        filename="podcasts/howie-liu.md",
        type=ArtifactType.PODCAST,
        date="2025-08-31",
        word_count=18139,
        guest="Howie Liu",
        tags=["ai", "leadership", "strategy"],
    ),
    Artifact(
        id="elena-verna-40",
        title="Growth loops, the PMF treadmill, and the rise of the vibe coder",
        filename="podcasts/elena-verna-40.md",
        type=ArtifactType.PODCAST,
        date="2025-12-18",
        word_count=17618,
        guest="Elena Verna",
        tags=["growth", "pricing", "strategy"],
    ),
    Artifact(
        id="albert-cheng",
        title="How to find hidden growth opportunities in your product",
        filename="podcasts/albert-cheng.md",
        type=ArtifactType.PODCAST,
        date="2025-10-05",
        word_count=17236,
        guest="Albert Cheng",
        tags=["growth", "analytics"],
    ),
    Artifact(
        id="scott-wu",
        title="How Devin replaces your junior engineers with AI interns",
        filename="podcasts/scott-wu.md",
        type=ArtifactType.PODCAST,
        date="2025-09-08",
        word_count=19675,
        guest="Scott Wu",
        tags=["ai", "engineering", "startups"],
    ),
    Artifact(
        id="asha-sharma",
        title="Products as organisms, the death of org charts",
        filename="podcasts/asha-sharma.md",
        type=ArtifactType.PODCAST,
        date="2025-08-28",
        word_count=10939,
        guest="Asha Sharma",
        tags=["ai", "leadership"],
    ),
    Artifact(
        id="dr-fei-fei-li",
        title="The Godmother of AI on jobs, robots, and world models",
        filename="podcasts/dr-fei-fei-li.md",
        type=ArtifactType.PODCAST,
        date="2025-11-16",
        word_count=11651,
        guest="Dr. Fei-Fei Li",
        tags=["ai", "strategy", "career"],
    ),
    Artifact(
        id="beyond-vibe-checks",
        title="Beyond vibe checks: A PM's complete guide to evals",
        filename="newsletters/beyond-vibe-checks-a-pms-complete-guide-to-evals.md",
        type=ArtifactType.NEWSLETTER,
        date="2025-04-08",
        word_count=3558,
        subtitle="How to master the emerging skill that can make or break an AI product",
        tags=["ai", "engineering", "analytics"],
    ),
    Artifact(
        id="duolingo-growth",
        title="How Duolingo reignited user growth",
        filename="newsletters/how-duolingo-reignited-user-growth.md",
        type=ArtifactType.NEWSLETTER,
        date="2023-02-28",
        word_count=4812,
        subtitle="The story behind Duolingo's 350% growth acceleration",
        tags=["growth", "analytics"],
    ),
    # -- Round 2: gap-filling additions (non-AI / classic SaaS / hiring / pricing) ----
    Artifact(
        id="eoghan-mccabe",
        title="How Intercom rose from the ashes by betting everything on AI",
        filename="podcasts/eoghan-mccabe.md",
        type=ArtifactType.PODCAST,
        date="2025-08-21",
        word_count=13654,
        guest="Eoghan McCabe",
        tags=["pricing", "b2b", "ai", "leadership"],
    ),
    Artifact(
        id="jason-cohen-stalled-growth",
        title="5 questions to ask when your product stops growing",
        filename="podcasts/jason-cohen.md",
        type=ArtifactType.PODCAST,
        date="2026-01-25",
        word_count=21677,
        guest="Jason Cohen",
        tags=["growth", "pricing", "startups"],
    ),
    Artifact(
        id="grant-lee",
        title="\"Dumbest idea I've heard\" to $100M ARR: Inside the rise of Gamma",
        filename="podcasts/grant-lee.md",
        type=ArtifactType.PODCAST,
        date="2025-11-13",
        word_count=24649,
        guest="Grant Lee",
        tags=["startups", "growth", "go-to-market"],
    ),
    Artifact(
        id="brian-halligan",
        title="Sequoia CEO coach: Why it's never been easier to start a company, and never been harder to scale one",
        filename="podcasts/brian-halligan.md",
        type=ArtifactType.PODCAST,
        date="2026-02-15",
        word_count=14680,
        guest="Brian Halligan",
        tags=["leadership", "career", "b2b"],
    ),
    Artifact(
        id="keith-rabois",
        title="Hard truths about building in the AI era",
        filename="podcasts/keith-rabois.md",
        type=ArtifactType.PODCAST,
        date="2026-04-12",
        word_count=15807,
        guest="Keith Rabois",
        tags=["leadership", "career", "startups"],
    ),
    Artifact(
        id="matt-macinnis",
        title="10 contrarian leadership truths every leader needs to hear",
        filename="podcasts/matt-macinnis.md",
        type=ArtifactType.PODCAST,
        date="2025-12-28",
        word_count=18479,
        guest="Matt MacInnis",
        tags=["leadership", "startups", "career"],
    ),
    Artifact(
        id="jason-lemkin",
        title="We replaced our sales team with 20 AI agents - here's what happened",
        filename="podcasts/jason-m-lemkin.md",
        type=ArtifactType.PODCAST,
        date="2026-01-01",
        word_count=26179,
        guest="Jason Lemkin",
        tags=["b2b", "startups", "leadership"],
    ),
    Artifact(
        id="jessica-fain",
        title="The art of influence: The single most important skill that AI can't replace",
        filename="podcasts/jessica-fain.md",
        type=ArtifactType.PODCAST,
        date="2026-03-22",
        word_count=17445,
        guest="Jessica Fain",
        tags=["leadership", "career", "product-management"],
    ),
]


# -- Concepts --------------------------------------------------------------
#
# Defined once and reused across mentions. Each concept's id becomes the
# graph node id (prefixed with "concept:" by build_graph).

def _c(id_: str, name: str, kind: str, one_line: str, aliases: list[str] | None = None) -> Concept:
    return Concept(
        id=f"concept:{id_}",
        canonical_name=name,
        kind=kind,
        one_line=one_line,
        aliases=aliases or [],
    )


CONCEPTS: dict[str, Concept] = {
    c.id: c
    for c in [
        # Core hubs (cross-artifact)
        _c(
            "vibe-coding",
            "Vibe coding",
            "principle",
            "Building software by describing intent to AI without reviewing code, going on the vibes.",
            aliases=["vibe coder", "vibe-coded"],
        ),
        _c(
            "evals",
            "Evals",
            "framework",
            "Structured tests of an AI system's behavior on specific tasks. The PRD of the AI era.",
            aliases=["evaluations", "AI evals"],
        ),
        _c(
            "vibe-check",
            "Vibe check",
            "principle",
            "Informal qualitative judgment of an AI output. Useful early, dangerous as the only signal at scale.",
        ),
        _c(
            "moat",
            "Moat",
            "principle",
            "A durable barrier to competition. In AI, software is no longer the moat; distribution and stickiness are.",
        ),
        _c(
            "distribution-as-moat",
            "Distribution as moat",
            "principle",
            "Where capability gets commoditized, the durable advantage is whether you can reach people at all.",
        ),
        _c(
            "ai-native",
            "AI-native",
            "principle",
            "Building products from a starting assumption that AI is the default substrate, not a feature on top.",
            aliases=["AI-first"],
        ),
        _c(
            "growth-loops",
            "Growth loops",
            "framework",
            "Self-reinforcing cycles where output of one cycle becomes the input of the next. Stand up multiple, do not over-optimize one.",
        ),
        _c(
            "north-star-metric",
            "North star metric",
            "framework",
            "The single number that reflects the value the product is delivering. Drives prioritization across teams.",
            aliases=["north star problem", "north star"],
        ),
        _c(
            "feedback-loop",
            "Feedback loop",
            "framework",
            "An automated or semi-automated cycle where outputs are evaluated and fed back into the system to improve it.",
            aliases=["actionable feedback loop"],
        ),
        _c(
            "agentic",
            "Agentic",
            "principle",
            "AI that takes actions in the world, not just answers questions. Trades off control for capability.",
            aliases=["agentic loop", "agentic systems"],
        ),
        _c(
            "product-market-fit",
            "Product-market fit",
            "framework",
            "The condition where a product satisfies a market. In the AI era, it is no longer a destination but a treadmill.",
            aliases=["PMF"],
        ),
        # Cat Wu specifics
        _c(
            "research-preview",
            "Research preview",
            "principle",
            "Ship features under a research-preview label so the team can move fast without committing to long-term support.",
        ),
        _c(
            "evergreen-launch-room",
            "Evergreen launch room",
            "framework",
            "A standing channel where engineering, docs, marketing, and DevRel coordinate launches in a day instead of a week.",
        ),
        _c(
            "team-principles",
            "Team principles",
            "framework",
            "A written list of who the team's users are and what tradeoffs the team will make, so people decide without escalation.",
        ),
        # Nikhyl Singhal
        _c(
            "the-builders",
            "The builders",
            "principle",
            "PMs whose value is making things, not just shaping things. The next two years reward builders and punish the rest.",
        ),
        _c(
            "pm-slop-cannon",
            "PM slop-cannon",
            "metaphor",
            "A vivid label for the PM whose only output is volume of low-signal artifacts. Used as a warning, not a compliment.",
        ),
        # Amol Avasare
        _c(
            "throw-it-out",
            "Throw it out the door",
            "principle",
            "Operating inside an AI company means 50-70% of how you operated before is no longer load-bearing. Discard it.",
        ),
        # Evan Spiegel
        _c(
            "software-not-a-moat",
            "Software is not a moat",
            "principle",
            "A lesson Snap learned 15 years ago that everyone is rediscovering today with AI. Capability gets copied; distribution does not.",
        ),
        _c(
            "crucible-moment",
            "Crucible moment",
            "metaphor",
            "A defining year where strategic bets harden under pressure. Spiegel's framing for the AI inflection point.",
        ),
        # Lazar Jovanovic
        _c(
            "building-in-public",
            "Building in public",
            "principle",
            "Showing the work as you go, not just the polished output. The path from amateur to hireable in the vibe-coder economy.",
        ),
        # Simon Willison
        _c(
            "harm-no-one-rule",
            "Harm-no-one rule",
            "principle",
            "Vibe code freely when the only person hurt by bugs is you. Take a step back the moment your code touches anyone else.",
        ),
        # Brendan Foody
        _c(
            "eval-is-the-prd",
            "Eval is the PRD",
            "principle",
            "If the model is the product, the eval is the product requirement document. It defines what good looks like.",
        ),
        _c(
            "era-of-evals",
            "Era of evals",
            "principle",
            "The shift from prompt-engineering as the core skill to evaluation-engineering. Every customer is asking for evals.",
        ),
        # Howie Liu
        _c(
            "vibes-before-evals",
            "Vibes before evals",
            "principle",
            "For a novel form factor, start with vibes to find product shape; only then build evals to lock in quality.",
        ),
        # Scott Wu
        _c(
            "stickiness-over-moats",
            "Stickiness over moats",
            "principle",
            "In AI, durable advantage looks less like a moat and more like switching cost and habituation.",
        ),
        # Elena Verna
        _c(
            "pmf-treadmill",
            "PMF treadmill",
            "metaphor",
            "Product-market fit is no longer something you achieve and scale. In AI, you have to recapture it every three months.",
        ),
        _c(
            "adjacent-user-theory",
            "Adjacent user theory",
            "framework",
            "Bangaly Kaba's framework for finding growth: target users who sit just outside your core, with overlapping but not identical needs.",
        ),
        # Albert Cheng / Duolingo
        _c(
            "growth-model",
            "Growth model",
            "framework",
            "A quantitative representation of how a product grows. Surfaces the highest-leverage levers for retention and acquisition.",
        ),
        # Dr. Fei-Fei Li
        _c(
            "north-star-problem",
            "North star problem",
            "framework",
            "A single research problem worth committing a decade to. The forcing function that aligns a long career.",
        ),
        # Marc Andreessen
        _c(
            "ai-boom-hasnt-started",
            "The real AI boom hasn't started",
            "principle",
            "We are still in the pre-deployment phase. The economic transformation comes when the tools reach every workflow, not when they get demoed.",
        ),
        # Aishwarya & Kiriti
        _c(
            "agency-control-tradeoff",
            "Agency-control tradeoff",
            "framework",
            "Every time you hand decision-making to an agentic system, you relinquish control. Build for that explicitly.",
        ),
        # -- Round 2 additions ---------------------------------------------
        # Eoghan McCabe / Intercom
        _c(
            "outcome-based-pricing",
            "Outcome-based pricing",
            "framework",
            "Charge for the outcome the customer gets, not for seats or messages. Aligns vendor incentive with customer success.",
        ),
        _c(
            "beautifully-simple-pricing",
            "Beautifully simple pricing",
            "principle",
            "Madhavan Ramanujam's frame, used by Eoghan McCabe. Simpler, more predictable, fairer pricing makes customers stick around longer.",
        ),
        # Jason Cohen
        _c(
            "prices-too-low",
            "Your prices are too low",
            "principle",
            "Founders guess pricing once and never revisit. Raising prices usually does not move signups; the floor is higher than you think.",
        ),
        _c(
            "onboarding-is-the-bet",
            "Onboarding is the bet",
            "principle",
            "When you do not know what to do to fix growth, work on onboarding. Cancellation concentrates in the first 30 to 90 days.",
        ),
        # Grant Lee / Gamma
        _c(
            "first-30-seconds",
            "First 30 seconds",
            "principle",
            "Make the first 30 seconds of the product feel magical. Onboarding so good that users tell their friends.",
        ),
        _c(
            "hire-painfully-slowly",
            "Hire painfully slowly",
            "principle",
            "Resist the temptation to scale headcount the moment things work. Build a team where every person carries high impact.",
        ),
        # Brian Halligan / HubSpot
        _c(
            "kids-and-adults-table",
            "Kids and adults table",
            "metaphor",
            "Brian Halligan's frame for CEO maturation. Adults talk exec team and org design; kids do not.",
        ),
        _c(
            "blind-references",
            "Blind references",
            "principle",
            "Stop trusting your interview gut. Find someone you know who worked with the candidate and ask if they would enthusiastically rehire.",
        ),
        _c(
            "hire-slow-fire-fast",
            "Hire slow, fire fast",
            "principle",
            "Most founders do the opposite. Half of C-level hires are gone within 18 months.",
        ),
        # Keith Rabois
        _c(
            "value-creation-vs-preservation",
            "Value creation vs preservation",
            "framework",
            "Keith Rabois's hiring prism. For value preservation, experience helps. For value creation, it usually does not.",
        ),
        _c(
            "ceo-counterfactual-question",
            "CEO counterfactual question",
            "principle",
            "Ask senior candidates what they would have done differently if they had been CEO of their last company. Tests strategic editing instinct.",
        ),
        # Matt MacInnis / Rippling
        _c(
            "same-case-study-rubric",
            "Same case study rubric",
            "framework",
            "Give every product candidate at every level the same hard case. The level of the answer reveals seniority better than the resume does.",
        ),
        # Jason Lemkin / SaaStr
        _c(
            "founder-time-budget",
            "Founder time budget",
            "principle",
            "Spend 20% of your time selling and 20% recruiting. Anything less and your calendar dies on you.",
        ),
        _c(
            "pirates-and-romantics",
            "Pirates and romantics",
            "metaphor",
            "Early sales hires should be pirates and romantics, not enablement-team operators. Find the quirky one with extra IQ points who fell in love with the product.",
        ),
        _c(
            "first-ten-determine-dna",
            "First 10 determine DNA",
            "principle",
            "How your first 10 customers buy sets the company's go-to-market DNA. Self-serve first 10 means a self-serve company; high-touch first 10 means an enterprise one.",
        ),
        # Jessica Fain / Webflow
        _c(
            "forget-the-skills-with-execs",
            "Forget the skills with execs",
            "principle",
            "PMs lead with curiosity and empathy for users, then drop both the moment they walk into an exec room. The skill is the same; the audience is not.",
        ),
        _c(
            "executive-calendar-as-stream",
            "Executive's calendar as a stream",
            "metaphor",
            "An exec moves through a stroke-light stream of urgent decisions. Your problem has not had the time, energy, or wherewithal to land in their head yet.",
        ),
    ]
}


# -- Mentions --------------------------------------------------------------
#
# Each tuple is (concept_id, artifact_id, quote). Concept ids must match the
# CONCEPTS dict keys above. Quotes are short verbatim phrases from the source.

_MENTIONS_RAW: list[tuple[str, str, str]] = [
    # cat-wu
    ("concept:research-preview", "cat-wu", "we ship almost all of our features in research preview"),
    ("concept:evergreen-launch-room", "cat-wu", "they post it in our evergreen launch room"),
    ("concept:team-principles", "cat-wu", "we have this list of team principles"),
    ("concept:ai-native", "cat-wu", "extremely important for building AI-native products is iterating so quickly"),
    ("concept:evals", "cat-wu", "evals is this underappreciated thing that more PMs, more engineers should be working on"),
    ("concept:agentic", "cat-wu", "with these agentic tools, not just Claude Code"),
    # nikhyl-singhal-2
    ("concept:ai-native", "nikhyl-singhal-2", "the 8,000 people are going to all be AI first"),
    ("concept:the-builders", "nikhyl-singhal-2", "the builders are going to have the time of their lives"),
    ("concept:pm-slop-cannon", "nikhyl-singhal-2", "PM slop-cannon"),
    # amol-avasare
    ("concept:ai-native", "amol-avasare", "50%, 60%, 70% of how you operate in the past, just throw it out"),
    ("concept:distribution-as-moat", "amol-avasare", "we didn't have the free cash flow or the distribution of a Meta or Google"),
    ("concept:throw-it-out", "amol-avasare", "50%, 60%, 70% of how you operate in the past, just throw it out the door"),
    ("concept:feedback-loop", "amol-avasare", "this is a feedback loop that will accelerate us further and further"),
    ("concept:agentic", "amol-avasare", "agentic coding's a great example. It didn't exist a year and a half ago"),
    # evan-spiegel
    ("concept:moat", "evan-spiegel", "software is not a moat, which is something that everyone is discovering today with AI"),
    ("concept:distribution-as-moat", "evan-spiegel", "distribution is where it ends up being, what ends up being the new moat"),
    ("concept:software-not-a-moat", "evan-spiegel", "software is not a moat, which is something that everyone is discovering today with AI"),
    ("concept:crucible-moment", "evan-spiegel", "you described this coming year as the crucible moment"),
    # lazar-jovanovic
    ("concept:vibe-coding", "lazar-jovanovic", "I'm the first official vibe coding engineer at Lovable"),
    ("concept:building-in-public", "lazar-jovanovic", "it became a job by building in public"),
    # simon-willison
    ("concept:vibe-coding", "simon-willison", "Andrej Karpathy's original definition of vibe coding"),
    ("concept:harm-no-one-rule", "simon-willison", "if you're vibe coding something for yourself where the only person who gets hurt is you, go wild"),
    # marc-andreessen
    ("concept:vibe-coding", "marc-andreessen", "he loves vibe coding. He's on Replit all of the time doing vibe coding"),
    ("concept:moat", "marc-andreessen", "where moats exist in AI"),
    ("concept:ai-boom-hasnt-started", "marc-andreessen", "the real AI boom hasn't even started yet"),
    # zevi-arnovitz
    ("concept:vibe-coding", "zevi-arnovitz", "the most hands-on vibe coding PM I know"),
    # hamel-husain--shreya-shankar
    ("concept:evals", "hamel-husain--shreya-shankar", "evals are becoming the most important new skill for product builders"),
    ("concept:vibe-check", "hamel-husain--shreya-shankar", "vibe checks are good and you should do vibe checks initially, but it can become very unmanageable very fast"),
    # brendan-foody
    ("concept:evals", "brendan-foody", "we are entering the era of evals"),
    ("concept:eval-is-the-prd", "brendan-foody", "if the model is the product, then the eval is the product requirement document"),
    ("concept:era-of-evals", "brendan-foody", "we are entering the era of evals"),
    # aishwarya--kiriti
    ("concept:evals", "aishwarya--kiriti", "PMs should be writing evals, they're the new PRDs"),
    ("concept:feedback-loop", "aishwarya--kiriti", "owning the same feedback loop in a way"),
    ("concept:agentic", "aishwarya--kiriti", "every time you hand over decision-making capabilities to agentic systems"),
    ("concept:agency-control-tradeoff", "aishwarya--kiriti", "the agency control trade-off"),
    # chip-huyen
    ("concept:evals", "chip-huyen", "the goal of eval is to guide the product development"),
    ("concept:vibe-coding", "chip-huyen", "every time you open up one of these vibe coding tools where you could just describe anything you want"),
    ("concept:vibe-check", "chip-huyen", "good enough that you can vibe check it"),
    # howie-liu
    ("concept:evals", "howie-liu", "the power of getting good at evals"),
    ("concept:ai-native", "howie-liu", "in this AI-native world, clearly, you should be able to generate those apps agentically"),
    ("concept:agentic", "howie-liu", "Cursor did a great job of being an early pioneer of this more agentic way"),
    ("concept:vibes-before-evals", "howie-liu", "for a completely novel product experience or form factor, you should actually not start with evals and you should start with vibes"),
    # elena-verna-40
    ("concept:vibe-coding", "elena-verna-40", "everybody and their mother is starting a vibe coding business nowadays"),
    ("concept:growth-loops", "elena-verna-40", "stand up new growth loops one after another"),
    ("concept:north-star-metric", "elena-verna-40", "our North Star is just to get as much usage as possible"),
    ("concept:product-market-fit", "elena-verna-40", "every three months, I feel like we have to recapture our product-market fit"),
    ("concept:pmf-treadmill", "elena-verna-40", "every AI company is on this product-market fit treadmill"),
    ("concept:adjacent-user-theory", "elena-verna-40", "Bangaly wrote a really wonderful article on adjacent user theory"),
    # albert-cheng
    ("concept:growth-model", "albert-cheng", "with growth, you have a growth model, you have metrics, you have experiments"),
    ("concept:north-star-metric", "albert-cheng", "we keep the customer at the North Star of it"),
    # scott-wu
    ("concept:moat", "scott-wu", "I think it's often less about moats and more about stickiness"),
    ("concept:stickiness-over-moats", "scott-wu", "I think it's often less about moats and more about stickiness"),
    ("concept:agentic", "scott-wu", "an agentic loop to really do better on that"),
    ("concept:feedback-loop", "scott-wu", "code has this whole automated feedback loop"),
    # asha-sharma
    ("concept:moat", "asha-sharma", "their big moat is the data that they capture"),
    ("concept:north-star-metric", "asha-sharma", "what is the north star metric is something that we do"),
    # dr-fei-fei-li
    ("concept:north-star-metric", "dr-fei-fei-li", "AI is my north star, is my field's north star"),
    ("concept:north-star-problem", "dr-fei-fei-li", "very committed to a north star problem"),
    # beyond-vibe-checks
    ("concept:evals", "beyond-vibe-checks", "the ability to write great evals isn't just important, it's rapidly becoming the defining skill for AI PMs"),
    ("concept:vibe-check", "beyond-vibe-checks", "you shouldn't let an AI product launch without passing thoughtful, intentional evals"),
    # duolingo-growth
    ("concept:growth-model", "duolingo-growth", "rooted in an innovative growth model"),
    ("concept:north-star-metric", "duolingo-growth", "use Duolingo's data to find a North Star metric"),
    # -- Round 2 mentions -----------------------------------------------------
    # eoghan-mccabe
    ("concept:outcome-based-pricing", "eoghan-mccabe", "outcome-based pricing, which is what you're describing here, where you pay for an outcome"),
    ("concept:beautifully-simple-pricing", "eoghan-mccabe", "beautifully simple pricing is where you want to get to"),
    # jason-cohen-stalled-growth
    ("concept:prices-too-low", "jason-cohen-stalled-growth", "Your prices are way too low because you just guessed and you haven't changed them"),
    ("concept:onboarding-is-the-bet", "jason-cohen-stalled-growth", "if you don't know what to do, onboarding is a good bet"),
    # grant-lee
    ("concept:first-30-seconds", "grant-lee", "make the first 30 seconds of the product feel magical"),
    ("concept:hire-painfully-slowly", "grant-lee", "Hire painfully slowly"),
    # brian-halligan
    ("concept:kids-and-adults-table", "brian-halligan", "the adults are spending half their time just recruiting and interviewing"),
    ("concept:blind-references", "brian-halligan", "everyone dramatically overrates their ability to interview"),
    ("concept:hire-slow-fire-fast", "brian-halligan", "hire slow and fire fast. People hire fast and fire slow"),
    # keith-rabois
    ("concept:value-creation-vs-preservation", "keith-rabois", "are you hiring for value creation or value preservation?"),
    ("concept:ceo-counterfactual-question", "keith-rabois", "If you were CEO, what would you have done differently?"),
    # matt-macinnis
    ("concept:same-case-study-rubric", "matt-macinnis", "every product person at every seniority level is given the same case study"),
    # jason-lemkin
    ("concept:founder-time-budget", "jason-lemkin", "20% of your time in sales and 20% of your time in recruiting"),
    ("concept:pirates-and-romantics", "jason-lemkin", "We're looking for pirates and romantics in the early days"),
    ("concept:first-ten-determine-dna", "jason-lemkin", "if they were able to find you by putting their credit card and no one had to talk to them, then that's your DNA today"),
    # jessica-fain
    ("concept:forget-the-skills-with-execs", "jessica-fain", "the moment that we're talking to an executive, we forget those skills and those talents"),
    ("concept:executive-calendar-as-stream", "jessica-fain", "Describe an executive's calendar as a stroke light going off"),
]


MENTIONS = [
    ConceptMention(concept_id=cid, artifact_id=aid, quote=quote)
    for cid, aid, quote in _MENTIONS_RAW
]


# -- Trust edges -----------------------------------------------------------

TRUST_EDGES: list[TrustEdge] = [
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Nikhyl Singhal",
        artifact_id="nikhyl-singhal-2",
        quote="Nikhyl is, in my opinion, right now, the number one person to learn from on PM craft.",
    ),
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Hamel Husain",
        artifact_id="hamel-husain--shreya-shankar",
        quote="Hamel and Shreya have played a major role in shifting evals from being an obscure, mysterious subject.",
    ),
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Shreya Shankar",
        artifact_id="hamel-husain--shreya-shankar",
        quote="Hamel and Shreya have played a major role in shifting evals from being an obscure, mysterious subject.",
    ),
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Zevi Arnovitz",
        artifact_id="zevi-arnovitz",
        quote="Zevi is the most hands-on vibe coding PM I know, and I've personally learned so much from him.",
    ),
    TrustEdge(
        source_person="Elena Verna",
        target_person="Lazar Jovanovic",
        artifact_id="elena-verna-40",
        quote="my full-time vibe coder, his name is Lazar... he was very early on in the vibe coding wave.",
    ),
    TrustEdge(
        source_person="Simon Willison",
        target_person="Andrej Karpathy",
        artifact_id="simon-willison",
        quote="I like Andrej Karpathy's original definition of vibe coding.",
    ),
    TrustEdge(
        source_person="Howie Liu",
        target_person="Michael Truell",
        artifact_id="howie-liu",
        quote="Cursor did a great job of being an early pioneer of this more agentic way of leveraging the models.",
    ),
    TrustEdge(
        source_person="Elena Verna",
        target_person="Bangaly Kaba",
        artifact_id="elena-verna-40",
        quote="Bangaly wrote a really wonderful article on adjacent user theory.",
    ),
    TrustEdge(
        source_person="Brendan Foody",
        target_person="Sarah Guo",
        artifact_id="brendan-foody",
        quote="Sarah tweeted, evals equals your new marketing.",
    ),
    TrustEdge(
        source_person="Albert Cheng",
        target_person="Jorge Mazal",
        artifact_id="albert-cheng",
        quote="he wrote that very, very popular article about the growth model and how current user retention rate was the biggest thing.",
    ),
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Aman Khan",
        artifact_id="beyond-vibe-checks",
        quote="Aman Khan runs a popular course on evals developed with Andrew Ng.",
    ),
    TrustEdge(
        source_person="Aman Khan",
        target_person="Andrew Ng",
        artifact_id="beyond-vibe-checks",
        quote="Aman Khan runs a popular course on evals developed with Andrew Ng.",
    ),
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Amol Avasare",
        artifact_id="amol-avasare",
        quote="Amol leads growth at Anthropic during the fastest run in software history.",
    ),
    TrustEdge(
        source_person="Marc Andreessen",
        target_person="Replit",
        artifact_id="marc-andreessen",
        quote="he discovered Replit about three months ago, and discovered Vibe coding, and is completely obsessed.",
    ),
    # -- Round 2 trust edges --------------------------------------------------
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Madhavan Ramanujam",
        artifact_id="eoghan-mccabe",
        quote="We just had Madhavan the podcast and the pricing expert, and he has this phrase, beautifully simple pricing is where you want to get to.",
    ),
    TrustEdge(
        source_person="Brian Halligan",
        target_person="Parker Conrad",
        artifact_id="brian-halligan",
        quote="Parker Conrad has a good hack that I liked.",
    ),
    TrustEdge(
        source_person="Keith Rabois",
        target_person="Delian Asparouhov",
        artifact_id="keith-rabois",
        quote="Delian wrote this blog post of lessons he learned from Keith.",
    ),
]


# -- Build helpers ---------------------------------------------------------


def _concepts_by_artifact() -> dict[str, list[Concept]]:
    by_artifact: dict[str, list[Concept]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for mention in MENTIONS:
        if mention.concept_id in seen[mention.artifact_id]:
            continue
        seen[mention.artifact_id].add(mention.concept_id)
        by_artifact[mention.artifact_id].append(CONCEPTS[mention.concept_id])
    return dict(by_artifact)


def main() -> None:
    out_path = Path(__file__).resolve().parent.parent / "app" / "data" / "graph.json"
    graph = build_graph(
        artifacts=ARTIFACTS,
        concepts_by_artifact=_concepts_by_artifact(),
        mentions=MENTIONS,
        trust_edges=TRUST_EDGES,
        source="seed:starter-pack-curated-28",
    )
    write_graph(graph, out_path)
    print(f"Wrote seed graph to {out_path}")
    print(f"  Artifacts: {len(ARTIFACTS)}")
    print(f"  Concepts: {len(CONCEPTS)}")
    print(f"  Mentions: {len(MENTIONS)}")
    print(f"  Trust edges: {len(TRUST_EDGES)}")
    print(f"  Total nodes: {len(graph.nodes)}")
    print(f"  Total edges: {len(graph.edges)}")


if __name__ == "__main__":
    main()
