# mocc の X/P 計装を pin 候補へ載せる前段 — 計装 patch はそのまま commit すると D297 が拒否し、include 1 行と型 2 箇所の修正で D297 を通る (実装は Codex 利用枠切れで次 wave へ)

authority: none
default_effect: no-state-change

- 日付: 2026-09-21
- wave: `dev-wave-mocc-xp-pin-candidate` (branch `worktree-dev-wave-mocc-xp-pin-candidate`)。着手時 local main `d99c556dfa23e446987ef3ccbb5c018986fe10b5`、記録前に `47368e7d5`、記録 commit 直前に `f646e7e85` へ ff-only
- 起点: ユーザーの `/dev-wave` 引数 (逐語 = `verbatim/verbatim-request.md`)。既裁定 = D2114 項 3、D2150 項 1、D1686、D1603、D579、D297、D16、D95 (逐語は job dir `verbatim/`)
- job dir (probe script・生 log・codex receipt): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/`
- **本資料の内容は Codex の敵対検査を受けていない。** 段 3 の相談 2 本は起動直後に Codex の利用枠切れで失敗し (出力 0 byte、§6)、段 6 のレビューも無い。
  代わりに独立 context の Claude (opus、読み取りのみ) に本文と fragment の事実照合を 1 本させ、所見を反映した (`verbatim/factcheck-dispositions.md`)。これは dev-wave 契約上の Codex レビューの代替ではない。
  段 2 plan は受理したが、その結論は次 wave の段 3 で点検される前提の起草である。

## 0. 結論

1. **合流関係:** T-2294 の X/P 計装 patch (`patches/instr-mocc-lock-coverage.patch`、sha256 `e9e65b78…`) は hook branch `izanagi-t1943-mocc-g2-readfrom-witness` の先端 = 現行 pin `e9e477ca` に厳密適用で当たる。負例 patch 4 本は e9e477ca 単独では rc=1、e9e477ca + 計装の上では rc=0 (`verbatim/p1-patch-merge.log`)。
2. **patch をそのまま commit した候補は D297 検査で拒否される。** scratch の probe commit `5e0fda49` (e9e477ca + 計装 patch、blob `1ec11e5c…`) に対し、`tools/check_trace0_preprocess_identity.py` は rc=1「include 行文字列（順序込み）が不一致」(`verbatim/d297-asis-gcc11.stderr.txt`)。原因は `#if TRACE` 内に追加した `#include <set>` で、検査器 (`_mocc_trace_include_addition_index`) が追加として受理する include は mocc の trace.hh 1 行だけである。
3. **`#include <set>` の 1 行を除き、`std::multiset<const void*>` 2 箇所を `std::unordered_multiset<const void*>` に替えた版は D297 を通る。** `<unordered_set>` は同じ `#if TRACE` 内で include される `include/trace.hh` が供給する。`#line 17` を含む他の行は T-2294 と同じ bytes (`verbatim/p7-candidate-ids.log` の diff = 3 行)。GCC 11.4 / 12.3 とも `result: pass` (§2)。これは TRACE=0 の前処理の実測で、TRACE=1 の build と実行は測っていない。採否は次 wave の段 3・4 で決める。
4. **pin 候補の commit C は作っていない。** 実装面は Codex `role=author` だけが書ける (D95)。Codex の利用枠は表示上「Sep 26th, 2026 7:35 PM」(時間帯の表記なし) まで復帰しない。D95 決定 (3) に従い親は代筆せず実装を止め、段 4 で「実装しない」と裁定した (`verbatim/s4-ruling.md`)。既定は Codex 復帰後の次 wave で進めることで、復帰前に進める場合だけ D105 の waiver (ユーザー裁定) が要る。本 wave は waiver を求めていない。
5. **I 面 ([T-2295]) は不足のまま。** 現行 pin の `cc/` と `include/` に、verifier が I emitter と認識する文字列は 0 件 (§5)。certification gate は I を要求しないが、mocc の I を閉じるには write-intent shadow の新設計が要る。

## 1. 依頼と、この wave がしたこと・しなかったこと

