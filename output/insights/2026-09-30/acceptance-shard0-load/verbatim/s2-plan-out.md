## 前提の反証

1. **P1 の行の単純置換は同値ではない。** `output_snapshot_ignores.py:564–630` の現行 snapshot は file 行を常に SHA256 で表す。前後の片側だけが cacheable なら、提案の blob 行と SHA256 行は、内容が同じでも異なる。例えば file の内容を変えずに mode だけを変更すると、後側は Git status により fallback しうる。比較時に混在した行だけを内容照合する必要がある。
2. **mode だけの変更を検出するという要件は現行の判定と両立しない。** 現行の file 行は `("file", relative, digest)` で mode を含まない (`output_snapshot_ignores.py:623–630`)。内容と path が同じなら mode 変更前後は等しい。新比較器で mode を検出すれば受理集合を狭め、現行同値にはならない。テストでは「現行と同じ結果」を固定し、mode 変更の検出を要求するなら別の仕様変更として裁定を要する。
3. **項 6 の「安価で厳密な全状態指紋」も自明ではない。** `git status --porcelain=v1 -uall --ignored` の出力だけでは、既に ignored である file の内容変更や、Git が監視を抑えた path の内容変更を表せない。全 file の内容を毎回 SHA256 にすれば厳密だが、約 1.1 GB の base を各 hit で読むため、P2 の短縮を相殺しうる。まず検出契約と hit 費用を分けて実測すべきである。

## P1

