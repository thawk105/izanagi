# [T-1316] 受入 lease 取得後・受入 command 投入前に落ちる型の裁定パッケージ

wave `dev-wave-t1316-acceptance-recovery-ruling` / 2026-08-19

本 wave は**実装しない**。成果物は `ruling-package.md` (裁定パッケージ本体、次回 `/rulings` へ)
だけである。段 2 (codex plan)・段 3 (敵対レンズ A/B) の逐語記録は `verbatim/` にある。

## 何を裁定パッケージへ返すか

t1180 で実測された「受入 lease 取得後・受入 command 投入前に main が進み、
`--merge-message-file` を渡していなかったため lease だけ失う」型 (F365 が名指し、
[T-1275] が明示的に本 T-1316 へ切り出した残余)。親の provisional 案 (P1: message file を
常時同梱すればコード変更ゼロで race を閉じられる) を段 3 の 2 レンズで攻撃し、
9 件 real・2 件 refuted の所見を得た。詳細は `ruling-package.md`。

## 推奨の要旨

- **P2 (`--merge-message-file` を必須化し claim 前に snapshot する) を恒久策として推奨**。
- P1 (運用規約のみ) は即時の暫定 mitigation として提案するが、単独の恒久策としては非推奨
  (既存の近い規約があっても t1180 は発生した実績があり、機械強制されない)。
- attempt 2 の複合レース (`claim-self-unverified`) と、merge の実装面著作 classifier
  (`merge-message-provenance`) は、同じ構造だが異なる引き金を持つ別問題として scope 外にし、
  将来の独立起票として記録した (DW-G03 の独立 2 例の基準に未到達)。
