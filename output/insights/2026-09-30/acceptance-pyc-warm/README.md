# 初回受入でも shard 開始前に bytecode cache をそろえる (md_7) — login collection を preflight 前に前倒しする実装を作り、変異 8/8 KILLED まで固めたが、事前登録の同時刻対照は 2 対とも不適格で「判定不能」。実装は main へ入れず branch に残す (2026-09-30)

依頼: `/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_7.txt` (共通指示 `common.txt`)。受入の shard が collection を始める前に投入元 worktree の pyc をそろえ、初回受入の pre (session 開始 → collection 完了) を縮める。受理集合・判定は変えない。
wave: branch `worktree-dev-wave-acceptance-pyc-warm` (実装の tip `f4920ddb3`、base = local main `d79fd3524`)。job dir `/work/1/SFC/tanab/dev-wave-jobs/acceptance-pyc-warm-20260930/`。
段 2 plan・段 3 相談 2 本・段 6 敵対レビュー 2 本・焦点再レビュー 1 本を行った (依頼が段 2・3・6 を省かないと指定)。子の出力の写しは `reviews/`、brief と裁定は `rulings/`、実測は `data/`。

## 結論

1. **設計択一は (c)「login collection を preflight の前に起動して重ねる」を採った。** 依頼の (a)「shard が login collection の完了を待つ」は、計算ノードの job が投入の約 9 秒後に始まるのに対し冷の login collection は投入意図から 85〜108 秒かかるので、待つ分が得を上回り悪化する見込み (約 14〜39 秒、段 3 相談 B の訂正値)。(b)「計算ノード worker に pyc を書かせる」は D918 が F52 を理由に却下済みで、しかも 48 worker が同時に冷で collection するので初回には効かない。
2. **md_2 の区間分解は投入意図を起点にしており、`tools/run_tests.py` の起動から投入意図までの区間を含んでいなかった。** md_2 の対照 4 走では 101〜102 秒、本 wave の対照 4 走では 55.7〜79.1 秒 (`data/pairs-aggregate.json` の `start_to_intent_s`)。login で preflight を個別に計ると `git ls-files --deleted` が 34.2 / 88.7 秒、RuleOps 検査が 2.6 / 8.1 秒 (`data/preflight-timing-*.txt`、別走なので同一走の内訳ではない)。session dir の作成 (birth time) は投入意図と同じ秒か約 1 秒前で (md_2 の対 1 H で 00:27:29 と 00:27:30、本 wave の 4 走は同じ秒)、この区間はほぼ全部 `main()` 側にある。(c) はこの区間に collection を重ねる。
3. **実装 (branch の f4920ddb3): shard 経路で submodule marker が有効なときだけ、最初の preflight の前に login collection を subprocess として起動し、`run_parallel` の `collect_login` ではその回収だけを行う。** command・env・cwd・exclusions・`login-collection.log` の bytes・rc・parse は従来経路と共通の helper。collection 子は従来の `subprocess.run` と同じく親の process group で走り、signal の扱いも従来のまま (自前 handler なし)。前倒しが rc 0・`text=True` と同じ厳密復号・parse 成功でなければ、log を書かずに従来形で 1 回取り直す (先行処理由来の新しい赤経路を作らない、F1083 の教訓)。marker 不在は submodule 初期化で木が書かれるので従来順序のまま。5100 秒の deadline の起点は不変。
4. **変異 8 本 (事前登録 M1〜M8) は 8/8 KILLED、期待 node と完全一致** (`data/mutation-final.json`、tip f4920ddb3、runner は `test_run_tests_shards.py -k early_login_collection`)。焦点走は run_tests 関連 7 file で 747 passed / 1 skipped / 0 failed、inventory 4 群と bytecode guard の test は 580 passed (1 件の赤は未 commit 差分を拾う検査で、commit 後の単独再走は緑)。
5. **同時刻対照 (事前登録、2 対) の判定は「判定不能」。適格な対が 0 だったので、事前登録どおり実装は land しない。** 対 1 は K の shard 2 の待ち行列が 78 秒 (適格条件は 60 秒以内)、対 2 は K の 3 shard (484 / 128 / 412 秒) と H の shard 1 (129 秒) が長い待ち行列で、H の shard 2 に赤 3 件があった。
6. **観測 (判定には使えないが事実として):** 対 1 は H の 3 shard の pre が 67.9 / 70.7 / 69.0 秒で温の峰に入り、K は 93.0 / 93.3 / 85.7 秒。shard pre 中央値の差は 24.0 秒 (K 93.0 − H 69.0)。H の login collection は投入意図の 33 秒後に完了し、K は 72 秒後。対 2 は待ち行列が長く K も温の峰に入り (中央値 69.2 秒)、H と差がない (69.6 秒)。H の login collection は投入意図の 9 秒後に完了していた。仕組みの読み (待ち行列が短い初回受入で pre が約 24 秒縮み、長ければ差が消える) と矛盾しないが、n = 1 対で事前登録の適格条件を満たしていない。
7. **現行 main (K) の pre は冷の峰 (md_2 の K = `PYTHONDONTWRITEBYTECODE=1` で 136〜138 秒) ではなく 86〜93 秒だった。** md_2 の雛形修正後は、従来経路の login collection も shard と並走して pyc を書くので、短い待ち行列でも部分的に温まっている。本実装の上乗せは対 1 で約 24 秒で、md_2 README の「残り約 38 秒」より小さい。

