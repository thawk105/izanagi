---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2674-t1998-results-doc
seq: 1
title: [T-2674] [T-1998] balanced stock-inline 対の単独 results 稿を一次資料全体 (権威 bytes・campaign WAL・事前登録・裁定) から書き、README の results 表へ 1 行足した — 敵対レビュー 2 レンズが must-fix 8 / should-fix 6 / nit 1 を出し、全件反映して焦点再レビューで closed 12 / partial 3 / regressed 0 (docs のみ、branch worktree-dev-wave-t2674-t1998-results-doc、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2674] [T-1998] balanced stock-inline 対 (2026-09-13 測定・2026-09-14 認証 accepted、
  improvement_percent 11.225375361916456、認可 D1874) の単独 results 稿を docs/paper-story/results/ 系列の規則どおり書く
  (docs のみ) — 一次資料全体から作り直し、横断稿 results/2026-09-16-b7-three-run-materials.md で補完しない。権威 bytes・
  WAL・事前登録・裁定の対応が欠ける箇所は欠落として明記する。各 arm 5 標本の median 比であって A-1 の対差平均ではないこと、
  A-2 / A-6 とプールしないこと (D1993 項 6)、B-7 の要件充足ではないこと (D2044 項 3) を限定に書く。README の results 表へ
  1 行足す。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の統制稿だけ」。
- **閉じた。** 成果物は `docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md` (results 系列の凍結物、
  限定 20 件、対応が確かめられない 10 項目を「成果物に無い / 束縛の範囲 / 本稿で未照合」の 3 区分で明記) と
  `docs/paper-story/README.md` の results 表 1 行。一次資料は `output/insights/2026-09-18/t2674-t1998-results-doc/README.md`。
  **新しい測定は 1 件も行っていない。凍結物 (事前登録・成果物・既存稿) の bytes は 1 byte も変えていない。**
- 活動を止める裁定は段 1 で 0 件 (検索語「単独稿」「results 系列」「統制稿」「結果節」、D1993 以降。hit は D1993 の理由節と
  D2120 項 15 で、後者は「paper-story の単独 results 稿 = T-2611 / T-2674 の型を使う」と支持側)。
- 段 1 で親が一次資料の現物を全部読み、稿へ写す値を確定した — 成果物 root 23 file の sha256、campaign WAL 40 record
  (8 genome × 5 stage、abort 0)、campaign.lock (loader 束縛 63 blob)、投入受領証、consumer 判定 JSON、事前登録 blob
  (`464e3af5…`、測定 commit `a551cdd3` と現行木で同値)、測定 commit の blob 8 件 (job body・投入器・pipeline・p2_2・
  env_contract・loop は lock / receipt と一致、backoff_sweep.py は loader 束縛外、patch file)。5 標本・median・cv・
  ratio 1.1122537536191646・improvement 11.225375361916456 は再計算で全桁一致。図は無い (figures/ に T-1998 は 0 件)。
- 素材: **正しさ検査の条件 (4 thread・200 tuple・rmw・1 秒・max_ope 5) は成果物のどこにも記録されていない。** lock が束縛する
  pipeline.py の `CorrectnessWorkload` 既定値と、loop.py が `correctness` を渡さず lock の search_config に `verify` key が無い
  という呼出し経路から導いた値であり、稿は「束縛された code の読み取りであって実行時 argv の記録ではない」と書き分けた。
  正しさの記録は「登録 2 arm とも legacy 条件 1 回ずつ serializable / certified / anomaly 0」まで (A-2 / A-6 の
  「legacy 1 回 + performance 5 回」とは形式が違う)。
- 素材: **producer の 8 genome の記録を全部載せたが、事前登録が読む 2 点以外から何も導かない。** 事前登録 §2 / §6 が
  argmax と 6 点の代入を禁じており、稿は登録外の点との比較文を持たない (段 6 レンズ B の指摘で比較文と hash 余談を削った)。
- 段 6 (read-only codex 2 レンズ、`gpt-6-astra` / `medium`): レンズ A (数値・逐語・識別子) must-fix 7 / should-fix 2、
  レンズ B (過剰・削除・限定・裁定整合) must-fix 1 / should-fix 4 / nit 1、いずれも「着地を止める」。**15 件すべて real として
  反映した (B の 8 点表削除案は部分採用 = 表は残し比較文を削除)。** 最重要 3 件: (1) 是正 commit `4d7cd40a9` を最初に含む
  main first-parent 上の commit は `b1a3d45d…` (2026-09-14 08:30:25 JST) で、親の `--since` 付き走査が返した `291892b90…`
  (11:40:29) は取り逃しだった。(2) job の終了時刻と Elapse 712 秒の出所は stdout でなく stderr (NQSV の終了要約) — 親が
  2 file を 1 command で読んで取り違えた。(3) 限定 5 の「温度ドリフトを含まない」は影響の排除に読める断定で、
  「順次測定で時間変化の影響を分離・評価していない」へ撤回。
- **親の手打ちで `tracked_diff_sha256` を 1 桁誤った (`986dc` → `986cb`)。** 稿の全 sha256 と数値を権威 bytes から再計算して
  突き合わせる機械照合 (job dir の使い捨て script) が捕まえた。稿への sha は手打ちせず現物から貼る。
- 焦点再レビュー 1 本 (fix 後、`DW-O16` の対応表): closed 12 / partial 3 / regressed 0、新規所見 0、「着地は止めない」。
  partial の残り 2 件 (§2.1 の「保全されていない」断定、§5.5 の経緯重複) は再レビュー後に直した。
- 変異 matrix は実装面差分ゼロで免除 (`DW-S04`)。三軸語走査 (holdout rr20 / rr80) hit 0。`check_docs.py` rc=0。
  受入全走は land 経路で 1 走 (結果は land の受領証)。
- 運用の記録: codex 起動器の preflight で 2 回止まった (`--base-commit` の省略形 → hex40 必須、artifact dir 不在) —
  いずれも親の argv 作成の誤りで codex は未起動、3 回目で 2 本とも起動。
- 工数: codex 子 3 本 (review 2 / focus 1、すべて `outcome=accepted` / `stop_reason=completed`、model_calls 22 / 6 / 11、
  wall 約 471 / 148 / 265 秒)。親の実測: 一次資料の現物読取と sha256 再計算、WAL 解析 script 3 本、git blob 8 件の取り出し、
  編集面照合 (全 branch)、機械照合 3 回、check_docs 3 回。計算ノード job は使っていない。

## 次の一手差分

### 完了

- [T-2674] [T-1998] balanced stock-inline 対の単独 results 稿を一次資料全体から書き、README の results 表へ 1 行足した
  (`docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md`)。
  remaining: none
  base: 048cfe07239cb7cfa60bc79a4d9252fcc1435a28075dd1c139444148136e169d
