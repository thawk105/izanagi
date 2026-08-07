# 段 4 裁定 — [T-503] 第一 slice (使い捨て専有 worktree)

親が段 3 の全所見を real/refuted・採用/不採用・scope 内/外に裁定し、プラン v2 と変異事前登録を確定する。
両レンズは段 5 進行を NO-GO と返した。**親の裁定は「縮小して GO」である。** 理由は本文末尾に書く。

## 0. 段 3 後に親が実測して決着させた事実

| # | 実測 | 結果 | 決着した所見 |
|---|---|---|---|
| M1 | 使い捨て木で受入全走 `python3 tools/run_tests.py -rf` | **6806 passed / 20 skipped** (929.73 s、wall 1229 s)。wave の通常受入値と**一致** | **A-2 は refuted** |
| M2 | 大域 `git worktree prune` を使わず `<common>/worktrees/<name>` だけを `rm -rf` | worktree 登録 9→8、`prunable` 0 件、他 7 worktree と共有 submodule は無傷 | **A-4 / B-8 に対案が成立** |
| M3 | probe の rc を pipefail 付きで測り直し | `add_rc=0` / `submodule_rc=0` / `fullsuite_rc=0` / `harness_plan_only_rc=0` (pipe 無しで直接取得) | **A-8 / B-13 は real、是正済み** |
| M4 | `output/pegasus-dispatch` を repo 外への symlink にして dispatch | evidence は外部へ出て teardown 後も残る (8 file)。**ただし symlink 自体が clean gate に 1 行として映る** (`.gitignore` の `output/pegasus-dispatch/` は末尾スラッシュ付きで directory しか一致しない) | **B-5 の symlink 案は不採用**、rename 退避案を採る |

M1 は本 slice の中心的前提だったので、これで「使い捨て木で測ると結果が変わる」という筋は
実測で閉じた。M2 は blocker A-4/B-8 を設計変更で消す。

## 1. 所見の裁定

### real かつ採用 (scope 内 / 実装に反映する)

