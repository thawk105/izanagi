# 小履歴コーパスの未被覆 2 案 (F03・F06) と B06 の分類 G1c を、手で導いた期待値の test にした ([T-2847] の残り (1)、2026-09-23)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-corpus-gaps` (branch `worktree-dev-wave-t2847-corpus-gaps`)、起点 local main `cadaf3805` (開始 gate rc 0、2026-09-23 08:4x JST)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-corpus-gaps/` (brief・裁定・Codex の prompt / 出力・probe の道具・変異台帳の原本)。
設計の正本 = `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §3・§3.1。依頼の逐語 = `verbatim/request.md`。

## 1. 結論

1. 新規 file `orchestrator/tests/test_verifier_corpus_gaps.py` に 3 test を置いた (Codex author、実装 commit `d0ed93bab`)。期待値は設計 §3 の表の「手で導いた辺と判定」をそのまま literal で書き、verifier の出力から写していない (D799)。3 test とも現行 verifier で緑で、**期待と合わない箇所は無かった** (verifier の欠陥は見つかっていない)。
2. 変異 9 件 (対照 1 + 負例 8) を login の自走 probe で観測し、計算ノードの本走 (独立 clone の固定 commit `d0ed93bab`、runner = 新 test file + 既存 `test_verifier.py`) で **9 / 9 が期待 node と完全一致** した (基準走 PASSED)。
3. **新 test だけが検出した変異は M5 (B06) の 1 件**。「wr だけの巡回を G1c にしない」分類器の壊れ方を、既存の `test_verifier.py` 132 test は全部緑のまま通した。既存の分類 test (`test_classify_branches`) は wr と ww が混ざった G1c しか見ていないためである。
4. **F03・F06 型の壊れ方は、既存 test も捕まえた。** 試した 5 形 (M1・M2・M6・M8・M9) はすべて既存 test でも赤になった。既存側で捕まえたのは、凍結した結果 hash と実データ fixture の件数 (M1・M8) と、`test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`・`test_v3_packed_mapping_and_read_bounds` (M2・M6・M9) である。後の 2 test は同じ key を違う版で読む trace を持ち、辺の隣接を具体値で固定している。設計書はこれを「範囲外の版の境界 test」として別の意味に数え、F06 を未被覆とした。**試した壊れ方の範囲では、F03・F06 の test は既存 test に対して新しい検出力を示していない。** 新 test の寄与は、二重読みの意味 (F03 は制約が増えない、F06 は G2) を手で導いた期待値として独立に固定したことである。

## 2. 追加した test (期待値は設計 §3、x = `aa`、y = `bb`)

| test | 履歴 | 固定した期待 | 殺す壊れ方 (設計 §3.1) |
|---|---|---|---|
| `test_f03_same_version_double_read` | T0@v1:W(x)；T1@v2:R(x,v1),R(x,v1) | 辺集合 {0→1}・多重度 1、serializable・certified、`n_edges` 1、`n_reads` 2、巡回 0 | 二重読みで辺を重複して数える |
| `test_f06_different_version_double_read` | T0@v1:W(x)；T1@v2:W(x)；T2@v3:R(x,v1),R(x,v2) | 辺集合 {0→1, 0→2, 1→2, 2→1}、non-serializable、巡回 1 本 {1,2}、G2、2→1 に rw (x, v1 → v2)、1→2 に wr (x, v2) | 二重読みの後の方だけを残す |
| `test_b06_wr_only_cycle_is_g1c` | T0@v1:R(y,v2),W(x)；T1@v2:R(x,v1),W(y) | 辺集合 {0→1, 1→0}、non-serializable、巡回 1 本 {0,1}、**分類 G1c**、巡回辺の理由は wr だけ (0→1 は x、1→0 は y) | 分類器が常に G2 / wr を別種に取り違える |

- 辺集合は、`verify_trace_dir` と同じ本番経路の構築 (`_parse_trace_dir_compact` → `DSG.from_compact` の `adj`) で読む。`VerifyResult` は辺集合を返さないため (段 4 裁定 (P1))。compact parse が legacy 経路へ落ちたら fail する。
- 証拠面は test 内の合成 silo source (X・P の emitter を持つ) に束縛した。`test_verifier.py` は import していない。
- trace は 1 thread file にまとめた v2 frame。temp dir は finally で消す。pytest 無しの自走 runner (`_run()`) を持つ。
- 自走: 親の wave worktree で 3 passed (0.1 秒)。子の自走も 3 passed (`verbatim/s5-author-report.md`)。

## 3. 変異 (事前登録 = `verbatim/s4-ruling.md`、対象 = `orchestrator/verifier/dsg.py`)

| ID | 種別 | 壊し方 | 新 test の赤 | 既存 test_verifier.py の赤 (件数) | 新規の検出力 |
|---|---|---|---|---|---|
| M0 | 対照 | docstring の 1 語だけ | なし | 0 | — (drift 核なし、SURVIVED の検出が生きている) |
| M1 | 負例 | compact 隣接の replay で重複辺を保つ | F03 | 7 | なし |
| M2 | 負例 | packed の読み loop で、同じ key の次の読みがあれば今の読みを捨てる | F06 | 2 | なし |
| M3 | 負例 | `_classify` の G1c を G2 に | B06 | 1 (`test_classify_branches`) | なし |
| M4 | 負例 | 巡回の理由で wr を rw と書く | B06・F06 | 9 | なし |
| **M5** | 負例 (再照準) | `_classify` が G1c を返すのを ww も含む場合に限る (wr だけの巡回は G0 になる) | **B06** | **0** | **あり** |
| M6 | 負例 (再照準) | M2 を「次の読みが違う版のときだけ」に絞る | F06 | 2 | なし |
| M8 | 負例 (再照準) | replay で同じ出力 run 内の重複だけを保つ (task 間の重複は従来どおり畳む) | F03 | 7 | なし |
| M9 | 両層 (再照準) | M6 と同じ壊し方を packed・tuple・legacy の 3 つの読み loop すべてに入れる | F06 | 2 | なし |

- 経緯: 事前登録の M1〜M4 は login probe 1 巡目で全部既存 test にも捕まった (`mutation/probe-1.json`)。DW-M08 (新 test だけが検出する差分を示す) に従い、既存 test が通しそうな形へ再照準したのが M5・M6・M8 (`mutation/probe-2.json`) と M9 (`mutation/probe-3.json`)。M9 は M6 が「packed と tuple の結果の一致」を見る差分検査に捕まったのを避けるため 3 経路すべてに入れたが、既存の 2 test が辺の隣接を具体値で固定していたため、なお赤になった。これ以上の再照準は作為的になるので止めた。**事前登録の 4 件はすべて本走に残し、初回結果を消していない。**
- 単一理由性: 各変異で、新 test 側の赤は狙った test の狙った assert だけだった (M4 は B06 と F06 の両方の理由検査に当たり、どちらも wr を rw と取り違えた証拠。probe の `fail_lines` に assert の値がある)。
- 本走: `tools/mutation_worktree.py` を独立 clone (`<job dir>/mutation-source`、main = `d0ed93bab`) に当て、`--runner-mode dispatch --detached`、runner = `tools/run_tests.py --force-dispatch orchestrator/tests/test_verifier_corpus_gaps.py orchestrator/tests/test_verifier.py -q -rf`。spec sha256 = `bfaaf23e8dd098fc2da304259925bf5f4a06cd94f7d5932d4e242339ac48bc91` (`mutation/mutation-spec-final.json`)。summary = KILLED 8・SURVIVED 1・MISMATCH 0 (`mutation/mutation-final-results.summary.json`、原本 305,580 bytes は job dir に残し sha256 で束縛)。runner 時間は基準走 28.9 秒 + 変異 9 本 計 264.5 秒 = 293.4 秒 (collection の dispatch は別)。
- 期待 node は login の自走 probe (注入 → 自走 → 原 bytes へ復元し sha256 と `git status` 空を照合) で集めた。probe の道具 (`login_probe.py`・`make_final_spec.py`・`summarize_results.py`) は job dir にだけ置き、repo には入れていない。

## 4. 限界・言わないこと

- 「新しい検出力なし」は、試した 5 形の壊れ方についての実測である。F03・F06 の test が既存 test では捕まらない壊れ方を持たないことは示していない。
- 既存 test の期待値の多くは verifier 自身の出力か、実装の 2 経路の一致である (D799 の独立性の区別)。新 test の期待値は手で導いたものだが、変異の結果だけからは「独立の期待値であること」の価値は測れない。
- 本 wave は verifier・既存 test・fixture を変更していない。gate・検査・台帳は足していない。
- 残りの (2) 変異の実走・(3) 容量の実測・(4) si の v2 化は別 wave の担当である。
