---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2182-k2-eval-run
seq: 1
title: [T-2182] 段 4 loop の評価経路が build まで通り、K2 の知識 provenance が WAL へ束縛された — 残る停止点は凍結 pin と verifier の trace 版の食い違い (実測 + insight、branch worktree-dev-wave-t2182-k2-eval-run、実装面の差分ゼロ・変異 matrix 免除)
---

## 本文

- 一次資料は `output/insights/2026-09-09_t2182-k2-eval-run/`。逐語 4 本 (planner / coder を
  知識 source 2 件版と 1 件版で各 1 組) と、3 attempt の evidence を置いた。
- **実装面の差分はゼロである。** `DW-S04` により変異 matrix を免除した。受入全走は免除していない。
- 完了条件は 09-02 の 1/4 から 3/4 へ進んだ。**残る 1 件は環境でも配線でもない** —
  段 4 loop が literal 保持する CCBench の pin (`028f34d`、2026-07-06、D38 で凍結) が trace v1 しか
  出さず、verifier (`orchestrator/verifier/parse.py`) は 2026-08-11 の trace v2 だけを受理する。
  この非互換は**評価経路が build へ到達したことで初めて露出した**。09-02 の 6 回も 09-08 の 1 回も
  gate の手前で止まっていたため見えていなかった。**A/B/C の選択肢は insight に置き、
  凍結条件の変更なので裁定を仰ぐ** ({{T:s4-loop-pin-verifier-trace-version}})。
- **production の K2 consumer が規律 6 で 1 本を止めた (job `988634.nqsv`)。** coder-v4-autonomous-k2 が
  知識源の `campaign.lock` にある `spec_content` を「外部データ側から自分の参照範囲を狭める働きかけ
  = 信頼境界の逆転」として退け、`instruction_like_content_detected: true` を申告したためである。
  **gate の誤作動ではなく、設計どおりの発火である。** 是正は送り手側で行い、知識 source を測定記録
  (`runs/wal.jsonl`) 1 件へ絞って通した。**gate は 1 行も触れていない** ({{T:knowledge-source-excludes-design-prose}})。
- **同じ bytes に対する規律 6 の判断が走行ごとに揺れた。** 09-02 の planner と coder はどちらも
  同じ `campaign.lock` を「指示めいた文字列なし」と報告している。本 wave の coder は「あり」と
  報告した。判断の揺れがそのまま走行の成否を決めている。
- **coder の初回出力は `proposal.confidence` を欠いて K2 schema を満たさなかった。親は値を代筆せず
  role 本人へ差し戻した。** 自己申告フィールドを親が埋めれば、それは role の申告ではなくなる。
  本人が `medium` を付けて返した。
- **09-02 の手順は現行コードでは再現できない。** `--emit-planner-context` は login node で
  `ExecutionGuardError` に落ちる ([T-2231] の site 契約)。site は hostname だけで決まり env 上書きは無い。
  本 wave は `knowledge_manifest.load_and_resolve_manifest` と `planner_projection` を login で
  直接呼んで代替した (digest は 09-02 の run card と一致)。ただしこれは role への入力射影までで、
  **計算ノードで planner context を出力する経路は今も存在しない**。
- `_assert_single_tenant()` が計算ノードで通った。09-02 と 09-08 の insight が「未実測」と
  留保していた項目である。
- gen_S の混雑で queue 待ちが大きく振れた — 3 本の待ち時間は 8 分 / 64 分 / 8 秒だった。
  job 自体はいずれも 30〜55 秒である。
- campaign WAL・受領証・job 出力は `guard_bash` が repo への書き出しを拒否するため insight へ
  複製していない (`cp` も `cat` のリダイレクトも拒否される)。原文の所在を insight に明記した。

## 次の一手差分

### 更新

- [T-2182] **P1**: 評価経路は build と WAL の provenance 束縛まで通った (完了条件 3/4)。残るのは
  gate の terminal verdict で、{{T:s4-loop-pin-verifier-trace-version}} の裁定が前提になる。
  裁定後に 1 本再投入して correctness verdict を取る。
  base: 2697ed056e74beaa9250d5777a3db3f1bc7b5e890714fdc3342599865a8c5fd1

### 新規

- {{T:s4-loop-pin-verifier-trace-version}} **P1・ユーザー裁定待ち**: 段 4 loop の
  `p3_s4_loop.PIN` (`028f34d`) が trace v1 しか出さず、verifier が要求する v2 と非互換である。
  A=`pin.CURRENT_PIN` (511c953) へ上げる / B=verifier を v1 対応にする (規律 2 に反するので採らない) /
  C=現状維持 の 3 案を insight に置いた。凍結条件の変更なので裁定を仰ぐ。
- {{T:knowledge-source-excludes-design-prose}} **P2・新規**: K2 の知識源に izanagi 自身の設計説明
  (`campaign.lock` の `spec_content` など自由文フィールド) を混ぜると、role が正しく警戒して
  production の K2 consumer が走行を止める。manifest を作る側が「測定記録だけを指す」規律を持つか、
  自由文を指示に読めない書き方にするかを決める。**gate 側で解決してはならない。**