| 所見 | 裁定と対応 |
|---|---|
| **A-4 / B-8** 大域 prune は共有 `.git` 全体への mutation | **real・採用。** `git worktree prune` を使わない。teardown は「自 container を `rm -rf` → 自分の admin dir (`git -C <container> rev-parse --absolute-git-dir` で取得し、`<common>/worktrees/` 配下かつ `gitdir` file が自 container を指すことを確認) だけを `rm -rf`」とする。M2 で成立を実測済み |
| **A-5 / B-1** scratch が違えば harness の lock が分裂し同じ台帳を後勝ち上書きできる | **real・採用。(P1) は誤りだった。** wrapper は provision の前に `--out` の**絶対 path から導いた lock file** へ `flock(LOCK_EX\|LOCK_NB)` を取り、取得できなければ即停止する。論理 run の単一走行を producer scope へ戻す |
| **B-5** dispatch evidence が木と一緒に消え、完走後の台帳が自己検証不能 | **real・採用 (実装は変更)。** symlink 案は M4 で不採用。**完走時のみ** `<container>/output/pegasus-dispatch` を `<out>.dispatch-evidence/` へ rename 退避し、旧 path→新 path を wrapper receipt に記録する。**未完了時は木を破棄せず保持**し、exact な resume コマンドを stderr へ出す (絶対 path が生きたまま resume できる) |
| **A-10** 「終了時に必ず破棄」は SIGKILL 残骸の記述と矛盾 | **real・採用。** 破棄条件を「完走 (ledger が terminal) または `--plan-only`」に限定する。未完了は保持。docs・test 名・worklog の文言も「正常・例外・SIGINT・SIGTERM で共有木を触らない」までに限定する |
| **A-3** orphan runner が同じ固定 path の別 incarnation を汚染しうる | **real・部分採用。** 既存 container は**拒否**し (自動削除しない)、未完了 container は保持するので、同じ path に別 incarnation は作られない。これで再汚染筋は閉じる。scheduler terminal 証明までは作らない (V-3 の発火面は後続 slice) |
| **B-7** lexical path の `mkdir` は所有 identity ではない | **real・部分採用。** `mkdir(exist_ok=False)` で所有し、**既存 container は一切削除しない**ため誤削除面が無い。inode 束縛 teardown と自動 stale 削除は**作らない** (段 2 プランの `DW-G04` 拒否を支持) |
| **A-6** `--commit` が自己選択で anchor に束縛されない | **real・縮小採用。** 既定を source worktree の HEAD とし、解決した full SHA を receipt と stderr に残す。段 4 anchor への機械束縛は、対応する既存 artifact/計測 ID が無いため `DW-G04` により作らない |
| **B-4** outer wrapper の identity が台帳に無い | **real・縮小採用。** wrapper は `<out>.wrapper-receipt.json` に自身の sha256・解決 commit・container path・scratch root・lock path・child rc・evidence 退避先を書く。**台帳 (`--out`) 自体は触らない** (harness 無改変を守る) |
| **A-9** MW-05/MW-07/MW-09 が単一理由でない | **real・採用。** 事前登録から除外し、§3 の登録表へ差し替える |
| **B-12** 旧禁止 (変異中の受入・tree 書込) と新許可が併存する | **real・採用。** 本 slice は**並行許可を出さない**。`DW-M05` に「wrapper 経由でも source/main は observation-only、変異走行中の受入全走・tree 書込の禁止は維持」と明記する。緩和は専用 probe 後の別裁定とする |
| **B-3** §9.1 の充足は 0/6 | **real・採用。** docs と worklog に「本 slice は §9.1 の 1〜6 のいずれも充足しない。共有 checkout に対しては使い捨て木で回避を試みるが、転換の充足ではない」と exact に書く。`T-503 complete` / D130 条件 3 `closed` / T-486 `closed` とは書かない |
| **B-6** SIGKILL 後の人間待ちは消えず外へ移っただけ | **real・採用 (文言)。** 「共有 checkout の汚染は消えるが、campaign の自己再開は未達」と書く。ただし未完了 container 保持により、**同じ scratch root での resume は可能**になった (段 2 プランの前提より改善) |
| **A-1 / B-11** status-only の対照走行は不十分・高コスト | **real・採用 (置換)。(P4) を修正する。** 12 変異 × 2 経路をやめ、次の 3 点に置換する。① fake inner harness で argv/env/cwd/stream/child rc を exact 比較する透明性テスト、② real git fixture + **実 harness** + `--runner-mode local` + 極小 spec の E2E を**テスト内**で 1 本、③ 退避済み evidence に対する `--resume --plan-only` の再検証テスト。さらに M1 (全走 6806/20 一致) を同値性の実測証拠として使う |
| **B-9** namespace churn と stale の線形成長 | **real・should・採用 (文言)。** 自動 GC を作らない以上、`DW-M05` に「完走した wave は container が自動で消える。未完了で残した container は resume か手動削除で閉じる」と運用注記を書く。8 並行の burst probe は行わない (本 slice は同時 1 本しか使わない) |

### real だが本 slice の scope 外 → 裁定パッケージでユーザーへ返す

| 所見 | 理由 |
|---|---|
| **A-7 / B-2** 機械 admission が無いので prose-only。旧 direct 経路が残る | **(P3) を反対採用。** `DW-M05` に「必須」と書かない。harness 側 admission + legacy drain は U-8 の activation gate 一式であり、harness 改変 (U-10 解除) と consumer 停止を含む。**本 slice の外**。裁定パッケージ V-7 として返す |
| **B-10** 新規 `tools/` script の実行場所分類が未実施。分類はユーザー手番 | **real。**本 wave は wrapper を**ログインノードで走らせない** — E2E は tests 内 (dispatch 済み計算ノード) で行うため本 slice は進行できる。将来の実運用のため、分類依頼を裁定パッケージ V-8 として返す |
| **A-3 の残り** scheduler terminal 証明 / V-3 exclusive lease | in-place 復元経路を作る後続 slice で発火。放棄ではない |
| **V-4 / V-5** `clean` capability・metadata admission | 本 slice に arm も `clean` も復元も無いため発火面が無い。放棄ではない |

### refuted

