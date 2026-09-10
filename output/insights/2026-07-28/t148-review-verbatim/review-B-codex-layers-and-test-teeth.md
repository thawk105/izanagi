結論は **NO-GO**。静的検査で、偽 `STOCK` を実際に作れる経路を3系統、正当候補の過剰拒否、loop の参照取り違えを確認した。

## must-fix

1. **digest の文脈が実 CMake ターゲットと一致せず、既知マクロだけで偽 `STOCK` を作れる。**

   - file: [source_digest.py:149](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:149), [CompileOptions.cmake:1](/home/SFC/tanab/github/izanagi/external/ccbench/cmake/CompileOptions.cmake:1), [Options.cmake:42](/home/SFC/tanab/github/izanagi/external/ccbench/cmake/Options.cmake:42), [cc/silo/CMakeLists.txt:1](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/CMakeLists.txt:1)
   - 根拠: digest は `g++ -E ...` に `-std=c++20` を渡さない一方、実ビルドは `CMAKE_CXX_STANDARD 20`。`__cplusplus` は builtin 集合に入るため、次をガードが受理する。

     ```cpp
     #if __cplusplus >= 202002L
     CHANGED
     #else
     STOCK
     #endif
     ```

     digest は既定 C++17 側の `STOCK`、実ビルドは C++20 側の `CHANGED` を選ぶ。

     さらに digest は全 Options 既定値を一律 `-D` するが、silo ターゲットは universal と silo 固有だけを供給する。例えば `DEBUG_MSG=0` は oze 用で silo には未供給なのに、digest では定義済みになる。

     ```cpp
     #ifdef DEBUG_MSG
     STOCK
     #else
     CHANGED
     #endif
     ```

     これも digest と実 silo TU で枝が逆転する。
   - 成果物影響: `src_token="stock"`、stock の `variant_id/cache_key` になり、既存 stock certified record/cache binary の skip・再利用、または変更バイナリの stock cache への格納が起こる。certified 選択とレポートが実行コードを指さない。

2. **条件指令の正規表現走査は正規なプリプロセッサ記法を網羅せず、ガードを発火させずに偽 `STOCK` を作れる。**

   - file: [source_digest.py:93](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:93), [source_digest.py:227](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:227), [backoff.hh:9](/home/SFC/tanab/github/izanagi/external/ccbench/include/backoff.hh:9), [result.hh:12](/home/SFC/tanab/github/izanagi/external/ccbench/include/result.hh:12)
   - 根拠: g++ は `#/**/ifdef` を条件指令として受理するが、`_COND_DIRECTIVE_RE` は `#` の直後に空白しか許さず見落とす。実 `backoff.hh` は `result.hh` 経由で `MAX_TX_TYPE` を得る一方、digest は include を除去するため、次が反例になる。

     ```cpp
     #/**/ifdef MAX_TX_TYPE
     CHANGED
     #else
     STOCK
     #endif
     ```

     実 TU は `CHANGED`、digest は `STOCK`、ガードは指令自体を検出しない。

     また `local_defs` は定義位置を無視した全ファイル集合なので、通常の `#ifdef MAX_TX_TYPE` の後ろへ `#define MAX_TX_TYPE 10` を置く形でも、実 TUとdigestの条件時点の definednessが違うのに受理される。
     
     `diff_quarantine.py:459-487` は通常 hole のコメント delimiter・生指令を拒むが、直接 `resolve/evaluate`、trusted patch、patchharness 経路の完全性は担保しない。
   - 成果物影響: 変更コードが stock ID/cache key を継承し、stock certified 結果の skip、stock binary の返却、または変更バイナリの stock 名前空間への永続化を許す。

