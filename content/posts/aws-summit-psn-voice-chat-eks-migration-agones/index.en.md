+++
date = '2025-06-26T05:25:26+09:00'
draft = false
title = 'How Did PlayStation™Network Voice Chat Migrate to Amazon EKS? — AWS Summit Japan 2025 Session Recap'
seo_description = "A deep dive into how Sony Interactive Entertainment migrated PSN's voice chat (a long-lived-connection application) to Amazon EKS, using Agones to solve session continuity and elastic scaling challenges. AWS Summit Japan 2025 session notes."
tags = ["AWS", "Kubernetes", "cloud-native", "game-dev", "architecture", "AWS Summit Japan 2025"]
categories = ["tech"]
cover = '460ed70d77d3d088c7577b2589f5ae8a.png'
images = ['460ed70d77d3d088c7577b2589f5ae8a.png']
nolastmod = true
+++

## Background

Voice chat is an application that requires a "long-lived connection lifecycle," and migrating this kind of service to Amazon EKS is notoriously difficult. Sony Interactive Entertainment's (SIE) session on migrating the PSN voice chat servers stood out for its technical depth among a sea of watered-down talks (one automaker is still "moving to the cloud," 50% done), and it left a strong impression on me, bringing back memories of my own years wrestling with Kubernetes. Anyway, on to the agenda.

## Agenda

- The common challenges long-lived connection applications face during containerization and cloud-native adoption, especially "session continuity" and "elastic scaling."
- How Agones was used to solve these challenges and successfully migrate the voice chat servers to Amazon EKS.
- How to shift traffic smoothly and flexibly while minimizing impact on users.

## Challenges of Long-Lived Connection Applications

### Characteristics of Long-Lived Connection Applications

- The client establishes and maintains a long-running session with **the same server**, keeping state for the duration of the session.
- The server must hold runtime state for every session, so any server interruption mid-session **severely degrades the user experience (UX)**.
- Whether scaling out or scaling in, **session continuity must come first**.

### Example Scenarios for Long-Lived Connections

- Always-connected applications using WebSocket (online collaboration tools, push notifications).
- Other real-time communication systems such as game servers and video chat.
- Microservices communicating bidirectionally over gRPC streaming.
- Servers that must maintain connections with large fleets of IoT sensors or devices.

### Characteristics of the PSN Voice Chat Servers

- Beyond the session continuity mentioned above, the talk emphasized the "spiky" nature of the traffic. The curve in the graph vividly illustrates how traffic swings violently between peaks and troughs.
- For real-time performance, the communication protocol is **UDP**. This leads to two key points:
    - Clients communicate **directly with the server**, **without going through a load balancer**;
    - Therefore, a mechanism is required to **notify** clients of the server's public IP address and port number.

## Architectural Pain Points

### Pain Points of Operating on Amazon EC2

1. **Difficult cost optimization**: Scaling in while keeping sessions alive is very hard, so AWS's automatic scale-in couldn't be used effectively to save money. On top of that, EC2 instances (virtual machines) boot more slowly than containers, so to absorb sudden traffic (scale-out), they had to keep extra spare servers on standby, pushing costs up even further.
2. **Cognitive load**: The PSN team's other services were already on EKS with cloud-native CI/CD pipelines. But voice chat, this "technical silo," was still stuck on EC2, forcing the team to maintain two completely different tech stacks and operational systems, a huge "cognitive load" and maintenance burden.

### The Three Core Obstacles of Vanilla Kubernetes

- **Guaranteeing session continuity**: Pod rescheduling, or restarts caused by failures, would interrupt in-progress sessions and hurt users.
- **Controlling scale-in / scale-out**: Automatic scale-in could "accidentally kill" Pods that are actively serving users. And if scale-out isn't fast enough, new users end up queuing or failing to connect.
- **Handling UDP traffic**: In K8s, simply exposing a Pod's UDP port to the public internet is already a hassle. And since a Pod's IP and port change with scaling and rescheduling, getting this dynamic address to clients is a major challenge.

