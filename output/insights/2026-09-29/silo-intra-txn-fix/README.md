# Silo の取引内の値の扱いの修正を CCBench の branch に入れた ([T-2905]・[T-2885]) — commit `7e5fa528`、上流 CI 2 本相当は緑、trace 実測で修正前は赤・修正後は 0 件、D297 は (a) が期待どおりの拒否、(b) は拒否 (原因は probe で確かめた範囲では `ERR` の行番号定数の差)。push はしていない (人間の手番)

authority: none
default_effect: no-state-change

- 日付: 2026-09-29
- wave: `dev-wave-silo-intra-txn-fix` (branch `worktree-dev-wave-silo-intra-txn-fix`)。着手時 local main `8fe87f852ec41e0a07a9be10bcb10e5d867117b4` (開始 gate rc=0、`verbatim/startup-gate.log`)
- 依頼: `/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/md_1.txt` (repo の外)。ユーザー裁定の逐語 (2026-09-29)「Siloに不具合があったなら直すよ。dev-wave文をください」 — [T-2885] の還元判断は CCBench に入れる方向で決着、上流への push は人間
- 一次資料 (不具合と修正案): `output/insights/2026-09-29/gen-opt-gate-liveness/README.md` (§1.2 patch、§2 結果、§4 限界、§6 還元候補)
- job dir (使い捨て script・生 log・Codex receipt・bundle・計算の全出力): `/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/`

## 0. 結論

| 項目 | 結果 |
|---|---|
| 修正 commit | CCBench の新 branch `izanagi-silo-intra-txn-fix` = **`7e5fa528037805dfc0459c742e4a21d6114c9799`** (親 F `25898d00`、tree `67ee0a27`)。変更は `cc/silo/transaction.cc` の 2 hunk だけで、修正案 patch (sha256 `2fca9651…`) を F に `git apply` した blob と一致 (`evidence/mk-fix.log`) |
| 上流 CI の format | 修正 tip の clean checkout で 213 file・rc=0 (login clang-format 14.0.0 と CI image :latest の 14.0.6)。対照 F も同じく rc=0 (`evidence/format-ci.log`) |
| 上流 CI の build | 計算ノードで CI image :ci (GCC 13.3.0、cmake 3.28.3、SIF sha256 `cb8cd1c3…`) の CI 手順で configure rc=0 (2 秒)・build rc=0 (22 秒)。警告 13 件はすべて第三者 masstree、CCBench 本体の警告・error は 0 件 (`evidence/ci/`) |
| trace 実測 (U0 と同じ照合器・2 workload) | 修正前 F: 取引内の値の照合 (D2b) が赤 (下表)。修正 tip: D2b 0 件・手順列と trace の照合 (D1) 0 件・既存の判定器 serializable・certified。事前登録と一致 (`evidence/trace/`) |
| D297 (a) F → 修正 tip | GCC 11・12 とも rc=1、`TRACE=0 正規化 preprocess 出力が不一致: path='cc/silo/transaction.cc'`。**事前登録どおりの期待拒否** (本物の修正は TRACE=0 のコードを変えるので一致しないのが正しい) |
| D297 (b) 合成 P′ (pin + 修正) → P″ (修正 tip と同じ tree) | GCC 11・12 とも rc=1、`header expanded 不一致: configure=stock entry=('<SOURCE>/cc/silo/transaction.cc', 'bomb_silo.exe')`。**事前登録 (pass) と不一致。** 親の probe (Silo の 1 file・TRACE=0・1 文脈) で見た差は `ERR` の `__LINE__` 定数 1 行 (pin + 修正は 693、修正 tip は 690)。検査器は最初の不一致で止まるので、他の entry の差の有無は確かめていない — §3 |
| patches/ の Silo 系 44 本 | F と修正 tip で判定が変わったのは V26 `broken-silo-stale-read-own-write`・V27 `broken-silo-repeat-update-buffer` の 2 本だけ (修正 tip に当たらない)。他 39 本は両方に当たり inert 一致、3 本は F でも当たらない ([T-2854] の範囲) — §4 |
| push | していない。§6 の依頼と、`#line` についての選択 (§3) をユーザーへ返す |

gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・`patches/` は変えていない。

## 1. 修正の中身

