# 段6裁定
- review-a/bのcaller fixture不足はreal。既存bind_admission_policyを新設test準備へ使うfix1を採用。製品コードとassertionは不変。
- review-bの追補§5参照誤りはreal。§5を本格系列specとして変更対象外と明記し、T2418新走statusだけ本追補へ従わせる文へ親が修正。
- 期待値の観測依存、乱択static化、旧artifact上書き、author無しハンク、版本取り残しはrefuted。
- 追加gate/framework/create-only検査は実装しない。
- focus-2.logで修正後の実走を記録。review-a/b/fix1はdone0とoutput checker0。
