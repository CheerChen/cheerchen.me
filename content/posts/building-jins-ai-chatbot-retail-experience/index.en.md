+++
date = '2025-06-25T12:00:26+09:00'
draft = false
title = 'JINS AI: Bringing Generative AI to Physical Retail — AWS Summit Japan 2025 Retrospective'
seo_description = "A deep dive into how eyewear brand JINS built an in-store AI shopping assistant in 3 months with a 3-person team: exploring RAG architecture, AWS managed services, and solving real-world retail AI adoption challenges."
tags = ["AI", "AWS", "architecture", "AWS Summit Japan 2025"]
categories = ["tech"]
cover = '250625_pressrelease.png'
images = ['250625_pressrelease.png']
nolastmod = true
+++

## Background

On Day 1 (June 25) of AWS Summit Japan 2025, during a session titled **“アイウエア接客の未来を拓く～生成 AI で進化するあたらしい店舗体験への挑戦～”** (*Pioneering the Future of Eyewear Customer Service: Challenging New In-Store Experiences Evolving with Generative AI*), eyewear retailer JINS shared the development journey, design details, and practical hurdles behind launching JINS AI.

JINS AI is a conversational in-store shopping assistant. When purchasing glasses at retail stores, customers can ask generative AI questions on the spot regarding frame and lens choices.

I've often felt that traditional physical retail—especially in Japan—tends to move sluggishly when adopting AI, often struggling to find practical, everyday use cases. Yet this project was built and piloted in retail stores by just three people in three months. In a company of this scale, that kind of turnaround is almost unheard of. The technical architecture presented at the summit had plenty of clever nuances that made me think, **"Oh, so you really can't just slap this together carelessly."** Here is my retrospective on the session.

## Scoping the Scenario

{{< figure src="1da1e727503f0d0f.jpg" >}}

With such a lean team, launching a production pilot in three months required ruthlessly defining a "1st Scope." JINS noted that with eyewear, "_EC よりも実物を見て買いたい人が多い_" (more people prefer seeing physical frames in person before buying compared to e-commerce). Rather than building an all-purpose e-commerce shopping bot, they surgically embedded AI into two distinct in-store decisions: **frame selection** and **lens selection**. Restricting the initial release strictly to this "1st Scope" was the decisive factor in shipping within three months.

## Architecture Design

{{< figure src="239b048c948e9c1f.jpg" >}}

- **A Clean RAG (Retrieval-Augmented Generation) Architecture**:
    - The system is a textbook implementation of RAG:
        1. Customer requests hit **AWS Fargate** applications via an Elastic Load Balancer (ELB).
        2. Fargate invokes **Amazon Bedrock** (the generative AI core).
        3. Rather than hallucinating from memory, Bedrock first queries **Amazon OpenSearch Service** for relevant domain knowledge.
        4. OpenSearch indexes data sourced from **Amazon S3**, which holds product catalogs and retail customer-service knowledge. The note on the right—"Chunking CSV data row-by-row and registering"—reveals how domain knowledge was segmented into vector embeddings, a critical step for retrieval accuracy in RAG.
    - This pattern remains the industry gold standard for mitigating hallucinations and anchoring LLM responses to verified facts.
- **Pragmatic Technology Choices**:
    - **All-in on Managed Services**: From compute (Fargate) and databases (RDS, DynamoDB) to AI (Bedrock) and search (OpenSearch), the team runs virtually zero self-managed servers. Offloading infrastructure let them focus entirely on domain logic—the primary driver behind rapid delivery.
    - **Purpose-Built Databases**:
        - **Amazon DynamoDB** stores prompts, completions, and conversation history. NoSQL is ideal for unstructured, high-frequency conversational write patterns, while building a valuable audit log for behavioral analytics and future model fine-tuning.
        - **Amazon RDS** handles traditional structured relational data.
    - **Security and Scalability**: Workloads reside in **private subnets**, communicating externally through load balancers and maintained via secure bastion hosts. Speed did not come at the expense of security hygiene. Combining Fargate with ELBs guarantees automatic scaling as in-store traffic spikes.

## The Five Big Hurdles

With few precedents for consumer-facing generative AI in physical retail, JINS AI iterated through considerable trial and error across five core hurdles:

### 1. AI Persona and Brand Voice

