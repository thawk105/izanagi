## 総括

**NO-GO。must-fix の閉集合は所見 1〜4 です。** 大きな一般化は不要で、既存関数・テスト・文面の局所修正で対応できます。

`author.patch` は `git diff 2ba400087 HEAD` と完全一致しました。read-only で確認し、pytest・変異は実行していません。以下の `ruling.md`、`docs.patch`、`focus-1.log`、`decision-fragment.md` は指定 parent 配下です。

**1 / must-fix / DW-O28 の実行例が必須引数を欠く**

- **根拠:** `docs.patch:15`、`tools/dev_wave_cleanup.py:1398–1407`。子の例は3 option ですが、parser は `--main-worktree` を含む4組を必須とします。wave 本体の例からも同引数が落ちています。main へ cd しても補完されません。
- **削った後の残余リスク:** 説明を縮めても、実行に必要な引数は省けません。
- **提案する差分の骨子:** 両経路に `--main-worktree <MAIN>` を明記。他の説明を縮め、DW-O28・checker literal・synthetic literal・byte assert を同時更新する。現在の **996 bytes と literal 一致は確認済みですが、実行可能性の証明にはなっていません**。

**2 / must-fix / 所有外のコミット済み差分が退避されない**

- **根拠:** `ruling.md:14` は `merge-base(main, HEAD)..HEAD` の所有外差分を退避すると裁定。実装の `tools/dev_wave_cleanup.py:1613–1622` は status と HEAD→worktree/index だけで、その比較起点・所有外差分の収集がありません。`decision-fragment.md:20–21` の説明とも不一致です。
- 正例の `orchestrator/tests/test_dev_wave_cleanup.py:207–215` は **子 HEAD を checkout してから**復元するため、`author-result.md` が証拠に含まれなくても通ります。
- **削った後の残余リスク:** 子 branch は残るので直ちに内容消失とはなりませんが、所有外成果の救出が証拠 dir だけでは完結しません。
- **提案する差分の骨子:** 既存 payload 生成に、merge-base→HEAD の所有外変更の退避を追加する。削除・rename も表現できる形にし、正例へ「所有外コミット差分が証拠にある」assertion を追加。HEAD→worktree の patch を単純に置換すると既存復元契約が壊れるため、そこは維持する。

**3 / must-fix / 新設占有テストの終了処理が焦点走で赤**

- **根拠:** `orchestrator/tests/test_dev_wave_cleanup.py:224–231`、`focus-1.log:37–80`。赤は `terminate()` 後の `wait(timeout=10)` です。ログには占有拒否 assertion の失敗は出ていません。
- **削った後の残余リスク:** sleep＋SIGTERM 依存を外しても、実プロセスによる占有検出は維持できます。
- **提案する差分の骨子:** 既存 `test_real_occupancy_scan_rejects_live_process_cwd`（同ファイル `1218–1236`）の stdin 待機・書込み終了方式を局所的に踏襲し、必要なら終了失敗時の kill/reap を添える。timeout 増量では閉じない。

**4 / must-fix / 運用文書から裁定の必須契約が抜けている**

- **根拠:**
  - `docs.patch:32` は「manifest へ登録」とだけ記し、path・purpose・branch・owned_paths の記載要件がありません。参照先 DW-O28 にも定義がなく、相互参照で終わっています。
  - `ruling.md:14` が要求する **rename の旧新両 path の登録**がありません。
  - `docs.patch:16` の「blob 一致」は、実装 `tools/dev_wave_cleanup.py:1495–1513` の存在・mode・type・OID 比較より弱い表現です。「dirty は退避」も、退避不能状態の拒否を省いています。
  - `docs.patch:17`、`decision-fragment.md:24` の unlock は主体が曖昧です。実装は `1739–1748` のとおり拒否時に unlock せず、負例も非変更を要求します。
  - `ruling.md:13,27` が決定への明記を求めた **同 path・同 branch 再作成の残余リスク**と、mutation 自己登録等の対象外範囲が fragment にありません。
