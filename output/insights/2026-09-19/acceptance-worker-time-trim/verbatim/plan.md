## 変更面

**優先は U1 の mutation 前 fixture 共有と、U3 の preflight 入力 repo の局所化。P2 の before 共用、P4 の完成 oracle 単純コピーは採らない。** 以下は静的確認による計画であり、同一性・削減秒・変異 kill 集合は未実測。

行番号は現 worktree 基準。本文では次の略号を使う。

- F：[test_s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_s8b_ratified_freeze.py)
- V：[test_s8b_ratified_verify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_s8b_ratified_verify.py)
- C：[test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_s8b_floor_campaign.py)
- O：[output_snapshot_ignores.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/output_snapshot_ignores.py)
- R：[test_run_tests_preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_run_tests_preflight.py)
- A：[test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_codex_reasoning_ab.py)
- P：[test_p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_p3_b4_producer_auth_experiment.py)
- T：[test_t1259_qsub_env_delivery_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py)

| 所有 | 位置 | 変更 | 型 | 段1からの削減見積り |
|---|---|---|---|---|
| U1 | F:1001–1127 | campaign 完了直後、追加ファイル・mutation 適用前の木を session 内で一度構築し、各呼出しへ copytree | ii・iv | 825秒の一部。builder 内訳未分離のため秒数未確定 |
| U1 | F:1286、V:215・686 | 共用 builder を利用。`load_ratified_freeze`、`launch_validate`、assertion は各呼出しで実行 | ii | 上段に含む。baseline 分を二重計上しない |
| U2 | C:1780、O:604–620 | clean index entry の既存 digest memo だけを session 共有。before/after は維持 | ii・iv | cold worker 数を W とすると概算 `15.6×(W−1)` 秒から共有費を引く。profile 値であり予測 |
| U2 | O:144–180 | ignore 規則 bytes の解析結果だけを同一入力 memo にする小候補 | ii | 未分離。1.4秒/回の規則照会全体は削れない |
| U3 | R:81、対象 login test 群 | 小さい実 Git repo を module base とし、test ごとにコピーして `RT._REPO` へ注入 | i・ii | 19 node の約200秒の大部分から、小 repo の実 fingerprint 費を引く |
| U3 | A:860–960 | session 共有の構築素材・snapshot 木＋worker copy。oracle と prompt 束縛はコピー先で再生成 | ii・iv | setup 135秒の一部。検証・コピー費を残すため125秒削減とは見積もらない |
| U4 | P:759・791・821 | 候補別 prepared tree の module 内 lazy 共有を条件付き候補にする | i | 同 worker に配置された場合だけ構築回数減。現在の group 不変では0秒もあり得る |
| U4 | T:73 | 現行維持を基本。template の session 共有は小候補として計測判断 | i・iv | file 単独 setup 約10秒が上限側の目安。550秒は削減可能額でない |

F:1439、V:483、A:1678、C:759・815は、後述の理由で主実装には含めない。production、conftest、nodeid、node 数、group、登録簿は変更しない。

## U1

**共有境界**

F:1085–1101 の `_run_official_fixture_campaign` が返った直後、F:1102 の `selector_extra_files` 適用より前を切断点とする。

共有物は repo 全体と、`base`、`checkpoint["C"]`、v1、pin、design/generator bytes、repo 相対の run directory。コピー後に F:1102 以降を実行し、state の読取り、mutation、admission evidence、G/A/X commit、最終 assertion を従来どおり行う。共有物に `VerifiedFreeze`、seal capability、`LaunchValidatedFreeze` 等の生きた検証済みオブジェクトは保存しない。

builder 全引数の分類は次のとおり。