1. **比較器を共有 module に置く。** `output_snapshot_ignores.py:564–630` に、例として `git_indexed_output_comparison_snapshot(output: Path, repo_root: Path, *, walk_entries=None, digest_file=None)` を追加する。戻り値の file 行は cacheable なら `("file", relative, ("index", blob_sha, repo_relative))`、それ以外は `("file", relative, ("sha256", digest))` とする。directory と symlink は現行と同じ行にする。二つの snapshot を照合する `indexed_output_snapshots_equal(before, after, repo_root)` も同 module に置く。
2. **観測と cacheable 判定を一箇所へ抽出する。** `output_snapshot_ignores.py:564–611` の ignore、walk、worktree 判定、`_index_blobs_for_output`、`_status_paths_for_output`、`cacheable` 式を内部 iterator に抽出し、現行 `git_indexed_output_snapshot` と新比較器の双方が使う。現行側の `_INDEX_BLOB_SHA256_CACHE` と digest 呼出し (`:612–622`) は変えない。Git 呼出し・walk は毎回行う。
3. **混在行を遅延照合する。** `output_snapshot_ignores.py:630` の後に置く照合器は、kind・path・symlink target を先に比較する。index/index は blob ID を比較する。SHA256/SHA256 は digest を比較する。index/SHA256 のときだけ、記録した blob を `git cat-file blob <oid>` で読み SHA256 を計算して比較する。Git object が読めなければ赤にする。これにより mode のみの変更や、一時的な fallback でも現行と同じ内容判定になる。`("index", …)` と `("sha256", …)` をそのまま Python の `==` に渡してはならない。
4. **9 関数の二時点だけ置換する。** `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 呼出し対は `13803/13830`、`13892/13907`、`13911/13949`、`14045/14066`、`14448/14469`、`14536/14557`、`14562/14600`、`14606/14636`、`14640/14659`。各 before を新 snapshot にし、末尾の assert を照合器にする。関数名・nodeid・既存の assertion の意味を保つ。`_real_output_snapshot` 本体 (`:1780–1793`) と契約 test (`:1815–2240`)、特に digest 回数 (`:1871–1901`)、Git 起動回数 (`:1993–2090`)、default root の再観測 (`:2168–2203`) は編集不要。
5. **新設テスト。** `test_s8b_floor_campaign.py:2240` 付近で小さな Git repo を作り、各状態の前後について「新照合器の真偽 = `_real_output_snapshot` の二時点等値」を独立に検算する。正例は不変と同一 bytes への復帰。負例は tracked 内容変更、可視 file・directory の追加と削除、symlink target 変更。mode だけの変更は上記反証どおり現行に合わせる。既存 `:2030–2090` の五つの fallback、すなわち assume-unchanged、skip-worktree、subtree `.gitattributes`、`core.autocrlf`、root `.gitattributes` 変換について、各二時点の判定と digest 呼出しを検算する。混在行の同一 bytes／異なる bytes を別々に固定する。
6. **同値の範囲。** 同一の通常 POSIX tree と Git object が読める条件では、現行の cacheable 行が表す SHA256 は index blob の bytes の SHA256 なので同値となる。ただし Git blob ID の衝突、Git status が誤って clean とする状態、読取中の並行変更、blob object 消失では保証しない。現行の process cache にも同じ Git/status 前提があるが、object 消失時は新比較器だけが赤になりうる。

## P2

1. **session の path と key の出所を共有する。** `_t080_join_shared_bases` (`test_s8b_oracle_driver.py:975–993`) の `str(ROOT), run_id` による path 計算を、明示的 `run_id` を受ける小 helper に抽出する。`_t080_stub_free_e2e_repo` (`:1025–1045`) の五要素 key も既定引数から作る helper に集約する。default は `("AI-Agent: none", False, True, False, False)`、active-v2 は第五要素だけ `True` (`_build_t080_active_v2_repo:1839–1843`)。controller に tuple literal を複製しない。四要素 legacy key の digest 規則は `_T080SharedBases.get:942–948` のまま。
2. **controller を先に参加させる。** `conftest.py:2362` 付近に job 属性、`:2501–2537` の可視 output job と同型の `_start_t080_shared_base_prewarm(node)` を置く。`pytest_configure_node:2675–2678` の `_early_memo_selected` 分岐で、可視 output job を開始した直後に一度だけ開始する。同期部分で module を import して ROOT を照合し、共通 session path で `_T080SharedBases` を生成する。この constructor (`test_s8b_oracle_driver.py:924–929`) が dir を `mkdir(exist_ok=True)` し `workers.lock` に `LOCK_SH` で参加する。**thread 開始前**にこの参加を済ませ、worker import (`:975–995`) と dir 作成順が入れ替わっても同じ dir・lock に合流させる。
3. **builder は写し完成後に走らせる。** background thread で可視 output の `result.json` 成功を待ち、それから同一 `_T080SharedBases.get()` (`:938–972`) で default、active-v2 を順に構築する。`get()` 自身の `<digest>.lock`、失敗残骸削除、`complete.pending` から `complete.json` への publish を再利用する。controller には xdist worker の環境変数が通常ないため、`_t080_copy_visible_output:997–1022` に thread 局所の明示 run ID を渡す経路を足す。process 全体の `PYTEST_XDIST_TESTRUNUID` を一時変更してはならない。通常 worker の環境変数経路は残す。可視 output の失敗・180 秒 timeout は job error として記録し、黙って実 repo 複製へ fallback しない。
4. **終了順を固定する。** `conftest.py:2538–2560,3027–3033` に `_finish_t080_shared_base_prewarm(config)` を追加し、thread join、thread error の取得、controller の `bases.close()` をこの順に行う。`_finish_memo_sessions` ではこの finish を可視 output cleanup より前に置く。最後の参加者だけが tree を消す既存 `close()` (`test_s8b_oracle_driver.py:931–936`) を使い、worker の後始末を新設しない。thread 起動失敗でも controller の lock を閉じ、既存 finish の first error 規律に従って例外を伝播する。
5. **分岐検査。** `conftest.py:2371–2388` の既存選択条件をそのまま利用するので、単独走・絞り込み・非受入 xdist は従来経路となる。`test_s8b_oracle_driver.py:1162` 付近の可視 output テストと `test_real_repo_serialization.py:6473–6608` の早期 prewarm テストに、controller が worker collection より前に参加・開始すること、二度目の configure が追加構築しないこと、非選択時に session dir を作らないことを新設検証する。既存の早期 memo 呼出し順の literal (`test_real_repo_serialization.py:6562–6577`) は維持する。

## 項 6

1. **marker に base 状態を追加する。** `_T080SharedBases.get` (`test_s8b_oracle_driver.py:938–972`) の builder 完了後、`complete.pending` を書く直前に、root HEAD、root と nested repo の index bytes、worktree の可視状態、ignored file の状態を指紋化して `complete.json` に記録する。hit 時は `<digest>.lock` 内で再計算し、不一致なら `AssertionError` で赤にする。marker 欠落は従来どおり再構築する。既存 marker の `root`・`document` と key digest の形を保つ。
2. **費用を明示して方式を決める。** `git status --porcelain=v1 -uall --ignored` と HEAD・index hash は必要だが、status 出力だけでは ignored file の内容変更を検出できない。少なくとも ignored と assume-unchanged／skip-worktree path は内容 hash が要る。全 worktree bytes を厳密に指紋化する案は hit ごとに約 1.1 GB を読む。author は hit 当たりの時間を計測し、P2 の効果を食うなら status・index・全 path の `lstat` 情報と上記例外 path の内容 hash という検出範囲を明記した実装にする。完全な bytes 不変性を主張するなら全内容 hash が必要であり、対照性能の再評価なしに land しない。
3. **小 builder と実 builder の両方を扱う。** `test_s8b_oracle_driver.py:1213–1228` の既存小 builder は Git repo を作らない。そこでは小 tree の file bytes・symlink target・mode の指紋を使えば、`:1231–1454` の build 回数 `(1, 0)`、四／五要素 key golden、marker 欠落時再構築を維持できる。新設テストは hit 成功、base の tracked file 書換え、untracked file 追加、HEAD 移動をそれぞれ固定する。負例は **共有 base 自体**を変異させ、consumer への独立コピー (`:1025–1070`) は変異させない。

## 変異

| 変異 | 壊す箇所 | 赤になるべき nodeid |
|---|---|---|
| M1 | `output_snapshot_ignores.py:603–610` の status による fallback を外す | 新設 P1 tracked 書換え同値テスト |
| M2 | 新照合器の混在行を単純な `==` にする | 新設 P1 同一 bytes・mode 変更テスト |
| M3 | `output_snapshot_ignores.py:586–590` 相当の ignore 判定を外す | 新設 P1 ignored path テスト、既存 `test_real_output_snapshot_excludes_git_ignored_real_output_changes` |
| M4 | `conftest.py:2675–2678` の P2 開始を collection 後へ移す | 新設 controller 開始順テスト |
| M5 | P2 thread が `result.json` を待たず builder を始める | 新設可視 output 完成待ちテスト |
| M6 | `_T080SharedBases.get:938–972` の hit 指紋照合を外す | 新設 base tracked 書換え・untracked 追加・HEAD 移動テスト |
| M7 | `_T080SharedBases.close:931–936` より前に controller の session dir を消す | `test_t080_shared_base_only_last_participant_removes_tree` と新設 controller／worker 参加テスト |

## 焦点走

`tools/run_tests.py` 経由で、少なくとも次を実行する。P1 は `test_s8b_floor_campaign.py::test_real_output_snapshot_*`、新設比較器テスト、上記 9 関数の 11 nodeid。P2・項 6 は `test_s8b_oracle_driver.py::test_t080_visible_output_snapshot_starts_once_and_preserves_copy`、`test_t080_shared_base_*` 全件、`test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5`、default／active-v2 の実 consumer 各 1 本。さらに `test_real_repo_serialization.py::test_early_memo_*` と `test_memo_barrier_*`、`test_s8b_binding_driftguards.py`、`test_b4_binary_record.py`、`test_s8b_dependency_prefix_bridge.py`、`test_hold_inventory.py` の各 file を含める。実走と全受入は親が担当する。

## 壊れうる test

- `test_s8b_oracle_driver.py:1456–1544` の AST 名簿は `_t080_stub_free_e2e_repo` の直接 consumer を数える。controller からこの helper を呼ぶ形にせず `_T080SharedBases.get()` を呼べば、期待 14 関数／20 node を変えずに済む。
- `test_s8b_oracle_driver.py:1109–1140,1231–1454` は builder 回数、copy の独立性、四要素 legacy digest、active-v2 分離、marker 欠落後の再構築を固定する。key digest と `get()` の返値を変えず、指紋だけ marker に追加する。
- `test_real_repo_serialization.py:6473–6608` は `pytest_configure_node` の早期 memo の位置と非絞り込み判定を固定する。既存 `_start_early_memo_job(node)` 行を保持し、その後に P2 を追加する。
- `test_s8b_floor_campaign.py:1815–2240` は旧 snapshot の API、SHA256 行、Git 起動回数と digest 回数を固定する。旧関数を新形式へ切り替えず、新 API だけを 9 consumer に使う。
- `test_hold_inventory.py` と import consumer 三 file は nodeid・関数名・skip／xfail・hold 対象が変わると壊れる。既存 test の名前・assert・parametrize・xdist group を変更しない。`D365` に従い、新旧 base の bytes 一致を恒常 test に重複生成で持ち込まず、親が改修前後の tree manifest を一回照合して記録する。

## 総括

P1 は共有観測抽出、混在行の遅延照合、9 関数置換の順で実装する。
P2 は session 参加と写し完成待ちを先に作り、終了順まで検証する。
項 6 は指紋の検出範囲と hit 費用を測ってから確定する。
最大の危険は、P1 の混在行による誤検出と、項 6 の全量 hash が P2 の短縮を消すことである。