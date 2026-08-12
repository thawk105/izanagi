静的レビュー結果は **NO-GO** です。実装本体より、段 4 の変異事前登録と現行 mutation spec の不一致が問題です。pytest・変異実走は行っていないため、kill 結果そのものは未確認です。

## BLOCKER — M1〜M6 の事前登録が現行 mutation spec に保存されていない

裁定は M1〜M6 の 6 件を登録していますが、現行 spec は M1/M2/M3/M5/M6 の 5 件だけです。さらに spec の M5 は、裁定の CLI 統合変異ではなく「消滅済み worktree 登録を再び拒否する」別変異へ置換されています。[s4-adjudication.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s4-adjudication.md:107>)、[mutation-spec.json](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/mutation-spec.json:6>)

| ID | 静的な単独帰属 | 根拠 |
|---|---|---|
| M1 | 成立 | test は prepare 完了後に wrapper を改竄し、直接 `_subprocess_scheduler()` を呼ぶため、prepare 中の publication 検査は先取りしない。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:803>)、[t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:1699>) |
| M2 | 成立 | 入力は staged bytes と宣言 hash を自己整合させているので、宣言 hash 検査は先取りしない。anchor 比較を消した場合だけ通る。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:819>)、[t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:213>) |
| M3 | 成立 | `prepare_group()` 直呼びで、live roots が無ければ最初の `mkdir` へ到達する入力になっている。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:840>) |
| M4 | **不成立** | 裁定の M3 と M4 はどちらも実質「union を caller roots のみにする」同じ変異で、別 case も spec もない。 |
| M5 | **不成立** | 裁定した「別 slot の request path」変異が spec から消失。加えて復元された既存 exact-argv assert と統合テスト冒頭の exact-argv assert が、subprocess 到達前に同じ変異を殺す。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:488>)、[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:905>) |
| M6 | 成立 | 読み取った bytes は元値のまま、同 inode の mtime だけを変更するため、fingerprint 比較だけに帰属する。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:874>)、[t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:182>) |

照準し直し案:

- M3 は「coordinator の live identity を caller config の `approved_git_identity` に戻す」変異と、その identity 自体を偽装する case にする。
- M4 は現在の union→caller-only 変異として残す。
- M5 は裁定どおり戻す。slot-00 を既存 exact-argv assert から除外し、統合テスト自身の `argv == wrapper_argv` も外す。そのうえで別 slot request を実際に実行させ、slot-00 receipt/runtime identity が得られないことだけで赤くする。
- stale-worktree 変異には M5 と別 ID を与える。

親は「M1〜M6 を維持した」および現行 spec に基づく mutation matrix の成立を撤回すべきです。修正前の land は不可です。

## MAJOR — P2 は anchor 正例の発火を証明していない

P1 は `prepared.repository_roots` に live anchor と caller root の双方が残ることを検査しており、union を消せば赤くなるので有効です。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:858>)

P2 は同じテスト末尾で staged bytes が同梱 bytes と同一であることを再比較しているだけです。`publish_wrapper_request()` から `_assert_staged_file_identities()` の呼出しや anchor 比較を消しても緑のままで、正例が検査を通過した証拠になりません。[t810_pbs_wrapper.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_pbs_wrapper.py:341>)、[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:870>)

P2 を独立 test にし、実検査を呼ぶ狭い helper/seam を spy して「byte 同一の入力が anchor 検査を通過した」ことまで固定してください。その helper 呼出し削除を positive mutation として赤にするのが明瞭です。

親は「P1/P2 の正例を維持」を「P1 は成立、P2 は入力 fixture の正当性だけ確認し、gate 発火は未証明」へ修正すべきです。

## MAJOR — 台帳予定文の (1)(2)(4) は修正が必要

### T-922 (1)

「統合経路の成立まで達成」はやや過大です。test は生成された shell script 自体や `coordinate()`、coordinator CLI、qsub/PBS を実行せず、script 最終行を parse して argv を直接 subprocess 実行しています。[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:905>)

書くべき逐語:

> T-922 (1) coordinator artifact → wrapper CLI: coordinator の `prepare_group()` が生成した script の最終 argv から staged wrapper file を直接 subprocess 実行し、`--request` parse、静的 request decode、PBS runtime identity 補完までを統合テストで確認した。`coordinate()` / coordinator CLI、shell script 自体、qsub/PBS、production producer を通る正例は未確認・未達。

### T-922 (2)

「自己整合した任意 wrapper と binary は拒否できない」は事実と逆です。wrapper file の bytes は coordinator 同梱版へ anchor されるため、自己整合していても任意 wrapper bytes は拒否されます。開いているのは自己整合した任意 binary、staged dependency closure、node 読取時点の TOCTOU です。[t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:201>)

書くべき逐語:

> T-922 (2) staged file identity hardening: 部分実施。request publication 時と qsub 直前に wrapper/binary の宣言 digest と live bytes の一致を検査し、wrapper file は coordinator 同梱 `t810_pbs_wrapper.py` の bytes にも束縛した。自己整合した任意 binary、staged package の依存閉包、qsub 後から node 読取までの TOCTOU は拒否できない。

### T-922 (3)

予定文どおりで過大・過小はありません。

> T-922 (3) guard/budget: 未実施。authority と 2 相結線を裁定へ返した。

### T-922 (4)

根幹の主張は正しい一方、差分には消滅済み linked-worktree registration を無視する受理拡大も含まれます。これは台帳から落としてはいけません。[t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:524>)、[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:1024>)

書くべき逐語:

> T-922 (4) repository roots: 実施。coordinator の live Git identity から main・現存 linked-worktree roots を導き、caller roots と和集合にしたため、caller は roots を増やせるが減らせない。付随修正として、登録先が既に消滅した linked-worktree entry は無視し、現存 registration と symlink/不正 registration の拒否は維持した。

## MAJOR — R1〜R6 は裁定材料だが、次作業者向けの実行票ではない

R1 だけは選択肢がありますが着手点がなく、R2〜R6 はほぼ問題記述だけです。[s4-adjudication.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s4-adjudication.md:84>)

最低限、次を補うべきです。

- R1: 既に閉じた wrapper file bytes と、未解決の binary authority・依存閉包を分離する。authority の三択、移行時の既存 prereg digest 再承認要否、着手点 `t810_preregistration.py::_validate_schema()`、`t810_coordinator.py::_assert_staged_file_identities()` を明記。
- R2: 「依存全ファイルの manifest 化」対「staged package を使わず承認済み設置物を実行」の選択肢を置く。着手点は `publish_wrapper_request()`、`build_wrapper_request()`、`_validate_request_artifact_chain()`。
- R3: 「node-local copy/hash 後に実行」対「immutable staging の運用保証」の択一を置く。着手点は `_canonical_job_script()` と wrapper `main()`。
- R4: snapshot provider、submit 後再評価、withdraw、receipt v2 の順序を明記。着手点は `_coordinate_authorized()`、`evaluate_parallel_guard()`、`withdraw_b_group()`、coordinator の `_validate_guard_receipt()`。
- R5: canonical ledger path を policy に置くか、authority-signed receipt に置くかを選択肢化。着手点は `t810_admission_v1.json`、`t810_budget.py::_validate_policy()` / `_external_ledger_path()` / `reserve_budget()`、coordinator の `_validate_budget_receipt()`。
- R6: producer を新設するか、意図的 dormant のまま §9.1 item 1 を未達に固定するかを選ばせる。producer を選ぶ場合は `launch_intent`、guard receipt、budget receipt、validator kwargs、authorization witness の生成責務と `coordinate()` 呼出しを実装範囲として列挙する。

親は「R1〜R6 を実行可能な裁定パッケージとして返した」という主張を避け、「論点一覧。実装票化には上記の択一と着手点が必要」とすべきです。

## MINOR — DW-G05 の成果物影響は「現時点ではゼロ」と明記すべき

T-810 には production producer がなく、prereg loader の launch API も authorization false を拒否します。[s4-adjudication.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s4-adjudication.md:6>)、[t810_preregistration.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/campaign/t810_preregistration.py:798>)

したがって land しても現存する:

- certified 選択結果の値・受理集合
- 材料レポートの proof-chain 参照
- 実試行台帳の予約・測定値・状態

はいずれも変わりません。これは「hardening が無意味」ではなく、「将来 producer が実装・承認された場合の coordinator 受理集合を先に狭めたが、現在の実測成果物へ到達する発火経路はない」という意味です。

潜在経路では、不一致 wrapper/binary、同梱版と異なる wrapper、repo 内 root の偽装、prepare 後の改竄が新たに reject されます。一方、消滅済み worktree 登録を含む入力は新たに受理されます。この両方向を記録してください。

## MINOR — 段 5 の既存 assert 復元自体は完全。ただし M5 の帰属を壊した

段 5 snapshot では slot-00 だけ exact-argv assert が除外されていましたが、現差分では全 slot の `assert argv == slot["wrapper_argv"]` に復元されています。[s5-snapshot.patch](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s5-snapshot.patch:65>)、[test_t810_coordinator.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:488>)

したがって「復元が完全か」への答えは **はい** です。ただし、その復元により裁定 M5 の先取り回避が失われました。[s6-fix.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t922-measure-happypath/s6-fix.md:44>) の「M1〜M6を維持」は撤回が必要です。

## 総括

**NO-GO。BLOCKER 1 件。**

実装述語の M1/M2/M3/M6 は静的には単独帰属が成立しています。しかし現行 mutation spec は M4を欠落させ、裁定 M5 を別変異で上書きし、復元済み assert が M5 を先取りしています。M3/M4 の再分離、裁定 M5 の復元・再照準、P2 の発火証明、台帳文言の修正後に再レビューすべきです。