| 分類 | 引数 | 根拠・扱い |
|---|---|---|
| campaign 前に効くため key | `now` | F:1091。run ID・時刻・cert に影響 |
| 同上 | `selector_valid_cell`、`selector_payload_hit` | F:1024–1027、1100。base と preflight に影響 |
| 同上 | `perf_available` | F:1087–1088。measure と perf receipt に影響 |
| 同上 | `compiler_input_rel` | F:1094。compiler-input bytes と receipt に影響 |
| 同上 | `cert_at_generation` | F:1064–1071。campaign 中の C commit 有無に影響 |
| コピー後に毎回適用 | `selector_extra_files` | `_prepare_emitter_base` に渡されるが、同関数内では未使用。実際の適用は F:1103 |
| 同上 | `mutate`、`mutate_g1` | F:1127、1225 |
| 同上 | `extra_closure`、`executable_role` | F:1192、1177 |
| 同上 | `journal_manifest_before_g`、`generation_strings_escaped` | F:1201、1228 |
| 同上 | `result_schema`、`mutate_attempt_registry` | F:1143–1165。入口の引数検査 F:1016–1021 は cache hit 時も実行 |
| 配置先 | `tmp_path` | 通常経路では key にしない。返却先を従来どおり `tmp_path / "repo"` にする |
| 別経路 | `receipt_root` | **非 None は memo を迂回し、現行処理を維持** |

session 識別には実 worktree root と `PYTEST_XDIST_TESTRUNUID` を含める。異なる worktree、A/B run、production mutant 間で共有しない。

**決定性と絶対パス**

決定性の根拠は F:278–314 の固定 Git identity/date・SHA-1・autocrlf 設定、F:391–410 の固定 host/process/receipt、F:516 の決定的 binary payload、F:1089–1093 の時計・sleep・probe seam である。ただし、これだけで全 key の byte identity が証明されたとは扱わない。

| 面 | 絶対パスの入口 | コピー後の判定 |
|---|---|---|
| cert | F:1064 の cert file path | artifact 本体は production `s8b_floor_campaign.py:5565–5580` の hash・時刻・run ID。root は含まれない |
| manifest/result binaries | F:544–548 の binary、build/cache/source root、argv | production 同 file:4746–4758、4789–4825、4933–4955 が相対化・placeholder 化。通常経路の移設根拠になる |
| journal/result sessions | F:590 の実 binary を含む run command | F:1277–1281 が journal/result 内の tmp/root/out bytes 不在を検査。コピー先でも既存検証を実行 |
| `durable_root_policy` | F:1097–1099 の `root.resolve()` | 実行時の書込み権限。capability を移送しない。コピー後に実行する処理ではコピー先の policy を使う |
| `_fixed_prepare.cache_root` | F:1060–1061 | 関数属性なので disk copy では移らない。cache hit 時もコピー先で設定し直す |
| `.git/izanagi` evidence | campaign が作成する内部状態 | legacy は F:1144–1147、v5 は `s8b_v2_freeze_fixture.py:586–588` で admission root を破棄し、毎回再構築する |
| selector 証拠 | F:804–825 の provider root・実行ファイル・`drive_journal` | 固定時計が明示注入されていない。`selector_valid_cell=True` の完全決定性は**未確認**。実測成立までは共有対象外 |
| その他の disk bytes | result.md、prepared cache、Git 管理ファイル等 | F:1278 の検査対象外。全木比較で旧 root 参照・symlink・gitdir を確認する必要がある |

固定 `/fixture/...` はコピー元固有パスとは区別する。artifact の root 文字列を一括置換する案は採らない。

**Git index**

production `orchestrator/campaign/s8b_ratified_freeze.py` の検索結果では、**`diff-index` 呼出しは存在しない**。

- `_capture_head`:340–359 は `rev-parse` と履歴防護。
- `_assert_namespace_clean`:367–378 は `status --porcelain`。
- :875、1512、1638、2713 の `ls-tree` は commit tree を読む。
- :1049–1055 は closure の worktree bytes と H blob を直接比較する。

したがって「この module の diff-index 偽陽性」という説明は訂正する。ただし brief の複製規律に従い、**copytree 直後、mutation 前に親 repo と内側 ccbench の `git update-index --refresh` と status 確認を置く**。campaign 後の未追跡 artifact は元から存在するので、repo 全体が clean であることは要求せず、元と同じ staged/unstaged/untracked 状態を確認する。`git add`、reset、checkout による清浄化はしない。

**fork と他 caller**

`in_sealed_fixture_process` は `s8b_v2_freeze_fixture.py:92–129` で test 本体を fork し、子が `os._exit` する。子で作った dict memo は次の test に残らないため、**disk memo＋flock が必要**。

`_T080SharedBases`:900–972 と同じく、collection 時は lifetime lock への参加だけ、構築は初回需要時、key lock 下で行い、完成 marker を最後に公開する。最後の worker が削除する。fork 子が親の lifetime lock を明示 unlock しないよう、所有 PID を区別する。非 xdist でも親が fork 前に disk memo の所在を持つ必要がある。

