## 段 1 brief (2026-09-20 21:05 JST、開始 gate rc=0 at HEAD f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad = local main)

- 研究前進: 論文 B-10 静的 backoff 右 tail (第 1 段 探索走 T-2418 → 第 2 段 本格 T-2500) の記述で、
  読み手が runbook の「exploration campaign」(campaign layout の use class) と D1813 の「探索」(標本への帰属) を
  混同する経路を消す。完了判定 = runbook に 1 節 (定義 2 + 対応表 + 読み分け) が入り、check_docs 緑、
  段 6 read-only レビューで事実誤り 0。
- scope: `docs/pegasus-runbook.md` に `### 7.9` を新設 (§8 checklist の該当項目へ 1 句のポインタ)、
  `docs/glossary.md` §4 に 1 項目。実装面 0 (コード・テスト・script・設定に触れない)。
- 確定済み裁定: D1879 (語の整理だけ。working bytes 拘束・`run_kind == "extended"` 必須化は採らない)、
  D1848 (探索走は official use class のまま、exploration root へ移さない、理由 5 項目目が本件の語の衝突を名指し)、
  D1813 (2 段構成)、D123 / D158 / D528 (exploration namespace・env seam・`declared_use_class` 閉表 4 値)。
  D1859 は B-10 driver 経路の meaning witness であり、全経路の保証へ広げない (引数の指示)。
- 不変条件: 凍結成果物・正式 consumer の受理集合・`run_kind`・コードに触れない。規律 2 不変。
  仮想リスク向けの gate・検査・台帳・一般化を足さない (DW-G05)。
- 一次資料 (実測済み):
  - `orchestrator/campaign/layout.py` `resolve_campaign_output_root`: `official` → `IZANAGI_OFFICIAL_OUTPUT_ROOT` (明示必須、repo 内 fallback 無し)、
    `exploration` → `IZANAGI_EXPLORATION_OUTPUT_ROOT` (省略時 repo 既定 `output/exploration/`)。閉表は D528 の 4 値、materialize できるのは 2 値。
  - module-level `DECLARED_USE_CLASS = "exploration"` は 7 module (s4 driver 族 5 + 8c `p3_autonomous_workload_trial` + `paper_story_a1_paired`)。
    `declared_use_class="official"` を渡す producer に `backoff_extended_sweep.py` (B-10 拡張 sweep、`RUN_KINDS = (extended, t2266-tail, t2418-explore)`) が含まれる。
  - `tools/pegasus/b10_backoff_grid.sh:578` は `IZANAGI_OFFICIAL_OUTPUT_ROOT` を export、`tools/pegasus/paper_story_a1_paired.sh:831` は `IZANAGI_EXPLORATION_OUTPUT_ROOT` を export。
  - `tools/pegasus/submit_b10_backoff_grid.sh` の `--explore-campaign` は `t2500-tail-formal` 限定で「探索走 (t2418-explore) の campaign directory」を指す (第 3 の表記)。
  - T-2418 insight §5 / §10 (`output/insights/2026-09-09_t2418-backoff-static-explore/README.md`)、T-2500 事前登録 §2.1 (`docs/b10-backoff-static-tail-preregistration.md`)、
    `docs/orchestrator-design.md` の namespace 節、runbook §8 の該当項目 (行 1750-1751、[T-422] / F98)。
- 割れうる前提 (親の provisional 裁定・攻撃対象):
  - (P1) glossary へ 1 項目足す (引数は「必要なら」)。provisional: 足す — 本件の本質が読み手側の語の衝突であり、glossary が読み手向けの正本。機体固有の事実は書かず runbook 節へ委ねる。
  - (P2) 節の置き場: `### 7.9` (Izanagi で使う場合) に定義・対応表、§8 checklist は既存項目にポインタ 1 句だけ。
  - (P3) 対応表に「A-1 対測定 (正式測定) は exploration use class」を直交性の例として載せる — use class の exploration が「非正式標本」を意味しないことの実例。
- 成果物の形: 節 = 定義 A (use class) / 定義 B (D1813 の探索) / 第 3 の表記 (`--explore-campaign`) / 対応表 (何を分類するか・宣言場所・環境変数・実例) / 読み分け規則 2 文。
- 段構成 (DW-C00): 軽量版。段 2・3 省略、段 4 親裁定、段 5 親が docs 起草 (実装面 0 につき実装子なし)、
  段 6 read-only codex review 1 本 (一次資料から事実を再抽出する docs-only、2 レンズを 1 本で)、変異 matrix 免除 (実装面 0、DW-S04)、
  受入全走 1 回 (記録 commit 後の tip、Pegasus 計算ノード dispatch)。
- 純増: D1848 理由 5 項目目と T-2418 insight §5 に「別語」の事実はあるが、runbook / glossary に定義と対応は無い。純増 = runbook 節 + glossary 項目。
- 条件表の再評価 (brief 直後): 08 freeze/oracle/proof chain = 不成立 (runbook / glossary は check_docs の構造 lint のみ、凍結 chain・hooks に束縛なし、実測 grep)。
  09 凍結 bytes = 不成立。10 = 不成立。11 削除 = 不成立。13 gate 新設 = 不成立 (scope 外と引数が明示)。

