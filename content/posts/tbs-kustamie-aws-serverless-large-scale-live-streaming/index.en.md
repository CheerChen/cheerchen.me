+++
date = '2026-06-26T12:00:00+09:00'
draft = false
title = "Behind TBS's Large-Scale Interactive Live Streaming: AWS Serverless Design — AWS Summit Japan 2026 Recap"
seo_description = "How TBS's interactive streaming platform Kustamie combines Amazon IVS, API Gateway, Lambda, SQS, Step Functions, ElastiCache, and Amazon Nova to serve tens of thousands of concurrent viewers, covering load testing, multi-tier caching, async design, and AI content moderation trade-offs."
tags = ["AWS", "Serverless", "architecture", "Amazon IVS", "generative-ai", "AWS Summit Japan 2026"]
categories = ["tech"]
cover = '22168_ext_01_0.jpg'
images = ['22168_ext_01_0.jpg']
nolastmod = true
math = true
+++

## Background

At AWS Summit Japan 2026, the session **"Behind TBS TV's 'LOVE it!' Large-Scale Streaming and AWS Serverless Design" (「TBSテレビ『ラヴィット！』大規模配信の裏側と AWS サーバーレス設計」)** featured Mr. Kameda, Technical Product Lead in the Future Technology Innovation Division of TBS Television's Media Technology Bureau, walking through the technical design of Kustamie, an interactive streaming platform. The session focused on a two-way live streaming scenario at a scale of tens of thousands of users: deliver low-latency video and real-time interaction reliably while protecting the API, database, and backend services from concentrated traffic spikes.

TBS Television is one of Japan's major commercial broadcasters. Its morning show *LOVE it!* (『ラヴィット!』) airs weekdays at 8 AM and bills itself as "Japan's brightest morning show." The show normally airs on TV, but "LOVE it! Bōnenkai '25" (「ラヴィット!忘年会'25」) was a year-end special live stream built around the show's IP: cast members who had been active in 2025 gathered around a kotatsu to drink, chat, and look back on the year's events, while viewers joined in online.

This was not a one-way video stream but the show's first **viewer-participation event**. Instead of just watching, the audience took part in real-time segments, interactions, and quizzes tied to the performers. In other words, it was not an ordinary VOD page but an online event that had to absorb concentrated access at a fixed time, plus real-time chat, interaction control, and video distribution.

The talk's value is that it broke down several problems common to large-scale live streaming with unusual clarity: separating video streams from business APIs, Lambda capacity planning, modeling real user behavior, multi-tier caching, slimming down the synchronous path, and using a small model for high-frequency content moderation.

## Kustamie: Turning Watching into Participating

{{< figure src="bg_1.jpg" >}}

