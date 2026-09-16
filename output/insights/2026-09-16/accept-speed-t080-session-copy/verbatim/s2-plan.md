## 前提の検算

**第一候補は実装可能。ただし P2 の index 状態、scan 回数、I1 の比較条件は訂正が必要である。** 本段は静的読解と既存ファイルの確認だけを行った。ファイル変更・Git 状態変更・pytest 実行はしていない。

以下、変更対象の `orchestrator/tests/test_s8b_oracle_driver.py` を **T**、`orchestrator/campaign/t080_freeze_migration.py` を **M**、`orchestrator/campaign/s8b_holdout_freeze.py` を **H** と略す。行番号は現行ファイルを指す。

| brief の記述 | 検算結果 |
|---|---|
| base 118.2 秒の内訳 | 52.9 + 53.3 + 9.5 + 2.5 = 118.2 秒。割合は約 44.8%、45.1%、8.0%、2.1% |
| output 複製 52.9 秒の細目 | 37.4 + 9.4 + 3.4 + 2.2 = 52.4 秒。残り約 0.5 秒は丸め・その他として扱う |
| `git add -A` は build の 8% | **直接には言えない。** 9.5 秒は `_run_git` 11 回全体。add 単独の時間ではない |
| verify 4.85 秒、その「うち」search 5.3 秒 | 包含関係として成立しない。母集団・呼出回数・平均方法を確認するまで、内訳として使用しない |
| 発行時 scan 最大 5 回 | **正常完走経路は 12 回。** 下表参照 |
| proto は index 未作成 | **誤り。** T:1443–1447 の `submodule add` が `.gitmodules` と gitlink を stage する |
| 分割点は連続した一か所 | T:1435–1441 の descriptor 変更を T:1450 の後へ移す必要がある |
| builder 後半は 1460–1660 | builder は T:1630 で終了。T:1633 以降は可視集合テスト |
| shared-base class は 896〜 | 宣言は T:894。constructor は T:897 |
| scan 点 M:2191 | helper の定義位置。実際の `search_repository` 呼出しは M:2201 |

発行 subprocess（T:1571–1603）の正常系における全件 scan は次のとおり。

| 段階 | scan 回数 | 根拠 |
|---|---:|---|
| `draft_receipt` | 3 | M:1959 の再構成から M:1727 の search と M:1731 の verifier → H:1029、さらに M:1985 |
| 明示的 `validate_draft` | 3 | M:2022 の再構成で 2 回、M:2023 で 1 回 |
| `finalize_receipt` | 4 | M:2035 の内部 `validate_draft` で 3 回、M:2048 で 1 回 |
| `verify_receipt` | 1 | M:2343–2346 → M:2201 |
| `gate_check` | 1 | driver:606 → driver:169 → 同じ live scan |
| **合計** | **12** | エラーによる途中終了では減りうる |

したがって「5 × 5.3 ≈ 26 秒」という発行 subprocess 内訳の推定は撤回する。12 × 5.3 秒も、異なる状態・cache 条件の平均を移植するため代替推定にはしない。**53.3 秒は子 process 全体の観測値として扱い、その内部配分は未測定とする。**

118 秒と 200〜222 秒は base と test node という測定範囲も異なる。差のすべてを競合へ帰属させず、競合削減は検証対象の仮説とする。案 C の「効かない」は今回のユーザー報告による訂正として明記し、repo 内一次資料で再確認できた値とは区別する。

## 分割点の確定

proto と key 側を以下に分ける。

| 現行箇所 | 配置 | 理由 |
|---|---|---|
| T:1370–1377 境界確認、mkdir、init、config | proto | key に依存しない |
| T:1380–1385 orchestrator・output 複製 | proto | 最大の共有対象。可視集合・ignore は変更しない |
| T:1387–1434 known の読込み、closure 抽出、basis 複製 | proto | 4 要素 key に依存しない |
| T:1435–1441 descriptor 変更 | key | `distinct_basis_blob` に依存 |
| T:1443–1450 submodule add、config、pin checkout | proto | key に依存しない |
| T:1451–1457 add、basis commit、never-issued assert | key | descriptor を含めた最終 basis を作る |
| T:1459–1630 発行分岐・subprocess | key | `issue_receipt`、trailer、extra path に依存 |

