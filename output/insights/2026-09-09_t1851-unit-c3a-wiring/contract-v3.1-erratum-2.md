# 契約 v3.1 の追記訂正 2 — campaign retry ordinal の束縛軸 (2026-09-09)

単位 C3a の実装 gate で判明した誤りを追記で訂正する。**本文 (`contract-v3.1.md`) は改変しない**
(絶対規律 7)。先例は `contract-v3.1-erratum-1.md` (単位 C2)。

## 訂正の対象

契約 v3.1 の 1.5 節が `campaign_record` の identity を規定する部分のうち、
**`retry_ordinal` を v2 slot のどの軸へ束縛するか**である。

## 何が誤っていたか (実測)

v2 `slot_id` は 5 軸である (`orchestrator/campaign/s8b_attempt_profile.py:159-168,238-256`)。

1. `slot_id[0]` = `freeze_holdout_key`
2. `slot_id[1]` = `configuration_id`
3. `slot_id[2]` = `repetition`
4. `slot_id[3]` = `measurement_ordinal`
5. `slot_id[4]` = `attempt_ordinal`

`series_key()` は先頭 4 軸で、`attempt_ordinal` は**その series 内の recovery 軸**である。

一方 campaign 契約は planned session に `retry_ordinal=None`、retry に `1..retry_slots_per_cell` を
要求する (`orchestrator/campaign/s8b_floor_contract.py:248-270`)。holdout 側の adapter も
campaign の retry 軸を `slot.measurement_ordinal` へ渡している
(`orchestrator/campaign/s8b_attempt_registry.py:2367-2370`)。

ところが訂正前の実装は次を要求していた。

- `retry_ordinal` は null 不可の非負整数 (`s8b_terminal_evidence.py:760-768`)
- `retry_ordinal == slot_id[4]` (同 `:1140-1157`)
- adapter / durable replay も独立に `campaign_record.retry_ordinal == slot.attempt_ordinal`
  (`s8b_attempt_registry.py:1394-1429`)

production registry は v2 reserve の `attempt_ordinal != 0` を拒否する
(`s8b_attempt_registry.py:2534-2538`)。したがって:

- **planned は `None` が型検査で拒否される。**
- **retry の `1..N` は、production で常に 0 になる `slot_id[4]` と一致しない。**

つまり **production では planned も retry も sealed terminal を構築できず**、
registry terminal と result v5 proof が完成しない。

## 訂正後の束縛

- `retry_ordinal is None` ⟺ `measurement_ordinal == 0` (planned)
- それ以外は `retry_ordinal == measurement_ordinal` (retry)

非 null 値に対する exact int・非負の検査は維持する。

## これは単調な緩和ではなく、受理集合の置換である

**(2026-09-09 の段 6 敵対レビュー RA-6 を受けて表現を訂正した。初出の
「受理の緩和ではない」という無限定の表現は正確でなかった。)**

訂正前の検査は、**production reserve を通過した v2 slot では** `attempt_ordinal` が常に 0 に
固定されるため、retry 側で**恒真に 0 を強いる検査**として働き、campaign の retry 軸を
1 つも束縛していなかった。

訂正の前後で受理集合は包含関係にない。**置換である。**

- **新たに拒否するもの**: planned の `retry_ordinal = 0`、retry の recovery 軸 `0` への束縛
- **新たに受理するもの**: planned の `None`、retry の measurement ordinal (`1..N`)

意図した軸への束縛強度は上がる。retry の `1..N` はこの訂正で初めて実際に束縛される。
planned の `None` は campaign 契約 (`s8b_floor_contract.py:248-270`) が定める形であり、
新しい受理形の発明ではない。

強度の対照として次の 2 つの負例を置き、**実際に発火することを実測した**。

- planned なのに `retry_ordinal` が非 null なら拒否される
- retry の `retry_ordinal` を `attempt_ordinal` (recovery 軸) へ差し替えたら拒否される

## 影響範囲

- 実装: `s8b_terminal_evidence.py`、`s8b_attempt_registry.py`
- fixture: `test_s8b_terminal_evidence.py`、`test_s8b_attempt_registry.py`、
  `test_s8b_floor_attempt_launcher.py` (planned helper の `retry_ordinal`)
- 凍結成果物の bytes は変わらない。`FORMULA_ID` は据え置き。

## 未裁定として残すもの

本訂正の**追認**はユーザー裁定へ返す (`ruling-package.md`)。とくに
「planned の `None` を表現可能にする」変更を、受理集合の単調縮小方針 (D1660) と
どう整合させるかを明示的に問う。
