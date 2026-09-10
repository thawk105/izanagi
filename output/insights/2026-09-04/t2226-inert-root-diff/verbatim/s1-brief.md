# 段 1 brief — [T-2226] inert (stock) 比較を「差を取ってから置き場所由来かを判定する」形へ

wave: `dev-wave-t2226-inert-root-diff` / branch `worktree-dev-wave-t2226-inert-root-diff`
基点 main: `c7ed565892cd4aba52d7fa47a7d1da17b117c005`
worktree (子の cwd もここ): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff`

## 1. 確定済みユーザー裁定 (D1523)

`evaluate_define_supply_effectuation` の inert (stock) 経路を、**前処理後 bytes の差を取り、
その差が source root / control root 由来のものだけかを判定する形**へ直す。
比較の前に root path を同一 token へ畳む案 (起草時の推奨) は**採らない** — 情報を捨ててから比べる形であり、
畳み方の誤りが本物の差を隠すため。
**正例 (patch 済み inert = stock で緑) と負例 (実際に意味が違えば赤) の両方を登録してから入れる**ことが裁定の条件である。

## 2. 実測で確認した前提 (親が本 worktree で実測済み)

- `orchestrator/campaign/condition_meaning_gate.py:2418-2432` — `unsafe_root_builtin` が真なら
  `preprocess-root-dependent-builtin` で赤。needle は inert 経路でのみ source_root / control_root を含む。
- `orchestrator/campaign/condition_meaning_gate.py:2062-2063` — code-owned 依存が `__FILE__` /
  `__BASE_FILE__` を含むと `root_dependent_builtin_paths` に積まれる。
- `external/ccbench/include/debug.hh` は `__FILE__` を 7 箇所で使う (code-owned)。
- `orchestrator/campaign/condition_meaning_gate.py:750-756` — `capture_define_inputs` は
  `stock == source` を `input-capture-failed` で拒否する。2 root は必ず別 path。
- `orchestrator/campaign/paper_story_a2_certification.py:606` — A-2 は
  `capture_define_inputs(variant_root, stock_root=source_root)` を呼ぶ。
- 以上より A-2 の inert cell は構造的に常時赤。この guard は情報を 1 bit も持たない。
- `orchestrator/campaign/condition_meaning_gate.py:3302-3411` — `_validate_supply_green_evidence` は
  evidence の key 集合を **exact** で検査し、`status_contract` が reason_code →
  (comparison, digests_equal) を束縛する。
- `orchestrator/campaign/condition_meaning_gate.py:3743` — `require_condition_gate_family` は
  `terminal_status == "green"` だけを見る。reason_code の許可リストは持たない。
- DW-O09 閉包 (実測): `condition_meaning_gate.py` の bytes を pin する `FROZEN_MANIFEST` key・
  generator source hash pin は **0 件**。`FROZEN_MANIFEST` の 23 key はすべて
  `output/s1-freeze/`・`output/s8b-freeze/`・2026-07-16 の insight であり本変更面と無関係。
  名前の hit は `output/insights/` 配下の歴史記録のみ。凍結成果物の再発行は不要 (DW-O10 も不成立)。
- reason code を exact 一致で読む consumer 3 件:
  `tools/pegasus/probes/t316_sandbox_backend_probe.py:370`、
  `orchestrator/tests/test_t316_sandbox_probe.py:163`、`orchestrator/tests/test_backoff_sweep.py:161`。
- 既存被覆の検索 (decisions / archive worklog / `output/insights/` を新しい順に一覧): D1523 を実装した
  wave は存在しない。`2026-09-02_a2-condition-gate-patched-root` は裁定パッケージの出所であり実装ではない。
  本 wave は純増。

## 3. scope (本題の実装だけ)

1. inert (stock) 経路の判定を次の順序へ変える。
   (a) requested / control の**実 bytes をそのまま**比較する。完全一致なら従来どおり
       `stock-inert-preprocess-identical` (green)。
   (b) 一致しないとき、**差分を取ってから**各差分区間が source/control root (および
       requested/control build root) の置き場所由来だけで説明できるかを分類する。
   (c) 置き場所由来だけ → green (新しい reason code)。残差が 1 byte でもあれば
       `stock-inert-mismatch` (red)。
2. 分類の evidence を record へ残す (差分区間数、置換した root の対応、残差の有無)。
3. 正例・負例のテストを登録する。

**scope 外** (仮想リスク向けの追加は作らない): 新しい gate・検査・台帳の新設、非 inert
(`requested-default-difference`) 経路の受理集合変更、`BACKOFF_NOINLINE` の意味 arm 厳格化
(裁定 2、別項)、CCBench (`external/ccbench`) の改変、一般化した path 正規化 utility。

## 4. 不変条件 (緩めない)

- **規律 2**: 置き場所以外の差が 1 byte でも残れば必ず赤。誤りの向きは「本物の差を赤にする」側に倒す。
  分類が判定不能なら赤。
- 置換は**差分区間にのみ**適用し、比較対象の元 bytes は加工しない。全出力を畳む実装にしない。
- 既存 green reason code `stock-inert-preprocess-identical` は **bytes 完全一致のときだけ**出す
  (consumer 3 件が exact 一致で読むため)。置き場所由来の緑は別 reason code にする。
- 非 inert 経路の受理集合・reason code を変えない。
- `_validate_supply_green_evidence` の exact schema と `status_contract` を同じ commit で整合させる。
- 既存テストの期待値を変えない。緑にするためにテストを甘くしない。

## 5. 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1-1)** 差分の粒度は**行単位**とする (preprocess 出力は linemarker + 本文の行構造を持つ)。
  byte 区間より粗いが、置換後の完全一致を要求するので隠す方向へは倒れない。
- **(P1-2)** fixture では control_root (`.../supplied/stock`) が source_root (`.../supplied`) の
  **子**である。置換は requested 側の差分行に対して requested_root → control_root の**一方向**だけ行い、
  最長一致優先とする。逆方向・両側置換はしない。
- **(P1-3)** build root も同じ扱いで置換対象に含める (現行 needle が build root を含むため)。
- **(P1-4)** 置き場所由来と判定してよいのは `root_dependent_builtin_paths` が**非空**のときだけとする。
  `__FILE__` を使う code-owned 依存が 1 つも無いのに root path 差が出るのは、置き場所では説明できない。
- **(P1-5)** 新 green reason code を新設する (既存コードの再利用は `digests_equal` 契約を壊す)。
- **(P1-6)** `preprocess-root-dependent-builtin` は非 inert 経路には**残す**。inert 経路からのみ外す。

## 6. 成果物の形

- `orchestrator/campaign/condition_meaning_gate.py` — 判定変更、evidence field 追加、
  `_validate_supply_green_evidence` の required 集合と `status_contract` の更新。
- `orchestrator/tests/test_condition_meaning_gate.py` — 正例 / 負例。
  `__FILE__` を持つ code-owned header を差し込んだ copied fixture で、
  現行実装では正例が赤になること (= 機構を通ること) を確かめられる形にする。
- 段 4 で変異事前登録、段 6 で変異 matrix + 受入全走。

## 7. 並列分割方針

編集面は `condition_meaning_gate.py` とその単一テスト file に閉じ、所有が一枚岩である。
段 5 の Codex `role=author` 実装子は **1 単位**とする。段 3 の敵対相談は正しさ防壁に触るため 2 本並列で省かない。

## 8. 受入・実測環境

login node。gate のテストは実 `g++` / `cmake` で小さい fixture を configure + preprocess する
(fixture は 4 file 程度)。計算ノードへの投入は不要。所要は段 6 で実測して記録する。
