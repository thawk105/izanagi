# [T-750] 統合実装 wave の逐語と変異台帳

wave = `dev-wave-t750-freeze-v2-manifest` / branch `worktree-dev-wave-t750-freeze-v2-manifest`。
base main = `0c0fbf25`、取り込み = `f4db7036` → `04e99891`。

## 何を実装したか

[T-750] のユーザー裁定 2 点 ((1) producer identity = 旧 module 内実装 / (2) budget authority =
人間承認が budget 数値そのものを承認する) と [T-782] (b) (reviewed spec を凍結成果物として先に作り
CLI は bytes を hash 照合する) を実装した。

- 単位 A = `s8b_holdout_freeze.py` に v2 g1 candidate producer と `generate-v2-candidate` CLI を純増。
- 単位 B = `s8b_oracle_spec.py` (新規) の reviewed spec schema / validator、
  `s8b_oracle_manifest.py` の `build-approved` CLI、および **`verify_manifest` の cell-product 検査**。

承認 authority は両者とも **module 内 pinned literal** (現在 `None` = 未承認 → fail-closed)。
Git commit の trailer を承認根拠にする設計は段 3 で恒真化と判定し破棄した。

## ファイル

| file | 中身 |
|---|---|
| `package.md` | 裁定パッケージ (P-1〜P-4)。ユーザー手番の入口 |
| `mutation-spec.json` | 変異事前登録 (8 件) |
| `mutation-ledger.json` | 変異本走の結果 (6 KILLED / 2 MISMATCH / SURVIVED 0) |
| `verbatim/s1-brief.md` | 段 1 brief (実測 M-1〜M-7 と provisional 裁定 P1〜P5) |
| `verbatim/s2-plan.md` | 段 2 プラン (file:line 粒度) |
| `verbatim/s3-lensA.md` / `s3-lensB.md` | 段 3 敵対 2 レンズ (いずれも NO-GO) |
| `verbatim/s4-adjudication.md` | 段 4 裁定 + 親の追加実測 N-1〜N-4 + 変異事前登録 |
| `verbatim/s5-prompt-*.md` / `s5-impl-*.md` | 段 5 実装子の prompt と報告 |
| `verbatim/s6-review-1.md` / `s6-review-2.md` | 段 6 敵対レビュー (いずれも NO-GO) |
| `verbatim/s6-adjudication.md` | 段 6 所見の裁定 (must-fix F-1〜F-8) |
| `verbatim/s6-fix-prompt-*.md` / `s6-fix-out-*.md` | fix の prompt と対応表 |

## 変異 matrix の erratum (`DW-M02`: 初回結果を消さず残す)

MISMATCH 2 件はいずれも**親の期待 node の誤りであり、コード側の欠陥ではない**。SURVIVED は 0 件。

- **MU-3B** (`O_EXCL` 撤去): 期待 2 node に対し実際は 3 node が落ちた。超過分は
  `test_v2_candidate_build_and_generate_synthetic_g1` (happy path) で、**過剰 kill** である。
  gate は実効。
- **MU-6** (spec pin の `None` 拒否を撤去): 期待 3 node に対し実際は 2 node。
  落ちた 2 件には「pin 無しでは出力前に失敗する」ことを見る
  `test_build_approved_active_without_pin_fails_before_output` が含まれるため、
  `DW-M03` の意味での kill (受理集合・fail-closed 挙動の変化) は成立している。
  期待に入れた `test_build_approved_valid_fixture_output_depends_only_on_spec_pin` は
  変異下でも緑のままで、親の見立てが外れた。

**実質は 8/8 で防壁が生存を許していない。**

## 親の実測の訂正 (段 4・段 6 で自分の主張を直した)

1. 段 1 の M-1「T-080 受領証が generator sha を metadata-only で受理済みだから単位 A の編集は
   v1 の受理集合を変えない」は**機序が誤り**。direct `verify()` は本 wave と無関係に
   **既に RED** であり (`design_source` の drift、`verify_document` が generator 照合より前に落とす)、
   結論 (受理集合は変わらない) だけが正しい。
2. 段 1 の M-5(ii)「configuration 網羅の検査は repo に不在」は**言い過ぎ**。
   `s8b_oracle_judge.py` に部分的な product 検査があり、holdout 間で構成集合が食い違う場合は
   捕捉する。捕捉しないのは**全 holdout で一様に間引いた**場合である。
3. 段 4 で自分が追加を裁定した cell-product 検査は、初版が期待積の holdout 集合を
   **schedule 自身**から導いており、**holdout を丸ごと落とした manifest を受理していた**。
   段 6 のレビュー 2 本が独立に指摘し、fix で `schedule の holdout 集合 == freeze の holdout 集合`
   を先に要求する形へ直した。
