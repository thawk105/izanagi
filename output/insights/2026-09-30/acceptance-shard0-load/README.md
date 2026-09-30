# 受入 shard-0 の最忙 worker の仕事を減らす — 主成分は T-080 共有 base の構築待ちと実測し、controller が collection 中に base を先に組む形を実装したが、同時刻対照 2 対が割れ (collection が長い走で T0 −130 秒、短い走で +11 秒) 事前登録の land 条件を満たさないので実装は main へ入れない (2026-09-30)

依頼: `/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_6.txt` (共通指示 `common.txt`)。受入 shard-0 の最も忙しい worker の仕事を、検査範囲 (受理集合) を縮めずに減らす。
wave: `worktree-dev-wave-acceptance-shard0-load`、base = local main `4f412c67b`。job dir `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/` (brief・裁定・codex の入出力・生死確認・対照・変異の生記録)。逐語は `verbatim/`、集計は `data/`。

## 結論

1. **shard-0 の最忙 worker (占有中央値 201.3 秒、shard-1/2 は約 160 秒) の中身は走ごとに違う 1〜3 本の長い item で、重い 2 群 (T-080 群・floor official 群) が占めるのは中央値 39 秒だった** (緑 10 走、§1)。worker 名 property は全 testcase に付いており、前 wave の「一部にしか付かない」は再現しなかった。
2. **2 群の時間の中身を計算ノードの生死確認で分けた** (§2)。T-080 群の 1 本 85〜117 秒の大半は test 本体 (3〜30 秒) ではなく共有 base の構築 (1 回 約 100〜150 秒) の flock 待ち、floor official 群の 1 本 約 87 秒は各 worker が 1 回払う全 tracked file の sha256 (約 37 秒) と前後 2 回の snapshot の固定費 (約 30 秒)。active-v2 の emitter 実走は 1 本 約 8 秒と小さい。
3. **md_6 の 3 候補のうち実装したのは T-080 共有 base の先行構築 1 つ** (controller が collection 中に default・active-v2 の 2 key を組む。D1708 が名指しした形)。floor の比較器の置換は、段 3 相談が racy clean と mode 変更の組合せで受理集合が広がる例・狭まる例を構成したので D1709 に照らして見送り、emitter 共有は効果が小さいので見送った (§3)。
4. **共有状態 (やること 3) は「consumer は複製にしか書かない」を新設 test と変異で示した。** 共有 base 自体の改変を hit のたびに検出する機構は足していない (§4)。
5. **同時刻対照 2 対 (計算ノード、両腕 fresh・冷) は割れた** (§7)。対 1 (collection 約 90〜120 秒) では shard-0 の test 段 T0 が 130.5 秒 (32%)、W0 が 162.8 秒縮み、T-080 群の合計は 3,045 → 2,187 秒。対 2 (collection 約 68 秒) では T0 が 10.7 秒、W0 が 11.7 秒伸び、T-080 群の合計も縮まなかった (2,102 → 2,195 秒)。**事前登録の land 条件 L1 (2 対とも ΔT0 > 0) と L4 (2 対とも W0 が悪化しない) を満たさないので、実装は main へ入れない** (記録だけを land する。D2242 と同型)。実装は branch `worktree-dev-wave-acceptance-shard0-load` (tip `c9af2b562`、実装だけの系列は `as0-u1` の `7d20b2c1f`) に残す。
6. 読み (n=1 ずつ、確定ではない): 先行構築は写しの完成 (約 60 秒以上) を待ってから始まり構築に約 100 秒かかるので、collection が短い温の木では test 開始に間に合わず consumer はほぼ従来どおり待つ。効くのは collection が長い (冷の木・混雑) 走に限られる。次に効かせるなら、写しを待たずに構築の前半を始める・構築そのものを縮める (probe4 の内訳: 写しの複製・`git add -A`・発行 child) 方向になる (§9)。
7. 対照の途中で本 wave の実装の実在欠陥を 1 つ見つけて直した: prewarm が写しを consumer 用の 180 秒上限で待ち、T-080 consumer を持たない shard を終了処理で赤にしうる (受入全体が `report-invalid`)。停止 event まで待ち、写しの遅延・失敗では構築せず静かに終える形にした (§5、`docs/failures.md` の新規 F)。