{{< figure src="f1a047b1a9eb6425.jpg" >}}

A successful generative AI product is the triad of **brand ethos, user experience design, and technical execution**. When launching an enterprise AI initiative, the first question shouldn't be "which model do we pick?", but rather: "How do we want our brand to sound when talking to customers?" Technology-led teams often overlook this, yet it dictates user perception.

- **Grounded in Brand Identity**:
    - The slide highlights **"Honest"**—JINS' core brand value: "Be honest with customers, walk the upright path."
    - This ensures that regardless of underlying model upgrades, the foundational values and tone of customer communication remain coherent with the brand.
- **Translating Abstract Philosophy into Concrete Behaviors**:
    - The team decomposed "Honest" into five operational AI behavior guidelines:
        - **Radically honest recommendations**: Never push products for the sake of selling; prioritize what genuinely fits the customer to earn trust.
        - **Clear, unambiguous phrasing**: Explain product benefits in concrete terms without evasiveness.
        - **Segmenting information for readability**: Use bullet points and spacing so responses are easy to skim on mobile screens—a great touch of UX restraint.
        - **Accessible visual communication**: Avoid jargon so customers immediately grasp optical benefits.
        - **Smooth guidance toward next actions**: The AI doesn't just passively answer; it proactively nudges: "Would you like to try them on?"—guiding the purchasing journey much like a seasoned sales clerk.

### 2. Answer Accuracy: Agentic Workflows

{{< figure src="492836055c395619.jpg" >}}

Rather than relying on a single monolithic model to handle every query, JINS adopted an **Agentic Workflow**. In traditional setups, tossing raw user input directly to an LLM frequently results in semantic drift and misinterpretation.

JINS structured the workflow like a specialized human retail team:

- **Reception / Preprocessing (前処理)**: Filters raw input immediately, separating fixed FAQs, policy violations, or queries requiring backend orchestration.
- **Dispatcher / Intent Classifier (意図判断)**: The core orchestrator. JINS routes this step to their most capable LLM to ensure accurate routing.
- **Domain Specialists (意図判断・RAG・AI 回答生成)**: Once intent is classified (e.g. "asking about frames"), the request routes to a dedicated "Frame RAG Node" (フレーム情報 RAG ノード). This node queries only frame-related embeddings; parallel nodes handle lenses and store FAQs. This specialization sharply improves domain precision.

The slide openly notes the trade-offs:

- **Benefits (メリット)**: Prevents responses from drifting off-topic; anchors outputs to classified user intent.
- **Challenges (課題)**: **Latency trade-offs** (sequential agent steps add latency); **difficulty of cross-domain recommendations** (e.g. synthesizing holistic advice covering both frame geometry and lens thickness simultaneously).

This architecture also optimizes cost and performance: the expensive, top-tier model runs only at the intent classification bottleneck, while downstream specialist nodes can leverage leaner, faster models to minimize latency and token spend.

### 3. Answer Accuracy: Query Refinement Pipeline

{{< figure src="31d50c35f2df044c.jpg" >}}

- **Step 1: Query Rewriting ("Translating Colloquialisms")**
    - Customer inputs are casual and unstructured (e.g., "I'm a woman in my 30s, do you have round black frames?"). Running raw embeddings directly against product catalogs yields mediocre results.
    - JINS uses Bedrock to translate colloquial user queries into structured search facets: `Color: Black`, `Category: Glasses`, `Gender: Women`. This aligns search queries with catalog schemas before vector lookup begins.
- **Step 2: Search Scope Optimization ("Pruning the Space")**
    - Using structured parameters from Step 1, the system applies metadata filtering in OpenSearch, scoping vectors strictly within "Women's Glasses."
    - Like going straight to the literature section in a library instead of wandering the building, this boosts both precision and query speed.
- **Step 3: Reranking ("Selecting the Best")**
    - Preliminary vector retrieval pulls 15 candidate matches, but vector similarity alone doesn't guarantee conversational relevance.
    - Bedrock reviews the 15 candidates against original conversational context, reranking them down to the top 3 best recommendations. LLMs excel at nuanced contextual judgment compared to raw cosine similarity.

### 4. Answer Accuracy: Observability and Memory Management

