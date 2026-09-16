---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2706-landed-timeout
seq: 1
title: [T-2706] 着地判定器の per-command 上限を実測で 5 秒から 45 秒へ決めた — 受理述語は不変、30 件の Git 操作別完了時間と予算内完走率から (コード + テスト + docs、branch worktree-dev-wave-t2706-landed-timeout、変異 matrix = baseline PASSED・6/6 KILLED・等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---
## 本文
- ユーザー依頼は「`tools/check_branch_landed.py` の per-command 上限 (`COMMAND_TIMEOUT_SECONDS = 5.0`、到達不能 commit 30 件で
  30/30 が `assessment-timeout`) を実測で決める (D2104 項 24)。先に受理述語が不変 (timeout は証拠にならず verdict は決定的証拠
  からだけ出る) であることを現物で確認し、Git 操作別の完了時間と全体予算内の完走率をこの repo で実測して有界な上限値を決め、
  定数を変える。無制限 retry や timeout 管理基盤は作らない。Codex author (D95) + 変異事前登録。本題だけ。gate・台帳の追加は
  scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2706-landed-timeout/README.md`。設計判断は
  {{D:landed-checker-command-timeout-from-measurement}}。実装 commit `73ca7e4e1` (Codex author、製品側は定数 1 行 +
  コメント 2 行、test 6 node)。
- **受理述語の不変を現物で確認した。** `AssessmentError` の捕捉は 10 箇所 (brief の 8 は段 2 plan・段 3 レンズ A が訂正)。
  決定的層 (spool 2 箇所・history scan・最上位) は `indeterminate` にしか落ちず、観測層は verdict に触らない。段 3 の両レンズが
  親の「上限の役割は早期 indeterminate だけ」を反証した — 不変なのは決定的証拠の受理条件で、時間内に確定できる入力集合は変わり、
  観測層の待ちが延びて終端 ref 確認が落ちる逆向きも理論上ある。裁定で不変条件をこの形に書き直した。
- **親の一般化 3 件を段 3 が反証した。** 「重いのは path log だけ」(`--find-object` 26.9 秒、`cherry` 13.7 秒が反例)、
  「5 秒は path log の中央値に掛かる」(全数の中央値は 3.8 秒)、「30/30 timeout は決定的」(同時刻対照では load 11〜25 で
  20/30 timeout・10/30 完走)。記録を実測値へ差し替えた。
- **値は段 4 で事前登録した規則を 30 件完了後に機械的に適用して決めた。** 最大 26.87 秒 × 1.5 = 40.3 → 格子 45。反復点検
  (path log 69 本、最大 35.9 秒、同一 path で 3.7 倍の幅) でも 45 を超えず据え置き。段 5 の暫定 30 (10 件時点) は反復で 2 本が
  超過していたので不採用。焦点再レビューが派生値 8 項目を原データから再計算して全一致。
- **段 6 レビュー: A は GO (nit: M6 除外・`TimeoutExpired.timeout` の assert 追加)、B は NO-GO (コメントの数値が途中集計で
  古い) → fix 子で最終集計の値 (45.0 とコメント逐語) と assert を反映。焦点再レビューは残りを親側の記録 (M6 除外の明記、
  採用値での phase 別 timeout 件数、値文書の誤記 2 箇所) と判定し、親が文書で閉じた。F1 (assert の偽赤は隣接 2 文の間に
  約 1 秒の停止が要る) は fix せず記録。**
- **M6 (`any_path.incomplete` → not-landed) は登録から除外した。** author・レビュー A・B が独立に「`--find-object` の timeout は
  非 spool の `_proof_unit` で捕捉されず最上位へ伝播するため当該分岐に到達しない」と判定。両層変異は一箇所置換の条件を外れる。
- 実走: 焦点走 (計算ノード) 判定器 file 102 passed / 新規 6 node PASSED / fix 後は判定器 + rescue 2 file 182 passed。
  provenance full 10,910 件・新規違反なし。同時刻対照の 30 件 CLI 実走 (既定予算 60): 旧 5.0 = 完走 10 / 確定 0 / timeout 20、新 45.0 = 完走 16 / 確定 3 (landed 1・not-landed 2) / timeout 14 (proof 13・終端 ref 確認 1) / refs-moved 2。完走 16 は無中断推計と一致。
- **変異 matrix (container worktree `.codex/worktrees/t2706-mutcontainer`、dispatch、probe → 本走):** baseline PASSED、負例 6 件
  (M1 timeout 握り潰し・M2 outcome error・M3 既定引数の切り離し・M4 全体予算超・M5 最上位 landed・M7 history scan) すべて KILLED で期待
  node と観測 node が完全一致、等価 M0 (コメント) SURVIVED、MISMATCH 0、TIMEOUT 0、所要 249 秒。専属 killer は M3/M4 (有界 pin) と M7。
- 残存 (scope 外、記録のみ): rescue の内部予算 8 秒では上限を何にしても 30 件のどれも完走しない (推計 0/30)。判定器既定
  60 秒では 16/30 完走 (確定は推計 4・実走 3) で、残りは unit 数 × path log の合計が予算を超える律速。`Git.run` は `OSError` を捕捉しない。
  共有 repo では長い判定が ref 移動に負ける (持ち上げ走 1 件、実走 2 件)。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / `medium`)。親の実測は
  再現 probe 1 本、持ち上げ計測 30 件 (37 分)、反復点検 75 本 (20 分)、同時刻対照 + 新定数の CLI 実走 60 件、焦点走 3 本
  (計算ノード)、変異 2 走、provenance full 1 本。

- [T-2706] 受理述語不変を現物で確認し、30 件の Git 操作別完了時間と予算内完走率から per-command 上限を 45 秒に決めた。

## 次の一手差分
### 完了
- [T-2706] `COMMAND_TIMEOUT_SECONDS` を実測で 45.0 にした。受理述語は不変、正例・負例の test 6 node と変異 matrix で示した。
  残る全体予算 60 秒 / rescue 内部予算 8 秒の律速は下の新規項へ分離した。
  remaining: none
  base: 770a71891c6ca4a1b2e4b1154b5dddb4732c6003d04f8fecef5ef5eb225152bc
### 新規
- {{T:landed-checker-overall-budget-and-rescue-inner-budget}} **P3・新規**: 着地判定器の全体予算 (`DEFAULT_TIMEOUT_SECONDS = 60`) と
  rescue の内部予算 (`DEFAULT_ASSESSMENT_TIMEOUT_SECONDS = 8`、外側 timeout も同値) の配分。per-command 上限 45 秒の実測
  (T-2706 の insight) で、既定 60 秒では到達不能 commit 30 件のうち 16 件しか完走せず (確定は推計 4・実走 3)、8 秒ではどれも完走しない
  (推計 0/30)。残りは unit 数 × `log -- <path>` (中央値 3.8 秒、最大 21〜36 秒) の合計が予算を超える律速で、上限では
  解けない。rescue の実用性 (救出 ref の解消) を回復するなら予算配分の裁定パッケージが要る。名指しの変更に限る D2104 の
  範囲外なので本 wave では変えていない。