- `TxExecutor::read`: 書き込み集合を先に探し、無ければ読み集合、無ければ tuple を読む (元は読み集合が先で、書いた後の読みが最初の読みの値になった)。
- `TxExecutor::update`: 同じ key が書き込み集合にあれば、その要素の `body_` を新しい値で置き換える (元は 2 度目の書きの値を捨てた)。`op_`・`rcdptr_`・key は変えない。
- F の `#line` 635/658/679/700 は変えていない (段 4 裁定 R2)。修正で update の行数が +3 になるので、update から `#line 635` までの TRACE=0 行は論理行番号が 3 進み、`#line` 以降は F と同じ番号に戻る。`ERR` の展開値は F と同じ 106・690 (`evidence/line_probe.log`)。
- 変えていないこと (限界): INSERT・DELETE の要素への 2 度目の update、`scan` の読み集合優先。
- commit message は上流の流儀の英語 (Codex author)、trailer 3 行 (Codex author・Codex reviewer・Claude manager)。commit は親 (`evidence/mk-fix.log` に message 全文)。
- 土台の確認: commit 直前に主 checkout の submodule で `izanagi-tpcc-v3-silo-mocc-fmt` = F `25898d00` を確かめた。F の branch は wave 開始直後の確認 (`evidence/master-probe.log` の 21:49:54 JST より前、その生出力は保存していない) で GitHub に無い (`git ls-remote` に無く、Actions の run 0 件)。
- 上流 master `b28f96b6` の Silo にも修正案 patch が fuzz 0 で当たる (offset -16 / -68、`evidence/master-probe.log`)。

## 2. trace 実測 (計算ノード bnode005、request 36211.nqsv、Elapse 194 秒)

U0 と同じ照合器 (`gate_check.py`、sha256 `73a979d8…`) と flags (200 record・zipf 0.9・rratio 50・1 取引 5 操作・4 thread・1 秒、`KEY_SORT` 既定 0)。計装 patch は F 用に作り直した (repo 外、Codex author、sha256 `76a4234d…`)。F と修正 tip の両方に厳密適用で当たり、`#if TRACE` の枝を除くと土台と bytes 一致 (`verbatim/author-a.md`)。起動器 v2 (sha256 `9c2cf740…`) は bundle (sha256 `72f82e71…`) を clone して OID を checkout し、判定器の `--ccbench-root` はその build の計装済み checkout。

| build | workload | commit | abort | 到達可能性 | D1 a / b1 / b2 | D2b (i) | D2b (ii) | 発生条件 (自分の書きの後の読み / 書きのある取引) | 既存の判定器 | 事前登録 |
|---|---|---:|---:|---|---|---:|---:|---|---|---|
| F (修正前) | W-rmw | 193,103 | 8,594 | pass | 0 / 0 / 0 | 27,942 | 14,748 | 27,942 / 186,999 | serializable・certified、取引 193,103 | 一致 |
| F (修正前) | W-blind | 217,827 | 13,485 | pass | 0 / 0 / 0 | 1,482 | 16,835 | 16,737 / 210,919 | serializable・certified、取引 217,827 | 一致 |
| 修正 tip | W-rmw | 190,789 | 8,520 | pass | 0 / 0 / 0 | 0 | 0 | 27,491 / 184,873 | serializable・certified、取引 190,789 | 一致 |
| 修正 tip | W-blind | 220,264 | 13,191 | pass | 0 / 0 / 0 | 0 | 0 | 17,178 / 213,485 | serializable・certified、取引 220,264 | 一致 |

- 事前登録 (段 4 裁定 R5): 対照は D1 0 かつ D2b の違反合計 ≥1、修正は D1 0・D2b (i)(ii) とも違反 0 かつ各条項の発生条件 ≥1・判定器 certified・取引数 = commit 件数。発生条件が 0 なら判定不能 (合格にしない)。
- 修正前の (ii) の違反取引数は複数回の書きの取引数と一致 (W-rmw 14,748、W-blind 16,835)、W-rmw の (i) は自分の書きの後の読みを含む取引数 27,942 と一致した。U0 (pin `68106660`) の読み (28,217 / 14,966 など) と同じ構造である。
- 修正前の測定 (U0 と本表の F 行) は当時の build の事実として残す (規律 7)。修正後の stock は別 build。
- build ごとの source・binary・trace archive の sha256 は `evidence/trace/trace-1.summary.txt` と `result.json`。trace 原本 (tar.gz) は job dir の `runs/trace-1/` (repo の外)。

