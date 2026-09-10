# [T-2324] 段 1 brief — 床値 official の §8 承認束縛

base main = f486ff13c / branch = worktree-dev-wave-t2324-official-approval-binding

## scope

床値 campaign の official 走行を塞いでいる「§8 未裁定」を理由とする無条件拒否を、D926 が定めた
承認束縛 (official 専用の別系統・submission nonce 値の env・job script での exact 一致・
不一致は build と driver より前に fail-closed) へ差し替える。走らせるのは受入まで。実測投入はしない
(D1641 の測定認可は本 wave の成果に含めない)。

## 確定済みユーザー裁定 (再裁定しない)

- D926: 方式は D461 型の submission nonce 束縛。official 専用の zero-arity 引数と nonce env を
  pilot 用とは別系統で追加。`tools/pegasus/floor_campaign.sh` は固定 official argv へ変更し
  mode の受け口は作らない (D323 不変)。job-result・失敗文言・guard・無条件拒否テスト・手順書を
  同じ変更単位で直す。**submission receipt schema、admission claim key 6 項目、
  refreeze 不適格 seam の 18 名集合、`_derive_refreeze_eligibility` の判定式は変更しない。**
- D926 の却下肢を復活させない: 承認を無条件 append する wrapper、core 拒否の撤去だけ、
  receipt へ `user_approved`、`result.json` の自己申告を信頼根、承認検証を claim 予約より後へ置く。
- D1562 / D1628: staged transport は driver 内部の既定へ移った。18 名集合と判定式は literal 不変。
- D1161: 予算承認 `output/s8b-freeze-budget-approvals/g1.json` は実在 (thawk105、2026-09-05)。
- D95: 実装面は Codex `role=author` の子だけが書く。親は docs 本文のみ。

## 実測した前提 (brief 前)

- **(新事実 N1) D461 が記述した nonce 束縛は repo に実装が無い。** `tools/pegasus/submit_floor.sh`
  は flag が `--dry-run` / `--repo-root` / `--attempts-root` / `--job-script` の 4 本だけで承認 flag を
  持たず、`floor_campaign.sh` にも承認 env の受け口が無く、`s8b_floor_campaign.py` に
  `--confirm-*` 系の承認 flag が無い (`--confirm-user-freeze` は freeze-protocol 専用)。
  実在する `--confirm-irreversible-pilot-holdout` は **oracle N pilot** 側
  (`tools/pegasus/submit_oracle_n_pilot.sh:106,152`、`tools/pegasus/oracle_n_pilot.sh:346,360,375`、
  `orchestrator/campaign/s8b_oracle_n_pilot.py:2794`) にあり、env は
  `IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT=1` の**固定 literal** で nonce ではない。
  reserve/consume 分岐では job script が無条件に append する。
  したがって「D461 型」は**設計の型**であって写せるコードではなく、nonce 一致検査は新規に書く。
  D926 の方式そのものは変わらないので再裁定は要らない (段 4 で明記する)。
- (N2) `submit_floor.sh:621` は既に `export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE"` を持ち、
  `floor_campaign.sh:41-43,547-549` が 32 桁小文字 hex を 2 度検査する。official 承認 env の
  比較対象はこの値であり、新しい nonce 生成器は要らない。
- (N3) `_nondefault_campaign_seams` は明示 kwargs だけを受ける (7082 / 7185 / 7262)。承認引数を
  そこへ渡さなければ 18 名集合は自動的に不変。D926 の「承認 bool は seam でない」は構造で満たせる。
- (N4) DW-G04 の発火経路は書ける — `submit_floor.sh --<official 承認 flag>` →
  `qsub -v <承認 env>=$NONCE` → `floor_campaign.sh` の exact 一致 → driver argv へ 1 個 append。
  予算承認 g1.json も実在するので発火条件は満たせる。
- (N5) `s8b_holdout_freeze.py` の 2 箇所は**別命題**である。940 の
  `_reject_unratified_generation` は v2 世代 schema field を持つ文書の発効拒否、951 は
  `_verify_source` の blob 救済照合を封じる根拠説明。どちらも D926 が裁定したのは
  「official 走行の承認方式」であって「v2 世代文書の発効経路」ではない。**拒否そのものは残し、
  古い理由 (§8 未裁定) だけを現状に合う文言へ直す** (規律 2)。

## 不変条件

1. official は承認が exact 一致で示されない限り拒否する。空文字・未設定・不一致はすべて拒否。
   拒否は build・driver 起動・claim 予約・副作用より前。
2. core と CLI の二重拒否を保つ (δ-3)。片方だけにしない。
3. 18 名 seam 集合、`_derive_refreeze_eligibility` の判定式、submission receipt schema、
   admission claim key 6 項目は 1 byte も変えない。
4. `_derive_refreeze_eligibility` の導出が承認 gate より前に来る call-order を保つ
   (`orchestrator/tests/test_s8b_floor_campaign.py:7805` が source 逐語で pin している)。
5. pilot の既存経路・既存拒否・既存テストの意味を弱めない。
6. 承認引数は seam 分類へ渡さない。

## 変更面 (実アンカー表)