{{< gemini >}}

Cloud-native platforms like Kubernetes were designed to manage stateless applications that can be destroyed and recreated at will. Stateful, long-lived-connection applications like voice chat have lifecycle requirements that run counter to K8s' default mechanisms. Classic K8s operations like rolling updates, node maintenance, and automatic scale-in can all be catastrophic for applications that need "sticky sessions."

{{< /gemini >}}

## The Solution: Agones

{{< figure src="picture_pc_cad71d7c7a06955477538efbf300c692.webp" >}}

1. An open-source Kubernetes extension designed for game servers.
2. How it works: it extends K8s with Custom Resource Definitions (CRDs) and custom controllers, letting K8s understand and manage the lifecycle of "session-based, real-time communication" applications (i.e., GameServer Pods).

### Core Capabilities

- **Protecting in-session Pods**: Agones gives Pods session state, ensuring a Pod actively serving users won't be terminated arbitrarily, which guarantees session continuity.
- **Pre-provisioned Pod resources**: With `Fleet` and `FleetAutoscaler`, you can maintain a buffer pool of "warmed-up" Pods. When a traffic peak hits, new servers can be allocated instantly, solving the scale-out latency problem.
- **Assigning public IPs and UDP ports to Pods**: Agones can directly assign each Pod its own public IP and UDP port so clients can connect directly, delivering the UDP direct-connect model described earlier in full.

{{< gemini >}}

- K8s' "session guarantee" problem -> solved by Agones' state protection.
- K8s' "scale-out latency" problem -> solved by Agones' buffer pool (Fleet).
- K8s' "UDP direct-connect" problem -> solved by Agones assigning IPs and ports directly to Pods.

{{< /gemini >}}

## Architecture Diagrams

### The Pre-Migration EC2 Architecture: "Before"

{{< figure src="20250802_174533(9).jpg" >}}

- Client "create/join session" requests are handled by a "routing service" (shown in the diagram as AWS Lambda + ELB).
- The routing service's job is to point all users in the same chat group at **the same EC2 server**.
- To enable UDP direct connections, each EC2 instance is configured with a **fixed Elastic IP (EIP)**.
- Once the client has the IP and port, it bypasses the routing service and sends UDP packets straight to the EC2 server.

### The New Post-Migration Architecture: "Now"

{{< figure src="20250802_174533(10).jpg" >}}

- **Pod management**: Inside EKS, an Agones `Fleet` maintains a buffer pool of Pods in the `Ready` state.
- **Session allocation**: When the routing service (Lambda) receives a session request, it no longer talks to the servers directly. It calls Agones' `Allocator Service`; the allocator pulls a `Ready` Pod out of the `Fleet` and flips its state to `Allocated`.
- **Information relay**: The allocated Pod's connection info (public IP, UDP port) is stored in an **Amazon DynamoDB** table.
- **Routing logic**: The routing service (Lambda) queries DynamoDB, fetches the info of an available Pod, and returns it to the client.
- **Direct communication**: With the dynamically assigned IP and port in hand, the client talks UDP directly to the Pod, just like before.

{{< gemini >}}

- **Core decoupling**: Introducing DynamoDB as a "service registry" cleanly decouples service requests (control plane) from service instances (data plane).
- **Dynamic substitution**: EC2 instances were swapped for Pods in EKS; fixed EIPs were swapped for dynamically assigned IPs.
- **Intelligent scheduling**: Agones plays the role of "intelligent scheduler," handling Pod lifecycle management and buffering to ensure high performance and high availability.

{{< /gemini >}}

## Session Allocation in Depth

### Agones' Design (Dedicated Pods)

{{< figure src="20250802_174533(11).jpg" >}}

- **One session = one Pod**: Agones is designed around assigning a dedicated Pod to each individual session.
- **On-demand scaling**: When a new session is needed, a Pod is pulled from the buffer pool (scale-out); when the session ends, that Pod is destroyed (scale-in).

The problems with dedicated Pods:

- **Increased server cost**: This model is frankly "extravagant." A single session may not consume a whole Pod's minimum resources (especially CPU), which is wasteful. On top of that, every Pod (i.e., every session) must carry a sidecar container, significant overhead in itself.
- **Impact on infrastructure**:
    - **IP address exhaustion in the VPC**: Millions of concurrent sessions mean millions of Pod IPs, putting enormous pressure on the VPC's IP address pool.
    - **Load on etcd and plugins**: All of a Kubernetes cluster's metadata lives in etcd. Creating and destroying millions of Pods places a heavy performance burden on etcd (the cluster's brain) and on various plugins.

### PSN's Actual Design (Shared Pods)

{{< figure src="20250802_174533(13).jpg" >}}

- The goal was to optimize resource efficiency by keeping each Pod running as close to full capacity as possible.
- During off-peak hours, the number of sessions each Pod hosts naturally decreases.
- Multiple independent sessions run inside a single Pod. This essentially implements a lightweight scheduling and management layer inside the Pod.

However, scaling with shared Pods becomes much more complex:

{{< figure src="20250802_174533(14).jpg" >}}

- **Scale-out**: Pod count grows to handle peak traffic. When a new session request arrives, the system looks for a Pod with spare "capacity" to assign it to. The diagram shows a full Pod rejecting new requests while a Pod with vacancies accepts them.
- **Scale-in**: To use Pods efficiently during off-peak hours, scale-in is needed. The diagram shows a "session merge" process: sessions on one Pod can be migrated to another Pod with free slots, and the fully emptied Pod is then destroyed.

{{< gemini >}}

This logic is far more complex than the "one-to-one" model. It requires more sophisticated monitoring and scheduling strategies both inside and outside the Pod. "Session merging" during scale-in, in particular, usually needs application-level support for session migration, or a graceful shutdown that nudges clients to reconnect to a new Pod. This shows the Sony team didn't just use Agones. They built their own higher-level, more refined scheduling system around it. This is genuinely advanced usage.

{{< /gemini >}}

### Agones' Design (Pod State Machine)

{{< figure src="20250802_174533(15).jpg" >}}

- Scheduled -> Ready (waiting for allocation) -> Allocated (assigned, serving a session) -> Shutdown (shutting down) -> Pod deleted.

- Scale-out happens at session start (Ready -> Allocated); scale-in happens after the session ends.

### PSN's Actual Design (Pod State Machine)

{{< figure src="20250802_174533(16).jpg" >}}

- Scale-out logic: when the number of Pods able to accept new sessions drops below a certain threshold, scale-out is triggered.
- **Scale-in logic (the essence)**:
    1. The Pod first enters a "stop accepting new sessions" state.
    2. It then waits for a period of time, letting existing sessions in the Pod end naturally.
    3. If sessions **still** remain in the Pod after the timeout, the system proactively sends a "please reconnect" instruction to these "lingering" clients, guiding them to migrate to other Pods.
    4. Only after all sessions have ended does the Pod enter the `Shutdown` state and get deleted.

{{< gemini >}}

Master-class stuff! This is no longer simple lifecycle management. It's a precise "graceful service decommissioning" process that accounts for all kinds of edge cases. Step 3, "instruct the client to reconnect," in particular, is a proactive and intelligent load "eviction" or "draining" strategy. It minimizes the impact of scale-in operations on online users. It clearly shows that the Sony team are not merely Agones users. They're experts at deep customization and extension.

{{< /gemini >}}

#### Scale-In Implementation Details: Fleet Autoscaler

{{< figure src="20250802_174533(17).jpg" >}}

- `Fleet Autoscaler` monitors the number of `Ready` Pods in a `Fleet`.
    - When a `Ready` Pod is allocated to a session and transitions to `Allocated`, the `Ready` count drops.
    - `Fleet Autoscaler` detects this immediately and automatically creates a new Pod to replenish the `Ready` buffer pool, keeping its size at the preset level.

{{< gemini >}}

