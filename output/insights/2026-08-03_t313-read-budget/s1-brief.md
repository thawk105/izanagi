# 段 1 brief — [T-313] dev-wave の byte 予算を常時読量 gate へ置換

## scope
`tools/check_docs.py` の `docs/dev-wave/**` 予算 gate を、「総 bytes」でなく「毎 wave が必ず読む量
(常時読量)」を測る gate へ置き換える。編集面は `tools/check_docs.py` と
`orchestrator/tests/test_check_docs.py`。docs 本文 (`docs/dev-wave/*.md`,
`.claude/commands/dev-wave.md`) は、置換の説明に必要な最小限を超えて変更しない。

## 確定済みユーザー裁定 ((109)、一次資料 = `docs/archive/worklog-phase3-0802-106-110.md`)
- 択 (a) 採用 — byte 上限を常時読量 gate へ置き換える。
- **予算値の引上げは不採用** (T-127 裁定を維持)。「置換で得た余地」以外の緩和をしない。

## 段 1 前提実測 (2026-08-03、worktree `dev-wave-t313-read-budget` @ e0b9073、実ファイル計測)
- 4 reference 実バイト = **25,198 / hard ceiling 25,200 (残 2 bytes)** — 予算は現に逼迫。
- 節単位の内訳から L1/L2 を実測 (層の定義は `DW-C00`: L1=段 dispatch の無条件節、L2=条件成立時のみ):
  - **L1 = 18,938 bytes (75.2%)** = core 8,537 (全節) + workers 4,623 (全節) + mutation 3,682 (全節)
    + operations の段 2/3 行 {O01,O02,O03,O05,O13} + preamble = 2,096
  - **L2 = 6,260 bytes (24.8%)** = operations の残り 15 節 (O04,O06,O08〜O12,O14〜O20,O23)
- 個別 cap の残余: core 1,063 / workers 377 / mutation 68 / **operations 44**。
  → 家族合計を外しても **operations の個別 cap を残す限り T-313 は実質何も解放しない**。
- (109) の「実読 10,515 / 23,990 = 44%」は docs-only 軽量 wave の実績値であり、
  上の L1 (=無条件節) とは別量。**両者の差が本 wave の設計択一の核心** ((P1))。
- pin 閉包 (`DW-O09`): `grep -rn "docs/dev-wave" --include=*.py` の hit は
  `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の 2 本のみ。
  docs 側に予算値の再掲なし。dev-wave の command/skill に SHA-256 pin なし
  (SHA pin は cleanup-branches だけ)。凍結 manifest への波及なし。

## 既存テスト被覆と純増検出力 (`DW-S01`)
- 既存被覆: `test_dev_wave_reference_limits_pin_adjudicated_caps` /
  `_budget_pins_cap_sum` / `_budget_pins_aggregate_ceiling` /
  `_cap_sum_rejects_above_110_percent` / `_accepts_exactly_110_percent` /
  `_limit_accepts_exact_boundary` / `_rejects_plus_one` /
  `test_raised_doc_budgets_still_reject_each_new_limit_and_aggregate` (N22)。
  → **総量・個別 cap・cap 総和の境界は既に ±1 byte で被覆済み**。
- 純増検出力 = 「L2 だけが増えたときは通し、**L1 が増えたときだけ落とす**」の区別。
  現行 gate はこの 2 つを区別できない (どちらも総量として同じに見える)。
  副次の純増 = L2 単節の肥大検出 (現行は家族合計に紛れる)。

## 不変条件
1. `docs/dev-wave/**` の閉包検査 (未登録実体の拒否・登録済み不在の拒否) を弱めない。
2. `STAGE_DISPATCH_CONTRACT` / `CONDITION_DISPATCH_CONTRACT` の既存照合を弱めない。
3. 予算のために安全義務本文を削らない。gate 置換で「L2 なら無制限」を作らない。
4. 新 gate は repo だけから決定的に計算でき、特定 wave の実績履歴に依存しない。
5. 受理集合の変更 (何が赤/緑になるか) を、置換前後の表で worklog に残す。

## 親の provisional 裁定 (攻撃対象)
- **(P1) 常時読量の定義** = `DW-C00` の L1 (段 dispatch の無条件節、18,938) を採る。
  「軽量 wave が実際に読む最小集合 (~9,182)」は採らない。理由 = 後者は段の実行有無という
  実行時判断に依存し、gate が repo から決定できない (不変条件 4)。
- **(P2) 実装の骨格** = `check_docs.py` 内に L1 節集合を明示宣言し
  (`STAGE_DISPATCH_CONTRACT` の無条件行のみから構成)、その節 bytes 合計に ceiling を課す。
  command 本文の dispatch 表は変更しない。
- **(P3) L2 の規律** = 家族合計でなく **L2 単節 cap** に置き換える。
- **(P4) 個別 file cap** = core/workers/mutation は L1 ceiling に包含されるため撤去、
  operations も撤去 (残すと解放がゼロ、上の実測)。閉包検査用の registry としては残す。
- **(P5) 予算値** = L1 ceiling は現行実測 18,938 に小幅 headroom、L2 単節 cap は現行最大
  (DW-O23 = 1,123) に小幅 headroom。具体値は段 2 で根拠付きに提案させ段 4 で確定。

## 成果物影響 (`DW-G05`)
放置すると `docs/dev-wave/**` の残余は 2 bytes のままで、次に必要になった安全義務は
「既存義務を削る」か「入れない」しか選べない。dev-wave 契約は certified 選択・材料レポート・
試行台帳を生む全実装 wave の gate を規定しているため、義務の欠落はそれらの受理集合を
検査なしで通す方向へ直接効く。

## 成果物の形
`tools/check_docs.py` の gate 置換 + `orchestrator/tests/test_check_docs.py` の
境界テスト置換 (±1 byte)。受入 = `python3 tools/check_docs.py` rc=0 と全走緑、
変異 matrix (新 gate の各枝) + 正例 (L2 だけ増やしても緑)。

## 分割方針
編集面は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の 2 ファイルだけで
相互依存が強いため、**段 5 は単一 Codex 実装単位**とする。

## 受入・実測環境
親環境 (Pegasus login ノード、この worktree、cwd = repo root) で `tools/run_tests.py` 受入形。
計算ノードは不要 (計測を伴わない docs/tooling gate 変更)。
