# Beneath the Org Chart

**Read what's underneath, before you respond.**

Built for the Lenny's Newsletter x Replit Buildathon.
Live: https://beneath-the-org-chart.replit.app/

---

## What the app does

Lenny's archive is hundreds of hours of the best product, growth, and
company-building operators in the world disagreeing productively. The problem
is that the value is locked in linear audio and long posts: you can't see which
ideas connect, who actually said what, or where the smartest people in the
corpus disagree. The org chart tells you who reports to whom. This tells you
what's underneath.

**Beneath the Org Chart** turns the archive into a queryable knowledge graph
and puts three surfaces on top of it. All three read the same graph.

- **Atlas** — an interactive, force-directed map of the entire corpus.
  Amber boxes are recurring concepts (ideas Lenny and his guests kept returning
  to), green dots are people, indigo dots are episodes and posts. Filter by
  top themes, shared language, or trust relationships; click any node or edge
  to see exactly where an idea showed up and the verbatim quote from the room.
  No LLM at runtime — it's a direct render of the pre-built graph, so the user
  can audit the evidence themselves.

- **Lookup** — paste a real situation you're facing at work. Claude reads it
  against the graph and returns the concepts that apply, **two genuinely
  contrasting takes** from real guests (each grounded in a verbatim quote),
  the political-capital tradeoff you'll pay for in the room, and a concrete
  draft move you can paste into a doc.

- **Briefing** — paste an external artifact: a CPO offsite talk, a PM job
  description, a board update, a Substack post. Claude returns what the person
  is *actually* saying beneath the surface phrasing, their priorities with
  verbatim evidence, **where Lenny's corpus agrees and where it pushes back**
  (every citation a real quote from a real episode), and the sharp questions
  you'd ask before you respond.

The throughline: never react to a situation or an artifact cold. Read it
against what the best operators have already said, see where they'd disagree,
then respond.

## How it uses Lenny's data

The application is built entirely on Lenny Rachitsky's open archive — the
starter-pack of **50 podcast transcripts and 10 newsletter posts (60 sources
in total)** spanning AI product development, growth, leadership, pricing,
sales, hiring, and company building.

1. **Offline extraction → a Network Intelligence Layer.** An offline pipeline
   reads every source in `data/starter-pack/` and extracts a graph: the
   concepts each piece of thinking contains, the artifacts they appear in, who
   said them, the **verbatim quote** that grounds each mention, and *trust
   edges* — who Lenny and his guests explicitly vouch for or cite. The result
   is committed as static JSON (`app/data/graph.json`) so the graph is
   reproducible and never built at request time.

2. **The graph today.** 834 nodes (582 concepts, 60 artifacts, 192 people)
   connected by 4,111 edges across four relationship types: `authored_by`,
   `appears_in`, `shared_language` (concepts that co-occur across the corpus),
   and `trust`. Every concept and every edge traces back to a quote that
   actually appears in the archive.

3. **Grounding at runtime.** For Lookup and Briefing, the graph is projected
   into the Claude prompt as the grounding context. The model is constrained
   to cite only verbatim strings present in the graph — every take, agreement,
   and pushback the app shows is tied to a real sentence a real guest said on
   a real episode. Nothing is invented. (The system prompt plus graph context
   are sent with Anthropic prompt caching so the corpus stays warm across both
   surfaces.)

4. **Browsable evidence.** The Atlas surface renders the same graph with no
   model in the loop, so anything the AI surfaces in Lookup or Briefing can be
   traced back, by hand, to the episode and the moment it came from.

In short: Lenny's archive *is* the application's knowledge base. The data is
extracted once, grounded in verbatim quotes, and every AI-generated answer is
anchored to it.

## Stack

Python 3.11, FastAPI, Uvicorn, and the Anthropic Claude API for the two
runtime surfaces; vanilla JS/CSS with a locally bundled vis-network for the
Atlas. No build step. Lookup and Briefing degrade to a deterministic stub when
no API key is set, so the graph and Atlas always work.
