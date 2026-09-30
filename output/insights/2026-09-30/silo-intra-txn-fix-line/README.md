# Silo の取引内の値の修正に `#line` +3 の 1 commit を足した ([T-2905]・[T-2885]、D2305 項 5) — 新 tip `dbac49b6`、上流 CI 2 本相当は緑、D297 (b) は GCC 11・12 とも一致 (予測どおり)、trace で D1・D2b は 0 件のまま。push はしていない (人間の手番)

authority: none
default_effect: no-state-change

- 日付: 2026-09-30
- wave: `dev-wave-silo-intra-txn-fix-line` (branch `worktree-dev-wave-silo-intra-txn-fix-line`)。着手時 local main `4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037` (開始 gate rc=0、`verbatim/startup-gate.log`)。記録前に local main `51765ae6c` を fast-forward で取り込んだ (gitlink は C `68106660` のまま)
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_12.txt` と同 dir の `common-4.txt` (repo の外)。裁定: D2305 項 5 (択 B)・項 6
- 前 wave の一次資料: `output/insights/2026-09-29/silo-intra-txn-fix/README.md` (§3 が本件の原因、§6 が前回の push 依頼)
- job dir (使い捨て script・生 log・Codex receipt・bundle・計算の全出力): `/work/1/SFC/tanab/tmp/silo-intra-txn-fix-line-2026-09-30/wave/`

## 0. 結論

| 項目 | 結果 |
|---|---|
| 新 tip | CCBench の branch `izanagi-silo-intra-txn-fix` = **`dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43`** (親 `7e5fa528`、tree `8fa00fea`)。変更は `cc/silo/transaction.cc` の `#line` 4 行だけ (635→638、658→661、679→682、700→703)。`evidence/mk-line.log` |
| 予測 (計算前、login) | pin + 修正 (合成 P′) と新 tip の file を、include を除き `ERR` を `IZ_ERR_AT(__LINE__)` にして TRACE=0 で前処理 → `ERR` は両方 106・693、出力は一致。旧 tip `7e5fa528` は 106・690 (`evidence/predict.log`) |
| 上流 CI の format | 新 tip と対照 `7e5fa528` の clean checkout で 213 file・rc=0 (login clang-format 14.0.0 と CI image :latest の 14.0.6)。`evidence/format-ci.log` |
| 上流 CI の build | 計算ノード (bnode009、37765.nqsv) で CI image :ci (GCC 13.3.0、cmake 3.28.3、SIF sha256 `cb8cd1c3…`) の CI 手順: configure rc=0 (1 秒)・build rc=0 (22 秒)。警告 13 行は masstree の 12 行 (`kvthread.cc`・`json.cc`・`log.cc`・`log.hh`・`configure.ac`) と make の jobserver 通知 1 行で、CCBench 本体 (`cc/`・`include/`) の警告・error は 0 件。`evidence/ci/` |
| D297 (b) 合成 P′ `d078f0f0` → P‴ `7e07ed13` (tree = 新 tip の tree) | **GCC 11 rc=0 (971 秒)・GCC 12 rc=0 (982 秒)、両方 `result: pass`、stderr 空。** 事前登録 (両方 rc=0) と一致。前回 (P″ = 旧 tip の tree) は両方 rc=1 だった。`evidence/judge/` |
| trace (U0 と同じ照合器・2 workload) | 対照 F は取引内の値の照合 (D2b) が赤、新 tip は D2b・手順列の照合 (D1) とも 0 件、既存の判定器は 4 run とも serializable・certified。4 run とも事前登録と一致 (§3) |
| push | していない。§5 の依頼をユーザーへ返す |

gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・`patches/` は変えていない。主 checkout の submodule の branch ref は land 後に `7e5fa528` → `dbac49b6` へ fast-forward で進める (本 wave の段 9、§5)。

## 1. commit の中身

