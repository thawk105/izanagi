# 親の実測 — [T-574]

親 (Claude) が自分で走らせて確認した事実だけを置く。子の報告は根拠にしない。
**射程を先に書く: 実測したのは leaf と component の counterfactual であって、E2E ではない。**

## 1. 段 1 前提実測 — 2 世代目で publish 済み成果物が読めなくなるか

方法: `orchestrator/campaign/env_contract.py` の `_build_registry()` へ pegasus の g2
(calibration の path/sha だけを変えた valid successor) を**実編集**で足し、
`validate_generations` の 1 世代 fuse を一時的に緩めた。monkeypatch は使っていない。

| 対象 | g1 のみ | g2 を current にした直後 |
|---|---|---|
| `s8b_floor_campaign.validate_protocol(output/s8b-freeze/floor_protocol.json)` | 受理 | `FloorCampaignError: protocol.contract_sha256 が env_contract.lookup('pegasus').contract_sha256 と不一致` |
| `s8b_oracle_report._receipt_expectations` (記録 hash を持つ manifest) | 受理 | `ReportError: manifest contract_sha256 が registry contract と不一致` |
| 同じ document を「記録 hash から解決した契約」で検証 | 受理 | **受理** |
| `env_contract.resolve_by_contract_sha256(記録 hash)` | g1 を解決 | g1 を解決 |

復元: `git checkout --` 後に tree clean、`env_contract.py` の worktree hash は
HEAD blob `abe103e5` と byte 一致。

probe の逐語は本節末尾に埋め込む。**実行可能ファイルとしては repo へ置かない** — 段 1 の前提実測は
`docs/dev-wave/core.md` の `DW-S01` が親に課す義務だが、親 (Claude) が書いた Python を repo へ
置くと `docs/ai-provenance.md` の「実装面には Codex `role=author` を必須とする」契約に抵触する。
規約を緩めず逐語も失わないため、計器はコード block として記録に残す形にした
(実際に `check_ai_provenance.py` が違反として検出したので、この形へ直した)。

**この実測の射程 (段 3 のレンズ 2 本が独立に指摘し、親が受け入れた限定):**
測ったのは上表の 2 leaf だけである。`s8b_ratified_freeze.launch_validate` は本 branch では
`[no-active] live active pointer が無い (v2 未発効)` で入口に到達せず、C2 / C3 / selector /
`build_observations` は測っていない。**「floor / freeze / selector / oracle report がすべて落ちる」は
D196 の文言の引き写しであって、本 probe が示した事実ではない。**

<details>
<summary>probe 逐語 (段 1 前提実測の計器)</summary>

```python
# -*- coding: utf-8 -*-
"""段 1 前提実測 — 2 世代目が current になったとき、published artifact の read-only
再検証が current lookup のせいで落ちるかを production consumer で測る。

repo を変更しない。呼び手が registry を実編集した状態で走らせる。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve()
REPO = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "orchestrator"))

from campaign import env_contract as ec  # noqa: E402
from campaign import s8b_floor_campaign as fc  # noqa: E402
from campaign import s8b_floor_contract as fcon  # noqa: E402
from campaign import s8b_oracle_report as orep  # noqa: E402

doc = json.loads((REPO / "output/s8b-freeze/floor_protocol.json").read_text())
recorded = doc["contract_sha256"]
env_tag = doc["env_tag"]

out = {}
out["registry_generations"] = {k: len(v) for k, v in ec.GENERATIONS.items()}
out["recorded_contract_sha256"] = recorded
out["current_lookup_sha256"] = ec.lookup(env_tag).contract_sha256
out["current_equals_recorded"] = ec.lookup(env_tag).contract_sha256 == recorded

# resolver (data 層、D176) は記録された hash から世代を解ける
try:
    entry = ec.resolve_by_contract_sha256(recorded, expected_env_tag=env_tag)
    out["resolver"] = {"ok": True, "generation": entry.generation}
except Exception as exc:  # noqa: BLE001
    out["resolver"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

# consumer A: floor protocol の read-only 再検証 (s8b_ratified_freeze.launch_validate と
# s8b_floor_campaign が共有する leaf。current lookup を注入する形)
try:
    fc.validate_protocol(doc)
    out["consumer_floor_protocol_current_lookup"] = {"ok": True}
except Exception as exc:  # noqa: BLE001
    out["consumer_floor_protocol_current_lookup"] = {
        "ok": False, "error": f"{type(exc).__name__}: {exc}"}

# 同 leaf を「記録された hash から解決した契約」で検証すると通るか (T-574 の狙い)
try:
    fcon.validate_protocol(
        doc,
        contract_sha256_lookup=lambda env: ec.resolve_by_contract_sha256(
            recorded, expected_env_tag=env).contract.contract_sha256,
    )
    out["consumer_floor_protocol_historical_resolve"] = {"ok": True}
except Exception as exc:  # noqa: BLE001
    out["consumer_floor_protocol_historical_resolve"] = {
        "ok": False, "error": f"{type(exc).__name__}: {exc}"}

# consumer B: oracle report の published manifest 再検証
manifest = {"run_contract": {"env_tag": env_tag, "contract_sha256": recorded}}
try:
    orep._receipt_expectations(manifest)
    out["consumer_oracle_receipt_expectations"] = {"ok": True}
except Exception as exc:  # noqa: BLE001
    out["consumer_oracle_receipt_expectations"] = {
        "ok": False, "error": f"{type(exc).__name__}: {exc}"}

print(json.dumps(out, ensure_ascii=False, indent=2))
```