3. **`__has_include` の「blanket reject」はマクロ展開された出現を検出せず、P2の穴が残る。**

   - file: [source_digest.py:227](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:227)
   - 根拠: 検査は条件式文字列中のリテラル `"__has_include"` だけを見る。`_DEFINE_RE` はマクロ本体を解析しないため、次は通過する。

     ```cpp
     #define IZ_HAS_LOCAL __has_include("atomic_wrapper.hh")
     #if IZ_HAS_LOCAL
     CHANGED
     #else
     STOCK
     #endif
     ```

     `IZ_HAS_LOCAL` は `local_defs` により既知扱い。実 `backoff.hh` では同ディレクトリの `atomic_wrapper.hh` が見つかるが、repo-root から stdin と `-nostdinc` で走る digest では見つからず、枝が逆転する。
   - 成果物影響: computed-include 依存の変更が `STOCK` に化け、stock certified 選択・cache binary・WAL参照を継承する。

4. **識別子走査が文字定数までマクロ扱いし、「未知マクロと `__has_include` 以外は狭めない」という不変条件を破る。**

   - file: [source_digest.py:232](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:232), [pipeline.py:441](/home/SFC/tanab/github/izanagi/orchestrator/campaign/pipeline.py:441)
   - 根拠: 正当な条件式 `#if 'A' == 65` に対して `_IDENT_RE` は `A` を抽出し、未知マクロとして拒否する。これはマクロ参照ではなく、g++ が普通に評価できる整数文字定数である。brief の「縮小方向は未知マクロ条件指令と `__has_include` のみ」に反する。
   - 成果物影響: 正当な候補が受理集合から除外され certified 選択へ到達しない。直接 evaluate 経路では identity-error が候補固有IDではなく `variant_id(genome)` の stock key で記録される。

5. **3本の coder loop は terminal skip 後、patchをrevertしてから重複IDを再計算し、別 variant の成果を返す。**

   - file: [p3_s4_loop.py:640](/home/SFC/tanab/github/izanagi/orchestrator/campaign/p3_s4_loop.py:640), [p3_s4_loop_sort.py:243](/home/SFC/tanab/github/izanagi/orchestrator/campaign/p3_s4_loop_sort.py:243), [p3_s4_loop_trigger_gating.py:399](/home/SFC/tanab/github/izanagi/orchestrator/campaign/p3_s4_loop_trigger_gating.py:399)
   - 根拠: `run_campaign` は `with applied(...)` 内の変更済み tree で正しい非stock IDを解決してskipする。しかし `summary.skipped > 0` の `_resolve_duplicate` は `with` の外、すなわちrevert済みtreeで `resolve()` を再実行する。backoff版はさらに `sub` も渡さず共有treeを参照する。したがって既存terminal候補ではなくstock IDのCOMMIT/VERIFYを検索する。
   - 成果物影響: stock COMMITがあれば候補の `variant/fitness_tps/verdict` がstock値に置換され、なければ既存terminal候補をaborted扱いする。whiteboard、trigger provenance、checkpoint、critic digestが誤ったvariant参照を永続化し、次iterationの選択・停止判定が変わる。

## should

1. **「identity確定はresolveへ一本化済み」は実コードと一致しない。**

   - file: [source_digest.py:49](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:49), [buildcache.py:564](/home/SFC/tanab/github/izanagi/orchestrator/campaign/buildcache.py:564), [pipeline.py:441](/home/SFC/tanab/github/izanagi/orchestrator/campaign/pipeline.py:441), [screening_driver.py:126](/home/SFC/tanab/github/izanagi/orchestrator/campaign/screening_driver.py:126)
   - 根拠: legacy `build()` の `src_token=None` は直接 `source_digest.src_token()` を呼び、ガードはcache判定・build後の `_recheck_src_token` まで発火しない。`pipeline.evaluate` は供給済みtokenを無検査で採用する。`screening_driver` は供給済みtokenからterminal判定し、skip時はbuild出口の再検査へ到達しない。
   - 現行S1/S6/S8a driverはpatch適用中にfreshな`resolve`値を渡しており直ちに偽hitする証拠はないが、API契約とdocstringは過大表現。