## 3. D297 (計算ノード bnode020、request 36212.nqsv、Elapse 1,978 秒。CI build と同じ job)

検査器は wave 木の `tools/check_trace0_preprocess_identity.py` (local main `8fe87f852` の版)、[T-2854] と同じ header 4 引数・GCC 11 と 12 の 2 起動。

| 比較 | GCC 11 | GCC 12 | 事前登録 | 判定 |
|---|---|---|---|---|
| (a) F → 修正 tip (`--expect-paths cc/silo/transaction.cc`) | rc=1、5 秒 | rc=1、4 秒 | 両方 rc=1、Silo の正規化前処理の不一致 | **一致** |
| (b) P′ `d078f0f0` (親 pin、tree = pin + 修正案) → P″ `26169333` (親 P′、tree = 修正 tip の tree) | rc=1、965 秒 | rc=1、971 秒 | 両方 rc=0 | **不一致** |

- (a) の拒否文は両方 `TRACE=0 正規化 preprocess 出力が不一致: path='cc/silo/transaction.cc' genome='silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0' context='base'` (`evidence/judge/a-gcc*.stderr`)。expect-paths の検査は通過し、最初の不一致が Silo の前処理出力。D297 は旧新の TRACE=0 の**一致**を見る検査なので、TRACE=0 のコードを意図して変える本物の修正では拒否が正しい結果である。
- (b) の拒否文は両方 `header expanded 不一致: configure=stock entry=('<SOURCE>/cc/silo/transaction.cc', 'bomb_silo.exe')` (`evidence/judge/b-gcc*.stderr`)。合成 commit は job dir の使い捨て clone にだけ作り (日時・作者固定、`evidence/mk-synth.log`)、branch にしていない。P′→P″ の差分 path は pin → F と同じ 4 file。
- **(b) の原因 (親の probe、`evidence/line_probe_b.log`):** P′ と P″ の `cc/silo/transaction.cc` を、include 行を空行にし `ERR` を `IZ_ERR_AT(__LINE__)` と定義して TRACE=0 で前処理すると、差は 1 行だけ — P′ `IZ_ERR_AT(693)`、P″ `IZ_ERR_AT(690)`。pin には `#line` が無いので修正の +3 行がそのまま後ろの行番号に効くが、F の `#line 679` は行番号を修正前の値に戻すので、修正 tip では 690 のまま。検査器の header 分岐は include を展開するので `ERR` (debug.hh の `NNN` 経由の `__LINE__`) が定数になって差が現れ、`-P` で include を除く .cc の比較では現れない。
- **読み:** probe で確かめた範囲 (Silo の `cc/silo/transaction.cc` 1 file、include を除いた TRACE=0、1 文脈) では、修正 tip と pin + 修正の差は `ERR` の行番号定数 1 行だけだった。検査器は最初の不一致で止まるので、他の entry・文脈に差があるかは確かめていない。F の `#line` は「trace の整形が TRACE=0 の行番号を変えない」ために置かれたが、修正を挟むと修正の行数ぶんまで打ち消す。段 4 裁定 R2 (`#line` を変えない) は段 3 の相談も親もこの帰結を見落としていた。
- **選択肢 (ユーザーへ返す、§6):** (A) このまま push する。`ERR` の行番号は F と同じ、TRACE=0 は pin + 修正と (probe の範囲では) `ERR` の定数が違う。(B) push の前に 1 commit を足し、update より後の `#line` 4 本 (635/658/679/700) をそれぞれ +3 する。修正 tip の TRACE=0 が pin + 修正と一致する見込み (予測) で、(b) を取り直して確かめる (本 wave の実績では (b) が GCC 11 965 秒・GCC 12 971 秒、CI build と (a) を含む job の Elapse 1,978 秒 ≈ 0.55 node 時間。(b) だけなら約 1,000 秒の見込み)。依頼が「修正案と同じ変更を 1 commit」なので、本 wave は (A) の形で止めた。推奨は (B) (trace の `#line` が TRACE=0 の定数を変えない状態に戻せる。どちらも性能と正しさには影響しない — `ERR` の定数は異常終了時の表示にだけ使われる)。

## 4. patches/ の Silo 系 44 本の棚卸し (login、`evidence/inventory/`)

