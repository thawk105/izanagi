## 所見

以下、`probe` はレビュー対象の `test_t2630_scan_boundary_reach.py`、製品コードの参照は指定された wave worktree を指します。静的レビューのみで、実走結果は判定していません。

### A6-1 — 期待署名への一致だけでは、事前登録した赤理由を確認できない

- **区分: must-fix（成果物での原因照合。gate の変更は不要）**
- **根拠 (file:line):** `probe:367–388` は共通の `run`・`manifest`・`compilers`・適用復元の成功を全 node に要求する。`tools/mutation_harness.py:2083–2099` は FAILED node の集合が一致すると `KILLED` にする。`s4-ruling.md:35` は変異ごとの赤理由を指定している。
- **real と主張する理由:** clone コマンドの例外などが `run` に捕捉されれば、4 node が同じ理由で FAILED となり、M2 の期待署名と一致する。また configure 失敗・空 stdout は `/tu` の失敗になり、resolve が成功していれば N2 だけが赤になる。これは M3b/M4/M4b/M6 と同じ署名になりうる。baseline 成功は後続 run の環境失敗を排除しない。
- **必要な扱い:** 台帳の `KILLED` は保存しつつ、意味上の判定を `observations.json` と結び付ける。M2 は current の resolve が **include-match 拒否**であること、到達候補は両側の resolve・TU 採取が成功し、最後の bytes 比較で赤になったことを確認する。共通段階や configure の失敗なら「期待署名一致・原因不適合」と明記する。
- **成果物影響:** 放置すると、環境失敗を include 検査の検出力や digest–TU 不一致の実証として数えられる。

### A6-2 — raw bytes 差は意味差を自動判定していない

- **区分: should**
- **根拠 (file:line):** `probe:265–274,404–411`、`condition_meaning_gate.py:2107–2109`、`s4-ruling.md:25`。
- **real と主張する理由:** `_compare_bytes` と N2 は bytes の完全一致だけを調べる。`-P` は行マーカーを除くが、展開済み `__LINE__` の整数などは除かない。同一 worktree によって root 由来の `__FILE__` 差は抑えられるものの、挿入行による位置差まで排除する設計ではない。これは即座の欠陥ではなく、plan が要求する「対応差を名指し」の作業が残っているという境界である。
- **必要な扱い:** M1 の追加演算、M3 の `sleepTics(1)`、M4 の重複宣言、M4b の CAS 引数、M6 の trace 展開を保存 diff で確認する。位置差だけなら到達と認定しない。
- **成果物影響:** 放置すると「前処理 bytes が違う」を「意味的に違う」へ過大解釈する。

### A6-3 — 同一 build dir は再利用され、fresh configure との同等性は測っていない

- **区分: should**
- **根拠 (file:line):** `probe:199–225`、`condition_meaning_gate.py:1694–1735`、`external/ccbench/cmake/CompileOptions.cmake:5,6,22–27`。
- **real と主張する理由:** build dir 名は side を含まず、`_configure_compile_commands` は `CMakeCache.txt` や build root を削除しない。reference→current の再 configure は必ず実行されるが、既存 cache を利用する。CMake 側には現在値へ文字列を追加する処理もあるため、「同じ引数なら再 configure 後の全設定も同じ」とは一般化できない。
  
  ただし今回の8変異は CMake の意味を変更せず、stock/variant の build dir は別々である。コンパイラは毎回実行されるため、compile command が同じでも変更された source/header を読み直す。**今回の cache 再利用が変異を隠す具体的経路は確認できなかった。**
- **必要な扱い:** 保存された両側の configure argv・owner command を比較し、観測を「同一 build dir の再 configure 条件下」と記す。
- **成果物影響:** 放置すると、既存 cache 条件での観測を fresh build 全般へ拡張してしまう。

### A6-4 — node の合否は、補助証拠の取得成功を保証しない

- **区分: should**
- **根拠 (file:line):** `probe:330–351,377–388`、`source_digest.py:249–259,2429–2432`、`s4-ruling.md:25,27,30`。
- **real と主張する理由:** `_pair` は `/preimage`・`/evidence`・`/trace`・`/object`・`cache/change` を require しない。これらが失敗しても N1/N2 は予定どおりの署名になりうる。特に variant ID は `/evidence` が成功した場合に保存される `verification_variant` に依存する。object は追加観測という plan に合っているが、その失敗を署名からは判別できない。
- **必要な扱い:** 主張ごとに証拠の有無を確認する。token 一致には `token.txt`、preimage 一致には両側の `preimage.bin`、ID 一致には両側の `verification_variant`、compile 成否には compile の rc と object 記録を使う。`cache/change` が未観測なら「変化なし」と書かない。
- **成果物影響:** 放置すると、取得できなかった ID・compile・cache 証拠まで確認済みと扱われる。

