# [T-2858] mocc の X/P 計装 commit C を新しい ccbench pin として再承認するかの提示 — 材料 3 点・更新 wave の波及見積り・TPC-C 候補との切り分け

authority: none
default_effect: no-state-change

- 日付: 2026-09-23
- wave: `dev-wave-t2858-mocc-xp-pin-revalidation` (branch `worktree-dev-wave-t2858-mocc-xp-pin-revalidation`)。着手時 local main `3886a1fd36657537af2b6c6ed389257363d92bef`
- 経路: D2114 項 3 (見送り台帳の ccbench pin 更新項 [T-167] の再承認として提示)、D2219 項 8 (人間の push の後に AI が提示 wave を起こす)、D1603 (材料 3 点が揃えば前進してよい)
- 本書は提示であり、何も承認・変更しない。gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` は e9e477ca のまま。push は人間 (D16)
- job dir: `/home/SFC/tanab/.claude/jobs/4811f999/` (brief `s1-brief.md`、取得確認の script と log `ghfetch.sh` / `ghfetch.log`)

## 0. 決めてほしいこと (1 問)

**C = `68106660686232781bca3be792a750d3e19d7a8a` を新しい ccbench pin として承認するか。承認するなら、pin を今 C へ進めるか、TPC-C の候補と合わせて 1 回で進めるか。**

| 択 | 中身 | 得るもの | 払うもの |
|---|---|---|---|
| **(a) 推奨: C を単独で承認し、更新 wave を今起こす** | C を新 pin として承認する。更新 wave (AI、Codex author + 変異事前登録) は D2150 項 1 と同じ ①④⑦ に限る (§3)。TPC-C の commit は、あとで C の上へ載せ替えた別の候補として改めて承認を求める | MOCC の口 S2 ([T-2849]、D2220 項 6) と TPC-C の mocc 認定 ([T-2854] 単位 3) の前提がそろう。TPC-C 側の未決着 (§4) に C が巻き込まれない | pin 前進が TPC-C と合わせて計 2 回になる (TPC-C 設計 §8 の親決定 3 の「1 回」を変える)。更新 wave 1 本分の工数 (§3.3) |
| (b) C を承認し、pin 前進は TPC-C の候補と合わせて 1 回にする | C の内容を承認する。gitlink 等の更新は、TPC-C の commit を C の上へ積んだ候補が承認されるまで待つ | pin 前進の手続きが 1 回で済む (TPC-C 設計どおり) | S2 と mocc の認定の前提が、TPC-C 候補の完成と承認まで止まる。その候補は D297 検査器が header 差分で落ちる問題を抱え、受理方法が決まっていない (§4) |
| (c) 見送る | 承認しない。[T-167] は見送り台帳に残る | — | S2 は無効のまま。第 2 プロトコルの疎通 ([T-2849] の完了条件) が開かない |

**推奨 (a) の理由:** S2 と、TPC-C の mocc 認定のうち今回先に解消する X/P の前提は、C の X/P 計装で足り、TPC-C の候補を要しない (TPC-C の mocc 認定そのものは、別に mocc の v3 emitter などを要する)。現在の C1 / C2 は C と変更する file が重ならない (§4) ので、C の上へ載せ替えても path 上の衝突は無い。ただし内容の結合確認と、TPC-C の mocc 側 (単位 3 の v3 emitter、未実装) の証拠は後続候補の仕事で、2 回目の承認は C からの差分に加えて結合後の証拠をそろえて別途求める。「1 回」は TPC-C 設計の親決定であってユーザー裁定ではない (D2219 項 2 が採ったのは設計 §8 の 4 = 段 1 → 段 2 の分割)。同設計が 2 回に分ける例外として書いたのは「段 1 を急いで使う必要が出た場合」であり、今回の理由 (第 2 プロトコルの疎通 [T-2849] が C 待ちで止まっていること) はその例外に当たるものではなく、同設計の時点で勘定に入っていなかった新しい理由として 1 回の方針を変えることを求めるものである。

**(a) でも (b) でも、承認の対象は C の OID ただ 1 つである。** C の上に積む TPC-C の commit (C1 `56b5cb70` / C2 `a6f2c741` を載せ替えた版) は含まない。TPC-C の候補は、完成した時点で別途、材料をそろえて承認を求める。

## 1. 承認の対象と、含まないもの

| 項目 | 値 |
|---|---|
| 候補 OID | `68106660686232781bca3be792a750d3e19d7a8a` (ccbench branch `izanagi-mocc-xp-instrumentation`) |
| 親 | 現 pin `e9e477ca1b55348ab4530de0b1cf663ce4555290` ちょうど 1 本 |
| 差分 | `cc/mocc/transaction.cc` の +64 行だけ (mode 不変、CMake に触れない)。mocc の X (lock 被覆) と P (write set の並べ替え) の計装を `#if TRACE` 枝に置く |
| GitHub 上の実在 | `git ls-remote https://github.com/thawk105/ccbench.git` で `refs/heads/izanagi-mocc-xp-instrumentation` = C (2026-09-23 07:44:42 JST) |
| GitHub だけを取得元にした取得 | 空の repo へ `git fetch --depth 1 <GitHub URL> <C>` が rc=0。tree `6dc0883c5bcc854eb6425101508b81a36bd7bf45`、親 e9e477ca、`cc/mocc/transaction.cc` の blob `e393efbfd5fad7bbe05117b43669ccc0f44abb6a` はいずれも材料 §2 と一致 (07:50:09 JST、job dir `ghfetch.log`) |

