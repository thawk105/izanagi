# [T-1441] 単位3 B1実装のD574決定(3)監査 — macro名不一致バグの発見と修正 (2026-08-20)

## 一言で

T-338単位3 (`orchestrator/submission_gate/_semantic_validator.py`、entry724で本日land済み) の
B1実装 (`_validate_compile_legs`、CMakeCache検査) は、D574決定(3)「validatorは申告値と独立に、
schemaのargvに現れるmacro定義・compile_commandsの当該TUの実compile argv・実ファイル上の
raw CMakeCache.txtを再読して三者を比較する」の**三者比較という構造は実装していたが、
compile_commands脚が実際のCCBenchビルド出力と一致しないmacro名を検索しており、正当な受領証を
含め常に拒否する実装バグを持っていた。** 本waveで修正し、実際にD574決定(3)を満たす状態にした。

## 経緯

1. ユーザー裁定2026-08-20 Q-B=択(a)により、単位3のB1実装が本日landしたばかりのD574決定(3)を
   満たすか、別waveとして直ちに監査することになった (一次資料
   `output/insights/2026-08-20_t338-unit5-d574-conflict/package.md` Q-B節)。
2. 親が直接 `_semantic_validator.py` を読み、`_validate_compile_legs` (1030-1114行) が
   schema argv脚・compile_commands脚・raw CMakeCache脚の3脚照合を実装していることを確認。
   schema (D282 pin、`receipt-schema-v1.json`) が `cmake_cache_record` サイドカーを
   `additionalProperties:false` で拒否し、shape検査が semantic検査より必ず先に走ることも確認し、
   「満たしている」という暫定結論(P1)に達した。
3. 段2 read-only codex (独立監査) が親の結論を追認しつつ、`ReceiptSchema.__post_init__` が
   documentの再ハッシュをしない潜在的境界を新規発見 (production caller 0件のため今回は対応不要
   と判定)。
4. 段3敵対相談2レンズのうち、正しさ境界レンズ (レンズA) が「実CCBenchの compile_commands.json
   のmacro名は`TRACE`/`ADD_ANALYSIS`であり、validatorが検索する`CCBENCH_TRACE`/
   `CCBENCH_ADD_ANALYSIS`とは一致しない」という決定的な所見を発見。親が
   `external/ccbench/cmake/Options.cmake`/`ProtocolHelpers.cmake` を直接読み、確定させた。

## 確定した事実 (バグの実体)

- `external/ccbench/cmake/Options.cmake:60-69` の `ccbench_universal_definitions` は、CMake
  キャッシュ変数 `CCBENCH_TRACE`/`CCBENCH_ADD_ANALYSIS` を `TRACE=`/`ADD_ANALYSIS=` という
  プレフィックスなしの名前へリネームする (コメント: 「maps each CCBENCH_FOO into a
  target-private `-DFOO=<value>`」)。
- `external/ccbench/cmake/ProtocolHelpers.cmake:29,41-43` の `ccbench_add_protocol` が
  これをそのまま `target_compile_definitions` 経由でコンパイラへ渡す。
- したがって実際の `compile_commands.json` には `-DTRACE=`/`-DADD_ANALYSIS=` が現れ、
  `-DCCBENCH_TRACE=`/`-DCCBENCH_ADD_ANALYSIS=` は決して現れない。
- 旧実装 (`_semantic_validator.py:1057,1059`) は `_macro_value(argv, "CCBENCH_TRACE", ...)`/
  `_macro_value(argv, "CCBENCH_ADD_ANALYSIS", ...)` を呼んでいたため、実際のCCBenchビルドに
  対しては compile_commands 脚が常に拒否する状態だった (D509裁定パッケージV1が言及した
  「semantic validatorを常時拒否 (受理集合が空)」の状態そのもの)。
- configure argv脚 (CMake configureコマンドライン形式、`cmake -S . -B build -DCCBENCH_TRACE=0`)
  は `CCBENCH_` プレフィックス付きが正しく、そちらは無改修で正しかった。
- 同じ `_semantic_validator.py` 内の `_OPT_PARAMETER_KEYS`/`_EXPECTED_OPT_PARAMETERS`
  (118-143行、`ShowOptParameters()` ログ検証用) は、既にプレフィックスなしの正しい命名
  (`ADD_ANALYSIS` 等) を使っており、CCBenchの実出力形式についての正しい理解が同ファイル内に
  既存していた。
