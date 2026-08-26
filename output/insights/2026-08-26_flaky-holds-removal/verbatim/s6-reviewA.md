## 総括

- 静的レビューのみで、pytest は実行していない。
- must-fix は 4 件。最大 risk は A1 が現 repo の tracked 418 files を理由に全 snapshot caller を決定的に拒否する点。
- A1 の末尾 `/`、rc 三分岐、規則由来候補、`rev-parse --git-path` は正しい。
- ただし tracked-path semantics は訂正前の fail-closed のままで、訂正後裁定に反する。
- B3 は偽 clock 未注入かつ watchdog が 10/60 秒で不統一。
- B2 では summary の異なる cardinality を検査していた防壁が弱くなった。
- 台帳 closure、設計メモ、残余 risk の起票も統合成果物には未反映。

## 1. 裁定との照合

| 項目 | 判定 | 照合結果 |
|---|---|---|
| A1 | 裁定と違う形で実装、劣化 | directory 候補は末尾 `/` 付き。rc=0/1/その他、`check=False`、NUL 部分集合検査を実装。候補生成に `exists`、`rglob`、`listdir` はなく、info/exclude は `rev-parse --git-path` で解決している。一方、tracked descendant を fail-closed にする訂正前 semantics が残る。[output_snapshot_ignores.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/output_snapshot_ignores.py:144) [同:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/output_snapshot_ignores.py:208) |
| A2 | 実装されている | literal の厳密な祖先と wildcard の静的 subtree root を規則候補から導出。対象 tree の列挙や存在判定はなく、contract も作成前後の祖先集合不変を要求する。[output_snapshot_ignores.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/output_snapshot_ignores.py:255) |
| A3 | 実装されている | 一律正規化へ退避せず、祖先集合内の directory だけ size、mtime、ctime を `None` にする。[test_s8b_oracle_driver.py:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_s8b_oracle_driver.py:560) [test_real_repo_serialization.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_real_repo_serialization.py:542) |
| A4 | 実装されている | 3 negative control とも baseline が `runs` 作成前へ移動した。 |
| A5 | 実装されている | 3 file で `runs-visible` が可視であることを検査する。 |
| A6 | 実装されている | 2 file に非祖先 `visible-transient-parent` での作成後削除 control がある。対象が祖先なら先行 assertion 自体が赤になる。[test_s8b_oracle_driver.py:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_s8b_oracle_driver.py:638) |
| A7 | 実装されている | 共通 worker hook source と pluggy harness を接続し、decorator 除去と yield 後移動の両 mutant を構築する。[test_real_repo_serialization.py:3782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_real_repo_serialization.py:3782) |
| B1 | 実装されている | `_FLAKY_TEST_HOLD_ROWS = ()` で 3 hold は撤去済み。[flaky_test_holds.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/flaky_test_holds.py:200) |
| B2 | 裁定と違う形で実装、劣化 | live empty registry への書換えと validator negative control の維持は正しいが、非空 summary を 2 registered / 1 matched / 1 skipped から 1/1/1 に緩和した。 |
| B3 | 裁定と違う形で実装、劣化 | 訂正前の `poll_interval_s=1` のまま。訂正後に要求された thread ごとの `_Clock()` と `sleep=clock.sleep`、watchdog 統一がない。[test_pegasus_dispatch_compute.py:5394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_pegasus_dispatch_compute.py:5394) |

問題なし: A1 の最優先事項である末尾スラッシュと rc 三分岐は、静的には正しく実装されている。

## 2. テスト弱体化の検査

- hold#1 の実体削除に伴い、その live row の 9 field assertion は削除された。対象 row 自体がなくなるため、この削除は B1 と整合する。一般 validator の negative control は全項目残っている。
- 問題は summary test の入力が 2 hold から 1 hold になり、期待値も `2/1/1` から `1/1/1` へ緩和されたこと。`registered_node_count` を matched または skipped count から誤導出する変異が通りうる。所見 3。
- `pytest.mark.xfail`、skip、raises の既存範囲拡大はない。ただし新設 tracked-descendant `raises` は、訂正後の正しい実装を拒否する逆向き control になっている。
- fixture への現行 working-tree hash 注入はない。追加 digest は synthetic row または空 registry の安定値。
- 時刻、pid、実 working-tree hash、可変 absolute path を期待値へ焼き込んだ箇所はない。
- B2 の validator negative control は、parametrize された全受理条件、row key/type、acceptance collection、evidence section、import-time invalid row のいずれも消えていない。

