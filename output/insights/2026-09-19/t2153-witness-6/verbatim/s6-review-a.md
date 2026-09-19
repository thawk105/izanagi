## 総括

**NO-GO。** 登録簿 +2 と rung1 の配線に、直接の受理拡大は確認できませんでした。ただし REPORT 正例は現状失敗し、変異登録の期待・帰属にも修正が必要です。最終 production 登録簿での official 同形確認も、提示資料からは完了を確認できません。

レビューは静的検査のみです。以下の実走結果はすべて親の [focus-logs.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/focus-logs.md) に基づきます。

### 1. REPORT 正例の fixture が supply を拒否させる

**real / must-fix / scope 内**

[test_condition_meaning_gate.py:1049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_condition_meaning_gate.py:1049) の正例は、REPORT の owner TU が条件付き宣言だけです。REPORT=0 の前処理結果は空になり、meaning が green でも supply は `preprocess-output-empty` になります。親ログの `[False]`・`[True]` 失敗と一致します。

REPORT fixture に無条件の宣言を1行足す修正が適切です。gate の空出力検査は維持してください。

`_request(5)` 自体の supply green 前提は静的には成立します。fixture builder が既存 `transaction.cc` と `backoff.hh` を補い、Options が BACKOFF_FIXED を供給するため、5 と既定 −1 で前処理本文が異なります。ただし現在の正例は先の assert で止まり、この後半を実走で確認できていません。

**放置時の影響：** 正常な REPORT の admitted／未確立解除を示す正例が赤のまま残り、完了台帳や変異成績を green と記録できません。

### 2. companion 欠落は meaning 単独の対照ではない

**real / nit / scope 内**

[test_condition_meaning_gate.py:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_condition_meaning_gate.py:1090) の `string(REPLACE …)` は、この fixture の入力では RUNG1=1 の flag だけを除き、REPORT の flag は保ちます。

しかし supply の `_collect_preprocess` も companion を検査するため、同じ入力を supply に渡すと **`companion-define-mismatch` で赤**になります。空 TU の修正後も同じです。

この test は「meaning arm が欠落を検出する」という名前・assert としては正当です。「meaning 単独が family を拒否した」証拠への流用はできません。両 arm の拒否を明示するか、meaning arm 単体の検査と記録してください。

**放置時の影響：** production の受理は変わりませんが、対照・変異台帳で拒否理由を meaning 単独へ誤帰属し得ます。

一方、SORT の `#undef` 負例は **refuted / nit / scope 内**です。無条件の `condition_gate_sort_variant = SORT_VARIANT` が undef より前に残り、supply の差分を維持します。枝は両値で非選択となるため、meaning 単独の `not-discriminating` に帰属できます。親ログも通過です。成果物への誤帰属は確認しませんでした。

### 3. rung1 の追加 test は実 helper の配線を検査しない

**real / nit / scope 内**

[test_silo_ladder_rung1_driver.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_silo_ladder_rung1_driver.py:30) は `getsource` の文字列検査だけです。factory 呼出しがコメントや未使用式に残っていても通せます。REPORT の確立後に RUNG1／BACKOFF_FIXED が未確立のまま残ることも、この test は検査していません。

現物の helper は factory の戻り値を evaluator に直接渡しており、現在の配線ミスはありません。追加するなら実 helper を呼び、evaluator に届く宣言型・対象 request を捕捉する検査が最小です。

**放置時の影響：** 将来の配線退行で rung1 JSON に REPORT が未確立として残っても、文字列 pin が通過し得ます。現版の値の誤りは未確認なので nit とします。

S1 の「fixture に枝がない」という疑いは **refuted / nit / scope 内**です。[helper:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_s1_direct_comparison.py:697) が owner TU に唯一の `#if SORT_VARIANT` を追加します。実 evaluator を通り、親ログでも新規 test は通過しています。ただし合成 fixture の検査であり、official TU の検証とは区別が必要です。

### 4. bytes 不変性と witness の主張境界

**refuted / nit / scope 内：直接のロジック緩和・過大主張は未検出**

base `657e1e5a7` と比較して確認しました。

- worktree の差分は `author-impl.patch` と bytes 単位で一致。
- gate 内の全113個のトップレベル関数・クラスのソース bytes が一致。
- `DEFINE_SPECS`、factory の1/0条件、旧宣言、CLI、`_effective_companions`、shared build root 分岐は不変。
- S1、p3_s4、S6 の production ファイルも bytes 不変。

module docstring は本文の意味・動的到達性・正しさを明示的に除外しています。SORT の正例名と本文変更対照も枝選択の範囲です。REPORT の assert は companion argv と `(selected, completed)` に限定され、footer の実行や報告値の正しさを主張していません。

