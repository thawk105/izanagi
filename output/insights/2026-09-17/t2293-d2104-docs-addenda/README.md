# [T-2293] [T-2687] [T-2688] [T-2692] D2104 項 3 / 21 / 22 / 30 の追記・手順改訂 — D1875 と D922 の追補 D、rc 表の indeterminate、DW-O18 から hold 登録の一般手順を取り下げて check_docs の pin を追随した (2026-09-17)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。

wave: `dev-wave-t2293-d2104-docs-addenda` (branch `worktree-dev-wave-t2293-d2104-docs-addenda`)。起点 main `38353207f`。
commit 列: 統合 `76aad5e4c` (docs 4 箇所 + fragment 2 本、親; `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py`、Codex author) →
記録 commit (本 README、worklog fragment、decisions fragment の nit 訂正、親)。

## 何を閉じたか (ユーザー裁定 D2104、「推奨通りで」)

| 項 | T | 実施 | 所在 |
|---|---|---|---|
| 3 | T-2293 | D1875 の「D114 が定めた承認済み generation 予算 1」を D410 (2026-08-15) の 2 (実装 `MAX_APPROVED_GENERATIONS = 2`) と訂正する追補 D。T-2293 の Q2〜Q4 の保留は維持、一括承認はしない | `docs/spool/decisions/…-1.md` の 1 本目 (land 時採番) |
| 21 | T-2687 | D922 点 4 の「打ち切りを `indeterminate` へ倒す」対象を候補探索の上限超過について限定し、照合済みの正証拠で確定した `landed` は維持する追補 D。timeout・parse 不能・shallow・履歴書き換え・ref 移動は変えない。実装不変 | 同 fragment の 2 本目 |
| 22 | T-2688 | `docs/unreachable-object-ledger.md` rc 表 `2` 行へ「landed 判定に `indeterminate` が 1 件でもある場合を含む (D1231)」 | 直接編集 (pin 対象外) |
| 30 | T-2692 | `DW-O18` から hold 登録の一般手順 3 文を取り下げ (997 → 995 bytes、`verbatim/dw-o18-{before,after}.md`)、`tools/check_docs.py` の逐語 pin と契約 test を追随。F1000 の恒久対応確定を supersede 追記 | `docs/dev-wave/operations.md`、`tools/check_docs.py:605`、`orchestrator/tests/test_check_docs.py` (`:166` fixture、`:9484` byte assert 997→995、`:9582` / `:9639` needle M2 / M11)、`docs/spool/failures/…-2.md` |

## 引数の前提を覆した新事実 (段 1 実測)

「docs のみ」で処理できるのは (a)(b)(c) だけだった。`DW-O18` は `tools/check_docs.py` の `DEV_WAVE_DW_O18_SECTION_LITERAL` に
節全体が逐語 pin され (`DEV_WAVE_EXACT_VISIBLE_SECTIONS`)、`orchestrator/tests/test_check_docs.py` の独立な合成 fixture・byte 固定
assert・変異 case M2 / M11 の needle が旧文言に依存する。docs だけを当てた状態の `check_docs.py` は
「可視 H2 節 'DW-O18 — …' の節全体が exact 契約と不一致 — sections=1」の 1 件で赤 (段 1 で impl worktree にて実測)。
pin 追随 2 file を Codex author に限定して書かせ (D95)、実装 (`check_branch_landed.py` / `check_branch_rescue.py` /
`flaky_test_holds.py`) には触れていない。

## DW-O18 の改訂 (取り下げた 3 文と足した 3 文)

| 取り下げ | 置き換え |
|---|---|
| 再赤/決定的赤はmain既存Fを証拠にCodex`role=author`が`orchestrator/tests/flaky_test_holds.py`へ登録(field正本=同file)。 | 再赤/決定的赤でもhold登録簿へ登録しない(契約testが1件に固定、F1000)。 |
| F不在は登録せず裁定送り、 | 真に決定的な不安定testはその1件のpin更新を個別に諮り、 |
| 停止条件外は治すかhold登録後だけ投げ直しwaveを止めない。 | 停止条件外は治すか上記の制限内で投げ直しwaveを止めない。 |

見出し・他の安全義務 (判定主体の境界、5 分超禁止、単独再走→受入再走、同一 tip で各 1 回、判定不能・原因未理解は停止、
受理は `child-green` だけ) は逐語で不変 (段 3 相談 §1・段 6 レビュー B §5 が照合)。「上記の制限内で」は直前の
「同一tipで各1回だけ」を指し、再投入枠を増やさない (段 3 相談の提案を採用)。

## 段 3 相談 (1 本、luna / medium)

real 2 / refuted 5 (`verbatim/s3-consult.md`)。
- R1 (must-fix): D922 追補の起草が「候補上限や期限へ達しても」と書き、deadline にまで正判定優先を一般化していた。実装は
  deadline を `AssessmentError` で raise し (`check_branch_landed.py:215`, `:241`, `:750`)、assessment 全体を `indeterminate` に
  する (`:1989`, `:2002`)。候補上限超過だけ (`:784` のコメントどおり正証拠照合が上限報告に先行) に射程を限定した。
- R2 (must-fix): `test_check_docs.py:9484` の byte 固定 assert 997 の追随が brief の編集箇所表から漏れていた (author prompt には
  含めてあった)。
- refuted: 安全義務の弱化 (F1)、個別 pin 相談が F1000 の防壁を破る (F2)、byte・最長行 (F3: DW-O18 に最長行上限は無い
  `check_docs.py:5983`, `:6022`)、D1875 追補の事実誤り (F4)、rc 表追記の誤り (F5)。

