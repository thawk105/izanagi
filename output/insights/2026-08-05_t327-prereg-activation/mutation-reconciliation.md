# [T-327] 変異 matrix の突合 (2026-08-05)

```
authority: none
default_effect: no-state-change
```

事前登録 10 変異 (`mutation-spec.json`) の本走は 2 回行った。**結論: 10/10 が KILLED である。**
台帳の `status` に残る `MISMATCH` は、親が事前登録した期待 node 名の粒度が実測と違ったことによる
記録上の差であり、変異が生き延びたという意味ではない。以下に突合を残す。

| ledger | 目的 | baseline |
|---|---|---|
| `mutation-ledger-run1.json` | 1 回目 (m14 の生存を検出した走行) | PASSED |
| `mutation-ledger.json` | 2 回目 (m14 の負例追加とフレーク堅牢化の後) | PASSED |

## 1 回目 — KILLED 3 / MISMATCH 6 / SURVIVED 1

- **MISMATCH 6 件 (m02 / m05 / m07 / m11 / m13 / m19) はいずれも KILLED である。**
  親が登録した期待 node が実測より狭かった (m02 は 4 件と書いたが実際は 39 件が赤、m19 は
  6 param すべてと書いたが実際に落ちるのは `null` 枝の 1 件、m05 / m07 / m13 は別の
  invariant / 履歴テストが先に撃った)。受理集合は期待どおり fail-closed 側へ動いている。
- **SURVIVED 1 件 (m14) は真の検出漏れだった。** 注入実在は harness の injection diff で確認済み。
  既存テストは `successor is None` (相互に異なる改訂) しか撃っておらず、「一方の親の状態が他方の
  後継であるが merge commit 自身の状態がその後継と一致しない」枝が無検査だった。
  `DW-M02` に従い実効 gate へ再照準し、単一理由の負例
  `test_successor_merge_rejects_merge_commit_with_different_state` を追加した (実装は不変)。

## 2 回目 — KILLED 7 / MISMATCH 3 (実質 KILLED 10)

| 変異 | status | 実測 |
|---|---|---|
| m01 (`all` → `any`) | KILLED | 48 node |
| m02 (非 UNSATISFIED を充足扱い) | KILLED | 39 node |
| m05 (保護 hash から §5 欄名を除く) | MISMATCH | 同一テストが赤。node ID に xdist group 接尾辞 `@s8c-preregistration-candidate` が付いたための表記差 |
| m07 (保護 hash から規範本文を除く) | MISMATCH | 6 node が赤 (期待 5)。増分は m14 用に新設した負例と、上と同じ group 接尾辞 |
| m08 (`supersedes` 検査の無効化) | KILLED | 1 node |
| m11 (裁定見出しを字面一致へ緩和) | KILLED | 3 node |
| m13 (core blob 一致検査の無効化) | KILLED | 1 node |
| m14 (merge 後継判定の緩和) | MISMATCH | **新設した単一理由の負例が撃った**。旧 2 テストは設計どおり不発 (別枝を見ているため) |
| m19 (§5 の `null` 拒否を無効化) | KILLED | 1 node |
| m20 (充足可能述語の negative control 必須を外す) | KILLED | 1 node |

**erratum:** 期待 node をこの実測へ合わせて 3 回目を走らせれば `MISMATCH` は消えるが、
得られる情報は同じであるため走らせていない (実験スケールを無造作に増やさない)。
本書がその突合の記録である。
