# 次 wave の出発点 — 単位 D2 (consumers/fixtures)

継承 wave はここを最初に読むこと。本 file は branch `worktree-dev-wave-t1851-unit-c2` 側にだけ置く
(同 dir の `README.md` は main へ先行着地させたので、両者を byte 一致に保って merge 競合を避ける)。

**この branch を land できるようにする唯一の残り単位が D2 である。** D1341 と D1703 (どちらも
ユーザー裁定) により、branch は D2 が揃うまで land しない。branch は 2026-09-02 以降 4 単位
(C1b / C2 / C3a / C3b) を載せたまま未 land で、main との乖離が開き続けている。**D2 を閉じることが
遅滞を解く唯一の正規経路である。**

## 変更面の実アンカー (2026-09-10 に親が実測)

| アンカー | 現状 |
|---|---|
| `orchestrator/campaign/s8b_holdout_freeze.py:1437` | `frozenset(result) != expected_result_keys` で v4 の key 集合を exact 要求 |
| 同 `:1439` | `result.get("schema") != s8b_floor_contract.RESULT_SCHEMA` (= v4) |
| `orchestrator/campaign/s8b_ratified_freeze.py:2399` | `_validate_result_top_level_keys()` が v4 の top-level key を exact 要求 |
| 同 `:2404` | `document["schema"] != _floor_contract.RESULT_SCHEMA` (= v4) |
| `orchestrator/campaign/s8b_floor_contract.py:36` | `RESULT_SCHEMA = LEGACY_RESULT_SCHEMA`。producer は `s8b_floor_campaign.py:6816` で `attempt_registry is not None` のとき v5 を出す条件分岐 |

## 不変条件 (D2 の brief がそのまま引き継ぐべきもの)

- **受理集合を単に広げない。** D1194 の要求は「新規成果物へ前向きに束縛を掛ける」であって
  「v5 も通す」ではない。**consumer は prefix proof 7 key
  (`schema` / `registry_schema` / `freeze_sha256` / `protocol_sha256` / `schedule_sha256` /
  `row_count` / `chain_head_sha256`) を実際に検証して初めて受理する**形にする。
  検証せず schema だけ広げると、D1194 が却下した「謳うだけで発火しない保証」になる。
- `s8b_floor_contract.py:30-31` の comment 「現 producer は v4 のまま」は C3a 後に陳腐化している。
  D2 で現況へ直す。
- 凍結 23 件の bytes を変えない。`FORMULA_ID` 据え置き。

## main 取り込みで必ず起きる競合 (2026-09-10 に親が実測)

`orchestrator/tests/acceptance_duration_ledger.json` は wave 側 `nodeid_count` 22,483 に対して
main 側が 22,245 で、**内容競合する。** 正本 producer は
`python3 tools/update_acceptance_duration_ledger.py`。`--add-only` は既存 entry を byte exact に
保って未登録 nodeid だけを足すが、**merged tree の JUnit が要る**ため、main を取り込んだ後に
その tree で 1 度走らせてから台帳を更新する順序になる。親が 2026-09-10 に前倒しで解こうとして
順序が合わず merge を戻した。

## D2 が終わったら

1. branch 全体を land する (D1341 の同時 land 条件が初めて満たされる)。
2. 着地待ちの裁定 **10 件**を再提示する — C3a の 5 件
   (`2026-09-09_t1851-unit-c3a-wiring/ruling-package.md`) と C3b の 5 件 (同 dir の
   `ruling-package.md`)。D1703 により単位が揃うまで個別裁定しない扱いだったものである。
3. 本 dir の `ruling-package.md` の裁定 1 (allowlist の束縛先) が解ければ、単位 C3c として
   official 床値を再走し、**契約 9 節が要求する attempt registry 側 gate の実値域**を初めて
   供給できる。C3b の走行は claim / marker / registry を 1 件も作っていないので凍結世代は
   焼けていない。