| 依頼の項目 | 状態 |
|---|---|
| 冒頭で patch と hook branch の合流関係を確かめる | **済** (§0 の 1・2、§2) |
| X/P 計装を e9e477ca の hook 系統 submodule branch へ統合する | **未** — D297 (TRACE=0) を通す修正案を実測で特定した (§0 の 3、§3)。TRACE=1 build は未測定、採否は次 wave の段 3・4、commit は Codex 枠の復帰後 |
| positive / negative control | **静的な対照のみ** (proof-surface 判定・負例 patch の適用可否、§2)。TRACE=1 build と compute 実走は未 |
| D1603 材料 (1) 候補 commit | **未作成**。目標の bytes は blob `e393efbf…` (§3) |
| D1603 材料 (2) D297 検査 | 候補の bytes に対して GCC 2 版 pass、clang 14 は比較未完了 (§2)。C を作った時点で同じ checker を走らせる |
| D1603 材料 (3) 波及範囲 | **起草のみ** (段 2 plan §6、未検査、§4) |
| I 面を同時に閉じられるか | 閉じられない (§5)。不足として明記 |
| push・gitlink / `CCBENCH_FULL_SHA` 更新・再承認の提示・探索開始 | 行っていない (依頼どおり scope 外) |

## 2. 実測 (login `pegasus02`、2026-09-21 14:08〜14:56 JST = probe log の mtime)

scratch の一時 commit は job dir の scratch (`probe/scratch-*`) にだけ作り、repo にも submodule branch にも入れていない。wave 木の submodule の store にも 3 本とも無い (`git cat-file -e` rc=128、`verbatim/p10-probe-commits-absent.log`)。

| probe | 手段 | 中身 | 結果 | 逐語 |
|---|---|---|---|---|
| p1 | 単独適用は wave 木の submodule の作業木に `git apply --check` (読み取りのみ)。積み重ねは `git archive` から作った scratch (`probe/scratch-e9`) | 各 mocc patch の単独適用と、計装適用後の負例 4 本 | 計装 rc=0、負例 4 本は単独 rc=1 / 計装後 rc=0。template は単独 rc=0、計装 template 版は単独 rc=1 | `verbatim/p1-patch-merge.log` |
| p2 | `git clone --shared` の scratch (`probe/scratch-clone`) に計装を当てて一時 commit | e9e477ca → `5e0fda49` (計装そのまま) の D297、g++ 11.4 | **rc=1** include 行文字列の不一致 | `verbatim/p2-d297-asis.log`、`verbatim/d297-asis-gcc11.stderr.txt` |
| p3 | 同型の scratch (`probe/scratch-clone-min`) | `#include <set>` と `#line 17` を除き、`std::multiset` 2 箇所を `std::unordered_multiset` に替えた版 (`211bc924`) | D297 は GCC 2 版 pass。負例は early-unlock / hot-update-unlock が **rc=1** (両 patch の先頭 hunk の文脈に `#line 17`) | `verbatim/p3-minimal-variant.log` |
| p4 | 同型の scratch (`probe/scratch-clone-min2`) | `#include <set>` だけ除き同じ型置換、`#line 17` は残す版 (`eb8dc6fe`) | D297 は GCC 2 版 pass、負例 4 本すべて rc=0 | `verbatim/p4-keep-line17.log`、report JSON 2 本 |
| p5 | verifier の production 関数 (`capture_` / `assess_compiled_protocol_source_snapshot`)。e9e477ca は wave 木の submodule checkout、他は p2 / p4 の scratch | proof surface の判定 | e9e477ca: X/P/I とも evidence-absent、gate 偽。計装そのまま / p4 版: X/P evidence-present、I absent、gate 真 | `verbatim/p5-proof-surface.log` |
| p6 | p4 の scratch に検査器を直接 (14:56 に argv・rc を記録する形で再実行) | p4 版の D297、`/usr/bin/clang++` → `/usr/lib/llvm-14/bin/clang` (Ubuntu clang 14.0.0) | **rc=1**、stdout 0 byte、空入力の環境 prefix と不一致 (比較前に fail-closed、t2756 §3.3 と同型の既知限界) | `verbatim/p6-d297-clang.log`、`verbatim/d297-candidate-clang14.stderr.txt` (初回の stderr) |
| p7 | 読み取りのみ | 3 版の識別子と、p4 版と計装そのまま版の差 | §3 の表 | `verbatim/p7-candidate-ids.log` |
| p8 | 読み取りのみ | silo の write-intent branch と現行 pin の祖先関係 | §5 | `verbatim/p8-t152-ancestry.log` |
| p9 | 読み取りのみ | 現行 pin で I emitter の文字列を数える | §5 | `verbatim/p9-i-emitter-grep.log` |