- **削った後の残余リスク:** 詳細を別の短い手順へ移しても、親が完全な manifest を作る責務と世代識別の限界は残ります。
- **提案する差分の骨子:** 登録 field と rename 両端を手順に明記。「tree entry 一致」「退避可能な dirty」とし、不能時は **親が unlock・報告**すると明記する。tool の拒否時非変更は維持。決定へ上記の限界・対象外範囲を短く追記する。

**5 / 削除 / 未使用の Git allowlist 項目**

- **根拠:** `tools/dev_wave_cleanup.py:227` の `("ls-files", "--others", "-z", "--exclude-standard")` に呼出箇所がありません。
- **削った後の残余リスク:** 現実装の機能・被覆は失われません。
- **提案する差分の骨子:** この1項目を削除する。登録 CLI、`--integration-ref`、履歴 pack、子 branch 削除、purpose 列挙、余分な manifest field は追加されておらず、この点は裁定どおりです。

**6 / 縮約 / submodule 走査と不変な統合証明の重複**

- **根拠:** `tools/dev_wave_cleanup.py:1538–1562` は初期化済み gitlink ごとに同じ `submodule status --recursive` を呼び、さらに子 module へ再帰します。`1510–1523` は main 到達判定を同じ呼出し内でも繰り返します。`992` では固定 SHA 間の owned tree 比較も再実行します。
- **削った後の残余リスク:** 固定 SHA の比較結果は変わりませんが、main/branch ref、追加 reflog、index、submodule 実体の変化は引き続き再検査が必要です。
- **提案する差分の骨子:** recursive status は各階層で遅延評価して一度だけ取得。祖先性 A が成立した場合の履歴再判定を省く。admin 再検査では ref 固定・現在の reflog 保存条件を残し、不変な tree 比較の再計算だけを省く。preflight と recheck の実体検査を丸ごと削る案は不採用です。

**7 / 縮約 / テスト数だけを理由とする削減は不要、共有検査の重複は区別する**

- **根拠:** `orchestrator/tests/test_dev_wave_cleanup.py:335–388` の manifest 10例と submodule 5例は、同じ phase でも異なる入力条件です。dirty と ignored は同じ status 判定を通りますが、ignored 例には `--ignored` 欠落を検出する意味があります。
- 子の realpath 例（`289–301`）と admin binding 例（`304–323`）は、既存の `1281–1292`、`1611–1659` と共有検査の被覆が重なります。ただし子経路への接続確認は残ります。
- **削った後の残余リスク:** 新設例を一律削減すると、子経路で共有検査を呼び忘れる回帰を見逃します。
- **提案する差分の骨子:** node 削減を必須にしない。重複分は変異の「新規検出力」に加算せず、追加するなら所見2の未被覆 assertion を優先する。

**8 / nit / m0〜m7 は anchor を固定しないと検出力を評価できない**

- **根拠:** `ruling.md:92–103`、author 報告 `author.md:20`、以下の実装箇所。
- **削った後の残余リスク:** 「全件赤化」という集計だけでは、意図した検査の除去を検出したのか、別の例外で落ちたのか判別できません。
- **提案する差分の骨子:**

