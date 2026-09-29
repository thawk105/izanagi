# 段 1 brief — [T-2872] MOCC validation の隙間の修理 (wave: dev-wave-mocc-validation-fix)

- 研究前進: 論文の比較 cell (MOCC read-heavy) の stock に出た G2 を「本体の欠陥 → 直した」と書ける状態にする。完了判定 = CCBench の branch `izanagi-mocc-validation-fix` の 1 commit が CI 2 本 (build・clang-format 14) を手元で通り、trace build の 112 走で G2 0・commit 側 class A 0、同時刻の修正前 F で同形の class A (と G2) が出る。gitlink は動かさず、push 依頼で止める。
- 依頼: `/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/md_1.txt` (逐語は insight verbatim へ写す)。確定裁定: D2277 項 1・2 (逐語は md_1 と decisions)、D2293 (F の中身と CI 手順)、D16/D18/D20 (上流は人間)、D297/D2255/D2275 (header 受理規則 v2)、規律 1・2・7。
- 既存被覆 (純増の確認): T-2779 の診断 patch `mocc-close-version-counter-gap.patch` は validation の再読 + cold 側 abort を束ねた repo 外の診断で、CCBench の commit・CI・計器での class A 0 の実測は無い。T-2872 は切り分けまで (修理なし)。本 wave の純増 = CCBench 上の修理 commit、CI 相当、修正前後の同時刻対照、patch 棚卸し。
- 前提の実測 (2026-09-29): F = `25898d00b9a6…` は submodule に実在 (origin の `izanagi-tpcc-v3-silo-mocc-fmt`)。main の gitlink = C `68106660`。F の validation は md_1 の記述どおり (版 load 1034-1036 → 比較 → lock load 1047 → `max_rset_` 再読 1061)。`ERR` の `__LINE__` は 521 と 1289 (後者は `#line 1187` の後) で、validation の行増は届かない。RWLOCK は cc/mocc/CMakeLists.txt で常に定義。Silo (cc/silo 453-478) は 1 回の load `check` で版比較・lock bit・`max_rset_` を賄う。
- 模擬と実の差: 本 brief の順序論証は静的。受理集合の主張は実測 (trace build の verifier と計器) で確かめる。

## 親の provisional 裁定 (攻撃対象)
- (P1) 修理の形は「lock 状態の読みの後に版をもう一度 acquire load し、最初の版 `check` と (epoch, tid) が違えば abort (failed_verification_ と ADD_ANALYSIS の by_tid 計上は既存の版不一致と同じ)、`max_rset_` は `check` から取る」(案 A)。理由: 既存条件への条件追加なので受理集合を厳密に縮める (md_1 の「縮める方向だけ」を字義で満たす)。(epoch, tid) が record ごとに単調増加なら、V1=V3 かつ lock 読み時点で未施錠は「lock 読みの瞬間に Silo の 1 word 検査を通る」と同値。案 B (lock を先に読み、その後 1 回だけ版を読む) も Silo 同値だが、元のコードが拒否する interleaving (lock 読みの後に他者が施錠・未公開) を受理するので字義の「縮める方向だけ」を満たさない。単調性 (ABA 無し) の根拠を現物で確かめること。
- (P2) `#line`: 修理で validation に N 行増える。`#line` directive の意味 (trace 区間を除いた source の行番号) を保つため、修理より後ろの既存 `#line` の値を +N する案と、触らない案がある。provisional = 触らない (差分を修理だけに閉じ、ERR の `__LINE__` も変えない。trace 区間の後ろの `#line 1158` 以降は元の値のままで、修理から `#line 1158` までの論理行番号が +N ずれるだけ)。patch 棚卸しで context に `#line` 行を持つ patch があるかを両案の判断材料にする。
- (P3) 実測: 計器 patch を F 用と修正後用に作り直し (repo 外、Codex author、macro off の前処理が元 source と一致することを runner が build 前に確かめる既存の作法を維持)、1 job の中で修正前 (F) と修正後 (X) の arm を交互に回す。arm = T_F・T_X (TRACE=1+probe、verifier)、N_F・N_X (TRACE=0+probe)、P_F・P_X (TRACE=0 素、commit 数の観測)。事前登録: T_X 112 走 (延長なし)、判定 = T_X の G2 0/112 かつ T_X・N_X の commit 側 class A 合計 0。対照 = T_F・N_F で class A が出ること (N_F は切り分けで 112/112 走に出た) と G2 の件数 (0 もありうる、率 4.5% で 112 走 0 件の確率は約 0.6%)。P_F/P_X の commit 数は観測として記録のみ (headline・性能主張に使わない)。
- (P4) D297: F → 修正後 tip で検査器を GCC 11.4・12.3 で走らせる。修理は TRACE=0 の翻訳単位を意図して変えるので、TRACE=0 同一性は構造上 rc=1 になる見込み。header 差分は 0 (header 分岐は不発火)。記録は「header 規則: 差分 path = cc/mocc/transaction.cc のみ、header なし」「TRACE=0 同一性: 修理の意図した差で不一致」とし、不一致が修理の hunk だけに由来することを別途示す (F と修正後の TRACE=0 前処理出力の差 = 修理の文だけ)。pin 前進 wave (C → 修理込み tip) で D297 がこの差をどう扱うかは本 wave で決めず、gitlink 前進 wave の起票に書く。
- (P5) 実装の置き場: 親が submodule に F から branch `izanagi-mocc-validation-fix` を切り、Codex author がその木の `cc/mocc/transaction.cc` だけを編集、親が 1 commit にする (trailer = Codex author・reviewer・Claude manager、D2293 の先例と同形)。commit message は上流の流儀の英語。