The "buffer pool" mechanism is a proactive, predictive approach to scaling, not scrambling to create servers only after users arrive and find none available (reactive scaling). The diagram is clear: when the `Ready` pool drops from 3 to 2, the system immediately tops it back up to 3. This guarantees there's always a server "standing by," keeping user wait times near zero.

{{< /gemini >}}

### Agones' Design (Session Allocation)

{{< figure src="20250802_174533(18).jpg" >}}

- The standard Agones flow: receive a session request -> call the Allocator service to flip a `Ready` Pod to `Allocated` -> fulfill the assignment request.
- This Allocator service processes requests **in batches**, which introduces **up to 500 ms of latency**.
- For a real-time application like voice chat, a half-second delay at startup is **unacceptable** and severely degrades the user experience.

### PSN's Actual Design (Session Allocation)

{{< figure src="20250802_174533(19).jpg" >}}

**Core idea: decoupling!** Separate "a user requesting a session" (an operation demanding an ultra-fast response) from "the system allocating a Pod," a relatively slow background operation.

- A user's session request (via Lambda) no longer directly triggers Pod allocation.
- Lambda queries DynamoDB and immediately fetches an available Pod from **a list of pre-allocated Pods that can accept sessions at any time**.
- The 500 ms allocation operation is completed **in advance, proactively** by the "Pod management service" in the background, which registers the allocated Pod info into the DynamoDB list.

{{< gemini >}}

A classic architectural pattern for solving a latency problem with the "buffer pool" idea. On top of Agones' `Ready` Pod buffer pool, they effectively built a **second buffer pool**: a pool of `Allocated` Pods standing by, ready to serve at any moment (the list in DynamoDB). User requests always draw from this hot "secondary buffer," so the background 500 ms latency stays hidden from users.

{{< /gemini >}}

#### Scale-Out Implementation Details: When to Trigger Auto-Scaling

{{< figure src="20250802_174533(20).jpg" >}}

- **When to stop accepting sessions**: When an individual Pod maxes out on CPU usage or hosted session count, it stops accepting new sessions and is removed from the DynamoDB available list.
- **When to trigger background scale-out**: The Pod management service continuously monitors the number of "Pods that can accept new sessions" in DynamoDB. Once that number **drops below a configured threshold**, it immediately requests new Pods from Agones' Allocator service, runs through the 500 ms flow, and adds the freshly prepared Pods to the DynamoDB list for future use.

{{< gemini >}}

This is their custom "two-tier auto-scaling" logic. Here's an analogy:

- **Agones**: like a flour mill, continuously producing "dough" (`Ready` Pods).
- **Pod management service**: like the bakery's back kitchen. It anticipates foot traffic and bakes the "dough" into "bread" (`Allocated` Pods) ahead of time, lining them up on the counter.
- **Routing service (Lambda)**: like the front-of-house clerk. When a customer (user) walks in, they hand over a ready-made "bread" straight from the counter, with no waiting for the kitchen to bake.
- This "Pod management service" is the bakery manager, watching the bread count on the counter and rushing an order to the kitchen the moment it runs low. A mature, robust two-tier buffered scaling system.

{{< /gemini >}}

#### Scale-In Implementation Details: "Graceful Draining"

{{< figure src="20250802_174533(21).jpg" >}}

- A Pod is serving multiple sessions normally.
    - The system decides to scale it in, so the Pod enters "stop accepting new sessions" mode.
    - Over a period of time, some sessions end naturally and the Pod's load drops.
    - After the timeout, for the "holdout" sessions still remaining, the system proactively issues a "please reconnect" instruction.
    - Upon receiving the instruction, clients re-request the routing service and get assigned to a new, healthy Pod.
    - The original Pod is fully emptied and eventually deleted safely.

{{< figure src="20250802_174533(22).jpg" >}}