D297 report の中身 (p4 版、`verbatim/d297-candidate-gcc{11,12}.report.json`、sha256 `2ed2a0a5…` / `ea3a3b47…`):

- schema `izanagi-trace0-preprocess-identity/v2`、`result: pass`、`old_is_ancestor_of_new: true`、差分は `cc/mocc/transaction.cc` の 1 path (blob `1f4e9453…` → `e393efbf…`、mode 不変)。
- include 行は 11 行 (`include_line_count`) で、16 context すべてで正規化前処理出力と include 活性が一致。include 比較の basis は 16 件とも `exact_identity` (trace.hh の追加特例の経路を通っていない)。
- 正規化出力の digest は 2 種 (`148e44ea…` 8 件 / `4db297ef…` 8 件) で、t2756 §3.1 の前回 pin 比較と同じ値。compiler は `x86_64-linux-gnu-g++-11 (… 11.4.0)` / `x86_64-linux-gnu-g++-12 (… 12.3.0)`。

**この実測が言えないこと:** p4 は TRACE=0 の前処理の同一性であり、TRACE=1 の build (`-O3 -Wall -Wextra -Werror -std=c++20`) の成功・X/P の実発火・`.text` の一致は測っていない。負例 4 本は `git apply --check` が通ることまでで、C 上で X/P が発火することは実走していない。p4 の script 冒頭コメント (「`#line 17` を除き」) は処理本文 (`#line 17` を残す) と食い違っており、結果は本文に従って読む。

## 3. 候補の中身 (次 wave の author が作る bytes の目標)

| 版 | probe commit | `cc/mocc/transaction.cc` blob | sha256 |
|---|---|---|---|
| e9e477ca (現行 pin) | — | `1f4e9453c39a42451e652b3a28d791b90844f184` | — |
| 計装そのまま (D297 拒否) | `5e0fda494f6b6717af68b8e1f71dbaea645cc404` | `1ec11e5c12aa7e673a794e744ee9ea0563d9ba66` | `bd0add59890a60150b9c650155943ddd0c1e91eeccc0121a6b674c834b3ed04c` |
| **p4 版 (D297 pass、負例 4 本適用可)** | `eb8dc6fef9df3bb65f9fc71f88168e184424320a` | `e393efbfd5fad7bbe05117b43669ccc0f44abb6a` | `712e31b5cbf2a3a63df442d50203c5c0787c98c83672d49a20210719bf32ebe4` |

p4 版と計装そのまま版の差は 3 行だけ (`#include <set>` の削除、`izanagi_pre_sort_rcdptrs` / `izanagi_post_sort_rcdptrs` の宣言の型)。p4 版は親が repo 外の scratch 上で機械置換して作った**測定対象**であり、Codex author の成果物ではない。

内容同一性で D297 の結果を引き継げる条件: C が e9e477ca の単一の子で、差分が `cc/mocc/transaction.cc` の 1 path、その blob が `e393efbf…` なら、C の tree は `eb8dc6fe` の tree と同一になる。検査器は old / new 各 commit の対象 file に加え、各 commit の `cmake/Options.cmake` と protocol の CMakeLists (head define)、`--repo` の作業木と commit tree (不在 macro の走査)、`--cxx` の compiler を読む。tree が同一で、検査器の版と compiler が同じなら入力は同一になる。C を作ったら同じ checker を走らせて確かめる。

意味論 (段 2 plan §1 の起草、未検査): `unordered_multiset` の等値は pointer 値ごとの多重度の一致で、D1686 の P の主張 (size と `rcdptr_` multiset の保存) と同じ述語になる。一方で計算・確保の挙動は `multiset` と違うので、TRACE=1 の観測負荷は T-2294 と同一ではない。T-2294 の compute 実測 (job 979791) は bytes が違うため C へ引き継がず、C 上で正例・負例を再走する。

## 4. D1603 材料 3 点の状態

