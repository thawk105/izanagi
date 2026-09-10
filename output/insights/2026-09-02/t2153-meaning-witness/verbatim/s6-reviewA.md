## 所見

1. **重大度: BLOCKER**

   **何が問題か:** witness は対象条件だけを切り出し、所有 TU の前方 context と実 compile argv を捨てて standalone 前処理するため、実 TU で枝が選択されなくても green になる。これは裁定の「要求値で対象枝を選択」という条件を満たさない。  
   **根拠:** `orchestrator/campaign/condition_meaning_gate.py:2325-2358`、`s4-adjudication.md:72-77`

   具体例:

   ```cpp
   int supply_probe = IZANAGI_BREAK_PERMUTATION;
   #undef IZANAGI_BREAK_PERMUTATION
   #if IZANAGI_BREAK_PERMUTATION
   int guarded;
   #endif
   ```

   所有 TU の要求値 1 / 既定値 0 は `supply_probe` により異なるので supply は green になりうるが、対象枝は両方で不選択になる。現実装は先頭 2 行を捨て、抽出片へ改めて `-D...=1/0` を渡すため meaning も green になる。

   **成果物への影響:** その macro が誤って `unestablished_meaning_macros` から消え、certified 選択・材料レポート・台帳が false-green の meaning record/admission ID を参照する。  
   **是正案:** 抽出片ではなく marker を挿入した所有 TU 全体を前処理し、supply 側が確定した実 compile command を再利用する。要求値と既定値以外の argv と source context を同一に固定する。

2. **重大度: BLOCKER**

   **何が問題か:** 深さ判定は物理行への正規表現であり、C/C++ の行継続、コメント除去、raw string、コメント前置きの指令を扱わない。そのため非指令を指令として数え、実際の入れ子を深さ 0 と誤認する。  
   **根拠:** `orchestrator/campaign/condition_meaning_gate.py:227-229`、`:2220-2268`

   誤って深さ 0 とする入力:

   ```cpp
   #if 0
   // この endif は行継続後にコメントへ入る \
   #endif
   #if IZANAGI_BREAK_PERMUTATION
   int guarded;
   #endif
   #endif
   ```

   実プリプロセッサでは対象枝は外側の `#if 0` 内だが、実装は物理行の `#endif` で深さを 0 に戻す。`/* prefix */ #if 0` のようにコメント除去後は有効になる外側指令も見落とす。

   誤って深さ非 0 とする入力:

   ```cpp
   /*
   #if 0
   */
   #if IZANAGI_BREAK_PERMUTATION
   int guarded;
   #endif
   ```

   raw string 内の行頭 `#if` も同様に誤計数する。さらに、対象の `#if` 自体が block comment/raw string 内にある場合、その文字列だけを抽出して standalone 前処理し green にできる。

   **成果物への影響:** false-zero では存在しない、または到達不能な条件枝を established と記録し、false-nonzero では正しい枝を red にして選択・材料生成を不当に拒否する。  
   **是正案:** translation phase 2/3 相当の行継続とコメント処理を行う lexer、または実コンパイラ由来の指令位置情報で開始指令と深さを判定する。上記の false-zero、false-nonzero、raw-string 例を負例・正例へ追加する。

3. **重大度: MUST-FIX**

   **何が問題か:** 事前登録 MUT-6 の負例は completion marker の観測要求へ到達せず、`#endif` 不在の抽出エラーだけで赤になる。また 8 件の通過試験は実 patch の owner/directive のみ照合し、機構自体は生成した平坦な fixture で通している。  
   **根拠:** `orchestrator/tests/test_condition_meaning_gate.py:170-207`、`:583-628`、`:698-713`、`orchestrator/campaign/condition_meaning_gate.py:2269-2273`、`:2380-2408`

   **成果物への影響:** completion marker 要求や source-context 束縛を弱めても指定テスト群が green のままになり、8 macro の meaning record と admission 参照が誤って更新されうる。  
   **是正案:** well-formed な `#endif` を持たせたまま completion count を 0 にする負例を追加し、`(1,1)/(0,1)` 検査へ直接照準する。実 patch 適用後の conditional/prefix を通す正例と、所見 1・2 の敵対入力も追加する。

4. **重大度: NIT**

   **何が問題か:** `proof_kind` と module docstring は適切に限定された一方、直列化される arm は `runtime-meaning`、reason は `declared-meaning-observed` のままで、admission の説明も「every macro's meaning is established」としている。evidence を展開しない読み手には実行時意味の確認に見える。  
   **根拠:** `orchestrator/campaign/condition_meaning_gate.py:10-18`、`:515-526`、`:2469-2475`

   **成果物への影響:** reason code を直せば meaning record ID と、それを含む材料レポート・admission の参照値が変わる。現状は表示上の主張境界が曖昧になる。  
   **是正案:** 新 field を増やさず、compile-time 専用 reason code を使い、admission の説明を「各 record の proof_kind 境界で established」と訂正する。

