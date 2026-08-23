---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: worktree-rulings-20260824-followup
seq: 1
---

## {{D:t139-pilot-remains-forbidden-until-operational-closure}}. T-139 の pilot 禁止は運用経路の閉包まで維持する

**決定 (ユーザー裁定):** T-139 の `pilot_submission = forbidden` を現時点では解除しない。
sealed series / receipt-set、production consumer、公開 API、PBS driver、collector を実装・検証し、
private receipt の検査から実投入までの運用経路を閉じた後に、pilot だけを本走と分離して再提示する。
本走禁止、certified 成果物、公表への昇格は引き続き変更しない。

**理由:** private receipt gate の実装と検証は完了したが、実投入を担う producer / driver / collector と
receipt-set は未実装である。canonical な解禁だけを先行させると、D292 が避けた「実装を条件へ
合わせるために受理条件を緩める圧力」を再導入する。残る実装 wave は pilot 禁止を維持したまま進められる。

**却下した選択肢:**
- private gate の緑だけで pilot を直ちに解禁する — 解禁の運用実体が無く、decision だけが先行する。
- pilot と本走を同時に解禁する — 根拠と成果物影響が異なり、D292 の分離要求に反する。

## {{D:shard-receipt-completeness-deferral-maintained}}. shard 完全性の受領証証明は実害が出るまで見送る

**決定 (ユーザー裁定):** 受入が既定 K=2 で分割される事実を踏まえても、受領証へ shard 完全性の
証明項目を追加する変更は見送る。従属する red-check receipt の `nodes` / `collections` 対応を
束縛する schema 変更も行わない。分割の取りこぼし、または空の収集結果を受理したことに起因する
実害が1件観測された時点で、両者を同時に再訪する。

**理由:** 「分割は既定で動いていない」という D728 の補強論拠は D733 で撤回されたが、実害0件と、
実行器内部の完全性検査が実在することは変わらない。欠けているのは受領証だけを読む第三者向けの証明で、
受理条件を扱う3道具と旧 schema の移行を今変更する費用は主目的から遠い。

**却下した選択肢:**
- 既定 K=2 になった事実だけで直ちに受領証 schema を改訂する — 実害の有無と外部証明の要否を混同する。
- red-check schema だけを先に変える — 従属先と分離すると同梱理由が消え、処遇が再び宙に浮く。

## {{D:trace0-identity-gaps-close-before-formal-measurement}}. TRACE=0 同一性検査の3穴は正式計測前に閉じる

**決定 (ユーザー裁定):** TRACE=0 前処理同一性検査に残る次の3穴を、同検査を通した値を正式な
性能証拠へ使う前に同一 wave で修理する。(1) CMake の間接マクロ供給と行継続 `#define` の見落とし、
(2) macro include operand の差し替えによる false-green、(3) 活性 hash 不一致と
`identical: true` が同時に立つ report の自己矛盾。各穴を単独に発火させる負の対照を置く。
pilot-only・非認証の配線確認まで一律に禁止しない。

**理由:** include 差し替えの false-green は、性能計測用ビルドから trace 処理を完全除去する
絶対規律1へ直接掛かる。mocc の TRACE=0 値を正式材料へ使う前なら、成果物を遡及訂正せずに閉じられる。

**却下した選択肢:**
- report の自己矛盾だけ直し解析上の2穴を残す — 表示は整っても false-green の受理集合が残る。
- 3穴を既知限界として受容する — 正式な性能証拠が観測者効果の除去を証明できない。

## {{D:post-fold-targeted-preland-validation}}. fold 適用後 tree は実コーパス依存検査を land 前に通す

**決定 (ユーザー裁定):** fold の決定的な dry-run 出力を隔離した tree へ適用し、fold が変更する
canonical 台帳を読む実コーパス依存テストだけを land 前に実行する関門を追加する。受入全走を
fold 前後で2回行わない。対象検査の選定と、fold 出力と実適用 bytes の一致を実装 wave で固定する。

**理由:** 受入全走が緑でも、その後の fold が main を赤にした実害が1件ある。fold は決定的なので、
原因に近い対象検査だけを事前に掛ければ、全走コストを倍にせず同型退行を閉じられる。

**却下した選択肢:**
- fold 後に受入全走をもう1回行う — 費用が実害の範囲に見合わない。
- land 後の赤を次 wave で修理する — 全 wave を止める canonical main の赤を再許容する。

## {{D:codex-skill-real-repo-growth-hold-maintained}}. Codex Skill の real-repo docs 検査は growth hold を維持する

**決定 (ユーザー裁定):** `test_check_docs.py::test_real_repo_clean` は
`GROWTH_TEST_HOLDS` のままとし、受入全走へ戻さない。Codex Skill の実ファイルと checker 定数の
一致は、クラス2/3完了時に必須の `python3 tools/check_docs.py` 明示実行で担保する。

**理由:** held node は docs 総量に比例する同じ checker の重複実行であり、戻しても検出力は増えない。
既存の explicit-user-command-only 裁定と、成長比例テストを受入から外す目的を維持できる。

**却下した選択肢:**
- 当該 node だけ受入へ戻す — 同じ checker を二重に実行し、既裁定の成長比例 cost を戻す。
- checker の明示実行も省く — Skill drift の機械防壁そのものを失う。

## {{D:cleanup-branches-codex-safety-reductions-maintained}}. Codex cleanup-branches の安全縮退7面を維持する

**決定 (ユーザー裁定):** D745 が全数記録した Codex 固有の安全縮退7面をすべて維持する。
Claude command と同じ削除結果へ揃えず、「共通 dispatcher に安全縮退を上乗せした裁定済み例外」
として扱う。今後も完全一致とは記述しない。

**理由:** 7面はすべて prune・削除・権限拡大の範囲を狭める向きで、CC自動合成の主経路へ影響しない。
製品間の結果一致だけを得るために破壊操作の安全弁を外す利得はない。

**却下した選択肢:**
- Claude command と同じ結果へ揃える — local main、foreign / locked worktree、prune 等への
  破壊操作範囲を広げる。
- 差を未記録へ戻す — 次の一致検査が同じ差を未解決として再発見する。