- 前 commit `7e5fa528` は `TxExecutor::update` に 3 行を足した (同じ key への 2 度目の update で値を置き換える修正)。その後ろにある `#line` 4 本は、trace 用の整形で変わった行数を打ち消して trace 無しの source の論理行番号を保つ固定値なので、修正の 3 行まで打ち消していた。そのため TRACE=0 の `__LINE__` (`ERR` の表示) が「trace 無しの source + 修正」(= pin + 修正) と 3 行ずれ、D297 の補助比較 (b) が header 分岐で拒否していた (前 wave §3)。
- 4 本を +3 して一致させた。`#line 365`・`#line 381` は update より前 (read の修正 hunk は行数 ±0) なので変えていない。
- 実行の意味は変わらない。変わるのは診断に使う行番号 (TRACE=0 と TRACE=1 の両方の `__LINE__`) だけ。
- file 変更と英語 message は Codex author、commit は親 (`commit -F`)。trailer 3 行 (Codex author・Codex reviewer・Claude manager) は commit 前後で段 4 裁定 R1 と行単位で照合した (`evidence/mk-line.log` に message 全文)。
- 土台の確認: commit 直前に主 checkout の submodule の `refs/heads/izanagi-silo-intra-txn-fix` が `7e5fa528` であることを確かめた (同 log)。wave 木の submodule git dir に同名 local branch を `7e5fa528` から作って 1 commit し、`line.bundle` (sha256 `6e578792…`) に固めた。

## 2. D297 (b)

- 構成: 前回の合成 P′ `d078f0f05b7fc4b668d65f4a5d37f7f5af2e693c` (親 pin `68106660`、tree = pin + 修正案) を使い、P‴ `7e07ed13cb34d8933b75199ad8af55a150e2a9a3` (親 P′、tree = 新 tip の tree、作者・日時固定) を job dir の使い捨て clone にだけ作った (`evidence/mk-synth2.log`)。P′→P‴ の差分 path は pin → F と同じ 4 file。
- 検査器は wave 木の `tools/check_trace0_preprocess_identity.py` (sha256 `bcd46b29…`、前回と同じ)、header 4 引数、`--expect-paths cc/mocc/transaction.cc cc/silo/transaction.cc include/tpcc.hh include/trace.hh` (段 3 相談 C3 で追加。差分 path 集合の厳密一致を足すだけで判定は緩めない)。GCC 11 は 37765.nqsv (CI build と同じ job)、GCC 12 は 37772.nqsv (別ノード)。
- 結果: 両方 `result: pass`、header 分岐の比較 357 件 (planned = executed、重複除き 118 件)、genome 8・1 file あたり文脈 16 (`evidence/judge/b-gcc1{1,2}.report.json`)。
- (a) F → 新 tip と `7e5fa528` → 新 tip は回していない (段 3 相談 C4: 取引内の値の修正と行番号の差で拒否が見込まれ、(b) の証拠を増やさない)。前回の (a) (F → 旧 tip、期待どおりの拒否) を参照する。
- **読み:** 新 tip の TRACE=0 正規化前処理出力と include 活性は、検査器が選ぶ macro 文脈で pin + 修正と一致する。後続 [T-2917] の gitlink 前進で「本物の修正は旧新一致が成り立たない」を扱う材料として、この (b) を使える。

## 3. trace (計算ノード bnode001、request 37764.nqsv、Elapse 195 秒)

U0 と同じ照合器 (`gate_check.py`、sha256 `73a979d8…`) と flags (200 record・zipf 0.9・rratio 50・1 取引 5 操作・4 thread・1 秒、`KEY_SORT` 既定 0)。起動器 v3 (Codex author、sha256 `ceec71a4…`) は `line.bundle` を clone して OID を checkout し、F → `7e5fa528` → 新 tip の親子と F..新 tip の変更 path (`cc/silo/transaction.cc` だけ) を照合する。計装は対照 F に前回の F 用 patch (sha256 `76a4234d…`)、新 tip に L 用 patch (sha256 `edaad463…`、F 用との差は `#line 658` → `#line 661` の文脈 1 行だけ) を当てた。どちらも土台に厳密適用で当たり、`#if TRACE` の枝を除くと土台と bytes 一致 (`verbatim/author-a.md`)。

