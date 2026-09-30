# 段 4 裁定 — acceptance-pyc-warm (md_7)  (2026-09-30 JST、結果を見る前に固定)

入力: brief.md、codex/plan-out.md、codex/consult-a-out.md (レンズ A 正しさ・process 寿命)、codex/consult-b-out.md (レンズ B 実効性・過剰)。裁定 inbox は 19:20 の full42 まで再走査、本件に関わる裁定なし。

## 所見の裁定

| 所見 | 判定 | 採否・scope |
|---|---|---|
| plan 反証: `_preflight_submodule` は marker 不在で `git submodule update --init` を実行し木を書く | real | 採用。前倒しは submodule marker が有効なときだけ。不在なら従来順序 (preflight → dispatch → collection) |
| A1 collection の import 副作用が preflight より先に起きる | real (論証の穴) | 採用 (記録 + 対照で検査)。集合不変の主張は「tracked file を書かない」ことに条件づける。対照で H の終了後 `git status --porcelain` 空と、K/H の universe 一致を検査。tracked を書く collection は現行でも受領証の post 指紋で赤になる (新しい経路ではない) |
| A2 観測する木の同一性の窓が約 100 秒広がる | real (限界) | must-fix にしない (DW-G05: 受理集合・値は変わらず、窓は shard 自身の数分の collection・実行窓より短い)。一次資料の限界に「nodeid 集合一致は bytes 同一の観測を意味しない」と明記 |
| A3 preflight 赤などの赤経路でも pyc が書かれる | real | 採用 (記録のみ)。P3 を成功経路に限定。赤経路で増えるのは ignored の pyc だけで、受領証の指紋 (git status) は不変。撤去証拠量が増えうる点を一次資料に書く |
| A4 前倒し Popen の失敗が新しい早期失敗面になる (F1083 型) | real | 採用。前倒しの起動失敗 (OSError・一時 file 作成失敗) は黙って捨て、従来の collection 経路 (`_collect_login_universe`) に戻る。rc の優先順位は現行と同じ (preflight rc が先) を test で固定 |
| A5 process 寿命の境界 test 不足 | real | 採用。実 subprocess で PID・子孫・一時 file の消滅を検査 |
| A6 deadline の起点未決 | real | 採用。5100 秒は現行どおり `_dispatch_result` の run_parallel 直前起点で不変。前倒し process の寿命は main が所有し、回収時の待ちは `deadline_at - now` で上限、未回収なら main の finally で停止 |
| A7 並走で RuleOps (60 秒 timeout) が延びる危険 | real (未測) | 対照の害検査で扱う (下の H1)。production への marker 追加はしない |
| A8 test が本体の流れを通らない | real | 採用。少なくとも 1 本は `main → _dispatch_result → run_parallel` を偽 dispatch と実 collection subprocess で通し、起動回数 1・回収結果・log bytes を検査 |
| B1 K/H の test 集合が違うと universe が一致しない | real | 採用。K = H と同じ tip の fresh 木で `tools/run_tests.py` だけ base blob に戻した作業木 (commit しない) |
| B2 約 40 秒は見込み、実受入への一般化は未測 | real | 採用。一次資料は見込みと実測を分け、直接起動の対照である旨を明記。主判定は pre、外側 wall は報告 (下の判定) |
| B3 投入前 101 秒の内訳は同一走で未確定 | real | 部分採用。production に marker は足さない (D1729 の見送りと同方向、scope 外)。対照で `start-epoch → session dir birth` (= preflight 区間) を run ごとに記録する。tree_fingerprint が shard 経路で呼ばれないのは事実として brief を訂正 |
| B4 揃わない条件・部分的な条件 | real | 採用。全 shard を除外せず報告 |
| B5 素朴 (a) の比較値が過大 | real | 訂正: (a) 単独の悪化見込みは約 14〜39 秒 (H pre 108〜111 → 温 65 の得 43〜46 秒 < 追加待ち 60〜82 秒)。(c)+上限つき待ちは採らない (1 cycle 後の候補) |
| B6 同時起動の login 競合・短い待ち行列の定義 | real | 採用。下の事前登録で固定 |
| B7 採算未立証・D987 の再受入費用 | real | 採用。land 条件を事前登録し、満たさなければ実装は land せず記録だけ (md_6 と同じ扱い)。LAND-READY に「tools/run_tests.py を変える」を添え、land 順は調整役 |
| B8 compileall・計算ノード先行 collection は不採用 | real | 採用 (不採用と明記) |
| B9 計算の余裕が小さい | real | 採用。見積りを下に積み、再走で 2 node 時間を超える見込みになったらユーザー確認 |

