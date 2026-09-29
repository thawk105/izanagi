# [T-2854] pin 前進 (1)(2) — C2' の上に clang-format 14 の整形 commit F `25898d00` を乗せ、CCBench の CI 2 本 (format・build) を CI image で手元通過し、D297 規則 v2 で C → F を GCC 11.4 / 12.3 とも pass と判定した。push はしていない (人間の手番)

authority: none
default_effect: no-state-change

- 日付: 2026-09-29
- wave: `dev-wave-t2854-ccbench-format-ci` (branch 同名)。着手時 local main `035fc11fa601547f5d68e54f5661c5daa70b93a5` (開始 gate rc=0、`verbatim/startup-gate.log`)。判定 job の終了後に local main `ce124f388` を fast-forward で取り込んだ (検査器・buildcache・genome に変更なし)
- 依頼: D2277 項 1 の (1)(2)。承認の逐語 = ユーザー「1, 推奨通り。あなたの仕事はのちにCI落ちしたりしていた。CCBench CIが通る品質を意識してください。」(D2277)
- 既裁定: D2277 項 1、D2275、D2255、D780 項 1、D95、D16・D18・D20、D2212 項 4、F1056
- job dir (使い捨て script・生 log・Codex receipt・bundle・image・計算の全出力): `/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/` (= `/work/1/SFC/tanab/tmp/...`)

## 0. 結論

1. **F:** CCBench の新しい local branch `izanagi-tpcc-v3-silo-mocc-fmt` = C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` の子 **F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e`** (tree `c96b282d`)。変更は `cc/mocc/transaction.cc`・`cc/silo/transaction.cc`・`include/trace.hh` の 3 file (mode 不変、79 行追加 / 77 行削除) で、clang-format 14 の整形と `#line` 3 本だけ。整形した行はすべて `#if TRACE` 区間内で、足した `#line` 3 本はその区間の直後 (`#endif` の次の行) にある。F の作成は Codex author (D95)、commit は親 (trailer 3 行 = Codex author・Codex reviewer・Claude manager)。bundle = job dir `F.bundle` (3,206,018 byte、sha256 `5253d961…`、complete history、`git bundle verify` 済み)。
2. **`#line` を足した理由 (段 4 の新事実):** 整形だけだと、行数が変わる `#if TRACE` 区間の後ろで TRACE=0 の論理行番号がずれる (mocc -3、silo は区間ごとに +1 ずつ、最大 +2)。mocc の TRACE=0 有効コードの `ERR;` は `include/debug.hh` の `NNN` 経由で `__LINE__` に展開されるので、**trace 用コードの整形が TRACE=0 の性能計測 build を変える** (規律 1)。そこで区間直後に `#line` を置き、TRACE=0 の全コード行の行番号を C2' と一致させた (mocc `#line 115`、silo `#line 365`・`#line 381`)。D2277 の「意味を変えない整形だけ」の趣旨を守るための付随変更で、判断と理由は本 wave の decisions fragment に記録した。
3. **CI の format (完了条件 a):** F の checkout (bundle から clean に取り出したもの) で CI の step (`git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format --dry-run --Werror`) を 2 通り回し、**どちらも 213 file・rc=0**: login の clang-format 14.0.0 と、CI image `:latest` (`ghcr.io/thawk105/ccbench-devcontainer`、manifest `sha256:aa58dc0d…`) の clang-format 14.0.6。対照として同じ手順を C2' に当てると rc=123・違反 84 件 (mocc 36・silo 23・trace.hh 25) で、事前の数え上げと一致 (`verbatim/evidence/format-ci-F.log`・`format-ci-C2p-control.log`)。
4. **CI の build (完了条件 b):** 計算ノード (request 35484.nqsv、bnode036、48 core、Elapse 33 秒) で CI image `:ci` (manifest `sha256:8f4ee69d…`、SIF sha256 `cb8cd1c3…`、GCC 13.3.0・cmake 3.28.3・ccache 4.9.1) を apptainer (`--userns`) で動かし、CI と同じ `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache` と `cmake --build build -j 48` で **configure rc=0 (2 秒)・build rc=0 (22 秒)**。生成された実行 file は 38 本で、CMake の検出用 4 本を除く CCBench の実行 file は 34 本 (protocol の benchmark 33 本と `replay_test.exe` 1 本、CI の記述「34 binaries」と一致)。警告 13 件はすべて第三者の masstree 内で、CCBench 本体 (`cc/` `include/` `common/`) の警告・error は 0 件 (`verbatim/evidence/build-report.json`・`build-build.log`)。
5. **D297 (完了条件 c):** 規則 v2 の検査器 (blob `f4f7913a`、D2275 の判定時と同一) で **C `68106660` → F `25898d00` は GCC 11.4 (974 秒) と GCC 12.3 (983 秒) の両方で pass (rc=0)**。request 35460.nqsv、Elapse 988 秒。選定 configure 17 (stock・mocc 0〜7・silo 0〜7)、未選定の調査 tictoc 24・cicada 24 (consumer なし)、consumer 21 entry / 12 file、compiler ごとに比較の予定 357 = 実行 357、集約後の実比較 118 件はすべて完全展開・include 活性とも一致、`.cc` 2 本 (mocc・silo の transaction.cc) も既存の文脈で match、gitlink `third_party/shirakami` (fb14e659) は旧新一致 (`verbatim/evidence/judge-gcc11.report.json`・`judge-gcc12.report.json`)。
6. **pin は C のまま。** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・`patches/` は変えていない。push もしていない。F の branch の push と GitHub の CI 確認は人間の手番、その後の同時更新と patch 54 本の厳密適用は別 wave (D2277 項 1 (3)(4))。
7. **新事実 (D2277 の記録との食い違い):** D2277 項 1・4 は「C2' の branch `izanagi-tpcc-v3-silo-mocc` はユーザーが既に push していた (GitHub の ref は `40a7f4acb`)」と書くが、2026-09-29 16:24:10 JST (date 実測) の確認時点で **GitHub に無い**: `git ls-remote https://github.com/thawk105/ccbench.git` の izanagi 系は 6 branch でこの名は無く、GitHub API は `/branches/izanagi-tpcc-v3-silo-mocc` に 404 (Branch not found)、同 branch の Actions の run は 0 件、C2' の commit `40a7f4ac` 自体も `/commits/<sha>` が 422 (No commit found) を返した (生応答 = `verbatim/evidence/github-check.log`)。wave 開始時と 16:05 にも同じ結果だったが、その生出力は保存していない。主 checkout の submodule にも `refs/remotes/origin/izanagi-tpcc-v3-silo-mocc` は無い。確認後に人間が push した可能性は排除しない。F の branch を push すれば祖先の C2' も一緒に上がるので、本題は止まらない。