**成果物への影響：** 対象 witness が green なら未確立一覧から当該 macro が消え、red なら family が拒否されます。旧経路の受理条件を緩める変更はありません。

ただし **分岐コード不変と REPORT の供給経路不変は別**です。登録により REPORT は共有 root 分岐に入ります。probe の同一入力では supply status・前処理 bytes/digest が一致していますが、任意の CMake cache 履歴に対する集合包含の証明ではありません。この一般化は **判定不能 / backlog / scope 外**です。放置時に履歴依存の入力で supply 判定が変わる可能性は残りますが、今回の入力で反例は確認していません。

### 5. m0〜m7 の事前登録修正

**real / must-fix / scope 内**

まず REPORT 正例を green にしてから matrix を走らせる必要があります。現状の既存失敗を KILLED に数えると変異成績が無効です。

| 変異 | 静的判定・登録の具体的修正 |
|---|---|
| m0 | コメントだけなら意味的に等価。**SURVIVED** が妥当。ただし現状の REPORT baseline 失敗を変異起因に数えない。 |
| m1 | 期待集合は不足。tuple pin に加え `test_v1_domain_and_claim_boundaries_are_exact`、registry macro 正例の SORT parameter、SORT 新規正負例、S1 新規正例も対象。`_compile_time_source_root` は削除 entry を直接引くため、多くは **unestablished ではなく KeyError** で落ちる。S1 新規正例もまず宣言型 assert で落ちる。帰属を区別する。 |
| m2 | 同様に domain pin・REPORT parameter・REPORT 新規正負例が対象。現在の rung1 文字列 test は登録簿削除で落ちないため、期待から除く。実 helper 検査を追加した場合のみ再登録する。 |
| m3 | patch 束縛 test による KILLED は妥当。ただし helper は登録 directive から fixture を作るため、通常の REPORT 正例は変更後の単純枝でも通り得る。意味的に等価ではなく、独立 patch pin が必要な変異。 |
| m4 | 現在は文字列 pin が KILLED にするだけ。「宣言型検査」「正常版 reject→変異版 admit」は未実装なので事前登録からその説明を外すか、対応 test を追加する。 |
| m5 | **0/0 は KILLED、0/1 は SURVIVED**。`default != "0"` が残るため。非対値 test の3 macroそれぞれについて、失敗期待は0/0に限定する。これは宣言可能集合の拡大であり、そのまま family admit の証明ではない。 |
| m6 | SORT 正例2 parameter は一意性違反で KILLED。さらに undef 負例も落ちる。復元した外側枝にも undef が入り、無条件値差分が消えるため supply green の assert が成立しない。期待集合と帰属を追加する。 |
| m7 | 変異箇所を具体化する。たとえば `combined = {}` なら REPORT の要求・既定とも枝が消え、正例の supply は赤、meaning も非識別になる。**単一 arm の帰属ではない**。registry macro の REPORT parameter を meaning 単体の検出 node として登録し、両 arm 正例とは分ける。companion 欠落負例の理由コードも変わり得る。 |

全suiteの失敗 node 完全集合は静的検査だけでは確定していません。上表は現登録の明確な不足・誤りです。実走 spec は選択 node 集合を明示し、その集合内の期待失敗を完全列挙してください。

**放置時の影響：** baseline failure、KeyError、supply拒否を meaning の検出力として数え、変異台帳の KILLED 集合と単一理由の記録が誤ります。

### 6. official 確認と成果物への到達

**判定不能 / must-fix / scope 内**

提示された実測は shadow 登録簿の login probe と、計算ノードでの fixture 焦点走です。裁定が要求する「最終 production 登録簿・official 同形供給の login／計算ノード cell」、変異 matrix、受入全走の完了証拠はありません。焦点走2は green ですが、pytest 344.57秒で5分上限も超えています。

永続化のコード経路は確認できました。

- rung1：helper が admission を JSON 化し、`gap_leg.condition_gates` に格納。
- S1：[condition_gate_receipt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/s1_direct_comparison.py:253) が admission を直列化し、[session-start:1251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/s1_direct_comparison.py:1251) に保存。

従って未確立一覧が縮む経路は存在します。ただし新しい実成果物で縮小した証拠とはまだ同一視できません。

**放置時の影響：** official SORT が環境要因で meaning red なら従来通った certified cell が拒否され、成功時の receipt が出ません。これを未確認のまま台帳で「official 完了」と扱うことはできません。

**GOへの条件は、REPORT fixture 修正、変異登録の訂正と green baseline 上での検証、裁定済み official 確認の完了です。**