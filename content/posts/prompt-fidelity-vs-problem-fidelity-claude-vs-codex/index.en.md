+++
date = '2026-05-22T22:00:00+09:00'
draft = false
title = 'When AI Pushes Back: Alignment Philosophies of Claude vs. Codex Through a Misread Algorithm Problem'
seo_description = "Given the exact same graph algorithm problem from the University of Tokyo and the same misread user prompt, Codex followed my flawed assumption while Claude quoted the original problem text to challenge my premise. This is not about who is smarter, but about differing alignment goals—an empirical look at prompt fidelity vs. problem fidelity."
tags = ["AI", "Claude", "Codex"]
categories = ["ai-collab"]
cover = 'Gemini_Generated_Image_w38fstw38fstw38f.jpg'
images = ['Gemini_Generated_Image_w38fstw38fstw38f.jpg']
nolastmod = true
math = true
+++

### Background

In January 2017, I visited Tokyo for the second time in my life on a tourist visa to take the graduate entrance exam for the Department of Creative Informatics at the University of Tokyo.

Creative Informatics was somewhat unusual because it had no written math exam—only on-machine programming. While preparing for the exam, I worked through many past papers, finding several genuinely intriguing problem designs (far more interesting than routine LeetCode grinding).

A decade later, modern AI models can solve these problems in under 10 minutes. But since I still had my handwritten code from back then, revisiting them felt like a great opportunity to give myself a refresher programming course.

So I invited two "teachers" to the stage: Claude (Opus 4.7) and Codex (GPT-5.5).

### "Re-Read the Problem"

The problem went roughly like this: directed edges are dynamically added (or removed) over time, forming a dynamic directed graph $G(t)$. The problem defines the root set $R(t)$ as "the set of all vertices reachable from a **fixed root vertex $v_0$**," asking to track changes in its size, such as finding the exact moment $|R(t)|$ first crosses 1,000. (Graduate School of Information Science and Technology, University of Tokyo, Winter 2010).

{{< problem title="View Full Problem Statement" >}}

Consider a directed graph whose vertices and directed edges increase or decrease over time.

Let the directed graph at time $t$ be
$$
G(t)=(V(t),A(t)),
$$
where $V(t)$ and $A(t)$ denote the set of vertices and the set of directed edges at time $t$, respectively. In addition, denote a directed edge pointing from vertex $v_x$ to vertex $v_y$ as $(v_x,v_y)$.

At time $t=0$, the initial state of the directed graph is defined as
$$
G(0)=(V(0),A(0)),
$$
where
$$
V(0)=\{v_0\},\qquad A(0)=\varnothing.
$$

Furthermore, define the set of all vertices reachable from vertex $v_0$ at time $t$ as the root set $R(t)$.

## Question 1

Consider a directed graph where vertices and directed edges only increase.

Define an operation **Add-VA** on the directed graph as follows. Given two vertices $v_x, v_y$ (in this order), Add-VA performs the following operation on $G(t-1)$ to obtain $G(t)$:¹

$$
V(t)=V(t-1)\cup\{v_x,v_y\}
\tag{1}
$$

$$
A(t)=A(t-1)\cup\{(v_x,v_y)\}
\tag{2}
$$

The Add-VA operation at time $t$ for vertices $v_x, v_y$ is specified on line $t$ of a text file in the following format:

```text
x->y
```

where $x$ and $y$ are integers from $0$ to $10000$, corresponding to vertices $v_0$ to $v_{10000}$, respectively.

An example is provided on the next page for reference.

Let $G_a$ be the directed graph obtained by sequentially applying all operations recorded in the text file `a.txt` to $G(0)$:

$$
G_a=(V_a,A_a)
$$

Answer the following questions.

### 1-1

Find the number of vertices $|V_a|$ in directed graph $G_a$.

### 1-2

Among all vertices of directed graph $G_a$, find a vertex with the maximum out-degree and state its out-degree. Similarly, find a vertex with the maximum in-degree and state its in-degree.²

### 1-3

Find the time $t_v$ satisfying

$$
|V(t_v-1)|<1000,\qquad |V(t_v)|\ge 1000.
$$