## 1. 最忙 worker の実測 (やること 1)

受入の緑 10 走 (9/30 02:42〜05:06 開始、shard dir の digest は `data/baseline-runs.json`) を、junit の worker property と `report.json` の `session_timeline` から集計した (`data/baseline-result.txt`、`data/baseline-span.txt`)。

| 指標 (秒) | shard-0 | shard-1 | shard-2 |
|---|---:|---:|---:|
| 最忙 worker の占有 (testcase time の和) の中央値 | 201.3 | 160.0 | 160.6 |
| span 最大 (最初の開始 → 最後の終了) の中央値 | 213.1 | 160.1 | 160.6 |

- worker 名の property (`izanagi_acceptance_pairing_v1_worker`) は 82 走・328 file の全 testcase (4,613,456 件) に付いていた。前 wave (md_2 §6 項 2) の「一部にしか付かない」は再現しなかった。
- shard-0 の最忙 worker の中身は走ごとに違う 1〜3 本の長い item で、重い 2 群 (T-080 群 44 nodeid、floor official 群 54 nodeid) が最忙 worker の占有に占めるのは中央値 39 秒だった (10 走中 4 走は 0 秒)。2 群はどちらも全 10 走で shard-0 に入り、23〜32 個の worker に散る。shard-0 では占有最大の worker と最後に終わる worker が一致したのは 2/10 走だけで、span − 占有の中央値は 60.5 秒 (最大 229 秒)。testcase time に入らない待ちが span にある (内訳は junit と report からは分けられない)。
- 2 群の中で値がそろう: T-080 群は約 20 本が 85〜117 秒、floor official 群は約 10 本が 84〜95 秒。

## 2. 何が時間を食っているか (生死確認、計算ノード、コード不変)

| 確認 | 条件 | 結果 |
|---|---|---|
| probe1 | `-n 0` の 1 process で floor の snapshot 付き 3 本と兄弟 1 本、T-080 4 本 | floor 67.4 → 30.5 / 31.6 秒、snapshot 無しの兄弟 0.10 秒。T-080 は xdist 無しでは共有 base が効かず 133〜157 秒 |
| probe2 | `-n 1` (共有 base 有効) で T-080 6 本 | default key: 構築込み 154.2 秒 → 同 key の 2 本目以降 3.2 秒。active-v2: 構築込み 149.8 秒 → 24.9 / 31.3 秒 |
| probe3 | py-spy、active-v2 1 本 (124 秒) | emitter の実走 (`build_production_emitter_g1`) 約 8 秒、`launch_validate` 約 3 秒 (`data/probe3-agg.out`) |
| probe4 | py-spy `--idle`、default key 構築 1 本 (113 秒) | `_build_t080_stub_free_e2e_repo` 98 秒 = 可視 output の複製 47.4 秒 (単独走なので実 repo の Lustre から) + `git add -A` 14.6 秒 + 発行 child 33.4 秒 + 他 (`data/probe4-lines.out`) |

読み: 受入で T-080 の約 20 本が各 85〜117 秒かかるのは、test 本体 (3〜30 秒) ではなく base 構築 (1 回 約 100〜150 秒) の flock 待ちが大半である (1,000〜1,800 秒 / 走は `-n 0` / `-n 1` の単独走からの外挿)。floor の 11 本は、各 worker が 1 回だけ払う全 tracked file (32,462 個・1.1 GB) の sha256 (約 37 秒) と、前後 2 回の snapshot の固定費 (約 30 秒) でできている。

## 3. 採ったもの・見送ったもの (やること 2)

md_6 が挙げた 3 候補のうち 1 つを実装した。