コピー後の portable receipt 検証は production `s8b_ratified_freeze.py:1831` → `s8b_binary_admission.py:324` の durable schema 検査であり、issuer capability 自体を要求する API ではない。**異なる PID からの load/launch 成功は静的根拠があるが、実測は未確認**。

他 caller の保護条件は以下。

- F、holdout、oracle 経由でも signature と返却 tuple を変えない。
- `receipt_root=` は T-080 の既存 R・source closure・ccbench pin を保持する F:1030–1056 を必ず通す。通常 fixture と混ぜない。
- `append_production_emitter_g2`:1291 は変更しない。g2 用 cache root は :1303–1304 で再設定される。
- `load_emitter_g1`:1286 は builder の共有だけを受け、`M.load_ratified_freeze(root)` は毎回実行する。

**baseline と旧 builder**

V:215 の baseline は「構築」を共有できるが、**baseline の合格判定を module 一回へ移してはならない**。各 caller で load と launch assertion を残す。引数追加による nodeid 変更は不要。

なお現 tree では `_assert_emitter_baseline` の呼出しサイトは8箇所で、parametrize を含む実行数は別になる。brief の「9呼出し」と一致しておらず、削減計算前に collection と突合する。

F:1439 の `build_valid_semantic_g1` と V:483 の独立 builder は、それぞれ通常の `_git/_commit`、`_lgit/_lcommit` を使い、Git 日時が固定されていない。前者は base SHA が g1 bytes に入り、後者も C/G/A/X/H を返す。**現行のまま決定的完成木として memo する案は採らない**。固定日時への変更を今回の4型に紛れ込ませない。

## U2

**P2 は不採用**

module baseline B に対し、先行 test が変更 X を残した場合、後続 test が何も変更しなくても `after != B` で失敗する。現行の直前 before/after なら後続 test は成功する。逆に後続 test が X を B に戻すと、module baseline では変更を見逃す。

したがって帰属だけでなく、**失敗 node 集合と個別 test の検出条件が変わる**。before/after の両呼出しを維持する。

現 tree の該当 callsite は C:13796、13885、13904、14038、14441、14529、14555、14599、14633 の**9組18呼出し**。brief の10 test・20呼出しとは差がある。C:2194・2198 の2呼出しは自己検査であり、official test の組数に混ぜない。

**共有できる部分**

O:604–620 の現在の cacheable 条件をそのまま使い、`(blob_sha, repo_relative)` → digest の値だけを session 内で共有する。

- walk、index、status、fallback 判定は各 snapshot で実行。
- dirty/untracked、変換属性、assume-unchanged、skip-worktree は従来どおり実 file を読む。
- session 共有を使うのは C の実 root 経路からの明示指定だけ。O の一般 caller と自己検査の既定動作は維持。
- key ごとの書込みを25,185回 flock する実装にせず、miss の集合をまとめて共有する。
- 完成 snapshot tuple や「unchanged」という判定は保存しない。

ignore 規則については、O:115–141 が取得した **bytes tuple を key にした :144–180 の純粋解析結果**だけなら memo 可能。source bytes の再読取り自体、`:183` の Git 判定、`:251` の tracked 例外、`:268` の現在存在する ignored paths は一回化しない。

index snapshot の一回化は不採用。実測では `ls-files` は約0.01秒であり、意味を失うリスクに対して利得も小さい。

**自己検査の維持条件**

- C:1815：rglob oracle との一致、順序、directory/symlink/file。
- :1834：同サイズ変更、復元、untracked file、空 directory。
- :1901–2098：digest cache、fallback、**snapshot ごとの index/status 呼出し回数**。
- :2117・2139：visible change の検出、ignored change の除外。
- :2168：default root でも依存関数を毎回観測。
- :2205：digest failure を伝播。
- :2218：reference oracle の独立性。

特に :2034–2036 が index/status 各3回を pin しているため、これを assertion の変更で通す案は採らない。

**約90 test の経路**

profile は9.9秒中9.1秒が `s8b_holdout_admission.py:5230` 以下の二乗 ledger 回復と示す。subprocess 18回は計0.03秒で、authority repo 構築や fake build は主因ではない。