棚卸し script (repo 外、Codex author、sha256 `3c060a6f…`) を親が修正 tip の実物で走らせた (`inventory.md` sha256 `c61fd8ce…`)。方法: 各 patch の重ね順の前提を patches/README と driver から出典付きで表にし、F・修正 tip・pin の clean な一時 worktree に前提を当てた後で素の `git apply --check` (driver の `apply_patch` と同じ) → 実適用。当たったものは stock の define (D297 検査器の `_head_defines` と同じ取得系) を与え TRACE=0 / 1 で前処理して、前提だけを当てた土台と比べる (inert 照合)。hunk が修正の 2 領域と重なるかも判定した。

| 分類 | 件数 | patch |
|---|---:|---|
| A: F・修正 tip とも当たり inert 一致・修正領域と重ならない | 39 | (表 `inventory.md`) |
| C: F に当たり修正 tip に当たらない | 2 | V26 `broken-silo-stale-read-own-write` (read の 214 行付近で文脈不一致)、V27 `broken-silo-repeat-update-buffer` (update の 526 行付近) |
| D: F でも当たらない | 3 | `broken-silo-corrupt-write-payload`・`broken-silo-published-version-mismatch` (pin には当たる、F の writePhase の整形・trace v3 で文脈が変わった)、`silo-backoff-requested-us` (pin でも当たらない、`cmake/Options.cmake`・`include/backoff.hh`) |
| B (当たるが修正領域と重なる)・E (当たるが inert 不一致) | 0 | — |

- F → 修正 tip で判定が変わったのは V26・V27 の 2 本だけ。
- 最初の棚卸し (fix 前の script) は E を 18 本出したが、軸マクロ (`SORT_VARIANT` など) を未定義で前処理して `#error` に当たった誤検出で、stock の define で照合し直して 0 になった (段 6 の親の実走で判明、`verbatim/fix-1.md`)。
- **裁定 (段 4 R9):** patches/ は編集しない。V26・V27 は修正で「壊す相手」の挙動が変わる (V26 は旧い探索順での自分の書きの読みを旧 tuple の値に戻す変異、V27 は「2 度目の書きを捨てる」stock を前提に buffer を壊す変異)。gitlink を修正 tip へ進める wave で、修正後の挙動を壊す形に作り直す (V26 = 書き込み集合を先に返す読みを旧 tuple の payload に戻す、V27 = 2 度目の update の置換を old・new どちらとも違う byte にする。どちらも既定 OFF inert・発火計数つき)。D の 2 本 (pin に当たるもの) は F への前進 ([T-2854]) の範囲。変異を外して緑にしない (規律 2)。
- 限界: 重なり判定は hunk の行範囲だけを見る。修正の 2 領域に触れないが read・update の挙動に意味で依存する patch (例: write set を操作する write-intent 系) の意味の変化は、この棚卸しでは判定していない。

## 5. 段の経過と費用

- 軽量版: 段 2 省略、段 3 相談 1 本 (所見 8 件すべて採用、`verbatim/consult-a.md`・`s4-ruling.md`)、段 5 author 1 本、段 6 レビュー 1 本 (NO-GO: must-fix 3・should 2、`review-a.md`) → fix 1 本 → 焦点再レビュー 1 本 (GO、R01〜R06 closed、`focus-1.md`)。
- 焦点再レビューの N01 (should): `mk-fix.sh` の commit 後の表示行 (`F branch:`) が wave 木の submodule git dir で ref を引いて失敗しても rc=0 で進んだ。commit 前の照合は主 checkout の submodule の ref を読んで F を確かめており (`evidence/mk-fix.log` 6 行目)、表示行だけの欠陥として記録にとどめた。
- 親の near miss: `mk-fix.sh` の 1 回目は F の ref を wave 木の submodule git dir で引いて見つからず、何も作らずに停止した (`evidence/mk-fix-attempt1.log`)。branch ref は主 checkout の submodule git dir にだけあり、wave 木の git dir には object だけがある。
- 計算: 36211.nqsv 194 秒 + 36212.nqsv 1,978 秒 = 2,172 秒 ≈ 0.60 node 時間 (2 node 時間の線の下)。
- Codex 子: consult・author・review・fix・focus の 5 本 (全て gpt-6-sol / medium)。
- 変異 matrix: repo の実装面の差分 0 (本 wave の commit は insight と spool fragment だけ) なので DW-S04 により免除。修正の検出力は修正前 F の D2b 赤 (§2) が担う。

