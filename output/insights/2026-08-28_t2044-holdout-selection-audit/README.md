# [T-2044] holdout 選択防壁の限定監査

authority: none
default_effect: no-state-change

固定 commit `f34e19be94a3608099773ac6c1a12a98ae992048` を read-only 中心で監査した記録である。状態の正本は worklog、採用済み判断は decisions とする。本監査は新しい guardrail、署名、台帳、nonce、one-shot 代替を実装していない。

## 結論

**「holdout の値を見てから使用する測定を選択・凍結・主張へ採らない」は、official 解禁後の実装では守られていない。**

現 commit では official の production 拒否と budget approval 未批准により A/B 攻撃は到達不能である。しかし両者は同じ A/B を一律に止める可用性 blocker であり、使用 result を値を見る前に固定する選択防壁ではない。official・budget・通常 activation が独立に満たされた後は、適格な fresh 完走 result A/B の値を見てから B を `--floor-result` に渡し、最初の candidate を B から生成できる。

一方、floor 数値は s8b oracle winner/tie-break と s8c conclusion の直接入力ではない。同一 judge 入力を固定した狭い非干渉は成立する。これを、floor-backed な candidate・再凍結・proof chain・論文主張全体が D1124 準拠である、という強い主張へ一般化してはならない。

## 稼働 wave との重複

開始時の worktree、process、job artifact を T-2044 と対象 symbol で検索した。T-2044 を所有する別 wave は 0 件だった。同時稼働していた T-1817 / T-1840 / T-1905 / T-1933 / T-1934 / T-2018 は別対象であり、この branch の変更 path と重複しない。

## consumer 件数

production と test、値 read と構造契約、同名別 family を混ぜずに数えた。

| 対象 | 件数 | 分類 |
|---|---:|---|
| `_assert_official_permitted` 定義 | 1 | `s8b_floor_campaign.py` |
| 同 production callsite | 2 | public wrapper と private core |
| 別入口の CLI official 拒否 | 1 | 上の関数 call ではない |
| 同 test textual reference | 10 | runtime 防壁に数えない |
| floor-result `eligible_for_refreeze` direct production read | 4 | renderer、live admission verifier、candidate admission、ratified full validator |
| 同 structural schema contract | 1 | `s8b_floor_contract._RESULT_KEYS` |
| 同名別 receipt family の production consumer | 1 | MoCC trace receipt は false を要求。floor-result chain から除外 |
| 同 test textual reference | 31 | 8 test / fixture file。runtime 防壁に数えない |
| ratified full proof-chain production entrypoint | 4 | oracle gate-check、run-block、report CLI、judge CLI |
| `floor_result_path` CLI 入口 | 1 | caller 指定の必須引数 |
| 同 formal parameter / keyword edge / sink | 3 / 3 / 1 | sink は `_load_repo_object` |
| 事前固定 path との equality predicate | 0 | official path・protocol・完走性・資格の検査とは別 |
| `s8c_result_judge` 公開3関数の production callsite | 0 | library contract は final claim 配線の証拠でない |

`eligible_for_refreeze` の security-relevant な2段は candidate admission と ratified full validatorである。live admission verifier は reported bit と共有台帳から再導出した bit の一致を検査する。renderer は表示だけで、防壁ではない。

## A/B の具体的経路

1. A/B は同じ protocol、freeze、environment に属する異なる fresh official 完走 run とする。
2. 両方が current schema、official path、sibling manifest/journal、binary receipt、live admission、統計再計算、`eligible_for_refreeze is True` を満たす。
3. candidate が未作成の状態で A/B の値を比較し、B の repo 相対 `result.json` path を `generate-v2-candidate --floor-result` へ渡す。
4. `s8b_holdout_freeze._validate_floor_inputs()` は B 自体の整合を厳格に検査するが、測定前に選んだ単一 path との一致は検査しない。
5. `build_v2_g1_candidate()` は `B.floors` を candidate `floor` へ投影し、B の path/hash を `floor_source` へ記録する。
6. fixed candidate path の create-only はこの B の初回書込み後の上書きを止めるが、初回に B を選ぶ操作を止めない。

現 commit の実走では official と budget で止まるため、この反例は条件付き real である。blocker を選択防壁と数えない。

## downstream の実効範囲