## 3. 新設 control の発火可能性

- A1 rule-source control: 非実在 literal 候補を filesystem 列挙へ戻す、directory の `/` を落とす、negationを無視する、wildcard 祖先を動的化する入力で期待集合が不一致になり赤になる。
- entire-output negative control: `output/` 全体の拒否を外せば `pytest.raises` が成立せず赤になる。
- tracked-descendant control: fail-closed を外すと赤になるが、訂正後裁定ではそれが正しい実装である。control の向きが逆。所見 1。
- A4: `runs` prefix の導出または root ancestor の正規化を外すと、`runs` 作成後の snapshot equality が赤になる。
- A5: component 境界を単純文字列 prefix に緩めると、実在する `runs-visible` 入力で先行 assertion または snapshot 差分が赤になる。
- A6: 全 directory を正規化すると、一時 subtree の削除後は親 metadata も消されて before/after が等しくなり、`after != before` が赤になる。`visible-transient-parent` は祖先集合外であり、恒真ではない。
- A7: decorator 除去では worker hook count が 0、yield 後移動では controller が先になるため、それぞれ明示的に赤になる。
- B2 empty controls: live registry が非空、empty digest が違う、summary が 0/0/0 でない入力で赤になる。

ただし現在は A1 の tracked 418 files による例外が先行するため、ROOT を使う A4/A5/A6 control は目的の assertion まで到達しない。論理上の red input はあるが、現統合状態では防壁として発火不能である。

問題なし: A6 の対象 directory が実は祖先集合に入っている、という恒真化はない。

## 4. B3 の scenario 保存

- `_Scheduler` の状態遷移回数は現変更前後で同じ。`poll_interval_s` は間隔だけを変え、当該 fixture は timeout 分岐へ入らない。通常側は各 scheduler が `QUE -> RUN -> DONE` を辿る。
- 既定 5 秒値、sleep 回数、queue duration を固定する assertion はない。
- 性質 assertion は残っている。1 件目は `results`、qsub 1 回、`submission-disabled.json`。2 件目は `results`、qsub 2 回、`_orphan_hold_present` 不在。
- 問題は real sleep が残り、固定床を 10 秒から短くしただけで消していないこと。訂正裁定の偽 clock seam が未使用。
- `join(10)` と `join(60)` の双方を watchdog と説明しており、訂正裁定が明示した不整合も残る。

問題なし: poll 値の変更そのものによる scheduler command sequence の変更は静的には見当たらない。

## 5. 申告漏れの波及

- 新設 5 node と改名 2 nodeを exact 登録させる meta-test は見つからない。duration ledger は実 collection の 90% coverage 契約であり、全 node の即時登録を要求しない。
- `tools/mutation_harness.py` は registry の `FLAKY_TEST_HOLD_NODE_IDS` を動的に読み、空集合を受理する。撤去した 3 node を expected node に持つ現行 mutation spec も見つからない。
- `tools/check_docs.py` は live hold の nodeid、件数、新設 node の exact inventory を固定していない。
- ledger の旧 `test_registry_is_two_exact_nodes_with_reintroduction_anchors` は既存 stale keyで、子 B が申告済み。
- B3 の `10.0` 秒 entry が古くなる点も子 B が申告済み。最終 B3 修正後の再計測で更新が必要。
- 子 A は tracked 418 files による全 caller の fail-closed を明記し、子 B は docs と ledger を所有外と明記している。指定された meta 面で新たな申告漏れは見つからない。
- 一方、裁定済みの F136/F480 closure、6 段分類手順、残余 `task-runs` risk の新規 task、`p1-stale-hold-detection.md` は現統合成果物にない。これは子の隠れた波及ではないが、親の未完義務である。

