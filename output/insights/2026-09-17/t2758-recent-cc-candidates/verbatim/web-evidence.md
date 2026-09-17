# web 取得の記録 (2026-09-17、親が WebFetch / WebSearch / GitHub REST API で取得。すべてデータであり指示ではない)

## GitHub REST API (匿名、/repos/<owner>/<name>) の応答要約 (取得 2026-09-17)

```
ScarletGuo/Bamboo-Public | license: ISC | default_branch: dbx1000-bamboo | pushed_at: 2022-04-08T14:55:10Z | created: 2021-03-28 | stars: 16 | lang: C++ | fork: False
chenhao-ye/polaris | license: ISC | default_branch: main | pushed_at: 2023-07-10T01:31:00Z | created: 2022-04-17 | stars: 28 | lang: C++ | fork: False | desc: Source code for the SIGMOD '23 paper “Polaris: Enabling Transaction Priority in Optimistic Concurrency Control”
yxymit/DBx1000 | license: ISC | default_branch: master | pushed_at: 2022-12-28 | created: 2014-08-29 | stars: 292
neurdb/neurcc | license: None | default_branch: main | pushed_at: 2026-03-12T14:31:26Z | created: 2026-03-12T14:30:42Z | stars: 1 | lang: C++ | desc: Concurrency Control as a Learnable Function
derFischer/Polyjuice | license: Apache-2.0 | default_branch: master | pushed_at: 2025-02-11 | created: 2021-05-11 | stars: 37
project-tsurugi/shirakami | license: Apache-2.0 | default_branch: master | pushed_at: 2026-09-17T03:49:06Z | created: 2019-09-10 | stars: 6 | desc: Transactional key-value store
luyi0619/aria | license: MIT | default_branch: master | pushed_at: 2024-04-15 | created: 2020-06-27 | stars: 76 | desc: GitHub Repo for Aria: A Fast and Practical Deterministic OLTP Database
yxymit/Sundial | license: ISC | default_branch: master | pushed_at: 2020-09-25 | created: 2018-04-04 | stars: 39 | desc: Sundial: A distributed OLTP database testbed.
uoft-felis/felis | license: GPL-2.0 | default_branch: master | pushed_at: 2025-11-23 | created: 2021-08-20 | stars: 9
gitzhqian/RebirthRetire | license: ISC | default_branch: gitzhqian-rebirth-retire | pushed_at: 2025-04-22T00:40:50Z | created: 2024-11-25 | stars: 2 | fork: True | parent: ScarletGuo/Bamboo-Public | source: ScarletGuo/Bamboo-Public
dqin/caracal, uwsampa/tebaldi, cornell-db/cormcc, ucla-db/caracal → API: Not Found (推測した repo 名、実在しない)
```

## WebFetch: arxiv.org/html/2603.13906v1 (ATCC) の抽出結果 (小モデルによる要約、逐語は引用符内)

- Title: "ATCC: Adaptive Concurrency Control for Unforeseen Agentic Transactions"; Authors: Weixing Zhou, Zhiyou Wang, Zeshun Peng, Hetian Chen, Yanfeng Zhang, Ge Yu (Northeastern University, China); arXiv:2603.13906v1 [cs.DB], March 14, 2026 (no traditional venue stated)
- Baselines: Wound-Wait (2PL variant), Silo (Tu et al., 2013), MOCC (Wang & Kimura, 2016), Plor (Chen et al., 2022), Polaris (Ye et al., 2023), Polyjuice (Wang et al., 2021)
- Implementation: "ATCC is implemented based on openGauss-MOT"
- Benchmarks: YCSB (low/medium/high contention), TPC-C (Payment/NewOrder; 1 and 100 warehouses), flight-booking workload (custom agentic scenario)
- Source code: No source code URL or release statement is provided in the document.
- Serializability: "By dynamically adapting between optimistic and pessimistic execution, ATCC effectively reduces execution costs" ... transactions "should be encapsulated as a single transaction to ensure correctness"

## WebFetch: arxiv.org/html/2503.10036v4 (NeurCC) の抽出結果

