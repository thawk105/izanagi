# 段 4 裁定 — K2 手動 loop 第 3 巡 (2026-09-19 22:12 JST)

裁定 inbox 再走査: wave 開始後の新規 2 件 (`2026-09-19-b7-fixed5-three-workload-regression-authorization.md`、
`2026-09-19-t2778-child-worktree-manifest-cleanup.md`) は本 wave に無関係。main は docs-only で `a99425b66` → `657e1e5a7`
(t2489 insight + fold)。記録 commit 前に取り込む。submit-tree は着手時 SHA `a99425b66` で切る (計測 code に差分なし、B#4)。

## 所見の裁定 (real / refuted、採否)

| # | 所見 | 判定 | 採否・処置 |
|---|---|---|---|
| A#1 | 診断に行動誘導 (avoid、最優先 R0、候補 10/1) がある。助言≠義務を prompt でも明示 | real / should | 採用。prompt tail に「採用義務・値の禁止・実行予算の追加を意味しない」を明示 (既に含む文を補強) |
| A#2 | 防壁が role 本文と親説明だけ、という評価は不正確 | refuted | 機械側 (exact 6 field / boundary / 適用条件 / loader の申告拒否) を記録に併記。型検査通過を「指示混入なし」の証明にしない |
| A#3 | 診断経由で 20・25 が見えるのは漏れではない (D2155 の設計) | refuted (漏れではない) | 採用: 「許可された診断兄弟 key での開示」と記録。「既知値を見ずに合成した」とは書かない |
| A#4 | 入力防壁の説明を K2 診断の開示で限定せよ | **real / must-fix** | 採用。brief 不変条件 3 を「whiteboard・通常射影へ勝ち筋値を足さない。D2155 の診断には既知値 (20/25 と tps) と機序候補が含まれる」に訂正。coder-4 は coder-3 と違い 20/25 の評価済みを知る、と主張限定に書く |
| A#5 | 規律 2 (anomaly 救済・再投入) の懸念 | refuted | 手順は既存契約 (`run_campaign` → `pipeline.evaluate`、trace/perf 別 build) を触らない。実走前の確認であり結果の保証ではない |
| A#6 / B#13 | P1 (stock 未実走) は原依頼の縮小。完了条件に置き換えない | **real / must-fix** | 採用。**本 wave は「候補生成 1 回 + 候補のみの評価 1 本」の縮小走行**とし、同 job stock 対照は**未達**として insight・worklog・rulings-inbox に明記。「認可された第 3 巡の完了」とは書かない。裁定パッケージ (下) へ |
| A#7 | N1 の「必ず新 launcher」「他 job では pin も揃えられない」は探索結果より強い | real / should | 採用。記録は「既存 S4 口に stock 結線なし。確認した代替 (A1 paired / B10 grid / floor / T-1998 stock-inline / guided `--genome`) は不適合。全手順の不在証明ではない」に限定 |
| A#8 | P2 / P6 は整合 | refuted | P2: 20 → 投入なし、25/30/40 → 既知値と記録して 1 評価。P6: certified ∧ continue で critic-3 ≤ 1 (親の追加制限、ユーザー逐語の明示認可とは書かない、B#10) |
| A#9 | N2 は現物と一致 | refuted | fresh tree + 新 checkpoint で進む。ID 同一 ≠ 走行同一を明記 |
| A#10 / B#14 | N3 は既出 (round 1 README §射影) で新型ではない。site 分類は hostname + NQSV 証拠。`898f567f` は OTHER 契約で束縛した cfg の計算値 | real / should | 採用。failures fragment は作らない。runbook 追補の CLI 記述との食い違いは本 wave の変更面に含めず、裁定パッケージ候補 (docs 追記 1 文) として返す。記述を「PEGASUS_LOGIN 分類で admission 拒否 (round 1 と同じ)」に訂正 |
| A#11 / B#8 | probe の「同 bytes」「緑」の範囲、組立て script の照合不足 | real / should | 採用済み: `build_round3_inputs.py` を plan どおり受領証正準 bytes 全体・identity preimage 全体・knowledge 射影 bytes・tripwire の照合に更新して実走 (22:06、全緑)。記録は実際に照合した範囲に限定 |
| A#12 | 送付・採用申告・効果の区別 | refuted (plan 妥当) | 記録規則として採用 (下「主張限定」) |
| B#1〜B#7 | staging / preflight / identity / harness 差 / 20 分岐 AO / 取込み検査 / 件数 | refuted | plan どおり。B#5: 20 分岐は AO 取込み・材料レポートなし (C2 へ追記しない)。B#6: 取込みは rc を個別確認、旧 ref / 旧 digest を写さない。B#7: 正常分岐 source_refs = N+1+3 (WAL 5 なら 9) |
| B#9 | critic-3 に過去 2 走 (round 1 tree d97c423bd / round 2 tree d2ebef7a4、同 ID 別 tree) を開示 | real / should | 採用。critic-input-3 の parent_disclosures に 2 走を明記 (全履歴の網羅宣言にはしない) |
| B#10 | critic は Bash を持ち B-4 非適格 | refuted (既知) | 記録に残す |
| B#11 | critic prompt 全文の保存手順が欠ける | **real / must-fix** | 採用。critic-3 の prompt 全文を `materials/critic-prompt-3.md` に固定してから起動し、取込みで `--agent-prompt` を付ける |
| B#12 / B#15 | 証拠一覧・正規化の複写、過剰/欠落 | refuted | 一次資料一覧は B#12 の列挙を採用。正規化は必要時のみ、原文 SHA を残す |

## plan v2 (実行手順の確定)

1. **入力 (済):** `build_round3_inputs.py` (22:06 実走) の出力を使う。`planner-input-4.json` (sha 87a7fb53…) を prompt (head + JSON 逐語 + tail) にして `planner-v4` へ inline 送付。出力逐語を `verbatim/planner-4.json` に保存。
2. **coder-4:** `coder-input-4-skeleton.json` の `planner_direction` を planner-4 の proposal から 4 key (axis / direction / magnitude / justification) で射影して `coder-input-4.json` に保存 (tripwire 再検査)。prompt (head + JSON + tail) を `coder-v4-autonomous-k2` へ inline 送付。出力逐語を `verbatim/coder-4.json` に保存。
3. **proposal-4:** `{planner: proposal, coder: envelope, prior_critic_reverse: false}`。検査 3 本 (schema K2 / 文法 preflight は accepted を assert / loader with knowledge_input + coder_role)。既知値判定 (20 / 25 / 30 / 40)。
4. **分岐:** value=20 → job 投入なし、AO 取込みなし、材料レポートなし、記録のみ。それ以外 → 5 へ。範囲外・不正出力 → 拒否として保存、再生成しない。
5. **submit-tree:** `setup-submit-tree.sh` (a99425b66、job root 直下、submodule 再帰、hydrate 既定 staging)。rc と `submodule status --recursive` の先頭記号を実測。clean 0 行・HEAD・pin を確認。
6. **投入 1 本:** `qsub-submit.sh` (README §7 の 9 変数、`KNOWLEDGE_CLASSIFICATION` は coder-4 の自己申告値、`DE_NOVO_CLAIM=false`)。attempt dir は mkdir のみ。qstat 写しは job root 直下。待ち手は `evidence/attempt-0001/compute-result.json` の出現 1 本。preflight 拒否・失敗でも再投入しない。
7. **走行後:** WAL / loop_state / digest / receipt を読み、verdict・anomalies・median_tps・停止判定を記録。anomaly ≥ 1 → reject として記録 (救済なし)。
8. **AO 取込み (certified 時):** 新 WAL から `wal-refs.json` を再計算。planner-4 → coder-4 (variant = 本走 variant、`--agent-prompt` 付き)。各 rc を個別確認。
9. **critic-3 (certified ∧ continue 時、≤ 1 回):** `critic-input-3.json` (round 2 形 + 本走実測 + 2 走の開示 + stock 対照なし) と `critic-prompt-3.md` を固定 → `critic` へ送付 → `verbatim/critic-3.md` 保存 → 取込み (`--agent-digest` は C3 の digest、`--agent-prompt` 付き)。
10. **材料レポート:** `layer3_report.py <C3> layer3_report.json --output-root <submit-tree>/output --generated-from-head a99425b66…`。期待 source_refs = N+1+AO 件数。
11. **記録:** insight `output/insights/2026-09-19/k2-loop-round3/`、spool worklog fragment 1 本 (failures / decisions なし)、rulings-inbox に裁定パッケージ 1 本。main `657e1e5a7` 取り込み後に記録 commit。
12. **変異 matrix:** 実装面差分ゼロ → 免除 (DW-S04)。**受入全走:** 実施。段 6: read-only review 1 本 (insight の事実照合)。

## 裁定パッケージ候補 (本 wave は判定しない)

1. **同 job の stock 対照 (未達)。** 既存 S4 口 (`p3_s4_loop_pegasus.sh` = driver 1 起動、`p3_s4_loop.py` の value 1..1000) に stock 結線がなく、確認した代替も不適合。択 (i) 同 job pair launcher を別 wave で実装 (plan 項 6 の設計メモ: job body の stock step、driver の stock genome 評価口、pipeline 自身が発行する stock WAL、identity への影響) してから候補 + stock の pair を再投入 (候補の再評価を含む認可が要る)、択 (ii) 本 wave の候補のみ評価を縮小走行として受理し stock は別途、択 (iii) 元の pair 要求を維持し手順と scope を別途確定。
2. **runbook T-2783 追補の手順 1 (CLI emit) は login では走らない** (round 1 と同じ制約)。追補に「login では production 関数直呼び (round 1/3 の形)」の 1 文を足すか (docs 追記のみ)。
3. (round 2 から持ち越し) attempt-0002 の事後承認、層 3 v1 reader、fresh 比較 consumer — 本 wave では触れない。

## 主張限定 (記録規則)

- 「送付した」= 保存した完全入力 JSON と実 prompt の対応 (SHA)。AO の `input_sha256` や診断の `source_sha256` を実受領の証明にしない。
- 「採った」= 出力中の参照・提案内容との一致・自己申告 (`knowledge_use` / `classification` / `data_boundary_report`) をそれぞれ記録。候補 10 と一致しても診断が原因とは書かない。
- 「効いた」= 診断なし統制が無いので主張しない。
- coder-4 は診断経由で 20/25 の評価済みと tps・機序候補を知る (coder-3 は知らなかった)。「既知値を見ずに合成」とは書かない。
- 同 job stock 対照は未実走。同時刻対照なし。非同時刻値 (round 1 719324.5 / round 2 687508.5) を対照にしない。`delta_pct=null`、success = certified。
- 改善の実証・新 CC 構造・候補間 certified 選択・K2 因果・B-4 適格を主張しない。
