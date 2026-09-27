### 1. P1 の比較

| 観点 | 案 A：BEGIN 直前の prologue 7 行 | 案 B：`abort()` 冒頭から BEGIN 直前まで |
|---|---|---|
| 提示された差分 | R4 の型差し替え・reason reset、R5 の `return;`、R7 の `FLAGS_clocks_per_us`／`Backoff` の局所 shadowing を拒否する | 同じ差分を拒否する |
| 同じ関数本体内での移設 | `return;`、reason reset、局所 shadowing を prologue の**直前**へ移せば通る | 凍結する冒頭領域内なので拒否する |
| 正当な producer | 骨格のみ・骨格＋tally とも追加形なしで通る | tally が開き括弧直後に入るため、2 形の受理が必要 |
| 結合と実装量 | 骨格 patch の 7 行だけに結合し、fixture 更新は小さい | pin 6810666 の CCBench 原文 20 行にも結合する。合成 fixture、とくに実 compile する fixture の更新が大きい |

**案 B を推奨する。** 親 brief の「A は 1 行上へ動かすだけで通る」は、少なくとも R5 と R7 について正しい。A が元の挿入位置を拒否することは、この反証にならない。B の 2 形は tally patch が挿入する bytes だけを許し、任意の追加行を許さない。根拠は [brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/s1-brief.md:32)、[骨格適用後の source](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/evidence/transaction.cc.skeleton-applied:61)、[tally patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/instr-silo-backoff-trigger-gating-tally.patch:8)。

### 2. 受理言語の差分

[T-1048 の条件 1〜3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/t1048-README.md:26)に、marker のある source の**論理積条件 4**を足す。

4. `begin = begins[0].start()` とし、`raw[:begin]` が、`abort()` の宣言行から始まる凍結 bytes の「骨格のみ」または「骨格＋tally」のいずれかで終わること。凍結末尾は BEGIN **行頭の直前**であり、BEGIN 自体は従来の block 条件で検査する。宣言行より前の bytes は比較しない。

比較対象には各行末の `\n` と、原文の `#endif\n` 後・prologue 後の空行位置を含める。従ってその領域の CRLF 化も拒否する。一方、[既存 regex](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:57)が BEGIN を見つける範囲や、[epilogue 後を凍結しない条件](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/t1048-README.md:34)は変えない。

### 3. 凍結定数

[axis_trigger_gating.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/axis_trigger_gating.py:27)の既存定数の隣に、次を置く。

- `FROZEN_TEMPLATE_ABORT_HEAD_BYTES`：`void TxExecutor::abort() {\n` から、原文の最初の `#endif\n\n` まで。[pin の原文 27〜46 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/external/ccbench/cc/silo/transaction.cc:27)由来。
- `FROZEN_TEMPLATE_ABORT_TALLY_BYTES`：[tally patch の追加行 9〜32](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/instr-silo-backoff-trigger-gating-tally.patch:9)由来。head の宣言行直後にだけ挿入する。
- `FROZEN_TEMPLATE_PROLOGUE_BYTES`：[骨格 patch の追加行 79〜85](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/silo-backoff-trigger-gating-variant.patch:79)由来。
- 比較用の 2 形は `HEAD + PROLOGUE` と、`HEAD` の宣言行直後へ `TALLY` を挿入してから `PROLOGUE` を付けたものとして組み立てる。実行時に patch や CCBench file を読まない。

[test_build_admission.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_build_admission.py:716)の独立整合テストに、骨格 patch の `+` 行 79〜85、tally patch の `+` 行 9〜32 をそれぞれ patch 本文から抽出して定数と比較するテストを足す。原文は submodule の `.git` が無い場合だけ skip し、初期化済みなら `git -C external/ccbench show CURRENT_PIN:cc/silo/transaction.cc` の bytes から `abort()` 宣言〜最初の `Backoff::backoff` の直前を抽出する。pin object や file が欠ければ **fail** とする。[既存の submodule 判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_campaign.py:11322)と同じ境界である。

### 4. 検査の差し込み点

[build_admission.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:34)に定数 import を足す。[同 200〜203 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:200)の marker 件数・順序確認の直後で `prefix = raw[:begins[0].start()]` を取り、2 形のどちらにも `endswith` しなければ `_reject_trigger_axis()` を呼ぶ。既存の epilogue 照合、block／hole 照合はその後に現状の順序で残す。[`derive_build_admission` と `require_build_admission` の呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:656)も変えない。ENOENT 受理、marker・token とも無い stock 受理、marker あり照合という三分岐は [170〜201 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:170)のまま維持する。

### 5. テストと fixture

[test_build_admission.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_build_admission.py:227)の `_trigger_source_bytes` に `before`／`tally` 指定を足し、既定を canonical な `abort()` 冒頭＋prologue とする。現行の marker 説明コメントは**関数宣言より前**へ残す。`_write_trigger_source` を使い、以下を追加する。