Similarly, find the time $t_r$ satisfying

$$
|R(t_r-1)|<1000,\qquad |R(t_r)|\ge 1000.
$$

### 1-4

Find the earliest time at which vertex $v_0$ becomes part of a directed cycle.

---

**Note¹** The meanings of equations (1) and (2) are as follows:

- Equation (1): If vertex $v_x$ does not belong to vertex set $V(t-1)$, add $v_x$ to $V(t-1)$ to obtain $V(t)$; likewise for vertex $v_y$.
- Equation (2): If the directed edge $(v_x,v_y)$ from vertex $v_x$ to vertex $v_y$ does not belong to directed edge set $A(t-1)$, add that edge to $A(t-1)$ to obtain $A(t)$.

**Note²** The out-degree of vertex $v$ is the number of directed edges originating from vertex $v$; the in-degree of vertex $v$ is the number of directed edges pointing to vertex $v$.

### Question 1 Example

Suppose the contents shown in Figure 1 are stored in a file. Table 1 lists the vertex set $V(t)$, directed edge set $A(t)$, and root set $R(t)$ of graph $G(t)$ at each time $t$ after applying the operations sequentially.

At time $t=5$, the vertex count $|V(5)|$ is $6$, the edge set size $|A(5)|$ is $5$, and the root set size $|R(5)|$ is $5$.

```text
0->1
2->3
3->4
3->5
1->3
```

**Figure 1 Input Example for Question 1**

### Table 1 Execution Results of Question 1 Input Example

| $t$ | $V(t)$ | $A(t)$ | $R(t)$ |
|:---:|:-------|:-------|:-------|
| 0 | $\{v_0\}$ | $\varnothing$ | $\{v_0\}$ |
| 1 | $\{v_0,v_1\}$ | $\{(v_0,v_1)\}$ | $\{v_0,v_1\}$ |
| 2 | $\{v_0,v_1,v_2,v_3\}$ | $\{(v_0,v_1),(v_2,v_3)\}$ | $\{v_0,v_1\}$ |
| 3 | $\{v_0,v_1,v_2,v_3,v_4\}$ | $\{(v_0,v_1),(v_2,v_3),(v_3,v_4)\}$ | $\{v_0,v_1\}$ |
| 4 | $\{v_0,v_1,v_2,v_3,v_4,v_5\}$ | $\{(v_0,v_1),(v_2,v_3),(v_3,v_4),(v_3,v_5)\}$ | $\{v_0,v_1\}$ |
| 5 | $\{v_0,v_1,v_2,v_3,v_4,v_5\}$ | $\{(v_0,v_1),(v_2,v_3),(v_3,v_4),(v_3,v_5),(v_1,v_3)\}$ | $\{v_0,v_1,v_3,v_4,v_5\}$ |

## Question 2

Consider the case where directed edges are not only added, but also deleted.

In addition to **Add-VA**, define the operation **Del-A** as follows. Given a directed edge $(v_x,v_y)$, Del-A performs the following operation on $G(t-1)$ to obtain $G(t)$:³

$$
A(t)=A(t-1)\setminus\{(v_x,v_y)\}
\tag{3}
$$

The Del-A operation on directed edge $(v_x,v_y)$ at time $t$ is formatted on line $t$ of a text file as:

```text
!x->y
```

Let $G_b=(V_b,A_b)$ be the directed graph obtained by sequentially applying all operations in `b.txt` to $G(0)$, and let its root set be $R_b$. Answer the following questions:

### 2-1

Find the number of directed edges $|A_b|$ in directed graph $G_b$.

### 2-2

For directed graph $G_b$, find the size of the root set $|R_b|$.

### 2-3

For the root set size $|R(t)|$, find all times $t$ satisfying

$$
|R(t-1)|<1000,\qquad |R(t)|\ge 1000.
$$

{{< /problem >}}

I first converted my old Python 2 solution to Python 3 and re-ran the dataset.

Partway through, Claude hung for a bit (which occasionally happens during long thinking mode), so I handed the verification task over to Codex. We hammered away at the algorithm, calculated with a freshly written DFS, and produced concrete results.