| 境界 | real/refuted | 事実 |
|---|---|---|
| candidate 初回 A/B 選択 | real | 事前固定 identity との比較 0 |
| candidate → ratified g1 自動同一性 | refuted | candidate path/hash の参照 0 |
| ratified `floor` → `floor_source.result.floors` 投影一致 | refuted | equality 検査 0 |
| ratified source bytes/proof chain | real | path/hash、journal、manifest、binary receipt、eligibility を再検証 |
| s8b oracle winner への floor 数値直結 | refuted | floor は argmax/tie-break の入力でない |
| s8b oracle verdict への artifact 間接影響 | real | binary receipt/store 再検証が determinate/indeterminate を変え得る |
| s8c conclusion への floor 数値直結 | refuted | `judge()` は floor receipt を受け取らない |
| s8c publish provenance | real | current floor path/hash を metadata と publish gate に使う |
| s8c production final claim 配線 | refuted / 未証明 | 公開関数の production callsite 0、CLI 0 |

ratified generation は後続世代で `/floor` と `/floor_source` の変更を許す。oracle full validation は g1 以外を拒否するが、s8c の floor bytes 検査は同じ full validation を共有しない。この consumer 境界差も強い一括主張を禁じる。

## D1124 と D893

D1124 は新しい fresh 測定を繰り返すことを許すが、値を見て certified source を選ぶことを禁止する。D893 は同一試行識別子を複数実行先で複製する best-of-N を対象とする。異なる fresh A/B は D893 の射程外であり、同 D の T-469 機構も未実装である。campaign/run ID、attempt ID、資格 bit の存在を代替防壁に数えない。

## 主張上限

安全に主張できるのは次だけである。

- 現 commit の official A/B 経路は到達不能。
- 同一 oracle/8c judge 入力を固定すれば、floor 数値は winner/conclusion の計算入力でない。
- 選んだ floor source の path/hash と current provenance は記録・再検証される。

次は主張できない。

- 使用 floor result が値を見る前に固定された。
- ratified floor 数値が candidate および floor_source から自動導出・同一性束縛された。
- floor-backed candidate、再凍結、oracle/8c 公開物が D1124 準拠の certified 選択・論文主張を支える。
- s8c official table が production final claim へ配線済みである。

したがって、測定前固定の既存 proof が示されない floor-backed candidate・再凍結・主張は **advisory / non-certifying** を上限とする。狭い floor 数値非干渉は別に維持する。

## 最小裁定項

将来 official 解禁後の強い floor-backed claim を許す前に、D1124 の「値を見る前の使用測定固定」をどの既存 authority が証明するかを裁定する。既存 authority で証明できない場合の実装は別 wave とし、D95 Codex author を必須とする。

## 実測と未実走

- 静的: `rg` / source 再読 / AST により上記件数、def-use、call closure、0 edge を確認した。
- read-only Codex: plan 1 本、敵対相談 2 本。すべて `check_codex_output.py` rc=0。逐語は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2044-holdout-selection-audit/`。
- 関連 test 6 file: `tools/run_tests.py` 経由、621 passed / 2 skipped、rc=0、677.74 秒、bounded local peak 2,949,328,896 bytes。skip 2 件は explicit-user-command-only の tracked-files growth hold。
- full acceptance 1: `tools/dev_wave_wait.py acceptance --lease-optional` 経由、18,033 passed / 61 skipped、赤 0、`child-green`、tested main `f34e19be94a3608099773ac6c1a12a98ae992048`、tested tip `eeb6207a3545041f65dec61c6fa3ac17f9c4a07d`、log sha256 `28bfb085a7b99b32c1db20aaa190c12591450e335d0245835ae2f224e663d264`。
- floor / oracle / 8c の本走と性能測定は 0 件。未実走を緑と扱っていない。

## scope 外

- 新しい guardrail、署名、台帳、nonce、one-shot 代替。
- D893 / T-469 の実装、official guard 解禁、budget approval、successor preregistration。
- floor / oracle / 8c の本走、性能値の再取得。
- 将来実装の設計・author 作業。必要なら D95 Codex author の別 wave とする。

## dev-wave 改善候補

段 8 で `docs/skill-self-improvement.md` を再読して確定する。この wave では改善も次 wave も起動しない。