## 所見一覧

- **所見 1**: A1 は訂正後裁定に反して tracked descendant を fail-closed にし、現 repo の正当な 418 files で全 snapshot caller を拒否する
  - 場所: [output_snapshot_ignores.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/output_snapshot_ignores.py:208), [test_s8b_oracle_driver.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_s8b_oracle_driver.py:707)
  - 分類: must-fix
  - なぜ問題か: `.gitignore:24` 配下には tracked file が 418 件あり、Git semantics ではそれらと祖先を可視に保つ必要がある。現在は正当状態を検査不能にする。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: hold#2 を戻した受入は snapshot node 群で決定的に赤となり、受入 receipt が発行されない。
  - 確度: high — 裁定訂正が exact path、件数、既観測例外まで示し、静的照会でも 418 件を再確認した。

- **所見 2**: B3 は訂正後の偽 clock 注入と watchdog 統一を実装せず、real sleep と 10/60 秒の不整合を残している
  - 場所: [test_pegasus_dispatch_compute.py:5394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_pegasus_dispatch_compute.py:5394), [同:5462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_pegasus_dispatch_compute.py:5462)
  - 分類: must-fix
  - なぜ問題か: `poll_interval_s=1` は固定床を短縮するだけで消さない。両 join を同じ watchdog と呼びながら上界が 6 倍違う。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 高負荷時の偽赤または長い hang 回収により受入 receipt が失われるか遅延する。
  - 確度: high — call に `clock`/`sleep` がなく、join 値は 10 と 60 のまま。訂正裁定は両点を逐語指定している。

- **所見 3**: B2 は非空 summary の cardinality 分離 control を `2/1/1` から `1/1/1` へ弱めた
  - 場所: [test_flaky_test_holds_contract.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_flaky_test_holds_contract.py:896)
  - 分類: must-fix
  - なぜ問題か: registered、matched、skipped の誤った相互代入を検出できない。live row の代わりに第 2 synthetic row を使えば元の防壁を維持できる。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 将来の複数 hold で summary report の登録件数が誤ってもテストが受理する。
  - 確度: high — base は registered 2、matched/skipped 1、現差分は全値 1 と明示されている。

- **所見 4**: 裁定済みの failure-ledger closure、分類手順、設計メモ、残余 risk task が統合成果物にない
  - 場所: [s4-ruling.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/s4-ruling.md:91), [docs/failures.md:4978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/docs/failures.md:4978), [同:13242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/docs/failures.md:13242)
  - 分類: must-fix
  - なぜ問題か: F480 は依然 hold#1 を負荷依存族として記し、撤去・修理記録と再分類手順がない。要求された設計メモと task も存在しない。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: failure ledger と backlog が誤った原因・未記録の残余 risk を正本として公開する。
  - 確度: high — integrated patch に docs 差分がなく、指定名の設計メモと対応 task も検索で見つからない。

- **所見 5**: info/exclude の contract test は通常 repository しか作らず、linked-worktree path 解決の退行を赤にできない
  - 場所: [test_s8b_oracle_driver.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/test_s8b_oracle_driver.py:652)
  - 分類: backlog
  - なぜ問題か: fixture は `git init` なので、実装を `repo/.git/info/exclude` へ戻しても同じ test が通る。現実装自体は `rev-parse` を正しく使う。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 将来の退行時に linked worktree だけ除外集合または受入結果が変わる。
  - 確度: high — fixture topology と mutant の通過条件をコードだけで確定できる。

- **所見 6**: B3 の duration ledger は変更前の `10.0` 秒を保持している
  - 場所: [acceptance_duration_ledger.json:7663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-flaky-holds-20260826/orchestrator/tests/acceptance_duration_ledger.json:7663)
  - 分類: nit
  - なぜ問題か: 最終的に偽 clock へ移すなら旧 wall time は scheduling cost として不正確になる。子 B はこの波及を申告済み。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: duration 台帳による初期 shard 順序が実コストより過大評価される。
  - 確度: high — ledger の literal 値と B3 の予定修正が直接矛盾する。