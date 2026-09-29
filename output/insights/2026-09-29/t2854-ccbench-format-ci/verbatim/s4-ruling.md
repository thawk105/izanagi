# 段 4 裁定 — [T-2854] pin 前進 (1)(2)

入力: 段 1 brief `s1-brief.md`、段 3 相談 A `out/s3-consult-A.md` (受理 rc=0)、親の追加実測 `probe/pp_probe_lines.log`。

## 親の新事実 (段 3 の後、裁定の前提を修正する)

- 整形後の 3 file を `#include` 除去・`-P` なしの `g++ -E -dD` (TRACE=0) で整形前と比べると、行番号マーカーが **mocc で -3、silo で +2 ずれる** (trace.hh は一致)。字句は一致 (pp_probe.log)。原因: 整形で行数が変わる `#if TRACE` 区間のうち、直後に `#line` の無い区間がある (mocc は先頭の 24〜115 行の区間。C の時点から `#line` が無い)。
- mocc の TRACE=0 有効コード 523 行 `ERR;` は include/debug.hh の `ERR` → `NNN` → `__LINE__` に展開される。整形だけの F では、この定数が 523 → 520 に変わり、**TRACE=0 の binary が変わる** (エラー経路の fprintf 引数)。trace 用コードの整形が性能計測用 build を変える = 規律 1 に触れる。D297 の header 分岐は consumer entry (mocc の TU は trace.hh の consumer) を実 include 込みの `-E -P -dD` で比べるので、この差で F を拒否する見込み。
- この branch の既存 commit (C1'・C3・C2') は「`#line` で TRACE=0 の論理行番号を基点に戻す」作法を取っている (message 逐語)。

## 裁定

- **R1 (採用、brief (P1) の修正):** F = clang-format 14 の整形 (違反 3 file) + **整形で TRACE=0 の論理行番号がずれる箇所にだけ `#line N` を足す**。置き場所は行数が変わった `#if TRACE` 区間の直後の `#endif` の次の行、N は C2' で同じ次行が持っていた行番号。目標 = 3 file とも `#include` 除去・`-P` なしの `g++ -E -dD` の TRACE=0 出力 (行番号マーカー込み) が C2' と byte 一致 (2 文脈以上)。既存の `#line` の値は変えない。`#line` を足したあとも clang-format 14 の `--dry-run --Werror` が 0 件であること。D2277 の「意味を変えない整形だけ」の趣旨 (TRACE=0 を変えない) を守るための付随変更であり、報告と commit message に明記する。
  - 禁止の署名: 「コードの字句・文字列・コメントの文言・既存 directive の値を変える変更」は不可。通る正例: `#endif` の直後に `#line 116` を 1 行足す。
