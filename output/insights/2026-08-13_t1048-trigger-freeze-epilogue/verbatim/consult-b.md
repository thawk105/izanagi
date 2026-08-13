### 所見1 — R2 は prologue と reason 状態から迂回できる

- 主張: `END + epilogue` の逐語一致だけでは、gate の意味は固定されない。
- 根拠: `plan.md:43-58` は BEGIN 前を検査せず、patch の prologue は `patches/silo-backoff-trigger-gating-variant.patch:79-111`。例えば次の差分は block と epilogue を一切変えない。

```diff
 #if BACKOFF_TRIGGER_GATING
-  bool izanagi_gate_pass = true;
+  struct GatePass {
+    GatePass& operator=(bool) { return *this; }
+    explicit operator bool() const { return false; }
+  } izanagi_gate_pass;
 #endif
```

  pristine の `izanagi_gate_pass = true;` も、32 個の hole も no-op になり、epilogue の `if` は常に false になる。

  さらに、BEGIN 前へ次を挿入しても同じく通る。

```diff
 #if BACKOFF_TRIGGER_GATING
   bool izanagi_gate_pass = true;
+  izanagi_abort_reason_ = IzanagiAbortReason::kUnset;
 #endif
```

  `emit_predicate` は全 predicate に `kUnset` を含める (`reflux_ir.py:131-141`)。

- 影響: mask を主張しても、実バイナリが常時 backoff または常時 no-backoff になる。R2 の実効意味は未閉鎖。
- 推奨 (must-fix): prologue と reason producer を別途凍結・検査するか、「quarantine 済みの正規 skeleton に限る」と主張を狭める。

### 所見2 — P1 は emitter の構文事実を意味論へ一般化している

- 主張: P1 の「無条件代入だから prologue 不要」は、通常の `bool` lvalue という未記載前提に依存する。
- 根拠: `reflux_ir.py:131-141` は確かに単一代入を出力するが、型、lvalue の同一性、`izanagi_abort_reason_` の状態は保証しない。pristine の `true` 代入も同じ前提に依存する。加えて gate 対象は 8 要因中 5 要因だけ (`axis_trigger_gating.py:68-76`)。
- 影響: 現行 YCSB では隠れても、`kInsertNode` / `kScanNode` の abort では全 mask の predicate に該当項がなく、将来 workload で意味が崩れる。
- 推奨 (nit): P1 を「正規の primitive bool と現行 5 要因に限る」と明記する。将来要因の意味論は scope 外の裁定候補。

### 所見3 — `FileNotFoundError` は新検査を完全に迂回する

- 主張: source が無い場合、epilogue 検査へ到達せず黙って受理される。
- 根拠: `build_admission.py:169-177` の `FileNotFoundError: return`。この挙動は `test_build_admission.py:464-477` でも正例として固定され、plan も `plan.md:110-119` で維持している。検査の挿入位置自体は pristine return より前 (`plan.md:43-58`) なので、問題はこの早期 return である。
- 影響: partial checkout、source 消失、receipt 由来の未実在 `source_root` では、拡大後の保証を表示上だけ受けられる。通常の `buildcache` は後段再照合で止まるため、これ単独で certified build bypass とまでは断定しない。
- 推奨 (must-fix): admission を standalone gate と呼ぶなら、axis 対象の ENOENT は拒否し、stock/non-trigger の「対象外」と source 不在を分離する。

### 所見4 — 検査未到達経路は存在するが、既知の非認証面である

- 主張: 標準の admitted build 経路では gate 呼出し漏れは見つからない。一方、診断 build と resume は gate 外である。
- 根拠: `pipeline.py:768-798`、`buildcache.py:1273-1277` / `1538-1542`、`s8a_trigger_coverage.py:135-165` は gate を呼ぶ。対して `s2_verify_calibration.py:247-278`、`s3_lock_coverage.py:142-168`、`s5_permutation_coverage.py:138-164` は直接 CMake を呼び、`materializer_admission.py:50-65` で明示的に `non-admissible` とされる。S8b resume は binary hash だけで、admission receipt を束縛しない (`s8b_floor_campaign.py:46-48`, `3688-3721`)。
- 影響: これらを certified build や proof chain の入力に流せば、R2 検査は発火しない。
- 推奨 (scope 外): 非認証診断として扱い続け、S8b binary と admission receipt の束縛は RP-4 相当の裁定パッケージへ分離する。