- `test_trigger_axis_rejects_mutated_abort_prefix`：R4 の `GatePass` 差し替え、R4 の reason reset、R5 の `return;`、R7 の `FLAGS_clocks_per_us` と `Backoff` の shadowing を parameter 化する。加えて R4 の reset、R5、R7 の両 shadowing を prologue 直前へ移した形を拒否する。[実証差分](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/consult-b.md:6)、[R5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/consult-a2.md:8)、[R7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/review-b.md:15)に対応。
- `test_trigger_axis_accepts_tally_abort_prefix`：骨格＋tally、および tally＋misattr の **abort() 側が同一**である形を受理する。misattr の変更箇所は [lockWriteSet の hunk](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/broken-silo-trigger-misattr.patch:5)なので、必要なら abort() 外の bytes に同 patch 由来の差分を置き、prefix 条件がそこを凍結しないことを示す。
- [既存の 32 mask、pristine、epilogue 後の正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_build_admission.py:397)をそのまま通す。既存の負例・ENOENT 正例の期待も変えない。

残る fixture 3 箇所は形だけ更新する。[test_campaign.py:6236](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_campaign.py:6236)では render 前の `base_text` に canonical prefix を付ける。[test_buildcache_v2.py:5688](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_buildcache_v2.py:5688)では fake checkout の marker 置換に加え、`abort()` 冒頭〜BEGIN 直前を canonical bytes へ置換する。このテストは compile 前の観測で止める。

[test_reflux_campaign_issuer.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_reflux_campaign_issuer.py:169)は実 compile するため、`static void exercise_trigger_gate()` を `TxExecutor::abort()` に替え、canonical head をそのまま置く。最低限、`TxExecutor` の `abort` 宣言と `write_set_`／`read_set_`／`node_map_`、`WriteEntry` の `op_`・`storage_`・`key_`・削除可能な `rcdptr_`、`OpType::INSERT`、`Masstrees[...]` と `remove_value_if_present`、`get_storage`、`gc_records`、`rdtscp` を stub 化し、`<vector>` と `<cstdint>` を含める。既存の `Backoff`、flag、reason enum は再利用し、`main` は `TxExecutor` を作って `abort()` を呼ぶ。[materialized hole の置換](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_reflux_campaign_issuer.py:211)と各テストの受理・拒否期待は維持する。

### 6. 変異候補

[新しい比較箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:200)に対し、(M1) prefix 検査の削除、(M2) prologue 7 行だけの照合へ弱化、(M3) 骨格＋tally 形を削除、(M4) 関数宣言より前まで一致を要求、(M5) tally を任意位置・任意 bytes として許す、を候補にする。M1 は提示差分、M2 は移設版、M3 は tally 正例、M4 は関数前の説明コメント、M5 は tally 近傍への余分な行でそれぞれ見る。M3・M4 は過剰拒否側である。

[contract-loader 閉包](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/campaign_lock.py:81)に実装 2 file が入るため、未 commit 変異は drift 層の node も落とし得る。段 4 の probe では、上記の**直接 admission／整合テスト node**と**contract-loader-drift node**を別集合として記録し、前者だけを新検査の単独検出力に帰属させる。期待失敗 node は probe 後に完全列挙する。[前 wave の変異帰属上の指摘](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/review-b.md:1)に従う。

### 7. 残る限界と docstring

[build_admission.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:170)の docstring は、「`abort()` 冒頭から BEGIN 直前まで、骨格のみ／骨格＋tally の raw bytes を照合する。**その領域内**の R4 型差し替え・reason reset、R5 非到達化、R7 局所 shadowing の提示形と移設形を拒否する」と書き換える。R4/R5/R7 が無条件に解消したとは書かない。

同じ docstring に、関数より前の file scope 宣言、他 file の header／class member による名前解決差し替え、前処理器による識別子置換を残存限界として明記する。既存の R1 コメント・raw string、R3 ABA、R6 dangling `else`、ENOENT 受理も残す。[現行の限界記述](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:173)、[brief P4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/s1-brief.md:49)に対応する。

## 総括

案 B を採用し、`abort()` 宣言から BEGIN 行頭直前までを逐語照合する。  
受理形は骨格のみと、開き括弧直後に tally が入る形の 2 つに限定する。  
既存の block・epilogue 条件と三分岐は維持し、受理集合を狭める。  
定数は骨格 patch、tally patch、pin の CCBench 原文との独立一致テストで固定する。  
4 箇所の fixture を canonical な冒頭へ寄せ、既存テストの受理・拒否期待を変えない。  
この段階では静的確認のみを行った。編集・build・テスト実行は親の実装段に委ねる。