---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2792-a1-sized-rerun-auth
seq: 1
title: [T-2792] A-1 sized attempt-0002 を投入可能にする択 1 — rear gate と公開先 gate に exact な認可 record の入力を足し (定数 1 件 × 一致 record × 先行 attempt-0001)、producer subcommand と事前登録 §6.1 / §6.4 の追補 (別版) を着地した (コード + docs、branch worktree-dev-wave-t2792-a1-sized-rerun-auth)
---

## 本文

- ユーザー裁定 D2172 項 2 (2026-09-20、第 24 回 /rulings 項 2、択 1 を attempt-0002 の 1 attempt 限定で認可) の実装 wave。依頼文の逐語は insight
  `verbatim/T-2792-origin.md`。一次資料は `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` (brief・plan・相談・裁定・
  レビュー・fix の逐語、実測、変異台帳)、追補は `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`、設計判断は
  {{D:a1-sized-rerun-authorization-record-gate}}。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/HANDOFF.md`。
- 起点 local main `371674ea6`。brief 前の実測: 現行 gate を実 durable base に read-only 実走し同 study の attempt-0002 を拒否・別 study を受理、
  事前登録 README は policy・契約 v2・driver・test の 4 箇所で sha 束縛 (凍結)、base を走査するのは driver 1 箇所、driver に live な bytes pin なし
  (AST 構造 pin 4 本のみ)。**実 base には 1 byte も書いていない** (dogfood は job dir の複製で行った)。
- 段 2 plan (codex read-only) は P1/P3/P4/P5 支持・P2/P6/P7 条件付き。段 3 consult 1 本 (2 レンズ + 全層到達性) は **must-fix 2 / should 3 / nit 3、全件採用
  (refuted 0)**: A1 = 認可対象の attempt を限定しても解除する先行証拠が限定されていない (attempt-0003 が bench 到達済みでも通る) → 定数に先行 attempt 名
  `attempt-0001` を固定、B1 = 配線 test は intent 前の sentinel でなく `_run_qsub` 捕捉まで通す → job_contract test を変更面に追加 (3 file)。
  全層到達性: job shell / measure / lock preseed / barrier / complete / materialize に先行 attempt を理由とする他の拒否なし (trial registry 内部は親が読了、
  `ident.py` 内部は未読)。
- 段 5 は Codex author 1 本 (driver +146/−3、paired test +396/−3、job_contract +73、新 test 22 関数 / 52 case)。**author と fix 子は pytest を実走できない**
  (sandbox 内の dispatch は qstat preflight rc=16、login の直接 pytest は guard 拒否) → 「実装済み・未実走」で受け取り、親が計算ノードへ dispatch した。
- 段 6 レビュー 2 本 (A 正しさ境界 / B 過剰・削除) は **must-fix 各 1 = 同一 (spawn-site 台帳が driver の `run_measurement` sink を行番号 7428 で pin、
  挿入で 7545 へ移動)**。受理集合の逸脱・保存条件の緩和・非認証 lane の変更は両者とも発見なし。fix1 (Codex) で lineno 2 箇所と nit 3 件 (digest helper の
  重複検査、duplicate case の単一理由化、item case を 2.0 に) を closed。追補の文言 (digest の対象・先行 attempt 名は定数側・拒否範囲の限定・完全性検査の
  言い方・見出し) は親が是正。焦点再レビュー子は起動せず (must-fix は機械的な lineno 追随 1 件、焦点走の緑で閉じた)。
- 実装 commit `886c19259`、追補 commit `ec696308a`、記録 commit は本 fragment の commit。計算ノード焦点走 (11 file = 変更 3 + consumer / メタ 8):
  未 commit 差分での走 (request 12491) は 1695 passed / 2 failed (作業木 dirty 検査と台帳 lineno)、**commit 886c19259 での走 (request 12519) は
  1697 passed / 0 failed / 6 skipped**。replica dogfood (実 base の attempt-0001 証拠を job dir へ複製、path 書換 + digest 再計算): record 無し = 拒否、
  exact record = 受理、不一致 9 種 = 全部拒否 (gate 単体の証明であり qsub 到達・materialize 全工程の証明ではない)。
- 変異 matrix (独立 clone @886c19259、計算ノード dispatch、2 test file 全走、等価対照 1 + 負例 14): probe (全件 SURVIVED 登録) で観測 node を集め、final で
  **baseline PASSED・14/14 KILLED (期待 node 完全一致)・M0 SURVIVED・MISMATCH 0**。record 不在 / attempt 名 (定数側・比較側) / study (定数側・比較側) /
  source sha / 裁定 id / digest / 完全性検査 skip / 先行 attempt の限定解除 / 公開先 create-only / record 無しの兄弟公開先 / producer の再作成 (2 hunk) /
  submit 配線の各変異を単一 node 群で殺した。詳細は insight §5。
- 限界・言わないこと: 投入も測定もしていない (attempt-0002 の値・稿・図は無い)。認可 record は署名でも「性能値を見た後の選択」を防ぐ装置でもない。
  追補 file 自身の実行時 digest 検査は無い (束縛は source commit 経由)。配線 test は scheduler 境界まで (fixture が policy-ready / CCBench / git /
  durable base / hostname / qsub / qstat を stub)。L-A1S-4 は残る。
- 段 1 の見落とし (記録のみ、fix 1 巡で吸収): `test_ccbench_spawn_sites.py` の行番号 pin を DW-O09 の閉包で読まず、焦点走 (DW-O26 の consumer 集合) で検出。
- 工数: codex 6 本 (plan 1、consult 1、author 1、review 2、fix 1)、計算ノード job = 焦点走 2 + 変異 (probe + final) + 受入。

## 次の一手差分

### 更新

- [T-2792] **P1・実装済み (択 1、D2172 項 2) → 投入手番 (AI、別 wave)**: land 後に fresh submit-tree を作り、その HEAD を `--expected-head` にして
  `paper_story_a1_paired.py authorize-rerun --study-id paper-story-a1-20260901-balanced5-sized-v1 --attempt-root <base>/attempt-0002 --decision D2172
  --decision-item 2 --decided-on 2026-09-20` で durable base に record を置き、既存 `submit` (hydrate 済み third-party source root 必須) を 1 回実走する。
  どこかの層で落ちたら再投入せず報告して止める。materialize の公開先は兄弟 dir `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`。
  成果 = attempt-0002 の results 系列稿と 2 attempt の並記 (プールしない、D1993 項 6)。gate の設計は {{D:a1-sized-rerun-authorization-record-gate}}、
  追補は `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`。
  base: 437f0d0d3c2cff95e47fc47c37ff917d10ce59c33b761eade3bb75c285dfbf24
