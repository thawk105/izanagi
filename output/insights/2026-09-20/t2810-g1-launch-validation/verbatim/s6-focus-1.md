## 所見対応表 (所見 / 判定 closed|partial|regressed / 根拠)

対象は HEAD `083a45ee9`。以下、行番号は現 HEAD 基準。略号は次を指します。

- [F: production](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2810-g1-launch-validation/orchestrator/campaign/s8b_ratified_freeze.py)
- [T: verify test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2810-g1-launch-validation/orchestrator/tests/test_s8b_ratified_verify.py)
- [B: production emitter fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2810-g1-launch-validation/orchestrator/tests/test_s8b_ratified_freeze.py)
- [O: oracle test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2810-g1-launch-validation/orchestrator/tests/test_s8b_oracle_driver.py)

| 所見 | 判定 | 根拠 |
|---|---|---|
| RA-1: M12 の集計別枠 | partial | `s4-addendum-1.md:38` で拒否段階 / cause の契約検出として別枠化済み。F:3129 の後段拒否は残り、実装子の直接確認でも block 除去後は `scan-exemption-invalid / active-chain-mismatch`。正式 matrix の集計への反映は本レビュー外。 |
| RA-2 = RB-3: docstring | closed | fix1 が F:2071 に6行追加。「記録内の整合情報であり PBS job の外部認証ではない」を明記。 |
| RB-1: 試験縮約は任意 | closed | 維持で問題なし。T:2972、2988、2995 の直積試験は不変。fix1 / fix2 に test 差分なし。 |
| RB-2: 関数数・AST 比較条件 | partial | 再計算で新規 test 17 関数 + helper 5 関数。追加引数と option 分岐を default 側へ戻した AST は、docstring 込みでは不一致、除外すれば一致。技術的照合は完了。親の集約記録への反映は未確認。 |
| RB-4: comment 維持 | closed | O:131 の policy epoch、追随経緯、live 拒否、historical 到達点の comment を維持。裁定どおり。 |
| 追補1: 焦点走1の赤への fix2 | closed | F:3633 で G の追加 path から選択。T:1729 の既存 test は無変更。焦点走2は対象ファイルを含み、集計上0 failed。個別 PASSED の証拠限界は後述。 |

regressed と判定する所見はありません。

## fix2 の受理集合の照合 (追補 1 の各項と file:line)

**追補1に対する裁定外の変更は確認しませんでした。** fix2 は F:3631 の世代文書選択 block だけを変更しています。以下の受理は、他の既存 gate が成立することを前提とします。

| 追補1の項目 | 照合結果・根拠 |
|---|---|
| G が追加した `_GEN_RE` 一致 path がちょうど1個 | F:88 の正規表現、F:3633 の `_added_paths`、F:3635 の個数検査で成立。G が他の非世代ファイルも追加することは禁じない。 |
| 選択 path の H 内導入集合が `{G}` | F:3641 で H の oid、F:3642 で全到達履歴の導入集合を取得し、F:3643 で比較。resolver の結果に依存しない。 |
| `generation_number` と path 内番号を照合しない | 新 block に番号比較なし。段階2の scope 拒否は F:3273、段階7の active chain 比較は F:3129 に残る。 |
| 現物 g1 の受理 | `32ba8cae4` に helper と同じ diff-tree を実行し、追加が `output/s8b-freeze/holdout_freeze.v2.g1.json` だけであることを確認。導入集合検査も通れば受理。fix2 後の実 repo 全経路再実測は親に残る。 |
| 独立 fixture の default / option の受理 | T:647 は option 時に C を確定し、T:662 で g1 文書を書いて T:664 で G を作る。どちらも G が追加する世代文書は1個。 |
| production emitter の g1 / g2 chain | g1 は B:1326、1339、g2 は B:1535、1554 で自世代の文書を G に追加。他の artifact の追加・旧 artifact の削除は世代文書の個数を増やさない。 |
| wrong_g=A の拒否 | 独立 fixture の A は T:671、production emitter の A は B:1345 で approval record のみ追加。`_GEN_RE` 一致は0個となり、F:3635 で `binding-chain-mismatch / generation-introduction`。既存期待は T:3154、新負例は T:3109 に維持。 |
| 世代文書を追加しない commit | 一致0個で同じ拒否。F:3635。 |
| 世代文書2個以上の同時追加 | 一致個数が1でないため同じ拒否。F:3635。 |
| 削除後、同一 bytes で再作成 | F:518 が元の導入と再導入をともに列挙し、F:3643 の `{G}` 比較で拒否。 |
| 過去に異なる bytes が存在 | F:509 で `history-mutated`。既存の履歴不変条件を維持。 |

**merge G の前提は、実際の Git 挙動と一致しました。** 既存 merge `ee00b2db4ab215e96b63e8dd19c718bbddae81e3` に、F:684 と同じ

`git diff-tree --no-commit-id --no-renames --name-status -r <merge>`

を実行すると出力は **0 bytes**。比較用の `-m` 付きでは16行でした。したがって、この helper の呼出しでは追加集合が空となり、新 block に達すれば0個として拒否されます。