| build | workload | commit | abort | 到達可能性 | D1 a / b1 / b2 | D2b (i) | D2b (ii) | 発生条件 (自分の書きの後の読み / 複数回の書き) | 既存の判定器 | 事前登録 |
|---|---|---:|---:|---|---|---:|---:|---|---|---|
| F (修正前) | W-rmw | 191,212 | 8,527 | pass | 0 / 0 / 0 | 28,064 | 14,926 | 28,064 / 14,926 | serializable・certified、取引 191,212 | 一致 |
| F (修正前) | W-blind | 218,488 | 9,738 | pass | 0 / 0 / 0 | 1,496 | 16,625 | 16,894 / 16,625 | serializable・certified、取引 218,488 | 一致 |
| 新 tip | W-rmw | 191,604 | 8,349 | pass | 0 / 0 / 0 | 0 | 0 | 27,509 / 14,606 | serializable・certified、取引 191,604 | 一致 |
| 新 tip | W-blind | 217,984 | 9,692 | pass | 0 / 0 / 0 | 0 | 0 | 16,615 / 16,549 | serializable・certified、取引 217,984 | 一致 |

- 事前登録 (段 4 裁定 R5、前回 R5 と同じ): 対照は D1 0 かつ D2b の違反合計 ≥1、修正は D1 0・D2b (i)(ii) とも違反 0 かつ各条項の発生条件 ≥1・判定器 certified・取引数 = commit 件数。発生条件が 0 なら判定不能 (合格にしない)。
- 表の「複数回の書き」は結果 JSON の `write_write_transactions`。対照の (ii) の違反数はこの件数と一致し、W-rmw の (i) の違反数は「自分の書きの後の読み」の件数と一致した (前回と同じ構造)。
- build ごとの source・binary・trace archive の sha256 は `evidence/trace/trace-1.summary.txt` と `result.json`。trace 原本は job dir の `runs/trace-1/` (repo の外)。
- 対照 F の行は、照合器が修正前の不具合を今も検出する正例として回した (前回の F の値とは別の走行)。

## 4. 段の経過と費用

- 軽量版: 段 2 省略、段 3 相談 1 本 (所見 6 件すべて採用、`verbatim/consult-a.md`・`s4-ruling.md`)、段 5 author 1 本、段 6 レビュー 1 本 (NO-GO: must-fix 1・should 2、`review-a.md`) → 親裁定 (R1 は refuted: 判定 script は検査器が走り終われば rc=0 とし、合否は親が `b-gccN.rc` で読むと段 4 で決めた。R2 表示行の引数ずれ・R3 起動器の親 OID 照合は採用) → fix 1 本 → 焦点再レビュー 1 本 (GO、R2・R3 closed、`focus-1.md`)。
- 計算: 37765.nqsv 1,003 秒 + 37764.nqsv 195 秒 + 37772.nqsv 988 秒 = 2,186 秒 ≈ 0.61 node 時間 (2 node 時間の線の下)。3 job を同時に投げ、同じ worktree からの dispatch は直列にした (wave 木から 1 本、子木から trace → (b) GCC 12 の 2 本)。
- Codex 子: consult・author・review・fix・focus の 5 本 (すべて gpt-6-sol / medium)。
- 変異 matrix: repo の実装面の差分 0 (本 wave の commit は insight と spool fragment だけ) なので DW-S04 により免除。修正の検出力は §3 の対照 F の D2b 赤が担う。

## 5. push の依頼 (人間の手番)

land 後、本 wave の段 9 で主 checkout の submodule git dir の `refs/heads/izanagi-silo-intra-txn-fix` を `7e5fa528` → `dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43` へ非 force で fast-forward する。その後、主 checkout で:

```
cd external/ccbench
git push origin izanagi-silo-intra-txn-fix
```

- 別名の新 branch なので force は不要。GitHub には F (`izanagi-tpcc-v3-silo-mocc-fmt`、`25898d00`) が既にある (D2305 項 6)。上がるのは `7e5fa528` と `dbac49b6` の 2 commit。
- push 後に GitHub の Actions で build・format が緑であることを確かめる。手元の結果 (§0) は CI image と CI の手順による再現で、GitHub の CI の結果ではない。
- gitlink を新 tip へ進めるのは、F への前進 ([T-2854]) が main に着地し、GitHub の CI が緑になった後の別 wave ([T-2917])。

