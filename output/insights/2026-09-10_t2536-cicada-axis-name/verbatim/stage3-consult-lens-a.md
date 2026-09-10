## 1. refuted — P1 の逆写像は D1864 が却下した両名 alias ではない

- file:line: `plan.md:113-135`、`rulings-d1863-d1864.md:42-50`、`orchestrator/calibrator/cli.py:429-459`
- 反例または変異: cicada の旧名 `CCBENCH_INLINE_VERSION_OPT` は、候補軸を正方向へ戻すと `CCBENCH_INLINE_VERSION_OPT_CICADA` になり不一致で拒否される。新旧両 token を入れても旧名の処理時点で拒否される。逆に新 scoped 名だけは exact 逆引きされる。計画どおりなら両方が通る反例は構成できない。
- 現行コードは旧汎用名をそのまま `INLINE_VERSION_OPT` として受けるため、受け手変更は既存の偽 genome 受理を閉じる変更でもある。
- 成果物影響 1 行: 旧汎用名による偽 cicada genome は消え、正しい scoped 名だけが canonical genome に写る。

## 2. real — 「双射」の前提を検査しておらず、2 軸が同じ cache 変数へ潰れても照合が通る

- file:line: `brief.md:39-41`、`plan.md:115-135,169-184`、`external/ccbench/cc/cicada/CMakeLists.txt:5-6`
- 反例または変異: CCBench の `INLINE_VERSION_PROMOTION` も `${CCBENCH_INLINE_VERSION_OPT_CICADA}` を読むよう変更し、Izanagi 表の同軸も同じ cache 名へ合わせる。CCBench 解析表と静的表は exact equality のまま通るが、producer は同じ `-DCCBENCH_INLINE_VERSION_OPT_CICADA` を異なる値で二度出す。逆写像も一意にできない。
- これは左右の対応が一致しているだけで、protocol 内の cache 名が injective かを検査していないためである。
- 成果物影響 1 行: canonical genome は 2 軸の異なる値を記録できる一方、コンパイラには後勝ちの 1 値しか届かず、選択・レポート・台帳が偽の variant を参照する。

## 3. real — 軸集合については CCBench 側が `SPACES` に射影され、独立実体になっていない

- file:line: `plan.md:169-184,190-197`、`orchestrator/campaign/genome.py:172-204`、`external/ccbench/cmake/Options.cmake:33-34`、`external/ccbench/cc/cicada/CMakeLists.txt:8-9`
- 反例または変異: `CICADA_SPACE` から `WRITE_LATEST_ONLY` を落として、意図的に除外されている `SINGLE_EXEC` を追加し、静的対応表も同じように置換する。軸数は 17 のまま、非恒等写像も cicada の `INLINE_VERSION_OPT` だけである。両 cache 変数は CCBench に実在するため、`SPACES` の軸だけを解析する計画の比較は通る。
- 検査は cache 名については 2 実体だが、「どれが genome 軸か」については Izanagi 側だけを見ている。
- 成果物影響 1 行: certified 選択は `WRITE_LATEST_ONLY` を失い、測定対象自体を変える `SINGLE_EXEC` を軸として記録する。

## 4. 判定不能 — 新 CMake parser が重複 mapping を拒否するか未定義

- file:line: `plan.md:154-184`、`orchestrator/campaign/source_digest.py:639-718,784-862`
- 反例または変異: cicada `OPTIONS` に二本目の `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_PROMOTION}` を追加する。新 helper が辞書化時に先勝ちなら検査は通るが、実際の compile definitions は同じ TU マクロを二度供給する。
- 既存 `_parse_supplied_macro_details()` は同一左辺の異なる cache 名を拒否するが、計画は新 parser に同じ拒否を明記せず、既存 parser の再利用も決めていないため判定不能。
- 成果物影響 1 行: 見逃した場合、受領証の genome 値とコンパイラで最終的に有効な値が分離する。

## 5. 判定不能 — 値取り違え検査が軸間 swap を捕捉する入力か不明

- file:line: `plan.md:190-201`、`orchestrator/campaign/model.py:61-63`
- 反例または変異: `INLINE_VERSION_OPT` の出力値だけを `REUSE_VERSION` から取る。0/1 ケースで全軸を同じ値にした genome を使うと通るが、非対称な genome なら落ちる。
- 計画は 0 と 1 の個別期待を記すだけで、他軸と異なる値を同時に置く fixture を明記していない。
- 成果物影響 1 行: 見逃した場合、レポートは `INLINE_VERSION_OPT=1,REUSE_VERSION=0` と記録しても実バイナリには逆の値が届く。

## 6. refuted — 片側 rename と既存の四つの拒否は計画上維持される