1. **T-080 共有 base の構築待ち (実装した。対照で land 条件を満たさず main へは入れない、§7)**: 受入の非絞り込み shard 実行で、controller が `pytest_configure_node` の早期 prewarm 分岐 (`_early_memo_selected`、可視 output の写しと同じ条件) から、worker の collection と並行に default key と active-v2 key の共有 base を既存の `_T080SharedBases` 規約 (同じ session dir・`workers.lock`・key の flock・`complete.json`) のまま先に組む (`orchestrator/tests/conftest.py` の `_start_t080_shared_base_prewarm` / `_finish_t080_shared_base_prewarm`)。worker 側の `get()` と複製は変えない。D1708 が「次の一手として残す形」と名指しした形で、D2271 (可視 output の写し) と D2284 (発行 child の走査) の次の段にあたる。
2. **floor の `_real_output_snapshot()` 前後 2 回の重複排除 (見送り)**: 段 2 で「cacheable な file は (index blob, path) を行に持つ比較器」を起草したが、段 3 相談が、`git status` が誤って clean と答える状態 (racy clean) と mode 変更の組合せで、現行なら赤の入力を緑にする例と逆の例を構成した (`verbatim/s3-consult-out.md` 所見 1)。受理集合が同値にならないので D1709 に照らして実装しない。受理集合を変えない代案は、11 本を 2 本ずつ xdist group にして process 内 cache を共有する形 (初回 約 37 秒を 5 回分程度減らす、鎖は 約 120〜160 秒) で、評価していない。
3. **active-v2 の emitter memo 迂回の共有 (見送り)**: 実測で 1 本あたり 約 8 秒 × 約 6 本と小さく、key の拡張が `test_t080_shared_base_*` の key 要素数の golden を動かすので実装しない (受理集合・nodeid・成果物 bytes は不変、残る費用は単独走の値で受入では未測定)。

## 4. 共有状態 (やること 3)

- 共有 base は以前から worker 間で共有されている (実装は作り手に controller を足すだけ)。consumer は必ず `copytree` した複製へ書く。
- 新設 `test_t080_shared_base_unchanged_after_consumers_mutate_copies`: 実 git repo を持つ小 builder で base を作り、2 consumer が複製へ tracked 書換え・untracked 追加・commit をした後も、共有 base 自体の全 file の bytes・mode・symlink target と HEAD が構築直後と一致することを固定する。変異 M6 (複製をやめて共有 base をそのまま返す) はこの test と既存の独立性 test 2 本を赤にする (§6)。
- 範囲の限定: 共有 base 自体の改変を hit のたびに検出する機構は無い (段 3・段 6 で「hit ごとに 1.1 GB を読む指紋は短縮を食い、status だけでは ignored の内容を見ない」と判断して足していない)。示したのは「consumer は複製にしか書かない」ことである。

## 5. 失敗時の振る舞い (段 6 と対照で直した)

段 6 の敵対レビュー 2 本がどちらも NO-GO を出し (`verbatim/s6-review-a-out.md`、`s6-review-b-out.md`)、fix 1 巡 (F1、`verbatim/s6-fix1-u1-out.md`) で閉じた (`verbatim/s6-focus-review-out.md`)。その後、対照の実走で実在欠陥が出て fix 2 巡目 (F4、`verbatim/s6-fix2-u1-out.md`) を入れ、新設 test の helper の競合を F5 (`verbatim/s6-fix3-u1-out.md`) で直した。最終形 (`4258b0c76` + F5) の振る舞い:

- 構築 thread は daemon。finish はまず停止 event を立て、合計 900 秒 (構築 1 回の実測 98〜154 秒、受入の T-080 1 本の最大 155〜159 秒の約 5.7 倍) で join し、生きている builder がいれば controller の lock と木を撤去せずに例外を返す (木は /tmp に残りうる)。生きていなければ従来どおり撤去する。
- thread の起動途中の失敗にも同じ上限付き終了を当て、元の起動例外を返す。
- **写しは停止 event まで待ち、写しの遅延・失敗では構築せず静かに終える** (写しの失敗は既存の可視 output の finish が従来どおり送出する)。F4 前は consumer 用の 180 秒上限で待って例外にしていたため、写しが遅い走では T-080 consumer を持たない shard が終了処理で赤になり、受入全体が `report-invalid` になった (対照の 2 走で実測、`docs/failures.md` の新規 F)。
- builder の実行時例外は session 終了時に例外として出る (consumer は `complete.json` が無ければ従来どおり自分で構築する)。
- 残課題 (成果物影響なし、段 6 焦点再レビュー新規 1・2): 起動失敗時の後片付けの例外は捨てられ起動例外だけが残る。起動失敗 test の `Thread.start` 差し替えの範囲が test 全体に及ぶ。