According to the [TBS Tech Portal](https://www.tbs.co.jp/techportal/products/kustamie/), Kustamie is a still-in-development "two-way participation app for shows and events." It isn't built for ordinary video on demand or a bare-bones streaming player. It's built for live broadcasts and events, which tend to collapse into one-way communication: interactive features like quizzes, reactions, and multi-angle streaming create stronger two-way interaction between performers and participants, raising the audience's sense of participation.

Kustamie has to handle a set of behaviors happening all at once: viewers open the event page, fetch program info and interaction controls, join the real-time chat, watch low-latency video, and participate in segments at key moments, and all of this spikes around the start of the stream. The hard technical problem is fitting video distribution, real-time interaction, business APIs, state management, and content moderation into a single event experience that stays stable with tens of thousands of simultaneous participants.

## Architecture Overview: Separating Event Info from Real-Time Data

{{< figure src="slide-01-architecture.svg" >}}

{{< figure src="mermaid-01-architecture.svg" >}}

Kustamie's traffic splits cleanly into two paths.

The first is the **event information** path. Clients hit multiple Lambda functions through Amazon API Gateway, which then call application services on ECS; the backend manages state with ElastiCache and Amazon RDS / Aurora Serverless v2. This path handles relatively structured business data like program metadata, participation state, and interaction-control definitions.

The second is the **video, audio, and real-time interaction** path. Clients connect to IVS Chat over WebSocket, and the video stream goes through Amazon IVS Low-Latency / Real-Time. ECS also injects interactive data into IVS so clients can fire interaction events along the video timeline.

This split is the premise for every optimization that follows. High-frequency real-time data (user comments, chat, video distribution) never lands on the API Gateway + Lambda + RDS path; it goes to the managed fan-out of IVS / IVS Chat instead. The data left on the API path changes far less often and has much lower consistency requirements, which is what makes caching and async processing possible.

One less common shape in the architecture: API Gateway fronts Lambda, and Lambda in turn calls ECS. It is likely a thin-Lambda + thick-ECS design: Lambda handles auth, parameter validation, rate limiting, and light orchestration, while ECS owns the heavy business logic and the database connection pool. This avoids the connection-management problems of Lambda hitting Aurora directly, at the cost of one extra service hop.

## The Initial Problems: No Caching and 12-Second Responses

{{< figure src="slide-02-problems.svg" >}}

The first problem TBS hit ahead of the large-scale stream: the existing client API was not designed with caching in mind. The slide noted that API Gateway was using a Regional endpoint and suggested the Edge-Optimized type would be more appropriate. Two concepts need separating here: an Edge-Optimized endpoint is not itself a cache. It mainly moves TLS termination and ingress to CloudFront edge locations. The pieces that keep requests off the backend are API Gateway stage caching or a self-managed CloudFront cache policy.

If users are concentrated in Japan and the API is deployed in `ap-northeast-1`, a Regional endpoint isn't inherently worse than Edge-Optimized. The bigger problem: when tens of thousands of people open the client in a short window, GET requests for program metadata, interaction-control definitions, and participation-entry state punch through to Lambda, ECS, and RDS every single time, and the backend gets crushed by amplified traffic.

The second problem was more tangible: the stream-participation API took up to **12 seconds** to respond. Architecturally, this probably came from multiple serial internal calls, Aurora Serverless v2 scale-up latency under burst traffic, VPC Lambda cold starts, and external control-plane API calls. The slide also called out server-to-server communication overhead from numerous internal API calls, and the team admitted they had never run systematic load tests, so behavior under high load was unknown.

## Capacity Planning: Lambda Concurrency Isn't the Only Metric

{{< figure src="slide-03-lambda-load-metrics.svg" >}}

Capacity planning for API Gateway + Lambda has to watch at least three metrics at once.

First, the **API Gateway throttle rate**. The default is **10,000 req/s** per region per account, and you can request an increase.

Second, **Lambda concurrent executions**, which can be approximated with Little's Law:

$$
\text{concurrency} = \text{requests per second} \times \text{duration in seconds}
$$

At 10,000 requests per second with a 0.1-second execution each, steady-state concurrency is 1,000, the default Lambda account concurrency limit.

Third, and most easily overlooked: the **Lambda scaling rate**. For functions that finish quickly but see very high request rates, steady-state concurrency looks small, yet the function can get stuck on the scaling rate during ramp-up. Init during cold starts also occupies concurrency slots, meaning capacity is consumed before an instance has actually processed a single request.

## The Counterintuitive Risk of Short Functions

{{< figure src="slide-04-lambda-scaling.svg" >}}

The slide illustrated this risk with two cases.

In the first case, the function runs 0.1 seconds at 10,000 req/s. Concurrency is 1,000 and the scaling rate is also 10,000 req/s, within default limits.

In the second case, the function runs 0.05 seconds at 20,000 req/s. Concurrency is still 1,000, seemingly inside the default concurrency quota, but the required scaling rate is 20,000 req/s, which exceeds the default capability and can cause throttling.

Shorter average runtimes are not always better here: **short functions + high RPS** shift the pressure onto the scaling rate. When you only look at steady-state capacity through Little's Law, this problem stays hidden.

The slide's fix was to raise the concurrency quota to 2,000. That claim needs careful interpretation, because AWS's official description of the Lambda scaling rate does not scale proportionally with the account concurrency quota. In practice, more reliable options include requesting the relevant quotas in advance, using Provisioned Concurrency, reducing the burst of requests reaching Lambda, or moving ultra-high-frequency hot paths to always-on services.

## Load Testing: k6 and a Cross-Account Setup

{{< figure src="slide-05-load-test-method.svg" >}}

{{< figure src="mermaid-05-load-test.svg" >}}

They picked k6 for load testing, a pragmatic choice: scenarios can be written in JavaScript / TypeScript so engineers can review them easily, the Go runtime is resource-efficient, and AWS Prescriptive Guidance also lists k6 as a load-testing tool.

The test topology separated the load-generating account from the Kustamie account. The management node used a `t3.medium`; large-scale workers used `c6i.2xlarge`. Medium-scale tests (100 to 5,000 VU) could run on a local PC; large-scale tests (5,000 to 60,000 VU) spun up an EC2 worker cluster.

The point of this design is isolation. The CloudWatch Logs, costs, IAM roles, and service quotas generated by load testing don't pollute the production account, and even a buggy test script is easier to contain.

The k6 output on the right of the slide also highlights a common observation: the p95 of `http_req_duration` can look great while the max of `iteration_duration` still runs to a dozen seconds. For serverless architectures, averages and p95 alone don't tell the story. The long tail is what users feel as stutter.

## Scenario Modeling: Live Traffic Isn't Linear

{{< figure src="slide-06-scenario-load-test.svg" >}}

This slide was one of the most transferable methodologies in the whole talk: instead of hammering a fixed RPS, they simulated the curve of real users entering the stream.

Kustamie's scenario assumed 10% of max VU already online when the standby stream began, then VU growing exponentially over the 30-minute standby period and peaking when the main program started. The curve came from data from past similar events, not guesswork.

Traffic for live and event-driven products rarely ramps linearly. Thirty minutes before the show you might only have core fans; general users start arriving around five minutes out; and in the last few dozen seconds before start there is a visible stampede. That exponential tail runs head-on into the Lambda scaling rate, API Gateway throttling, the database connection pool, and external API rate limits. Unless you model this curve, load tests won't surface the real problems.

## Load Test Results: 4xx Errors at 10,000 RPS

{{< figure src="slide-07-quota.svg" >}}

The E2E load test result was blunt: once request volume passed **600,000 requests per minute** (an average of **10,000 RPS**), 4xx errors started climbing. That number lines up exactly with the API Gateway default throttle rate.

The investigation path was clear too: no errors on the Lambda side, so the problem was judged to be at the API Gateway layer. The slide acknowledged that standard API Gateway metrics only show 4xx counts without distinguishing the specific error type; to pinpoint it in production you need access logging that records status, requestId, error messages, and throttling context.

In the end they requested two quota increases: the API Gateway throttle rate to **30,000 RPS**, and Lambda concurrent executions to **50,000**. The 50,000 figure looks aggressive, but once you factor in the exponential tail, cold starts, short-function scaling, and safety margin, it is not sized for steady-state concurrency. It is headroom for absorbing bursts.

That's a reminder that large-scale serverless systems can't treat service quotas as a post-launch firefighting item. They belong on the pre-deploy checklist and should be kept consistent between the load-test account and the production account.

## Multi-Tier Caching: Stop Requests as Early as Possible

{{< figure src="slide-08-multi-tier-cache.svg" >}}

{{< figure src="mermaid-08-cache.svg" >}}

The first step in the performance work was multi-tier caching.

Tier one: the **API Gateway stage cache**, applied to GET only. On a hit, the request is served straight from API Gateway without even invoking Lambda. This tier suits read-heavy, short-TTL-tolerant data like program metadata, UI configuration, and interaction-control definitions.

Tier two: **Lambda global variables**. When the Lambda execution environment is reused, variables declared outside the handler are not re-initialized, so you can cache configuration, ID mappings, JWT public keys, and expensive-to-initialize client objects. The limits are equally clear: nothing is shared across instances, containers can be reclaimed at any time, and anything needing strong consistency does not belong here.

Tier three: **ECS + ElastiCache for Valkey**, shielding RDS at the application-service layer. Valkey is largely compatible with Redis 7.2, and AWS has pushed Valkey hard since the Redis license change; choosing it is as much about licensing and cost as performance.

Methodologically, the principle is simple: the closer a cache sits to the request source, the more backend work a hit saves. The API Gateway stage cache skips Lambda, ECS, and the database entirely; the Lambda global cache skips downstream service calls; ElastiCache skips RDS queries.

Cache invalidation is not that hard here, since the architecture routed real-time user-generated data to IVS Chat from the start. Most of what remains on the API path is pre-arranged or changes predictably, so TTL-based expiry covers the majority of cases.

## Going Async: Cutting the User-Facing Path to 150ms

{{< figure src="slide-09-async.svg" >}}

{{< figure src="mermaid-09-async.svg" >}}

The biggest improvement came from going async: the participation API's response time dropped from a worst case of **12,000ms** to an average of around **150ms**, an 80x improvement.

The core idea: keep only what the user needs immediately on the synchronous path. That path goes through API Gateway into Lambda, then a Step Functions Express Workflow that completes UserID generation, IVS token generation, and the SQS enqueue. Everything that doesn't affect the user starting playback goes through SQS into the async path, consumed in the background by Lambda and ECS.

This wasn't parameter tuning. It redefined what must complete synchronously. The user needs to enter the stream right away, so the UserID and IVS token must come back synchronously; registration records, associated state, and history writes can wait.

IVS Real-Time token handling mattered too. The slide notes the IVS API call rate is **50 TPS and cannot be raised**: if 60,000 users pile in at once and each triggers an IVS API call, you hit the control-plane limit immediately. So tokens are signed and issued directly by Lambda. A token here is a JWT generated with a private key. The pattern replaces a rate-limited control-plane API call with a verifiable local cryptographic operation. S3 presigned URLs and CloudFront signed URLs / cookies follow the same idea.

Choosing Express Workflows for Step Functions also makes sense. The flow is high-frequency and short-lived, so it doesn't need Standard Workflow's long-duration persistence and full execution history; Express is cheaper and lower-latency for lightweight orchestration. The slide also mentioned implementing retries in the calling Lambda when the workflow concurrency limit is hit, a pragmatic line of defense in a managed-service architecture.

## AI Chat Moderation: Post-Moderation for a Real-Time Experience

{{< figure src="slide-10-ai-chat-moderation.svg" >}}

{{< figure src="mermaid-10-chat-moderation.svg" >}}

Kustamie also uses Amazon Nova Micro for chat moderation. The pipeline: a user message enters IVS Chat over WebSocket while also flowing through Data Firehose to backend storage; a stream then triggers a Lambda that calls Bedrock. If the model flags a violation, the system updates state and issues a delete-message request to IVS Chat.

This is **post-moderation**, not pre-screening: messages appear first and are judged and deleted asynchronously. It trades a few seconds of safety lag for a real-time chat experience. For a variety show that is acceptable; for higher-risk scenarios (children's content, political streams, financial customer support) you would have to reconsider whether pre-moderation or human review belongs in the loop.

Beyond transport, Firehose also buffers at peak traffic. Variety-show chat surges and ebbs with the show's high points; synchronous per-message moderation would expose model latency to users and amplify Bedrock call peaks. Async stream processing fits this kind of high-frequency, short-latency-tolerant task better.

## Calling Nova Micro: Small Models and Batching

{{< figure src="slide-11-nova-micro.svg" >}}

In the Nova Micro invocation example, the input is a JSON array of multiple messages and the output a structured array in matching order. `categories` being an array means one message can match multiple violation categories at once; an empty array means clean; the `language` field does language identification along the way.

The most notable part is batching. The example batches five messages per call for a total latency of **1.6 seconds**, about 320ms per message on average. But latency isn't the only gain: the system prompt goes out once, and network and Bedrock routing overhead get amortized across the batch, so throughput and cost both improve. For post-moderation, waiting for a few messages to accumulate and then calling the model in a batch is a reasonable trade-off.

Nova Micro fits because the task is high-frequency, low-complexity text classification. It doesn't need complex reasoning or long-context generation; what it needs is to be cheap and fast. In a high-volume chat scenario, judging messages one by one with a large model would be over-engineering.

## Model Selection: Speed, Cost, and the Missing Accuracy Data

{{< figure src="slide-12-service-comparison.svg" >}}

The slide compared several candidates.

Amazon Comprehend Trust and Safety's problem was language support: it is designed for content-safety classification but only supported English at the time, which rules out a Japanese variety show.

Third-party serverless models on Bedrock (Claude included) are strong on multilingual capability, but the presenter found their response times slower. That judgment has real grounding in Kustamie's scenario: Nova Micro is AWS's own small model, and its latency and cost suit high-frequency classification. But the comparison has an obvious gap: no accuracy data.

Content moderation can't be judged on speed alone. Japanese chat is full of homophone wordplay, internet slang, quotes, sarcasm, dialect, and emoji combinations. How often a small model misjudges or misses these edge cases can only be measured against real data. For a variety show with post-moderation like Kustamie, Nova Micro's "fast enough, cheap enough, good enough" may be the right call; carrying the same latency-only criterion into a high-risk business would be incomplete.

This slide also reflects the venue effect of AWS Summit. The whole system runs on AWS, where choosing Nova keeps IAM, monitoring, billing, and internal justification simple; at an AWS flagship event, picking AWS's own foundation model is also the natural narrative.

## Video Moderation Concept: From Every Message to Sampled Frames

{{< figure src="slide-13-video-moderation.svg" >}}

{{< figure src="mermaid-13-video-moderation.svg" >}}

The video moderation section used the word "構想" (concept), meaning it is not a shipped feature yet. The idea: periodically take snapshots from the IVS video stream, hand the images to a multimodal model like Nova Lite for judgment, and notify the organizers based on the result.

Video moderation is much harder than chat moderation. Chat produces discrete events, so every message can be checked. Video is a continuous stream, so you can only sample. Higher sampling frequency means higher cost; lower frequency means brief violations slip through. One frame per second misses almost nothing persistent, but a 3-hour stream is 10,800 frames; one frame per 30 seconds is far cheaper but only catches problems that persist.

Composite frames make judgment harder too. When gameplay, a commentary inset, the streamer's face cam, and text overlays appear together, the model has to understand which region is the main content and which is background. A single-frame snapshot also loses temporal context: a racing crash, a game battle, and real-world violence can look similar in one frame while meaning entirely different things.

So the slide choosing "notify the organizers" rather than auto-stopping the stream is reasonable. The cost of a video false positive far exceeds that of wrongly deleting one chat message. A human in the loop here is a necessary safety valve, not a formality.

## Summary: The Serverless + IVS + Nova Combination

{{< figure src="slide-14-summary.svg" >}}

TBS's recap can be summed up in three layers.

Layer one, large-scale streaming capability: Amazon IVS did the heavy lifting for video distribution and real-time interaction, so the team didn't have to build low-latency video infrastructure themselves.

Layer two, API performance: API Gateway stage cache, Lambda global variables, and ElastiCache for Valkey formed the multi-tier cache, while SQS and Step Functions Express moved expensive work to async paths. The former reduced backend calls; the latter shortened the path users feel.

Layer three, AI safety: Nova Micro handles fast chat moderation, and Nova Lite is folded into the future video-moderation concept. The common thread is putting small models on high-frequency, low-complexity, short-latency-tolerant classification tasks, rather than just "using generative AI."

The slide's last note: Kustamie plans to offer a beta in **fall 2026**. That also means "LOVE it! Bōnenkai '25" was closer to a limited-scale experiment or PoC, still some distance from a publicly available, long-running service.

## What Stood Out

The session's technical value lies in decomposing large-scale interactive streaming into several manageable boundaries.

First, **separation of concerns**. Video, chat, event metadata, and background writes don't share one path. Real-time data went to IVS / IVS Chat; slow-changing data stayed on the API path. That is what made caching and async processing natural rather than propped up by a complex invalidation mechanism.

Second, **load testing modeled on real user behavior**. A fixed RPS or linear ramp mostly proves the system looks fine at steady state; what is actually dangerous in live streaming is the exponential growth in the final minutes before the show. Turning historical event data into a k6 scenario is what surfaced API Gateway throttling, the Lambda scaling rate, and external API rate limits ahead of time.

Third, **re-cutting the synchronous path**. The jump from 12 seconds to 150ms didn't come from bigger machines but from keeping only the UserID and IVS token (the things users need immediately) on the synchronous path and pushing everything else to SQS. A lot of performance problems aren't "things ran too slowly" but "the system synchronously waited on things it didn't have to wait for."

Fourth, **treating control-plane limits as architectural constraints**. With the IVS API capped at 50 TPS and unable to be raised, you can't let every user hit the control plane in real time. Signing tokens locally in Lambda replaces a constrained remote API with verifiable local computation. In large-scale AWS architectures, quotas, rate limits, and cold starts are not afterthoughts; they are constraints that must be designed in from the start.

Finally, **pragmatic use of a small model**. Nova Micro isn't a demonstration that "AI is powerful." It carries a high-frequency, simple, batchable, async-tolerant classification task, chosen on a balance of latency, cost, and "good enough." That said, accuracy data was absent, which is worth remembering with cloud-vendor case studies in general: talks emphasize the happy path, but before replicating anything in your own system you still have to supply your own evaluation of false-positive rates, miss rates, cost, and operational complexity.
