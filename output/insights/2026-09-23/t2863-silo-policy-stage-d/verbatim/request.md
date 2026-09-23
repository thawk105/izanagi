# 依頼の逐語 ([T-2863]、2026-09-23)

## 起動 (ユーザー直接起動の `/dev-wave`、引数)

[T-2863] (P1) silo-function-policy 軸の段階 D (IR の機械偵察) を行う。設計 =
  output/insights/2026-09-21/silo-function-synthesis-space/README.md §5 (型付き有限 IR、停止性・算術安全を構成で保証)、前段 =
  output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md と D2226・D2214、手順 = docs/axis-onboarding.md §3-D。生成器・列挙・偵察
  driver を Codex author (D95) で書き、段階 C の骨格・検査器・診断経路 (orchestrator/campaign/silo_policy_coverage.py)
  を再利用する。計算ノード投入前に、段階 C の実測単価 (job Elapse) でタスク合計の node 時間を出し直してユーザー確認を取る (設計時換算
  1.15〜2.69 node 時間、D2212 項 4)。偵察結果は二値 (床を超える地形の有無) だけを後段へ渡し (§3-D の
  firewall)、継続/見直しは人間判断。正しさゲートは不変 (anomaly 即 reject、trace は compile 時に除去)、規律 2
  は緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。

## 計算の確認 (段 4 の後、AskUserQuestion)

- 提示: 合計はシナリオ値で約 1.7〜3.1 node 時間、各 job に walltime 上限を付けた上限で 4.0 node 時間 (初走 2 job × 10 件、再測は条件成立時だけ 1 job、開発時の検査)。
- 回答 (選択肢): 「上限 4.0 h で承認 (Recommended)」 — 合計 4.0 node 時間を上限に全体を承認。超えそうなら止めて再確認。

## 作業中のユーザー指示

「一瞬で終わらせてね。計算ジョブを分割して投げることで」
