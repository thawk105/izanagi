# 段 6 裁定 — レビュー A / B の所見

## real (採用)

| # | 出所 | 所見 | 対応 | 担当 |
|---|---|---|---|---|
| R1 | A must-fix 1 | panel 内注記 `L >= 0.299` は四捨五入で偽 (balanced の min L = 0.29889、read-heavy 0.27379 → `0.274`)。裁定 §2.3 自身の指定誤り | `_direct_label` を `min L = <小数 3 桁>` (不等式を使わない) に変える | fix 子 (生成器) → 親が再生成 |
| R2 | A must-fix 2 | README fig8 節の `campaigns[].campaign_path` は実 JSON に無い。正しくは `campaigns[].admission.campaign_path`。brief:7 と裁定 §2.2 手順 3 の誤記が伝播 | README を訂正 | 親 (docs) |
| R3 | A nit 1 | caption に測定環境名 (Pegasus) が無い (FIGURE_CONVENTIONS §6) | 生成器が `identity.measurement_env == "pegasus"` を検査し、条件列を "Conditions: Pegasus compute nodes, 48 threads, …" にする | fix 子 (生成器 + fixture) |
| R4 | A nit 2 | 探索走 `t2418-explore` / `t2266-tail` 系列の標本非混合が caption に無い | caption 末尾に 1 文 "No samples from the exploratory run t2418-explore or the t2266-tail series are included; 9999 us was newly measured in this cohort." を足す | fix 子 (生成器) |
| R5 | A nit 3 | README・plotting README の相互検算の記述が実装より広い (CI・端点比は照合しない。L だけでなく U も検査) | 「平均 2 種・CV 2 種・abort 率の SD を `statistics` と照合、CI・端点比は再計算のみ」「L と U の一致」に直す | 親 (docs) |
| R6 | A nit 4 | certified の保証範囲 (観測した YCSB point read/write trace 上の直列化可能性まで) が caption に無い (版 §7) | correctness の文に "certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond" を足す | fix 子 (生成器) |
| R7 | B must-fix 1 | M11 (SHA 比較除去) に対し `test_pinned_hashes_are_used_when_no_override` は completion artifact 検査 (G:178) で拒否され続け、赤は診断文言差だけ (DW-M03 の kill ではない) | 同 test を単一理由にする: fixture の `-complete.json` の `artifacts` を **production の pin 値** (`PINNED_SHA256` の json/dat) にして completion 検査を通し、byte 比較だけが拒否するようにする。期待 message は "SHA-256 mismatch" | fix 子 (test) |
| R8 | B must-fix 2 | 変異の期待 node は完全集合でなければならない (M9 は `test_layout_failure_publishes_nothing` も赤、M1/M4/M5/M6 は着地 test も赤) | 最終 commit (着地 bundle 込み) の container worktree で probe → 観測 node 完全集合で final を登録 (裁定 §4 の予想は上書き) | 親 (変異) |
| R9 | B nit (closure の射程) | `validate_repo_closure` は保存済み cells からの再投影であり reps からの再計算ではない | README proof chain に 1 文追記 (独立再計算は `test_real_root_loads_…` と results 稿の照合が担う) | 親 (docs) |

## refuted / 対応不要

- A: 「declining / keeps decreasing が過大主張」「性能認証との混同」「caption 数値の転記誤り」「README 節欠落」— いずれも refuted (根拠は A の本文)。
- B: 並べ替え・位置 zip の誤対応、parse が SHA 不一致を隠す、fixture 寸法不足、禁止句 test・axes gate の恒真、skip/harness — いずれも refuted。
- B nit「負例 11 件は単一理由でない」— 登録変異の証拠に使っていないので対応不要 (台帳に記す)。
- B nit「公開の原子性」— layout check は mkdir・保存より前で、新規成果物は出ない。README の記述はその範囲で正確。対応不要。
- brief:7 の「statistics に median がある」は現物どおり (refuted)。「group id は JSON に無い」は top-level の意味で正しく、`admission.campaign_path` に含まれることは R2 で明記。

## 裁定パッケージ候補 (scope 外、実装しない)

- `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」へ fig8 の成立を案内する (版 `2026-09-17.md` §4 と results 稿 §3 限定 11 の「図は無い」は当時は真)。図の成立を性能認証・B-10 閉鎖・第 2 cohort (D2104 項 7) の解除には昇格させない。→ 段 7 の worklog fragment に次の一手として書く。

## 受理集合への影響

R3 で `identity.measurement_env == "pegasus"` を要求する分だけ受理集合が狭まる (実データは 3 campaign とも `pegasus`)。R7 は test の fixture 変更のみ。他は caption 文字列と docs の変更で受理集合は不変。

## 変異 matrix

R7 により M11 の単独 kill 証拠は `test_pinned_hashes_are_used_when_no_override` (単一理由化後) と `test_external_input_hash_drift_is_rejected` の両方になる。他の M は変更なし。fix 後に anchor を再検証 (DW-M07) し、probe で完全集合を確定する。