## 1. 実装の経緯

| 段 | 出来事 | 資料 |
|---|---|---|
| 2 plan | 反証: `_preflight_submodule` は marker 不在で `git submodule update --init` を実行し木を書く → 前倒しは marker 有効時だけ | `reviews/plan-out.md` |
| 3 相談 A/B | 両方「現 plan のまま採用しない」。collection の import 副作用、赤経路の pyc、起動失敗の rc 優先、deadline 起点、対照の K/H の test 集合差 (K は H tip で run_tests.py だけ base に戻す) などを裁定 | `reviews/consult-*.md`、`rulings/s4-ruling.md` |
| 5 実装 | Codex author。焦点走 1 回目で parametrize の引数名 `request` (pytest の予約名) による collection error、2 回目で代役 `wait_connections` が集合 `pending` をそのまま返し `run_parallel` の反復中 remove で rc 16 → いずれも test 側の fix | job dir `focus*-A.log`、`probe/why16.py` |
| 6 review A/B | 両方 NO-GO。must: log の復号差 (旧 `text=True`)、Popen 直後と cleanup 中の signal 窓、`/tmp` の一時出力失敗が新しい rc 16 経路。自前 handler と新 session をやめ従来と同じ signal 意味論に戻し、失敗時は従来形で取り直す fix | `reviews/review-*.md`、`rulings/s6-ruling.md` |
| 6 焦点再レビュー | NO-GO。取り直しで結果が従来の 1 回走と変わりうる (fail_first) は主張の言い過ぎとして訂正 (コード不変)、log の create-only 衝突と deadline 切れは従来と同じ rc 16 で refuted、割込みの窓と locale 依存 test は backlog | `reviews/focus1-out.md`、`rulings/s6-ruling.md` 追記 |
| 6 変異 | probe (全件 SURVIVED 期待) で観測した node を KILLED 期待に登録し本走 8/8 | `data/mutation-final.json` |

## 2. 同時刻対照 (結論 5〜7 の根拠)

事前登録: `rulings/s4-ruling.md`「同時刻対照の事前登録」と 23:01 の追記 (K の期待赤の確定方法)。runner / 集計器は Codex author 製 (job dir `meas/run-pair.sh`、`meas/aggregate.py`、`meas/make-trees.sh`)。

- 木: H tip `f4920ddb3` の fresh worktree 4 本。K1/K2 は `tools/run_tests.py` だけ `d79fd3524` の blob (`1c8af6ba…`) に戻した (commit しない)。H1/H2 は無変更 (blob `13c7ae4d…`)。作成直後の tests pyc 0、submodule marker あり (`data/trees.json`)。1 回目の作成で H1 の `git worktree add` が Lustre の EINTR で失敗し、同じ手順で H1/H2 だけ作り直した (`data/trees-attempt1.json`)。
- 起動: 各対で K と H を同時に `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` (起動差 0.003 / 0.005 秒)。対 1 23:18〜23:29、対 2 23:29〜23:47 (JST 9/30)。

| 対 | 腕 | prep (起動→session) | login collection (投入意図後) | 待ち行列 s0/s1/s2 | pre s0/s1/s2 | W_max | outer | rc |
|---|---|---:|---:|---|---|---:|---:|---|
| p1 | K | 55.7 | 72 | 9 / 10 / 78 | 93.0 / 93.3 / 85.7 | 281.9 | 420.7 | 1 (期待赤) |
| p1 | H | 55.7 | 33 | 11 / 9 / 10 | 67.9 / 70.7 / 69.0 | 346.6 | 446.7 | 0 |
| p2 | K | 79.1 | 83 | 484 / 128 / 412 | 67.5 / 83.9 / 69.2 | 268.8 | 865.1 | 1 (期待赤) |
| p2 | H | 78.1 | 9 | 11 / 129 / 9 | 68.3 / 69.6 / 95.1 | 328.8 | 485.1 | 1 (非帰属 3) |

