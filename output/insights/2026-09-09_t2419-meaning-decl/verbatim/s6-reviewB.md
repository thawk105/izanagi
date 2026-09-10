## 読んだもの

指定された一次資料 9 件を確認した。

- `s4-adjudication.md`
- `s5-author-out.md`
- `s5-impl.diff`
- `backoff_sweep.py`
- `backoff_extended_sweep.py`
- `backoff_overthrottle.py`
- `backoff_profile.py`
- `backoff_repro.py`
- `backoff_requested_us.py`

追加で、関連 consumer test、`condition_meaning_gate.py`、`screening_driver.py`、`condition_gate_test_support.py`、`s1_known_axes_freeze.py`、凍結 JSON、acceptance ledger、B10 shape driver、実 patch、T2228 probe を静的に確認した。

`rg` による caller 全数調査、`git diff --check`、変更 7 file の AST parse は成功。pytest は指示どおり実走していない。

## 呼び出し面の表

`E(a) = encode_static_backoff_us(a)` とする。

| driver | 要求する非負値 | 渡す写像 | intent の出所 | 一致するか |
|---|---|---|---|---|
| `backoff_sweep.py` | 通常は `SWEEP_US={2,5,10,25,50,100}`。最小 screening は `{screening_fixed_us}` | `{a:a}` を実際の `gs` で絞る | a。物理格子は `SWEEP_US` (`backoff_sweep.py:60,240-249`) | 一致。`gs` の絞り込み後に同じ `gs` で写像を絞る (`:376-386,425-441`) |
| `backoff_extended_sweep.py` | run kind ごとに `E(EXTENDED_SWEEP_US)`、`E(T2266_REALIZED_US)`、`E(T2418_REALIZED_US)` | `{E(a):a}` | a。3 個の物理格子 (`backoff_extended_sweep.py:55-58,87,93`) | 一致。run kind が genomes と物理格子を同時選択し (`:1342-1363`)、同じ組を gate へ渡す (`:1368,1418-1427`) |
| `backoff_overthrottle.py` | imported extended references の `E(EXTENDED_SWEEP_US)` | `{raw:_point_backoff_us(point)}` | b。`decode_static_backoff_us` 由来 (`backoff_overthrottle.py:96-100`) | 一致。要求と写像を同じ `diagnostic_points` から作る (`:66-80`)。独立格子を持たない継承 consumer なので裁定どおり正当 |
| `backoff_profile.py` | 全走 `{2,5,10,25,50,100}`、単一点なら `{a}`。`None` は `-1` | `{a:a}` | a。`BACKOFF_US` と `amounts` が物理量 (`backoff_profile.py:74,931-974`) | 一致 (`:344-364`)。全点・単一点の双方で同じ `amounts` を要求と写像に使用 |
| `backoff_repro.py` | `{5,10}` | `{raw:raw}` | a。`ORIG.best_us` と物理集合 `{5,10}` から point を直接構築し、wire encode を挟まない (`backoff_repro.py:51-56,92-99`) | 一致。写像も同じ `points` から作る (`:72-85`) |
| `backoff_requested_us.py` | fixed gate は production で `-1` のみ。diagnostic gate は `BACKOFF_FIXED` 自体を要求しない | 両方 `{}` | 該当なし。非負要求なし | 一致。reference 全集合を検査後、adaptive `BACK_OFF=1, BACKOFF_FIXED=-1` を一意選択 (`backoff_requested_us.py:661-679`)。2 gate は `:110-140` |

helper 自身は、要求された非負 key 集合と写像 key 集合を capture 前に完全一致検査する (`backoff_sweep.py:108-156`)。production を過剰拒否する経路は静的には確認されなかった。

## 所見

所見 1: 実装子の consumer・所有外 caller 列挙が不完全

根拠:

- 実装報告の列挙は `s5-author-out.md:54-57`。
- 実 helper を通る最小 screening test がある (`orchestrator/tests/test_screening_opt_in.py:85-162`)。
- full/minimal sweep を実 helper で通す compiler-binding test がある (`orchestrator/tests/test_t1416_backoff_compiler_binding.py:76-148,173-307`)。
- 所有外 probe が変更された repro wrapper を呼ぶ (`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:923,953`)。
- 共有 fixture の実体化 helper は `orchestrator/tests/condition_gate_test_support.py:145-209`。実 decoder は `supplied/include/backoff.hh` からコピーされるため、新しい意味宣言でも構造上は成立する。

失敗シナリオ: 親が実装子の申告だけを focus 集合として採用すると、screening、compiler-binding、T2228 liveness の回帰を確認せず完了判定する。

成果物影響: 現差分で誤った計測成果物を作る欠陥は確認していないが、未列挙経路の回帰時には campaign または liveness 証拠が生成前に停止する。

深刻度: nit

所見 2: 2 個の monkeypatch wrapper test が新しい intent 引数を直接固定していない

根拠:

- overthrottle test は `macro_values` のみ検査し、`backoff_fixed_physical_us` を検査しない (`test_backoff_overthrottle.py:54-73`)。
- requested-us test も両 macro と `stock_root` のみ検査し、空写像を検査しない (`test_backoff_requested_us.py:732-752`)。
- extended の forwarding test も `configure_args` だけを検査する (`test_backoff_extended_sweep.py:936-955`)。ただし raw `3000` → physical `1000` は新しい実 helper test が別途検査する (`test_backoff_sweep.py:179-202`)。
- 現行 production 配線自体は正しい (`backoff_overthrottle.py:76-80`, `backoff_requested_us.py:121,138`)。

失敗シナリオ: 将来、stub が受ける keyword を欠落・誤配線しても wrapper test 単体は green のままになり、実 production だけが `TypeError`、key mismatch、または meaning mismatch で停止する。

成果物影響: 現差分ではなし。回帰時は overthrottle manifest または requested-us rep/manifest が生成されない。

深刻度: nit

F718 同型事故の停止点も確認した。物理 intent は declaration bits へ変換され (`backoff_sweep.py:143-154`)、実 decoder の観測と比較され (`:178-205`)、red は build・measurement 前に例外になる (`:206-215`)。raw `1000` → intent `1000` が観測 `0.0` となる負例も production helper 経由で固定されている (`test_backoff_sweep.py:205-244`)。

各 production 順序は、sweep `backoff_sweep.py:425-463`、extended `backoff_extended_sweep.py:1418-1429`、overthrottle `backoff_overthrottle.py:423-430`、profile `backoff_profile.py:384-395,931-976`、repro `backoff_repro.py:70-89,171-172`、requested-us `backoff_requested_us.py:1087-1113` で gate が build/measurement より前にある。

blocker、must-fix は確認されなかった。

## consumer 波及

変更で既存期待値を変更する必要があった test は 1 件だけで、対応済み。

- `test_backoff_sweep.py::test_real_family_helper_admits_effective_define_and_recomputes_file_digest` は `unestablished` から `green/declared-meaning-observed` と空の `unestablished_meaning_macros` へ変更 (`test_backoff_sweep.py:145-176`)。

新規 node は 3 件。

- `test_real_family_helper_observes_raw_3000_as_intended_static_1000`
- `test_real_family_helper_rejects_f718_intent_and_evaluator_records_red`
- `test_family_helper_rejects_physical_intent_contract_before_source_capture`

`rg '_require_backoff_condition_gate\s*\('` は 15 箇所、うち定義 1・呼び出し 14。production 7 呼び出しと `test_backoff_sweep.py` 内 7 呼び出しのすべてに必須 keyword がある。wrapper の外向き signature は変わっていないため、extended、profile、overthrottle、repro、requested-us の wrapper caller に引数追加は不要。

指定された consumer の状態:

- `test_backoff_extended_sweep.py`: 実 wrapper、partial point、run kind 3 種の経路を確認。期待値変更不要。
- `test_backoff_overthrottle.py`: wrapper は monkeypatch 経由。現行配線は正しいが写像 assert はない。
- `test_backoff_consumers.py`: repro の gate-before-yield 順序だけを静的検査 (`:395-405`)。期待値変更不要。
- `test_screening_opt_in.py`: 実 helper を通るが実装報告から漏れている。最小集合 `{-1,100}` と `{100:100}` は一致する。
- `test_p2_2_site_aware.py:376-515` と `test_t1416_backoff_compiler_binding.py:76-307` も実 helper consumer。
- `test_condition_meaning_gate.py` は変更 helper の直接 caller ではなく、下位 evaluator 契約の consumer。

## pin 閉包

変更 file のうち、bytes pin の path として見つかったのは `orchestrator/campaign/backoff_sweep.py` だけだった。他の変更 6 file は、確認した凍結 JSON に exact source path record がない。

path 側:

- `output/s1-freeze/known_axes_freeze.json:152-154,378-380,604-606`
- `output/s1-freeze/measurement_freeze.json:171-173,443-445,715-717`
- `output/s8b-freeze/holdout_freeze.json:157-159,424-426`

key 側はいずれも `_BASE and SWEEP_US` だが、実装は key 部分だけでなく file 全 bytes を hash する (`s1_known_axes_freeze.py:207-214,879-889`)。従って今回の helper 編集も hash に波及する。

記録 hash は `4e7fa96e...`、差分前 `HEAD` は `1b64f897...`、現在の worktree は `1f852a5b...`。つまり今回の差分で hash は再度変わるが、差分前から既に記録値と不一致であり、新しい赤ではない。凍結再発行をしない裁定と整合する。

holdout trust root が pin する `known_axes_freeze.json` 自体の hash は `354f4b87...` で、現 file bytes と一致しており今回不変 (`holdout_freeze.json:9-11`)。

acceptance ledger:

- 既存 node `test_real_family_helper_admits_effective_define_and_recomputes_file_digest` は登録済み (`acceptance_duration_ledger.json:3393`)。
- 新規 3 node はすべて未登録。
- ledger は完全一致でなく、全 collection の 90% 以上を要求する (`test_acceptance_schedule_order.py:660-716`)。記録 node 数は 22155 (`acceptance_duration_ledger.json:22159`)。
- 3 node の追加だけで hard failure と断定できる契約ではない。ただし正確な coverage と更新後所要時間は pytest collection 未実走のため親確認が必要。

## 裁定候補

既裁定済みの scope 外残件が 2 件ある。新しい裁定候補は確認していない。

- generic screening は今も declaration を常に `None` として meaning を `unestablished` にする (`screening_driver.py:219-227`)。単独で raw `1000` を扱う generic 経路は本変更では止まらない。ただし backoff sweep 自身は先行 family gate が支配するため止まる。S4 の B2 scope 外裁定どおり。
- T2418 report の固定文字列は今も `unestablished_for_positive...` (`backoff_extended_sweep.py:99-101`) で、report へ複数箇所から出力される (`:660,1181,1288`)。再走時の実態とは古くなるが、S4 の B3 scope 外裁定どおり。
- B10 shape driver は新 helper を通らないが、独立した encode/decode 閉集合 (`b10_backoff_shape_sweep.py:782-817`) と applied-tree・物理 residual 検査を持つため、未防護の F718 経路とは分類しない。

## 総括

6 driver の intent は裁定どおりで、decode 由来は overthrottle だけだった。  
完全一致検査で production を止める部分集合・run kind・単一点経路は見つからなかった。  
F718 同型事故は 6 driver では build/measurement 前に停止する。  
blocker / must-fix はなし。consumer 列挙漏れと wrapper assert 不足を nit 2 件とした。  
pytest 未実走のため、ledger coverage と実 test 成否は親確認が必要。