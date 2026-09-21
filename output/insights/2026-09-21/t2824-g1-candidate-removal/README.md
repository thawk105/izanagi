# [T-2824] 凍結 v2 g1 の未発効候補文書を削除し、held 真値を削除後の実測へ追随する (2026-09-21)

wave `dev-wave-t2824-g1-candidate-removal`、着手時 local main `5efd69367` (fresh worktree、開始 gate rc=0)。専用 handoff は repo 外
(`/work/1/SFC/tanab/dev-wave-jobs/handoff/2026-09-21-t2824-g1-candidate-removal.md`)、wave artifact dir は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2824-g1-candidate-removal/` (逐語・evidence・codex 成果物・変異台帳の原本、本 README の `verbatim/` `evidence/` `mutation/` はその写し)。
依頼の逐語は `verbatim/origin.md`、裁定の逐語は `verbatim/D2194-item5.md`、前提資料の逐語は `verbatim/t2810-insight-s5-s8.md`
(一次資料 `output/insights/2026-09-20/t2810-g1-launch-validation/README.md` の §5・§8)。

## 1. 入力と出所

| 対象 | 実体 | 出所 |
|---|---|---|
| 削除対象 | 未発効候補文書 (`output/s8b-freeze-candidates/` 配下の `holdout_freeze.v2.g1.json`、20,737 bytes、sha256 `7e1114…`、blob `15861416…`) | 現物 (base `5efd69367`) |
| 導入 commit | X2 `4d8fb93b7` (`record(s8b): freeze v2 g1 candidate を official 床値 result から生成する (未発効、保存 branch のみ)`、main の祖先) | `git log` |
| 同 bytes の保持先 | 世代文書 `output/s8b-freeze/holdout_freeze.v2.g1.json` (同一 blob `15861416…`、sha256 `7e1114…`) と X2 の履歴 blob | 現物 |
| held 真値 | `orchestrator/tests/test_s8b_oracle_driver.py` の `_ACTIVATED_G1_REFUSALS` (実 repo live P3 の拒否集合、exact 照合) | 現物 |
| 真値の consumer | driver 4 node + `test_s8b_binding_driftguards.py` 2 node = held 6 node (growth hold、受入全走では走らない) | `git grep -n _ACTIVATED_G1_REFUSALS` |
| 裁定 | D2194 項 5 (択 (a))、控え `rulings-inbox/2026-09-21-rulings-full27-verdicts.md` 項 5 | decisions / 控え |

## 2. 実施 (commit)

1. `58ec3e928` — 削除 commit。diff は候補 1 file の削除だけ (1 file changed, 1 deletion)。`--message-file` 検査 rc=0、直後の全史 provenance 監査は 12,262 件で新規違反 0。
2. `ce84ed8da` — held 真値の追随 (Codex author `gpt-6-astra` / `reasoning=medium`、`verbatim/s5-author.md`、1 file changed, 8 insertions, 6 deletions)。
   第 1 要素の hit 列挙が rr80 / rr20 とも 4 件 → 3 件 (候補 path が消えただけ)、第 2 要素 (live の policy 拒否) は byte 不変。直上 comment を削除後の実測へ更新。
   親も AST で定数を取り出し、実測 JSON の `refusals` と集合一致・候補 path の不在を検算した。

## 3. 実測 (login node、`evidence/`)

削除前 = base `5efd69367`、削除後 = `58ec3e928` (loader / reverify / launch_validate / P3 / 走査 CLI)。rc は親の実行ログの値 (gate-check の JSON 自体は rc を持たない)。

| # | 経路 | 削除前 | 削除後 | 差 |
|---|---|---|---|---|
| (e) | `load_ratified_freeze(root)` | 成功、世代 1、sha `7e1114…`、G `32ba8cae4` (12.6 s) | 同じ (11.7 s) | 不変 (`activation_head` だけが HEAD に追随) |
| (a) | `reverify_published_freeze` (historical、記録 contract、policy 照合なし) | `closure-hit-mismatch` (rr80 未申告 = 候補 path、94.2 s) | **成功 (`ReverifiedFreeze`、59.7 s)** | 段階 8 の未申告 hit が解消 |
| (b) | `launch_validate` (live、現行 policy) | `manifest-invalid` / `binary-admission` (0.23 s) | 同じ文字列 (0.31 s) | 不変 ([T-2812] 系、本 wave の scope 外) |
| (c) | runbook §2 P3 gate-check、g1 path | rc=2、`allowed: false`、拒否 2 件 | rc=2、`allowed: false`、拒否 2 件 | layer-2 hit が 4 件 → 3 件。他は byte 不変 |
| (c') | 同、v1 path | rc=2、既知 4 件 | rc=2、4 件 | 走査拒否 2 件の hit が 4 件 → 3 件。`floor-null` / `budget-null` は不変 |
| (f) | `s8b_holdout_freeze search` (repo 走査) | — | rc=1、rr80 / rr20 とも hit 3 件 (official run_dir の 3 file) | 走査除外は広げていないので clean scan は設計どおり赤のまま |

held checks 3 件 (`t080.live-*`) と両 path の stderr は削除前後で不変。**P3 の拒否内容の差は候補 path の除去 (hit 4→3) だけ**で、
削除前の拒否集合から候補 path を除き件数を 3 に直した集合は、削除後の実測集合と完全一致した (g1 / v1 とも、`evidence/` の JSON を機械比較)。
(a) の所要は login node の値で一般化しない。

## 4. 到達範囲と非保証

- 本 wave が示したのは **「未発効候補文書を削除した checkout で historical reverify (`reverify_published_freeze`) が成功すること」** までである。
  live `launch_validate` は現行 admission policy 照合で拒否のまま ([T-2812] 系)。P3 の全 gate 受理 (`allowed: true`) は未達。
- historical の成功は live admission の代替ではなく、certified 昇格・W-4 (spec 承認)・W-5 (実走)・床の採否を動かさない。certified 選択・レポート値・台帳・批准参照・live の受理条件はいずれも不変。
- production の**受理述語 (コード) は不変**である。変わったのは実入力 (repo tree) で、その結果として実 checkout の historical 判定が拒否から成功へ変わった (段 6 レビュー A の指摘を反映した書き分け)。
- 削除の根拠は「候補 path の役割が批准済み世代 (D2180) へ移って終わったこと」である (D2194 項 5)。**同 bytes であることは削除の許可ではなく来歴の保持の説明**であり、D2077 を削除許可としては引かない。
- 候補の bytes と来歴は、世代文書 (同一 blob `15861416…`) と X2 `4d8fb93b7` の履歴 blob で保持される。

## 5. 帰結 (裁定が記録を求めた項目)

1. **再生成で hit が復活しうる。** `V2_CANDIDATE_REL` の定数と create-only 書込み (`_write_v2_candidate_create_only`、`O_EXCL`) は残してある。削除で消えたのは
   「既存 leaf があるために存在拒否が発火する状態」だけで、create-only 規則そのものは不変。`generate-v2-candidate` を再実行すれば候補 path が復活し、
   repo 走査の hit と historical の `closure-hit-mismatch` も復活する (fail-closed の向き)。存在拒否が発火しなくなったことは生成全体の成功を保証しない (他の検証は不変)。
2. **held 真値の hit 列挙が変わる。** `_ACTIVATED_G1_REFUSALS` を削除後の実測へ追随した (`ce84ed8da`)。held 6 node は受入全走で走らないので、
   実走せずに真値だけ書き換えると F10 再発型 (pin 前進で参照が静かに腐る) になる。本 wave は実走して確かめた (§6)。
3. **候補 bytes と来歴の保持先**は §4 のとおり (世代文書と X2 の履歴 blob)。

## 6. 検査

| 走 | 対象 commit | 結果 |
|---|---|---|
| held 診断焦点走 (`focus/focus-held-1`、14653.nqsv、`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command`、hold 台帳は不変) | `ce84ed8da` | **6 passed** (93.3 s、job Elapse 99 s)。真値の 6 consumer が削除後の実 repo で緑 |
| 焦点走 (`focus/focus-impl-1`、14666.nqsv、`tools/run_tests.py --force-dispatch`、7 file = 変更 test + 真値 consumer + 候補 path / 実 repo 走査に触れる test) | `ce84ed8da` | **1262 passed / 13 skipped**、赤 0 (301 s、job Elapse 308 s) |
| 変異 probe (`mutation/mutation-spec-probe.json` sha256 `e140e562…`、独立 clone @`ce84ed8da`、計算ノード dispatch、全件 SURVIVED 登録で観測 node を集める) | `ce84ed8da` | baseline PASSED、M0 SURVIVED、M1 は held 6 node を赤にした (`MISMATCH` = probe 設計どおり)。原本 sha256 `887245b7…` |
| 変異 final (`mutation/mutation-spec-final.json` sha256 `1d6860be…`、probe の観測 node を完全集合として登録) | `ce84ed8da` | **baseline PASSED、M0 SURVIVED、M1 KILLED、期待 node 完全一致、MISMATCH 0** (`KILLED 1 / SURVIVED 1`)。原本 sha256 `a08e6a2d…` |
| provenance | `58ec3e928` | 全史監査 12,262 件、新規違反 0 (rc=0) |

**変異の数え方 (DW-M03 / DW-M08):** M1 (第 1 要素を削除前の値へ戻す) の KILLED は **diagnostic sensitivity pin として別枠**に数える。held 真値は production の
受理述語を変えない構造化シグナルの exact pin なので、受理集合の kill ではない。M1 が示すのは「更新後の真値が削除後の実 repo と実際に照合されていて恒真でないこと」
だけである。赤の理由が拒否集合の exact 照合 (`_assert_exact_refusals` の集合不一致、hit 3 件の実測 対 4 件の旧値) であることは probe の log で確認した。
production の受理述語を変える変更が本 wave に無いため、production 変異は登録していない (M0/M1 だけで production 全体の検出力を示したとは書かない)。

## 7. 段 3 / 段 6 所見と採否

段 2・3 は省略した (D2194 項 5 が択と不変条件を確定しており設計択一が無い。実装面は test 定数 1 個の追随)。段 6 は敵対レビュー 2 本 (`verbatim/s6-review-A.md`、`verbatim/s6-review-B.md`)、
裁定は `verbatim/s6-adjudication.md`。fix は 0 件 (実装面の所見なし) で、焦点再レビューは行っていない。

- レビュー B (過剰・削除 + 記録の限定): **GO**、must-fix 0。should 1 (runbook §2 P3 の「最新の一次資料」参照が削除前の値を指したままになる) を採用し、同表の参照先に本 insight §3 を足した。
  nit (成果物影響の補足) も採用 (§4)。
- レビュー A (正しさ境界・規律 2): 差分は GO、**held 実行の権限根拠の記録について NO-GO**。real と認め、記録で閉じた (§8)。should 2 件 (runbook の状態文、「受理集合」→「受理述語」の書き分け) と
  nit 1 件 (D 番号: 解除機構は D360、「ユーザー明示専用」の読みは D2125。段 4 裁定の文面では D2105 と誤記していた) を採用した。
  refuted とした懸念: 真値の弱体化なし (AST で取り出した定数が実測 JSON と bytes 集合一致、`_assert_exact_refusals` と 6 node の assertion は不変)、候補の tracked 存在に依存する取り残しなし、
  fixture 補助 3 箇所は合成候補を自分で作るので空振りしない、scan 除外・exact exemption・B-10 pin は不変、実測の過大な一般化なし。

## 8. held test を走らせた権限の根拠 (レビュー A の must-fix への処置)

held 6 node は `IZANAGI_RUN_GROWTH_HELD_TESTS` の exact token でしか走らない (D360 = 解除口を 1 本に限る決定。解除の主体は同決定に書かれておらず、
「ユーザー明示専用」という読みは D2125 の却下案に現れる)。本 wave が token を立てた根拠は次の 3 点である。

1. **依頼の逐語** (`verbatim/origin.md`、ユーザーの直接メッセージ) が「held 真値 `_ACTIVATED_G1_REFUSALS` を現在値に更新する」を名指しで指示している。
   held node は受入全走で走らないため、実走せずに真値を書き換えることは F10 の「再発: 2026-09-20」節が記録した失敗型そのものになる。同節は
   「policy epoch を動かす wave は held 真値の再実測を帰結に含める」と書いている。
2. **使用範囲を依頼が名指す真値の検証に限った**: held 6 node の診断焦点走 1 回と、変異 probe / final の走行だけ。hold 台帳・`growth_test_holds`・受入の既定・
   `conftest` の hold 登録はいずれも変えていない (diff で確認)。
3. **先例**: [T-2724] ax-delegated と [T-2810] が同じ 6 node を同じ token で実走し、land 済み。

## 9. 収録物

- `verbatim/`: 依頼逐語、裁定逐語 (D2194 項 5)、前提資料逐語 (T-2810 insight §5・§8)、段 1 brief、段 4 裁定、段 6 裁定、author 報告、レビュー A / B。
- `evidence/`: 削除前 (reverify-before、p3-before-g1、p3-before-v1)、削除後 (reverify-after-delete、p3-after-delete-g1、p3-after-delete-v1)。
  走査 CLI の出力 (§3 (f)) は **repo へ写していない** — 出力自体が holdout の値を含み、写すと新しい走査 hit を作って段階 8 の未申告 hit が別 file で復活するため
  (記録前の凍結 gate 走査で実測。原本は wave artifact dir の `evidence/search-after-delete.json`)。
- `mutation/`: spec (probe / final) と results の要約 (原本は wave artifact dir、sha256 で束縛)。
