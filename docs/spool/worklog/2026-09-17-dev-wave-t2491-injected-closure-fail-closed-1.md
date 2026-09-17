---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2491-injected-closure-fail-closed
seq: 1
title: [T-2491] 閉包検査の injected-* 経路を fail-closed へ寄せた — 握り潰された返却物検査を被覆に数えない (D1882 の実装、test file 1 本、branch worktree-dev-wave-t2491-injected-closure-fail-closed、変異 matrix = 旧走 M1 KILLED 3 node で閉包 PASSED / 新走 baseline PASSED・M0 SURVIVED・M1〜M13 KILLED 13/13 期待 node 完全一致・MISMATCH 0)
---

## 本文

- ユーザー依頼は「閉包検査 `test_define_sink_cross_product_has_no_unreviewed_ungated_member` の injected-* 特殊経路について、
  『sink 直後に名前 suffix が一致し第 1 引数が sink の代入名である call が 1 つある』だけでは被覆済みに数えない形へ、名指しした判定だけを
  fail-closed 側へ寄せる (D1869)。F918 が実測した『拒否を握り潰す変異 (except: pass) が閉包検査を通る』穴を負例として登録し KILLED を確認。
  着手直前の local main から fresh worktree。実装面は Codex author (D95)、変異事前登録要。規律 2 を緩めない。本題の判定修正だけ。追加の gate・台帳は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2491-injected-closure-fail-closed/README.md` (逐語は同 `verbatim/`)。設計判断は
  {{D:injected-closure-unswallowed-rule}}。実装 commit `125ab5fd1` + 段 6 fix `79dd07742` (いずれも Codex author、`orchestrator/tests/test_ccbench_spawn_sites.py` のみ)。
  F918 の恒久対応欄は supersede 追記で閉じた。
- **判定の形 (要約):** 記録する check を文の値そのものの call に限り、enclosing try を内側から外側へ辿って、helper の明示的な拒否 (s1 `DriverError`) を捕まえる最初の handler が
  脱出文なしに末尾で再送出することを要求する。bare 再送出は外側でも同じ条件、本 file の class への変換再送出で追跡を止める。TryStar と finally の脱出文は先に落とす。
  判定できない形 (Attribute 型・外来名・再束縛された名前の handler、`raise SystemExit(0)` 等) は被覆に数えない。受理集合は現行 main の真部分集合。
  production の injected sink 4 つ (s1 ×2、s8b_oracle_driver、s8b_oracle_n_pilot) は covered のまま、繰延べ台帳・campaign 経路・既存 test の期待値は不変。
- **段 2 plan が brief v1 の誤りを正した (real)。** 「全 enclosing try に規則を当てる」は s8b_oracle_driver の外側 try (`except Exception` が `break` 終端、実際は
  `if evaluate_started: raise` の条件付き再送出) で誤拒否になる。親が repo 外 probe で 4 check の try 連鎖を実測し「変換再送出で追跡を止める」v1.1 へ訂正。helper の raise 文は 7 でなく 8 箇所。
- **段 3 (2 レンズ) の real 所見:** scope 内 = 到達不能 raise、finally の脱出、TryStar の順序、lambda 内 call の記録、`raise SystemExit(0)`、NONE 分類の再束縛と優先順位、plan の正例が v1.1 では負例
  (すべて段 4 で採用)。scope 外 = 変換後の外側握り潰し、MAYBE 型 handler の未変換経路、suppress / 条件 guard / 代入名の再束縛 (裁定パッケージ候補、下記 新規)。
  前提 pin の assert (P4) と alias chain は最小形 (D1869) で落とした。
- **段 6 レビュー 2 本は実装 must-fix 0。** レビュー A が「裁定の規則どおりだが穴」3 つ (変換先の module 再代入、字句的親関数・引数での束縛、as 名の再代入) を挙げ、親は fail-closed 側へ
  締める fix (R3a〜R3c) と規則ごとの専属負例 5 本 (n13〜n17) を裁定。レビュー B が親の時刻表記 (推定) の不一致を指摘 → mtime で全部実測して訂正 (事前登録 → author 投入 → 実装の順は保たれていた)。
  焦点再レビューは F1〜F3 closed (反例 3 つを独立に組んで拒否を追跡)、must-fix 0。nit (p8 の厳密な一変更対、comment の射程表現) は記録のみ。
- **変異 matrix (計算ノード、`mutation_harness.py --runner-mode dispatch --detached`、使い捨て detached worktree 2 本):** 旧走 (main 38353207f) は baseline 154 passed、
  F918 と同一置換の M1 が KILLED = n_pilot 3 node 完全一致 (151 passed = 閉包検査は緑)。新走 (79dd07742) は baseline 178 passed / 2 skipped、M0 (comment) SURVIVED、
  M1〜M13 の 13 件 KILLED・期待 node 完全一致 (matching 14/14、MISMATCH 0、1 走目で確定、probe 不要)。M1 の注入 diff は旧新で sha256 同一で、閉包検査が旧版 PASSED / 新版 FAILED
  (DW-M08 の差分)。M1 の赤 = 旧 3 + 閉包検査 + 分類 pin 2 + 新 production pin = 7 (冗長 gate = r33 の driver bytes digest pin)。M2〜M13 の専属 killer は新 synthetic 負例
  (M2 → 14 node、M11 → n13 + n16、他は各 1)。
- 実走: 焦点走 66 passed / 1 skipped (125ab5fd1、計算ノード) → 71 passed / 2 skipped (79dd07742、login)。skip は `except*` の 2 例 (Python 3.10、TryStar 規則は実走未検証)。
  受入全走は記録 commit 後に land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、焦点再レビュー 1、全段 `gpt-6-astra`)。親の実測: repo 外 probe 1、焦点走 2、変異 2 走 (17 run)、provenance full 1。
  段 0 で EnterWorktree(name) が「git config を読めない」で失敗し、手動 `git worktree add` → EnterWorktree(path) で回避。author / fix 子は sandbox で dispatch の `qstat -Q` preflight が
  失敗して未実走 (親の焦点走で代替)。

## 次の一手差分

### 完了

- [T-2491] 閉包検査の injected-* 経路を fail-closed へ寄せ、F918 の変異を負例登録して新版 KILLED / 旧版で閉包 PASSED を実測した。
  remaining: none
  base: b65d062caf1964058a269b727925c2c9064ce634eeb590c18df711cd80e117f0

### 新規

- {{T:injected-closure-guarantee-limits}} **P3・ユーザー裁定要**: 閉包検査 injected-* 経路の新判定 ({{D:injected-closure-unswallowed-rule}}) が
  検査しない形を、保証限界のまま置くか閉じるかを裁定する。(1) 変換再送出 (`raise PilotError(...) from exc`) の後の外側の握り潰し — 閉じるには
  s8b_oracle_driver の外側 `except Exception` の条件付き再送出 (`if evaluate_started: raise`) を静的に証明する flow 解析 (D1882 が却下した支配関係解析) を
  認めるか、同 sink を繰延べ台帳へ移すかが要る。(2) Attribute 型など MAYBE の handler が実際に E を捕まえて bare 再送出する未変換経路。(3) `with` の `__exit__` に
  よる抑止、条件 guard 内の check、代入名の再束縛、finalbody 内の check (D1882 の却下範囲)。(4) 前提 pin (helper の明示的な拒否 raise は base `DriverError`、
  `class DriverError(RuntimeError)`) を assert で固定するか (D1869 で落とした)。(5) TryStar 規則の実走検証 (Python 3.11 が要る)。
  一次資料は `output/insights/2026-09-17/t2491-injected-closure-fail-closed/README.md` の「裁定パッケージ候補」。
