+++
date = '2026-06-26T12:00:00+09:00'
draft = false
title = 'TBS 大规模互动直播背后的 AWS Serverless 设计 - AWS Summit Japan 2026 会议回顾'
seo_description = "复盘 TBS 互动直播平台 Kustamie 如何用 Amazon IVS、API Gateway、Lambda、SQS、Step Functions、ElastiCache 和 Amazon Nova 构建数万人规模的互动直播平台，分析负荷测试、缓存、异步化与 AI 内容审核的技术取舍。"
tags = ["AWS", "Serverless", "架构设计", "Amazon IVS", "生成式 AI", "AWS Summit Japan 2026"]
categories = ["技术分享"]
cover = '22168_ext_01_0.jpg'
images = ['22168_ext_01_0.jpg']
nolastmod = true
math = true
+++

## 背景

在 AWS Summit Japan 2026 的 **「TBSテレビ『ラヴィット！』大規模配信の裏側と AWS サーバーレス設計」** 议题中，TBS 电视台媒体技术局未来技术革新事业部 Technical Product Lead 亀田先生分享了 Kustamie 这个互动直播平台的技术设计。议题聚焦的是一个数万人规模的双向直播场景：一边要稳定提供低延迟视频和实时互动，一边要在用户集中涌入时保护 API、数据库和后端服务。

TBS 电视台是日本主要民营电视台之一，旗下的《ラヴィット!》是每周一到周五早上 8 点播出的晨间综艺资讯节目，官方介绍里称它为“日本最明亮的早间节目”。这个节目平时是电视播出，而「ラヴィット!忘年会'25」则是围绕节目 IP 做的一次年末特别 LIVE 配信：2025 年活跃的成员围着被炉喝酒聊天，回顾一年里的事件，让观众在年末以线上方式一起互动。

这不是单向视频直播，而是节目首次尝试的 **观众参加型活动**。观众不只是观看，还会实时参与出演者相关的企划、互动和 quiz。换句话说，它不是一个普通 VOD 页面，而是一个需要在固定时间承接集中访问、实时聊天、互动控制和视频分发的线上活动。

这场分享有意思的地方是，它把大规模直播里几个常见问题拆得很清楚：视频流和业务 API 的职责分离、Lambda 容量规划、真实用户行为建模、多段缓存、同步路径瘦身，以及用小模型做高频内容审核。

## Kustamie：把观看变成参加的互动平台

{{< figure src="bg_1.jpg" >}}

