# Stage 6 review 裁定

## 実測

- 修正前差分は `s6-pre-fix.patch` に固定した。
- production target の通常 finding は `AI-Agent trailer がない` の exact 1 件だった。
- 分断 message は legacy `AI-Agent` parser が前半 block、isolated correction parser が後半 block を返し、現実装では `CorrectionAudit.exact=True` になった。
- target の通常 merge path は空、`diff-tree --cc` は docs 3 path、per-parent union は実装面を含んだ。

## real — 今回の code/test fix

1. correction と通常 `AI-Agent` が同じ最終 trailer block にあることを isolated default-divider parse でも要求する。raw 物理1行と `--no-divider` canonical parse は残す。
2. `forward-corrected=1` は全 finding が空で rc=0 のときだけ stdout へ出す。内部で exact target missing だけを相殺する条件は不変。
3. object 不在と Git 実行不能を区別する。missing だけ False、基盤異常は rc=2。
4. singleton の key/target/payload の重複正本をなくす。payload が名指す target と相殺 target は同一生成元にする。
5. D95 path は merge preflight と履歴監査で combined semantics に揃える。通常 child は staged path、`MERGE_HEAD` 中は index が全 parent と異なる path の積集合、commit 後 merge は combined diff path。per-parent union で持ち込まれただけの実装を当該 merge actor の新規 authoring としない。
6. production target の normal finding exact 1 件、分断 block、merge pre/post parity、object backend failure を回帰テストで固定する。複数 tip、merge-side 既存 correction、代表的 raw whitespace も、冗長化しない範囲で固定する。

## real — Stage 7 の docs/operations fix

1. `DW-O17` を auto-merge 回避の実行手順へ改訂する。`OLD_HEAD` 保存、`git merge --no-commit`、message-file 作成と単独 rc preflight、`git commit -F`、commit 後の full-history provenance 監査を必須にする。conflict は解消後に同じ preflight を再実行する。
2. correction を初めて取り込む branch の `OLD_HEAD..HEAD` は target を含まないため、coupled evidence の監査範囲として不完全である。checker の selected-set membership は緩めず、correction candidate を含む audit は target-inclusive range または既定 full-history を権威にする。delta range は補助診断に限定する。
3. F25/F37 の再発として、auto-generated merge message が preflight を迂回した型と、merge 後 full audit を省略した型を記録する。
4. 停止 consumer は T-145/T-146/T-173 の handoff path で列挙し、task ID drift を起こさない。既存 handoff は書き換えず本 wave handoff から再開条件を束ねる。
5. 新 D は通常 merge path 空、combined diff docs 3 path、per-parent union の実装 pathを分離する。「combined path」を手動 conflict resolution の証拠とは呼ばず、role=integrator は merge 前の採否判断から裁定する。

## refuted / scope

- correction selected set に target が必要な条件は維持する。`C^!` を単独 green にする受理拡大はしない。
- payload の `claude-opus-5/xhigh/integrator` と scope なしは回収 evidence と一致する。
- stdout の rc を読む consumer には識別可能だが、green status の文字列を失敗時に出す必要はないため上記のとおり狭める。
- ambient Git object/replace-ref 全般の hardening、一般 correction registry、履歴 rewrite は scope 外。

## mutation 再登録

- M1/M2/M4/M6/M7 は outcome-changing kill のまま。
- M3 は固定 payload の全 enforcement site を同時に変える combined mutant とする。
- M5 は raw value exactness の単一 authority を壊す mutant とする。実装側の重複 enforcement は除く。
- M8 は normal-green 前提を可視化する structural/diagnostic pin とし、outcome-changing kill に数えない。
- M9 は merge の非 first-parent 側にある既存 candidate を落とす mutant を含める。
- M10 は diagnostic sensitivity pin であり kill 件数に数えない。
- M11 は raw/canonical/final-block multiplicity の全 enforcement site を同時に弱める combined mutant とする。

## Stage 6 判定

fix 前は NO-GO。上記 code/test fix 後に、両 reviewer 所見の closed / partial / regressed 表を持つ焦点再レビューを1本実行する。
