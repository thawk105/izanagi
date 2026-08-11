---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t809-8c-fanout
seq: 1
title: 8c trial の workload 単位 fan-out を評価した — 本体を割る実装は要らず条件の明文化だけが要る、親の禁止理由 2 件は敵対レンズが撤回させた (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t809-8c-fanout)
---

## 本文

- **依頼は [T-809] の評価** (ユーザー指定: 本番コードの編集はせず評価と設計に留める)。
  裁定パッケージと凍結逐語は `output/insights/2026-08-11_t809-8c-workload-fanout/`。
  RP-1〜RP-6 は**ユーザー裁定待ち**であり、本 wave では何も実装していない。

- **結論は「本体 loop を割る実装は要らない」。** 正式 (registered) 経路は既に leaf 分解済みで
  1 trial = 1 workload が機械強制、受入は report 6 本 exact。複数 workload の逐次 loop が
  使えるのは探索 pilot だけで、その探索 pilot も `--workloads` を 1 個にして N 回起動すれば
  今日そのまま割れる。**割ったときに消えるのは機構ではなく保証** (期待集合の被覆検査・共有 wall・
  session 相異検査・trial 単位の start-once がいずれも 1 process 内へ縮む)。

- **実測**: gen_S `bnode019` (request 903110) で fixture + `--no-build` の 3 arm。
  1 workload 単独 1.122 s / 3 workload 逐次 2.006 s (再走 2.027 s) / 3 process 同時 1.189 s。
  **3 process 同時は衝突ゼロで全 complete。** ただしこれは supervisor 配線だけの値で、
  LLM 4 役も build も bench も含まない。**本番利得の根拠に使わないことを裁定文に明記した。**
  probe を 2 本空費した: `PBS_JOBID` がコロンを含み `PATH` 上の python3.10 shim を壊すこと、
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` が git 配下を拒否し `dev-wave-jobs/` が `.git` を持つこと。

- **親の禁止理由 2 件を撤回した。** (i) 初稿は「別 workload が同じ変異を合成すると build cache の
  claim が衝突して後着が落ち手動回収が要る」を最大の障害としたが、**標準 CLI では衝突しない** —
  cache identity は `SourceEvidence.source_root` を含み、build 経路の source root は process ごとに
  一意な使い捨て worktree だからである。本当の代償は run 内 cache 再利用の喪失であって禁止理由ではない。
  (ii) 初稿の (P3)「8c は workload 間比較そのものだから cross-node fan-out を現行 protocol で
  許さない」も過剰。現行 A/B/C は `scientific_claim=false` の配線 pilot で job 間の性能比較をしない。
  **これは worklog (418) で撤回した「未測定量を根拠に広く禁止する」の再発であり、
  敵対 2 レンズが独立に指摘した。**

- **親の事実誤りを 7 件直した** (実行ノードの取り違え、`role-invalid` は次 workload へ進むのに
  「部分成功 = fail-stop」と書いたこと、campaign identity に execution contract が入ると書いたこと、
  claim 衝突の帰結、中断証拠、workload 独立性の射程、cache 衝突の成否)。
  段 2 plan (codex `gpt-5.6-sol` reasoning=max) が 8 件指摘し、段 3 の敵対 2 レンズ (sol / luna) が
  blocker 6 件 / 5 件を返した。両レンズとも全体判定は fan-out 実装 **NO-GO**、
  条件付き GO は「no-build の探索 singleton 実行」だけで一致した。

- **交絡の線引きが本質。** job 内で閉じる比較 (leaf 内の correctness、bench rep の median/CV、
  同一 node の stock/variant 対) は無条件で許され、job を跨ぐ性能比較 (正式系列の
  descriptor on/off/swapped の arm 差) は node を block / randomization 因子として protocol が
  定義するまで許されない。**「6 process だから 6 node へ散らしてよい」という読み方が
  本評価で最も危険な誤読**であり、裁定文で明示的に潰した。

- **scope 外の real 所見を 1 件回収した** (fan-out とは独立の既存 gap)。正式受入
  `assert_trial_registry_acceptance` は Layer-3 chain を必須経路で呼ばず、宣言 arm が実際に
  走った arm であることも認証せず、6 report 間で `measurement_head` の一致も検査しない。
  証拠契約は acceptance 自身からの Layer-3 呼び出しを要求している。

## 次の一手差分

### 更新

- [T-809] **P2・ユーザー裁定待ち**: 8c trial の workload 単位 fan-out の評価は完了した。
  裁定パッケージ (RP-1 実装可否 / RP-2 build 付き fan-out / RP-3 正式 6 trial のノード配置 /
  RP-4 部分成功 / RP-5 再投入 / RP-6 条件をどこへ書くか) は
  `output/insights/2026-08-11_t809-8c-workload-fanout/package.md`。
  親推奨は RP-1 (a) 実装しない・RP-2 (a) 許さない・RP-3 (c) 着手時に再評価・RP-4 (a) 現状維持・
  RP-5 (a) 経路別に明文化・RP-6 (c) runbook 2 箇所へ 1 行ずつ。**裁定が下るまで実装しない。**
  base: 669743e50e1be3212a2a495f661479ef5a7f1ad333de2920ff079b8c1f8e5c14

### 新規

- {{T:s8c-acceptance-layer3-gap}} **P2・新規**: 8c 正式受入の証拠 gap 3 件を閉じるか裁定する。
  `assert_trial_registry_acceptance` は (i) `assert_campaign_layer3_chain` を必須経路で呼ばず
  (`trial_registry.py` は `assert_autonomous_trial_completeness` しか import しない)、
  (ii) 宣言 arm が実際に走った arm であることを認証せず (registry 自身が明記)、
  (iii) 6 report 間で `measurement_head` の一致を検査しない。
  証拠契約 `s8c_preregistration_evidence_contract.v1.json` は acceptance 自身からの
  Layer-3 呼び出しを要求しており、契約と実装が食い違う。**[T-809] の fan-out とは独立の既存 gap**
  であり、正式系列の着手前に閉じるか、意図的な限界として明文化するかを決める必要がある。
  **実装面のため Codex author 必須。**
- {{T:pegasus-job-env-pitfalls}} **P3・新規**: 計算ノード job の環境 2 件を runbook へ書く。
  (i) `PBS_JOBID` は `0:903095.nqsv` のようにコロンを含むため、`PATH` に載る directory 名へ
  そのまま使うと python3.10 shim が丸ごと無効になる (実測で 1 job 空費、全 arm が
  Intel python 3.9.13 で `dataclass(slots=True)` に落ちた)。
  (ii) `IZANAGI_EXPLORATION_OUTPUT_ROOT` は `_has_git_ancestor` で git 配下を拒否するが、
  runbook §8 が指す「job 専用の /work 配下」として自然な `/work/1/SFC/tanab/dev-wave-jobs/` は
  `.git` を持つため拒否される (実測でもう 1 job 空費)。非 git base の指定を明記する。
