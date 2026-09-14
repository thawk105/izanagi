# [T-1706] 段 1 brief — schedule の hash 用 / validation 用 二重読みを一度読みへ直す

基準 commit: f5423e2fff3adb164731963ca33e82ed08d08c4d (local main)
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1706-schedule-bytes-toctou

## 研究前進

T-189 の model-routing 証拠系では、launch receipt の `schedule_sha256` が「どの schedule で測ったか」を
認証する trust root であり、replay / aggregate はこれを exact 比較して certified 判定を出す。3 入口とも
SHA 用と本体用で **別々に読む** ため、同一 UID の書き手が A→B→A と差し替えると、receipt に A の SHA を
残したまま B の slots (arm↔model の割付、price version、cardinality、slot_id 集合) で検査・集計が通る。
論文の routing 主張は「この receipt の schedule で測った」に依存するので、ここが開いている限り
certified 判定の意味が保証されない。最小差分 = 3 入口で **一度だけ読み、その同じ bytes から**
descriptor SHA と schedule を導く。完了判定 = 3 入口それぞれで、読み直しの窓が閉じたことを
負例テストで固定する。

## scope

- `tools/codex_reasoning_ab.py` の 3 入口 (`supervise_pair` / `_replay_manifest` / `make_packets`) と、
  そこだけが使う bytes 返し helper 1 つ。
- `orchestrator/tests/test_codex_reasoning_ab.py` の対応テスト (各入口 1 本以上の負例)。
- **scope 外 (ユーザー明示):** 仮想リスク向けの gate・検査・台帳・一般化の追加。
  `_artifact_path` の全 caller への横断変更、新しい凍結台帳、docs 方針の変更も含む。

## 確定済みユーザー裁定

- 実装面は Codex `role=author` が書く (D95 決定 1・2)。親は brief / 裁定 / 統合 / 全走 / 記録 / commit のみ。
- 規律 2 (正しさゲートを緩める変異を許さない) を緩めない。受理集合を広げない。
- 3 入口のどれも取り残さない。
- 着手直前の local main から fresh worktree (実施済み: f5423e2ff)。

## 不変条件

- **受理集合を広げない。** 現在受理される正当な schedule は同じく受理され、現在拒否されるものは拒否される。
- **非攻撃時の出力 bytes を変えない。** run root の `schedule.json` の内容、launch receipt / attempt ledger の
  `schedule_sha256` の値は現行と同一。
- **DW-O09 pin 閉包:** 現行 bytes (`d7baa221ceeacb20976dc234239e9386a5129871667056e502d0ddcfa7903988`) を
  pin する live consumer は 0 件。旧装置 bytes (`58f1176e...`) の歴史 pin が
  `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` に 1 件あり、D1285 で更新対象外。
  範囲 = path 検索 / key 検索 (`tool_sha256`・`apparatus-pin`) / 現行 sha の値検索 (hit 0) /
  §8.3 wiring slice の全 field 走査。`tools/check_docs.py` はコード行番号参照を検査しないので、
  prereg の `(:7373)` 等の行ずれは gate にならない。

## 変更面の実アンカー (f5423e2ff 時点)

| 入口 | 現行の読み回数 | 行 |
|---|---|---|
| `supervise_pair` (`:7593`) | source 1 回 (`:7632`)、frozen 比較 (`:7634`)、sha 用 (`:7638`)、JSON 用 (`:7639`) | 最大 4 回 |
| `_replay_manifest` (`:11119`) | `_artifact_path` 内 (`:11137`)、`_load_json_object` (`:11138`)、`_sha256(read_bytes())` (`:11152`) | 3 回 |
| `make_packets` (`:11668`) | `_artifact_path` 内 (`:11700`)、`_load_json_object` (`:11703`) | 2 回 (inline descriptor 時は 0 回) |

helper: `:8971 _load_json_object` / `:8981 _load_json_object_with_sha256` / `:9005 _artifact_path`。
`_validate_schedule` の呼び手は `:7647` / `:11145` / `:11711` の **ちょうど 3 箇所** (全数)。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** 「同じ bytes から導く」で足りる。file descriptor の pin (open したまま fstat / inode 固定) までは不要。
- **(P1-b)** `supervise_pair` は frozen copy を書いた後に読み直さず、in-memory bytes を authority にしてよい。
- **(P1-c)** 3 入口以外に schedule を読む経路は無い (`_validate_schedule` 呼び手が全数 3)。
- **(P1-d)** `_artifact_path` 自体は変更せず、bytes も返す姉妹 helper を足して 3 入口だけが使う。
- **(P1-e)** 欠陥の存在は **ソース読解** で確定した (同一 path への `read_bytes()` が入口ごとに複数)。
  攻撃の成立自体は未実測であり、段 5 の負例テストが実測の初出になる。

## 成果物の形

production 3 入口の限定修正 + 各入口の負例テスト。負例は「SHA 照合後に中身が差し替わっても、
差し替わった側の内容で受理されない」を実体で発火させる (依存先を stub しない、F649)。

## 分割方針

編集 path が 2 file (production 1 / test 1) で素集合に割れないため、段 5 の実装子は **1 単位**。
所有 = `tools/codex_reasoning_ab.py` + `orchestrator/tests/test_codex_reasoning_ab.py`。

## DW-G05 成果物影響

放置時: certified receipt の `schedule_sha256` が、検査・集計に実際に使われた schedule を指さない場合が
あり得る。`aggregate.json` / `verify.json` の受理集合が、receipt の認証していない slots 定義の下で
成立しうる。

## gate 適用

- DW-G01 (生死実験先行): 該当なし。新しい探索軸でも大型機構でもなく、既存 3 箇所の限定修正。
- DW-G03 (族一般化には独立 2 例): 同型欠陥は 3 入口で独立に成立するが、ユーザー明示により
  一般化は scope 外。3 入口限定の局所修復にとどめる。
- DW-G04 (条件付き機能の発火 gate): 新設しない。
- DW-C00 により **軽量版にしない**。正しさ防壁 (receipt の trust root) に触るため、
  段 2・3 と段 6 の review 子を省かない。
