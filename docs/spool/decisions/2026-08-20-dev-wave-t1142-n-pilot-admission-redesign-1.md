---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1142-n-pilot-admission-redesign
seq: 1
---

## {{D:t1142-n-pilot-r33-admission-authority}}. n-pilot R33 admission authority

**決定:** R33 の admission role は既存 `n_pilot` と分離した `n_pilot_r33` とし、role
contract の authority pin は numeric D 番号ではなく `t1142-n-pilot-r33-admission-authority`
とする。

**機械 pin:**

- authority slug: `t1142-n-pilot-r33-admission-authority`
- R33 admission contract: role=`n_pilot_r33`; generation=`n-pilot-r33`; pilot_rounds=33; allocation_count=3; cell_count=12; schedule_row_count=396.
- R33 protocol distinction: `design.allocation_role`=`primary-segment`; `observation_role`=`n_pilot_r33`.

**理由:** D 番号は `docs/spool/` の fold 時点で初めて確定するため、実装 commit の
Python source が numeric D 番号を持つと、実装時点で存在しない値への依存になる。stable
slug を role contract と decision 本文の共通 pin とする。

既存の R=11 実測 (`observation_role="n_pilot"`, campaign_run_id="t1142-run-1") は
admission 機構の排他 claim 設計 (cell key が `campaign_run_id` を含まない一発勝負ロック)
により、既存 claim の上に追加投入することが構造的に不可能であることを pegasus02 実機で
確認した。事前登録済み目標 R>=32 (実質 R=33、32 以上かつ 3 で割り切れる最小値) を満たす
ためには、新しい observation role 世代での独立した admission 発行が必要であり、
`n_pilot_r33` をその role として採用する。

**限界:** この exact-pin 検査は role・decision 間の generation / round / allocation
値のうっかりした不一致を防ぐためのものであり、role・decision・checker を意図的に同一
commit に揃える濫用や、完全な時系列を強制するものではない。izanagi には push しない
運用のため GitHub Actions 等の protected CI が実質的に機能せず、merge base 側の検査を
委ねる実行主体が無い。恒久的な時系列強制が必要になった場合は別 wave の課題とする。

**却下した選択肢:**

- 実装 commit に `D<N>` を直接埋め込む方式 — fold 前には番号が存在しない。
- protected CI / merge base 検査による時系列の機械強制 — izanagi は push しない
  local main 運用のため実行主体が無い。
- checker-only commit → decision-only commit → implementation commit の3段階land
  — izanagi の通常 fold / land 契約 (1 wave = 1 回の受入・land) と整合しない。
- 新しい git clone/checkout で admission root を分離し既存 key を再 claim する方式
  — 事前登録が「不可逆・一度きり」と明記した観測承認の安全装置を回避することになり
  不採用。
