---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-md20-lock-order-loop
seq: 1
title: [T-2946] gen-opt の段 A の軸 (競合度順の施錠) を探索ループにつないだ — 要求つき判定器・D5 の build 時 snapshot への束縛・小モデル結果の関門・反例の閉じた返却、名前つき対照の 1 周は fixture 付きの配線確認 (コード + test + insight、branch worktree-dev-wave-md20-lock-order-loop)
---

## 本文

- 依頼: gen-opt 第 5 陣 md_20 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20.txt`)。一次資料 `output/insights/2026-09-30/gen-opt-lock-order-loop/README.md` (段の記録は同 `verbatim/`、変異は同 `mutation/`)。
- commit: `61aaf3714` (段 5 統合、Codex author 2 単位)、`c33afae78` (段 6 fix 1)、`8631dee79` (段 6 fix 2) と記録 commit。
- 生死確認 (計算ノード 1 job、fixture 付きの配線確認で certified の主張ではない): 名前つき対照を driver の関数経路で通し、本番の登録簿 (未登録) では `model-unregistered` で build 0 回。fixture の結果を明示すると、U1 + Silo 修正 + 骨格の trace build で 2 workload とも D1・D2 違反 0・D5 pass・要求 true・版 2・certified、Silo 修正なしでは D2b 違反で `verifier-not-certified` を返した (live-2、40121.nqsv、bnode058、Elapse 160 s)。live-1 は dispatch の job 環境に TMPDIR が無く起動器の preflight で止まった (5 s、build 前)。
- 焦点走: f1 38 file 10 failed / 3,860 passed、f2 39 file 1 failed / 3,900 passed、f3 41 file 4,055 passed / 11 skipped (40135.nqsv)。赤はすべて自分起因 (実装子が試験を走らせられず出した新 test の組み立て 8、perf 閉包への不要な追記 1、run_campaign の末尾 2 引数の順序 1、層 3 の閉包 test 1)。
- 変異: 事前登録 16 本 (等価 1 + 負 15) の本走が完全一致 (KILLED 15・SURVIVED 1、40203.nqsv)。M2 (loop.py の運搬) は閉包 file のため contract-loader-drift の赤しか出ず owner の証拠なし。M13 は置換位置が test の経路外で、M13b へ狙い直した (`mutation/erratum-1.md`)。親が probe の完全 SHA を手打ちで誤転記し 1 回空振りした (5 s)。
- 段 3 相談 2 本 (A NO-GO・B 条件付き GO)、段 6 レビュー 2 本 (A NO-GO・B 条件付き GO) と焦点再レビュー 1 本 (NO-GO)。real で直した最重要: 要求つき build が build 出口の再照合で必ず不一致になる (buildcache が要求を知らない)、成功時の検証結果が driver に届かない (pipeline が反復ごとに verify_result を捨てる → WAL の verify_done に gate 節を載せ driver が全件を照合)。refuted: 登録外の場面の反例で拒否するのは過剰 (拒否は安全側)。backlog: 要求つき local 並列検証の受信側 (N1、fail-closed)、WAL 記録数と期待反復数の照合 (N2)。
- セッション異常: 段 5 の実装子 2 本が子の sandbox で試験を走らせようとして rc=16 で同時に途中停止した (親の prompt の書き漏れ、{{F:author-stop-rule-hits-untestable-sandbox}})。継続子で完了。2026-10-01 00:4x〜03:10 は利用上限で一時停止 (land 調整役の指示)。
- 工数: Codex plan 1・consult 2・author 2 + 継続 2・起動器 author 1・fix 3・review 2・focus 1 (計 14 本)。計算ノード 約 0.44 node 時間 (焦点走 3・生死確認 2・変異 4 の job 合計、受入を除く)。
- D442: 判定器 (core.py・model.py) の bytes が変わったので、変更前に作った campaign lock は land 後の main から読むと drift になる (md_14 と同じ帰結。生成器対照の本走は submit checkout)。

## 次の一手差分

### 完了

- [T-2946] gen-opt の軸の driver から判定器を要求つきで呼び、capability 経路・pipeline・build 出口の再照合に要求を通し、D5 を build 時の source snapshot に束縛した (`output/insights/2026-09-30/gen-opt-lock-order-loop/README.md` §1・§4・§5)。pipeline 経由の certified の取り直しは pin 前進の後に [T-2896] で行う。
  remaining: none
  base: ad2f6db8a92f50dac117bce5c12666c57c65f4c05605a027d52d0e19e74f4a14

### 更新

- [T-2888] **P2**: gen-opt の driver `orchestrator/campaign/p3_s4_loop_lock_order.py` と小モデル結果の関門 `silo_lock_order_model_gate.py` (受け口 `cc-model-result/1`、期待 digest と登録場面は軸の定数から取り既定は未登録 = 全拒否、反例は `validate_counterexample` 済みの閉じた field で history へ) は着地した (`output/insights/2026-09-30/gen-opt-lock-order-loop/README.md` §2・§3)。残り: (1) md_19 の着地後に `axis_silo_lock_order.py` の登録簿へ仕様 digest・登録場面・語彙を書き、実物の結果で関門を通す (結果が実際の checker の実行から来たことを登録の判断点で確かめる。受け口が実物と合わなければ最小差分で合わせる)。(2) LLM の coder role (agents・manifest・adapter・`codex_roles/policy.py` の axis 固定・`projection_guard` の contract) と coder 向け接続仕様。(3) 要求つきで local 並列検証を使うなら受信側の key 集合を要求で切り替える、本評価の前に WAL の verify_done 記録数を期待反復数と照合する (同 §6・§7 の N1・N2)。
  base: c6c85c2151b20db7f98050951ac9bb83e6cfc3eccecba72a4b700304f21b12e2
- [T-2896] **P2**: 段 A の試し 1 本 (D2289)。候補は **競合度順の施錠** (`output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md`)、名前つきの対照は Cicada の近似 (版が新しいほど先に施錠)、workload は 3 点を結果の前に登録する。前提の済み: [T-2884] (判定器 版 2)・[T-2886] (軸の入口)・[T-2887] (小モデル部品)・[T-2946] (要求つき判定の配線、driver は `p3_s4_loop_lock_order.py`)。残り: U1 と Silo 修正を含む pin への前進 ([T-2854]・[T-2917]。前進後に骨格 patch の当て直しと pipeline 経由の certified の取り直し)、この軸の小モデルの結果 (3 取引の層を含む) の本番登録と [T-2888] の残り (1)(2)、計数 build (並べ替えを使った取引の数)。計算: pair job 1 本 0.206〜0.220 node 時間で、対照 1 本 × 3 点 ≈ 0.62〜0.66、LLM の候補 2 本を足して 9 本 ≈ 1.85〜1.98 node 時間、小モデルの 3 取引の層を計算ノードで流すと仮定付きで約 1.6 が加わり 2 node 時間を超えるので、投入前に land 調整役へ相談する。要求つき判定の追加所要は 20 万取引規模で 11〜12 s/run (md_20 の小規模の実測、本評価の規模では未測定)。job は workload × 反復で割って 1 本 5 分程度にする (pair は 1 job に入れる)。優先度は親の暫定。
  base: b123526514738da1dc254cff0275a627546f2cd9fe5d3400463c00d86ecf54b4