</details>

## 2. `resolve_by_contract_sha256` の production consumer

着手時点で 0 件 (test のみ)。D176 の「履歴 resolver は production の消費者を持たない
data 層の準備である」という限定が、そのまま残っていた。

## 3. `launch_validate` は live 実走の admission である (段 3 の blocker の裏取り)

`s8b_oracle_driver.run_block` が `launch_validate` を呼び (`s8b_oracle_driver.py:1066`)、
`_prepare_v2_execution` (`:737`) がその戻り値を `isinstance(LaunchValidatedFreeze)` で要求し、
通過後に marker / WAL / 予算を書く。
**したがって段 1 brief が C1〜C3 を「read-only 再検証」と分類したのは誤りだった。**
本 wave はここから入口分離へ舵を切った。

`LaunchValidatedFreeze` (`:764-777`) は封印されていない素の frozen dataclass である。
型分離は偽造耐性を持たない (D176 が型分離を権限 gate として却下した理由と同じ)。
効くのは「自分たちの consumer が黙って広がらないこと」だけである。

## 4. silo `validate_current_bindings` という第 5 の層 (scope 外と裁定)

`silo_ladder_rung1.py:3534` が committed artifact の
`binding["calibration"]["contract_sha256"]` を **current** lookup と比較する。
親が現物で実走した結果は **今日すでに赤**:

```
EvidenceFailure(reason_code='binding', detail='current binding mismatch: driver')
```

歴史 proof verifier なのか current 互換 verifier なのかが未裁定のため、本 wave では触らず
択一 R2 として返す。

## 5. DW-O09 pin 閉包 (段 1 の判定を段 4 で訂正)

段 1 brief は「publish 済み artifact に旧 hash を pin したものは `output/` に 0 件」と書いたが、
これは**偽**だった。正しくは:

- `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:67` が
  `orchestrator/campaign/env_contract.py` の sha `88d557ba…` を path key で pin する。
- `output/env/pegasus/t419-probe-causality/0_889400.nqsv/manifest.json:110,270` が
  **role 名 key** `env_contract_sha256` で同じ値を pin する (path 検索では見つからない)。
- 現物の `env_contract.py` は `8d529822…` で、すでに一致しない。

**本 wave は `env_contract.py` を変更しないため、この pin を新たに壊さない。**
本 wave が編集した 3 module (`s8b_ratified_freeze.py` / `s8b_oracle_report.py` /
`s8b_floor_contract.py`) の旧 hash pin は、path key・role key の双方で 0 件である。

## 6. 受入と変異 (親が計算ノードで実走)

| 実測 | 値 | checkout |
|---|---|---|
| 対象 4 test file (fix 前) | 359 passed | `fac84353` |
| 対象 4 test file (fix 後) | 448 passed / 1 skipped | `7f1dc184` |
| **受入全走 (実装 commit)** | **6806 passed / 20 skipped** (1123.89s) | `a05ce433` (main `1f352ce2` 取り込み後) |
| 受入全走 (docs commit 後の再走、F34) | 6806 passed / 20 skipped (873.70s) | `d1e70d5c` (probe を .py で含む版) |
| **受入全走 (最終、probe を記録へ埋め込み直した後)** | **6806 passed / 20 skipped** (1006.90s) | `2c1e0c3d` |

`d1e70d5c` は `check_ai_provenance.py` が「実装面に Codex `role=author` がない」として
1 違反を返したため amend した (親が書いた probe の `.py` が実装面に当たる)。
最終 commit `2c1e0c3d` では full-history 監査が 1560 件・違反なしである。
| 変異 run 2 | 12 変異中 12 が事前登録どおり (KILLED 9 / SURVIVED 3) | `7f1dc184` |

変異 run 1 は erratum として同 dir に残す (`mutation-*-run1-erratum.json`)。
run 1 で判明したのは次の 2 点で、run 2 はこれを反映した再照準である。

- **M3a / M3b / M3c がすべて SURVIVED。** 実装が C1 に足した hash 再検査 2 箇所は、
  既存の `s8b_floor_contract.validate_protocol` の等値検査に**冗長**である。
  実効 gate まで含めた 3 層同時変異 M3e を足したところ KILLED になり、実効 gate が
  第 3 層であることを確認した。C4 側 (`_receipt_expectations`) は単層のため M3d が単独で KILLED。
- **M1 / M2a / M2c / M5 は過剰決定。** 新規 test が resolver の呼出し引数と identity を spy で
  pin するため、resolver 配線を変える変異は広い node 集合を一度に落とす。
  run 2 では実測どおりの node 集合を登録し直した。**単独変異の受理集合 kill 証拠としては扱わない**
  (DW-M03)。

M7 は**構造 pin**であり受理集合 kill に数えない。正当な後継世代では `clocks_per_us` /
`numactl` が世代間で同値になるため、この unit でしか検出できない。