## 1. 完了条件と状態

| 完了条件 (依頼・段 1) | 状態 |
|---|---|
| C2' の上に整形だけの commit、Codex author | **済** — F `25898d00` (整形 + TRACE=0 の行番号を戻す `#line` 3 本、§0 の 2) |
| format.yml と同じ clang-format 14 `--dry-run --Werror` | **済** — 213 file・rc=0 (login 14.0.0 と CI image 14.0.6) |
| build.yml と同じ Release・sanitizer OFF の全 protocol build | **済** — CI image `:ci` で rc=0 (CI との差は §3) |
| 新 tip で D297 規則 v2 を C 基点で取り直す | **済** — GCC 11.4・12.3 とも pass (F に限る) |
| push は人間へ返す | 返す (§6) |
| 2 node 時間以上ならユーザー確認 | 実費 1,030 秒 ≈ 0.29 node 時間 (§4)、確認線の下 |
| D297 の合格は新 tip に限る、TPC-C の certified を名乗らない、規律 1・2 不変、scope 外を足さない | 守った (§7) |

## 2. F の中身と意味不変の照合

- 差分の逐語 = `verbatim/C2p-to-F-diff.md`。整形の hunk は mocc 25〜115 行 (先頭の `#if TRACE` 区間、24〜115) と 1159〜1306 行の 6 区間、silo 362〜364・378〜380・584〜659・738〜744、trace.hh 108〜170 (25〜173 の区間) で、整形した行はすべて `#if TRACE` 区間内 (親が C2' の条件指令の入れ子と照合した)。足した `#line` 3 本はそれぞれの区間の `#endif` の直後にある。
- 照合 (親と Codex の 2 系統):
  - Codex author の `verify_format_only.py` (job dir `scripts/`、sha256 は `job-dir-sha256.md`) を F の commit に当てて rc=0 (`verbatim/evidence/verify-F-commit.json`): (i) C2'..F の raw diff = 3 file・mode 不変、(ii) 足した `#line` 行を除いて空白を全部除いた bytes が一致、(iii) 文字列・文字 literal の列が一致、(iv) 前処理指令の列が足した `#line` を除いて一致、(v) 足した `#line` の一覧、(vi) TRACE=0 の推定行番号の列が一致 (2 文脈)。
  - 親の独立 probe (job dir `probe/`、予測用): `presumed_lines.py` で 3 file × 2 文脈の推定行番号の列が一致 (`verbatim/evidence/parent-checks.log`)、`line_macro_probe.py` で `ERR` の `__LINE__` 展開値が C2' と F で一致 (mocc 522・1193、silo 106・690、`line_macro_probe.log`)。
  - 検証器の (ii) は空白を全部除くので TRACE=1 側の字句の結合を見逃しうる (段 6 S6-2)。そのため親が diff 全件を読み、字句・文字列・コメント文言・既存 directive の値に変化が無いことを確かめた。
- `#line` の値: mocc は 115 (C2' の 17 行目に既存の `#line 17` があり、以降の物理行は論理行番号が 1 小さいため、物理 116 行 = 論理 115 行)。silo は 365・381。
- 決め手は D297 の本判定 (§0 の 5) で、上の probe は予測である。

## 3. build の CI 同等性 (言える範囲)

「CI image と CI の build 手順による手元通過」であり、GitHub Actions の緑ではない。CI との差:
- 依存の供給: CI は FetchContent が GitHub から取得する。手元は計算ノードが offline なので、手元 cache (`/work/1/SFC/tanab/izanagi-thirdparty-cache`) から `git clone --no-local` で scratch へ取り出し、pin (masstree b3c5d054・mimalloc v2.3.2 = 02a2f5df・googletest f8d7d77c、ThirdParty.cmake の TAG と一致) を detached で checkout し、`git status --porcelain --ignored` が空であることを確かめてから `-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=…` と `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` で渡した (追加 argv はこの 4 つだけ、report に CI argv と分けて記録)。
- ccache は空から (CI は前回の cache を restore)。runner の資源 (CI の runner に対し手元は 48 core)。
- image は 2026-09-29 に取得した tag の実体 (上記 manifest digest)。GitHub の CI が走る時点で tag が動いていれば別の image になる。
- 1 回目 (request 35469.nqsv、Elapse 9 秒) は計算ノードの apptainer が setuid 方式で起動しようとして `starter-suid doesn't have setuid bit set` で失敗し、job の先頭の起動確認で rc=3 に止まった (login の同じ apptainer 1.4.5 は starter-suid に setuid bit があり動く)。`--userns` を明示して 2 回目で通った (`verbatim/evidence/build-attempt1-preflight.log`)。

## 4. 費用

| 計算 | request | Elapse |
|---|---|---|
| D297 判定 (GCC 11・12 並行) | 35460.nqsv | 988 秒 |
| CI build 1 回目 (起動確認で停止) | 35469.nqsv | 9 秒 |
| CI build 2 回目 | 35484.nqsv | 33 秒 |

合計 1,030 秒 ≈ 0.29 node 時間 (受入を除く)。見積り (段 4 R7: 判定 ≈ 1,000 秒 + build 未実測) の範囲。Codex 子 9 本 (全子 gpt-6-sol / medium: 相談 1・author 2・review 2・fix 2・焦点 1・段 7 の記録レビュー 1) で model call 125、wall 1,681.9 秒。うち review 1 本 (6 call・70.0 秒) は親の投げ文の path 誤りで不受理。login では image の取得 (約 1 時間、Lustre 混雑) と format の静的検査だけを行った。

## 5. 経過

### 5.1 段 1〜4
- 軽量版 (段 2 省略、段 3 相談 1 本・段 6 レビュー 1 本)。受理集合と正しさ防壁は変えないが、計算ノード job を投げて数値を書く wave なので相談とレビューを 1 本ずつ残した。
- 段 3 相談 (`verbatim/s3-consult-A.md`) の must-fix 3 件 (空白除去一致だけでは不足、D297 の結果を F に結び付ける、build の「CI と同じ」の範囲を明示) と should 4 件を段 4 で採用した。負例対照の再実施は削った (検査器は D2275 の判定時と同一 blob、D2277 項 1 (2) が求めるのは F の正例)。
- 段 4 の前に親が行番号マーカー込みで比べ直し、整形だけだと TRACE=0 の行番号がずれて `ERR` の `__LINE__` 定数が変わることを見つけた (`verbatim/evidence/pp_probe_lines.log`)。段 4 裁定 R1 で `#line` を足す形にした (`verbatim/s4-ruling.md`)。

### 5.2 段 5・6
- 実装子 A は、親の書いた完了条件「行番号マーカー込みの byte 一致」が成立しないことを実測して規定どおり停止した (140 秒)。`#line` 自身が前処理出力にマーカーを出すので、この条件は原理的に満たせない (親の誤り、本 wave の failures fragment に新規として記録)。守るべき性質を「TRACE=0 の各コード行の推定行番号の列」に直して (段 4 追補 1) 続きの A2 を投げ、mocc の `#line` を 116 → 115 に直して成立した。
- 段 6 レビュー 1 本目は親の投げ文の相対 path (`probe/line_macro_probe.log`) を子が `review/` 相対と読み、規定どおり即停止した (F819 の型、同 fragment に再発として記録)。全 path を絶対化して再投入した A2 は NO-GO で、must-fix 1 件 = 親の事前所見 P-1 (build script が依存 cache を `cp -a` で複製し、masstree の cache に残る git 管理外の `config.h`・`.a`・`.o` を持ち込む。masstree の custom command は出力があれば作り直さないので、CI image の build で手元 GCC の古い生成物を使いうる)。fix 1 で clean clone に直し、焦点再レビュー F1 は GO (`verbatim/s6-ruling.md`・`s6-review-A2.md`・`s6-fix1.md`・`s6-review-F1.md`)。
- fix 2 (実機 blocker、§3 の setuid) は `--userns` と `--home` の指定だけの変更で、子の login での実走は Codex sandbox の `getsockopt: operation not permitted` で rc=255 だった。親の環境では同じ command が rc=0 (GCC 13.3.0 を表示) で、sandbox 由来の偽赤と判定した。計算ノードの 2 回目の build の成功で閉じた (DW-O16、実行環境依存の変更は実走で閉じる)。
- 親の near miss: F を commit する script の mode 照合の awk が `:100644` と `100644` を比べて常に不一致になり、commit 前に rc=11 で止まった (fail-closed)。一時 worktree と直前に作った空 branch を撤去し、照合を直して再実行した (`verbatim/evidence/mk-F.log` は 2 回目、1 回目は job dir `mk-F-attempt1.log`)。

### 5.3 段 7 記録レビュー

記録 (本 insight と fragment 3 本) を独立 read-only レビュー 1 本 (`verbatim/s7-review-record.md`、29 call・289.0 秒) が一次資料と照合した。判定値・所要・件数の主要部は一致。NO-GO の所見 5 件のうち、GitHub に C2' の branch が無いことの生出力の欠落 (must-fix)、実行 file 34 本の内訳、`#line` の位置、118 件が compiler ごとであることの 4 件を直し、worklog の `base:` が元本文の raw sha256 と違うという所見は定義の違い (fold の base digest) として refuted にした (`verbatim/s6-ruling.md` 追補)。

### 5.4 変異
izanagi repo の実装面の差分は 0 (本 wave の commit は insight と spool fragment だけ) なので、変異 matrix は DW-S04 により免除。F の検査は format の対照 (C2' で rc=123) と D297 本判定が担う。

## 6. push の依頼 (人間の手番)

F の branch は land 後に主 checkout の submodule の git dir へ非 force で取り込む (本 wave の段 9)。その後、主 checkout で:

```
cd external/ccbench
git push origin izanagi-tpcc-v3-silo-mocc-fmt
```

別名の新 branch なので force は不要。C2' (`40a7f4ac`) は GitHub に無いが (§0 の 7)、F の祖先として一緒に上がる。push 後に GitHub の Actions で build・format が緑であることと、GitHub から F を取得できることを確かめてから、gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新と patch 54 本の厳密適用を別 wave で行う (D2277 項 1 (3)(4))。

## 7. 主張しないこと

- GitHub Actions の CI が緑であること (push 前。§3 の差がある)。
- D297 の pass は **F `25898d00` の結果に限る**。保証は D2255 項 2 の名 (選定した macro context における TRACE=0 正規化 preprocess 出力と include 活性の同一性) のままで、trace のコンパイル時完全除去の証明ではない (D780 項 1)。選定外の文脈・GCC 以外は範囲外。
- TPC-C の certified、pin 前進の完了、patch の F への適用可否。
- TRACE=1 の build の成功 (CI の build は既定の TRACE で、trace 有効の build は回していない)。
- 予備 probe (`fmt_scan`・`pp_probe`・`pp_probe_lines`・`presumed_lines`・`line_macro_probe`) の一般化 (`#include` を除いた模擬、2 文脈)。

## 8. 再現資料

- `verbatim/`: brief・相談・段 4 / 段 6 裁定・実装子 2 本・fix 2 本・レビュー 2 本の報告・開始 gate・F の差分 (`C2p-to-F-diff.md`)・job dir の sha256 (`job-dir-sha256.md`)。
- `verbatim/evidence/`: 判定 report 2 本、build の report・configure / build log・1 回目の起動確認 log、format の本走と対照、親の照合 log、検証器の JSON、予備 probe の生出力、F の commit log。
- job dir: 使い捨て script (Codex author の `judge/run_judge.sh`・`build/run_ci_build.sh`・`scripts/`、親の投入・commit script)、Codex receipt (`codex/`)、F.bundle、image 2 つ (`images/`)、計算の全出力 (`evidence/`)。