## 6. push の依頼 (人間の手番)

修正の branch は land 後に主 checkout の submodule git dir へ非 force で取り込む (本 wave の段 9)。その後、主 checkout で:

```
cd external/ccbench
git push origin izanagi-silo-intra-txn-fix
```

- 別名の新 branch なので force は不要。祖先の F (`izanagi-tpcc-v3-silo-mocc-fmt`、未 push) と C2′ も一緒に上がる。
- push の前に §3 の (A)/(B) を選ぶ。(B) なら push 前に `#line` の +3 を 1 commit 足す wave が要る。
- push 後に GitHub の Actions で build・format が緑であることを確かめる。gitlink を修正 tip へ進めるのは、F への前進 ([T-2854]) が main に着地し、この CI が緑になった後の別 wave (spool で起票)。

上流 (thawk105/ccbench の master) へ送る説明文の下書き:

```
fix(silo): preserve the latest value within a transaction

TxExecutor::read looked up the read set before the write set, so a read
after a write in the same transaction could return the value of the
earlier read. TxExecutor::update returned early when the key was already
in the write set, so the value of a second update to the same key was
discarded.

Reproduced with YCSB (200 records, Zipf 0.9, 50% reads, 5 ops/tx, RMW on,
4 threads, 1 s): 28,217 committed transactions read a value different
from their own write and 14,966 did not install their last write.
Serializability checks on versions do not see this, because YCSB does
not branch on values.

Fix: search the write set first in read, and replace the pending write's
body on a repeated update. A second update to an INSERT or DELETE entry
and scan's read-set priority are unchanged. The patch applies to master
(b28f96b6) without fuzz.
```

## 7. 主張しないこと

- GitHub Actions の CI が緑であること (push 前。手元は CI image と CI の手順による再現)。
- 修正後の Silo で全 API の取引内の意味がそろったこと (§1 の限界)。
- D297 (b) の差が `ERR` の定数だけであること (probe は Silo の 1 file・TRACE=0・1 文脈、検査器は最初の不一致で止まる)。(B) で (b) が pass になること (予測)。
- 構成を変えたとき (record 数・thread 数・`KEY_SORT=1`・TPC-C) の D1・D2b。各構成 1 回。
- 性能 build への影響の大きさ (修正は stock の命令列を変える、測っていない)。

## 8. 再現資料

- `verbatim/`: 段 1 brief、段 3 相談、段 4 裁定、実装子・レビュー・fix・焦点再レビューの報告、開始 gate。
- `evidence/`: commit (`mk-fix.log`・1 回目 `mk-fix-attempt1.log`)、合成 commit (`mk-synth.log`)、format (`format-ci.log`)、上流 master (`master-probe.log`)、行番号 probe (`line_probe.log`・`line_probe_b.log`)、trace (`trace/`)、D297 (`judge/`)、CI build (`ci/`、dispatch log `cijudge-1.log`)、棚卸し (`inventory/`)。dispatch log の `| ` 行の行末空白は §9 の正規化。
- job dir: 使い捨て script (Codex author の `fix1-out/scripts/`・計装 patch `fix1-out/patches/`、親の `mk-fix.sh`・`mk-synth.sh`・`format-ci.sh`・`inv-run.sh`・`run-trace.sh`・`run-cijudge.sh`・probe)、Codex receipt (`artifacts/`)、`fix.bundle` (sha256 `72f82e71…`)・`synth.bundle` (sha256 `b2fbe213…`)、計算の全出力 (`runs/`)。

## 9. 写しの可逆な最小正規化

`git diff --check` に掛かる行末空白 (space / tab) だけを、写した 8 file (`evidence/ci/build.log`・`evidence/ci/configure.log`・`evidence/cijudge-1.log`・`evidence/line_probe.log`・`evidence/line_probe_b.log`・`evidence/mk-fix.log`・`evidence/trace/trace-1.log`・`verbatim/review-a.md`) から除いた。可視文字は変えていない。file ごとの原本 sha256・byte 数・正規化後 sha256 と、除いた行 (1 始まりの行番号と除いた文字列) は `NORMALIZATION.json` にある。復元は、記録した各行の末尾へ除いた文字列を足し戻す。原本は job dir の同名 file (ただし `evidence/line_probe.log` の原本は job dir の `probe/line_probe.log`、`evidence/line_probe_b.log` の原本は `probe/b.log`)。