- **R2 (相談 must-fix 1、採用):** 意味不変の照合を強める。Codex author が `scripts/verify_format_only.py` を書き、C2' と F の 3 file について (i) raw diff の path 集合 = 3 file・mode 不変、(ii) R1 で足した `#line` 行を除いたうえで空白 (space・tab・CR・LF) を全部除いた bytes が一致、(iii) 文字列・文字 literal の列 (内部の空白を含む逐語) が一致、(iv) 前処理指令行の列 (継続を結合し、先頭 `#` 後の空白を 1 個に畳んだもの) が足した `#line` を除いて一致、(v) 足した `#line` の一覧 (file・行・値) を出力、を検査し rc で返す。親は F の実 diff を全件読む。
- **R3 (相談 must-fix 2、採用):** D297 判定は C → F を GCC 11.4 / 12.3 で新規に起動する。job script は new OID を引数に取り、job 内で (a) new の親 = C2' 40a7f4acb174ca43cb590f40d13847216a1564bc、(b) C2'..new の変更 path = 3 file、(c) bundle の head = new、(d) bundle 内で C と new を解決できる、を照合してから起動する。report の old/new OID・result・compiler を親が照合する。検査器・起動引数・cache・prefix・scratch・walltime は前回と同じ。
- **R4 (相談 should 3、採用 = 削る):** 負例対照は再実施しない。検査器は前回 (82e9e780 の検査器、現 main でも同一 blob を親が段 5 前に照合) と同じで、D2277 項 1 (2) が要求するのは F の正例判定。これで既知の errexit 欠陥の経路も消える (script から負例部を除く)。
- **R5 (相談 must-fix 3・should 6、採用):** build は計算ノードで CI image `:ci` を apptainer exec し、CI の configure argv と `cmake --build build -j $(nproc)` をそのまま使う。job の最初に image の起動可否 (`g++ --version`・`cmake --version`・`ccache --version`・F の checkout の可読) を確かめ、失敗なら即 rc≠0。CI との差 = offline の依存供給 (`-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=<cache の複製>`・`-DFETCHCONTENT_FULLY_DISCONNECTED=ON`)、ccache は空、runner の資源。report に image の sha256 と `apptainer inspect` の digest/label、compiler 版、依存 3 つの HEAD OID と tree OID、追加 argv、nproc、所要、rc を記録する。記録の言い方は「CI image と CI の build 手順による手元通過」。GitHub Actions の緑は人間の push 後に確かめる別条件。F が赤なら C2' の build は親が別途決める (標準経路から外す)。
- **R6 (相談 should 4・nit 9、採用):** 予備 probe (fmt_scan・pp_probe・pp_probe_lines) は予測と明記し、根拠は F の実 diff・verify_format_only・CI 手順の rc・D297 report に置く。format は F の checkout で `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format --dry-run --Werror` の rc を、login の clang-format 14.0.0 と image `:latest` の clang-format の 2 通りで取る (login の静的検査)。
- **R7 (相談 should 5・8、採用):** 見積り = 判定 ≈ 1,000 秒 (前回の正例 2 起動並行 980・988 秒、負例を削る) + build (未実測) を 2 node 同時。実費は job Elapse で累計し、追加投入で 2 node 時間に届く見込みが出たら投入前にユーザー確認。
- **R8 (P5・P7 維持):** branch `izanagi-tpcc-v3-silo-mocc-fmt` (新 local branch)。izanagi repo の実装面差分は 0 → 変異 matrix 免除 (DW-S04)、受入全走は行う。
- **R9 (新事実の扱い):** GitHub に `izanagi-tpcc-v3-silo-mocc` が無い (D2277 項 1・4 の記録と食い違う) ことは記録と報告に書く。push 依頼は F の branch 1 本で足りる (C2' を祖先に含む)。

## 段 5 の分割

author A 1 本 (所有 = 子木 `output/runs/t2854-fmt-ci/` 配下の ccbench clone の 3 file、`scripts/run_judge.sh`・`scripts/run_ci_build.sh`・`scripts/verify_format_only.py`・`scripts/check_format_ci.sh`)。段 6 はレビュー 1 本。

## 追補 1 (段 5 の実装子 A の停止を受けて、15:2x JST — date 実測 15:22 の直前)

- R1 の完了条件「行番号マーカー込みの byte 一致」は親の誤り。足した `#line` 自身が前処理出力にマーカーを出すので、`#line` を足すかぎり原理的に成立しない (実装子 A が実測して停止、out/s5-author-A.md)。
- 守るべき性質は「TRACE=0 で出力される各コード行が C2' と同じ推定行番号を持つ」こと (`__LINE__` と debug 行情報に効くのはこれだけ)。R1 の完了条件をこれに置き換える: 3 file とも、`#include` 行を除いた入力の `g++ -E -dD -nostdinc -x c++ -DTRACE=0` 出力について、行番号マーカーで行番号を更新しながら「(推定行番号, 行の文字列)」の列 (マーカー行と空行を除く、`<stdin>` 由来の行だけ) を作り、C2' と一致すること (2 文脈)。定義の参照実装 = probe/presumed_lines.py (親の予測用)。
- 親の実測 (probe/presumed_lines.log): 子の作業ツリーで silo は一致、mocc は `#line 116` で +1 ずれ (整形だけだと -3)、trace.hh は TRACE=0 のコード行 0 で一致。verify_format_only.py の (vi) はこの定義で実装する。
