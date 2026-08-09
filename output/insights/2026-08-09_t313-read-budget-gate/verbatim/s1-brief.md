# 段 1 brief — [T-313] 常時読量 gate

## scope

`tools/check_docs.py` の `docs/dev-wave/**` byte 予算を、**層 scope の予算**へ置き換える。
`.claude/commands/dev-wave.md` の 段 dispatch 表に条件性の機械可読な marker を入れ、
L1/L2 分類を表へ束縛する。`DW-CTX` / `DW-O04` の読み動線不一致を直す。

**scope 外:** `.claude/commands/*.md` (L0) と `docs/skill-self-improvement.md` の予算、
`DW-O23` の機械契約移管 (t664 R2(b) = 移管しない)、L2 節の削除 (t664 R1(a) = 候補ゼロで確定)。

## 確定済みユーザー裁定 (一次資料で確認済み)

1. **[T-313] 一次裁定** (`docs/archive/worklog-phase3-0803-140.md:67-71`) = 前 wave パッケージの
   **択 (1)**。同パッケージ本文 (`output/insights/2026-08-03_t313-read-budget/s4-ruling.md:58-61`) は
   択 1 を「3 層それぞれに現在値の上限を置く。常に読む量を凍結、クラス依存も凍結、
   条件のみは単節 cap (現行最大 935 → 1,000)」と定義する。裁定文はこれを
   「常に読む層は固定上限を維持、ノウハウ全体の固定文字数上限は撤廃、
   **剪定は byte 数でなく発火実績 + 機械検査での義務代替**」と要約する。増枠ではなく
   「常に読まない部分を予算対象から外す」構造変更である。
2. **§49 (2026-08-09)** = [T-664] を R1(a)/R2(b)/R4(a)/R5(a) で終端、需要を本項へ集約、**P1 へ引上げ**。
3. **起票文** (`docs/archive/worklog-phase3-0802-106-110.md:372-375`) が
   「あわせて `DW-CTX` / `DW-O04` の位置 (読み動線と不一致) も」を本項の一部としている。

## 実測 (worktree @ 34957a24、`measure_layers.py`)

| 層 | bytes | 節数 |
|---|---:|---:|
| L1 常に読む (wave 開始 / 段 1・4・7・8・9 の無条件節 + 3 preamble) | **10,625** | 15 |
| L1.5 wave クラス依存 (段 2・3・5・6 の無条件節) | **9,566** | 20 |
| L2 条件成立時のみ | **5,008** | 13 (最大 `DW-O09` = 935) |
| 合計 | 25,199 | (cap 25,200、残 **1 byte**) |

file 別: core 8,655 / workers 4,526 / mutation 3,689 / operations 8,329。
worklog (334) の実測と一致する。前 wave (2026-08-03) の L1 10,568 からの差は本文改訂による。

## 既存被覆と純増検出力 (性質で検索)

現行が持つのは (i) file 単位 byte cap 4 本、(ii) 集約 25,200、(iii) 個別 cap 総和 > 集約 の赤、
(iv) 段/条件 dispatch 表と `STAGE_DISPATCH_CONTRACT` / `CONDITION_DISPATCH_CONTRACT` の集合一致。
**どれも「常に読む量」を測っていない** — core.md は単体で 945 bytes 増やせる。
純増検出力は 2 つだけ書ける。(a) L1 の増加を検出する (現行は検出しない)。
(b) **節を L1 から L2 へ付け替える迂回を検出する** — 現行 parser は段 dispatch 表の
「成立した条件の」「commit するなら」を捨てて全行を 1 集合へ畳むため、修飾語を消すだけで
分類を動かせる (前 wave 段 3 所見 A1/B-05、real 裁定済み)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 実装は「層 scope 予算」= L1 ≤ 10,625 / L1.5 ≤ 9,566 / L2 は単節 ≤ 1,000 のみ、
  集約 25,200 と個別 file cap 4 本は撤廃。file cap を残すと operations.md の残余が 71 bytes で
  L2 が実質解放されず、裁定の趣旨を満たさない。