| 材料 | 状態 | 次に要ること |
|---|---|---|
| (1) 候補 commit | 未作成 | Codex author が候補の差分を作り、親が wave 木 submodule の一時 worktree で e9e477ca の単一の子として `commit -F` (witlight 先例、`output/insights/2026-09-19/mocc-witlight-arm-run/README.md` §2・§7)。bundle を保全し、主 checkout の submodule git dir へ fetch する |
| (2) D297 検査 | 候補 bytes に対して GCC 11.4 / 12.3 pass、clang 14 比較未完了 | C に対して GCC 2 版 + clang を実走し、計装そのまま版を負例対照として並べる |
| (3) 波及範囲 | 段 2 plan §6 に起草 (`verbatim/s2-plan.md`)。`e9e477c` を含む tracked file 43 件 (docs の 3 台帳・archive・spool と `output/insights` を除く) を「pin を C へ進めた時」の扱いで分類: 追随 15・据置 27・衝突 1 (`orchestrator/campaign/axis_mocc_temperature.py`)。親の検算は件数と path 集合の一致まで (`verbatim/count-ripple.log`)。分類の正しさは未検査 | 次 wave の段 3 で点検する。文字列外の依存 (計装・template の patch の preimage、mocc trace pilot と D2153 の receipt v2、build admission policy の epoch 移動 = t2304 §0 の 4、fixture・事前登録・較正・凍結) も plan §6 後半にある |

## 5. I 面 ([T-2295]) — 不足

- 現行 pin の `cc/` と `include/` に、verifier が I の emitter と認識する文字列 (`emit_write_intent_violation`、literal `"I "`。`orchestrator/verifier/model.py` の `_WRITE_INTENT_EMITTER_PATTERNS` の核) を含む file は 0 件 (`verbatim/p9-i-emitter-grep.log`)。文字列検索なので、別表記の不在までは証明しない。verifier が proof surface を評価する protocol は silo / si / mocc の 3 つ。
- certification gate (`ProofSurfaceAssessment.certification_gate_satisfied`) は X と P だけを要求する。したがって X/P を載せた候補では I が absent でも gate は真になる (p5)。
- mocc の I を閉じるには、write_set から逆生成しない独立の write-intent shadow を write intent の登録点に置く設計 (storage / key / op / record pointer / 多重度の定義、hot の早期 lock と RLL 再 lock との順序、abort・retry 後の clear、対照 patch、TRACE=0 の完全除去) が要る (段 2 plan §7 の起草)。Silo の write-intent 実装 (`izanagi-trace-t152`、`c9c1a9c2`) は現行 pin の祖先ではなく (`merge-base --is-ancestor` rc=1、merge-base `d706650c`、`verbatim/p8-t152-ancestry.log`)、mocc へそのまま使えない。
- X/P の候補化と同時には閉じられない。本 wave では実装も設計もしていない。

## 6. 段の経過と Codex の利用枠

- 段 1: 開始 gate は「OK: wave startup checks passed」(log mtime 14:08:15、rc=0 は親 session の出力)、brief (`verbatim/s1-brief.md`、条件表 08 / 09 / 10 / 13 の再評価込み)。
- 段 2 plan: Codex read-only、14:22:03〜14:32:10、rc=0、41,946 byte、受理検査 rc=0 (`verbatim/s2-plan.md`、prompt = `verbatim/prompt-s2-plan.md`)。
- 段 3 相談 2 本: lane sol は 14:32:57 投入・14:33:03 終了、lane luna は 14:32:59 投入・14:33:04 終了 (launcher log 上 6 秒 / 5 秒)。launcher rc=2 (receipt `outcome=launcher_error`、codex の exit code 1)。
  `turn.started` の後に `turn.failed`「You’ve hit your usage limit. … try again at Sep 26th, 2026 7:35 PM.」で失敗し、出力 0 byte (`verbatim/s3-consult-{A,B}.attempt-0001.events.jsonl`、prompt = `verbatim/prompt-s3-consult-{A,B}.md`)。
- 段 4 裁定 (`verbatim/s4-ruling.md`): 実装しない (`4→7→8→9`)、変異 matrix 免除 (実装面の差分ゼロ)、受入全走は land 対象 tip で 1 回。brief の provisional 裁定 (P1)〜(P6) と、plan が brief を超えて足した要素 (hot-update-unlock の正負例 2 走、`.text` bytes 比較、候補固有 7 key、land 前 fetch) は確定せず次 wave の段 3 へ持ち越す。
  裁定文の段 3 の投入時刻 (「14:32:57 投入、両方 6 秒」) と D297 検査器の入力の記述 (「old/new の blob・差分 path 集合・祖先関係」) は不正確で、正しくは本節と §3 のとおり (裁定文は逐語として残す)。
