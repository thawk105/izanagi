---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: worktree-dev-wave-t1472-floor-refreeze
seq: 1
---

## {{D:d510-followup-implementation-audit}}. D510 追随実装の所在監査と項目6 (測定近接性ラベル) の実装見送り

**決定:**

1. D510 (D510) が要求する判定器・3表・事前割当 attempt registry は、
   `orchestrator/campaign/between_run_floor.py` (A2 between-run noise floor calibration
   driver、D510 とは無関係) ではなく、`orchestrator/campaign/s8c_result_judge.py`
   (paired diff 判定・3表、T-1352 由来) と `orchestrator/campaign/trial_registry.py`
   (事前割当 attempt registry、T-325 由来・T-1310 が D510 attempt registry へ統合) に
   既に実装済みであると確定する。role payload 非干渉性の二層 digest も T-1311 で
   実装済みだが、`docs/phase3-8c-preregistration.md` §4/§6 が明記する通り評価器は
   非充足を返し続ける (機械検査対象ではあるが充足経路0、意図的な fail-closed 設計であり
   欠陥ではない)。
2. D510 項目6 (測定の近接性と主張の強さ、`docs/phase3-8b-descriptor-design.md` §10.4) は
   `s8c_result_judge.py` の `_ObservationContext`/`_build_observation_context` に実装の
   痕跡がなく、唯一の未実装項目と確定する。ただし本改訂では実装しない。

**理由:**

- command 引数が土台に指定した `between_run_floor.py` への言及は、T-425 commit
  `3ef63484` が「between_run_floor.py がそもそも official/pilot 儀式を経ない設計である
  ため、この driver の手続きを直接は変更しない」と明記する軽微な schema_version 追加
  (3 hunks) にすぎず、D510 が要求する「同一 campaign 内 paired 差分統計」の判定器そのもの
  とは無関係だったと、段3 敵対2レンズが独立に確認した。
- 項目6の最小実装案は、`judge()` の入力契約を無条件で厳格化すると既存の (旧形式の)
  有効入力の受理結果を変えてしまい、「既存受理集合を変更しない」という不変条件と衝突する。
  また `relation_kind` (継続測定/復旧後測定/意図的過去比較の3区分) が既存の raw-value
  attestation (SHA・issuer) と独立な自己申告フィールドのままだと、観測の実性質を偽って
  より強い主張ラベル (継続測定) を詐称できる — 規律2 (正しさゲートを緩める変異を許さない)
  の精神に照らし、対策なしに実装するのは危険と2レンズが独立に指摘した。
- `s8c_result_judge.judge()` には現時点で production caller が存在せず、参照はテストと
  静的 AST evaluator (`s8c_preregistration_evidence.py` の C07 検査) に限られる。
  発火条件を満たす既存 artifact path が無い状態での実装は、実運用では到達しない
  コードを作ることになる。
- D510 項目7 (仕様のみ発効、測定を認可しない) は `s8c_preregistration_evidence.py` の
  `SATISFIABLE_CONDITION_IDS` 空集合により既に構造的に fail-closed であり、項目6を
  今追加しても実害防止効果がない。将来 producer (provenance を生成し `judge()` へ渡す
  経路) と、role payload 非干渉性 (D510項目5) の producer 統合方針が確定してから
  着手する方が、private schema の手戻りを避けられる。

**却下した選択肢:**

- `between_run_floor.py`/`s8b_floor_campaign.py`/`s8b_oracle_driver.py` を土台に
  judge・3表・validator を新規実装する (当初 command 引数の指示) — 実測の結果これらは
  既に別実装 (`s8c_result_judge.py` 等) が存在する D510 の対象ではなく、二重実装に
  なるため却下した。
- 項目6を最小実装 (`_ObservationProvenance` 追加のみ) してこの wave で着地させる —
  発火条件を満たす既存 artifact path が無く、producer なしでは実運用で到達しない
  コードになるため却下した。