- **(P2)** L1/L2 分類は `.claude/commands/dev-wave.md` の段 dispatch 表から**機械的に導く**。
  表の条件性 marker を parser が保持し、check_docs 側の pin 定数と両方向照合する。
  片方だけの編集で分類が動くなら (P1) の cap は無意味になる。
- **(P3)** `DW-O04` の位置修正 = 段 8 dispatch 行から落とす。条件 04 が「commit message に
  防護パス文字列を含めて作る直前」を既に持ち、段 8 固有の義務ではない。
- **(P4)** `DW-CTX` の位置修正 = **wave 開始行から落とす**。冒頭 2 行が外部 supervisor へ
  条件付きで課し、条件 21/22 が同じ節を指す。段 9 行は残す (対話 wave の manager の義務)。
  **節本文の分割はしない** — 分割は節 ID 新設・consumer 閉包・D94 (c) との緊張を伴う設計択一で、
  親が既成事実化してよい範囲を超える (パッケージへ返す)。
- **(P5)** 節の切り出しは行頭 `## ` 規約で、可視 scanner へ替えない。前 wave 所見 B-06 が
  「fence 内偽 H2 の扱いで受理集合が双方向に変わる」と指摘した面を本 wave では開かない。
- **(P6)** `NORMATIVE_DISPATCH_ALLOWLIST` は現行どおり `REFERENCE_LIMITS | SELF_LIMITS` の
  key から作る。(P1) で `REFERENCE_LIMITS` が消えるなら、参照 file 集合を別定数へ切り出して
  allowlist と層分類の**共通 source** にする (前 wave 所見 A4 = self doc が allowlist 外になる赤)。

## 不変条件

- 受理集合を**縮める**方向の変更は L1 のみ。L2 の byte 上限撤廃は裁定の明文。
- 安全義務文を byte のために削らない (`tools/check_docs.py:165-167` の前科)。本 wave は
  `docs/dev-wave/**` の**本文を 1 byte も削らない** (`DW-CTX`/`DW-O04` は表側の行だけ動かす)。
- `docs/dev-wave/**` の bytes と `.claude/commands/dev-wave.md` の bytes を変えうるため
  `DW-O09` の pin 閉包を実施済み: pin は `orchestrator/tests/test_check_docs.py` の
  `REFERENCE_LIMITS` / `DEV_WAVE_AGGREGATE_BYTES` assertion のみ。
  `FROZEN_MANIFEST` にも `CLEANUP_COMMAND_SHA256` にも `docs/dev-wave/**` は無い (実測)。
- `.claude/commands/dev-wave.md` の cap は 9,500 / 140 chars。現行 bytes を段 2 で実測し、
  条件 marker 追加が cap を割らないことを確認する。

## 成果物の形 (`DW-G05`)

`tools/check_docs.py` + `orchestrator/tests/test_check_docs.py` + `.claude/commands/dev-wave.md`
+ (位置修正のみ) `docs/dev-wave/**`。
**実装しなかった場合に成果物が変わる点:** 予算で止まっている項目 ([T-328] 従属 4 件、
[T-648]/[T-550]/[T-665]/[T-662] の見送り分) は docs 契約を書けないままで、
運用 gate が発火しない状態が続く。certified 選択・レポートの**値は変わらない** (docs 契約のみ)。

## 分割方針

段 5 は単一実装単位 (check_docs + test + command 表 + docs 位置修正)。分割すると
parser・pin 定数・表の 3 面が別々の子に落ち、整合が段 6 まで検出されない。
前 wave 所見 B-09 が同じ分割方針を refuted (欠陥でない) としている。

## 環境

受入全走は `tools/run_tests.py` の dispatch recipe で gen_S へ投入する (login での pytest は禁止)。
背景 job のため受入は背景投入し、直前に local main を再確認する。
