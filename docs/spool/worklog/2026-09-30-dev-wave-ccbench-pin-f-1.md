---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-ccbench-pin-f
seq: 1
title: [T-2854] CCBench の pin を C 68106660 から F 25898d00 (TPC-C trace v3 と整形) へ進めた。F で厳密適用が外れる patch は 98 本中 4 本 (壊し、現行 pin の consumer なし)、生成器対照の本走は C 固定の checkout のまま影響なし (コード + test + insight、branch worktree-dev-wave-ccbench-pin-f)
---

## 本文

- 依頼: 第 5 陣 md_15 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_15.txt`)。一次資料 `output/insights/2026-09-30/ccbench-pin-f/README.md`、設計判断 {{D:ccbench-pin-f-advance}}、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-f/`。
- 前提の実測 (22:13 JST): GitHub (HTTPS) の fresh clone で F を取得、C は祖先、C..F は 4 commit・4 file (CMake に触れない)、F の check-runs は build・format-check とも success。
- patches/ の厳密適用 98 本: C・F とも当たる 54、F で新たに外れる 4 (`broken-mocc-early-unlock`・`broken-mocc-hot-update-unlock`・`broken-silo-corrupt-write-payload`・`broken-silo-published-version-mismatch`)、単独では両方外れる 40 (重ね当てで C・F 同結果)。4 本は作り直さず [T-2854] の残りへ。
- [T-2917]・[T-2919]・[T-2945] の前提「F への pin 前進 ([T-2854]) の main 着地」は本 entry の land で満たされる。3 item の本文は同時に走る md_16 (束ねた tip の作成) が更新する担当なので、fold の base 衝突を避けるため本 fragment では書き換えない。
- 生成器対照の本走 (md_11、[T-2867]、D2305 項 1): submit checkout 16 本は HEAD `1da88472b`・submodule C・lock のまま (着手時と 23:34 JST の 2 回読んだ)。main の gitlink 変更は届かない。Silo の方策 driver は `pin.CURRENT_PIN` を読むので、新しい main から submit checkout を作り直すと F になる — land 後に本走の wave へ知らせる。
- 段 2・3 は省略 (前例 [T-2858] と同型)。Codex 子 = author 1 (test を login で走らせられず全件「実装済み・未実走」と申告、歴史 golden の改名ミス 1 件を持ち込んだ)、fix 1、review 2 (A: should-fix 1 = 8b 再開 runbook の P1 → 親が docs を修正、B: 所見なし GO)。
- 焦点走: set1 (163 file、request 39785、Elapse 854 s) 10 failed / 15,705 passed / 56 skipped → fix1 → set2 (13 file、request 39992、43 s) 1,716 passed / 2 skipped。set1 の 1 job は目安 5 分を超えた (同じ worktree の dispatch は直列が契約で、割っても合計は減らない)。
- 変異 (実装面の最終 commit `c2e25f9ae`、runner 8 file): probe で観測 node を集めて final を再登録し、final は KILLED 3 (mut1 13・mut2 63・mut3 46 node)・SURVIVED 1 (等価)・4/4 一致、rc=0。mut3 の 46 は mut2 に含まれる drift 層で、pin 値の単一理由の証拠は mut2 だけが殺す 17 node (前例 [T-2858] と同じ構造)。
- 三軸語走査 (`s8b_holdout_freeze search`) は rc=1 だが、hit は 2026-09-16 の既存の較正成果物 3 file だけで、前例 (9/23) と同じ。本 wave の file の hit は 0。
- 自己点検 (調整役の通達、10/01 00:3x): 同じ原因の失敗が 2 系統あった — {{F:isolated-session-compound-command-rejected}} と F810 の再発。
- 新規 worktree の submodule 初期化は 2 本とも 1 回目 `runtime-io-failure (update-no-fetch)`、同じ引数の 2 回目で rc=0 (DW-O08 の既述どおり)。

## 次の一手差分

### 更新

- [T-2854] **P1・pin 前進は完了 (本 entry、{{D:ccbench-pin-f-advance}}) → 残り = campaign で TPC-C を評価する配線、F で外れる壊し patch 4 本の作り直し**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
  点読み・点書き・insert のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`
  (§7.1 の実装単位、§8 の親決定)。実装は Codex author、正しさゲートは不変、trace は compile 時に除去する (規律 1)。
  **済:** 単位 1〜5・11 と D297 規則 v2 (D2225・D2224・D2230・D2232・D2238・D2244・D2255・D2260・D2275)、整形 commit F と C → F の D297 pass (D2293)、F の push と GitHub の CI 緑 (D2305 の収集)。経緯と各単位の一次資料は archive の entry 1959 の本項。
  **pin 前進 (本 entry):** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同一 commit で F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` へ進めた。F は silo・mocc の v3 emitter (単位 11 の C2' と同じ内容に整形を足したもの) を含む。v3 の実 trace は単位 11 で C2' の上で確かめたもので、F の上での tpcc の実走はしていない。campaign での評価は未配線。
  C に独立束縛の系列 (MOCC の関数方策の campaign pin、VHash の Cicada 系列、生成器対照の本走) は C のまま。一次資料 `output/insights/2026-09-30/ccbench-pin-f/README.md`。
  **残り:** (1) campaign で TPC-C の候補を評価する配線 (設計 §7.1 の単位に無い): production の build は `ycsb_<protocol>.exe` だけを作り (buildcache)、workload の登録・flag の受け渡しも ycsb だけ。
  critic の reason 説明「YCSB allowlist 外」も TPC-C の v2 reject に合わせる (単位 5 の insight §6・§9)。
  (2) F で `git apply` が外れる壊し patch 4 本 (`broken-mocc-early-unlock`・`broken-mocc-hot-update-unlock`・`broken-silo-corrupt-write-payload`・`broken-silo-published-version-mismatch`) の作り直し。
  現行 pin に当てる consumer は無い (MOCC の 2 本は e9e477ca 束縛、Silo の 2 本は condition gate の登録と一回限りの変異走だけ)。作り直すなら F (または修理を束ねた tip) の上で壊れ方が発火することを実走で示すまでを 1 単位とする。
  単位 1・2 の実 trace は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/`、単位 3 の実 trace は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/traces-1/`、単位 11 (C2' の silo・mocc) は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/evidence/traces-1/` に zstd で保持。
  段 2 へは段 1 の存在契約をそのまま広げない (削除後の再挿入で版順が存在の遷移と逆になりうる、範囲読みの不在は §4.3 の初期キー一覧、entry 1843 の insight §8)。
  見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件は単位 5 で再評価した (pipeline は受理するが corpus の実体は無いので着手しない、単位 5 の insight §8)。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 1 タスクの job 合計が 2 node 時間を超える投入は、land 調整役に相談して GO を得てから投入する (common-5 §4、ユーザーの委任)。
  一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
  base: 392c039298d20e766c33935278ea0fa055d302c4058809953a10c0a3ba2a3f1f