2. **5本のテストは個別機能には歯があるが、全層保証とM1〜M4の単一理由性を証明していない。**

   - file: [test_campaign.py:3188](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_campaign.py:3188), [handoff:53](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-28-dev-wave-t148-macro-context.md:53)
   - 静的判定:

     | テスト | 修正なしの判定 | 歯 |
     |---|---|---|
     | TU context identity `:3207` | 赤 | GVD形には実効 |
     | unknown conditional `:3234` | 赤 | 通常綴りの`#ifdef/defined`だけ |
     | builtin/local/supplied正例 `:3264` | 緑 | 過剰拒否検査でありmutation killerではない |
     | hidden TRACE `:3285` | 赤 | helper直呼びには実効 |
     | `__has_include` `:3310` | 赤 | g++12では`-nostdinc` + `<atomic>`自体がpreprocess errorになり、blanket guard以外の理由でも赤 |

   - M1は共有 `_context_overlays()` をbase-onlyにするとidentityテストとTRACEテストの2本が落ちる。M2早期returnはunknownと`__has_include`の2本が落ちる。M3だけはTRACEテスト単独。M4の専用raise削除はgeneric unknownメッセージにも`__has_include`が残るためテストが緑で、diagnostic pinにもなっていない。
   - F27型の現行hash差し込みはない。F42は既存自走harness内への追加なので成立。F29型は残る――実g++は使うが、fake repo・stdin・CMake flagsなしであり、実TU文脈ではない。
   - builtin照会の起動失敗・非zero・空集合は実装上すべてfail-closedだが、それを固定するテストはない。
   - `_any_cxx` は親環境のT-137型skipを回避する一方、production既定のg++-13とC++20条件を検査していない。既存実tree roundtrip `:2896` は直接`src_token()`を呼び、g++-13不在時skipなので、新guardを通したgolden互換の歯ではない。

3. **「broken patchの裸マクロはtriggerだけ」というpatch inventoryは誤り。**

   - file: [handoff:18](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-28-dev-wave-t148-macro-context.md:18), [broken-silo-norw-validation.patch:9](/home/SFC/tanab/github/izanagi/patches/broken-silo-norw-validation.patch:9), [broken-silo-lockskip-validation.patch:9](/home/SFC/tanab/github/izanagi/patches/broken-silo-lockskip-validation.patch:9), [broken-silo-permutation-erase.patch:9](/home/SFC/tanab/github/izanagi/patches/broken-silo-permutation-erase.patch:9)
   - 根拠: trigger以外にもhighkey、norw、lockskip、early-unlock、permutation-erase/swapが `IZANAGI_BREAK_*` を裸で参照する。現状はいずれも直接CMake characterization driverでありcertified経路への直結は確認しなかったが、P4の静的照合結果は事実誤認。

## 確認済みの非所見

- `assert_trace_diff_matches_head` はlegacy/v2のcache-hit・fresh-build全4出口で発火し、fresh時は返却・publish前。identity側と同じ `_context_overlays()` を使うため内部の二重文脈化は整合している。ただしmust-fix 1の実ビルド文脈との乖離は両方に共通する。
- S1、S6、S8aの本driverはpatch適用中に`resolve()`し、そのtokenをevaluateへ渡す。
- productionの直接`compute/baseline` callerはなく、直接`src_token` callerはlegacy buildcacheが主経路。較正用broken-patch driverはsource digestを使わない。
- `[ctx:...]` と `\x02` を解釈する他moduleは見つからず、外部token形式は従来どおり`stock`または64桁hex。stock時のpure `variant_id/cache_key` golden形式自体は維持される。

## 総括

**NO-GO**

| 裁定 | 実在判定 | 理由 |
|---|---|---|
| P1 | **refuted** | GVD単体の二重文脈は効くが、実C++20/target define、指令字句、include由来definednessを覆わない |
| P2 | **refuted** | マクロ展開された`__has_include`がblanket rejectを通過する |
| P3 | **refuted** | fallbackテストのcompiler/language contextがproductionのg++-13/CMake C++20契約と一致しない |
| P4 | **refuted** | 有効な文字定数条件を過剰拒否し、broken patchの裸マクロ列挙も誤っている |