C:759 の authority は同一 out_root 内で既に再利用され、以後 admission ledger を持つ。共有するなら予約前の pristine tree だけだが、Git 日時非固定と小さい利得が残る。**今回は変更しない。90×5.8秒を削減見積りに入れない。**

public preflight の clone＋実 scan も現行維持。scan は検査対象であり、clone を copy に置換するだけの利得は未確認。

## U3

**preflight：P3 を採用**

R:81 の `_tracked_repo` を元に、小さい実 Git repo を module fixture で構築し、対象 test ごとに copytree する。追加する fixture は `_clean_runner_env`:58 に依存させ、汚染された Git 環境を除去した後にコピー・Git 操作・`RT._REPO` 注入を行う。

対象は durations の19 node を生む次の関数群に限定する。

`R:477, 1304, 1382, 1539, 1837, 2204, 2225, 2314, 2369, 2393, 2413`

parametrize と assertion は維持する。四象限 test の dispatch 枝にも必要な最小の正常 repo 入力を用意し、どの枝も機構を置換しない。

比較結果：

| 案 | 判定 |
|---|---|
| `RT._REPO` を tmp 実 repo へ | 採用。main に repo 引数はなく、module の root 定数が外側の入力 seam。fingerprint の実装・5 command はそのまま |
| fingerprint 戻り値を固定／memo | 不採用。CAP_OOM 前後比較の機構を差し替える |
| 実 worktree の fingerprint を一回共有 | 不採用。前後の変化を観測できない |
| 実 worktree 全体を複製 | 意味は保ち得るが、この routing test への入力として過大。小 repo 案より優先しない |

既存 fingerprint mock の R:565、1449、1873、1898、1926 は変更しない。

`tools/run_tests.py:2540` と :2567 の実 fingerprint は毎回実行する。これで DW-O14 の検査機構維持を満たす。

**RecordingSession の注意**

`tools/run_tests.py:1068` には `_REPO/output/task-runs` への経路がある。さらに **constructor の :1029 の default `Path(_REPO)` は import 時に束縛済み**であり、`RT._REPO` の変更だけでは `self.repo_root` は変わらない。:1097 の自動記録開始に到達すると、旧実 repo を使い得る。

一方、正規 runner の子環境は :1118、1299、1599 で automatic recording を `0` にし、:2155–2157 は非記録経路へ進む。R:58 はこの変数を消していない。したがって今回の正規実行経路では追加の RecordingSession patch は不要。ただし、**親の A/B 起動環境でこの値を確認すること**。直接 pytest 起動まで安全と断言しない。

**codex_ab：P4 は共有範囲を限定して採用**

完成した fixture dict をそのまま copy することはできない。

- `tools/codex_reasoning_ab.py:3600`：oracle の `snapshot` は絶対パス。
- :3617：そのパスを含む oracle 全体の digest。
- :3727–3732：rendered prompt にコピー先絶対パスを埋め込む。
- :3766–3774：prompt SHA、`new_root`、`absolute_paths`、snapshot oracle SHA。
- A:924–958：root、sessions、base、snapshot、oracle、prompt の Path。
- production :1046–1066：submodule 初期化時の local source URL。
- :1511–1545：submodule `.git` の移設可能性検査。

共有構築では、現在の A:866–943 の入力 bytes、base、POS/NEG の木、構築中の base metadata 観測を保存する。各 worker は木と入力を copytree し、**実 `verify_snapshot` をコピー先に対して実行して oracle を作り、実 `render_prompt` で prompt/receipt を作る**。共有時の oracle は worker の合格判定として再利用しない。

これは構築前の素材と構築された木の共有であり、validation の memo ではない。Git object closure、mode、symlink、submodule gitdir、index semantics を保つ。A:3795 の base 不変性 assertion と index 比較も残す。

単純な shared `_build_snapshot_base` だけでは、production :3343 の artifact `git show` 等が worker ごとに実 repo を読むため、実 repo 読取り一回という目的を完遂しない。共有構築側で POS/NEG の必要素材まで揃える。

コピー後の再検証が derive 費用の相当部分を再び使うため、**純削減の符号は未確認**。135秒全体を削れるとは扱わない。

**`_full_manifest` は memo しない**

A:1678–1840 は schedule、run root、実行ファイル、launch/event/done/output/rollout/receipt/packet の相互束縛を作る。:1765–1785 は記録された絶対パスから再読取りする。コピー後の文字列置換では、それらの hash・receipt chain が一致しない。

