# T-2008 — D1163 closure mismatch gate 撤去の実装・検証

- authority: none
- default_effect: no-state-change
- task: [T-2008]
- implementation anchor: `20bdef0b8d5dc6b19b7a7ece34b73cf3204f7ade`
- diagnostic-order fix: `cbae5f2963f4a43ace707290396fc9e50a346237`
- historical-consumer fix: `c4fb9ad4461a66eb965b89923038714239d1c52d`
- accepted intermediate tip: `79532ab38adc8e05660db4e8436f84a6201e45c5`

## 結果

D1163 の指定どおり、`CERTIFIED_ACCEPTANCE` で recorded closure と current closure の
blob map が不一致なだけで `recorded-current-closure-mismatch` を上げる 1 条件を撤去した。
`current-closure-unavailable`、recorded commit blob/digest、purpose 必須、certified/historical view 型、
reason enum、recorded blob map は維持した。

Historical view は `verifier_assessment_basis=recorded-at-original-verifier-epoch` を持つ。
Layer3、P2-2 summary、critic/online digest、backoff figure provenance、S1 9-pair provenance まで投影し、
certifying report への marker 混入は拒否する。過去の marker 無し Layer3 v3 と generation-time
generator SHA は現行 code と違うだけで無効化しない。

## 敵対レビューと fix

- 段3 consultation 2本は、historical consumer 取り残し、schema の certified marker 混入、
  persisted WAL 共通 certification の既存限界、public token の既存限界を指摘した。
- 段6 review 2本と焦点再レビューは、P2-2 summary 脱落、過去 figure の current-SHA 偽拒否、
  S1 最終 serializer 脱落、`WorkloadDigest` positional 互換、Layer3 診断順位を fix した。
- 中間受入の初回赤 14 node から、`autonomous_trial_completeness` の旧5-key/新6-key epoch 互換と
  backoff test double の marker 欠落を発見し、fix4 で閉じた。焦点再レビューは追加 must-fix 0。

逐語成果は `verbatim/` に凍結した。

`git diff --check` の契約に合わせ、次の原文は可視文字を不変のまま、行末の U+0020 2 byte だけを列挙行から除いた。

- `s3-lens-a.md`: 原文 SHA-256 `5c6ce6cb9c573016050bddf30e37c9823fe4efad8322b80b5486de0cc8c79219`、
  12891 bytes、原文 108〜111 行の各 2 spaces (合計 8 bytes)。
- `s3-lens-b.md`: 原文 SHA-256 `b806542de36c09d3062648680a7dd9f924b025ff67001bdfd375b08fa5e66dba`、
  17054 bytes、原文 212〜215 行の各 2 spaces (合計 8 bytes)。
- `s6-fix1.md`: 原文 SHA-256 `9cbb0d868e3e12044ad893a8b04b1f22e96355473ee7eadc0eefcd4e109650f3`、
  4129 bytes、原文 11 行の 2 spaces。

復元は列挙行の newline 直前へ ASCII space 2 byte を追加する。原文は repo 外 wave job directory に同 hash で保全している。

## 検査

- 変更 test module 7本の単独走: `117 + 25 + 13 + 138 + 157 + 16 + 27 = 493 passed`。
- D1163 の撤去対象外束縛: 36 passed。recorded blob、preregistration、freeze、
  trace/operation、live meaning compatibility、legacy reason reader を含む。
- fix4 焦点走: backoff 12 passed、autonomous completeness 257 passed、trial/workload 3 passed。
- `python3 tools/check_codex_agents.py`: 0 native / 13 static dormant / runtime blocked の正本と一致。
- `python3 tools/check_docs.py`: 違反 0。
- commit 前後・main merge 後の provenance: rc=0、新規違反 0。既知履歴 54 件は出力上分離。
- fix4 後中間受入: `18306 passed / 61 skipped`、red 0、flake 0、
  `effective_scheduler=loadgroup`。receipt は repo 外の
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/acceptance-intermediate-4.json`。

Dirty integration での `test_critic.py` 44赤は、意図的に維持した `current-closure-unavailable` が
HEAD/disk 不一致を検出したもので、clean implementation commit 上の再走は 138 passed。

## 変異 matrix

Fixed commit `cbae5f2963f4a43ace707290396fc9e50a346237` に対し、各 spec の baseline を独立に実走した。

| mutation | baseline | verdict | failed node |
|---|---|---|---:|
| recorded/current map 比較の復活 | PASSED | KILLED | 8 |
| historical basis literal 改竄 | PASSED | KILLED | 1 |
| Layer3 historical marker 脱落 | PASSED | KILLED | 1 |
| certified marker schema 禁止の無効化 | PASSED | KILLED | 1 |
| recorded commit blob 束縛の迂回 | PASSED | KILLED | 24 |
| freeze closure SHA 束縛の迂回 | PASSED | KILLED | 1 |
| verifier operation 束縛の迂回 | PASSED | KILLED | 1 |
| live resolver の historical 化 | PASSED | KILLED | 1 |

`SURVIVED=0 / MISMATCH=0 / TIMEOUT=0`。各結果と attempt receipt は repo 外の wave job directory に保全し、
repo 内の clean-scan を mutation 失敗文で汚染しない。repo 内挙動 test は事故的退行を検出するが、
gate と test を同一主体が改変できる限り、意図的共謀改変の完全防壁ではない (D387)。

## scope 外の裁定パッケージ

1. `current-closure-unavailable` も撤去するか。規律 7 との整合では撤去推奨だが、D1163 の exact scope 外。
2. persisted WAL の verdict/receipt を全 certified consumer の共通 admission 層で束縛するか。
3. `_CERTIFIED_VIEW_TOKEN` の module-private 限界を外部 capability へ移すか。
4. D956/D967 を後継決定で明示 supersede するか。今回は改訂していない。

## dev-wave 改善候補

- 共有 Git の active wave worktree を `mutation_worktree.py --source-repo` にした plan-only は、
  並行 land で local main が進むと共有木不変検査が rc=125 で正常停止する。
  今回は共通 Git 管理外の fixed clone + linked worktree + local submodule URL で安全に再開した。
  clone の primary worktree を `dev_wave_submodule_init.py` が受理しないなど細部があるため、
  手順の自動統合は別 wave 候補とする。
- 元 Claude session の `EnterWorktree({name})` 後に persistent shell cwd が共有 checkout に残り、
  Bash が全拒否になった件は実測済み。同 path の `EnterWorktree({path})` 再実行で復旧した。
  Codex 共通手順にそのまま追加せず、Claude 固有 surface の改善候補とする。