## 6. 変異 matrix (事前登録 → 実走)

事前登録は `verbatim/s4-ruling.md` と `verbatim/s6-ruling.md` の erratum E4〜E8 (いずれも各走の結果を見る前に固定)。harness は `tools/mutation_harness.py`、独立 clone (D1009、main = 対象 commit) に対して計算ノードへ dispatch、runner は 3 file を `-k` で絞る (実 builder を呼ぶ 1 本は最終版で除外)。結果の JSON は `data/mutation-*.json`。

| 変異 | 壊すもの | 期待 (完全集合) | 4258b0c76 (F4 後) | 備考 |
|---|---|---|---|---|
| M1 | configure_node からの起動を外す | T1 | KILLED 一致 | |
| M2 | 写しを待たず即構築する | T2、写し公開前停止 test | KILLED 一致 (c9af2b562 でも KILLED 一致) | F4 前は T2 だけ |
| M3 | controller の lifetime 参加を外す | T3 | KILLED 一致 | |
| M4 | builder の例外を捨てる | T4 | KILLED 一致 | F4 前は T2 も赤 (T2 が伝播に依存していた) |
| M5′ | 可視 output job があれば分岐外でも起動する | T5 | KILLED 一致 | 無条件起動の M5 は実 session 全体を rc=3 にして node 単位の赤にならず再照準 (E5) |
| M6 | 複製をやめ共有 base をそのまま返す | T7、独立性 test 2 本 | KILLED 一致 | 静的導出の期待 2 本は MISMATCH (観測 3 本)、初回 probe と明記して再登録 (E7) |

- T1〜T7 は `test_t080_shared_base_prewarm_publishes_both_keys_before_consumers`、`..._waits_for_visible_output`、`..._controller_participation_keeps_tree`、`..._error_propagates_and_closes`、`..._not_started_when_unselected`、`..._join_timeout_raises`、`test_t080_shared_base_unchanged_after_consumers_mutate_copies`。T6 (hang の上限) は hang 変異になるので登録していない (DW-M06)。
- 6ec6c1f28 (F4 前) でも M1〜M4・M5′・M6 は KILLED 一致だった (`data/mutation-6ec6c1f28-*.json`)。F4 は実装の文面を変えたので新 tip で全 6 本を取り直し、F5 (test helper だけ) の後は置換元の一意性を静的に再確認して M2 だけ取り直した (E8)。

## 7. 同時刻対照 (やること 4)

事前登録: `verbatim/s4-ruling.md`「対照の事前登録」と `verbatim/s6-ruling.md` の erratum E1〜E3・E6・E8 (いずれも各走の結果を見る前)。runner / 集計器は Codex author 製で repo に入れない (job dir `meas/run-pair-ab.sh` sha256 `94c29042…`、`meas/aggregate-ab.py` `b7dab70c…`、自己検査は `verbatim/meas-SELFCHECK.md`)。各対は fresh detached worktree 2 本 (tests の pyc 0、clean、HEAD 照合) から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を同時起動した (起動差 0.001〜0.005 秒)。

| 対 | A / B commit | W0 A / B (秒) | pre0 A / B | ΔT0 (A − B) | ΔT0 / T0(A) | ΔW0 | max(W1,W2) B − A | shard-0 span 最大の差 | 群 A 合計 A / B |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 対 1 (`data/control-pair1-out3-*`) | 4f412c67b / 4258b0c76 | 525.350 / 362.512 | 119.691 / 87.352 | +130.499 | +0.322 | +162.838 | −5.872 | +123.978 | 3045.4 / 2187.1 |
| 対 2 (`data/control-pair2-out4p1r-*`) | 4f412c67b / 7d20b2c1f | 283.538 / 295.224 | 67.715 / 68.728 | −10.673 | −0.049 | −11.686 | +12.738 | −17.319 | 2102.4 / 2194.9 |