また profile の46.2秒は production `verify_manifest` の実行で、fixture 作成費ではない。既存 `memoize_construction_snapshots` の patch を拡大・既定化する案も提示しない。6呼出し・115秒をそのまま削減可能額にしない。

## U4

**p3_b4**

現コードは「3 test×3 tree」ではなく、P:759 が3候補、:791 が3候補、:821 が frozen のみで、**計7 tree**。

module scope の lazy candidate factory は構成可能。ただし次の条件を付ける。

1. 使用する候補だけを構築する。全3候補を eager 構築すると、issuer の異常で frozen 専用 node まで失敗し得る。
2. production `ScratchTree` と `prepare_candidate_tree` を実行して prepared tree を作る。
3. P:782 の明示 `validate_exact_replacements` は省かない。最初の test には未適用の pristine tree を別に渡し、そこで毎回実行する。
4. prepared tree を読む AST・hash・順序 assertion は各 test に残す。
5. failed construction は完成品として memo しない。
6. 消費側は現在どおり読取りだけ。変更が必要な consumer には独立 copy を渡す。

ただし module fixture は worker ごとであり、3 node が別 worker に配られれば共有効果はない。pristine tree の保持・コピー費も増える。**現在の group を維持した A/B で利得が出なければ不採用**とする。session 共有まで増築して利得を追う案は主計画にしない。

P:1141 の8 wave mutant node、および production `run_isolated_cases`:2001 の各 case は隔離そのものを試すため変更しない。`ScratchTree` の展開・破棄と `tools/run_tests.py` 子実行が残る律速である。

**t1259／P5**

T:73 は既に module template、:83–97 は test ごとの deepcopy である。本体0.43秒の driver 経路を in-process 化する理由はない。

ただし「局所候補が全くない」とまでは言えない。既存 template の元になる `probe._repo_snapshot(REPO_ROOT)` を T-080 同型の session 共有へ移す候補は型 i・iv に収まる。既存の清浄化投影と deepcopy、既存 patch の位置は変えない。

優先度は低い。段1の file 全体12秒・setup10秒に対し共有管理費が必要で、48 worker 台帳550秒の解消を説明できない。**主計画は無変更、小候補の利得は未確認**とする。

## 不採用

- module baseline 一回による before の省略：個別検出条件と失敗 node 集合が変わる。
- walk・status・index・ignore 結果の無条件共有：現状観測と自己検査の契約を壊す。
- baseline の load/launch 成功、snapshot oracle、`verify_manifest` の判定 memo：古い判定の再利用。
- U1 の process dict memo：fork 子で消える。
- 非決定的 Git builder の完成木 memo：Git SHA・artifact bytes 不変を満たせない。
- `receipt_root` 経路を通常 emitter cache に統合：T-080 の入力閉包・R の意味を失う。
- p3_b4 の wave mutant／isolated case の木共有、子 runner の in-process 化：隔離・実子起動という検査対象を変える。
- D2068 の3案、圧縮設定変更、hold・parametrize・group・launcher の変更：提示対象外。

## A/B と変異

**計測**

ABABAB の3対は最低限として実施可能。ただし P6 の「12 worker の比が48 workerへ転移」は未確認である。

| 穴 | 対処 |
|---|---|
| page cache と常に後走する B の優位 | A/B 双方を同条件で予備走。ABABAB の順序依存を記録し、可能なら逆順対も追加。共有マシンの cache drop は使わない |
| session memo の持越し | 各走で別 testrunuid・別 tmp root。A/B・mutant 間で memo を共有しない |
| `/tmp` 残骸 | 各走の開始前・終了後の使用量と inode を記録。対象 run の残骸だけを片付ける |
| pyc | 両側を同条件にする。変異走は新 interpreter と独立 cache を使い、同サイズ・同時刻編集による古い pyc 読込みを避ける |
| ScratchTree の容量・teardown | 856 MB/本に同時生存数と shared base を掛けた使用量を見積もる。teardown を計測外へ逃がさない |
| shared lock の待ち時間 | 構築費だけでなく、待機・コピー・削除を junit 合計に含める |
| source の不一致 | ff 取込み後の共通 production を基準に、A/B の差を許可 test/helper のみに固定 |
| file 単独と6 file 同走の差 | 最終比較は6 file 同走、同じ `-n 12`・scheduler・hold 条件で実施 |
| junit への帰属 | setup/call/teardown 合計を集計し、collection・atexit 等の外側費用を wall 時間でも併記 |

