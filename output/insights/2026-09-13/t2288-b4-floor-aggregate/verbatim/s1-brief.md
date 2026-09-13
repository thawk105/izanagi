# 段 1 brief — [T-2288] B-4 床値の集約規則を事前登録へ追補し、既存 floor pin へ渡す

**研究前進.** B-4 還流 ablation の材料レポートは、正規経路で分析 verdict を 1 種類 (`floor_domain_error` →
protocol violation) しか出せない。原因は事前登録 §5 の floor 欄が逐語 `未記入` であることだけである
(`p3_b4_material_report.py` は §5 を読み `resolve_preregistered_authoritative_floor` へ渡す配線が着地済み)。
D1855 は floor 欄を埋める 3 案がすべて既裁定に阻まれると確定し、D1936 項 7 が案 B を採った。案 B に
足りないのは「3 成果物の保守側最大を 1 件へ集約する規則が下流に無い」ことだけである。本 wave はその規則を
事前登録へ追補し、既存 issuer を N 入力へ拡張して 1 集約成果物を発行し、既存 pin/resolver が受理することを
示す。完了判定は (a) 追補が §5.1 の floor 項目に入り §5.1.1 の 2 pin が不変、(b) 3 summary から 1 集約成果物が
発行され既存 resolver が受理、(c) 集約規則の各条項を個別に倒す変異が対応 test だけを赤にする、(d) 受入全走 green。

**確定済みユーザー裁定.** D1936 項 7 (= D1855 案 B)。D1641 決定 3 (保守側の最大を取る対象集合 =
「凍結したセル集合 × 2 時間窓の全部」、統計関数 = 標本最大値を 95 パーセンタイル・信頼度 95% の片側許容限界、
成果物は create-only JSON、n = 62 は D1695)。D1383 (発効の権限はユーザー)。D1060 (既存値を根拠にしない)。

**着手前の実測で判明した新事実 (段 4 で確定させる).** 床値の**実測は本 wave では開始できない**。
凍結 spec は calibration を 1 件だけ束縛し cell ごとに `calibration.workload == perf.workload` を要求する
(`orchestrator/campaign/floor_pair_driver.py:1191`)。登録済み較正は `output/env/pegasus/calibration/registered/`
の 3 件で全て `ycsb_rratio=50` / threads=48。rr95・rr5 は 0 件。`floor-pair-spec/v3` の実体も repo に 0 件。
D1936 項 7 の理由文自身が「取得には項 6 の停止原因解消が先に要る」と書いている。よって本 wave の成果物は
規則と配線までとし、床値の値・§5 への記入・発効は行わない。

**scope (純増).** (S1) 事前登録 §5.1 の **floor 項目**への集約規則の追補 (docs、親が書く)。
(S2) `p3_b4_floor_artifact_issuer.py` を「N 個の floor-pair summary → 1 集約成果物」へ拡張 (実装面)。
(S3) `load_authoritative_floor` / `resolve_preregistered_authoritative_floor` が集約成果物を受理 (実装面)。
(S4) 正例・負例テスト (実装面)。**scope 外**: 較正取得、床値の実測、§5 値セルの記入、別の集約基盤、
汎用 multi-calibration schema、workload 一致要求の撤去 (D1854 で不採用)、仮想リスク向けの gate・台帳・一般化。

**(P1) 親の provisional 裁定 (攻撃対象).** 「対象集合が結果を見る前に閉じている」ことの機械検査は、
集約器が **caller から明示の期待閉包 (3 spec の相対 path と sha256、および window_id の集合) を受け取り、
入力 summary 群から導いた実閉包と exact 一致を要求する**形で行う。過不足・重複・欠落はすべて fail-closed。
理由: cell 集合は spec の中にあるので spec を pin すれば閉じる。窓は各 summary の `window_artifacts` /
`campaigns` にある。新しい台帳も manifest 形式も増やさずに済む。**この形が適切かを段 2・3 は攻撃してよい。**

**不変条件 (規律 2 を緩めない).** 集約は保守側 = **最大**であり、平均・中央値・最小を採らない。
exact 比較は `Fraction` で行い binary64 の丸めで下振れさせない。値域は `0 <= floor < 1` で、1 以上は丸めず
`floor_domain_error` 相当で拒否する (§11.2「値域」)。env_tag / protocol / threads は全入力で一致を要求し、
workload と campaign は和を取る。create-only を維持し既存成果物の上書き・削除・改名をしない。
各 summary の `proof_limitations` と既存 `non_guarantees` は 1 件も落とさず持ち越す。
**事前登録 §5.1.1 の raw sha256 と semantic sha256 を変えない** — 同節の pin 範囲は「§5.1.1 の見出しから
次の level<=4 見出し (= §6) まで」なので、§5.1 の**末尾**への追記は凍結バイトを壊す。追補は §5.1 の
floor 項目 (現行 228 行目付近、§5.1.0 より前) に置く。追補は §5.1 の解除条件を 1 つも緩めず、
記入の権限も実走の許可も与えないことを本文に明記する。

**変更面のアンカー.**

| path | anchor | 変更 |
|---|---|---|
| `docs/phase3-b4-reflux-ablation-preregistration.md` | 228 行 `- **floor**:` 項目の末尾 | 追補を追加 (親) |
| `orchestrator/campaign/p3_b4_floor_artifact_issuer.py` | `issue_authoritative_floor` (994)、`_authority_value` (901)、`_artifact_filename` (931)、`load_authoritative_floor` (1039)、`B4_FLOOR_ARTIFACT_SCHEMA_VERSION` (36) | 集約発行と受理 |
| `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` | 全体 | 正例・負例 |
| `orchestrator/tests/test_p3_b4_material_report.py` | 963 行 resolver 呼び出し | 波及確認 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 新規 nodeid | 台帳追加 |

**成果物の形.** 集約成果物は既存 issuer が書く create-only JSON 1 件。`docs/spool/` 断片、
`output/insights/2026-09-13/t2288-b4-floor-aggregate/` に逐語・変異台帳。床値の数値は載せない。

**並列分割.** 段 2 = plan 1 本。段 3 = 敵対 2 レンズ (sol: 正しさ境界と保守性、luna: 凍結・受理集合・
既存 consumer への波及)。段 5 = 実装子 1 単位 (issuer + test は所有が一枚岩)。段 6 = review 2 本 + fix。
**受入・実測環境**: login node の受入全走のみ。計算ノード job は投入しない (実測が scope 外のため)。