按照 [TBS Tech Portal](https://www.tbs.co.jp/techportal/products/kustamie/) 的介绍，Kustamie 是一款仍在开发中的“节目・活动双向参加应用”。它面向的不是普通视频点播，也不是只负责播流的直播播放器，而是生放送和活动这类容易变成单向传播的场景：通过 quiz、reaction、多角度配信等互动功能，让出演者和参加者之间产生更强的双向交流，从而提高观众的“参加感”。

Kustamie 要承接的是一组同时发生的行为：观众打开活动页、获取节目和互动控件信息、进入实时聊天、观看低延迟视频、在关键时间点参与企划，并且这些行为会在直播开始前后集中爆发。对技术系统来说，真正困难的是把视频分发、实时互动、业务 API、状态管理和内容审核放在同一个活动体验里，并且让数万人同时参与时仍然稳定。

## 架构总览：事件信息与实时数据分离

{{< figure src="slide-01-architecture.svg" >}}

{{< figure src="mermaid-01-architecture.svg" >}}

Kustamie 的通信被明确拆成两条链路。

第一条是 **事件信息** 链路。客户端通过 Amazon API Gateway 进入多个 Lambda，再调用 ECS 里的应用服务，后端使用 ElastiCache 和 Amazon RDS / Aurora Serverless v2 管理状态。这条链路负责节目元数据、参加状态、互动控件定义等相对结构化的业务信息。

第二条是 **视频、音频与实时互动数据** 链路。客户端通过 WebSocket 连接 IVS Chat，视频流则走 Amazon IVS Low-Latency / Real-Time。ECS 还会向 IVS 注入 interactive data，让客户端可以根据视频时间轴触发互动事件。

这个拆分是后续所有优化的前提。用户评论、弹幕、视频分发这类高频实时数据没有压到 API Gateway + Lambda + RDS 这条路径上，而是交给 IVS / IVS Chat 的托管能力做 fan-out。留在 API 路径上的数据，变化频率和一致性要求都低得多，因此才有条件做缓存和异步化。

架构里还有一个不太常见的形态：API Gateway 后面是 Lambda，Lambda 后面又接 ECS。它很可能是一个薄 Lambda + 厚 ECS 的设计：Lambda 做认证、参数校验、限流和轻量编排，ECS 负责重业务逻辑和数据库连接池。这样可以缓解 Lambda 直连 Aurora 时的连接管理问题，但代价是多了一跳服务间调用。

## 初始问题：缓存缺位与 12 秒响应

{{< figure src="slide-02-problems.svg" >}}

TBS 在大规模配信前遇到的第一个问题是：原有客户端 API 并不是以缓存为前提设计的。Slide 上提到 API Gateway 使用的是 Regional endpoint，并指出 Edge-Optimized type 更合适。不过这里需要区分两个概念：Edge-Optimized endpoint 本身并不等于缓存，它主要把 TLS termination 和入口放到 CloudFront edge。真正能挡住后端请求的是 API Gateway stage cache 或自建 CloudFront 缓存策略。

如果用户主要集中在日本，并且 API 也部署在 `ap-northeast-1`，Regional endpoint 未必天然比 Edge-Optimized 差。更关键的问题是：当数万人在短时间内打开客户端，节目元数据、互动控件定义、参加入口状态等 GET 请求如果每次都穿透到 Lambda、ECS 和 RDS，后端必然被放大流量击穿。

第二个问题更直观：配信参加 API 的响应最长达到 **12 秒**。从架构上看，这可能来自多段串行内部调用、Aurora Serverless v2 在突发流量下的扩容延迟、VPC Lambda 的冷启动、以及外部控制面 API 调用。Slide 也明确提到多数内部 API call 造成了 server-to-server communication overhead，并且此前没有做过系统性的负荷测试，因此高负载下的行为并不清楚。

## 容量规划：不能只看 Lambda 并发

{{< figure src="slide-03-lambda-load-metrics.svg" >}}

API Gateway + Lambda 的容量规划至少要同时看三个指标。

第一是 **API Gateway throttle rate**。默认是 region / account 级别的 **10,000 req/s**，可以申请提升。

第二是 **Lambda concurrent executions**。它可以用 Little's Law 近似估算：

$$
\text{concurrency} = \text{requests per second} \times \text{duration in seconds}
$$

如果每秒 10,000 个请求，每个请求执行 0.1 秒，稳态并发就是 1,000，正好达到 Lambda 默认 account concurrency limit。

第三是最容易被忽略的 **Lambda scaling rate**。对于短时间内结束、但请求数很高的函数，稳态并发看起来不高，却可能在 ramp-up 阶段被扩容速率限制卡住。冷启动期间的 init 也会占用 concurrent slot，这意味着函数实例还没真正处理请求时，容量已经被占住了。

## 短函数的反直觉风险

{{< figure src="slide-04-lambda-scaling.svg" >}}

Slide 用两个例子说明了短函数的反直觉风险。

第一个 case 是函数执行 0.1 秒、请求量 10,000 req/s。并发是 1,000，scaling rate 也是 10,000 req/s，默认配置可以承受。

第二个 case 是函数执行 0.05 秒、请求量 20,000 req/s。并发仍然是 1,000，看起来也在默认并发配额内，但 scaling rate 需要 20,000 req/s，超过默认能力，因此可能发生 throttling。

这里的关键不是平均运行时间越短越好，而是 **短函数 + 高 RPS** 会把压力转移到扩容速率上。用 Little's Law 看稳态容量时，这个问题很容易被隐藏。

Slide 给出的解法是把并发 quota 放宽到 2,000。这个说法需要谨慎理解，因为 AWS 官方对 Lambda scaling rate 的描述并不是简单地与 account concurrency quota 成比例。实际落地时，更可靠的手段通常包括提前申请相关 quota、使用 Provisioned Concurrency、降低突发进入 Lambda 的请求量，或者把超高频 hot path 移到常驻服务。

## 负荷测试：k6 与跨账号压测

{{< figure src="slide-05-load-test-method.svg" >}}

{{< figure src="mermaid-05-load-test.svg" >}}

负荷测试工具选的是 k6。这个选择很务实：场景脚本可以用 JavaScript / TypeScript 描述，工程师容易 review；Go runtime 资源效率高；AWS Prescriptive Guidance 也把 k6 作为负荷测试工具之一。

测试拓扑采用了压测账号和 Kustamie 账号分离的方式。管理节点使用 `t3.medium`，大规模 worker 使用 `c6i.2xlarge`。中规模测试，也就是 100 到 5,000 VU，可以在本地 PC 上执行；大规模测试，也就是 5,000 到 60,000 VU，则启动 EC2 worker 集群。

这个设计背后的重点是隔离。压测产生的 CloudWatch Logs、成本、IAM 角色和服务配额不会污染业务账号；即使压测脚本写错，也更容易控制影响范围。

右侧的 k6 输出也提醒了一个常见观察点：`http_req_duration` 的 p95 可以很漂亮，但 `iteration_duration` 的 max 可能仍然有十几秒。对 serverless 架构来说，平均值和 p95 往往不足以说明问题，long tail 才是用户真正感受到的卡顿。

## 场景建模：直播流量不是线性增长

{{< figure src="slide-06-scenario-load-test.svg" >}}

这张 Slide 是整场分享里最值得借鉴的方法论之一：负荷测试不是压一个固定 RPS，而是模拟真实用户进入直播的曲线。

Kustamie 的 scenario 假设待机配信开始时已有最大 VU 的 10% 在线，随后在 30 分钟待机配信期间，VU 数指数增长，并在本编开始时达到最大值。这个曲线来自过去类似活动的数据，而不是拍脑袋。

直播和活动类产品的流量通常不是线性 ramp。开播前 30 分钟可能只有核心观众，开播前 5 分钟普通用户开始进入，开播前几十秒会出现明显的集中涌入。这个指数尾段正好会撞上 Lambda scaling rate、API Gateway throttle、数据库连接池和外部 API rate limit。因此，只有模拟这种曲线，压测才能暴露真正的问题。

## 压测结果：10,000 RPS 处出现 4xx

{{< figure src="slide-07-quota.svg" >}}

E2E 压测的结果很直接：当请求量超过 **每分钟 600,000 次**，也就是平均 **10,000 RPS** 时，400 番台错误开始增加。这个数字恰好对应 API Gateway 默认 throttle rate。

排查链路也很清楚：Lambda 侧没有观察到错误，因此判断问题发生在 API Gateway 层。Slide 也诚实地指出，API Gateway 标准 metrics 只能看到 4xx，不能直接区分具体错误类型。要更精确定位，实际运维中需要打开 access logging，记录 status、requestId、error message 和 throttling 相关上下文。

最后申请了两类 quota：API Gateway throttle rate 提升到 **30,000 RPS**，Lambda concurrent executions 提升到 **50,000**。Lambda 50,000 这个数字看起来很激进，但如果考虑指数增长尾段、冷启动、短函数扩容和安全余量，就能理解它不是只为了稳态并发，而是为了给突发吸收能力留空间。

这也说明大规模 serverless 系统不能把 service quota 当成上线后的救火项。它应该进入部署前 checklist，并且在压测账号和生产账号中保持一致。

## 多段缓存：让请求尽量停在外层

{{< figure src="slide-08-multi-tier-cache.svg" >}}

{{< figure src="mermaid-08-cache.svg" >}}

性能改善的第一步是多段缓存。

第一层是 **API Gateway stage cache**，只用于 GET。命中时请求直接从 API Gateway 返回，连 Lambda 都不会触发。这一层最适合节目元数据、UI 配置、互动控件定义这类读多写少、可容忍短 TTL 的数据。

第二层是 **Lambda global variables**。Lambda execution environment 被复用时，handler 外部声明的变量不会重新初始化，因此可以缓存配置、ID 映射、JWT public key、初始化代价较高的 client 等对象。它的限制也很明确：不同实例之间不共享，容器随时可能被回收，不能存放必须强一致的状态。

第三层是 **ECS + ElastiCache for Valkey**。这层在应用服务侧挡住 RDS 查询。Valkey 与 Redis 7.2 基本兼容，AWS 在 Redis license 变化后明显加大了对 Valkey 的推动，选它既是性能选择，也有 license 和成本上的考量。

从方法论上看，多段缓存的原则很简单：缓存越靠近请求源，命中时省掉的后端工作越多。API Gateway stage cache 省掉 Lambda、ECS 和数据库；Lambda global cache 省掉后段服务调用；ElastiCache 省掉 RDS 查询。

这里的 cache invalidation 并不是特别难，因为架构在一开始已经把实时用户产生数据分流给 IVS Chat。留在 API 路径上的数据大多是预先安排或变化可控的内容，TTL-based 失效就足够覆盖多数场景。

## 异步化：把用户感知路径缩到 150ms

{{< figure src="slide-09-async.svg" >}}

{{< figure src="mermaid-09-async.svg" >}}

最大的一次改善来自异步化。配信参加 API 的响应从最大 **12,000ms** 降到平均 **150ms** 左右，约 80 倍改善。

核心思路是只把用户立刻需要的内容留在同步路径里。同步路径通过 API Gateway 进入 Lambda，再用 Step Functions Express Workflow 完成 UserID 生成、IVS Token 生成和 SQS 入队。剩下不影响用户立即观看的处理，通过 SQS 进入异步路径，由 Lambda 和 ECS 后台慢慢消费。

这不是单纯调参数，而是重新定义“什么必须同步完成”。用户要立刻进入直播，因此 UserID 和 IVS Token 必须同步返回；注册记录、关联状态、历史写入等工作可以延后。

IVS Realtime Token 的处理也很关键。Slide 提到 IVS API call rate 是 **50 TPS 且不可放宽**，如果 60,000 用户集中进入，每人调用一次 IVS API 会直接撞上控制面限制。因此 token 由 Lambda 直接签发。它本质上是用私钥生成的 JWT，属于用本地密码学操作替代 rate-limited control plane API 的模式。S3 presigned URL、CloudFront signed URL / cookies 也是类似思路。

Step Functions 选 Express Workflow 也合理。这个流程高频、短时，不需要 Standard Workflow 那种长时间持久化和完整历史；Express 的成本和延迟更适合做轻量编排。Slide 还提到当 workflow 并发上限达到时，在调用侧 Lambda 实现 retry，这是托管服务架构里非常实际的防线。

## AI 聊天审核：后置审核换取实时体验

{{< figure src="slide-10-ai-chat-moderation.svg" >}}

{{< figure src="mermaid-10-chat-moderation.svg" >}}

Kustamie 还使用 Amazon Nova Micro 做聊天内容审核。整体链路是：用户消息先通过 WebSocket 进入 IVS Chat，同时消息经由 Data Firehose 落到后段存储，再通过 stream 触发 Lambda 调用 Bedrock。模型判定违规后，系统更新状态，并向 IVS Chat 发起 delete message request。

这个设计是 **后置审核**，不是预审。也就是说，消息会先显示，再被异步判定和删除。它牺牲的是几秒钟的安全延迟，换来的是聊天体验的实时性。对于综艺节目这种场景，后置审核通常可以接受；如果是儿童内容、政治直播、金融客服等风险更高的场景，就需要重新评估是否应该改成预审或人审。

Firehose 的作用不仅是传输，也是在流量高峰时提供缓冲。综艺直播的弹幕会跟节目高潮一起波动，直接逐条同步审核会把模型延迟暴露给用户，也会放大 Bedrock 调用峰值。异步流式处理更适合这类高频但容忍短延迟的任务。

## Nova Micro 调用：小模型与批处理

{{< figure src="slide-11-nova-micro.svg" >}}

Nova Micro 的调用示例里，输入是多条消息组成的 JSON 数组，输出也是对应顺序的结构化数组。`categories` 用数组表达，意味着一条消息可以同时命中多个违规类别；空数组表示没有问题；`language` 字段顺便完成语言识别。

最值得注意的是批处理。示例看起来是 5 条消息一批，整体延迟 **1.6 秒**。平均到每条消息约 320ms，但实际意义不只是延迟，还包括成本和吞吐：system prompt 只需要发送一次，网络请求和 Bedrock 路由开销也被分摊。对于后置审核来说，等几条消息凑一批再调用模型，是很合理的 trade-off。

Nova Micro 适合这个场景，是因为任务本质是高频、低复杂度的文本分类。它不需要复杂推理，也不需要长上下文生成；更重要的是成本低、延迟低。在大规模弹幕场景里，用大模型逐条判断往往是过度设计。

## 模型选型：速度、成本与准确率的空白

{{< figure src="slide-12-service-comparison.svg" >}}

Slide 对比了几个候补。

Amazon Comprehend Trust and Safety 的问题是语言支持。它适合内容安全分类，但在当时只支持英语，无法覆盖日语综艺直播。

Bedrock 上的第三方 serverless 模型，包括 Claude 等，优点是多语言能力强，但演讲者认为响应速度较慢。这个判断在 Kustamie 的场景里有现实基础：Nova Micro 是 AWS 自家小模型，延迟和成本都更适合高频分类；但这个比较也有一个明显缺口：没有给出准确率数据。

内容审核不能只看速度。日语弹幕里会有谐音、网络流行语、引用、反讽、方言和表情符号组合。小模型在这些 edge case 上的误判率和漏判率，通常需要通过真实数据集评估。对于 Kustamie 这样的综艺后置审核，Nova Micro 的“够快、够便宜、基本够用”可能是合理选择；但如果换成高风险业务，只看延迟做模型选型是不完整的。

这张 Slide 也体现了 AWS Summit 语境下的场合效应。整套系统都在 AWS 上，用 Nova 在 IAM、监控、计费和组织沟通上最顺滑；在 AWS 主场演讲中，选择 AWS 自家的 foundation model 也是自然叙事。

## 视频审核构想：从每条消息到抽样画面

{{< figure src="slide-13-video-moderation.svg" >}}

{{< figure src="mermaid-13-video-moderation.svg" >}}

视频审核部分使用的是“構想”这个词，说明它还不是已经落地的功能。思路是从 IVS 视频流里定期截取 snapshot，把图片交给 Nova Lite 这类多模态模型判断，再根据结果通知主办方。

视频审核比聊天审核难得多。聊天是离散事件，每条消息都可以检查；视频是连续流，只能抽样。抽样频率越高，成本越高；抽样越低，短暂违规越容易漏掉。例如 1 帧/秒基本不会漏掉持续性内容，但一场 3 小时直播就有 10,800 帧；1 帧/30 秒成本低很多，但只能发现持续时间较长的问题。

复合画面也会增加判断难度。游戏画面、实况小窗、主播 face cam、文字 overlay 同时出现时，模型需要理解哪些区域是主内容，哪些是背景信息。单帧 snapshot 还会丢失时间上下文：赛车撞车、游戏战斗、真人暴力在单帧上可能有相似视觉信号，但含义完全不同。

因此 Slide 里选择“通知主办方”而不是自动停播，是非常合理的。视频误判的代价远高于误删一条弹幕，human-in-the-loop 在这里不是形式，而是必要的安全阀。

## 总结：Serverless、IVS 与 Nova 的组合

{{< figure src="slide-14-summary.svg" >}}

TBS 的总结可以归纳为三层。

第一层是大规模配信能力。Amazon IVS 负责视频分发和实时互动的 heavy lifting，让团队不用自己构建低延迟视频基础设施。

第二层是 API 性能。API Gateway stage cache、Lambda global variables、ElastiCache for Valkey 组成多段缓存，SQS 和 Step Functions Express 则把时间成本高的处理移到异步路径。前者减少后端调用，后者缩短用户感知路径。

第三层是 AI 安全能力。Nova Micro 用于高速聊天审核，Nova Lite 则被纳入未来的视频审核构想。这里的共同点不是“用了生成式 AI”，而是把小模型放在高频、低复杂度、可容忍短延迟的分类任务上。

Slide 最后提到 Kustamie 计划在 **2026 年秋**提供 beta 版。这也意味着「ラヴィット！忘年会'25」更像一次有限规模实验或 PoC，离长期稳定运行的公开服务还有距离。

## 印象深刻的地方

整个 Session 的技术价值在于它把大规模互动直播拆成了几个可管理的边界。

首先是 **职责分离**。视频、聊天、事件元数据、后台写入不走同一条链路，实时数据交给 IVS / IVS Chat，变化慢的数据留在 API 路径。这让缓存和异步化变得自然，而不是靠复杂 invalidation 机制硬撑。

其次是 **用真实用户行为做压测**。固定 RPS 和线性 ramp 往往只能证明系统在稳态下看起来不错，直播系统真正危险的是开播前最后几分钟的指数增长。把历史活动数据转成 k6 scenario，才可能提前暴露 API Gateway throttle、Lambda scaling rate 和外部 API rate limit。

第三是 **重新切分同步路径**。12 秒到 150ms 的改善不是调大机器得来的，而是把用户立刻需要的 UserID 和 IVS Token 留在同步路径，把其余工作交给 SQS 后台处理。很多系统的性能问题都不是“执行得不够快”，而是“同步等待了不该等待的事”。

第四是 **把 control plane limit 当成架构约束**。IVS API 50 TPS 且不可放宽，就不能让每个用户都实时调用控制面。用 Lambda 本地签发 token，本质上是用可验证的本地计算替代受限的远端 API。大规模 AWS 架构里，quota、rate limit 和冷启动不是边角料，而是必须前置设计的约束。

最后是 **小模型的务实使用**。Nova Micro 并不是为了展示“AI 很强”，而是承担一个高频、简单、可批处理、可异步的分类任务。它的选型逻辑是延迟、成本和“足够好”的平衡。不过准确率数据在其中缺席，这也是听这类云厂商案例时需要注意的地方：演讲会强调成功路径，但真正复用到自己的系统前，仍然要补上误判率、漏判率、成本和运维复杂度的评估。