各 file の対差 `A_i−B_i` の中央値・最小・最大を報告する。共有 helper の効果が別 file に帰属する可能性があるため、6 file 合計も併記する。受入48 worker は別の完了確認とし、12 worker の比から秒数を外挿しない。

**変異候補**

以下は一時的な mutation 実験用であり、land する production 変更ではない。各変異を一つずつ、修正前／修正後 test に適用する。KILLED 実測は未確認。

| U | production の位置 | 置換内容 | 観測が変わる既存 test |
|---|---|---|---|
| U1 | `s8b_ratified_freeze.py:1024` | source の `_blob_at_or_fail(...)` を `(root / path).read_bytes()` に | V:1433 の worktree drift 正例が失敗 |
| U1 | 同:1015 | `parents[0] != frozen` を `False` に | V:1457 の期待 refusal が変わる |
| U1 | 同:1042 | closure SHA 不一致条件を `False` に | V:1489 の `closure-sha-mismatch` 観測が変わる |
| U2 | `s8b_floor_campaign.py:7605` | checkpoint 後 raw hash 不一致条件を `False` に | C:13861 の「raw hash」拒否が消える／別理由になる |
| U2 | 同:7611 | launch-start の cert SHA を `"0" * 64` に | C:13795 の cert/journal 束縛 assertion が変わる |
| U3/R | `tools/run_tests.py:2560` | `return scope_result.child_rc` を `return 0` に | R:1837 の rc=5 assertion が失敗 |
| U3/R | 同:2571 | `tree_before != tree_after` を `False` に | R:1885 の変更時 dispatch 禁止が破れる |
| U3/A | `tools/codex_reasoning_ab.py:3514` | HEAD 不一致条件を `False` に | A:3552 の独立 HEAD pin 拒否が消える |
| U3/A | 同:3516 | branch 不一致条件を `False` に | A:3734 の detached HEAD 拒否が消える |
| U4 | `p3_b4_producer_auth_experiment.py:483` | patch の `guard_issuer()` 挿入 bytes を2行にする | P:791 の guard call count が2になる |
| U4 | 同:527 | `guard_raw_assembly()` 挿入 bytes を2行にする | 同じく RAW 候補の call count が2になる |

mutation matrix は全対象 node の setup/error/call failure を含めて比較する。共有構築失敗を「全 consumer の setup error」に広げてしまった場合も不一致として扱う。無変異の緑、収集 node 集合一致、各変異の非空失敗集合を前提に、**`failed_before == failed_after`** を要求する。

U1 は6 file のほか、既存の F・holdout・oracle の caller、特に receipt-root 経路も互換性確認に含める。これは編集 scope の拡大ではない。

## 所有分割

| 所有 | 編集可能 file |
|---|---|
| U1 | F、V |
| U2 | C、O |
| U3 | R、A |
| U4 | P、採用判断した場合のみ T |

U2 は F の builder、`_run_official_fixture_campaign`、固定 seam を編集・共用化しない。C 内の snapshot wrapper と O の digest memo に閉じる。共有管理コードを新 framework や conftest に移さない。U1〜U4 の file 所有は重ならない。

## 裁定パッケージ候補

- production `s8b_holdout_admission.py:5230` の attempt ledger 二乗回復。約90 node の主要律速だが、別 wave の production 改善候補。
- production snapshot verification と p3_b4 ScratchTree／子 runner の費用。今回の計画では維持し、改善が必要なら検査意味を明示した別課題にする。
- P2 をどうしても採る場合は、失敗 node 集合不変という現契約の変更が必要。今回の実装候補には含めない。

## 総括

U1 は mutation 前の disk fixture 共有、U3/R は小さい実 repo 入力を優先する。
U2 は before/after を保ち、clean blob digest の重複計算だけを共有する。
U3/A・U4 はコピーと再検証を含む純利得を確認して採否を決める。
bytes・Git SHA・別 PID 消費・変異失敗集合の同一性は未確認であり、親の計算ノード実測が必要。
本段ではファイル変更・pytest・性能測定を行っていない。