- file:line: `plan.md:169-199`、`orchestrator/calibrator/cli.py:383-464`
- 反例または変異:
  - CCBench 側だけの cache rename、Izanagi 宣言側だけの rename、cicada 非恒等 entry の protocol 取り違えは exact pair 比較で落ちる。
  - `missing_axes`: scoped 名を論理軸へ戻した後も、別軸を一つ欠けば `cli.py:455-460` で落ちる。
  - duplicate define: 同じ scoped 名を二度入れれば、逆変換後の同じ論理軸が `cli.py:440-443` で落ちる。
  - build argv define: 逆変換より前の `cli.py:425-428` で落ちる。
  - TRACE: 表外の恒等逆写像で `TRACE` のまま残り、欠落・非 0 は `cli.py:446-450`、重複は duplicate 検査で落ちる。
- 成果物影響 1 行: これらの負例では現行どおり受領証が拒否され、certified 成果物は生成されない。

## 7. real — build 経路で値が実際にコンパイラへ届くことは新検査の対象外

- file:line: `plan.md:169-186`、`orchestrator/campaign/condition_meaning_gate.py:4-21,2191-2208`
- 反例または変異: `ProtocolHelpers.cmake` が protocol `OPTIONS` を `target_compile_definitions` へ渡さないよう変わっても、新 helper は `Options.cmake` と protocol `CMakeLists.txt` だけを解析するため、静的対応表との照合と producer 単体検査は通る。
- 既存 condition gate は emitted compile command まで確認する先例だが、その supply domain は patch-derived define であり、cicada genome へ拡張するのは本 wave の scope 外である。
- 裁定パッケージ候補: 完了主張を「CMake source 上の cache-name 契約を修正した」に限定するか、別 wave で owner TU の compile command まで証明するかを選ぶ。現 wave へ汎用 gate を黙って追加しない。
- 成果物影響 1 行: downstream propagation が壊れた場合、検査は緑でも binary は既定値となり、選択・レポート・台帳は未供給値を genome として記録する。

## 8. real — P3 は実装範囲としては妥当だが、完了能力を言い過ぎている

- file:line: `brief.md:3-8,20-22,30-31,43`、`plan.md:226-232,251-257`、`rulings-d1863-d1864.md:31-36`
- 反例または変異: producer を直しても公式 launcher に cicada の枝はなく、live cicada driver もないため、公式経路から cicada の認定 record は作れない。
- 依頼逐語は mapping 修正と drift 検査を求める前提記述であり、同 wave で whitelist を広げる指示ではない。したがって launcher を編集しない判断は正しいが、「認定の対象にできるを満たした」は「その前提を一つ除去した」と書くべきである。
- 成果物影響 1 行: 本 wave 後も公式経路の cicada certified 選択・レポート・台帳は 0 件のままである。

## 9. refuted — P2、P4 と高位 API の制約認識は正しい

- file:line: `brief.md:42-44`、`plan.md:76-91,273-274`、`orchestrator/campaign/source_digest.py:85-94,840-862,1994-2068`
- 反例または変異: 対応表を CCBench source から実行時生成すると 2 実体を失うが、計画は静的表とテスト時解析を分離している。`model.py` は `genome.py` を import せず、既存方向は `genome.py → model.py` なので循環もしない。
- 親の「高位 resolver は cicada に使えない」も、`EVOLVE_BLOCK_SOURCE_PROTOCOLS` に cicada source がなく `_source_protocol()` が未知 source を拒否するコードと一致する。
- 成果物影響 1 行: この設計部分による runtime submodule 依存や import failure は生じない。

## 10. 判定不能 — 親の「他 3 protocol は全軸恒等写像」は射影内で再検証できない

- file:line: `parent-measurements.md:7-15`、`plan.md:49-73`
- 反例または変異: silo、mocc、tictoc のいずれかに未報告の非恒等 RHS があれば、literal 表は既存認定 protocol の argv を誤る。
- 許可された射影には各 protocol の `CMakeLists.txt` がなく、親の実測結果以上の独立判定はできない。段 5 の source 解析検査が実ファイルを読むまでは確定不能。
- 成果物影響 1 行: 前提が誤っていれば既存 protocol の certified genome と binary の参照関係が変わる。

## 総括

- must-fix: protocol 内の cache 名一意性と、重複 TU mapping の拒否を検査契約へ明記する。
- must-fix: `SPACES` から独立した意図軸集合を固定し、`WRITE_LATEST_ONLY → SINGLE_EXEC` の置換を落とす。
- must-fix: P3 を「認定可能化の前提修正」に限定し、実 compile command 層は別裁定とする。実走はしていない。