---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t244-p3-redesign
seq: 2
---

## {{D:p3-origin-ledger-prototype-v3}}. D121 P3 の origin ledger は U-A〜U-G の明示裁定に従い prototype として実装する — 敵対 28 所見を 3 巡で閉じ、P3 充足とは数えない

**背景:** D147 は P3 の実装を差し戻し、裁定パッケージ U-A〜U-G を返した。2026-08-04 12:44 の
ユーザー明示裁定 (「５件は推奨通りで」、一次控えは rulings-inbox、fold は別 wave) が全 7 件を
親推奨どおり採用し「実装 wave を再起票できる」とした。本 wave はその再起票である。
着手時点の brief は明示裁定の着弾前で、起票を黙示の採用と読む推定を置いていた —
これは D147 却下案 (a) と同型であり、敵対レンズが攻撃した後、明示裁定へ根拠を差し替えた
(brief-erratum-1)。

**決定 (1): origin 識別を構造で閉じる。** `origin_id` は authority manifest (設計本文 §3.5 の
列挙を固定 schema 化、`ccbench_commit_oid` は 40hex 強制) の canonical digest とし、caller handle を
持たない。cell key = descriptor / axis semantics / verifier policy / environment contract の
4 digest で、authority loader が同一 cell の 2 件目を拒否する。authority root は repo 内固定
path 1 点で committed bytes 照合 (HEAD を OID へ 1 回解決し `<oid>:<path>`、hardened git env)。
runtime は git-common-dir 配下で git commit しない (U-E の分離の帰結)。

**決定 (2): batch を第一級にし、開示は seal に集約する。** cardinality >= 2 の salted
commit-reveal (candidate / result / class とも salt は producer 保持、seal で開示・照合、
既知 schema_ref は IR decode で wire 正準性検証)。certifiable seal は **sealed batch の
query 数**で floor を判定し (tombstone 消費は予算のみ)、公開 class は distinct 全集合との
完全一致。floor 未充足の終端は aborted seal (class 空)。予算 floor は formula_id + 非退化
条件 + 構築的 feasibility 検査を持ち、係数値は authority 注入のまま。

**決定 (3): 変異証拠の限界を正直に記録する。** (a) M-A2 の登録 operator
「global → per-origin flock 置換」は単一点変異で表現不能と判明し、flock 除去 operator へ
再照準した (erratum)。(b) operation 排他は多層防御であり、両層変異でも「別 operation の受理」は
再現しない — 変異で証明済みと名乗るのは「二層除去での altered continuation 受理」までとする。
(c) M-N12 は受理集合を変えない diagnostic sensitivity pin として別枠記録し、実行 spec では
category=negative へ写像した (harness の許可集合が 3 値のため。凍結 spec との差分は台帳に記録)。

**決定 (4): 成果物の名乗りは U-G の会計に従う。** 本実装は「P3 用 origin-ledger prototype
(codec/FSM/registry)」であり、**P3 は依然 FAIL、cap-lift 上限 1 (D114) は不変**。P3 の充足は
producer 結線と P7 (consumer の origin proof 要求、受理集合の変更ゆえ D96 手続) まで含めて数える。
production authority は空 registry で、実在 campaign からの manifest 捏造登録は行わない。

**却下した選択肢:** (a) 起票を黙示の裁定採用と読んで進める — D147 却下案 (a) と同型
(明示裁定の実在により結論は同じだが、根拠として不可)。(b) 期待値未達の変異登録を
そのまま KILLED 集合に残す — F28 型の偽 kill。(c) seal 前 bytes への平文保持 —
低エントロピー結果の辞書 oracle になる。

**研究状態への影響:** production caller ゼロ・authority 空のため、certified 選択・レポート・
試行台帳・proof chain の現在値は不変。受理集合の変更もない (未結線 leaf + 専用テストのみ)。