**承認に含まないもの (承認しても解決しない):**
- TPC-C の commit (§4)。
- clang での TRACE=0 同一性 — clang 14 の D297 比較は未完了 (§2 の材料 2)。
- I 面 ([T-2295]) — I (insert) の emitter は全 protocol で不足のまま。C 上の stock mocc が certified になることは、X / P の emitter があることを含意するが、I の被覆は含意しない。
- mocc の hot 経路 (hot-update-unlock) の C 上での再立証、同じ大きさのポインタ置換の動的立証。
- mocc を変異探索の面へ入れること (D579 の独立実証は別途)、温度述語 hole の採用 (D2134 項 9)、TicToc の候補化。
- 旧 pin の測定・判定の無効化 (規律 7。旧記録は旧 pin の取得事実として保つ)。

## 2. D1603 の材料 3 点

正本は `output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md` (以下「材料」)。

1. **候補 commit (材料 §2):** 上の表のとおり。旧計装 (T-2294) から `#include <set>` を足さず、P の snapshot の容器を `include/trace.hh` が供給する `std::unordered_multiset<const void*>` にした形 (D2207)。自己完結 bundle と主 checkout の submodule 格納域への取り込みは T-2844 で済み。
2. **D297 検査 (材料 §3):** TRACE=0 の正規化前処理出力と include 活性の同一性は、GCC 11.4 / GCC 12.3 とも 16 context で pass。**clang 14 は比較前に既知の限界 (環境 prefix の不一致) で止まり、比較未完了**。旧計装をそのまま commit した負例は同じ検査器が include 規則で拒否した。前回 (D2150 項 1 (iii)) は同じ状況で「GCC 2 版の pass で足りる、clang 未確認は限界として記録」と裁定した。加えて C 上の正例・負例 1 走 (材料 §4) は all_pass: stock 2 走が certified、X / P の単一理由の負例 3 本が所定の違反だけで indeterminate、lockskip の 4 thread は cycle を伴う non-serializable。
3. **波及表 (材料 §5):** 当時 45 件 = 追随 15・据置 29・衝突 1 (`orchestrator/campaign/axis_mocc_temperature.py`)。現 main での再集計は §3.1。

## 3. 承認後の更新 wave の波及見積り (T-2304 の先例から)

### 3.1 現 main での再集計

- **`e9e477c` を含む tracked file** (材料 §5 と同じく docs の 3 台帳・`docs/archive/`・`docs/spool/`・`output/insights/` を除く): 当時 45 件 (main `36fb14a3d`) → 現在 **54 件** (main `3886a1fd3`)。増えた 9 件・消えた 0 件。増えた 9 件は、いずれも過去の実測記録か固定した図の出所で、値を保つ **据置** に当たる:
  - T-2844 の追加物 2 件 (`orchestrator/tests/test_mocc_xp_pin_candidate.py`、`output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`) — 材料 §5 の「本 wave の追加物」表どおり据置。同表の候補 patch `patches/instr-mocc-lock-coverage-pin-candidate.patch` は文字列を含まないので 54 件の外 (扱いは同表どおり据置)。
  - 論文ストーリー 2026-09-22 版と図 15 (witlight 4 arm) の 5 件 (`docs/paper-story/2026-09-22.md`、`docs/paper-story/figures/README.md`、`docs/paper-story/figures/fig15_mocc_witlight_four_arm.provenance.json`、`tools/plotting/plot_mocc_witlight_four_arm.py`、`orchestrator/tests/test_plot_mocc_witlight_four_arm.py`) — e9e477ca + patch で測った正式結果の条件の記録。
  - silo-function-policy 軸の実測 2 件 (`output/env/pegasus/calibration/silo_function_policy_coverage.json`、`silo_function_policy_smoke.json`) — 取得時の `ccbench_commit`。
