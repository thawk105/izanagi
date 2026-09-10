## 変更点一覧（行番号は現行ファイル基準）

- `orchestrator/tests/test_coder_effect_gate.py:5-7`  
  `from typing import Final` を追加。

- `orchestrator/tests/test_coder_effect_gate.py:67` 付近（`_CATEGORY_PROBES` の直前）  
  次の独立 literal を追加する。

  ```python
  _FROZEN_DENY_IDENTIFIERS: Final[dict[str, frozenset[str]]] = {
      "process-shell": frozenset((...)),
      "file-stdio": frozenset((...)),
      "network": frozenset((...)),
      "sleep-block-thread": frozenset((...)),
      "escape-hatch": frozenset((...)),
  }
  ```

  5 category、各 18 / 35 / 18 / 18 / 7 identifier、合計 96 個を含める。`...` は計画上の省略であり、段5では全 literal を貼り付ける。

- `orchestrator/tests/test_coder_effect_gate.py:91` 付近（既存の category probe の直後）  
  新規関数 `test_deny_table_identifiers_are_not_removed_from_frozen_baseline() -> None` を追加する。

  ```python
  current_by_category = {
      rule.category: frozenset(rule.identifiers)
      for rule in DENY_TABLE
  }

  assert sum(
      len(identifiers)
      for identifiers in _FROZEN_DENY_IDENTIFIERS.values()
  ) == 96

  for category, baseline in _FROZEN_DENY_IDENTIFIERS.items():
      missing = baseline - current_by_category.get(category, frozenset())
      assert not missing, (
          f"DENY_TABLE shrank in {category}: {sorted(missing)!r}"
      )
  ```

- `orchestrator/campaign/coder_effect_gate.py:58-105, 117-138, 576-614`  
  変更しない。`DENY_TABLE`、`_IDENTIFIER_RULE`、`scan_host_effects` の挙動は不変とする。

## 1. Frozen baseline の設計

category 別の `dict[str, frozenset[str]]` を採用する。flat set よりも、identifier の削除だけでなく category 間の移動・category 名の変更も検知でき、失敗時に対象 category と missing identifier を直接表示できるためである。

baseline は `DENY_TABLE` から実行時に生成しない。段5 author は、production ファイルを変更していない基準状態で一度だけ次のような dump を実行し、出力を literal として貼り付ける。

```python
from orchestrator.campaign.coder_effect_gate import DENY_TABLE

for rule in DENY_TABLE:
    print(
        f"{rule.category!r}: "
        f"frozenset({tuple(sorted(rule.identifiers))!r}),"
    )
```

dump 後に production を編集した状態で再生成してはならない。貼り付け後は category 別件数・総数 96・各 identifier を `coder_effect_gate.py:58-105` と人手で照合する。生成スクリプトや runtime helper は commit しない。

## 2. 比較則

| 比較 | 長所 | 短所 |
|---|---|---|
| `current ⊇ frozen` | 削除だけを検知し、将来の禁止 identifier 追加を許容する | 追加・置換そのものは検知しない |
| 完全一致 | 追加・削除・移動をすべて検知する | 正当な追加でも baseline 更新が必要になり、今回の「縮んでいない」という契約を越える |

`current_by_category[category] ⊇ frozen[category]` を推奨する。T-1357 の対象は縮小であり、brief の不変条件 (c) と一致するためである。

なお、現行の既存テスト `:81` は category 集合を `_CATEGORY_PROBES` と完全一致させている。したがって本案で許容する拡張は、主に既存 category 内の identifier 追加である。新 category 追加まで許可する変更は別途必要になるため、本 wave では行わない。

## 3. 既存テストとの関係

併存させる。

`test_each_deny_table_category_has_a_mutation_killing_probe`（現行 `:78-88`）は、各 category の代表 identifier が実際に scanner で拒否されること、rule ID と category の対応が保たれることを確認する。

新検査は、代表 probe 以外を含む全 identifier の table 所属を独立 baseline と比較する。既存テストを置き換えると、scanner の意味的 positive-control anchor を失うため、二重 anchor を残す。

## 4. `coder_effect_gate.py` 側の変更要否

変更不要。production 側は `DENY_TABLE` の内容を保持したまま、テスト側で現在値を観測するだけで要件を満たせる。

`_IDENTIFIER_RULE` が `DENY_TABLE` から導出されること（`coder_effect_gate.py:126-132`）は production の通常実装であり、新検査の期待値をそこから導出しない限り自己参照には当たらない。

## 5. 段6の変異事前登録候補

各変異は production の tuple から該当 identifier 1 個だけを削除し、テスト literal は変更しない。

| category | 削除対象 | 既存 probe | 旧テスト | 新テスト |
|---|---|---|---|---|
| process-shell | `fork` | `posix_spawnp` | SURVIVED | KILLED |
| file-stdio | `fopen` | `read` | SURVIVED | KILLED |
| network | `socket` | `connect` | SURVIVED | KILLED |
| sleep-block-thread | `pthread_create` | `sleep_for` | SURVIVED | KILLED |
| escape-hatch | `syscall` | `__asm__` | SURVIVED | KILLED |

各変異では既存の代表 identifier が残るため、category-level probe は通過する。一方、新検査の `missing` はそれぞれ削除対象一個を含む。

## 6. Reward hack 耐性への自己点検

- baseline の RHS は literal のみとし、`DENY_TABLE`、`effect_gate` の helper、`_IDENTIFIER_RULE` から導出しない。
- 新検査は空の parameterization にしない。単一関数内で全 category を走査し、baseline 総数 96 も確認する。
- `pytest.mark.skip`、`xfail`、環境依存の早期 return、例外を握り潰す条件分岐を追加しない。
- dump は現在の実装を写すだけなので、T-396 §7 が指摘する time/random、未列挙の副作用 call、loop、`throw` などの既存欠落を修復するものではない。これは「完全な安全性の証明」ではなく「現行禁止集合の以後の縮小防止」である。
- 同じ identifier 文字列が production と test に存在するため、文字列全置換型の粗い変異なら両方を変更できる。段6では production の対象 AST／行だけを変異し、frozen literal が不変であることを確認する。
- `Final` は静的注釈であり、module-level の outer `dict` を runtime に凍結するものではない。テスト内で baseline を変更しないことを段3の adversarial review で確認する。

## 所有パス

- 段5で変更する唯一のファイル  
  `orchestrator/tests/test_coder_effect_gate.py`
- 不変として監視するファイル  
  `orchestrator/campaign/coder_effect_gate.py`
- 設計根拠として参照した read-only 資料  
  `/work/SFC/tanab/dev-wave-jobs/t1357-deny-table-shrink-guard/artifacts/s1-brief.md`  
  `output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md`

## 総括

独立した category 別 frozen literal をテストへ固定する。  
比較は identifier 単位の superset とし、追加は許容・削除は検知する。  
既存の category probe は scanner anchor として併存させる。  
production は変更せず、段6で各 category の代表外 identifier 削除を検証する。