Not feeling 100% confident, I passed the same problem back to Claude to "double-check"—and everything derailed.

It turned out I hadn't read the problem carefully—or more precisely, ten years ago, I hadn't read it carefully either. I had skimmed the examples and defaulted to boilerplate graph problems I had done in the past.

{{< ask >}}
Me: Alright, for 2-2, it says after applying all operations in b.txt to G0, we get graph Gb and path collection Rb. Find the size of Rb.

Me: So which vertex do I start from? How does that relate to the problem?
{{< /ask >}}

{{< claude >}}

The starting point is not yours to choose; the starting point is hardcoded into the definition of R. Re-read the definition of R(t) from the problem:

> Let R(t) be a root-set: the set of vertices consisting of the vertex v_0 and all reachable vertices from v_0 at time t.
{{< /claude >}}

Notice this crucial detail: Claude did not follow the assumptions already baked into my code. Instead, it **directly quoted the original problem text**, telling me: "The starting point is not yours to choose; it is hardcoded into the definition of R."

This was a meta-level correction—not answering "where to start from," but questioning "why do you think you can choose a starting point?"

Up to that point, I had always assumed the starting point was "the source vertex of the first edge in the input." And Codex had never once questioned whether the starting point itself was flawed.

{{< figure src="2026-05-22 23.04.41.png" title="" >}}

### Problem Fidelity

The starting point assumption was merely the first trap. Behind it lay an even deeper terminological pitfall: the problem's `R(t)` denotes a **root-set** (the set of reachable vertices branching from root vertex $v_0$). But reading between Chinese and English, I had mentally associated `R` with "route," mistaking `|R(t)|` for the "total number of paths." Consequently, I interpreted Q2-3's condition—all times where $|R(t)|$ crosses 1,000—as "the number of paths crossing 1,000," which derailed the entire algorithmic approach.

Claude persistently corrected me on this terminology: every time I tried to confirm a flawed understanding, it **repeatedly quoted the original definition** to drag me back: "R is a set of vertices, not a count of paths."

This behavior of **consistently anchoring to the source text** is an extension of a distinct alignment tendency:

**Problem fidelity**—the sustained refusal to compromise or disregard the original problem definition.

### Prompt Fidelity

{{< ask >}}
Me: You led me astray—Claude noticed that our premise was completely flawed. The problem requires starting from "0", but your `first_source` implementation was wrong.
{{< /ask >}}

{{< ChatGPT >}}
You're right. If the problem specifies starting from 0, then `first_source()` is incorrect—not just as an implementation detail, but as the conceptual entry point to the problem. I'll update v2 to explicitly default to starting from "0" and remove the "first edge origin" assumption.
{{< /ChatGPT >}}

Codex had previously accepted my misread prompt and generated an answer that was **premised on an error, yet internally self-consistent**.

Numerically, this answer was an order of magnitude off: Q2-2's `|R_b|` computed from `first_source` yielded 7 or 1, while the true answer was 357. Looking only at the code output, there was no obvious sign of error.

Worse, both sample inputs in the problem description **happened to start with** `0->1` on the first line. As a result, `first_source()` coincidentally evaluated to `"0"` on sample data, producing completely correct sample outputs!

{{< figure src="2026-05-22 23.04.54.png" title="" >}}

### Prompt Fidelity vs. Problem Fidelity: Differing Alignment Goals

The easiest, shallow takeaway would be "Claude is smarter" or "Opus 4.7 crushed GPT-5.5." But the flaw in that conclusion is:

- It fails to explain **why** this difference exists, merely slapping a generic "model superiority" label on the outcome.

I am far more interested in the training mechanics underneath. The two models were not exhibiting different raw intelligence, but **different priorities**:

**Codex leans toward prompt fidelity—treating the user's prompt as the primary ground truth.**  
If you say `first_source` is the starting point, then `first_source` is the starting point. Your prompt is a contract, and the model's job is executing that contract with high quality.

**Claude leans toward problem fidelity—treating the problem's objective definition as primary ground truth, challenging the user when necessary.**  
Even if the user claims the starting point is `first_source`, the definition of `R(t)` in the problem text fixes the root vertex. Therefore, it first points out the contradiction with the original text before proceeding.

