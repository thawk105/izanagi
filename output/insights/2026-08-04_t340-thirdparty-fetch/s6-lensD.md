pytest は実行していない。以下の変異判定は、対象 4 ファイルのハッシュ再照合後に行った静的到達性判定であり、実測の緑・赤ではない。

### 所見 1 — JSON の `.cache_root` は hydrate を迂回し、R1 の ignored artifact 防壁を無効化する

**深刻度**: blocker

**根拠**: 裁定は ignored artifact を運ばないため hydrate を fresh clone にした一方、consumer 例では `.cache_root` を qsub に渡している (`s4-ruling-planv2.md:25`, `s4-ruling-planv2.md:30`, `s4-ruling-planv2.md:107`)。実装も常に cache 自体を `cache_root` として出す (`tools/pegasus/fetch_third_party.py:601`, `tools/pegasus/fetch_third_party.py:604`)。cache の検査は `git status --untracked-files=all` だけなので ignored file は見えない (`tools/pegasus/fetch_third_party.py:325`)。

T-139 probe は渡された root の各 source をそのまま `cp -a` する (`tools/pegasus/probes/t139_positive_control_probe.pbs:35`, `tools/pegasus/probes/t139_positive_control_probe.pbs:38`)。M2 テストも poison が消えたことを hydrate 後の個別 `resolved_path` でしか検査せず、qsub に渡す `.cache_root` は検査していない (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:217`, `orchestrator/tests/test_pegasus_thirdparty_fetch.py:222`)。

安全な hydrate 先自体は、driver の `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (`orchestrator/campaign/silo_ladder_rung1.py:54`) と helper の解決先 (`tools/pegasus/fetch_third_party.py:489`)、凍結 submitter の実パス (`tools/pegasus/submit_silo_ladder_rung1.sh:143`, `tools/pegasus/submit_silo_ladder_rung1.sh:152`) が一致する。しかし、その共通 root は JSON に出ていない。

さらに `verify-deps` は cache が存在しなくても成功することをテストが明示している (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:551`, `orchestrator/tests/test_pegasus_thirdparty_fetch.py:563`)。それでも main は存在未確認の `.cache_root` を返す。

**壊れる具体例**: pinned-clean な masstree cache に、`.gitignore` 対象の改竄済み `libkohler_masstree_json.a` を置く → `verify` は成功して cache root を出す → 裁定どおりその値を qsub に渡す → probe の `cp -a` が改竄 archive を build source に運ぶ。HEAD と clean status は正しいまま、binary の入力だけが pin とずれる。これは裁定自身が blocker とした結果 (`s4-ruling-planv2.md:164`) である。

**最小の直し方**: R6 を再裁定し、qsub 用には `hydrate` 後だけ出す独立な `source_root` を使わせる。`.cache_root` を consumer-ready root と称さない。テストは ignored artifact を仕込んだ後、JSON の指定 field をそのまま probe と同じ `root/name` 解決へ渡し、artifact が存在しないことを検査する。

### 所見 2 — 危険 Git config の手書き parser は forbidden key を実際に通す

**深刻度**: blocker

**根拠**: R3 は `filter.*`、`remote.*.uploadpack` 等を Git 起動前に拒否する契約である (`s4-ruling-planv2.md:62`)。しかし section regex は dot を通常の section 名として取り込む (`tools/pegasus/fetch_third_party.py:29`) のに、拒否側は `section == "filter"` / `section == "remote"` だけを見る (`tools/pegasus/fetch_third_party.py:204`)。

非書込 stdin 診断では、Git 2.34.1 は次を `filter.evil.clean` として受理した一方、実装の `_inspect_cache_config()` も例外なく受理した。

```ini
[filter.evil]
clean = /bin/false
```

M14 は引用 subsection 形式 `[filter "x"]` と `[remote "origin"]` しか与えていない (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:424`, `orchestrator/tests/test_pegasus_thirdparty_fetch.py:430`)。

別経路として、実装が読むのは `.git/config` 一冊だけである (`tools/pegasus/fetch_third_party.py:269`)。repo 内既存テストは `extensions.worktreeConfig=true` と `git config --worktree filter.evil.process ...` が実在する状態を作っている (`orchestrator/tests/test_dev_wave_land.py:835`, `orchestrator/tests/test_dev_wave_land.py:837`)。本 helper は `extensions.worktreeConfig` も `.git/config.worktree` も拒否・検査しない。

**壊れる具体例**: cache の `.git/config` に legacy dotted 形式の clean/process filter を置く → raw 検査を通過 → `_verify_source()` が `git status` を起動する (`tools/pegasus/fetch_third_party.py:325`)。推論: Git が内容変換を必要とする tracked path を検査すると、source を拒否するより先に filter command が実行されうる。少なくとも「危険 key を Git 起動前に拒否」は既に偽である。

**最小の直し方**: dotted legacy subsection は全拒否するか、base section と subsection に正規化して危険 family を検査する。`extensions.worktreeConfig` は拒否するか、`config.worktree` も Git 起動前に同じ parser で検査する。M14 は実 repo を作り、Git wrapper を「一度でも呼ばれたら失敗」にして pre-Git 拒否を検証する。

### 所見 3 — M1・M6・M13 は有効な kill を持たず、M12 は単一理由性を失っている

**深刻度**: blocker

**根拠**: 裁定は M1〜M15 の各変異を単一理由で kill すると要求する (`s4-ruling-planv2.md:139`, `s4-ruling-planv2.md:141`)。実装報告は全件対応済みと列挙する (`s5-impl.md:19`) が、テスト本文は次の状態である。

| M番号 | 赤くなるテスト名（静的予測） | 判定 (kill 可・不可) |
|---|---|---|
| M1 | `test_m01_policy_cmake_drift_is_rejected_before_acquisition` (`:193`) | kill 不可 |
| M2 | `test_m02_hydrate_fresh_clone_excludes_ignored_cache_artifact` (`:210`) | kill 可 |
| M3 | `test_m03_shallow_cache_is_rejected` (`:226`) | kill 可 |
| M4 | `test_m04_alternates_cache_is_rejected` (`:239`) | kill 可 |
| M5 | `test_m05_replace_refs_are_rejected` (`:253`) | kill 可 |
| M6 | なし。同名テスト (`:276`) は baseline assertion が成立しない | kill 不可 |
| M7 | `test_m07_head_mismatch_is_rejected` (`:291`) | kill 可 |
| M8 | `test_m08_origin_url_substitution_is_rejected` (`:310`) | kill 可 |
| M9 | `test_m09_final_component_symlink_is_rejected` (`:324`) | kill 可 |
| M10 | `test_m10_publish_reservation_never_replaces_existing_empty_directory` (`:340`) | kill 可 |
| M11 | `test_m11_existing_cache_never_runs_clone_fetch_pull_or_checkout` (`:357`) | kill 可 |
| M12 | `test_m12_git_environment_ignores_host_global_config_and_askpass` (`:376`) | kill 可・単一理由不可 |
| M13 | `test_m13_cache_root_inside_repo_is_rejected` (`:412`) | kill 不可 |
| M14 | `test_m14_dangerous_cache_config_keys_are_rejected_before_git` (`:424`) | kill 可。ただし parser 単体のみ |
| M15 | `test_m15_publish_is_reverified_before_success` (`:444`) | kill 可 |

M6 は `status.showUntrackedFiles=no` を設定した後、file ではなく空 directory を作るだけである (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:284`, `orchestrator/tests/test_pegasus_thirdparty_fetch.py:285`)。Git は空 directory を status に出さないため、現行の `--untracked-files=all` の有無にかかわらず line 287 の rc=1 期待を支えられない。

M1 と M13 は `_enable_local_fetch()` を呼ばない (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:193`, `orchestrator/tests/test_pegasus_thirdparty_fetch.py:412`)。対象変異で手前の gate を外すと、実装は HTTPS clone へ進む (`tools/pegasus/fetch_third_party.py:450`, `tools/pegasus/fetch_third_party.py:456`)。production env は HTTPS を許可する (`tools/pegasus/fetch_third_party.py:140`)。したがって失敗理由は外部 GitHub、診断文、cache 作成副作用に分散する。M1 は診断 assert が state assert より先 (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:206`)、M13 も診断 assert が cache state より先である (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:420`)。DW-M03 の受理集合 kill にならない。

M12 は env の内部 field assert 群 (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:395`) が behavioral Git call (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:403`) より先に止まる。登録理由の insteadOf 実効性ではなく、辞書 key 欠落でも同じ node が失敗する。

**壊れる具体例**: M6 の `--untracked-files=all` を削除しても、fixture に untracked file がないため検出差が生じない。M13 の包含検査を外すと、local fixture ではなく `https://github.com/fixture/...` へ接続を試み、その失敗文だけで test node が失敗しうる。

**最小の直し方**: M6 は実 file を作る。M1/M13 は常に local insteadOf + file-only protocol を有効化し、mutant で operation が成功する、または forbidden side effect が起きることを最初の assert にする。M12 は内部 env shape と behavioral rejection を別テストに分け、事前登録上の期待 node・理由を一つに固定する。

### 所見 4 — JSON sources の期待値が payload 自身で、値の破損を検出しない

**深刻度**: must-fix

**根拠**: JSON テストは期待 dict の `"sources"` に `payload["sources"]` 自身を入れている (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:540`, `orchestrator/tests/test_pegasus_thirdparty_fetch.py:544`)。後続 assert は source 名と key 集合しか見ず、`pin`、`head`、`resolved_path` の値を検査しない (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:546`)。別テストで実 payload の `resolved_path` を読むのは M2 の一箇所だけである (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:222`)。

**壊れる具体例**: `_verify_source()` の `"resolved_path": str(source)` を `str(source.parent)` に変える (`tools/pegasus/fetch_third_party.py:352`) → JSON テストは自己参照なので検出しない → M2 も親 directory 直下に `poison.a` がないため検出しない → consumer には source ではなく root が渡る。同様に `pin` と `head` を偽値にしても key 集合は一致する。

**最小の直し方**: operation ごとに、fixture から独立導出した exact record を比較する。`fetch/verify` は `cache/name`、`hydrate` は凍結 shell と一致する固定 root/name、`pin/head` は fixture の commit SHA を期待値にする。期待値生成に tool の `_load_policy()` や payload 自身を使わない。

### 所見 5 — helper の受理集合には裁定されていない合法 config 拒否も混入している

**深刻度**: nit

**根拠**: 凍結 shell の最終判定は real directory、HEAD、tracked/untracked clean だけである (`tools/pegasus/submit_silo_ladder_rung1.sh:6`, `tools/pegasus/submit_silo_ladder_rung1.sh:12`)。helper が shallow、alternates、replace、origin 等を追加拒否する差は裁定済み (`s4-ruling-planv2.md:35`, `s4-ruling-planv2.md:52`) だが、合法な Git config 文法全体を独自 subset に縮める裁定はない。

`_config_entries()` は section 行全体が regex に一致しないと拒否する (`tools/pegasus/fetch_third_party.py:185`, `tools/pegasus/fetch_third_party.py:190`)。非書込診断では Git が `[core] # benign` を合法として受理した一方、helper は同じ入力を `not safely parseable` で拒否した。M14 は拒否例だけで、合法な config の正例を持たない (`orchestrator/tests/test_pegasus_thirdparty_fetch.py:424`)。

受理差をまとめると、metadata/origin の追加拒否は裁定済み、ignored artifact は raw cache では両者とも見逃して hydrate だけが除去、dotted filter は拒否すべきなのに helper も見逃す、inline-comment config は shell が受理するのに helper だけが未裁定で拒否する。

**壊れる具体例**: pinned-clean clone の `[core]` section 行へ無害な末尾コメントを付ける → 凍結 shell は受理する → `verify` は rc=1 で拒否する。helper は任意なので campaign の最終受理集合は変わらないが、CLI 自身の受理集合は裁定外に縮んでいる。

**最小の直し方**: unquoted trailing comment を正しく扱うか、許可する config 文法 subset を裁定へ明記する。少なくとも Git が受理する無害な config の正例を追加し、危険 key の負例だけで parser を固定しない。

## 総括

- blocker あり。
- 最重 1: `.cache_root` consumer が hydrate を迂回し、ignored build artifact を T-139 へ運ぶ。
- 最重 2: R3 の config 防壁を dotted subsection / worktree config が迂回する。
- 最重 3: M1・M6・M13 の kill が成立せず、うち M1/M13 は外部 network に到達しうる。