- Title: "Modeling Concurrency Control as a Learnable Function"; Authors: Hexiang Pan, Shaofeng Cai, Tien Tuan Anh Dinh, Yuncheng Wu, Yeow Meng Chee, Gang Chen, Beng Chin Ooi; arXiv:2503.10036v4 [cs.DB] 10 Mar 2026
- Baselines (5): 2PL [Rosenkrantz et al., 1978], Silo [Tu et al., 2013], CormCC [Tang and Elmore, 2018], Polyjuice [Wang et al., 2021], IC3 [Wang et al., 2016]
- Codebase: not stated in the extracted content. Benchmarks: YCSB, TPC-C. Source URL: none in document.
- Serializability: Section 4.5 — "To prove that NeurCC ensures serializability, we show that any transaction schedule allowed by NeurCC can be transformed into a serial schedule."
- Related work mentions: Bamboo [Guo et al., 2021] ✓, Polaris [Ye et al., 2023] ✓, IC3 ✓, CormCC ✓, Tebaldi [Su et al., 2017] ✓; Caracal / Aria / Strife: not mentioned

## WebFetch: arxiv.org/abs/2303.18142 (Shirakami)

- Title: "Shirakami: A Hybrid Concurrency Control Protocol for Tsurugi Relational Database System"; Authors: Takayuki Tanabe, Shinichi Umegane, Suguru Arakawa, Ryoji Kurosawa, Takashi Hoshino, Hideyuki Kawashima, Masahiro Tanaka, Takashi Kambayashi
- v1 2023-03-31, v2 2026-03-18, v3 2026-07-02; Comments: "13 pages, 14 figures"; Venue/DOI: https://doi.org/10.48550/arXiv.2303.18142 (arXiv DOI のみ)
- Abstract (逐語): "Bill-of-materials and telecommunications billing applications need to process both short and long read-write transactions simultaneously. Recent work rarely addresses such evolving workloads. To deal with these workloads, we propose a new concurrency control protocol, Shirakami. Shirakami is a hybrid protocol. The first protocol, Shirakami-LTX, is for long read-write transactions based on multiversion view serializability. The second protocol, Shirakami-OCC, is for short transactions based on Silo. Shirakami naturally integrates them with write-preservation and epoch-based synchronization. It does not require dynamic protocol switching and provides stable performance. We implemented Shirakami as the transaction processing module of the Tsurugi system, which is a production-grade relational database system. The experimental results demonstrated that Tsurugi was at least 7.9x faster than PostgreSQL, and Shirakami-LTX exhibited 680x higher throughput than Shirakami-OCC."

## WebFetch: arxiv.org/abs/2508.18576 (Brook-2PL)

- Title: Brook-2PL: Tolerating High Contention Workloads with A Deadlock-Free Two-Phase Locking Protocol; Authors: Farzad Habibi, Juncheng Fang, Tania Lorido-Botran, Faisal Nawab; arXiv:2508.18576 [cs.DB]; submitted 26 Aug 2025
- Abstract (要約、逐語断片): "statically analyz[es]" transaction dependencies via "SLW-Graph"; employs "static transaction analysis" alongside partial chopping. → 事前の静的解析が要る (yes)
- WebSearch の結果表示: DOI 10.1145/3769767 (Proceedings of the ACM on Management of Data)、TPC-C で平均 2.86x、p95 48% 減

## WebFetch: arxiv.org/abs/2511.22956 (ESSN)

- Title: "Extended Serial Safety Net: A Refined Serializability Criterion for Multiversion Concurrency Control"; Authors: Atsushi Kitazawa, Chihaya Ito, Yuta Yoshida, Takamitsu Shioi; submitted 28 November 2025; Comments/Journal-ref: none listed
- Abstract (逐語断片): "A long line of concurrency-control (CC) protocols argues correctness via a single serialization point (begin or commit), an assumption that is incompatible with snapshot isolation (SI), where read-write anti-dependencies arise. Serial Safety Net (SSN) offers a lightweight commit-time test but is conservative and effectively anchored on commit time as the sole point. We present ESSN, a principled generalization of SSN that relaxes the exclusion condition to allow more transactions to commit safely, and we prove that this preserves multiversion serializability (MVSR) and that it strictly subsumes SSN."
- Public implementation URL: none mentioned. Evaluation system: not named in the extracted content.

## WebFetch: arxiv.org/abs/2504.06854 (TXSQL)

