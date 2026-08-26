## 総括

- 判定は条件付き NO-GO。`output/runs/` 不在による元の決定的な赤は、プランどおりなら解消する。
- ただし wildcard 規則は引き続き実在 path から得るため、除外集合自体の状態依存が残る。
- exclude source の列挙、`git check-ignore` の rc、NUL 出力処理が未規定で、実装前に契約化が必要。
- `output/task-runs/` は Git-visible のままであり、並行 shard による F136 型の偽赤は残る。
- `.codex/worktrees/` と `.claude/worktrees/` は `output/` の外なので、snapshot へ混ざる経路はない。
- pytest、焦点走、受入全走は実行していない。以下は静的読解と read-only Git 状態照会による結論である。

## 1. 新しい導出の状態依存

`output/runs/` については改善される。プランは repository root `.gitignore` の規則 bytes から literal directory 候補を作り、directory の実在を候補生成に使わないとしている。現行規則は `.gitignore:18` の `output/runs/` なので、fresh worktree でも候補になる。さらに最終判定を Git に戻すため、列挙済み候補については negation の最終結果も Git が決める。

一方、除外集合全体は規則由来にならない。

- `s2-plan.md:76-78` は現行 `git ls-files` との和集合を残し、`.gitignore:19` の `output/variants/*/bin/` は実在後にだけ追加すると明記している。したがって同じ commit でも、実在する ignored path により返り値が変わる。
- この helper は実 repository から得た prefix を任意の `tmp_path` にも適用する。例えば temp tree に `variants/x/bin/` があって実 `output/` には無い場合と、別 shard が実 `output/variants/x/bin/` を作った後とで、同じ temp tree の snapshot 結果が変わりうる。`s2-plan.md:80-89` の `runs` 専用 contract はこの経路を検出しない。
- `**`、末尾スラッシュなしの directory 候補、nested `.gitignore`、`.git/info/exclude`、global excludesfile の候補列挙は `s2-plan.md:71-75` で具体化されていない。最終 matching を Git に任せても、候補に入らない nonexistent path は判定されない。
- この checkout は linked worktree である。`repo_root/.git` を directory と仮定して `.git/info/exclude` を読む実装は成立しない。`git rev-parse --git-path info/exclude` 相当で解決する必要がある。現行 common exclude の `.claude/worktrees/` 規則は `/work/1/SFC/tanab/izanagi/.git/info/exclude:11` にあるが、`output/` 外なので今回の集合には影響しない。
- `.gitignore` の未 commit 編集、common `.git/info/exclude`、ユーザーの global excludesfile を読むなら、結果はそれらの ambient state に依存する。どの source を受入契約に含めるかと Git config 環境を固定しなければ、checkout 間で再現できない。

`git check-ignore --no-index --stdin -z` は次の三分岐を明記すべきである。

- rc 0: 1 件以上一致。stdout を NUL 区切りとして読み、入力候補の部分集合であることを検査する。
- rc 1: 一致なし。stdout が空であることを要求し、空集合として扱う。
- その他: Git error として fail-closed にする。

現行 helper の `check=True` 形を流用すると rc 1 をエラーにし、逆に「非 0 は一致なし」とまとめると本当の Git error を隠す。プラン自身も `s2-plan.md:272-275` でこの部分を未確認としている。

また `--no-index` には別の穴がある。literal 候補 `"runs"` を prefix 化した後、`is_git_ignored_output_path()` は全 descendant を除外する (`output_snapshot_ignores.py:47-53`)。将来 `git add -f` された tracked file が `output/runs/` 配下に入っても、index を無視した判定と prefix 除外により Git-visible な tracked file まで隠れる。候補 prefix 配下に tracked entry が無いことを `git ls-files --cached` で検査する必要がある。

問題なしと判断した点: repository 外の submodule の実体化有無は、`output/` pathspec と `output/` 限定 prefix に閉じる限り結果へ混ざらない。

## 2. 実行順序への依存

`runs` に関する既知の順序依存は解消する設計である。

- 3 negative control は baseline を ignored parent 作成前へ移す (`s2-plan.md:135-151`)。
- 2 個の `_t080_output_snapshot` は全 directory の size、mtime、ctime を正規化する (`s2-plan.md:126-133`)。
- floor helper は元から directory timestamp を持たない (`test_s8b_floor_campaign.py:1484-1510`)。

