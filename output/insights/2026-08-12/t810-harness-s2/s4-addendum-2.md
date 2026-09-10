# 段 4 裁定追補 2 — 子 B の fail-closed 停止 (schema 不足 3 点) + 親起因の語彙不整合

子 B も実装せず停止し、schema への要求 3 点を返した。全点 real と裁定する。
あわせて、親が追補 1 で導入した reason code の綴りが既存語彙と不整合であることを自ら認め、
同じ改訂で正す。**本追補は s4-adjudication.md および追補 1 に対して優先する。**

## 裁定 B-i: node receipt の機械可読 limitation (real・採用)

`preflight.repo_absence` は boolean 4 項目で「検査が通った」しか書けず、s4 裁定 4 が要求した
「共有 mount 上の repo 到達性は検査で消えない」という**残存限界の宣言**を receipt に載せられない。
node-event の envelope へ `limitations` を追加する — exact object、既知 key のみ、値は bool。
初期 key 集合は次の 2 つとする。

- `shared_mount_repository_reachability_not_eliminated`
- `execution_mediation_incomplete` (slice 1 validator が既に返す限界と同名。同じ意味で使う)

## 裁定 B-ii: 測定直前の第 2 process scan を初回と区別して記録 (real・採用)

`start_ack` payload へ `pre_measurement_process_scan` を追加する。形は preflight の
`competing_processes` と同型の生証拠 (プロセス列) に加え、**読取不能を記録できる**こと
(`unreadable` 列: pid と読めなかった項目名を持つ record)。初回 preflight scan とは別 field なので
coordinator は両方を独立に再計算できる。

## 裁定 B-iii: 再走査失敗の reason code (real・採用)

post_release 境界へ `competing_process_detected`、`process_observation_unreadable` を追加する。

## 裁定 B-iv: reason code 語彙を snake_case へ統一 (親起因の欠陥・自己是正)

追補 1 で親が書いた 4 件は kebab-case で、既存語彙 (`start_spread_exceeded` 等) と不整合だった。
子は指示どおり実装したので子の欠陥ではない。次のとおり改名する。

| 旧 (追補 1) | 新 |
|---|---|
| `release-marker-mismatch` | `release_marker_mismatch` |
| `ack-missing` | `ack_missing` |
| `ack-unknown-slot` | `ack_unknown_slot` |
| `ack-duplicate` | `ack_duplicate` |

**coordinator (commit 済み) がこの 4 literal を使っているため、同じ改訂で追従させる。**
所有分離は並列時の要件であり、本 wave は逐次投入なので、この改訂子が schema と coordinator の
両方 (とそれぞれのテスト) を単独所有する。

## 順序の反省 (段 8 候補へ)

段 5 を「schema 先行凍結 → consumer」の順にしたため、consumer が要求する field が 2 度出て
2 度止まった。単位分割としては正しいが、**先行単位の凍結前に全 consumer の必要 field を
親が列挙する工程**が抜けていた。
