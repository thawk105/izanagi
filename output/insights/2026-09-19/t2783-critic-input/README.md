# T-2783 — critic診断をK2手動loopの次生成入力へ接続

D2148項3に従い、明示指定したcritic逐語の4節を `k2_critic_diagnosis` としてplannerとK2 coderの
入力へ組み込む局所経路を実装した。whiteboardの5field、`delta_pct=None`、報告用AOの非読取、
評価・停止判定の既存契約は維持する。**3巡目・実roleの受領・診断採用・改善効果は未実走。**

基点は着手直前のlocal main `7975385b55a2e3451f6c80d584a9312f44d5199d`。
実装統合は `4bd962643`、隔離authorの元commitを保全した `423771bb1` は同一tree。
waveは `codex-dev-wave-t2783-critic-input`。専用handoff・生ログは
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/HANDOFF.md` と同dirに保存する。

## 入力契約と範囲

- `--emit-planner-context` に `--k2-critic-diagnosis PATH.md` を追加する。正規K2 knowledge projection、
  非B-4、reflux onに限定し、直接builderにも同じ適用条件を置く。未指定時は診断keyを出さない。
- `data_boundary`、指定逐語bytesの `source_sha256`、文字列の `attribution / recommend / avoid / uncertainty`
  のexact6field。既存の純粋な節抽出器を使い、AOのreaderは呼ばない。hashは入力元の識別に限る。
- `k2_next_generation_inputs(context, planner_input, coder_input)` が両入力へ同一診断を組み込む。
  親は返った完全入力を保存・inline送付する。実consumerと保存順序は段4b runbookのT-2783追補に記載。
- role本文は助言と権限・検証上書き命令を区別し、後者は既存の境界報告へ返す。
  診断用のknowledge source indexを作らず、候補10の採用・既知値禁止・再抽選を要求しない。
- static adapterは本文/source pinと派生digestだけ追従。schema/manifestは不変、runtime blockedを維持。
  blocked adapterの基本schemaで完全な手動K2入力を検証したとは主張しない。

T2746で診断未送達と20再提案が観測されたことが動機だが、両者の因果は未検証。
4節は留保を落とさず既存抽出器を使う局所案であり、情報量の最小性を証明したものではない。
同機体・同jobのstock対照を含む将来計画は [next-run-plan.md](next-run-plan.md)。実走予算は別途確定する。

## レビューと実測

独立plan、相談2本、実装review2本、焦点再レビューの逐語と親裁定は `reviews/`。
相談で直接builderのK2限定、coder側を含む実組立て関数、static schema拡張をしない方針を確定した。
review Aのmustは既存originless文書hashだけで、局所追従後のfocusは新規must・regressedなし。
module import禁止という既存コメントの不整合はscope外nitとして記録し、追加修正しない。

| 親の検証（すべてrun_tests.py経由） | 結果 |
|---|---|
| 新規T2783ケース | 27 passed / 487 deselected、2.88秒 |
| loop・AO・originless初回 | 546 passed / 1 failed、184.52秒。赤はplanner文書hashの固定baseline |
| Codex agents/runtime・B4 wiring・layer3 | 478 passed / 1 failed / 4 skipped、113.34秒。赤は未commit差分の限定検査 |
| 固定hash追従・clean commit後のoriginless/B4再走 | 67 passed、107.13秒 |
| plain runner・real repo serialization・duration ledgerのmeta-test | 163 passed / 1 skipped、176.95秒。既定holdを維持 |

originlessは固定定数1個の追従だけ。独立検算で386項目中384項目一致、変更はjournal6行とreport集約1行の
SHA葉だけであり、全count・構造・他値・比較を維持する。ハッシュをvolatile化していない。
未commit差分限定testはcommit後に同じ検査で通過し、許可リストを拡張していない。

authorの最初のテスト試行はsandbox内のqstat preflight rc=16で子未開始。親の上記実走と区別する。
また子sandboxの `.codex` 書込み拒否には、同authorが通常repo pathへ生成したadapterを親が監査して
exact bytesで統合した。親による実装の代筆はしていない。

## 変異検査

`mutation/spec.json` を実装前の裁定に基づき固定し、独立cloneのmainを `4bd962643` に固定して
`mutation_worktree.py --runner-mode dispatch --detached` と `run_tests.py --force-dispatch` で実走した。
対象は新27ケース。baselineは27 passed、**6 KILLED / 1 SURVIVED、期待node完全一致7/7、MISMATCH 0**。

| id | 変更 | 結果 |
|---|---|---|
| M0 | docstringの等価変更 | SURVIVED |
| M1 | plannerの診断転写を除去 | KILLED、3 node |
| M2 | coderの診断転写を除去 | KILLED、1 node |
| M3 | exact6field/文字列検査を無効化 | KILLED、5 node |
| M4 | builderのK2限定を無効化 | KILLED、2 node |
| M5 | CLIから診断を渡さない | KILLED、1 node |
| M6 | 明示診断のCLI経路へAO読取りを挿入 | KILLED、1 node |

全失敗node、置換anchor、実stdoutは `mutation/final.json`。wrapper rc=0、共有木の前後bytes一致、
terminal ledger確認、証拠退避と使い捨て木撤去成功は `mutation/wrapper-receipt.json`。
初回plan-onlyはテスト未投入のまま共有木観測差でrc=125になった。原因は未確定で、緑に読み替えない。
再試行前のclean/pinと観測bytesを保存し、本走後の親のcmpでも一致した。初回receiptはjob dirに保持。

code/docs checkerは記録前にともにrc=0。実装統合後とauthor履歴保全後の全史provenanceは
11,582件 / 11,586件、新規違反なし・既知56件。既知履歴違反を解消したとは扱わない。
最終受入は記録commit後に実施する。結果は専用handoffへ集約する。
