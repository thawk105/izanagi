# [T-595] reasoning effort の adoption latch — 逐語と変異台帳 (凍結、2026-08-07)

親の裁定要約は `docs/worklog.md` の該当エントリ。実装 commit は `cf110ad1` と `3772116d`。
branch = `worktree-dev-wave-t595-reasoning-ab`、起点 main = `9cb0f24b`。

## 射程 (これを越える引用を禁じる)

**本 wave は [T-595] が依頼した paired・blind・非劣性 A/B を実装も実走もしていない。**
`max` → `high` の非劣性・引き下げ可否を示す evidence は **0 件**である。
実装したのは現行の `max` 記述を守る adoption latch (`tools/check_docs.py` の docs pin) だけで、
評価装置・protocol・endpoint 台帳・campaign は未実装である。

この latch は **served model や実効 effort を attest しない**。守るのは
`docs/dev-wave/workers.md` の記述だけである。certified 選択・材料レポート・試行台帳の
評価値は本 wave で一切変わっていない。

先行 wave T-181 の台帳は現在も `experiment_complete=false` である。本 wave はその未認証結果を
新設計の根拠へ格上げしていない。

## 実測 (すべて親が実走)

| 対象 | 結果 |
|---|---|
| 受入全走 (`tools/run_tests.py`、commit `3772116d`) | 7113 passed / 20 skipped、rc=0 |
| `test_check_docs.py` + `test_plain_runner_coverage.py` (計算ノード) | 307 passed、rc=0 |
| `python3 tools/check_docs.py` | rc=0 (現行 `workers.md` を受理) |
| 変異 最終走 (`mutation-ledger-final.json`) | 7/7 KILLED、全件 `matches_expectation=true` |

### 親の独立 probe (書き込みなし、in-memory)

`_check_dev_wave_reasoning_effort_pins()` へ直接与えた入力と結果。

| 入力 | fix 1 巡目 (`cf110ad1`) | fix 2 巡目 (`3772116d`) |
|---|---|---|
| 現行 `workers.md` 実物 | finding 0 (正しい) | finding 0 (正しい) |
| DW-S02 を裸の `reasoning=high` | 赤 | 赤 |
| 可視 `high` + HTML comment 内 `max` | 赤 | 赤 |
| 可視 `high` + code fence 内 `max` | 赤 | 赤 |
| 同一節に `max` と `high` を併記 | 赤 | 赤 |
| **可視 `model_reasoning_effort="high"` + 可視の `reasoning=max` 例示** | **通過 (穴)** | **赤** |
| 可視 `model_reasoning_effort="high"` + comment 内 `max` | 赤 | 赤 |

## 変異の経過 (3 走。初回結果は消していない)

| 台帳 | 対象 commit | 結果 |
|---|---|---|
| `mutation-ledger-run1-infra-abort.json` | `cf110ad1` | baseline が dispatch receipt を得られず `PARSE_ERROR` で中止。**変異結果ではない** (runner に `--force-dispatch` が要ることを見落とした infra 起因)。 |
| `mutation-ledger.json` | `cf110ad1` | 6 件中 KILLED 4 / SURVIVED 2 (MR-04 = 可視化除去、MR-06 = 引用行除去)。両者とも注入実在を確認 (`anchor_counts` 1 件、`injection_diff_sha256` あり)。 |
| `mutation-ledger-round2.json` | `cf110ad1` | 両層同時変異 MR-07 / MR-08 がともに KILLED。親は「MR-04 / MR-06 は冗長層」と解釈した。 |
| `mutation-ledger-final.json` | `3772116d` | 再照準した 7 件が 7/7 KILLED、全件が期待 node と一致。 |

**親の「冗長層」解釈は焦点再レビューに反証された。** 実際の起動キー
`model_reasoning_effort=` を検査が認識していなかったため、MR-04 / MR-06 は単独で
fail-open 反例を構成できた。親が probe で裏取りし、fix 2 巡目で閉じた。
`mutation-ledger-round2.json` の KILLED は、既存の裸 `reasoning=high` fixture に対する結果であり、
単独 SURVIVED を冗長とする根拠にはならない。

## 段 4 で real と裁定しながら未実装のまま持ち越した所見

A-4, A-5, A-6, A-10, A-11, B-3, B-4, B-6, B-7, B-9 の 10 件。
対象となる新 case family / 新 endpoint 台帳 / 新 protocol を本 wave が作らないため**未発火**である。
**refuted / closed / resolved ではない。** 全文は `s3-lensA.md` / `s3-lensB.md`、
対応表は `s6-focus.md` にある。campaign 設計の入力として持ち越す。

## 凍結ファイル

| ファイル | 役 |
|---|---|
| `brief.md` | 段 1 brief (親)。数値 2 件は段 4 で自己訂正した — `s4-ruling.md` を優先する |
| `s2-plan.md` | 段 2 Codex plan (scope 択一・装置一般化・endpoint 定義・事前登録) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 (実験妥当性 / 射程・fail-open)。両者 NO-GO |
| `s4-ruling.md` | 段 4 裁定 (自己訂正・採否・変異事前登録) |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー。両者 NO-GO、独立に同じ 2 件を指摘 |
| `s6-fix.md` | fix 1 巡目 |
| `s6-focus.md` | 焦点再レビュー。親の冗長層解釈を反証 |
| `s6-fix2.md` | fix 2 巡目 |
| `mutation-spec*.json` / `mutation-ledger*.json` | 変異の事前登録と台帳 (3 走 + infra 中止 1 件) |

## limitation (構造上の事実)

- **docs pin は実効 effort の attestation ではない。** `workers.md` の記述を守るだけで、
  実際に起動された子の effort を検証しない。
- **表記の網羅は列挙である。** `reasoning=` / `reasoning_effort=` / `model_reasoning_effort=` を
  拾うが、将来 CLI が別の綴りを導入すれば同じ型の穴が再発する。
- 見出しの区切り記号を変えると節抽出が 0 件になり finding が立つ。これは
  `_reference_id_sections()` の既存挙動で、`DW-S09` / `DW-O23` の既存 pin と同型である
  (段 6 RA-4。本 wave 固有ではないため別 ID とした)。
- 引用内に effort 値の例示を書いた DW-S02 / DW-S03 節は新たに拒否される。
  意図した fail-closed 化であり、comment / code fence 内の例示は引き続き受理する。
- 節が欠落・重複したときは pin finding と既存の必須節検査の finding が二重に出る。
  rc は不変 (段 6 RB-5、nit として不採用)。