### 所見5 — 変異の単独帰属は core 検査では成立するが、既存負例は証拠にならない

- 主張: epilogue exact 検査と直結重複検査には、それぞれ単独帰属できる変異がある。ただし既存の frame/hole 負例を kill 証拠にしてはいけない。
- 根拠: `B0 + 改変 E` は block 検査では見えず、`B0 + E + E` も最初の E 検査だけでは通る (`plan.md:187-196`)。一方 `test_build_admission.py:540-551` は自ら「gate 単独変異の kill 証拠には数えない」としている。
- 影響: 既存の malformed block テストだけで新検査の検出力を報告すると、帰属が不成立になる。`E` 後を受理する正例は過剰拒否の回帰検査であり、拒否検査の mutation kill ではない。
- 推奨 (nit): canonical block + bad epilogue を `derive_build_admission` へ直接渡す mutation case を別登録する。core の新拒否条件自体には冗長検査は見当たらない。

### 所見6 — brief の純増検出力の経路分類が誤っている

- 主張: quarantine が候補挿入中心という説明は概ね正しいが、S8b と S-1 extime を「quarantine 非経由」とする具体化は誤り。
- 根拠: S-1 extime は明示的に quarantine を通る (`s1_verify_extime_calibration.py:341-364`)。S8b floor は `prepare_cell` を使う (`s8b_floor_campaign.py:3185`, `3414-3418`)、S8b oracle も同じ (`s8b_oracle_driver.py:1270-1271`, `1433-1437`)。trigger configuration の `prepare_cell` は `p3_s4_loop.quarantine` を呼ぶ (`s1_direct_comparison.py:563-603`)。また `pipeline.py:74-105` は diff quarantine ではなく hole binding 検査である。
- 影響: 新検査の純増検出力、変異対象、成果物影響を過大評価する。
- 推奨 (must-fix): brief/plan の経路表を修正し、真に quarantine 非経由の characterization/pristine 経路と、S8b/S-1 の quarantine 済み経路を分ける。

### 所見7 — 直結重複検査は狭い検出力しかなく、R2 の証拠にしてはいけない

- 主張: `E + E` 拒否は arbitrary post-epilogue code を凍結しない。
- 根拠: `plan.md:47-58`, `131-147` は E 直後の完全重複だけを見る。次の追加は通る。

```diff
 #endif
+#if BACKOFF_TRIGGER_GATING
+  Backoff::backoff(FLAGS_clocks_per_us);
+#endif
 #if ADD_ANALYSIS
```

- 影響: predicate が false でも後続の無条件 backoff が実行され、mask の性能意味が崩れる。`E + E` 変異自体は、この検査を削除すれば既存検査をすべて通るため、単独帰属は成立する。
- 推奨 (must-fix): 私はこの検査を今回の R2 閉鎖証拠から落とすことを推奨する。残すなら「直結した同一 epilogue の重複だけを拒否する独立 invariant」と明記し、post-END 全体の保証に見せない。

## 総括

- `END` 直後の E 検査が閉じるのは、END と最初の gated `if` の間だけである。
- prologue の型変更や reason 状態の改変で、block と E を逐語一致させたまま gate 意味論を壊せる。
- `emit_predicate` は代入文字列しか保証せず、P1 の一般化は成立しない。
- ENOENT、非認証診断 build、S8b resume は検査外である。
- brief の S8b/S-1 quarantine 分類は実呼び手と一致しない。
- 直結重複検査は狭い独立検出だが、R2 全体の保証ではない。
- 静的検査のみ実施し、pytest は実行していない。