したがって `output/runs` をどの test file が先に作ったかによる単独走と全走の差は、プランどおりなら消える。

ただし次は残る。

- snapshot helper は Git-visible path を走査する。`test_s8b_floor_campaign.py:1492-1508` は file digest と directory entry を、`test_s8b_oracle_driver.py:560-580` と `test_real_repo_serialization.py:543-563` は entry と非 directory metadata を比較する。
- `conftest.py:673-679` は実 output/snapshot 系を real-repo reader/writer 競合面から明示的に除外している。このため xdist worker 分配が変われば、snapshot 窓と書き手の重なりも変わる。
- 現在の worktree には Git-visible な untracked `output/insights/2026-08-26_flaky-holds-removal/` がある。既に存在して不変なら before/after 比較は通るが、別 process が窓内で更新すれば正しく赤になる。
- `.codex/worktrees/` と `.claude/worktrees/` は repository root 直下であり、3 helper の走査 root は `ROOT / "output"` である (`test_s8b_floor_campaign.py:1484`、`test_s8b_oracle_driver.py:1194-1195`)。ignore 判定の `-- output/` pathspec も閉じている (`output_snapshot_ignores.py:11-14`)。この 2 subtree が混ざる経路はない。

問題なしと判断した点: preexisting untracked file の存在だけでは before/after の結果は変わらず、窓内の作成、削除、更新だけが差になる。

## 3. 並行 shard との相互作用

`output/task-runs/` を通る相互作用は残る。runner の既定 root は repository 内の `output/task-runs` (`tools/run_tests.py:1064-1069`) で、記録は test child 終了後に書かれる (`tools/run_tests.py:1211-1218`)。report 生成も `reports/` を作成して file を publish する (`tools/task_runs/aggregate.py:854-919`)。別 shard がまだ snapshot 窓内なら、その正当な書き込みを拾う。

real-repo lock でも閉じない。snapshot node は inventory 外であり (`conftest.py:673-679`)、既存 lock 自体も同じ host/filesystem だけを保証する (`conftest.py:951-968`)。複数計算ノードの shard 間には効かない。

F136 は現在、同じ機序の反復を 3 件より多く記録している。依頼の「3 回」は、header 後の最初の三つの再発として判定した。

1. 2026-08-11 の `output/pegasus-dispatch/<nonce>/result.json` (`docs/failures.md:5000-5010`): 同じ理由では再発しない見込み。`.gitignore:26` の literal directory rule から prefix を常に得て、directory metadata も正規化するためである。
2. 2026-08-25 の最初の shard 再発、`output/task-runs/reports` (`docs/failures.md:5012-5029`): 再発しうる。これは Git-visible で、プランは除外、writer 移設、shard 間同期のいずれも行わない。
3. 同日 2 例目の `output/task-runs/reports` (`docs/failures.md:5034-5046`): 再発しうる。2 と同じ経路であり、wave の差分内容ではなく shard の重なりで決まる。

後続記録も path ごとの判定は同じである。`runs/pytest-launcher-failures` の作成と root mtime 変化 (`docs/failures.md:5068-5075,5084-5101`) は今回の `runs` prefix と directory metadata 正規化で閉じる。一方、`task-runs/reports` の反復 (`docs/failures.md:5048-5066,5077-5084`) は残る。

問題なしと判断した点: `pegasus-dispatch` と `runs` の literal rule 由来除外は、正しく実装されれば shard の投入順に依存しない。

## 4. 撤去後に同じ赤が出た場合の判定

プランは snapshot 子を registry 子より先に統合することで、未修理の hold#2 を先に受入へ戻す危険を避けている (`s2-plan.md:249-270`)。しかし、撤去後の高並列再発を分類する手順はなく、`s2-plan.md:274-278` は焦点走と受入全走が必要と述べるだけである。

赤が出た場合は次の順で判定する。

