---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t2854-ccbench-format-ci
seq: 1
title: [T-2854] pin 前進 (1)(2) — C2' の上に clang-format 14 の整形 commit F 25898d00 (TRACE=0 の行番号を戻す #line 3 本つき) を作り、CCBench の CI 2 本を CI image で手元通過し、D297 規則 v2 で C → F を GCC 11.4 / 12.3 とも pass と判定した (CCBench の local commit + insight、push は人間の手番、branch dev-wave-t2854-ccbench-format-ci)
---

## 本文

- 依頼: D2277 項 1 の (1)(2) (ユーザー承認「CCBench CIが通る品質を意識してください」)。(3) push は人間の手番として返す。正本: `output/insights/2026-09-29/t2854-ccbench-format-ci/README.md`。設計判断は {{D:t2854-fmt-commit-line-restore}}。
- 新事実: D2277 項 1・4 は C2' の branch `izanagi-tpcc-v3-silo-mocc` を「ユーザーが既に push していた」と記録するが、2026-09-29 16:24:10 JST の確認時点で GitHub に無い (`git ls-remote` に無く、API は branch に 404・C2' の commit に 422、生応答は insight の `verbatim/evidence/github-check.log`)。F の branch の push で祖先として上がるので本題は止まらない。
- 段 4 の新事実: 整形だけだと TRACE=0 の論理行番号がずれ、mocc の `ERR` (`__LINE__`) の定数が変わって TRACE=0 の build が変わる。整形行の直後に `#line` を 3 本足して TRACE=0 の全コード行の行番号を C2' と一致させた。
- 計算: D297 判定 35460.nqsv (Elapse 988 秒)、CI build 35469.nqsv (9 秒、計算ノードの apptainer の starter-suid に setuid bit が無く起動確認で rc=3) と 35484.nqsv (33 秒、`--userns` で rc=0)。合計 1,030 秒 ≈ 0.29 node 時間。CI image 2 つ (`:ci`・`:latest`) は login で apptainer pull (約 1 時間、Lustre 混雑)。
- 棄却: 段 3 相談の「負例対照の再実施」は削った (検査器は D2275 の判定時と同一 blob)。段 6 の should (検証器の空白除去は TRACE=1 の字句結合を見逃す) は fix せず、親の diff 全件確認を根拠とした。nit (実行 file 一覧を削る) は不採用 (全 protocol の実行 file が揃ったことの記録)。
- セッション異常 (実害なし): (1) EnterWorktree (name) が既知型「Could not read the repository git config」で失敗、手動の worktree add 1 回目は checkout 100% 後に「Could not reset index file」rc=128 (admin dir だけ消え dir・branch 残存) → 掃除して作り直し、path 形の EnterWorktree は worktree list の 10 秒上限で失敗 → 絶対 path で運用。(2) 親が段 4 の完了条件を「行番号マーカー込みの byte 一致」と書き、実装子が不成立を実測して停止 (1 巡損、{{F:t2854-criterion-perturbed-by-own-change}})。(3) 段 6 review の投げ文に相対 path を足し子が即停止 (F819 の型)。(4) F の commit script の mode 照合 awk の誤りで commit 前に rc=11 (fail-closed、一時 worktree と空 branch を撤去して再実行)。(5) fix 2 の子の login 実走は Codex sandbox の getsockopt 拒否で rc=255 (親環境では rc=0、偽赤)。
- エージェント工数: Codex 9 本 (全て gpt-6-sol / medium: 相談 1・author 2・review 2 (うち 1 本は不受理)・fix 2・焦点 1・段 7 の記録レビュー 1 (NO-GO、所見 5 件中 4 件を直し 1 件 refuted))、model call 125、wall 1,681.9 秒。子木 `.codex/worktrees/t2854-fmt-a` (branch t2854-fmt-a、所有 file は git 管理外の output/runs のみ)。
- 変異 matrix は免除 (izanagi repo の実装面の差分 0、DW-S04)。受入全走は land の受領証が持つ。

## 次の一手差分

### 更新

- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2) 、単位 11 の材料は済 → 規則 v2 を D297 検査器に実装し C → C2' は GCC 11.4 / 12.3 とも pass (D2275) → pin 前進は CCBench の CI (build・format) が緑の tip に限り承認 (D2277 項 1) → C2' の上に整形 commit F `25898d00` を作り CI 2 本を CI image で手元通過、D297 は C → F が GCC 11.4 / 12.3 とも pass → 残り = 人間の push (F の branch `izanagi-tpcc-v3-silo-mocc-fmt`)・GitHub の CI の緑と F の取得を確かめた後の pin 前進 wave (AI)・campaign で TPC-C を評価する配線**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
  点読み・点書き・insert のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`
  (§7.1 の実装単位、§8 の親決定)。実装は Codex author、正しさゲートは不変、trace は compile 時に除去する (規律 1)。
  **済:** 単位 1・2 (CCBench 側、D2225、`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`) = CCBench の local branch
  `izanagi-tpcc-v3-trace` に pin e9e477ca の子として C1 `56b5cb709628c9cac98e4e18ff676defc77a9117` (trace.hh の v3 helper・tpcc.hh の取引種別 context と
  trace build 限定の計数) と C2 `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` (silo の v3 emitter)。計算ノード 1 走で v3 の構造・witness・内容、YCSB v2 の certified、
  TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確認。この branch は 2026-09-23 08:4x JST に人間が GitHub へ push した (D2227 項 7 の「今は push しない」と食い違い、F937 の再発)。
  公開済みのまま残し、pin 候補ではない (D2235 項 1、C1 / C2 は job dir の自己完結 bundle にも保全済み)。単位 11 で C の上へ乗せ直し、
  header 差分の受理方法と結合確認を揃えた候補は別名の branch で人間の push 判断へ渡す (D16、同名への force push はしない)。単位 4 (verifier 側、D2224、entry 1828、
  `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`) = v3 を (表, key) で読み cycle に表と取引種別を載せる。単位 3 (mocc 側、D2230、`output/insights/2026-09-23/t2854-mocc-v3-emitter/README.md`) =
  CCBench の local branch `izanagi-tpcc-v3-mocc` に [T-2844] の候補 C `68106660686232781bca3be792a750d3e19d7a8a` の子として C1' `6aa7a58fccff9efa218067d1b7ce83026a75357d`
  (C1 の cherry-pick、header の blob は C1 と同一) と C3 `53f6b09757331ac7200f3f6bb5d526a676480fe3` (mocc の v3 emitter)。計算ノード 1 走で C を基点に同じ形の確認
  (v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 6 件) を満たした。この branch も今は push しない
  (bundle で保全、単位 11 の候補の材料)。存在履歴 (entry 1843、D2232、`output/insights/2026-09-23/t2854-v3-existence/README.md`) =
  設計 §3.3 を silo の版付けに裏付けた段 1 の契約で検査し、単位 4 が立てた印 `Integrity.v3_existence_unverified` を撤去。単位 1・2 の実 trace (silo) は公開 API で certified、
  単位 3 の実 trace (mocc) も存在違反 0 (mocc の認定は X/P 証拠面が pin に入った後)。mocc でも存在の契約 (初期ロードの版が (1,0)、insert は既存 key で失敗) が
  静的に成り立つことは単位 3 の insight §6。単位 5 (entry 1852、D2238、`output/insights/2026-09-23/t2854-unit5-v3-wiring/README.md`) =
  CLI の `--json`・pipeline の reject 診断・受領証 digest を `core.result_to_dict_v3` に配線 (v2 は bytes・digest 不変)、pipeline の `_run_trace` は `tpcc_` で 57:43 の 4 flag が
  文字列で一致するときだけ受理し、verifier 後に v3 を要求 (v2 は既存 `trace-witness-unsupported-workload` で reject)。§6.1 の段 1 例は既存試験への対応づけと合成 v3 の
  lost update・直列対照・executor の witness 欠落 3 形態で揃えた (「genesis の誤用」は存在検査の `read-unborn-genesis`)。実 trace (silo) は pipeline の executor で certified。
  **単位 11 (本 entry、D2244、`output/insights/2026-09-26/t2854-unit11-combined/README.md`):** 新しい local branch `izanagi-tpcc-v3-silo-mocc` =
  C `68106660` → C1' → C3 → C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` (C2 の cherry-pick、新規 commit はこれだけ、未 push、job dir の自己完結 bundle に保全)。計算ノード 1 走 (Elapse 243 秒) で C を基点に、
  TPC-C の silo・mocc とも v3 の構造・witness・内容、YCSB の silo・mocc とも v2 の certified、TRACE=0 の 21 entry の前処理と 4 binary の逆アセンブルの一致、
  変異 4 件 (共有 header の setter、共有 header の `#line`、silo の表、mocc の種別) の KILLED を確認。現行の D297 検査器は C → C2' を `include/tpcc.hh` の header 差分で拒否する (rc=1)。
  D297 の合格・TPC-C の certified は名乗らない。
  **残り:** (1) C 単独の pin 前進は [T-2858] で承認・実施済み (D2227 項 1) で、C1' / C2' / C3 は C の上の別候補として改めて承認を求める。**D297 の header 差分の受理規則は設計審査を終えた (D2249 項 2 の択 1、D2255、`output/insights/2026-09-26/t2854-d297-header-review/README.md`):** 規則 v2 = header の M 差分に限り、実 compile database の全 entry から `-MG` なしの依存列挙 (旧・新 × TRACE=0/1) で変更 header の consumer を選び、選定 configure 集合 (stock と、consumer を含む production target の protocol の genome 空間。C → C2' では stock + silo 8 + mocc 8 = 17) の各 configure で全 consumer entry の TRACE=0 完全展開と include 活性を GCC 11.4 / 12.3 の別 configure で旧新比較する (実行は計算ノード)。**規則 v2 の承認と実装の委任は D2260 項 1 で決まった (ユーザー裁定、推奨どおり)。** **実装済み (D2275、`output/insights/2026-09-27/t2854-d297-header-v2/README.md`):** header 用の 4 引数 (`--header-cc` `--third-party-cache` `--dependency-prefix` `--scratch-root`) を全部与えたときだけ header の M 差分を規則 v2 で検査し、与えなければ従来どおり拒否する。改訂後の検査器で C → C2' は計算ノード 1 job (31903.nqsv、Elapse 1,944 秒) で **GCC 11.4・12.3 とも pass** (選定 17 configure、tictoc・cicada 各 24 genome は consumer なし、consumer 21 entry、予定 = 実行 357、.cc 2 本も match、gitlink `third_party/shirakami` は旧新一致)。負例対照 (tpcc.hh の `#line 56` 削除) は TPC-C consumer の完全展開不一致で拒否。変異 12 件 KILLED。wave の計算は受入を除き約 0.80 node 時間。**問い 2 は D2277 項 1 で承認済み (ユーザー裁定、条件 = 進める先は CCBench の CI が緑の tip に限る)。** pin 波及は同 insight §7 (code 5 file・test 14 file・`patches/README.md`、C2' の変える 4 file に当たる patch 54 本は適用可否が未測定、C を束縛する較正記録は D2184 どおり保持)。si の trace v2 (`patches/instr-si-trace-v2.patch`、[T-2847]) は枝へ移さず patch のまま据え置く (D2277 項 1)。**pin 前進 (1)(2) (本 entry、{{D:t2854-fmt-commit-line-restore}}、`output/insights/2026-09-29/t2854-ccbench-format-ci/README.md`):** C2' の上に F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` (CCBench の新しい local branch `izanagi-tpcc-v3-silo-mocc-fmt`、未 push、job dir の自己完結 bundle に保全) を作った。変更は 3 file (mocc・silo の transaction.cc、trace.hh) の clang-format 14 の整形と、整形で行数が変わった `#if TRACE` 区間の直後に TRACE=0 の論理行番号を戻す `#line` 3 本だけ (整形だけだと mocc の `ERR` の `__LINE__` 定数が変わり TRACE=0 の build が変わるため)。F で CI の format step は 213 file・rc=0 (login の clang-format 14.0.0 と CI image の 14.0.6)、CI の build 手順は CI image (GCC 13.3.0) で rc=0 (計算ノード、依存は手元 cache から clean に供給、CI との差は同 insight §3)。改訂後の D297 検査器で C → F は計算ノード 1 job (35460.nqsv、Elapse 988 秒) で **GCC 11.4・12.3 とも pass** (compiler ごとに予定 = 実行 357、集約後の実比較 118 件すべて一致、consumer 21 entry)。D297 の pass は F の結果に限って言う。GitHub の CI の緑はまだ確かめていない (push 前)。それまで pin は C。C2' の D297 pass は改訂後の検査器の結果 (上記) に限って言い、単位 11 の証拠を遡って pass と呼ばない。TPC-C の certified は名乗らない。D780 項 2 は維持し、その比較を trace 完全除去の防壁と呼ばない。択 2 (C2' 限定の例外)・択 3 (header を変えない作り直し)・択 4 (何もしない) は採らない。段 2 も header を変えるので、規則 v2 は段 2 の pin 前進にも適用できる (合格するかは段 2 の実差分で確かめる)。**人間の手番:** F の branch `izanagi-tpcc-v3-silo-mocc-fmt` の push
  (主 checkout の `external/ccbench` で `git push origin izanagi-tpcc-v3-silo-mocc-fmt`、別名なので force 不要。C2' の branch `izanagi-tpcc-v3-silo-mocc` と commit は D2277 の記録と異なり 2026-09-29 16:24 の確認時点で GitHub に無いが、F の祖先として上がる)。push 後に GitHub の CI (build・format) の緑と GitHub から F を取得できることを確かめてから、gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新と patch 54 本の厳密適用を AI の wave で行う (D2277 項 1 (3)(4)、先例 D2150 / D2184)。
  v3 emitter が pin に入るまで、現 pin の tpcc binary は v2 を出し単位 5 の v3 要求で reject される。
  (2) campaign で TPC-C の候補を評価する配線 (設計 §7.1 の単位に無い): production の build は `ycsb_<protocol>.exe` だけを作り (buildcache)、workload の登録・flag の受け渡しも ycsb だけ。
  critic の reason 説明「YCSB allowlist 外」も TPC-C の v2 reject に合わせる (単位 5 の insight §6・§9)。
  単位 1・2 の実 trace は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/`、単位 3 の実 trace は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/traces-1/`、単位 11 (C2' の silo・mocc) は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/evidence/traces-1/` に zstd で保持。
  段 2 へは段 1 の存在契約をそのまま広げない (削除後の再挿入で版順が存在の遷移と逆になりうる、範囲読みの不在は §4.3 の初期キー一覧、entry 1843 の insight §8)。
  見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件は単位 5 で再評価した (pipeline は受理するが corpus の実体は無いので着手しない、単位 5 の insight §8)。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 検証走・計測・開発の検査を含め 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
  base: 51f26ae80fee842729531eecae1c91248fd1d2f13b73608254a0390dd54c7a93
