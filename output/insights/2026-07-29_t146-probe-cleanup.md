# [T-146] AF_UNIX capability probe cleanup の例外安全性

## 結果

T-146 は test-only capability helper
`_sandbox_permits_short_alias_bind()` の cleanup / ownership 契約を固定した。
production `tools/dev_waves/`、isolation meta-test、product artifact は変更していない。
実装 commit は `5b650727ee653d1a60a7add4daa87c86cc7f24cd`。

helper は literal `.s` と既存 capability 列
`socket → bind → chmod → stat → listen` を維持し、次を追加で保証する。

- probe 前の `.s` 実在は regular file / broken symlink とも `FileExistsError` にし、置換も削除もしない
- bind が pathname を作らず失敗した場合は ownership syscall を呼ばず capability `False` にする
- bind が pathname を作ってから失敗した場合は bound address を直接観測し、helper-owned entry だけを回収する
- cleanup の `FileNotFoundError` は nofollow 再観測で不在を確認できた場合だけ受理する
- cleanup の非 `FileNotFoundError` は pathname が既に消えていても元の型・errnoで送出する
- unlink の成功応答後も pathname の不在を確認し、no-op unlink の偽緑を拒否する

hostile concurrent writer、socket close と unlink の複合 fault、production helper の partial-bind
一般化は、single-writer の test helper に対する T-146 の独立再現を越えるため scope 外に維持した。

## review と変異

段2 plan v1 は段3の ownership / acceptance 2レンズで NO-GO とし、preexisting entry、
recovery 前の直接観測、例外種別と pathname 状態の分離を plan v2 へ反映した。
段6の初回2 review も、path-absent bind failure で不要な `getsockname()` を呼ぶ退行と、
cleanup 変異が等価になる fault fixture を blocker として NO-GO にした。
fix 後の focused re-review は実装 blocker 0 で GO。

統合 commit 後の変異本走は 3/3 KILLED、unexpected node 0、SKIP 0。

- M-T146-A: partial-bind ownership 回収を失わせ、対象1 nodeだけが失敗
- M-T146-B: cleanup catch を `OSError` へ広げ、EPERM / EIO の2 nodeだけが失敗
- M-T146-C: unlink 後の不在確認を除き、no-op unlink の1 nodeだけが失敗

変更前 helper と新 tests の control は 6 failed / 4 passed / SKIP 0。
旧穴は3種類4 node、regression guardは4項目、preexisting identity再固定＋新policyは2 nodeとして
分離した。全 parameter を旧欠陥数として数えていない。rc、FAILED / SKIPPED node、復元結果を含む
機械可読の正本は `2026-07-29_t146-probe-cleanup-wave/mutation-ledger.json`。

## 検査

計測 checkout は専用 branch `codex/dev-wave-t146-probe-cleanup`。

- focused targeted: 11 passed
- 関連2 test file: 92 passed（変異前後とも green）
- 変異復元後 control: 10 passed
- 並行 main 統合・記録前の repository 全走:
  3683 passed / 18 skipped / rc=0 / 239.72秒
- 記録 commit 後の関連2 test file: 92 passed / 84.16秒
- 記録 commit 後の repository 全走:
  3683 passed / 18 skipped / rc=0 / 237.57秒
- `check_docs.py`: 違反なし
- `check_codex_agents.py`: OK
- integration commit 後 provenance: 501件、違反なし
- 並行 main merge 後 provenance: 530件、違反なし
- 記録 commit 後 provenance: 531件、違反なし

### 段9再開の計算ノード再受入

local main `ff82133365cb8ba3015d82adeeaa741ed68995e5` のT-180 / T-187完了系列を統合した
merge `f2c29ba6aa04f92eb7a30c202ce0d76957c96fe1`を、Pegasus計算ノードで再受入した。

- full suite: request `874117.nqsv`、`bnode114`、32 worker、
  3900 passed / 19 skipped / 214.99秒
- focused + checks: request `874118.nqsv`、`bnode117`、32 worker、
  390 passed / 23.22秒
- startup resume gate、`check_docs.py`、`check_codex_agents.py`、
  `git diff --check main..HEAD`: green
- full-history provenance: 549件、違反なし

merge前preflight `874111.nqsv`は、途中のdiff-check赤を後続greenで上書きするF37同型再発のため
不採用とした。fail-fastへ直した`874113.nqsv`でmessage provenance、docs、Codex agent、
手動解消したworklogのdiff-checkをgreenにしてからmerge commitを作った。

### T-188 land後の段9再開

local main `72e3800b8a388b450de31e742b7920e24360f9da` のT-188共通land契約を統合した
merge `b22288575a731ca26813adab2929c3c114027d7d`をPegasus計算ノードで再受入した。

- merge commit前: request `874196.nqsv`、`bnode065`、32 worker、
  274 passed / 22.90秒、message provenance / docs / Codex agent / staged diff-check green
- repository全走: request `874201.nqsv`、`bnode065`、32 worker、
  3951 passed / 19 skipped / 275.53秒
- focused + checks: request `874202.nqsv`、`bnode067`、32 worker、
  274 passed / 22.76秒
- startup resume gate、`check_docs.py`、`check_codex_agents.py`、
  `git diff --check main..HEAD`: green
- full-history provenance: forward-corrected 1 / 559件、違反なし
- 3 jobともrc=0、PBS会計痕跡あり。wave / focused worktreeは同じ`b222885`でclean

worker 最終応答、親 brief、裁定、pre-fix snapshot hash、変異台帳は
`output/insights/2026-07-29_t146-probe-cleanup-wave/` に置く。