1. candidate commit、標準 shard 数、全 junit、failure digest、`output/` 差分を保存する。単独再走の緑だけで修理済みとは判定しない。
2. hold#1 は `test_pegasus_dispatch_compute.py:5484-5495` を見る。thread 生存 assertion だけが同じ署名で落ち、結果、qsub 2 回、orphan 不在の性質に別の破れがなく、単独走では消えるなら元の latency flake の再発である。別 assertion や dispatch 結果が変わるなら新しい回帰である。
3. hold#2 は差分 path で分ける。
   - `"runs" in ignored_prefixes` が落ちる: 新しい規則導出の回帰。
   - ignored な `runs`、`pegasus-dispatch` または directory metadata だけが差になる: 本 wave の snapshot 修理不足。
   - Git-visible な `task-runs/reports`、`pilot.json`、`output/insights` が差になる: 残存する F136 型の並行 writer 競合。
4. hold#3 は `test_real_repo_serialization.py:3821-3836` を見る。各 hook 1 回、controller payer 1 回、worker payer 不在が成立したまま line 3827 の相対順だけが反転するなら元 flake の再発である。payer 回数、不在条件、subprocess rc が崩れるなら性質の回帰である。
5. exact historical signature、単独緑、同条件の全走でのみ再発、candidate diff から対象 test body へ到達しない、の四条件が揃った場合だけ「元 flake の再発」と分類する。ただし wave 成功とは扱わず、再 hold ではなく修理を追加する。
6. 一度の受入再投入で消えても証明にはしない。少なくとも同じ標準 shard 条件で再確認し、結果と分類根拠を台帳へ残す。

問題なしと判断した点: hold#1 と hold#3 の既存 assertion は、結果、payer 不在、回数、順序の識別に必要な情報を残している。

## 所見一覧

- **所見 1**: hybrid 導出は wildcard 規則について実在 path 依存を意図的に残している
  - 場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/s2-plan.md:71`
  - なぜ問題か: temp tree の ignore 判定が、別 shard の実 `output/` に同名 path が存在するかで変わりうる。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 同一 commit の受入結果と failure report が実行順によって変わりうる。
  - 確度: high — line 76-78 が実在後の `git ls-files` 依存を明記している。

- **所見 2**: standard exclude source の列挙と linked worktree での source path 解決が未設計である
  - 場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/s2-plan.md:68`
  - なぜ問題か: nested `.gitignore`、info exclude、global excludesfile の nonexistent literal 候補を拾えず、`repo/.git` 仮定は linked worktree で壊れる。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: main checkout、linked worktree、別 host で除外集合と受入判定が食い違う。
  - 確度: high — plan は危険を列挙するが、line 71-75 に exact source inventory がない。

- **所見 3**: `git check-ignore` の rc 0、1、error と NUL 出力の契約がプランに無い
  - 場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/s2-plan.md:75`
  - なぜ問題か: rc 1 を失敗にするか、Git error を一致なしに潰すと、除外判定が恒真または環境依存の全赤になる。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 正当な node が受理集合から外れるか、検出すべき output 変更が report から消える。
  - 確度: high — line 272-275 も引数と NUL 処理を未確認と明記している。

- **所見 4**: `--no-index` と prefix 除外の組合せは force-added tracked descendant を隠す
  - 場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/s2-plan.md:75`; `orchestrator/tests/output_snapshot_ignores.py:47`
  - なぜ問題か: index を無視して `"runs"` を採用すると、その配下の tracked file まで Git-visible snapshot から除外される。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: tracked 成果物への副作用を見逃し、受入の受理集合が本来より広がる。
  - 確度: high — `--no-index` と descendant 全体を隠す prefix predicate が明示されている。

- **所見 5**: 並行 shard の `output/task-runs/` 書き込みによる偽赤が残る
  - 場所: `tools/run_tests.py:1064`; `tools/task_runs/aggregate.py:854`; `orchestrator/tests/conftest.py:673`; `docs/failures.md:5012`
  - なぜ問題か: writer root は repository 内、snapshot node は shard 間同期外、対象 path は Git-visible のままである。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 正当な並行 shard が snapshot node を赤にし、受入 receipt が確率的に発行されない。
  - 確度: high — F136 に同じ path の複数再発と並行 request の実測が記録されている。

- **所見 6**: 3 hold 撤去後の再発を分類する acceptance 手順がプランにない
  - 場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/s2-plan.md:268`
  - なぜ問題か: 単独走は登録時から緑であり、焦点走だけでは元 flake と本 wave の回帰を識別できない。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 未修理 node を台帳から外すか、非帰属赤を wave 回帰として誤って land 停止する。
  - 確度: high — parent measurements と plan line 274-278 が高並列での分類証拠を持たない。