つまり、**T:1370–1434 と T:1443–1450 を proto にし、T:1435–1441 を派生コピー直後へ移す。** descriptor は submodule 操作が読む対象ではなく、双方とも最終 `git add -A` より前なので、この順序交換は最終内容を変えない。

`current_runtime_sources`（T:1416–1419）は後半でも必要である。proto の返却情報に相対パスの tuple を含める。実 repo からの runtime source 複製（T:1465–1467）も session 一回へ揃えるなら、proto repo **外の sibling** に現行 runtime bytes を保存し、key 側へローカルコピーする。repo 内へ置くと scan・tree が変わるため不可。

I1 の論証は次の条件付きとなる。

1. 同じ source snapshot、key、Git 設定・commit metadata を入力とする。
2. proto は既存のコピー処理と submodule 操作をそのまま実行する。
3. 派生は `.git` を含む全体を `copytree(..., symlinks=True)` で複製する。
4. descriptor 変更以降の処理・発行 subprocess を維持する。
5. 同じ内容・mode・gitlink を `git add -A` するので basis tree OID は一致する。
6. basis commit OID も一致する条件では、同じ production 発行処理が同じ receipt を作り、発行後 HEAD tree と working tree bytes も一致する。

**commit 時刻を統制しない別走間では receipt の完全一致は保証できない。** T:1452 の commit は時刻未固定で、M:1967 の receipt は `migration_basis_commit` を含む。同じ basis tree でも commit OID が違えば receipt bytes と発行後 tree OID が変わる。これは現行 builder 同士にも存在する非決定性である。比較テストだけで時刻を統制し、receipt の OID 欄を消して比較する方法は採らない。

Git 内部については、既存 fixture
`/tmp/izanagi-t080-e2e-base-3apxo21b/t080-stub-free-e2e`
の現物で以下を確認した。

- `.git/modules/external/ccbench/config:6`：`worktree = ../../../../external/ccbench`
- `external/ccbench/.git:1`：`gitdir: ../../.git/modules/external/ccbench`

この相対配置は repo 全体の移動で保存される。これは旧 wave の残存 fixture であり、今回の実行確認ではない。現在の builder が設定する親・submodule 双方の `gc.auto=0` は T:1374–1375、1448–1449 にあり、config ごとコピーする。

index の inode・stat cache は移動後に古くなるが、key 側の通常の `git add -A` によって再検査される。index を削除・再構成する高速化は加えない。

## 共有機構の設計

`_T080SharedBases` の lifetime をそのまま proto に適用する。

- session parent 内に `proto/` と、key digest と衝突しない `proto.lock` を置く。
- proto の完成情報は key 用 `*/complete.json` と区別できる名前・配置にする。
- proto 専用 lock 下で完成情報を確認し、不在なら残骸を削除して構築する。
- builder の正常 return 後に pending を書き、rename で完成情報を公開する。
- 例外時は完成情報を公開せず、次の要求で再構築する。
- key の lock と proto の lock は別。順序は **key → proto** に統一し、逆順を作らない。

proto のコピー中に再構築で削除されないよう、proto の利用期間をロックで保護する。推奨は fixture 専用の小さな context manager とする。

1. shared lock で完成情報を確認する。
2. 未完成なら一度解除し、exclusive lock を取得して再確認・構築する。
3. 完成後は shared lock にし、proto→key のコピー完了まで保持する。
4. key の commit・発行前には proto lock を解放する。

これにより完成済み proto のコピーは並行でき、再構築はコピー終了を待つ。汎用 cache framework にはしない。

寿命は T:900–916、959–961 の既存規約を維持する。全 worker が collection 中に参加し、最後の退出者だけが session parent 全体を削除する。proto 単独の `atexit` 削除は登録しない。共有経路では T:955 の `bases.close` に従属させる。

単独走にも process 内 proto memo を設ける。複数 key を使う直列走で共有を失わず、S2 の両経路要件にも合う。T:568 付近に成功済み proto の memo を追加し、T:985–997 の key memo miss から利用する。