- **pin 定数 (`CURRENT_PIN` / `CCBENCH_FULL_SHA` / `repo_stock_pin`) を読む `orchestrator/`・`tools/` の file:** T-2304 着地時 (main `2bf985125`) 70 件 → 現在 71 件。増えたのは `orchestrator/campaign/axis_silo_function_policy.py` の `PIN = pin.CURRENT_PIN` 1 件で、その test は submodule の HEAD が PIN で始まることを要求し、silo の template patch を当てる。C は silo の file に触れないので、pin を進めれば別名のまま追随する (template の適用可否は変わらない)。
- **`cc/mocc/transaction.cc` に hunk を持つ patch:** 8 本 (壊し patch 4 本・旧計装 2 本・温度述語 template 1 本・候補 patch 1 本)。材料 §5 の preimage の整理 (旧計装の二重適用、template の移植、hot 経路は C 上で未再立証) から変わらない。

### 3.2 更新 wave の中身 (D2150 項 1 と同じ範囲を想定)

1. ① gitlink・`CCBENCH_FULL_SHA` (`orchestrator/campaign/s8b_approved.py`)・`CURRENT_PIN` (`orchestrator/campaign/pin.py`) を同一 commit で C へ。
2. ④ `buildcache.py` が要求する生成物 (CMakeCache / DependInfo) の形の再実測。C は CMake に触れないので同形の見込みだが、T-2304 と同じく計算ノードで 1 回測る (T-2304 は 26 秒)。
3. ⑦ 現行 pin を期待する test の追随。材料 §5 の追随 15 件は ① の定数 file (`pin.py`・`s8b_approved.py`)、test、runbook・`patches/README.md`・probe を合わせた数で、test だけの件数ではない。**policy epoch の移動** (build admission の policy preimage が `repo_stock_pin = CURRENT_PIN` を含むので policy sha が動く) が SHA 文字列を持たない golden にも波及する。T-2304 では焦点走で 104 failed / 75 errors、受入全走でさらに 24 件が出た (`output/insights/2026-09-20/t2304-pin-advance/README.md` §3)。
4. **判断が 1 件要る:** 衝突の `axis_mocc_temperature.py` は `PIN` が `CURRENT_PIN` に追随する一方、`PROOF_PIN`・template・proof は e9e477ca に束縛されている。更新 wave で「`PIN` を e9e477ca の値に固定して旧 proof の系列として保つ」か「C 系列の proof を作り直す」かを決める (前者が変更最小。温度述語は D2134 項 9 で proof-only)。
5. land 後の submodule 同期: T-2304 と同じく `landed-postcondition-failed` (D16 の同期が要る) になり、主 checkout で `git submodule update` が要る。C の object は主 checkout の submodule 格納域に T-2844 で取り込み済み。
6. ②③⑤⑥⑧ (登録・identity、driver 移行、floor protocol、較正、性能事前登録) は各新系列の着手時。floor protocol の解決器は候補が複数あると gitlink と一致するものを選ぶので、C の gitlink と一致する successor が無い間は MOCC の floor 系列は fail-closed になる (材料 §5、S2 の較正の前に要る)。

### 3.3 工数の試算 (T-2304 の実績からの換算であり、上下限ではない)

- T-2304 の実績: Codex 子は worklog の記録 (`docs/archive/worklog-phase3-0920-1747.md` の T-2304 エントリ) で「15 本 (author 1・review 2・consult 2・fix 7・merge author 2)」。内訳の合計は 14 本で記録内に 1 本の食い違いがあり、insight §8 は記録時点の 8 本。計算ノードは generic 1 (26 秒)・焦点走 3〜6 回 (各 2.5〜3 分)・変異 2 回 (各約 15 分)・受入 4 回。
- 受入 1 回 ≈ 0.25 node 時間 (D2219 項 1 の実測単価) で同じ回数を換算すると、合計は **約 1〜2 node 時間**。確認線 (1 タスク合計 2 node 時間) に近いので、更新 wave は投入前に見積りを出し直し、合計 2 node 時間以上の見込みならユーザーの確認を取る。
- 波及の母集合は T-2844 の材料作成時 (main `36fb14a3d`) より 9 件多いが、増分はすべて据置で書き換えの対象ではない。policy epoch の golden は T-2304 と同じ機構で動くので、fix の規模は T-2304 と同程度を想定する。

### 3.4 並走中の作業への影響