- brief の訂正 (plan の指摘を採用): 「現行 pin の mocc 結果は常に indeterminate」は広すぎた。pinned producer の source (patch なし) は X/P emitter を持たず gate が偽だが、e9e477ca + T-2294 patch の診断実走は certified の正例を持つ (materializer 登録簿で NON_ADMISSIBLE の診断 build)。

## 7. 次の一手 (worklog の新規 T)

Codex の利用枠が復帰した後 (表示「Sep 26th, 2026 7:35 PM」、時間帯の表記なし) に fresh な wave で:
1. `verbatim/s2-plan.md` を段 2 成果物として流用し、段 3 の相談 2 本 (正しさ・観測者効果 / 過剰・削除と pin 材料・可搬性。prompt の下書き = `verbatim/prompt-s3-consult-{A,B}.md`) を当てて段 4 で確定する。
2. 段 5: Codex author が候補の差分を作る → 親が C を commit (branch 名の案 `izanagi-mocc-xp-instrumentation`、e9e477ca の単一の子、touch set = `cc/mocc/transaction.cc` 1 file) → 正例・負例の実走経路 (plan は既存 driver `orchestrator/campaign/s3_mocc_lock_coverage.py` に候補 mode を足す案) と test。
3. C に対して D297 (GCC 2 版 + clang) と compute 1 走、波及表の点検。
4. 他の wave の worktree の submodule が C を持つ保証は無い。submodule は `.git/worktrees/<wave>/modules/external/ccbench` に初期化され、origin は主 checkout の module store である。主 module store へ fetch する前に初期化された木には C が無く、fetch 後に初期化された木には `origin/<branch>` として入りうる (witlight の `5b02546f` が実例)。repo の test は C の存在を前提にしない形を段 3 で決める。

## 8. 主張しないこと

- C が作れること、C で X/P が発火すること、TRACE=1 build が `-Werror` で通ること、`.text` が一致すること (いずれも未測定)。
- D297 の合格が規律 1 の十分条件であること (必要条件の一つ、D780)。16 context が mocc の実効構成を 16 種覆うこと (t2756 §3.2)。clang での同一性。
- 波及表の分類の正しさ (起草のみ)。pin を C へ進めてよいこと (再承認は D2114 項 3 の見送り台帳経路で別途)。

## 9. 再現資料

- probe script (repo に入れない、job dir `probe/`): `p1-patch-merge.sh` `4c22e948…`、`p2-d297-asis.sh` `5020f9b4…`、`p3-minimal-variant.sh` `51d68e40…`、`p4-keep-line17.sh` `80b47165…`、`p5-proof-surface.py` `28d5d508…`、`p6-d297-clang.sh` `56a86d81…`、`p7-candidate-ids.sh` `e0a36e2b…`、`p8-t152-ancestry.sh` `abf8973b…`、`p9-i-emitter-grep.sh` `412e399c…`、`p10-probe-commits-absent.sh` `0a19f7ac…`。scratch (`probe/scratch-e9`、`probe/scratch-clone*`) も同 dir。
- 既裁定の逐語は job dir `verbatim/` (`extract_verbatim.py` で決定台帳から見出し単位に切り出し、D16 / 95 / 297 / 579 / 780 / 1603 / 1686 / 1687 / 2114 / 2150 項 1 / 2153)。
- 検算: 波及表の件数と path 集合 = job dir `count_ripple.py` (出力 = `verbatim/count-ripple.log`)。
- 可逆正規化 (DW-S07、可視文字不変): `verbatim/p1-patch-merge.log` は原文 (job dir `probe/p1-patch-merge.log`、1,500 byte、sha256 `92f78e43…`) の行 4 / 7 / 10 / 13 / 16 / 19 / 22 の行末空白 1 個ずつを除いた (1,493 byte、sha256 `6828c9c2…`)。復元は同じ 7 行の末尾に空白 1 個を戻す。
- 設計判断: decisions fragment `docs/spool/decisions/2026-09-21-dev-wave-mocc-xp-pin-candidate-2.md` (fold で採番)。