単位は秒。待ち行列 = compute-visible.json の mtime − 投入意図の mtime (どちらも共有 FS の mtime、秒単位)。pre と W は md_2 の aggregate と同じ定義 (計算ノードの report / junit)。

- 判定 (事前登録どおり): 適格な対 0 → 「判定不能」。主判定 (H の shard pre 中央値 ≤ K − 20 秒) は対 1 で成立 (24.0 秒)、対 2 で不成立 (−0.4 秒)。害検査 H1 (H prep ≤ K prep + 15 秒)・H2 (login universe と observed universe が K/H で要素一致、28,663 件)・H3 (H の終了後 `git status --porcelain` 空) は両対で成立。
- K の赤は両対とも 27 件で、事前実走で固定した期待赤 26 件 (新 test 16 + 無効化の添え物を持つ helper 経由の既存 test 10) に、`test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` が加わった。K の木は設計上 run_tests.py を書き換えた dirty な木で、この検査は作業木の変更を B4 の 2 file に限るので、対照の作り方に帰属する。事前実走は対象 file だけを走らせたので拾えなかった (期待赤集合の漏れ)。
- H 対 2 の赤 3 件 (`test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`、`test_codex_worker_launch_budget.py::test_slow_preparation_longer_than_attempt_budget_is_accepted`、`test_dev_wave_cleanup.py::test_remove_child_detached_ancestry_and_empty_backup`) は非帰属と判定した: 3 件とも同じ shard 2 (計算ノード bnode058、記録された 1 分 load 56.9 / 48 core) で、launcher の時間切れ・時間予算の境界・`/proc` 走査中の process 消失。3 file とも `run_tests` を参照せず、変更は login 側の shard mode の経路だけで計算ノードの shard が走るコードは K と H で同一。同じ shard の pre も 95.1 秒と H の他 shard (68〜70) より遅い (`data/p2-H-reds.txt`)。
- 終了後の tests pyc は 4 走とも 453。
- 計算: 対照 12 job の Elapse 合計 3,482 秒。wave 全体 (焦点走 5 job 383 秒、変異 20 job 227 秒、対照 3,482 秒) で 4,092 秒 = 1.14 node 時間 (land 用の縮小受入は別)。2 node 時間を超える見込み (約 2.1) の段階で land 調整役に相談し GO (ユーザー委任による) を得た。

## 3. 採らなかったもの

- 実装の land — 事前登録の条件 (適格な対 2 つで主判定と害検査が成立) を満たさない。対 1 の改善だけで land するのは結果を見た後の条件変更になる。
- 取り直し (追加の対) — 待ち行列の長さは制御外で、夜間の対 2 は 6 shard 中 4 shard が 60 秒を超えた。新しい事前登録 (例: 3 対以上、適格な対の多数決) を別 wave で置けば再訪できるが、land すると `tools/run_tests.py` の blob が変わり走行中の全 wave が受入をやり直す (D987) ことと、対 1 で観測した上乗せ約 24 秒 / shard (初回受入・短い待ち行列のときだけ) を比べて決める。
- (a) shard が login collection を待つ・(b) 計算ノードに pyc を書かせる・`compileall` での温め — 結論 1、D918。
- 自前 signal handler と新 process group での前倒し子の管理 — 段 6 review B が窓を示し、従来と同じ意味論に戻した (`rulings/s6-ruling.md`)。

## 4. 確かめたこと・確かめていないこと

- 確かめた: 投入前区間が main() 側の git 検査に占められること (session birth と intent の時刻、preflight の個別計測)、実装の受理集合不変 (焦点走、変異 8/8、対照 4 走で universe 28,663 件の要素一致、H の終了後 status 空)、対 1 での pre 約 24 秒短縮と前倒しの collection の完了時刻 (投入意図の 33 秒後 / 9 秒後)。
- 確かめていない: 事前登録の適格条件を満たす対での効果 (判定不能)、`tools/dev_wave_wait.py acceptance` 経由の実受入での効果 (対照は run_tests.py の直接起動)、受入全走 (実装は land しないので実装 tip では走らせていない)、collection 中の import 副作用が tracked file を書かないことの網羅的な確認 (対照 4 走と焦点走で status 変化なし、までは確認)。
- 限界: 待ち行列の時刻は共有 FS の秒単位 mtime。K/H の同時起動は login の git 検査と collection を互いに競合させる。
