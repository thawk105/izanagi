# 親の追加実測 (main 7f17e1c63、親が自分で確かめた)

段 2 プランの起草後に親が実測した事実である。プランがこれらを見落としている可能性があるので、
レンズは自分で確かめたうえで、プランと親 brief の両方を攻撃せよ。「実測」と書いたものは
親が実際にコマンドを走らせて得た。「読解」と書いたものはコードを読んだだけの推論である。

## 1. 非恒等写像を持つ protocol は cicada と oze だけ (実測)

`grep -n '\${CCBENCH_' external/ccbench/cc/<protocol>/CMakeLists.txt` を 5 protocol に対して実行した。
左辺 (TU マクロ名) と右辺 (cache 変数名、`CCBENCH_` 接頭辞つき) が食い違うのは次の 2 行だけである。

- `cc/cicada/CMakeLists.txt:5`: `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_CICADA}`
- `cc/oze/CMakeLists.txt:5`: `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_OZE}`

silo / mocc / tictoc の全行と、cicada / oze の残り全行は恒等写像である。oze は `SPACES` に無い。

## 2. CCBench 実体側から対応を取る既存の機構が repo にある (実測 + 読解)

親が見落としていた資産である。プランがこれを使わず新しい parser を書いているなら、その是非を
レンズが裁定せよ。使っているなら、使い方が正しいかを攻撃せよ。

- `orchestrator/campaign/source_digest.py:2021` `resolve_effective_defines_from_cmake_sources(
  source_rel, genome, *, options_text, protocol_cmake_text)` が、CCBench の
  `cmake/Options.cmake` と `cc/<protocol>/CMakeLists.txt` の**実テキスト**から
  `EffectiveDefineResolution` を作る。
- `EffectiveDefineResolution.cache_name(macro)` (同 file:338) が TU マクロ名 → cache 変数名
  (`CCBENCH_` 接頭辞を剥がした形) を返す。cicada なら
  `cache_name("INLINE_VERSION_OPT") == "INLINE_VERSION_OPT_CICADA"` になるはずである (読解)。
- 同 function は `genome.flags` の key を**cache 変数名**として解釈する。docstring 逐語:
  "``genome.flags`` models the caller's ``CCBENCH_<name>`` cache overrides. Each TU macro then
  receives the value of the cache variable named on the right-hand side of its CMake mapping.
  This intentionally does not use the older digest shortcut that lets a left-hand genome flag
  bypass a wrong cache mapping: a wrong RHS must remain observable to supply consumers."
  したがって cicada の genome `{"INLINE_VERSION_OPT": 1}` を渡すと、実効値は cache 既定の 0 に
  解決されるはずである (読解)。これは現行の欠陥を忠実に写した挙動であり、修正の正例・負例の
  oracle になりうる。
- production の consumer が既にある: `orchestrator/campaign/condition_meaning_gate.py:1332-1345` は
  silo の `BACKOFF_FIXED` について `cache_name(MACRO) != MACRO` または実効値不一致なら
  `supply-value-mismatch` で落とす。エラー文は実際の経路 `CCBENCH_<cache_name>, not CCBENCH_<MACRO>` を
  名指しする。**依頼が言う「対応が崩れたら落ちる検査」の先例がこれである。**
- `orchestrator/campaign/source_digest.py:_merge_defines` (同 file:902 付近) は逆に、
  `if left in flags: continue` で左辺の genome flag を最優先する古い近道を持つ。
  digest 経路と gate 経路で意味論が違う点は攻撃対象になりうる。

## 3. 親が probe で実測した対応表と、高位 API の射程 (実測)

probe は repo 外 (`/home/SFC/tanab/.claude/jobs/9930abe3/tmp/dev-wave-t2536-cicada-axis-name/probe_mapping.py`)
に置いて実行した。結果は次のとおりである。

- `source_digest._parse_supplied_macro_details(options_text, protocol_cmake_text)` は
  `(supplied 名集合, 裸名集合, macro -> cache 名の辞書)` を返す。**これが CCBench 実体側から取れる
  対応そのものである。** ただし private (先頭 `_`) である。
- 登録済み 4 protocol で非恒等写像は 1 件だけ:
  cicada の `INLINE_VERSION_OPT -> INLINE_VERSION_OPT_CICADA`。silo / mocc / tictoc は 0 件。
- `SPACES` の全軸は 4 protocol とも supplied 集合に入っている (値は正しい cache 名で渡せば TU へ届く)。
- mocc には裸 option `RWLOCK` がある (cache 名を持たない supplied マクロ)。表の形を決めるとき、
  この「cache 名なし」の場合を落とさないこと。
- 現行実測: `Genome("cicada", {"INLINE_VERSION_OPT": 1, "BACK_OFF": 1}).cmake_defines()` は
  `["-DCCBENCH_BACK_OFF=1", "-DCCBENCH_INLINE_VERSION_OPT=1"]` を返す。後者は CMake が未使用と
  報告する名前である。
- **高位 API は cicada に使えない (実測)**: `resolve_effective_defines_from_cmake_sources` に
  `source_rel="cc/cicada/transaction.cc"` を渡すと
  `RuntimeError: source_digest: EVOLVE-BLOCK の未知 source 'cc/cicada/transaction.cc' — protocol
  owner を確定できないため fails-closed (T-1437)` で落ちる。登録は
  `EVOLVE_BLOCK_SOURCE_PROTOCOLS` (同 file:90) の 3 件だけで、cicada は入っていない。
  登録簿を広げるのは本 wave の scope 外である。**この事実がプランの設計を縛る。**

## 4. 依頼の逐語 (command 引数)

「[T-2536] SPACES の cicada 軸 INLINE_VERSION_OPT を CCBench の実体 CCBENCH_INLINE_VERSION_OPT_CICADA
へ合わせる。合わせるまで cicada は認定の対象にできず、[T-2224] が閉じた受理集合 {silo, mocc, tictoc}
の外に置かれたままになる。名前の対応は CCBench の実体側から取り、対応が崩れたら落ちる検査を同じ
変更単位で置く。Codex author = D95。規律 2 は緩めない。本題の実装だけ。仮想リスク向けの
gate・検査・台帳・一般化の追加は scope 外。」