| 変異 | 静的評価・妥当な anchor |
|---|---|
| m0 | `1513` の `bool(proof.owned) and not mismatches` → `(bool(proof.owned)) and (not mismatches)`。明確な等価変異。 |
| m1 | `1483` の拒否だけを消すと selected が `None` のまま別例外となり、phase/rc だけの負例が通る可能性。任意 entry を選ぶ変異として固定する必要がある。 |
| m2 | `1514` の統合拒否条件を恒偽化。子固有の未統合負例に対応する。 |
| m3 | `1513` の `bool(proof.owned) and` を削除。空集合負例に対応する。 |
| m4 | `1745` の backup 呼出しが候補。ただし戻り値・証拠 dir 欠落による二次例外で赤化していないか確認する。 |
| m5 | 子経路の `1726` を対象にすれば接続確認。共有 `_assert_unoccupied` 自体を無効化すれば既存占有テストでも落ち、新規検出力ではない。 |
| m6 | `204–205` の realpath 比較だけを弱めても `190–191` の symlink 拒否が残る。新設 symlink 例ではその変異を検出できない。両方を弱めれば既存 unsafe-path 例も検出する。 |
| m7 | `978–979` の binding 比較だけを削っても `976–977` の snapshot 比較が inode 変更を拒否する。共有再検査全体を弱めれば既存 registry 例も検出する。 |

正式 harness 未実走という author の留保は適切です。現資料から「7件すべて新規検出力」とは認定できません。

**9 / nit / fragment の実測対象数と文書縮約の扱い**

- **根拠:** `decision-fragment.md:35–36` は4本すべてについて非祖先・報告だけの不一致を述べますが、`ruling.md:31` は `anc_parent=None` の t2484 を集計から外す裁定です。
- **削った後の残余リスク:** 数を外しても author/fix に限定した観測という根拠は残り、全 producer への一般化はできません。
- **提案する差分の骨子:** 再確認された対象数に直すか、「祖先性を確認できた対象」に限定する。D703／D2148 の置換範囲、stale lock・周期 sweep 禁止の維持、`{{D:slug}}`、`[T-数字]` 不使用は適合。本文に manifest schema 名・rc 表・phase 名・退避ファイル名の混入はありません。frontmatter の spool schema は別物です。
- DW-S05-A は区切り空行込み **860 bytes**。S05-C／S06-B は空白・改行の縮約で意味の変更は見つかりません。ただし S06-B の文字列変更は「不変」という裁定からは形式上の逸脱です。

焦点走の上位15件は次のとおりです（`focus-1.log:83–98`、node 名は接頭辞を省略）。

| 秒 | node |
|---:|---|
| 98.71 | cleanup_collection_positive_control_with_empty_production_exclusions |
| 10.19 | **remove_child_rejects_live_process_cwd** |
| 1.95 | norecursedirs_excludes_generated_hidden_and_vendor_trees |
| 1.34 | explicit_sort_swo_target_still_collects_without_runner_ignore |
| 1.05 | bare_pytest_collection_is_scoped_by_testpaths |
| 0.97 | ini_addopts_narrows_collection_while_runner_gates_stay_blind |
| 0.62 | **remove_child_checks_initialized_submodule[clean]** |
| 0.53 | pytest_ini_norecursedirs_restates_the_installed_pytest_defaults |
| 0.42 | **remove_child_archives_dirty_integrated_author_and_keeps_branch** |
| 0.40 | **remove_child_already_clean_with_receipt** |
| 0.38 | **remove_child_admin_binding_change_is_partial** |
| 0.37 | **remove_child_detached_ancestry_and_empty_backup** |
| 0.32 | conftest_scheduler_attestation_loads_without_xdist |
| 0.32 | **remove_child_checks_initialized_submodule[reflog]** |
| 0.29 | **remove_child_checks_initialized_submodule[ignored]** |

新設 node は終了待ちで失敗した1件を除き、上位でも1秒未満です。ただし新設群の**合計数秒**はこのログから断定できません。

結果は **1 failed・293 passed、103.21秒、skip の報告なし**（`focus-1.log:100–101`）。新設テストの終了処理の赤であり、親 docs 未適用の期待赤ではありません。author の「代替 capture/finalizer による183件直接呼出し PASS」とは実行条件が異なり、正式 pytest の緑へ読み替えられません。ログ自身も受入全走ではないと明記しています。

**NO-GO の閉条件：1＝実行例、2＝所有外差分退避、3＝占有テスト終了処理、4＝必須運用契約の補完。**