- When the Pod management service detects that an `Allocated` Pod needs to stop accepting sessions (for example, because it's full or has been selected as a scale-in target), it **directly deletes that Pod's entry from the DynamoDB available list**.
- Once the entry is deleted, the routing service (Lambda) can no longer find that Pod when querying DynamoDB, so naturally no new session requests get sent to it.

## Containerizing the Voice Chat Server

{{< figure src="20250802_174533(23).jpg" >}}

- **Networking**: Because it's UDP traffic, they used `hostPort` to expose the Pod's port directly on the host Node. The IP address is an EIP attached to the **Node**.
- **Integration**: The Agones SDK runs as a **sidecar container**, packaged in the same Pod as the main application container. This sidecar communicates with the Agones control plane for state management and to obtain the IP/port.

- **Architecture comparison**:
    - **Left (EC2)**: one process per EC2 instance, monopolizing one EIP.
    - **Right (EKS)**: multiple Pods can run on a single Node. Each Pod consists of "app container + Agones sidecar." These Pods share the Node's EIP but are distinguished by different `hostPort`s.

### How the IP Address / Port Is Obtained

- **EC2 era**: the IP was fetched from the instance metadata service, and the port number was fixed.
- **EKS era**: obtained through the Agones SDK Server. And to give Node instances a fixed public IP (EIP), they designed an automation script:

    1. Prepare a pool of EIPs in advance, tagged with a specific tag.
    2. When an EKS Node boots (before the K8s components run), a `userdata` script runs AWS CLI commands.
    3. The command finds an EIP carrying that tag that isn't already attached, and attaches it to the booting Node.

## Challenges at Launch

- Guiding principles:
    - **The service must never go down.**
    - **Impact on existing users must be minimized.**
    - **If something goes wrong, there must be a way to roll back immediately.**
    - **Keep observing after the switch, migrating gradually while confirming safety.**

{{< figure src="20250802_174533(26).jpg" >}}

- Traffic switchover
	- **Phased traffic shifting**: At the routing service (Lambda) layer, user requests were split by percentage between the old EC2 cluster and the new EKS cluster.
	- **Gradually increasing the ratio**: With extreme caution, they shifted traffic onto the new system bit by bit: **0.01% -> 0.1% -> 1%**.
	- **Close monitoring and one-click rollback**: At each stage, key metrics like connection error rate and latency were closely watched. The moment anything looked off, the EKS traffic ratio was dialed back to **0%**, a rollback in seconds.

## Going Hybrid Cloud

{{< figure src="20250802_174533(29).jpg" >}}

- **Background and goal**: After migrating to EKS, **cost optimization** became the next major topic. Voice chat is a CPU-intensive service, so compute costs are high. Meanwhile, SIE operates **its own on-premises data centers** around the world for streaming services. Their ultimate goal is to leverage these on-prem resources, build a hybrid cloud, and cut costs further.
- **Hybrid cloud architecture**:

    1. Build a Kubernetes + Agones environment inside the on-prem data centers as well.
    2. The core "Pod management service" and "routing service" are deployed **only in the AWS cloud**, acting as the unified "control brain."
    3. This cloud "brain" can manage and schedule traffic to both the AWS EKS and the on-prem K8s clusters simultaneously.

{{< gemini >}}

They turned the application itself (the voice chat server) into a standardized "shipping container" that can run anywhere. Depending on cost, load, and other factors, this "container" can be unloaded at AWS's dock (EKS) or at their own dock (on-prem). Keeping the control plane in the cloud while distributing the data plane is a mature, forward-thinking hybrid cloud architecture.

{{< /gemini >}}

## Summary

- **What was done**: The session covered migrating the voice chat servers to EKS and switching over traffic. Agones solved the hard problems of session continuity, scaling, and UDP communication; on top of that, a custom "Pod management service" enabled the advanced "multiple sessions per Pod" model and pushed latency optimization to the limit.
- **How it was done**: Phased traffic shifting minimized the impact on users.
- **Final results**:
    1. **Performance targets met**: Even after implementing complex scaling controls, connection error rates and latency held a level "no worse than" the previous EC2 architecture.
    2. **Efficiency gains**: They can now use the same CI/CD pipeline as the other services, reducing the team's "cognitive load" and improving development and operations productivity.