単独走では、安全確認した `mkdtemp` parent を先に cleanup 登録し、構築成功後だけ memo に代入する。失敗した値を memo に残さない。proto parent、builder の書込先、派生先には T:37 の境界検査を通す。

## 派生の具体差分

変更は T だけとし、次の分離を推奨する。

- `_build_t080_e2e_proto(parent)`：key 非依存部分を構築し、repo root と runtime 情報を返す。
- `_finish_t080_stub_free_e2e_repo(...)`：descriptor 変更から発行までの既存処理を担う。
- `_build_t080_stub_free_e2e_repo(...)`：既存名を残す互換 wrapper。

wrapper は既存の引数・返却値を維持し、内部用の任意 keyword `proto=None` を追加する。

- `proto` 指定時：安全確認後に `.git` を含む repo を `shutil.copytree(..., symlinks=True)` で派生し、finish を呼ぶ。
- 未指定時：指定 parent に proto 部分を直接構築して finish を呼ぶ。従来の直接構築入口を保つ。
- destination は既存でないことを要求する。`dirs_exist_ok=True` による残骸との合成はしない。
- metadata・runtime snapshot は repo 外に置き、キー側の scan 対象へ混入させない。

既存 3 呼出し点の扱いは次のとおり。

| 呼出し点 | 差分 |
|---|---|
| T:929 `_T080SharedBases.get` | key miss 時に proto を借り、wrapper へ渡す |
| T:992 process memo miss | process proto を取得して wrapper へ渡す |
| T:1723 境界負例 | 引数を変えない。proto 取得・mkdir より先に拒否する |

T:1000 の base→test コピーと T:1001 の document deepcopy は維持する。key tuple の順序・意味・digest 算出も変えない。

## 回帰テスト案

既存テストの更新は次のとおり。表の名前はすべて `test_t080_shared_base_` 接頭辞を持つ。

| 現行 node・行 | 更新内容 |
|---|---|
| `builds_real_builder_once_across_processes`：1047 | wrapper の `(1, 0)` は維持。proto builder も wraps で `(1, 0)` を確認する。既存の実 repo 構築を増やさない |
| `returns_independent_repos_and_documents`：1087 | 現在の値を維持。小型 proto も含め inode・bytes・symlink・document の独立性を追加 |
| `without_completion_marker_is_rebuilt`：1107 | key builder 2 回を維持。proto builder は 1 回でよいことを確認 |
| `waits_for_builder_lock`：1121 | key lock の既存期待値を維持。proto lock 待ちは別の小型テスト |
| `missing_session_uses_process_memo`：1173 | key builder 1 回を維持。proto memo も reset し、異なる key でも proto は 1 回と確認 |
| `keeps_all_four_key_fields_separate`：1186 | key builder 5 回を維持し、proto builder 1 回を追加。返却 document に内部 `proto` 引数を混ぜない |
| `only_last_participant_removes_tree`：1203 | 削除 1 回を維持。小型 proto を実際に配置し、最初の close 後にも存在することを確認 |
| `cleanup_tolerates_real_disappearance`：1220 | 既存の 2 parameter と期待値を維持 |
| `cleanup_propagates_other_errors`：1254 | EACCES/EIO/ENOTEMPTY の伝播を維持 |
| `cleanup_exhausted_disappearance_is_error`：1270 | 3 回で再試行終了し、例外を隠さない期待値を維持 |

T:1070–1084 の `t080_small_cache_builder` は、proto も小型にする必要がある。key builder だけを mock した結果、cache テストが実 repo proto を作る実装にしない。

新規テストは以下を候補とする。

**小型 source によるコピー・Git 同値性。**

T:1633 の可視集合テストと同様、小さな source root を作る。tracked regular、実行 bit、untracked regular、ignored、symlink、receipt/draft の除外、深い path を含める。直接準備した repo と proto 派生を比較し、全 path の種類・bytes・mode・symlink target、basis tree、submodule pin/config を照合する。

`_copy_git_visible_output(source_root, destination)` は既に注入可能である。builder 全体は T:34 の module `ROOT` を monkeypatch でき、T:554/561 のコピー helper も同じ `ROOT` を読む。ただし imported production module の default 引数までは切り替わらないため、単に `ROOT` を置換しただけで発行可能とは扱わない。

**receipt までの同値性。**

