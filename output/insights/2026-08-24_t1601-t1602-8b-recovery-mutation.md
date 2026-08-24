# [T-1601][T-1602] 8b 中断復帰 semantic core — 変異台帳と検出力の実測

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は測定記録
(measurement record) であり、裁定台帳ではない。

- 起点: 段4 裁定 (`stage4-adjudication.md`) の変異事前登録 12 件。裁定正本は D739 / D740。
- 測った checkout: branch `worktree-dev-wave-t1601-t1602-8b-recovery`、
  変異束縛 commit `8788f1119b76ff26809c5d5e7c67aa4bd1ca0d91`。
- 変異 spec: `izanagi-dev-wave-mutation-spec/v1`、
  sha256 `495b191e83614463de2f93df8e6f25526d83d427dd5bcf9c2403827572fcbe6f`。
- 結果 schema: `izanagi-dev-wave-mutation/v4`。
- 実行環境: Pegasus 計算ノード dispatch (`--runner-mode dispatch --detached`)。
  runner argv は `python3 tools/run_tests.py` に対象 3 file と
  `-q -p no:randomly -rf --force-dispatch` を渡す形で固定した。

---

## 1. 結果

baseline PASSED。12 変異すべて KILLED で、期待 node 集合と実測 node 集合は完全一致した。
SURVIVED、MISMATCH、TIMEOUT、PARSE_ERROR はいずれも 0 件である。

| ID | 単一変異 | 置換数 | 期待 node 数 | 結果 |
|---|---|---|---|---|
| m01 | core の semantic event 集合から `recovery` を外す | 1 | 33 | KILLED |
| m02 | 復帰理由の閉集合から `node_failure` を外す | 1 | 2 | KILLED |
| m03 | receipt の対象 start-event hash 比較を落とす | 1 | 1 | KILLED |
| m04 | authority policy hash の exact 比較を落とす | 1 | 1 | KILLED |
| m05 | nested receipt の digest 再計算比較を落とす | 1 | 1 | KILLED |
| m06 | start owner と復帰者の identity 差検査を落とす | 1 | 4 | KILLED |
| m07 | terminal 後の recovery 排他を落とす (2 層) | 2 | 2 | KILLED |
| m08 | recovery 後の terminal 排他を落とす (2 層) | 2 | 2 | KILLED |
| m09 | 次 ordinal の verified recovery 条件を無条件拒否へ倒す | 1 | 2 | KILLED |
| m10 | 復帰 row の exact key 集合へ `primary_value` を足す | 1 | 34 | KILLED |
| m11 | 通常 retryable 集合へ復帰の 2 理由を混入する | 1 | 4 | KILLED |
| m12 | 8c profile の event 表へ `recovery` を足す | 1 | 1 | KILLED |

合計 87 node。m09 だけが正例側の過剰拒否を測る変異で、他の 11 件は負例が受理へ反転することを測る。

---

## 2. 2 層 gate を持つ 2 件は両層同時に変異させた

m07 と m08 は、同じ入力を拒否する層が 2 つある。

- m07 (terminal 後の recovery): `assert_registry_rows` の replay 分岐と、
  `record_attempt_recovery` の事前検査。
- m08 (recovery 後の terminal): `assert_registry_rows` の replay 分岐と、
  `record_attempt_terminal` の事前検査。

API 側の検査だけを落としても、API が最後に `assert_registry_rows` を呼び直すため replay 層が
拾ってしまい、変異は生き残る。片層だけの変異は「他層の mask」であって検出力の証拠にならないので、
両層を 1 つの変異として累積適用した。各置換は適用後に一意性を再検査している。

---

## 3. 注記 — 落ちる node が広い変異が 2 件ある

m01 と m10 は node 数が 33 / 34 と際立って多い。これは検出力が広いのではなく、
**変異した gate が復帰意味論そのものを支えている**ためである。

- m01 は core の semantic event 集合から `recovery` を外す。以後どの復帰 row も
  unknown-event として拒否されるので、正例も負例も一括で落ちる。
- m10 は復帰 row の exact key 集合へ鍵を 1 つ足す。8b の exact-key 契約は「過不足なし」を
  要求するので、狙った負例 (primary 注入が受理へ反転する) が起きるのと同時に、
  正例側が「必須の鍵が足りない」で落ちる。この 2 方向を分ける単一理由の変異は、
  exact-key 契約を保ったままでは作れない。

どちらも gate 1 つ・原因 1 つ・node 多数である。node 数の多さを検出力の広さと読み替えてはならない。

---

## 4. anchor の再照準と probe

段4 の事前登録は散文なので、実装後の commit に対して anchor (old 逐語) と期待 node を
取り直した。手順は次のとおり。

1. 12 件の anchor を実体から抜き出し、各 `old` が対象 file 内で厳密に 1 回だけ現れることを検査した。
   複数置換を持つ変異は、先行置換を適用した後の本文で一意性を再検査した。
2. 全件を SURVIVED 期待で登録した probe spec を作り、統合 commit の作業木で
   一時変異 → 焦点走 → `git checkout --` 復元を 12 回繰り返して失敗 node を実測した。
   probe script は repo の外に置き、repo へは 1 byte も残していない。
3. 実測した失敗 node をそのまま期待 node の完全集合として最終 spec へ写し、本走した。

probe と本走で node 集合は完全に一致した。probe は login node、本走は計算ノードなので、
実行場所の差が結果を動かさないことも同時に確かめたことになる。

---

## 5. 変異本走の source を隔離した理由

`tools/mutation_worktree.py` は、走行の前後で primary worktree と source worktree の
`git status --untracked-files=all` を突き合わせ、bytes が変われば `rc=125` で落とす。

この repo の main checkout には `.codex/worktrees/` が **未追跡のまま**見えており、
並行セッションがその下で worktree を作る・触るだけで snapshot が変わる。今夜は 5 本以上の
セッションが同時に走っていたので、main を source にすると本走が落ちる確率が高い。

そこで固定 commit を持つ独立 local clone を作り、それを `--source-repo` に渡した。
clone は誰も触らないので primary も source も同じ木に閉じ、事後検査は緑で通った (rc=0)。
この前提は別 wave が先に実測しており、本 wave はその回避策を再現しただけである。

---

## 6. 限界

- 本走は焦点 3 file (`test_attempt_registry_core_s8b_profile.py`、
  `test_attempt_registry_core_equivalence.py`、`test_reflux_formal_consumer.py`) に対して行った。
  suite 全体に対する変異は行っていない。
- 変異は core と 8b profile の受理条件を測るものであり、**収集器が無いこと**は測っていない。
  scheduler accounting を実際に読む経路は存在しないので、production の authority が
  正しい receipt を出すかどうかについて本文書は何も言わない。
- m10 の注記のとおり、exact-key 契約を保ったまま「注入の受理反転」だけを単独で測る変異は
  作れていない。この 1 点は検出力の証明ではなく、契約の形から来る限界として残る。