- C は mocc の 1 file しか変えないので、silo の build に入る source の中身は e9e477ca と同じである。ただし運用上の影響はそれだけではない。
- **固定した checkout で続ける作業** (各 wave の worktree は自分の gitlink に従う) は、main を取り込まない限り影響を受けない。
- **新しい main へ移って続ける作業** は、source・build admission・identity の整合が要る。pin 前進で policy epoch が動くので、旧 policy の下で作った binary・lock・凍結物は新 main から live に消費できなくなる (T-2304 insight §4、材料 §5 の「policy epoch」、D2184)。silo を扱う並走 ([T-2847] の壊し patch の変異実走、[T-2863] の silo-function-policy 軸、TPC-C の silo emitter) も、新 main で再投入するなら新しい policy の下で作り直す必要があり、記録される `ccbench_commit` も変わる。旧記録は規律 7 により旧 pin の取得事実として保つ。
- 更新 wave の land 後に main を取り込んだ wave は submodule の同期が要る (T-2304 と同じ)。

## 4. TPC-C の候補 ([T-2854]) との切り分け

- TPC-C の CCBench 側は、ccbench の local branch `izanagi-tpcc-v3-trace` に **現 pin e9e477ca から続く 2 commit** として C1 `56b5cb709628c9cac98e4e18ff676defc77a9117` と C2 `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` がある (D2225)。系図は e9e477ca → C1 → C2 (C2 の親は C1) と e9e477ca → C の 2 系列で、C と C2 の共通祖先は e9e477ca である (2026-09-23 に `git merge-base` と各 commit の親で確認)。
- e9e477ca → C2 の差分は `cc/silo/transaction.cc`・`include/tpcc.hh`・`include/trace.hh` の 3 file (126 行追加・19 行削除)。C の `cc/mocc/transaction.cc` と重ならない (内容の結合確認は TPC-C 設計の単位 11 の仕事)。
- TPC-C 設計 (`output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §5.3・§8 の 3) は「pin 前進は T-2844 の候補 C の上で 1 回」とする。これは同設計の親決定で、「段 1 を急いで使う必要が出た場合だけ 2 回に分ける (+1 wave)」とも書く。
- **TPC-C の候補には未決着がある:** D297 の検査器は header の差分を例外なく拒否するので、`include/trace.hh`・`include/tpcc.hh` を変える TPC-C の候補では fail-closed で落ちる。受理方法 (検査器の拡張・別の保証名・裁定) は単位 11 で決める必要があり、D2225 は「D297 の合格とは呼ばない」とした (`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md` §8)。C は header に触れず、GCC 2 版で D297 に pass している。
- T-2854 は項目として進行中 (単位 1・2・4 済、残り = 存在履歴、単位 5・3・11)。2026-09-23 07:4x の時点で T-2854 の稼働 session・worktree は見当たらない。
- **したがって、C の承認は TPC-C の成果を含む候補の承認ではない。** (a) を選んだ場合、TPC-C の commit は C の上へ載せ替え、単位 11 で改めて承認を求める (そのときの審査対象は C からの差分と、結合後の証拠)。(b) を選んだ場合も、C の承認は C の OID に限られ、TPC-C の差分の承認は単位 11 の提示で別に行う。

## 5. 主張しないこと

- pin を C へ進めてよいこと (ユーザーの裁定待ち)。
- clang での同一性、D297 の合格が規律 1 の十分条件であること (必要条件の一つ、D780)。
- I 被覆、hot 経路の C 上での再立証、同じ大きさのポインタ置換の動的立証。
- 更新 wave の工数・node 時間 (§3.3 は T-2304 の実績からの換算で、C で実測したものではない)。
- 本書の再集計は「文字列を含む file」と「pin 定数を読む file」の数え上げで、更新 wave で変える file の完全な一覧ではない (policy epoch の golden は文字列を含まない)。

## 6. 再現資料

- GitHub 上の実在: `git ls-remote https://github.com/thawk105/ccbench.git refs/heads/izanagi-mocc-xp-instrumentation` (07:44:42 JST)。取得確認: job dir `ghfetch.sh` / `ghfetch.log` (07:50:09 JST)。
- 波及の再集計: `git grep -l "e9e477c" <commit> -- . ':!docs/worklog.md' ':!docs/decisions.md' ':!docs/failures.md' ':!docs/archive/' ':!docs/spool/' ':!output/insights/'` を `36fb14a3d` と `3886a1fd3` で比較。pin 定数の consumer: `git grep -l -e CURRENT_PIN -e CCBENCH_FULL_SHA -e repo_stock_pin <commit> -- orchestrator tools` を `2bf985125` と `3886a1fd3` で比較。mocc の patch: `grep -l "^+++ b/cc/mocc/transaction.cc" patches/*.patch`。
- 系図: wave 木の submodule で `git merge-base 68106660… a6f2c741…` = e9e477ca、`git diff --stat e9e477ca… a6f2c741…`。