- 判定: L1 (2 対とも ΔT0 > 0) 偽、L2 (ΔT0 / T0(A) の平均 ≥ 5 %) 真 (0.136)、L3 (2 対とも max(W1,W2) の悪化 ≤ 20 秒) 真、L4 (2 対とも W0 が悪化しない) 偽。**実装は land しない。**
- 対 2 の B (7d20b2c1f) は対 1 の B (4258b0c76) に test helper の 4 行 (F5) を足しただけで、実装 (`conftest.py`) は同じ。
- 無効にした走 (事前登録どおり、値は判定に使わない。記録は `data/control-invalid-*`): 最初の対 (A の赤 = `test_b5_contrast_launch.py` の時間依存の待ちループ、本 wave の差分は到達しない。runner の shard 対応が専用走に無い field を要求した欠陥も併発し F3 で直した)、次の 2 対 (B が §5 の欠陥で `report-invalid`)、F4 後の対 2 の 1 回目 (B が本 wave の新設 test の helper の競合で赤、F5 で直した)。
- 対 1 と対 2 は別時刻で、対 1 の間は親が変異 job 6 本・別対も流していた (混雑は両腕に同じく掛かる)。混雑が効果を大きく見せた可能性は否定できない。

## 8. 計算の使用量

計算ノードの job Elapse の合計は 18,559 秒 = 5.16 node 時間 (`data/compute-tally.txt`。生死確認 4 本 1,492 秒、焦点走 5 本 996 秒、単独再走 11 秒、対照 6 対 12 走 12,810 秒、変異 43 job 3,250 秒)。ユーザーの承認は途中で 2 回取った (約 2.4、次いで取り直し込み約 4.8)。超過分の主因は、本 wave の欠陥で無効になった対照 3 走と、F4・F5 後の変異の取り直し。これに land 用の縮小受入が加わる。

## 9. 次の一手 (記録のみ、起票しない)

1. 先行構築を collection の短い走でも効かせる: 写しの完成を待たずに構築の前半 (git init・orchestrator の複製・basis 以外) を始める、または構築の最大項 (probe4: 写しの複製 47 秒 (単独走)・`git add -A` 15 秒・発行 child 33 秒) を縮める。効果は今回と同じ 2 対の同時刻対照で、collection の長さを条件として事前登録する。
2. floor official 群の初回 sha256 (1 worker あたり約 37 秒 × 11 本): 受理集合を変えない形 (11 本を 2 本ずつ xdist group にして process 内 cache を共有、鎖 約 120〜160 秒) の効果は未評価。
3. 残課題 (段 6 焦点再レビュー新規 1・2、成果物影響なし): 実装を再び land に掛けるなら、起動失敗時の後片付けの例外の連結と、起動失敗 test の `Thread.start` 差し替えの範囲の限定を足す。

## 10. 確かめたこと・確かめていないこと

- 確かめた: 最忙 worker の item 列と property の付与率 (緑 10 走、82 走の全 junit)。T-080 群・floor 群の時間の内訳 (計算ノードの生死確認 4 本、py-spy 2 本)。実装 (最終 `4258b0c76` + F5) の焦点走 (変更 file と import 側・configure_node 系の 7 file で 420 passed、新設 test を含む小焦点走 36 passed)。変異 6 本 (全 KILLED、期待 node と完全一致、`data/mutation-*`)。同時刻対照 2 対の有効性と L1〜L4。本 wave の実装の実在欠陥 (§5) を対照で検出して直したこと。
- 確かめていない: 対照の各対は n=1 で、効果が collection の長さに依存するという読みは 2 点からの推測 (collection の長さを条件にした対照は取っていない)。混雑が対 1 の効果を大きく見せた可能性。floor の比較器を置換した場合・group 化した場合の実効。active-v2 の emitter 共有の受入での効果 (単独走の 8 秒 × 本数からの外挿のみ)。shard-0 の span と占有の差 (中央値 60.5 秒) の内訳。
- 実装は main に入れていないので、受入の受理集合・test・nodeid・台帳・成果物 bytes は本 wave の land で変わらない。