任意の数ファイルだけでは、固定 artifact hash、source closure、ccbench pin、known builder の glob 再構成を満たさない。比較用 source は次の「小さいが有効な corpus」とする。

- 現行 production import closure。
- 正規の known/holdout artifact bytes。
- known が列挙する source と、既存 builder が復元する historical basis bytes。
- known builder が実際に読む campaign artifact 群。
- descriptor、positive control、必要な ccbench pin とその独立 object store。
- 可視集合用の小さい追加ファイル。

これは**比較テスト専用の source**であり、実 e2e の output コピー集合を絞る変更ではない。既存 e2e は実 repo の全件コピーを維持する。

旧順序を明記した小型 reference 経路と、新 proto 派生経路を同じ source に対して走らせる。reference を新しい prepare/finish の単なる呼び直しにはせず、descriptor/submodule の旧順序を独立に固定する。production builder/verifier/gate は stub しない。

Git commit 時刻は比較テスト内だけで固定する。T:369 と子 process 内の sanitization が `GIT_*` を除去するため、親で日付環境変数を設定するだけでは不足する。例えば PATH 上のテスト専用 Git launcher が、**実 Git の commit 実行時だけ** author/committer date を設定して実 Git へ委譲する。通常 fixture の commit 方針は変えない。

比較項目は、receipt を含む working tree bytes、basis/発行後 HEAD tree OID、receipt document および raw bytes。最低限 default key と `distinct_basis_blob=True` を対象とし、他の key 分離は既存テストを利用する。

有効 corpus の完全な最小集合と所要は未確認である。発行できない場合に verifier を緩めたり `{}` の一致を receipt 同値性と称したりしない。小型比較の費用を焦点走で確認することを実装の初期工程に置く。

**proto の負例。**

小型 builder で部分ファイルを書いて例外を起こし、完成情報がないこと、次回に再構築することを確認する。pending のみ、完成情報の JSON 破損、root/`.git`/submodule pointer の欠損も対象にする。copy の途中例外では key の完成情報が付かないことを確認する。

全ファイルの任意の後発 bit corruption を毎回検出するための全件 hash gate は追加しない。その保証は今回の marker 規約とは区別する。

**AST 検査。**

T:1285–1361、特に T:1326 の direct consumer 検査は現行の 6 function / 11 node と境界テストを維持する。新しい cache テストは T:1011 の callable fixture、同値性テストは builder 層を使い、e2e helper の direct consumer を不用意に増やさない。

## 変異 matrix の事前登録候補

新規 node 名は仮称。対象行は現行アンカーを示し、実装後に新行番号へ対応付ける。

| 変異 | 対象 | 期待 KILLED node |
|---|---|---|
| proto の output コピーから可視 regular 1 件を落とす | T:1385 の移設先 | `test_t080_proto_derivation_matches_direct_small_source` |
| descriptor 追記を削除 | T:1435–1441 の移設先 | 同値性の distinct case、既存 T:1735 |
| proto→key コピーから `.git` を除外 | 新 wrapper、T:1364 付近 | 小型 Git 同値性テスト |
| submodule pointer を proto の絶対 path に固定 | T:1443–1450 の移設先 | `test_t080_proto_submodule_relocation_is_independent` |
| proto lock を外す | T:918 付近の新 proto 管理 | `test_t080_shared_proto_waits_and_builds_once_across_keys` |
| builder 完了前に完成情報を公開 | 同上 | `test_t080_shared_proto_failure_is_rebuilt` |
| proto 失敗値を process memo に格納 | T:568、985 付近 | `test_t080_process_proto_failure_is_not_cached` |
| key 失敗でも complete を公開 | T:929–938 | key 構築失敗の負例 |
| `symlinks=True` を削除 | 新派生コピー | 独立性・小型同値性テスト |
| key tuple から distinct field を除く | T:980 | 既存 T:1186 |
| 最初の worker の close で削除 | T:903–916 | 既存 T:1203 の proto 拡張 |
| proto の境界検査を削除 | 新 proto builder 入口 | T:1717 の境界テスト拡張 |
| runtime snapshot を省略・historical bytes に置換 | T:1465–1467 の移設先 | receipt 同値性、既存 stub-free e2e |