## 段 6 レビュー (2 本、medium)

- **B (docs 忠実性、accepted):** GO、must-fix 0、nit 1 — D1875 の残り 3 件 (fixture provider / `--no-build` / 世代制約) と
  T-2293 の Q2〜Q4 (production FSM / 起点専用 entry point / completion・report の起点分岐、archive 1566) を同一視した
  説明 → fragment を訂正 (記録 commit)。
- **A (pin 追随、reviewA-2 accepted):** GO、must-fix 0、nit 1 — author 報告の「check_docs 不一致 1 件」は統合前 (docs 未適用)
  の author 環境の結果であり、統合後は 0 件 (本 README で区別)。reviewA-1 は 2 attempt とも `event_invalid` で不受理
  (子が `cat -n orchestrator/tests/test_check_docs.py` 12,857 行を全文出力し launcher の証拠検査が壊れた型)。未受理版
  (`verbatim/s6-reviewA-unaccepted-attempt1.md`、データとして保存) の nit「各 1 回 → 各 2 回」の負例は、probe 前に M4 として
  登録した。fix 子は起動していない。

## 実走 (親)

- 焦点走 7 file (`test_check_docs` + importer 3 + `test_dev_waves_checker` + `test_growth_test_holds_contract` + `test_hold_inventory`、
  計算ノード 3992.nqsv、`verbatim/focus-1-run_tests.log`): 1245 passed / 8 skipped / 42.28 s (skipped は growth hold、D753)。
- `check_docs.py` 違反なし (統合後)。`spool_fold.py --dry-run` rc=0 (暫定採番 D2120 / D2121、land 時に確定)。
- 全史 provenance (統合 commit 後): 11,076 件・新規違反なし。三軸語・placeholder 走査 (`s8b_holdout_freeze search`) rc=0。
- 受入全走: 記録 commit 後の最終 tip に land 前に 1 回投げる (結果は land の受領証。本 README 記録時点では未実施)。

## 変異 matrix

container worktree `.codex/worktrees/t2293-addenda-mutcontainer` (detached 76aad5e4c)、`tools/mutation_harness.py` を直接使用
(`--runner-mode dispatch --detached`、runner `run_tests.py orchestrator/tests/test_check_docs.py -q -rf --force-dispatch -p no:cacheprovider`、
計算ノード dispatch)。対象は `tools/check_docs.py` の DW-O18 literal だけ (fixture・docs は固定)。probe (全件 SURVIVED 登録、
`mutation-ledger-probe.json`) で観測 node を集め、本走 (`mutation-spec-final.json` sha256 `d71e8a8c…`、`mutation-ledger-final.json`) は
**baseline PASSED (32.4 s)、負例 4 件すべて KILLED で期待 node と観測 node が完全一致 (matching 5/5)、等価 M0 SURVIVED、MISMATCH 0、
TIMEOUT 0、全 anchor 1 箇所**。各変異の失敗 node 数は job stdout の `IZANAGI_FAILURE_DIGEST_ACCOUNT failures=` と一致 (中継上限の
欠落なし)。

| ID | 変異 (literal 内) | 観測 node | 専属性 |
|---|---|---|---|
| M0 | 「同一tipで各1回だけ。」直後で `""" """` により隣接 2 文字列へ分割 (評価値同一) | 0 (SURVIVED) | 等価対照 |
| M1 | 「hold登録簿へ登録しない(」→「登録する(」 | 329 | 過剰決定 (合成 fixture の baseline が全 positive control で崩れる)。`test_dw_o18_exact_section_pin_accepts_synthetic_fixture`・`test_normative_exact_section_contract_is_handwritten_and_complete` を含む |
| M2 | 「真に決定的な不安定testはその1件のpin更新を個別に諮り、」を削除 | 330 | 329 + `test_non_attributable_landing_contract_mutations_have_one_finding[M2]` (専属) |
| M3 | 「停止条件外は治すか上記の制限内で投げ直しwaveを止めない。」を削除 | 330 | 329 + 同 `[M11]` (専属) |
| M4 | 「同一tipで各1回だけ。」→「各2回だけ。」 (段 6 レビュー A の nit、probe 前に登録) | 329 | M1 と同じ共通集合 (回数制限の改変を独立 fixture が検出) |

M2 / M3 の +1 は、docs 側 (合成 operations) から同じ句を削る case が変異済み literal と一致して期待 finding を失うためで、
段 3 相談 §6・段 6 レビュー A §4 の静的予測と一致した。

## scope 外で残る (記録のみ)

- T-2293 の Q2〜Q4 (D1875 の残り 3 件と同じ整合待ち): 還流設計 (D106 残余 1) が未解決のまま。本 wave は保留を解かない。
- `check_branch_landed.py` の deadline 経路 (走行全体を `indeterminate`) は追補で「変えない」と明記しただけで、挙動の妥当性は
  本 wave の主題ではない。
- 段 8 候補 (docs 予算に入らず記録のみ): 相談・レビュー子への「巨大 file の全文 cat 禁止」、authority docs の未 commit 差分が
  codex 起動を止める事実。どちらも既存 memory にあり、本 wave では L1.5 予算 (満杯) へ足していない。

## 逐語

`verbatim/` に brief、相談、裁定、author 報告、レビュー 2 本 (+ 未受理 attempt 1)、DW-O18 の改訂前後、焦点走 log。
`mutation-spec-{probe,final}.json` / `mutation-ledger-{probe,final}.json` は harness の入力と出力そのまま。