## plan v2 (実装の規定)

1. `tools/run_tests.py` だけ変更。`tools/acceptance_shards.py` は不変。
2. 前倒し条件 = run_parallel に到達する shard 経路 (`shard_mode`、空 argv、`internal_shard_spec is None`、dispatch 免除でない、Pegasus LOGIN、bounded membership でない) かつ `_submodule_is_initialized(repo)` が真。main の shard 適格性確定後・最初の preflight (`_preflight_unstaged_deletions`) の前に起動。
3. command・env・cwd・exclusions・log bytes・parse・rc は `_collect_login_universe` と共通 helper で byte 同一。stdout/stderr は repo 外の一時 file (tempfile) に流し、回収後に読む。新しい process group で起動。
4. 回収は `_dispatch_result` の `collect_login` callback が所有権を受け取り、`deadline_at - now` で待つ。前倒し process が無ければ従来の `_collect_login_universe` を呼ぶ。
5. 後始末: main が `try/finally` で所有。未回収なら group に SIGTERM → 猶予 → SIGKILL → wait、一時 file close・削除。前倒し起動から run_parallel の handler 設置までの SIGINT/SIGTERM も finally が走る形にする (既存 handler の意味は変えない)。
6. 前倒しの起動失敗は黙って従来経路へ。preflight の rc・メッセージは現行と同じ。
7. 非 shard 経路・marker 不在・内部 shard・免除 flag は byte 単位で現行挙動。
8. 規模上限: run_tests.py の差分 +150 行以内、test +300 行以内を目安 (超過は段 6 で差し戻し理由を問う)。既存 test の期待値を変えない。既存 test が main を偽 dispatch で呼ぶ箇所で実 collection subprocess が走ってしまう場合は、前倒し起動 helper を monkeypatch で無効にする添え物だけ許す (期待 rc・引数は不変)。

## 変異の事前登録 (DW-M01、nodeid は実装後に確定して erratum なしで照合)

| ID | 変異 (production) | kill 期待 |
|---|---|---|
| M1 | 前倒し条件を常に偽にする (起動しない) | 「preflight 前に起動済み」を検査する新 test |
| M2 | callback が前倒し process を使わず `_collect_login_universe` を呼ぶ (再 collection) | 起動回数 1・出力再利用を検査する新 test (main→run_parallel 通し) |
| M3 | 回収時に `login-collection.log` を書かない | log bytes を検査する新 test |
| M4 | preflight 赤の経路で停止・reap しない (finally の後始末を外す) | preflight 赤で process 消滅を検査する新 test |
| M5 | marker 不在でも前倒しする (marker 条件を外す) | marker 不在で起動しないことを検査する新 test |
| M6 | 起動失敗時に従来経路へ戻らず INFRA rc を返す | 起動失敗 fallback を検査する新 test |

単一理由性は実装後に確認 (F820)。harness は `tools/mutation_harness.py`、runner は dispatch (DW-M07)。

## 同時刻対照の事前登録 (結果を見る前)