lock 変異の killer は sleep による偶然の重なりではなく、既存 T:1121 の Pipe と lock 到達通知を踏襲する。異なる key の二つの要求で proto 構築を重ね、構築回数と待機を観測する。

## 焦点テスト集合と影響範囲

`orchestrator/tests/` 全体を検索した結果、指定 4 symbol の実コード参照は T 内に閉じている。

| symbol | consumer |
|---|---|
| `_t080_stub_free_e2e_repo` | callable fixture T:1011、境界 T:1726/1731、e2e T:1736/1837/1925/2158/2183/4754、AST T:1326 |
| `_build_t080_stub_free_e2e_repo` | T:929/992/1723、wraps/mock T:1054–1055/1081 |
| `_T080SharedBases` | join T:952、probe T:1006、cleanup T:1204/1205/1221/1255/1271 |
| `_copy_git_visible_output` | builder T:1385、可視集合 T:1688/1714 |

e2e の 11 node は以下の 6 function に属する。

- T:1735 `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`
- T:1835 `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5`：4 node
- T:1924 `test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5`
- T:2156 `test_t080_full_valid_history_defects_have_one_baseline_reason_f28`：3 node
- T:2182 `test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28`
- T:4753 `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`

conftest の real-repo access map にこの e2e 群は含まれず、T に handwritten `xdist_group` もない。proto 共有を理由に group・access map を変更しない。

再走集合は次とする。

1. shared-base 既存全テスト、新規 proto テスト、AST 検査、可視集合・境界テスト。
2. 上記 stub-free e2e 11 node。
3. `test_real_repo_serialization.py` の以下。
   - :1197 `test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default`
   - :1242 `test_t080_import_temp_environment_fails_closed_for_foreign_module`
   - :1586 `test_real_repo_group_collection_exactly_matches_canonical_nodes`
   - :1735 `test_shard_assignment_preserves_live_xdist_group_components_and_split_control`
4. 受入全走 K=3 と対照。

単独 process と複数 worker の共有機構は、小型テストで双方を検証する。実 repo e2e を同じ目的で何度も追加実行しない。本段ではいずれも未実行である。

## P3 の同時採用の価値

**今回は同時採用を推奨しない。**

`git ls-files -s` の mode 判定自体は T:794–812 で既に実装されている。T:836 の `is_file()` / `is_symlink()` は重複した分類ではなく、**index と working tree 実体の不一致を拒否する検査**である。

削除すると、tracked regular が symlink へ置換された場合に、既定の `copytree(symlinks=False)` がリンク先をコピーしてしまう。tracked file の欠損・directory 化も index mode だけでは検出できない。untracked には mode がなく、T:821–823 の実体確認が必要である。T:1709–1714 は tracked 欠損の拒否を既に固定している。

算術上の上限は以下。

- stat 部分 9.4 秒を完全除去できたとして、118.2 秒の約 **8.0%**。
- copytree 37.4 秒を理想的に 2 倍速化できれば **18.7 秒**削減。
- 理想的に 4 倍速化できれば **28.05 秒**削減。
- 両方の理想値を加えると **28.1 秒／37.45 秒**。

これは上限モデルであり、実現予測ではない。Lustre の帯域・metadata server・書込先が律速なら並列化で悪化しうる。

並列 copytree は、T:850–863 の ignore callback を各 directory で同じ意味に保ち、祖先集合、receipt/draft 除外、symlink、例外伝播、directory metadata の復元を維持する必要がある。proto 共有と同時に変更すると効果の帰属も難しくなる。

## 効果の見積りと計測設計

`R` を非依存の実 repo 準備、`D` を proto→key コピー、`G` を key 側 add/commit、`I` を発行とする。

- 現行の非競合 key 構築：`R + G + I`
- 新方式の最初の key：`R + D + G + I`

**非競合の最初の key は D だけ増える。** 期待する改善は、5 本の実 repo 準備が競合していた部分の削減である。単独 1 key 走では悪化が自然であり、受入の効果とは分けて報告する。

5 key の output 準備について、brief の直列値を便宜的に代入すると総作業量は、

- 現行：`5 × 52.9 = 264.5 秒`
- 新方式：`52.9 + 5D`
- 差：`211.6 − 5D 秒`

