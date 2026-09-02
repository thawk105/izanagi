---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2145-sort-oracle-ir
seq: 2
---

## {{D:sort-ir-acceptance-authority}}. sort hole の受理権威は IR admission 一本にし、恒真化する 2 者を gate と数えない

**決定:** sort comparator の受理言語を 79 値の型付き IR へ縮めたうえで、受理権威を次のとおり確定する。

| 機構 | 位置づけ |
|---|---|
| sort IR admission | **受理権威。** comparator 言語へ入れてよいと言える唯一の機構 |
| `_validate_single_sort_statement` | **恒真化。** 正準形への事後条件へ降格し、候補 gate として数えない |
| `coder_effect_gate.DENY_TABLE` | **別の関心事。** 全 hole 共通の deny-only veto であり受理を主張しない |
| `check_relation_matrix` | **候補 gate としては恒真化。** 79 値は構成上すべて SWO である |
| 実 TU conformance 照合 | **別の関心事。** 候補ではなく実装・環境の drift 検出器 |
| `sort_comparator_authority` | **別 domain の受理権威。** certified 側の 15 組 exact binding。触らない |

**理由:**

- T-396 で破棄された設計は、同じ hole を独立に**受理と主張できる**機構が 2 つ並ぶ形だった。
  `coder_effect_gate` は `passed=False` を作る経路しか持たない deny-only の前置 veto であり、
  これに当たらない。決定的な根拠は、**backoff 軸が既に「effect gate → 軸固有文法 admission」の
  並びで承認・稼働している**ことである。これが同じ失敗型なら backoff 側が先に壊れている。
- 恒真化する 2 者を実効 gate として数えると、成果物が発火しない保証を根拠として引く。
  proof chain は「候補の SWO 違反を動的に見つける gate」ではなく
  「構成的に SWO な言語への membership + 実 TU conformance」と書く。
- 79 値 admission と certified 側の 15 組 exact binding は別権威として分離する。
  79 値で置き換えると certified 側の受理集合が広がる。

**却下した選択肢:**

- 旧文形検査を候補 gate として残す — 入力が trusted 生成物になるため発火せず、恒真な保証になる。
- effect gate を sort だけ後段へ動かす、または外す — 全 hole 共通の防壁を軸ごとに非対称にする。
  deny-only である限り受理権威の二重化には当たらない。
- `sort_comparator_authority` を IR domain から生成し直す — certified 側の受理集合が 15 から 79 へ広がる。

## {{D:sort-ir-conformance-mismatch-unavailable}}. 実 TU と trusted evaluator の行列不一致は候補の拒否ではなく判定不能とする

**決定:** admission を通った候補は正準形へ正準化し、**正準形を材へ再 materialize する**。
build 対象・compile 対象・照合対象はすべてこの正準形で一致させる。
実 TU の観測行列と trusted evaluator の行列が byte 一致しない場合、および正準形の
compile / 実行 / timeout / 非決定性の finding は、候補の `REJECT` ではなく `UNAVAILABLE` とする。
`PASS` へ倒す経路は作らない。

**理由:**

- 正準化して再 materialize すると、候補が build へ入れられるバイト列は 79 個の正準形に限られる。
  compile されるのは trusted renderer の出力なので、その失敗や不一致は候補の欠陥ではなく
  evaluator・compiler・TU・pointer mapping の drift でしか起きない。
- D344 決定 4 は「候補に帰属できない故障は `REJECT` ではなく `UNAVAILABLE` とし、
  候補の受理集合・fitness・試行台帳に混ぜない」と定めている。本件はこれに該当する。
- 受理集合を狭める変更は過剰拒否を招きやすい。正当な IR が候補 reject として台帳と critic へ
  混入すると、その値の certified 選択を失わせる。
- `PASS` へ倒さないので規律 2 は緩まない。`UNAVAILABLE` は consumer 側で retryable として
  分離され、受理集合を広げない。

**却下した選択肢:**

- 不一致を候補の `REJECT` にする — 原因を候補へ一意に帰属できない。段 2 プランはこれを採っていたが
  段 4 で覆した。
- 候補の raw bytes を compile する — 正準化との二重表現になり、build 対象と照合対象がずれる。
- 不一致を無視して trusted 行列だけ採る — 実 TU conformance が恒真になり、検出器が消える。

## {{D:sort-ir-harness-indent-is-a-guard}}. hole の harness indent は整形ではなく安全性質として保持する

**決定:** 正準形の再 materialize も、既存の hole 挿入と同じく hole 行の indent を各行へ付ける。
sort 経路だけ indent を落とす引数を設けない。

**理由:**

- 既存実装が明記しているとおり、この indent は「行頭が空白+コードになり、diff 検疫の
  二次検査 (行頭 `#`) に偶発ヒットしない」ための担保である。整形上の都合ではない。
- 現在の正準形がたまたま空白始まりで `#` にならないことは、**候補集合に含意された恒真**であって
  担保ではない。正準 renderer の書式が変われば黙って防壁が消える。
- backoff 軸の正準再挿入は既定 (indent 保持) で行われている。sort だけ非対称にしない。

**却下した選択肢:**

- 正準形を逐語挿入する引数を足す — 上記の担保を sort 経路だけで外す。実装中に一度この形が
  入ったが、既存の検査が落ちたことで露見した。検査側の期待が過剰指定だったのではなく、
  実装側が防壁を外していた。