## 不変条件
- 受理集合は縮める方向だけ。検査を甘くする変更 (lock 検査の削除・版比較の緩和・abort の握り潰し) は取らない (規律 2)。
- cc/mocc/transaction.cc の validation 以外は変えない。trace (`#if TRACE`) 区間・writePhase・read phase は不変。cc/silo と Silo 修理 wave の branch、VHash wave の orchestrator/campaign/condition_meaning_gate.py・screening_driver.py に触らない。gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patches/ は不変。push しない。
- 性能の数字は trace-disabled build だけで取り、観測扱い (規律 1)。trace build と性能 build は別 build・別 run。

## 成果物
- CCBench: branch `izanagi-mocc-validation-fix` の 1 commit (F の子)。repo 外: 計器 patch 2 本・runner・arm 定義・投入 script・job 出力 (job dir)。
- izanagi: `output/insights/2026-09-29/mocc-validation-fix/README.md` (+ verbatim/)、spool worklog fragment (T-2872 item 更新、gitlink 前進 wave の起票)。

## 受入・実測環境
- login (pegasus02): 修理の編集、format (clang-format 14.0.0 と CI image :latest の 14.0.6)、patch 棚卸し (`git apply --check`)。
- 計算ノード: CI image `:ci` の build (先例 job dir `/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh`)、D297 判定 (同 `judge/run_judge.sh`)、trace 実測 (切り分けの runner を改作)。計算の確認線 2 node 時間: 実測は smoke の Elapse で見積もり、超えるならユーザー確認後に投入。
- 受入: `tools/dev_wave_wait.py acceptance` (izanagi 側は docs のみの差分)。

## 分割方針
- 段 2 plan 1 本 (read-only、修理の hunk・`#line`・計器と runner の改作・判定・D297 の扱いを file:line で)。
- 段 3 相談 2 本 (A = 並行性の正しさ: 案 A/B の受理集合と Silo 同値の論証、単調性、見落とした経路。B = 測定と記録: 事前登録・対照・計器の観測者効果・D297 の扱い・棚卸しの判定)。
- 段 5: 実装子 A (修理、submodule の 1 file) → 親 commit → 実装子 B (計器 2 本・runner・arm 定義、repo 外)。
- 段 6: レビュー 2 本 (修理の正しさ・CI、計器と runner)、fix、焦点再レビュー。
