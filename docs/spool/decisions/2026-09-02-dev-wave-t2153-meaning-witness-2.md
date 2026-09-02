---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2153-meaning-witness
seq: 2
---

## {{D:compile-time-branch-witness}}. 意味 witness の第二の型を、所有 TU 全体の枝選択として持つ

**決定:** `condition_meaning_gate` の実行側の意味の節に、既存の有限点別 witness とは別の型として
**compile-time の枝選択 witness** を持たせる。macro ごとに (所有 file の相対 path、開始指令の逐語)
だけを宣言し、値と同伴 define は `DefineRequest` と `_validate_define_request` の正本を再利用する。

観測は、開始指令の直後に選択 marker を、対応位置に完了 marker を挿入した**所有 TU 全体**を、
供給側が導出した実 compile command で前処理して行う。要求値と既定値の両方で観測し、
`(選択, 完了)` が要求値で `(1, 1)`、既定値で `(0, 1)` のときだけ green とする。
両者が同じなら非識別として赤にする。

主張の範囲は「所有 TU において、その define の値が宣言した枝の選択を決めている」ことに限る。
動的到達性、実行時の意味、positive control が期待する異常の発火は主張しない。

**理由:**

- 条件指令の断片だけを切り出して単体で前処理すると、所有 TU の文脈が失われる。手前に
  `#undef` が 1 行あるだけで、実 TU では枝が選ばれないのに witness は「選ばれた」と言う。
  これは意味を確立していない。段 6 の敵対レビューが具体的な入力で示した。
- 所有 TU 全体を前処理すれば、入れ子・行継続・コメント・raw string の扱いは**コンパイラ自身が
  決める**。自前の前処理指令パーサを持つ必要がなくなり、物理行の正規表現が
  「誤って深さ 0 と判定する」「誤って深さ非 0 と判定する」の両方の欠陥も消える。
- 指令がコメントや文字列の中にあった場合、挿入した marker も前処理で消えるため完了 marker が
  観測されず赤になる。fail-closed が構造的に成立する。
- D1242 が却下したのは「BACKOFF_FIXED 以外を**同じスカラー復号器**として一般化する」ことである。
  本決定は復号器を流用せず、macro ごとに別の型の witness を宣言する。

**却下した選択肢:**

- **選択された枝の本文 bytes の期待値を macro ごとに焼く** — patch の編集で常時赤になる。
  枝の選択を確かめる目的に対して過剰である。
- **自前の前処理指令パーサで入れ子の深さを数える** — 行継続・コメント・raw string の扱いを
  自前で持つことになり、実測で両向きの誤判定が見つかった。
- **断片の単体前処理を残したまま、前方に `#undef` が無いことだけ検査する** — header 側からの
  無効化を塞げず、文脈欠落の一般形が残る。

## {{D:meaning-supported-set-does-not-widen-legacy}}. 対応 macro 集合の拡張が旧宣言型の受理面を広げてはならない

**決定:** `MEANING_SUPPORTED_MACROS` を広げるとき、既存の `MeaningWitnessDeclaration` と
CLI の旧宣言経路は `BACKOFF_FIXED` に固定する。新しい witness は registry の factory 以外から
発行できないようにする。

**理由:**

- 旧宣言型の検査は「対応 macro 集合に属するか」しか見ていなかった。集合を広げた瞬間、
  別 macro を BACKOFF 用の数値復号器で評価して green にできる。これは D1242 が却下した形そのもの
  である。段 3 と段 6 の敵対レビューが独立に同じ穴を指摘した。
- 意味 witness を増やす作業は、受理集合を**狭める**方向でなければならない。集合の拡張が
  副作用として別経路の受理を広げるなら、正味で緩めたことになる。

**却下した選択肢:**

- **集合の拡張だけ行い、旧経路は既存のまま置く** — 上のとおり受理集合が広がる。
- **旧宣言型を削除する** — 既存の BACKOFF witness の呼び手を壊す。本 wave の射程外である。

## {{D:witness-wiring-only-where-artifacts-shrink}}. 宣言の配線は、成果物の未確立一覧が実際に縮む driver だけに行う

**決定:** 意味宣言の factory を配線するのは、対象 macro を実際に要求し、その admission が
成果物へ載る driver に限る。要求しない driver、または要求しても route 不一致で admission 前に
拒否される driver は配線しない。配線しない理由は driver 名とともに記録する。

**理由:**

- 汎用 pipeline は `CCBENCH_` 名前空間の cache option 経由で define を渡す。対象の positive control
  は名前空間外の裸マクロで route が一致せず、admission 作成前に拒否される。配線しても
  成果物の未確立一覧は 1 件も縮まない。
- 成果物の値・受理集合・参照を変えない編集は、編集面と pin 閉包を無駄に広げるだけである。
- 同じ macro が driver ごとに green と unestablished へ分裂する懸念は、対象 macro を要求する
  driver をすべて配線すれば生じない。分裂が起きうるのは要求しない driver ではない。

**却下した選択肢:**

- **意味の節を呼ぶ生産側をすべて機械的に配線する** — 自己 hash pin を持つ面を含み、
  成果物を変えないまま編集面と pin 閉包を広げる。
- **配線しない理由を件数だけで残す** — 後続が内訳を復元できない。