- 木: wave の最終 tip H (段 6 後) から fresh worktree 4 本 (detached)。K1/K2 は作成後に `tools/run_tests.py` だけ base main (`d79fd3524` の blob) に戻す (commit しない)。H1/H2 は無変更。作成直後の tests pyc 0、submodule 初期化済み、HEAD と run_tests.py の blob sha を記録。
- 起動: 各対で K と H を同時に `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py`、両側 `PYTHONDONTWRITEBYTECODE` unset、起動差 ≤ 5 秒。対 1 → 対 2 の順、対の間に他の対照 job を重ねない。
- 記録 (run ごと): start-epoch、session dir birth (= preflight 区間 prep)、intent・confirm・handled・login-collection.log の mtime、shard 別 compute-visible.json mtime、shard 別 pre と W (md_2 の aggregate と同じ定義)、W_max、outer (start-epoch → 統合 junit.xml mtime)、rc、login universe・observed universe、終了後の tests pyc 数、終了後の `git status --porcelain`。
- 適格 shard: intent → compute-visible ≤ 60 秒 (短い待ち行列)。対は 6 shard すべて適格のとき「適格な対」。不適格な shard・対も除外せず報告する。
- 期待赤: H は赤 0。K は H の新 test のうち新関数を使うものだけが赤 (集合は投入前に H の diff から列挙して固定)。それ以外の赤は非帰属として調べる。
- 主判定 (land 条件): 適格な対が 2 つあり、両対で H の shard pre 中央値 ≤ K の shard pre 中央値 − 20 秒。かつ害検査 H1: 両対で H の prep ≤ K の prep + 15 秒。かつ H2: 両対で K/H の login universe と observed universe が要素一致。かつ H3: H の終了後 `git status --porcelain` が空。
- 1 対でも適格でなければ「判定不能」とし、実装は land しない (記録のみ)。主判定が不成立でも land しない。
- 報告のみ (判定に使わない): outer と W_max の差 (W_max は shard-0 の外れ値で ±150 秒揺れるため)。
- 計算見積り: 対照 12 job ≈ 1.1〜1.2 node 時間 (md_2 実績 1.13)、受入 1 走 ≈ 0.3、変異 6 本の dispatch ≈ 0.2〜0.3 → 合計 ≈ 1.6〜1.8 node 時間 (2 未満)。再走などで 2 を超える見込みになったら止めてユーザーに確認する。

## 段 5 の分割

- U1 (Codex author、worktree は別 branch): `tools/run_tests.py`、`orchestrator/tests/test_run_tests_shards.py` (必要なら `test_run_tests_preflight.py` の添え物)。
- U2 (Codex author、別 worktree): 計測 runner を repo 内 `scratch-apw/` に書く (make-trees.sh・run-pair.sh・aggregate.py を md_2 の版から改修)。親が job dir `meas/` へ移し scratch を削除 (DW-C01)。U2 は repo の tracked file を編集しない。

## 追記 (2026-09-30 23:01 JST、対照の投入前・結果を見る前): K の期待赤集合の確定方法の訂正

事前登録は「K の期待赤 = H の新 test のうち新関数を使うもの (H の diff から列挙)」としたが、段 5 で既存 helper (`_prepare_default_login` ほか 3 箇所) に前倒し起動 helper を無効にする monkeypatch が入り、base の run_tests.py では属性が無いため helper 経由の既存 test も落ちる。静的列挙では閉じないので、K と同じ内容 (H tip f4920ddb3 の木で tools/run_tests.py だけ d79fd3524 の blob) で `tools/run_tests.py orchestrator/tests/test_run_tests_shards.py -q -rf` を 1 回実走し (wave 木の一時変異、復元照合済み、log は meas/k-red-prerun.log)、赤 26 件 (新 test 16 + helper 経由の既存 test 10) を期待赤とした。file: meas/expected-k-red.txt (sha256 9ab90bfd280a371a14b8ab5ba2eb5c094c243c69972cdfc8bb80fda9c9d49bb9)。判定式・閾値・適格条件は変えない。