## 恒真化の検査結果

**同じ観測を流用する恒真化は見つからない。**

- `probe:294–300` は reference を superproject HEAD の carrier、current を作業木の carrier として別々に取得する。
- `probe:319–343` は同一 worktree に各 carrier を適用・復元し、各 genome について実 resolve と実 TU 観測を再実行する。キーは `reference/stock`、`current/stock` などで分離され、lambda は `stage()` 内で即時実行される。
- `lru_cache` が共有するのは、この両側観測を完了した結果である。reference の結果を current に代入する構造ではない。
- `_pair` は両側の resolve 成功を要求するが、N2 では **token の一致を要求しない**。したがって M1 の digest 差が N2 の比較を妨げることもない。
- 前処理はコマンド成功と非空 stdout を要求する。空 bytes 同士が一致して緑になる経路はない。ただし失敗は N2 FAILED になるため、A6-1 の原因照合が必要である。
- object は毎回削除して再生成し、同一出力パスを使う（`probe:186–196`）。objdump のファイル名バナーだけで差を作る経路も抑えている。

指定された API の呼出しは現物の signature と整合する。`resolve_evidence` の keyword-only 引数、`canonical_source_preimage_bytes`、TRACE 検査、`checkout`／`applied`、gate の capture・request・configure・owner 選択・argv 変換に不整合は見つからない。

`BACKOFF_FIXED` は実際に `int` の `-1`／`1`。`make_define_request` は `int | str` を受け、`cmake_defines()` は文字列化する。`evidence.as_receipt()` と `verification_variant` も実在する。

4 node の `_detect_site_under_test` は `conftest.py:248–249` の模擬 site 適用を回避する。通常の観測例外は test body 内で FAILED になる設計であり、fixture ERROR にする構造ではない。ただし fixture 自体やプロセス停止までこの捕捉が保証するわけではない。

## 模擬と実の差 (限定として書くべきこと)

| 面 | 実物として測っている範囲 | 残る限定 |
|---|---|---|
| local clone | 実 Git object の PIN から実 `patchharness.checkout` で materialize し、実 `applied` で変異する | 共有 checkout の dirty/untracked 状態や repository 固有設定の再現ではない。common-dir の独立性は byte 同等性全体の証明ではない |
| `--no-checkout` | clone 本体を未展開でも、`checkout` は明示 PIN の detached worktree を作る（`patchharness.py:362–371`） | この方式自体に source が未展開になる問題はない |
| 永続 cache | 指定された依存 source と既存 `config.h` を利用する | masstree の生成処理は build custom command（`ThirdParty.cmake:66–78`）。owner 単体の直接 compile はそれを実行せず、fresh dependency build の再現ではない |
| cache inventory | 3 cache の前後のファイル名・hash 等を記録する | 前後一致は途中の変更・復元まで排除しない。gflags/glog、system header 等はこの inventory の対象外 |
| TMPDIR | checkout を scratch 配下に置き、reference/current は同じ source/build path を利用する | 通常製品経路の絶対パスや filesystem 条件との同一性は保証しない |
| object／objdump | 実 owner command による単一 TU の compile 成否と逆アセンブル差を観測する | full build、link、workload 実行、最終 binary の symbol 検査は未観測 |

`source-evidence.json` の `tracked_clean`／`tracked_diff_sha256` は source 状態の区別に有用だが、認証結果の receipt 発行や cache 再利用を示すものではない。両側の token・preimage・実 TU diff が取得でき、対応する意味差を確認できれば、plan v2 の限定された到達主張を支えられる。

## 総括

probe の観測は独立しており、実 API の呼出しにも不整合は見つからない。**最終判定で必須なのは、期待 FAILED 集合への一致を、登録した原因の確認と分けること**である。

実測前に変異の到達・拒否は断定できない。保存された段階別結果と raw diff を照合すれば、製品経路・cache 継承・runtime への過大な主張を避けながら、plan v2 の範囲で判定できる。書き込み・commit・push・テスト実行は行っていない。