上流 (thawk105/ccbench の master) へ送る説明文の下書き (2 commit をまとめた 1 PR。D2305 の「1 修正 1 PR」。出すのは修正が izanagi の pin に入り GitHub の CI が緑になった後で、PR の作成と merge は人間):

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
and scan's read-set priority are unchanged.

The second commit shifts the four #line directives after update by three,
so that __LINE__ in the untraced build (as printed by ERR) matches the
source with the fix applied. Execution is unchanged.
```

- 前回の下書き (前 wave §6) にあった「The patch applies to master (b28f96b6) without fuzz.」は修正案 patch についての事実で、`#line` は izanagi の branch (F 以降) にだけあり master `b28f96b6` の `cc/silo/transaction.cc` には 0 本なので、2 commit 目は master に当てる対象ではない。上流 master へ出す単位は PR 作成時に人間が決める (D2305)。
- 再現の件数 (28,217 / 14,966) は U0 (pin `68106660`) の測定。本 wave の対照 F は 28,064 / 14,926 (§3、別走行・別土台)。

## 6. 主張しないこと

- GitHub Actions の CI が緑であること (push 前。手元は CI image と CI の手順による再現)。
- D297 (b) が他の compiler・検査器が選ばない文脈で一致すること (検査器の保証は「選定した macro context」の範囲)。
- 修正後の Silo で全 API の取引内の意味がそろったこと (INSERT・DELETE の要素への 2 度目の update、`scan` の読み集合優先は未修正のまま、前 wave §1)。
- 構成を変えたとき (record 数・thread 数・`KEY_SORT=1`・TPC-C) の D1・D2b。各構成 1 回。
- 性能 build への影響の大きさ (本 commit は行番号定数だけを変え、命令列は前 commit の修正で変わっている。測っていない)。

## 7. 再現資料

- `verbatim/`: 段 1 brief、段 3 相談、段 4 裁定、実装子・レビュー・fix・焦点再レビューの報告、開始 gate。
- `evidence/`: commit (`mk-line.log`)、合成 commit (`mk-synth2.log`)、format (`format-ci.log`)、予測 probe (`predict.log`)、trace (`trace/`)、D297 (`judge/`、dispatch log `cijudge-1.log`・`judge12-1.log`)、CI build (`ci/`)。dispatch log の `| ` 行などの行末空白は §8 の正規化。
- job dir: 使い捨て script (Codex author の `review/scripts/`・計装 patch `review/patches/`、親の `mk-line.sh`・`mk-synth2.sh`・`format-ci.sh`・`run-cijudge.sh`・`run-childjobs.sh`・`probe/predict.sh`)、Codex receipt (`artifacts/`)、`line.bundle` (sha256 `6e578792…`)・`synth2.bundle` (sha256 `8fde6845…`)、計算の全出力 (`runs/`)。

## 8. 写しの可逆な最小正規化

`git diff --check` に掛かる行末空白 (space / tab) だけを、写した 8 file (`evidence/ci/build.log`・`evidence/ci/configure.log`・`evidence/cijudge-1.log`・`evidence/judge12-1.log`・`evidence/predict.log`・`evidence/trace/trace-1.log`・`verbatim/fix-1.md`・`verbatim/review-a.md`) から除いた。可視文字は変えていない。file ごとの原本 sha256・byte 数・正規化後 sha256 と、除いた行 (1 始まりの行番号と除いた文字列) は `NORMALIZATION.json` にある。復元は、記録した各行の末尾へ除いた文字列を足し戻す。原本は job dir の同名 file (ただし `evidence/predict.log` の原本は job dir の `probe/predict.log`、`evidence/cijudge-1.log`・`evidence/judge12-1.log` の原本は `runs/` 直下、`evidence/trace/trace-1.log` の原本は `runs/trace-1.log`、`evidence/ci/` の原本は `runs/cijudge-1/ci/`、`verbatim/` の原本は job dir 直下)。