- **Observability via Langfuse**
- **Session Memory Management**
    - Ephemeral workflow data (intent states, vector candidate sets) is maintained in-memory and wiped when the session concludes.
    - For retrospective auditing and model analytics, past conversation histories are persisted asynchronously in a PostgreSQL database.

### 5. Security, Compliance, and Data Sanitization

{{< figure src="a26d886373f04de0.jpg" >}}

- **The Core Dilemma: Unlocking Data Value While Guarding Privacy**
    - An AI application is only as good as the domain data it ingests. Real customer-clerk retail interactions are invaluable, but riddled with Personally Identifiable Information (PII) like names, phone numbers, and addresses.
    - JINS addressed this with a multi-layered sanitization pipeline: **"Two AI Passes + Dual Human Reviews"**:
        - **Steps 1 & 2 (Automated Screening)**: S3 file uploads trigger Lambda functions that run regex filters followed by a first pass with Bedrock to strip obvious PII (removing 80–90% of routine private data).
        - **Step 3 (Human Review + Secondary LLM Pass)**: Human auditors inspect the first pass; edge cases trigger a second, targeted LLM sanitization pass. Machines handle throughput; humans handle edge cases.
        - **Step 4 (Final Human Verification)**: A final human sign-off verifies the clean dataset before ingesting knowledge into OpenSearch. This dual-verification loop ensures clean, risk-free embeddings for RAG.

{{< figure src="837eee11a0b6fcfb.jpg" >}}

- **Transparent Terms of Service**:
    - Rather than presenting impenetrable legal terms, JINS distilled their policy into three prominent points:
        - **✓ This is a Beta**: Manages customer expectations upfront and disclaims edge-case errors.
        - **✓ Do not misuse**: Establishes clear legal ground to terminate abusive sessions.
        - **✓ Do not enter personal information**: Shares privacy responsibility directly with users.
- **Internationalization**:
    - The bottom right notes **"※日英中で対応" (Supported in Japanese, English, and Chinese)**, baking multi-lingual safety and policy compliance into the foundation for global retail shoppers.

### The "Last Mile": In-Store Customer Adoption

{{< figure src="10c2af91308c5552.jpg" >}}

1. **Context-Driven Signage (The Right Message at the Right Time)**
    - Instead of just plastering bare QR codes, store signage positioned the service clearly: "When store staff are **temporarily busy**, feel free to consult me."
    - This disarms hesitation: customers know when to use it (when clerks are tied up) and that doing so is welcomed. AI is framed as a thoughtful Plan B rather than a confusing imposition.
2. **Staff Guidance (Human-in-the-Loop Collaboration)**
    - Retail staff were empowered as AI ambassadors rather than feeling displaced by automation.
    - Crucially: **"Never force AI on customers."** When free, staff continue providing traditional customer care. The AI exists to alleviate peak congestion, especially for foreign tourists who might face language barriers.
3. **Multi-Point In-Store Placement**
    - For shoppers who prefer browsing independently, QR prompts were placed across entrance areas, display shelves, and consultation counters—weaving AI access naturally into customer walking paths.

## Real-World Pilot Results

{{< figure src="6133999bb37abfcf.jpg" >}}

JINS AI Beta launched a three-month store pilot starting in April 2025. In practice, the service was particularly well-received by foreign tourists and customers who wanted answers without feeling pressured by sales staff.

Addressing the biggest initial fear—"will customers abuse it for off-topic chats?"—the data showed the overwhelming majority of interactions focused directly on purchasing advice. Nearly 20% of conversations progressed to selecting specific frames or viewing product summaries, showing direct traction toward purchasing decisions. A new retail paradigm where generative AI supplements physical staff is taking shape.

## Q&A Discussion

After reviewing the materials, I threw three architectural questions to Gemini:

> 1. Are Agentic Workflows merely a workaround for weaker LLMs? Will they become obsolete as frontier models become smarter?

{{< gemini >}}

A great question that touches on the architectural future of AI applications.

**The short answer: No. Even with far more capable frontier LLMs, Agentic Workflows will not disappear; they will become even more foundational.**

They exist not to patch model weaknesses, but to build **reliable, auditable, and scalable** production systems.

Here is why:

1. **Divide and Conquer**:
    - Even if you have an omniscient "Super CEO" (future frontier LLM), you still need organizational structure—finance, legal, marketing, and engineering divisions (individual agent nodes).
    - The CEO's role is understanding the macro objective and **delegating** to domain specialists. Agentic Workflows provide this organizational blueprint: the LLM acts as an orchestrator calling specialized tools (RAG search, databases, APIs).

2. **Determinism and Reliability**:
    - A single, monolithic LLM prompt acts as a black box with inherent stochasticity. For enterprise commerce, unpredictable drift is unacceptable.
    - Agentic Workflows decompose complex workflows into bounded, inspectable steps. **Each stage is testable and predictable**. When errors occur, you can pinpoint the failing node immediately.

3. **Cost and Latency Optimization**:
    - JINS demonstrates this clearly. Even when powerful frontier models emerge, their inference costs remain high.
    - Agentic Workflows enable **intelligent cost tiering**: deploy heavy, expensive reasoning models only at the critical intent-classification bottleneck, while offloading formatting and FAQ retrieval to fast, low-cost models.

{{< /gemini >}}

> 2. What does "an AI's capability depends on the data it learns from" mean here? If LLM weights are already frozen, how does masked historical data improve the application?

{{< gemini >}}

This hits on a common misconception. We must distinguish between two forms of data:

1. **Pre-training Data for Foundation Models**:
    - Massive corpora of internet text and books used to train base models like GPT-4, Claude, or Gemini.
    - This establishes the base reasoning engine and world knowledge. Weights are indeed **frozen** after post-training. JINS does not alter this layer.

2. **Retrieval Data in RAG Systems**:
    - JINS AI's performance does not rely on changing model parameters, but on **supplying high-quality reference context to the LLM at the exact moment a customer asks a question**.
    - RAG operates like an **"open-book exam"**:
        - **The LLM**: An intelligent student who lacks access to JINS' proprietary, real-time internal data (inventory levels, sales tips for high-diopter lenses).
        - **RAG Knowledge Base (OpenSearch)**: The verified textbook provided to the student.
    - JINS AI's answers directly reflect the quality of that reference textbook.

**How does masked conversational data improve performance?**

JINS strips **Personally Identifiable Information (PII)** like names and phone numbers, while preserving valuable **Business Interaction Patterns**.

For example, a raw interaction:
> "Hello Ms. Reina Kuroo, my face is rather *round*, and I need *black* glasses suitable for *remote work* under *10,000 yen*. What do you recommend?"

Sanitized into RAG:
> **Query Pattern**: "[Female] customer, face shape [round], usage [remote work], color [black], budget [mid-tier], requesting frame recommendations."  
> **Resolution Pattern**: "Recommended [Model A], [Model B]. Key features: lightweight, flattering frame geometry. Customer feedback: positive."

When future customers present similar needs, the AI retrieves this verified customer-service pattern from OpenSearch. **Continuously augmenting the RAG store with sanitized, successful sales interactions updates the open-book textbook, steadily raising the LLM's accuracy over time.**

{{< /gemini >}}

> 3. What does it mean to "run a PoC just for the sake of doing a PoC"?

{{< gemini >}}

"Running a PoC for the sake of doing a PoC" is a notorious corporate trap, often termed "PoC Purgatory" or "Innovation Theater."

A **Proof of Concept (PoC)** is intended as a lightweight, fast experiment to validate whether an idea is technically feasible and commercially viable.

**A healthy, strategic PoC (The JINS approach)**:
- **Purpose**: Answer a specific business hypothesis (e.g., "Can conversational AI effectively resolve customer confusion in frame selection?").
- **Goal**: If validated, proceed immediately to the next phase (in-store pilot, rollout); if it fails, capture lessons and pivot quickly.
- **Outcome**: A deployed, value-generating product integrated into real workflows.

**A "PoC for the sake of PoC" project**:
- **Purpose**: Satisfy executive mandates or chase hype cycles ("Our company must have generative AI!").
- **Goal**: The PoC itself is the finish line. As long as a flashy demo can be shown on stage or in an executive slide deck, the project is deemed "successful."
- **Outcome**: The moment the presentation ends, the initiative dies. It never accounts for business integration, compliance, privacy scrubbing, or real customer distribution. It remains detached "tech fireworks" with zero lasting impact.

{{< /gemini >}}
