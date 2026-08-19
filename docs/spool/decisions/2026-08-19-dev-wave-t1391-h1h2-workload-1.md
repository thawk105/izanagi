---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1391-h1h2-workload
seq: 1
---

## {{D:t1391-workload-gate-scope}}. 前提条件1のscopeはacceptance gateに閉じ、run_trial起動経路は前提条件8へ残す

**決定:** 前提条件1 (H1/H2 workload定義) の実装scopeを、登録済みbuild reportの
acceptance判定gate (`orchestrator/campaign/autonomous_trial_completeness.py`の
`assert_campaign_layer3_chain`内producer-supported判定) 1箇所に閉じる。
`run_trial` (`orchestrator/campaign/p3_autonomous_workload_trial.py`) にも同型の
`WORKLOADS`単独参照gateが存在するが、修正しない。

**理由:**
- `run_trial`は自身のgateへ到達する前に`_preflight_workload_profile`を通り、これは
  exploratory以外のprofile選択を「effective preregistration unavailable」で無条件拒否する。
  正式holdout起動には二段束縛 (`prereg_content_commit`/`prereg_effective_commit`) の消費が
  要るが現行実装は未消費であり、`docs/phase3-s8c-autonomous-trial-runbook.md`が
  「現repositoryは12述語のSATISFIEDが0件、正式H1/H2起動が通ることを期待してはならない」と
  明言している。
- この二段束縛は`docs/phase3-8c-preregistration.md`§6の前提条件8に相当し、前提条件1とは
  別項目である。`run_trial`のgateを直しても`_preflight_workload_profile`が先に阻むため、
  受理集合・値・参照のいずれも1件も変わらない (成果物影響を1行で書けない = must-fixにしない
  基準に該当)。

**却下した選択肢:**
- `run_trial`のgateも同時に直す — 前提条件8が未充足のままでは観測可能な効果が無く、
  「実起動が今回で通るようになった」という誤った印象を記録に残すリスクがある。

## {{D:t1391-three-dict-separation}}. HOLDOUT_BINDINGS/WORKLOADS/FORMAL_WORKLOADSの構造分離を維持したまま参照だけ広げる

**決定:** producer-supported gateの修正は、`trial_registry.HOLDOUT_BINDINGS`
(holdoutラベルH1/H2→workload名の束縛)、`p3_autonomous_workload_trial.WORKLOADS`
(exploratory hardcode)、同`FORMAL_WORKLOADS` (freeze由来derived) の3辞書の**値を複製・統合せず**、
gateが参照する集合を`WORKLOADS`単独から既存resolver (`resolve_workload_entry`、両辞書を順に見る)
経由へ広げる形で実装した。

**理由:**
- 3辞書は元々「exploratory hardcode」「freeze由来derived」「holdoutラベル」という異なる性質を
  持ち、意図的に分離されている。値を複製すると将来freeze側の値が変わった際に不整合が生まれる。
- command引数の「非交差にする」という制約は、この既存の構造分離を壊すな (HOLDOUT_BINDINGSの
  キーH1/H2をWORKLOADSへ混入させるな、WORKLOADSとFORMAL_WORKLOADSも統合するな) という意味と
  解釈した。この解釈は段3敵対相談2レンズでも反証されず (コード上に明示的な非交差assertionは
  無いが、既存resolverの設計そのものが分離を前提にしている)。

**却下した選択肢:**
- rr80/rr20の値を`WORKLOADS`へ直接追加する — `FORMAL_WORKLOADS`と値が重複し、将来の
  freeze値変更で乖離しうる。