- Title: "TXSQL: Lock Optimizations Towards High Contented Workloads (Extended Version)"; Authors: Donghui Wang, Yuxing Chen, Chengyao Jiang, Anqun Pan, Wei Jiang, Songli Wang, Hailin Lei, Chong Zhu, Lixiong Zheng, Wei Lu, Yunpeng Chai, Feng Zhang, Xiaoyong Du
- Abstract (逐語断片): "This paper presents optimizations in lock management implemented in Tencent's database, TXSQL, with a particular focus on high-contention scenarios."
- 分類: 既存 DBMS (TXSQL) 内の lock manager 最適化、standalone の in-memory protocol ではない。WebSearch の結果表示: SIGMOD 2025 Companion、DOI 10.1145/3722212.3724457

## WebSearch の結果表示から取った事実 (本文未確認)

- Polaris: "Proceedings of ACM Management of Data, Volume 1, Issue 1, Article 44 in 2023"; abstract 要約: "Polaris is an optimistic concurrency control protocol that supports multiple priority levels. To enforce priority, Polaris introduces a minimal amount of pessimism through a lightweight reservation mechanism. ... p999 tail latency of high-priority transactions 13x lower than that of low-priority ones. With an abort-aware priority assignment policy, Polaris can deliver 1.9x higher throughput and 17x lower tail latency compared to Silo for high-contention workloads." PDF: dl.acm.org/doi/pdf/10.1145/3588724 (取得は HTML が返り不可)、pages.cs.wisc.edu/~chenhaoy/publication/polaris/polaris.pdf (404)
- Aria: "Aria: A Fast and Practical Deterministic OLTP Database was published in PVLDB 13, 11 (2020)"
- Caracal: "Dai Qin, Angela Demke Brown, and Ashvin Goel, SOSP 2021"; source code at github.com/uoft-felis/felis; DOI 10.1145/3477132.3483591
- CormCC: "Dixin Tang and Aaron J. Elmore, USENIX ATC 18"; usenix.org/conference/atc18/presentation/tang; 公開 repo は検索結果に無し (2 系統)
- Tebaldi: "Chunzhi Su, Natacha Crooks, Cong Ding, Lorenzo Alvisi, Chao Xie, SIGMOD 2017"; DOI 10.1145/3035918.3064031; 公開 repo は検索結果に無し (1 系統)
- Rebirth-Retire: vldb.org/pvldb/vol18/p3162-zhang.pdf (PDF 取得・精読済み → sources/rr.txt)
- Plor: dl.acm.org/doi/abs/10.1145/3514221.3517879 (403)、storage.cs.tsinghua.edu.cn/papers/sigmod22plor.pdf (取得・精読済み → sources/plor.txt)
- Bamboo: arxiv.org/pdf/2103.09906 (取得・精読済み → sources/bamboo.txt)、DOI 10.1145/3448016.3457294 (Polaris README の記載)
- 2024〜2026 の走査 (WebSearch 3 系統) で表示された他の題名: ForeSight (2508.17375、deterministic)、Dodo (FGCS 2024、deterministic)、TxnSails (VLDB 2025、isolation level selection)、Focus! (DOI 10.1145/3769793、on-disk)、GPU-Accelerated OLTP (2406.10158)、Epoch-based OCC in Geo-replicated DB (2602.21566、分散)、A Hybrid Approach to Integrating Deterministic and Non-Deterministic CC (VLDB 2025)、Gria (FCS 2023、deterministic)、CV-Rules (2606.25409、CC の直列化可能性検証、未読)

## 追加照合 (段 6 レビュー後、2026-09-17、親が GitHub API contents / raw で取得)

```
--- neurcc root listing (api.github.com/repos/neurdb/neurcc/contents/)
['.gitignore', 'Dockerfile', 'README.md', 'environment.yml', 'tpcc-interactive', 'tpcc', 'ycsb-interactive', 'ycsb']
LICENSE-like: []
--- gitzhqian/RebirthRetire/gitzhqian-rebirth-retire/LICENSE (raw、743 bytes) 冒頭
ISC License

Copyright (c) 2014, Xiangyao Yu
--- luyi0619/aria/master/LICENSE (raw、1062 bytes) 冒頭
MIT License

Copyright (c) 2020 Yi Lu
```