## 8 件の独立照合

- `IZANAGI_BREAK_PERMUTATION` — `patches/broken-silo-permutation-erase.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、sort 後かつ次の `#if TRACE` 前で深さ 0。
- `IZANAGI_BREAK_PERMUTATION_SWAP` — `patches/broken-silo-permutation-swap.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、sort 後かつ次の `#if TRACE` 前で深さ 0。
- `IZANAGI_BREAK_LOCK_COVERAGE` — `patches/broken-silo-lockskip-validation.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、先行 `#if TRACE` の対応 `#endif` 後で深さ 0。
- `IZANAGI_BREAK_EARLY_UNLOCK` — `patches/broken-silo-early-unlock-validation.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、先行 `#if WAL` の対応 `#endif` 後で深さ 0。
- `IZANAGI_BREAK_WRITE_INTENT_ERASE` — `patches/broken-silo-write-intent-erase.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、先行 `#if ADD_ANALYSIS` の対応 `#endif` 後で深さ 0。
- `IZANAGI_BREAK_WRITE_INTENT_FORGE` — `patches/broken-silo-write-intent-forge.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、先行 `#if ADD_ANALYSIS` の対応 `#endif` 後で深さ 0。
- `IZANAGI_BREAK_WRITE_INTENT_OPSWAP` — `patches/broken-silo-write-intent-opswap.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、先行 `#if ADD_ANALYSIS` の対応 `#endif` 後で深さ 0。
- `IZANAGI_BREAK_WRITE_INTENT_PTRSWAP` — `patches/broken-silo-write-intent-ptrswap.patch:9`、`cc/silo/transaction.cc`、開始指令完全一致、追加側 1 箇所、先行 `#if ADD_ANALYSIS` の対応 `#endif` 後で深さ 0。

## 負例の発火点

- `test_compile_time_branch_selection_rejects_non_discriminating_observation` — `condition_meaning_gate.py:2395-2408`。同一観測を許すと期待 reason または terminal status が崩れて赤になる。
- `test_compile_time_branch_selection_rejects_nested_start_directive` — `condition_meaning_gate.py:2250-2254`。深さ 0 要求を外すと standalone probe が green になり赤になる。
- `test_compile_time_branch_selection_rejects_duplicate_start_directive` — `condition_meaning_gate.py:2224-2228`。一意性を 1 箇所以上へ緩めると green になり赤になる。
- `test_compile_time_branch_selection_rejects_missing_matching_endif` — 直接の発火点は `condition_meaning_gate.py:2269-2273`。completion marker 観測要求 `:2380-2408` を外す MUT-6 の発火点は**特定できず**。
- `test_compile_time_factory_keeps_unregistered_macro_unestablished` — `condition_meaning_gate.py:789-791` と `:480-485`。registry 外へ宣言を返す変更で赤になる。
- `test_compile_time_factory_rejects_nonpaired_values` の 4 組 — `condition_meaning_gate.py:790-791`。1/0 以外を宣言すると赤になる。
- `test_legacy_meaning_declaration_and_cli_stay_backoff_fixed_only` — factory 側は `condition_meaning_gate.py:457-458`、CLI 側は `:3095-3103`。旧型または旧 CLI を非 `BACKOFF_FIXED` へ広げると赤になる。
- `test_compile_time_green_schema_rejects_missing_or_mutated_observations` — default 欠落は `condition_meaning_gate.py:2876-2882`、同一観測は `:2904-2907`、誤 proof kind は `:2871` / `:2917` が発火点。
- 既存の `test_v1_domain_and_claim_boundaries_are_exact` に追加された旧型 pin — `condition_meaning_gate.py:457-458` を集合所属へ戻すと赤になる。
- `test_condition_gate_rejection_stops_s5_before_build` に追加された factory 引渡し検査 — `s5_permutation_coverage.py:92-95` で factory の返値を渡さない変更により赤になる。
- screening と T152 に追加された検査は文字列による配線正例であり、新規の負例発火点はない。

## 総括

BLOCKER は 2 件であり、この実装は現状のまま land してはならない。  
8 registry entry の patch・開始指令・個数・現行挿入点の深さは全件正しい。  
旧型 constructor・evaluator・CLI の固定も効いており、従来拒否入力を新規受理する経路は見つからなかった。  
ただし standalone/context 欠落と非 lexical な深さ計数により、誤った established 値を成果物へ載せられる。