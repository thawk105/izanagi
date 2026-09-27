# 段 6 裁定 1 — [T-2867] (2026-09-27 15:0x JST、親)

入力: レビュー A (`codex/review-a.md`、判定規則・公平性・規律 2、15:01 完了 rc=0)、レビュー B (`codex/review-b.md`、過剰・事実照合、15:01 完了 rc=0)、親の自己点検 2 件。
対象: commit `4e1d79a25`。

| # | 所見 | 裁定 | 直し方 |
|---|---|---|---|
| A1 | 初期点の性能が LLM の初回入力に届かない | real・must-fix。実コード確認: `make_policy_coder_input` の自系列履歴 (p3_s4_loop_policy.py:283-285) には throughput が無く、性能は critic 診断を通してしか coder に届かない | critic を job 1 の後 (初期点と stock) にも回すと §4.1 に固定。初期点を系列の campaign の履歴と critic digest に載せることを §10 の前提に追加。性能が critic 経由でだけ届くことを LLM 構成の開示に追加 |
| A2 | 後発 anomaly の score 訂正が未定義 | real・must-fix | §6 に「その系列を不採用とし §6 の fallback へ訂正、日付付きの結果の訂正」を明記 (B-5 v1 §6 と同じ) |
| A3 | D2214 項 8 の公平性の目視が落ちている | real・must-fix | §6 の後に目視 (全系列の endpoint と勝ち候補、score 確定後・報告前、所見は併記、score と判定は変えない) を置く |
| A4 | 「同じ評価数」が停止規則より強い | real・must-fix | §1.1 を「評価数の上限 B = 10」にし、実消費 B の報告と B 未達系列の併記を §7.4 報告に足す |
| A5 | 進化の field 追加で next_state の拡張が一意でない | real・must-fix | 明示の next_state には新 field の自己参照を末尾に足し、省略の hook は省略のまま、と固定 |
| B1 | `select_endpoint` の同値規則を流用可と過大評価 | real・must-fix。`b5_generator_contrast.py:454` は (fitness 降順, value, b) | §10 と insight §2 で「同値規則は本書と違うので流用しない」と訂正 |
| B2 | n = 10 案で report の系列数が固定 12 | real・must-fix | §11.3 の n = 10 の行に「report の系列数 (`pair_differences` は 1..12 固定) も変える」を追記 |
| B3 | 「律速は週上限」と断定 | real・must-fix | 「律速になりうる」に改め、57 機会 / 週は 429 までの使用量を枠と仮置きした試算と書く |
| B4 | 3.0〜6.1 h の引用が 1 機会の実測範囲と合わない | real・must-fix | insight §3 を「1 機会 255〜1,021 s の 24 倍 = 1.7〜6.8 h (v2 準備の insight は 3.0〜6.1 h と記すが計算根拠が合わない)」に訂正 |
| B5 | job 準備費の出所表示 | real・nit | 「単価は実測、12 job 分は換算」に分ける |
| B6 | §8・§9・§13・§14 の縮小 | refuted (削除しない)。§8 の既知結果の開示は HARKing 境界として事前登録に要る (B-5 v1 §8 と同じ慣行)。§9・§13 は発効後の報告を縛る規則で、重複を削ると根拠の位置が散る | 変更なし |
| A6・A7・B7 | 算術・規律 2 の読み | refuted (両レビューとも誤りなしと確認) | なし |
| S1 (親) | §7.4 の生成不成立が初期点を endpoint に含めるとほぼ発火しない | real・must-fix | 生成不成立を「certified・品質正常の探索点を 1 つ以上持つ系列の数」が 6 未満と定義し直す。endpoint が初期点だった系列数は従来どおり報告 |
| S2 (親) | critic を初期点の後に回すか未定 | real (A1 と同根) | A1 で固定 |

- 規模の択一 (4 arm / 3 arm / n = 10) は草稿 §11.3 のまま、発効の確認でユーザーが選ぶ。
- 直した後に焦点再レビュー 1 本 (DW-S06-C、DW-O16 の対応表つき) を当てる。