- `orchestrator/tests/test_t338_submission_gate_unit3.py` の全13箇所 (compile_commands文脈の
  5箇所、configure_argv/CMakeCache文脈の8箇所) を grep実測。compile_commands文脈の5箇所全てが
  例外なく実CCBenchと異なる `-DCCBENCH_TRACE=` 形式を合成していたため、単位3 land時の変異matrix
  (baseline PASSED・11/11 KILLED) やテストスイートはこのバグを検出できなかった。

## 修正内容

`orchestrator/submission_gate/_semantic_validator.py:1057,1059` の `_macro_value` 呼び出し
macro名を `"CCBENCH_TRACE"`→`"TRACE"`、`"CCBENCH_ADD_ANALYSIS"`→`"ADD_ANALYSIS"` に変更
(compile_commands脚のみ、configure argv脚・raw CMakeCache脚は無改修)。対応する
`test_t338_submission_gate_unit3.py` のcompile_commands側fixture5箇所を実CCBench形式へ修正。

## 検証

- 段6敵対レビュー2本 (裁定準拠監査レンズ・回帰境界条件レンズ) はいずれもreal所見なし。
- `python3 tools/run_tests.py orchestrator/tests/test_t338_submission_gate_unit3.py -q` =
  39 passed。
- 変異matrix (`tools/mutation_worktree.py`、固定commit使い捨てworktree):
  baseline PASSED (39 passed)、2件登録 (M1: TRACE macro名revert、M2: ADD_ANALYSIS macro名
  revert)、2/2 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。各変異の失敗nodeは事前登録した6件
  (`test_semantic_validator_accepts_complete_performance_receipt`他) と完全一致。単一理由性を
  実測確認 (M1単独probeでも同じ6件、コード構造 — 各macroチェックが独立したif文で
  `_macro_value`が値欠落時に即座に例外を投げる — から論理的に導出される結果と一致)。

## 副次的所見 (今回のfix scope外、記録のみ)

1. **`correctness_evidence.minItems:0` によりcorrectness側三者比較 (trace=1/analysis=1) が
   未実行になりうる経路が既存契約として実在する。** §7.1(1) は検証attemptがcompletedのときだけ
   6件必須、失敗stageは0〜5件許容という既存承認済み設計 (D574以前から存在) であり、D574決定(3)
   自体の欠陥ではないと判断した (段3レンズA=refuted、レンズB=real、親裁定はレンズAを採用)。
   ただし「validatorが存在するcorrectness compile recordを常に検査する」という広い実効性の
   限定として記録する。
2. **`ReceiptSchema.__post_init__` (`_receipt_schema.py:34-43`) がdocumentの再ハッシュを
   しない。** 同じ ref/sha256 で偽documentを直接渡す `ReceiptSchema(...)` 構築が理論上可能。
   production callerは現状0件 (`_validate_receipt_semantics` の呼び出し元は
   `_semantic_validator.py:2646` とテストのみ、`load_schema`経由のロード以外に直接構築する
   productionコードは存在しない、grep実測で3者独立に確認)。統合(単位6)前にhardeningすべき
   対象としてbacklog。
3. **D509(5)とD574(3)の意思決定系列間reconciliation不足。** T-139系列(D574/K系列)とT-338系列
   (D509 6分割)が同じ実装面(writer・validator・vector・manifest)を指しながら相互参照していない
   状態は、`package.md` (Q-C) が既に指摘済み。本waveの結果 (D574(3)がD509(5)より厳しい要件で、
   単位3の実装は結果的に両方を満たす修正になった) は、Q-Cのreconciliation decisionを起こす際の
   追加材料になる。

## 成果物影響

certified選択・材料レポート・proof chain・凍結bytes・受理集合は本wave時点では不変
(単位3/4は単位6統合commitまでtop-level APIへ未export、D509決定7の意図的段階設計)。ただし
単位6が配線された後にこの修正が入っていなければ、D574決定(3)が要求する三者比較は実際には
機能せず、CCBenchの正当なビルドを一律で拒否する (受理集合が事実上空になる) 状態のまま統合
されていた。今回の監査・修正は、その将来のギャップを事前に閉じたものである。
