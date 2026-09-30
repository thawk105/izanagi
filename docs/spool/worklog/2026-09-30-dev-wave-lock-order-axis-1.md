---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-lock-order-axis
seq: 1
title: [T-2886] gen-opt md_13: 段 A の軸 silo-lock-order-policy の受理文法・骨格 API・骨格 patch を実装し、名前つき対照を計算ノードで 1 回通した (コード + test + insight、branch worktree-dev-wave-lock-order-axis)
---

## 本文

- 一次資料: `output/insights/2026-09-30/gen-opt-lock-order-axis/README.md`。提案文字列を検疫 → 受理文法 → 単独 compile の順に掛けて hole へ書く `order_gate` と、`validationPhase` の sort 1 行を置き換える骨格 patch (INSERT/DELETE を含む取引は stock の sort、既定 0 で inert)。
- 生死確認 (request 37881.nqsv、bnode052、Elapse 81 s): 名前つき対照 (版が新しいほど先に施錠) が gate を通り、trace・性能 build とも成功、既存判定器は RMW あり / なしとも serializable (certified の根拠ではない)。commit した UPDATE だけの複数書き取引のうち key 順と違う順で施錠したものが 39.17% / 39.24%。1 回目 (37865.nqsv、7 s) は起動器が短縮 PIN を完全 SHA と比べて preflight で止まり、起動器を直して再投入した。計算の合計は 2 node 時間を大きく下回る。
- 段 3 の相談が「禁止名が参照では拒否されるが宣言名 (状態 field 等) としては通る」ことを見つけ、新 profile にだけ宣言位置・参照位置の両方の禁止識別子検査を入れた。既定 profile (関数方策の軸) の受理集合は変えていない。
- 段 4 で、新 macro の登録に従属する件数の固定値と共有 fixture (`condition_gate_test_support.py` の Options.cmake) を列挙し漏れ、実装子の報告と親の焦点走 (7 failed) で見つけて追補裁定 2 本で直した。
- 事前登録の変異 M1〜M6 は独立 clone (2148b469a) で KILLED 6 / 6 (期待 node と完全一致)。1 回目は M5 の期待に login 自走の実行順依存の巻き添え node を入れていて MISMATCH、erratum で直して再走した (一次資料 §3.1)。
- 段 6 の review-a 所見 1 (`-DSILO_ORDER_VARIANT=foo` が `#if` で 0 と評価される) は nit に降格: identity の前処理が `-Werror=undef` で走るので fail-closed で止まる。最初の降格理由 (「STOCK として記録」) は焦点再レビューで誤りと分かり、裁定 file に訂正を追記した。
- 並行で着地した MOCC 版の軸の設計 (gen-opt-mocc-policy-axis §4.3) の「核 + 表」の核の最初の形がこの wave の `PolicyProfile`。同設計の凍結写しとの全 field 差分 test と、compile・IR module の表の分離はこの wave では作っていない。
- 実装子の起動器の終端 commit が `worktree-commit failed reason=add-all` で 3 回失敗した (成果は未 commit で木に残り、親が所有 path 限定で取り出した)。同じ producer で 3 例、原因未調査。
- エージェント工数: Codex plan 1・consult 2・author 4 (A・B・C・変異準備)・fix 5 (B 件数・C 起動器・test 2 巡・件数と fixture)・review 2・focus 1。

## 次の一手差分

### 完了

- [T-2886] silo-lock-order-policy 軸の受理文法 (新 profile + 宣言・参照の禁止識別子)・API header・単独 compile と UBSan harness・`order_gate`・骨格 patch・条件意味 gate への登録・名前つき対照と test を実装し、計算ノードで名前つき対照の生死確認を 1 回通した (一次資料 `output/insights/2026-09-30/gen-opt-lock-order-axis/README.md`)。
  remaining: none
  base: 7c776550a78c8cd3bb2ce079c2fb811e24e542f3266babb4b192a5d006959093

### 更新

- [T-2888] **P2**: gen-opt の driver に、仕様の digest ごとの小モデル結果を build 前に要求する関門 (欠ければ拒否) と、反例を閉じた field で `self_history` へ返す経路を足す。前提の [T-2886] は着地した: 新軸の入口は `orchestrator/campaign/silo_lock_order_gate.py` の `order_gate` (検疫・文法・単独 compile、全検査後にだけ書く。auditor なしの書き込みは origin `initial` / `machine` だけ)、軸定数は `axis_silo_lock_order.py`。driver 接続で要るもの: 全候補をこの gate に通す配線、`orchestrator/codex_roles/policy.py` の axis 固定 (`silo-function-policy`) の扱い、coder 向けの接続仕様 (関数方策の軸の `silo_function_policy_coder_spec.md` に当たるもの)、「並べ替えを使った取引の数」を数える計数 build (段 A の評価の前)。残る前提は [T-2887] の着地。根拠: 関門 §4.4・§7 の U5。
  base: 564bfef84d5c83eb9c835a76f1a5ce7a4c8324abebab5a321c01ced8006be97f