| # | file:line | 現状 | やること |
|---|---|---|---|
| A1 | `orchestrator/campaign/s8b_floor_campaign.py:465-476` | `_assert_official_permitted(mode)` が official を無条件拒否 | 承認引数を受け、未承認のときだけ拒否。文言を条件ごとに差し替え |
| A2 | 同 `:7205-7208` (`run_campaign` public wrapper) | `_assert_official_permitted(mode)` | 承認を受け取り渡す。seam 分類へは渡さない |
| A3 | 同 `:7304` (`_run_campaign_core`) | `_assert_official_permitted(mode)` | 同上。`_derive_refreeze_eligibility` (7277) より後の位置を保つ |
| A4 | 同 `:8435` 付近 (`_parser`) | official 承認 flag が無い | zero-arity flag を新設 (official 専用の別系統) |
| A5 | 同 `:8599-8607` (CLI) | official を無条件 refuse し rc=2 | 承認 flag が無い official だけ refuse。文言を差し替え |
| B1 | `tools/pegasus/submit_floor.sh:35-60,621` | 承認 flag 無し / `export_spec` は nonce 1 本 | zero-arity 承認 flag と、値が `$NONCE` の承認 env を追加 |
| B2 | `tools/pegasus/floor_campaign.sh:41-43,547-552` | nonce 検査のみ | 承認 env が設定済みなら nonce と exact 一致を要求。不一致は `write_failure 2 submit_binding` |
| B3 | 同 `:1202` | `--mode pilot` | 固定 official argv へ変更 (D926) |
| B4 | 同 `:1329,1360,1377` | job-result / 失敗文言が `pilot` | official 側へ揃える |
| C1 | `orchestrator/campaign/s8b_holdout_freeze.py:934-941` | 拒否理由が「§8 で未裁定」 | 拒否は残し理由文言だけ現状へ (N5) |
| C2 | 同 `:944-957` (`_verify_source` docstring) | 同じ古い理由 | 同上 |
| D1 | `orchestrator/tests/test_s8b_floor_campaign.py:7081-7130,7273-7300,7805` | 無条件拒否と call-order を pin | 承認あり/なしの正例・負例へ書き換え。call-order pin の逐語を新 signature へ |
| D2 | `orchestrator/tests/test_pegasus_floor_tools.py` | wrapper の token 検査 (D324) | 固定 official argv と承認 append の検査へ |
| E1 | `docs/pegasus-runbook.md` / `docs/phase3-8b-restart-runbook.md` | pilot 投入手順 | official 投入手順と承認 flag を記載 (親が書く) |

## 触らない

`REFREEZE_DISQUALIFYING_SEAM_NAMES`、`_derive_refreeze_eligibility` 本体、
`floor_submit_receipt.py` の schema、`certified_writer_admission.py`、
`orchestrator/tests/test_official_perf_closure.py` (稼働 wave が所有、承認経路は perf を呼ばない)。

## 成果物の影響 (DW-G05)

放置すると A-4 (床値 official) の実測が起動できず、§8 の「未取得」欄が変わらない。実装すると
official 走行が**承認付きの標準投入経路でだけ**起動可能になる。certified 選択の値・受理集合は
本 wave では変わらない (走らせないため)。承認なしの official は従来どおり拒否されるので、
受理集合が広がるのは「nonce 一致の承認を伴う投入」の 1 点だけである。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) 固定 official argv にすると、標準投入経路から pilot 床値が起動できなくなる。**
  親の provisional 裁定 = D926 の明文なのでそのまま実施する。段 2/3 は「pilot 床値を
  `floor_campaign.sh` 経由で必要とする生きた consumer が現に居るか」を実測で示すこと。居れば
  新事実として段 4 で裁定へ返す。
- **(P2) `s8b_holdout_freeze.py` は文言だけ直し挙動を変えない** (N5)。段 2/3 は「D926 が
  v2 世代文書の発効まで裁定していると読める根拠」を探して反証すること。
- **(P3) 承認 flag は core の引数として渡す (env を core が直接読まない)。** D1628 が
  「生の環境変数を authority にしない」と定めた向きに合わせる。段 2/3 は env 直読を要求する
  既存契約が無いか確かめること。
- **(P4) 承認 gate の位置は現在の `_assert_official_permitted` 呼出し点を動かさない。**
  D926 は「claim 予約より後へ置く」を却下しており、現在位置は claim より前。段 2/3 は
  現在位置が本当に build・claim・副作用のすべてより前かを code で確かめること。

## 並列分割方針

- 段 2: plan 子 1 本 (file:line 粒度)。
- 段 3: 敵対 2 本 — レンズ α「承認 gate の bypass 面と恒真化」、レンズ β「D926 の禁止事項
  (18 名集合・判定式・schema・却下肢) への抵触と pin 閉包の取り残し」。
- 段 5: 実装 2 単位 — U1 = driver (A1-A5) + C1/C2、U2 = 投入経路 (B1-B4) + テスト (D1/D2)。
  境界は file で分ける (U1 は `orchestrator/campaign/`、U2 は `tools/pegasus/` と
  `orchestrator/tests/`)。
- 段 6: 敵対レビュー 2 本 + fix 1 本 + 変異 matrix + 受入全走。

## 起動時検査

- 同名 wave なし。startup gate rc=0 (fresh、external handoff)。submodule 再帰初期化 rc=0。
- 編集面重複 (branch tip、未 commit は 0 件):
  `worktree-dev-wave-acceptance-speedup-20260905` が `test_s8b_floor_campaign.py`
  (@84 / @1690-1712 / @1746 以降)、`worktree-dev-wave-t1851-unit-a` が
  `test_official_perf_closure.py` (`_REVIEWED_PERF_FILES` / `_REVIEWED_PREDICATES` /
  `_REVIEWED_GUARDS`)。前者は自分の編集帯 (6347 / 7081-7130 / 7273-7300 / 7805) と重ならない。
  後者は触らない方針で回避する。