**scope 射影と `dedicated` に矛盾はありません。** T:1741 は `generation_number=1`、`generation_commit=g2.G` を作り、T:1747 の resolver 射影も世代番号だけを変更します。段階6は g2.G が追加した g2.json を選ぶため、g1.json の導入を g2.G に要求しません。

段階3の `dedicated` に入る g1.json は、F:3314 の measurement closure との role 衝突検査と F:3318 の要素数検査に使われます。`dedicated` 全体を読み込む処理ではなく、実際の capture 対象は別の `bound_paths` (F:3321) です。さらに `FREEZE_DIR` 配下は一律に measurement closure から除外されるため、g2.json も衝突防止の対象です。

なお、通常の g2 は引き続き F:3273 で拒否されます。射影 fixture の成功を、通常の g2 launch 解禁とは解釈できません。

## 焦点走の読み方と派生値の照合

| 項目 | 原データからの確認 | 判定 |
|---|---|---|
| 焦点走1 | `focus-impl-1.log:90` に対象 node の FAILED、`:91` に **974 passed / 13 skipped / 1 failed / 249.79 s** | 一致 |
| 焦点走2 | `focus-fix2-1.log:17` に **1876 passed / 13 skipped / 245.64 s**、`:10` に child rc=0 | 0 failed と整合 |
| fix1 | 提供 diff の追加・削除行を再計数し **+6 / −0** | 一致 |
| fix2 | 同じく **+10 / −1** | 一致 |
| 統合 production | `git show --numstat dc5b0f39b` で **+99 / −10** | 一致 |
| 統合 verify test | 同じく **+309 / −3** | 一致 |
| 統合 oracle test | 同じく **+7 / −5** | 一致 |

fix1 / fix2 の提供 diff は、それぞれ該当 commit の `git show --format=` と byte 一致しました。`git diff --check 800178b39 083a45ee9` も成功しています。

対象ファイルは、ログが参照する dispatch directory の `request.json` の `args` から再計数しました。

- 焦点走1: `f080ea85a5a7ce6a3e12ecda18ffef75`、10ファイル。
- 焦点走2: `80dba361d107e238c04719b113303c9c`、17ファイル。
- **集合として10ファイル全部を17ファイルが包含**。両方とも選択オプションは `-q -rf`。
- 追加7ファイルは `test_official_perf_closure.py`、`test_pegasus_floor_tools.py`、`test_s8b_holdout_admission.py`、`test_s8b_oracle_judge.py`、`test_s8b_oracle_report.py`、`test_s8b_verdict.py`、`test_t080_freeze_migration.py`。

集計総数は **988 → 1889、増分901**。passed の増分は902で、旧失敗1件の解消と追加901件の成功という説明と整合します。ただし、集計だけでは skip の内訳まで同一とは証明できません。

したがって `test_generation_two_rejected_before_artifact_io` は、**対象に含まれ、再度 FAILED になっていないことは確認でき、修復を支持する**と評価します。ログには当該 node の個別 PASSED 表示がなく、焦点走2の転記には6403 bytesの省略もあるため、「個別 PASSED 行を確認した」とは記録しません。

実装子報告も、[実行 events 原データ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/codex/dev-wave-t2810-g1-launch-validation/t2810-s6-fix2/attempt-0001.events.jsonl) と照合しました。

| 報告 | 原データ |
|---|---|
| 指定走10 passed / 1 failed | events:20 に **1 failed, 10 passed, 241 deselected in 32.37s**、exit=1 |
| g2 個別走の失敗 | events:24 に **1 failed in 2.18s**、exit=1 |
| sealed fixture の環境制約 | 上記両出力に `PermissionError: [Errno 1] Operation not permitted` |
| meta-test 6 passed | events:26 に **6 passed in 2.09s**、exit=0 |
| 直接確認 | events:31、exit=0。`DIRECT_CALL_PASS`、通常の wrong_g 拒否、新 block 除去後の段階7拒否を確認 |

報告表の成功数も **4 + 3 + 2 + 1 = 10** で一致します。実装子の環境制約による失敗と、親の計算ノードでの焦点走2は分けて記録する必要があります。

`git log --format=%B -3` では、fix1 `0d943f9cb`、fix2 `083a45ee9` の双方に次の trailer を確認しました。

`AI-Agent: product=codex; model=gpt-6-astra; reasoning=medium; role=author`

これは trailer の存在確認であり、全史 provenance 監査の代替ではありません。

## 新しい所見 (あれば、番号 RF-1, …、分類 must-fix|should|nit)

新規の must-fix / should / nit はありません。個別 PASSED の未表示と正式 matrix 未確認は、上記の証拠範囲として扱います。

## 判定 (GO / NO-GO と条件)

**GO — fix 後の静的な焦点再レビューとして。**

親の完了記録では、M12 を独立拒否能力の集計から分離し、RB-2 の関数数・AST 比較条件を正確に反映してください。正式 matrix、held 診断走、fix2 後の実 repo 再実測、裁定所定の受入検証は、この GO では代替しません。

## 総括

fix1 / fix2 は指定範囲に収まり、追補1の受理・拒否条件と整合します。差分行数、焦点走の集計、実装子の数値、trailer は原データと一致しました。残る partial は親の集計・記録の確認であり、実装修正を要する退行は見つかりませんでした。