となる。仮に D=2.85 秒なら約197.4秒減だが、2.85秒は完成 base→test の値であり、proto コピーの実測ではない。また総作業量の減少を受入 wall や node-hour の減少と読まない。

計測は以下を固定する。

- post の実装 tip、source snapshot、worker/shard 条件、実行入口。
- K=3 の canonical acceptance wall と各走の値。
- 同時刻対照の tip・実行区間・機体条件・cache 条件。
- shard-0 の span、最長 node、proto 構築・待機・派生時間。
- proto の成功構築回数、key 構築回数、異常再構築の有無。
- failure、timeout、遅い走も含む全結果。

新しい計測基盤は作らず、既存ログ・profiler・受入成果物を使う。発行内部の scan 数はコード上 12 回と記録し、所要配分とは分離する。

D1260 の 10% を判定するには、可能なら変更以外を揃えた **pre/post の paired full K=3** を用意する。同時刻の他 session junit しかない場合は、外乱の対照として分布を併記できても、canonical wall の paired 比較を満たしたとは書かない。

10% 未満、または符号不明なら、

- bytes 同値性・回帰結果
- 実 repo 準備 5→1 の構造的変化
- wall の各走値・中央値・対照分布
- 「10% 基準未充足」または「判定に必要な対比較不足」

を分けて報告する。P4 に従い成果物は残し、land の判断は親の段4に渡す。

## リスクと未確定点

- **完成 marker の誤公開**：builder の途中失敗、metadata 書込み失敗、copy 失敗で完成扱いしない。pending→rename は成功後に限定する。任意の後発内容破損を全面検知する保証は別問題である。
- **早期削除**：collection 中の lifetime 参加を維持する。consumer の初回呼出し時まで join を遅らせない。proto コピーは shared lock で保護する。
- **容量**：output だけで proto 1 本＋key 5 本は約3.84 GB。現行より約640 MB増え、さらに test ごとのコピー、orchestrator、Git object、runtime snapshot が加わる。`/tmp` が tmpfs ならメモリにも算入される。受入時に容量・inode・実配置を確認する。
- **session identity**：T:949–953 の `[ROOT, run_id]` を維持し、その内側に proto を置く。別 worktree や別 run の共有はしない。既存 digest directory と proto の名前を分離する。
- **source の時間変化**：session 一回化は最初の source snapshot を全 key に固定する。現行の各 key 構築間に untracked output が増減する場合との同値性までは成り立たない。受入の source snapshot を固定する条件を明示する。T:868 の comment も、この fixture の session snapshot と可視集合 helper の非 memo 化を区別して直す。
- **`.git` の差**：index stat、reflog、内部 timestamp の bytes 一致は I1 に含めない。working tree の bytes・mode、Git tree、receipt を対象とする。submodule の `.git` pointer は working tree 内なので比較する。
- **前 wave の config.h 差**：既存 `.gitignore` と `git add -A` の挙動をそのまま維持し、今回取り込む修正をしない。実 repo HEAD ではなく現行 fixture が比較対象である。
- **hardlink/reflink**：hardlink は破壊的変異が他の copy に伝播するため不可。reflink は通常 CoW であり同じ危険とは限らないが、今回の明示 scope 外で、filesystem 依存も増えるため採らない。
- **小型の有効 corpus**：receipt 発行まで通る最小入力と所要は未検証。固定 pin・closure・known builder の glob 入力を満たしたことを production 経路で確認する必要がある。
- **費用モデル**：proto のローカルコピー時間、同時コピー時の帯域、発行12 scanの内部時間、実際の容量ピークは未測定である。

## 総括

推奨は、**key 非依存部分を session/process 共通の proto にし、`.git` を含む独立コピーから従来の key 側処理を実行する設計**である。変更は T に限定し、受理集合・production scan・既存 e2e 11 node を維持する。P3 は同時採用しない。

実装前に反映すべき訂正は、**proto は index を持つ、正常系の発行 scan は12回、receipt 完全一致の比較には commit metadata の統制が必要**の3点。正しさと共有回数は小型回帰で示し、受入 wall の改善は K=3 と同時刻対照で別に判定する。