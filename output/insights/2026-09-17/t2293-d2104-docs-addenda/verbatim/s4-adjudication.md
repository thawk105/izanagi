# 段 4 裁定 (2026-09-17 21:55 JST、親)

段 3 consult 1 本 (luna / medium、`s3-consult.md`、check_codex_output rc=0) の所見と親 brief P1-1〜P1-4 を裁定する。
裁定 inbox の再走査: `docs/decisions.md` の末尾 D は D2119 で、D2104 項 3 / 21 / 22 / 30 を覆す新裁定は無い (wave 開始後の main 前進は 0 commit)。

## 所見の裁定

| # | 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|---|
| R1 | D922 追補が「候補上限や期限」と書き、期限 (deadline / timeout) にまで正判定優先を一般化している。実装は timeout を `AssessmentError` で raise し assessment 全体を `indeterminate` にする (`check_branch_landed.py:215`, `:241`, `:750`, `:1989`) | **real** | 採用 (must-fix) | 追補を「候補探索の上限超過」だけに限定し、timeout・parse 不能・shallow・履歴書き換え・ref 移動の扱いは変えないと明記。見出し・却下欄も同じ射程へ揃える |
| R2 | `test_check_docs.py:9484` の `len(_SYNTHETIC_DW_O18_SECTION) == 997` の追随が brief の編集箇所表に無い | **real** | 採用 (must-fix) | author prompt に既に含めてあった (brief 表の漏れ)。新値は 995 |
| F1 | DW-O18 の他の安全義務が弱まる | refuted | — | 逐語照合で残存を確認 (consult §1)。ただし「投げ直し」の制限を明示する「上記の制限内で」は採用 |
| F2 | 個別 pin 相談が F1000 の防壁を破る | refuted | — | F1000 が禁じるのは wave 自身による除外集合の拡大。ユーザー裁定による個別相談は禁じていない |
| F3 | byte・最長行の制約違反 | refuted | — | 995 bytes ≤ 1000 (`check_docs.py:360`)。DW-O18 に最長行上限は無い (`:5983`, `:6022`) |
| F4 | D1875 追補の事実誤り・保留解除 | refuted | — | 3 点とも現物一致。「T-2293 の Q2〜Q4 (D2104 項 3)」と参照を明示する訂正は採用 |
| F5 | rc 表追記の誤り | refuted | — | 経路 4 段を確認。文言は consult 案「landed 判定に `indeterminate` が 1 件でもある場合を含む (D1231)」を採用 |

## P1 の確定

- P1-1 (DW-O18 案文): **v2 を確定** (`wave/dw-o18-new.md`、995 bytes、見出し不変)。裁定の逐語「その 1 件の pin 更新を個別に諮る」へ寄せ、「上記の制限内で」を足した。削減は 997 → 995。
- P1-2 (変異): 採用。対象は `tools/check_docs.py` の literal だけ (fixture・docs は固定)。事前登録は下記。
- P1-3 (rc 表): 採用 (consult の文言)。
- P1-4 (段 2 省略): 採用。consult が「dispatcher の手続規則上の可否は未認定」と留保したが、`DW-C00` は「該当なしだけ既定の軽量版とし、段 2・3 と段 6 の review 子を省ける」と定め、本 wave は段 3 と段 6 を残しつつ段 2 だけを省く形で、省略可能な集合の部分集合である。

## scope 判断

- F1000 の supersede 追記 1 行: **採用 (scope 内)**。新しい恒久対応の設計ではなく、F1000 自身が「裁定パッケージへ送る」とした選択が D2104 項 30 で確定したことの記録。「施工完了」は書かず、方針確定と本 wave の改訂 (DW-O18) を分けて書く。
- 新しい gate・検査・台帳: 無し。実装 (`check_branch_landed.py` / `check_branch_rescue.py` / `flaky_test_holds.py`) は不変。

## 実装単位

- 単位 1 (Codex author、worktree `.codex/worktrees/t2293-addenda-impl`): `tools/check_docs.py` の `DEV_WAVE_DW_O18_SECTION_LITERAL`、`orchestrator/tests/test_check_docs.py` の `_SYNTHETIC_DW_O18_SECTION` / byte assert 997→995 / M2・M11 needle 再照準。
- 親: `docs/dev-wave/operations.md` DW-O18 (適用済み、両 worktree)、`docs/unreachable-object-ledger.md` rc 表、spool fragment 3 本 (decisions D 2 本 / worklog / failures supersede)。

## 変異の事前登録 (DW-M01、対象 `tools/check_docs.py` の literal だけ、runner `run_tests.py orchestrator/tests/test_check_docs.py -q -rf --force-dispatch -p no:cacheprovider`)

| ID | category | 置換 (old → new、literal 内) | 期待 | 単一理由 |
|---|---|---|---|---|
| M0 | positive (等価) | literal を隣接 2 文字列へ分割 (`…同一tipで各1回だけ。` の直後で `"` `"` を入れる、評価値は同一) | SURVIVED | 値不変 |
| M1 | negative | `再赤/決定的赤でもhold登録簿へ登録しない(` → `再赤/決定的赤でもhold登録簿へ登録する(` (登録禁止の反転) | KILLED | literal ≠ fixture → exact pin 不一致 |
| M2 | negative | `真に決定的な不安定testはその1件のpin更新を個別に諮り、` を削除 | KILLED | 同上 + M2 case の期待 finding 消失 |
| M3 | negative | `停止条件外は治すか上記の制限内で投げ直しwaveを止めない。` を削除 | KILLED | 同上 + M11 case |
| M4 | negative | `同一tipで各1回だけ。` → `同一tipで各2回だけ。` (段 6 レビュー A の nit N1 を採用、probe 前に登録) | KILLED | literal ≠ fixture → exact pin 不一致 (回数制限の改変を直接狙う) |

期待 node は probe (全件 SURVIVED 登録) で観測して本走へ登録する (DW-M07)。M1〜M3 の killer 候補 (静的予測、consult §6):
`test_normative_exact_section_contract_is_handwritten_and_complete`、`test_dw_o18_exact_section_pin_accepts_synthetic_fixture`、
`test_non_attributable_landing_contract_mutations_have_one_finding[M2|M11|…]`、および合成 repo を baseline とする正例群。

## 次段

段 5: midflight gate → author 投入 (`--max-model-calls 400`、reasoning 指定なし)。段 6: review 1 本 (レンズ: pin 追随の完全性と scope 逸脱) → fix (要れば) → 焦点走 (login) → 変異 probe/final → 段 7。
