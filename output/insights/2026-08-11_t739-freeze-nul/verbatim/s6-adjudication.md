# 段 6 レビュー裁定 — [T-739]

## must-fix の裁定

### R1 (review1) — 幅広 JSON で走査 stack がメモリ増幅する → **real / nit へ格下げ (不採用)**

親が実測した (`job dir/memory_probe.py`)。

```text
MAX_BLOB_BYTES = 16777216 (16 MiB)

width=10000   raw=188,906 B   parse+canonical peak 4.7 MB   traversal 追加 2.3 MB   比 12.13x
width=100000  raw=1,988,906 B parse+canonical peak 33.9 MB  traversal 追加 23.0 MB  比 11.56x
```

- 比が 12.13 → 11.56 と**平坦**であり、レビューの `O(n log n)` という主張は成立しない (実測は O(n))。
- 追加分 (約 11.6 × raw) より**手前の** `_strict_json` + `_canonical_bytes` のピーク (約 17 × raw) の方が
  大きい。走査で落ちる入力は、その前段で既に 1.5 倍近い峰を越えている必要がある。
- `read_blob_at` 経路は `MAX_BLOB_BYTES` = 16 MiB で上限があり、最悪でも合計 460 MB 程度。
  login ノードの 16 GiB 上限に対して桁が違う。
- したがって DW-G05 の「実装しなかった場合に成果物のどの値が変わるか」が**到達不能な条件下でしか
  成り立たない**。must-fix にしない。深さ比例走査への書き換えは防御的堅牢化であり既定で見送る。
- 記録: 段 7 の worklog へ実測値と判断理由を残す。

### R2 (review2) — NUL が文字列**中間**にある場合を検査していない → **real / must-fix (採用)**

現在の 41 個の拒否テストはすべて `"\x00alias"` を**末尾に付加**する。実装を
`node.endswith("\x00alias")` に変えても全部緑のままで、検出力に穴がある。

- 追加テスト: NUL を path の**中間**に挿入する case を、少なくとも
  `required_evidence` 側と `consumer_requirement` 側の 2 つで固定する。
- 変異 `M6-nul-position` を事前登録に追加する (下記 §変異)。

## nit の裁定

| 所見 | 判定 |
|---|---|
| detail が RFC 6901 の `~0` / `~1` escape をしていない (review1) | **不採用**。例外 detail の位置参照だけの問題で受理集合・hash・台帳は変わらない。escape を入れると全期待 pointer 文字列が変わり、得るものが釣り合わない |
| `test_current_evidence_contract_hash_is_frozen` と `test_existing_g1_record_pins_are_unchanged` がどの変異にも殺されない (review2) | **仕様どおり**。これらは検出力テストではなく hash drift の回帰 pin である。変異 score の分母から外して記録する |
| import 時の `assert len(cases) == 38` が collection error を起こす (review2、review1 も周辺に言及) | **採用**。独立したテスト関数へ移し、parametrize 自体は collect 可能にする |
| その他 (走査漏れ・文書順・生 NUL 漏洩・迂回経路・過剰拒否・停止性・既存 hash 回帰・E2E 到達性・オラクル独立性・テスト規律) | 両レビューが **refuted**。親も差分読解で同意 |

## 変異事前登録の追加 (DW-M01)

| id | 変異 | category | 期待 |
|---|---|---|---|
| `M6-nul-position` | `if is_path and isinstance(node, str) and "\x00" in node:` → `if is_path and isinstance(node, str) and node.endswith("\x00alias"):` | negative | **KILLED** (中間 NUL テストだけが殺す) |

既存の M1〜M5 は据え置き。`M2-first-only` について review2 は「legacy E2E は `conditions[0]` の
consumer path なので赤にならない」と予測した。これは事前登録の期待 node を絞る情報であり、
`M2` の期待 node からは legacy E2E と activation report E2E を除く。