| 所見 | 理由 |
|---|---|
| **A-2** 64 passed からの一般化は破れる | **refuted。** M1 で使い捨て木の全走が 6806 passed / 20 skipped、wave 通常値と一致した。A-2 が名指しした `test_s8b_protocol_builder.py` / `test_real_repo_serialization.py` / `test_check_wave_startup.py` も全走に含まれる |
| **A-1 の一部** 「receipt の `manifest_repo_root` が違うのに両方 pass する」 | 主張自体は real だが、**それは欠陥ではない** — 使い捨て木は別 path なのだから identity field が違うのは正しい挙動である。所見の実体は「対照走行の比較射影が粗い」であり、そちらは A-1/B-11 として採用した |

## 2. プラン v2 (段 5 の実装契約)

`tools/mutation_worktree.py` を新設する。`tools/mutation_harness.py` は **1 byte も変更しない**。

1. **CLI** — 段 2 プランの契約を採る。ただし `--commit` 既定は source worktree の HEAD。
2. **lock (新規・A-5)** — provision 前に `--out` の絶対 path から導いた lock file へ
   `flock(LOCK_EX|LOCK_NB)`。取得不能は即停止 (rc=125)。以後 process 終了まで保持。
3. **preflight** — 段 2 プランの署名を採る。`scratch root` は全 registered worktree の外、
   非 symlink、書込可。`spec` / `out` は registered worktree と生成 container の外。
   container は `mkdir(exist_ok=False)` で所有し、**既存なら拒否して何も消さない**。
4. **provision** — `git worktree add --detach <container>/repo <full-sha>` →
   `submodule update --init --no-fetch -- external/ccbench` → HEAD 一致 → porcelain 空 →
   submodule 初期化済みを再検査。
5. **harness 起動** — cwd = container、`--repo <container>`、runner argv は無改変で透過、
   stdout/stderr は親へ継承、`GIT_*` の repository 選択変数は継承しない。
6. **teardown (改)** — 完走 (child が terminal rc を返した) または `--plan-only` のときだけ:
   evidence を `<out>.dispatch-evidence/` へ rename → container を `rm -rf` →
   **自分の admin dir だけを `rm -rf`** (大域 prune は使わない)。
   未完了 (例外・SIGINT・SIGTERM・child 異常終了) では **container を保持**し、
   exact な resume コマンドを stderr へ出す。`git worktree remove` と `submodule deinit` は
   command allowlist に存在させない。
7. **共有木の事後検査** — provision 前と teardown 後に source / main の
   `status --porcelain=v1 --untracked-files=all --ignore-submodules=none` と
   `submodule status` の stdout bytes を比較し、差があれば rc=125。
8. **receipt (新規・B-4)** — `<out>.wrapper-receipt.json` に wrapper sha256・解決 commit・
   container・scratch・lock path・child rc・evidence 退避先・共有木 snapshot の一致可否を書く。
9. **自動 stale 掃除は作らない** (`DW-G04`)。既存 container は拒否し、手動手順を stderr に出す。

テストは段 2 プランの一覧から、実装しない機能 (自動 stale 掃除・inode 束縛削除) 向けを落とし、
lock・evidence 退避・条件付き teardown・範囲限定 admin 削除・receipt・透明性・E2E を足す。
**すべてのテスト名と docstring に「共有木の観測点間 bytes 不変だけを主張し、物理永続性は
主張しない」限定を残す。**

## 3. 変異事前登録 (`DW-M01`)

A-9 の指摘を反映し、前後層に mask されるものを除外した。各件は「無効化すると赤になる理由が
一つに絞れる」ことを実装後に `DW-M04` / `DW-M07` で再確認する。

