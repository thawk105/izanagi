# [T-338] 投入gate 単位5 (writer + conformance vectors) — 段1 brief

**scope:** D509決定(7) (`docs/decisions.md:21190-21195`) の6分割のうち単位5 (writer + conformance
vectors) を実装する。単位1/2/3/4は既にlandし`orchestrator/submission_gate/`配下に実装済み。
単位6 (統合+4名前export) はスコープ外 (別wave、依存順は `1||2 → 3,4 → 5 → 6`)。

**確定済みユーザー裁定:**
- D509決定8 Q-A=択(a): 投入gateへ production を投じる。6分割を複数waveで実行する計画どおり進める。
- D509決定8 Q-C=択(a): B1は`cmake_cache`申告値の拒否専用化で閉じる (単位3で実装済み)。
- D563: 単位1/2が確立した設計規約 (module-private capability token・keyword-only必須引数・
  digest固定後の再帰的凍結) は、単位5が新しい型を導入する場合も同じ規約に従う。

**実アンカー表 (現状 → 単位5が満たす方針):**
- `orchestrator/submission_gate/_binding.py:1-7` (module docstring、逐語):
  「受領証とbindingのsnapshot一致検査はwriter入口(単位5)の責務であり、本moduleはPreregBindingを
  要求するwriterを持たない」。単位5が埋める予約済みの穴そのもの。
- `output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:719-726` (§6.10、逐語2箇条):
  (1) 受領証を永続化する関数自体がPreregBindingを必須keyword-onlyで受け、同一snapshotの受領証・
  binding・measurement_headの三つ組を照合してから publish する。別経路のwriterは publish 不可。
  (2) 全fileRecord/blobRefについて「validator」がpointer実在・size一致・sha256一致を確認する。
  **(1)だけが単位5の新規スコープ。(2)は文言上validatorの責務であり単位3が実装済みの可能性が高い
  (P1、段2プランが実装済み判定と重複実装の要否を確認すること)。**
- `orchestrator/submission_gate/_receipt_io.py:151-164` (`create_receipt_bytes`、docstring逐語):
  「low-level exact-byte create-only I/O and is not part of the submission gate. The caller
  (the future writer entry point) is responsible for adding the PreregBinding comparison on top
  of this layer」。単位5はこの関数を呼ぶ薄いラッパーで足りる可能性が高い (P1)。
- `orchestrator/submission_gate/_safe_io.py:398-534` (`create_only_relative_bytes`):
  O_EXCL staging + 多段fsyncの原子公開が実装済み。D509決定6「原子公開と、排他生成+全量write+
  fsyncのパターン」の実体はここであり、単位5が新規実装する対象ではない。
- 同記録項目 §7 (`record-items-v2.md:728-744`、逐語): conformance vectorsは「test資材であり
  本書と同じlandでは発行しない」。production側の寄与はvector indexのdigestをapproval manifestへ
  pinする程度 (s1-classification.md「vector indexのsha256を1 field足すのは新設機構ではない」)。
  **vectorsを`orchestrator/submission_gate/*.py`のwc -l対象外 (test fixture等) に置けるかが
  行数リスクの核心 (P1、段2プランが配置場所を明示すること)。**
- `orchestrator/tests/test_t338_submission_gate_unit{1,2,3,4}.py`: 既存test命名規約。単位5は
  `test_t338_submission_gate_unit5.py`。

**不変条件:** certified選択・材料レポート・proof chain・凍結bytes・受理集合は不変 (単位5は単位6の
統合commitまでtop-level APIへ配線されない非公開部品)。`pilot_submission=forbidden`/
`main_submission=forbidden`/D264の4名前非exportは1bitも動かさない。

**最重要制約 (P1、段2の最優先成果物として検証させる):**
`orchestrator/submission_gate/*.py` 実測 = 5,974行 (2026-08-20再実測、command引数記載の09:00時点
実測と一致・drift無し)。D509上限6,200行に対し残余226行のみで、これは単位5と単位6 (別wave) の
**両方**をこの範囲に収める必要がある。上記アンカー表の(P1)群 (writerは薄いラッパー・vectorsは
production対象外) が正しければ226行に収まる可能性が高いが、誤りなら (例: §6.10箇条2の重複実装が
要る、vectorsがsubmission_gate/内のランタイムloadableコードを要求する等) 収まらない。
**段2 codexプランは最優先でunit5のproduction行数見積り (file:line精度) を出すこと。段4親裁定で
「226行 (単位6の最小余地を残した上で) に収まるか」を判定し、収まらなければ段5へ進まず、Q-A(c)型
(承認済み受理条件を明示的に縮小する新decision) の縮小裁定をユーザーへ返す。規律2を緩める方向
(writerの認可検査を弱める・別経路writerを許す等) では絶対に解決しない。**

**並列分割方針:** 単一実装単位 (writer本体とconformance vector digest pinを同一commitで結線する。
production/test分離はしない、codex author 1並列)。

**成果物の形:** `orchestrator/submission_gate/`内の新規/拡張モジュール (writer entry point) +
`orchestrator/tests/test_t338_submission_gate_unit5.py` + conformance vector資材 (配置は段2プラン
が決める) + 段7 decisions.md記録 (規模の申し送りを次wave=単位6向けに残す、entry 724と同型)。

**受入・実測環境:** 通常のdev-wave受入全走 (`tools/dev_wave_wait.py acceptance`)。本wave固有の
追加環境要件なし。