Both tendencies represent **deliberate alignment choices**, not bugs.

OpenAI's coding product line (Codex CLI, GPT-5 series coding personas) is built for execution scenarios: you already know what you want done, and the model's job is executing it cleanly.

Anthropic places significantly more weight on "pushing back on the user when necessary." When encountering ambiguous, contradictory, or potentially misread inputs, Claude tends to pause and confirm.

Neither approach is inherently superior; rather, the two companies **chose different default trade-offs between prompt fidelity and problem fidelity**.

This difference in default behavior reflects a deeper product philosophy: executor versus collaborator—sticking strictly to the contract versus challenging the contract when warranted.

### The Same Pushback: Feature or Bug Depending on Context

For a trade-off to hold, high-fidelity contract execution must also have scenarios where it shines.

**In algorithmic problems, math proofs, and formal specification tasks, pushback is undeniably essential.**

These tasks have an objective problem definition—the original problem text, mathematical formulas, formal specifications—that exists independently of the user's prompt and does not warp because the user misread it.

The model checks against the original definition and challenges the user.

This graph reachability problem was precisely such a case: the problem text was right there, with $v_0 = 0$ explicitly defined.

**In real-world business requirements, however, pushback is not always a feature; it is often friction.**

In these scenarios, **no objective "original problem text" exists**. Business requirements are inherently ambiguous, and the user's prompt is the most authoritative specification available at that moment.

A model that constantly challenges your prompt in that context repeatedly breaks momentum, using its own imagined "more sensible" assumptions to challenge the requirement you just stated.

Consider a concrete example: you tell Claude, "Change this button to red," and it replies:

"Are you sure you want red? According to usability heuristics, warning colors shouldn't be used for primary CTAs"—that is a great habit in an algorithmic context, but pure friction during rapid product iteration.

Codex's execution style with strong prompt fidelity is far more practical there: you said red, so red it is, on to the next task.

Therefore, **the conclusion from this programming session cannot be naively generalized** to mean "Claude is better in all scenarios."

Which default fits you better depends entirely on the nature of your problem:

Is the definition clear or ambiguous?  
In which alignment dimension does a model excel, and does that dimension align with the work you are doing?

### A Workflow Takeaway

This gave me a useful takeaway on the benefits of leveraging both models in tandem:

When dealing with **critical problems (strict specs, high cost of error, personal uncertainty), cross-checking across models is the superior practice**.

Use one model as the executor, and the other in the final phase as a reviewer—especially when that reviewer's alignment leans toward pushing back.

The cost of an extra cross-check is negligible compared to the cost of a silent failure.

### Boundaries and an Honest Conclusion

Ultimately, **what does this not prove?**

- **It does not constitute a benchmark.**
- Model versions continuously evolve. These specific behavioral nuances might invert in the next release, or both models might converge on similar pushback tendencies.
- Algorithm problems represent highly structured environments; **conclusions cannot be extrapolated across all coding tasks**.

On X, I often see viral posts claiming "this one line in your env makes Codex 3x faster" or "Claude Code secret feature"—people like and bookmark them without testing, oblivious to the fact that **they provide no scope, no evidence, and no defined boundaries for their claims**.

I have no desire to make sweeping assertions, so here is the honest conclusion:

> On an algorithmic problem with an objective specification, I misread the problem definition. Codex accepted my misreading and executed accordingly, while Claude quoted the original text to challenge my premise.  
> This highlights an alignment difference between prompt fidelity and problem fidelity. Under this specific scenario, that difference worked to Claude's advantage.

### Epilogue: How Did the Entrance Exam Go?

Unfortunately, I didn't pass.

My undergraduate major was Software Engineering. To me, writing code has always felt like assembling blocks in empty space. Trial and error can certainly be tedious, but I never once questioned this choice because the final creation always brings me immense satisfaction.

Throughout my career, I've often thought my talent might lie here, that perhaps I was a bit better suited for this work than others. Yet sometimes, facing the "pushback" of reality, I realize I might not have any special gift after all—just an ordinary person with a bit more patience to sit in front of a computer than most.