| ID | 無効化する述語 | 赤になるテスト | 単一理由性の根拠 |
|---|---|---|---|
| MW-01 | source が worktree root そのもの | `test_source_must_be_the_exact_worktree_root` | harness は生成後の `--repo` しか見ず source を知らない |
| MW-02 | scratch が全 registered worktree の外 | `test_scratch_inside_any_registered_worktree_is_rejected` | git は nested worktree を作れる。後段に拒否層が無い |
| MW-03 | scratch leaf が非 symlink | `test_scratch_symlink_is_rejected` | resolve 先が正常なら git も harness も拒否しない |
| MW-04 | container を `exist_ok=False` で所有し既存を拒否 | `test_existing_container_is_preserved_and_never_claimed` | 既存 sentinel の誤削除は他層が検出しない |
| MW-05 | `--out` 由来 lock の取得 | `test_same_out_from_different_scratch_is_rejected` | harness の lock は生成 repo path 由来なので**分裂する** = 後段に排他が無い |
| MW-06 | post-provision の `HEAD == 要求 commit` | `test_post_provision_rejects_head_mismatch` | harness は生成木の実 HEAD へ自己束縛するだけで要求値を知らない |
| MW-07 | admin dir 削除を自分の 1 件に限定 (大域 prune にしない) | `test_teardown_removes_only_own_admin_dir` | 他 worktree の admin 消失を検出する層は他に無い |
| MW-08 | evidence 退避を container 削除より前に行う | `test_dispatch_evidence_is_relocated_before_delete` | 削除後に evidence を回収する層は無い |
| MW-09 | 未完了時は container を保持する | `test_incomplete_run_keeps_container_for_resume` | 保持しないと resume 不能になるが、他層は気づかない |
| MW-10 | child rc の透過 | `test_child_return_code_is_propagated` | rc の後段 consumer は wrapper だけ |
| MW-11 | teardown 失敗を rc=125 で上書き | `test_teardown_failure_overrides_child_rc` | cleanup 赤を child 成功として返す経路を止める層は他に無い |
| MW-12 | signal を active child へ転送 | `test_sigint_and_sigterm_are_forwarded` | wrapper PID への signal は独立 session の child へ伝播しない |
| MW-13 | spec / out が registered worktree の外 | `test_spec_and_out_inside_registered_worktree_are_rejected` | harness は生成 repo 外なら source 内 spec を受理する |
| MW-14 | 共有木 snapshot の事後 exact 比較 | `test_shared_tree_drift_fails_closed` | harness は source/main への別変更を検査しない |

## 4. 「縮小して GO」の理由

両レンズの NO-GO は、主として (a) 大域 prune、(b) lock 分裂、(c) evidence 消失、
(d) prose-only の必須化、(e) §9.1 を満たしたと読める文言、に向いていた。
(a)(b)(c) は本裁定で設計を変えて閉じ、(d)(e) は**主張を縮める**ことで閉じた。
残る blocker (機械 admission、legacy drain、実行場所分類) は、いずれも
**harness 改変または人間手番を要する層**であり、`DW-G05` の意味で本 slice の成果物影響とは独立に
成立する。したがって本 slice を止める理由にはならない。

`DW-G05` の成果物影響 (縮めた版): 本 slice を実装しないと、wrapper 経由で走らせる選択肢自体が
存在せず、変異本走は常に wave worktree の tracked bytes を in-place で書き換える。SIGKILL 残留は
`_assert_clean_tracked` の阻止で人間待ちの停止を作り、走行中の並行 consumer は汚染木を測って
偽の赤/緑を変異台帳 (`status` / `failed_nodes`) と worklog へ載せる。実装すると、
**wrapper 経由で走らせた wave に限り**この 2 経路が消える。全 wave へ及ぼすには V-7 の
activation package が要る。

## 5. ユーザーへ返す裁定パッケージ (scope 外の real 所見)

| # | 軸 | 選択肢 | 親の推奨 |
|---|---|---|---|
| V-7 | 旧 direct 経路の閉じ方 | (a) harness に isolation admission を足し (U-10 解除)、legacy drain receipt と consumer 拒否まで含む activation package を次 slice で作る / (b) prose-only の既定手段のままにし、direct 経路を許し続ける / (c) 本 slice を shadow prototype と位置づけ、活性化は L-B の実機受入まで凍結する | **(a)**。ただし独立 wave とする。本 slice は (c) の位置づけで land する |
| V-8 | `tools/mutation_worktree.py` の実行場所分類 | (a) ユーザー端末で cgroup charged memory を実測して `local-ok` / `dispatch-required` を確定する / (b) 測らず `unknown` = dispatch-required のまま運用する | **(a)**。(b) だと wave ごとに計算ノード確保が要り、運用が重い。ただし測るまでは (b) で安全側に倒す |
| V-9 | 未完了 container の retention | (a) 手動削除のみ (本 slice の実装) / (b) 次 slice で owner record + exclusive lock による自動 GC を作る | **(a)**。実残骸 path を観測してから (b) を設計する (`DW-G04`) |
