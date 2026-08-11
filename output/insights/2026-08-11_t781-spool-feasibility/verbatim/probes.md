# probe の所在と bytes 同一性 (repo 外)

probe script は repo へ入れない ([T-317] 裁定 — repo へ入る probe は実装面であり Codex `role=author`
が要る。repo 外の運転 script・probe は親が書いてよい)。所在と SHA-256 だけをここへ凍結する。

置き場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/`

| file | sha256 | request | 実行ノード |
|---|---|---|---|
| `t781_spool_probe.sh` | `f60d3ce8510b894264ab3b3753b2c804a6fbfaae6511956b164e1f4360ff7b2c` | 901499 | bnode042 |
| `t781_held_probe.sh` | `cf42e5948a95352b2de011680a67ba42ae920b3e7dbc1f84ba96ce68cd8ae4fa` | 901501 | (hold → 解除後に実行) |
| `t781_probe2.sh` | `57e908968e5381026450446ad3eb6f1c2a8510f5ab68358e615c5864d9bf8a52` | 901512 | bnode046 |
| `t781_probe2_body.sh` | `b59ae38195f9a31c59bd06132e0210ac143046cb40573af761c008bcc0664e9b` | (901512 が exec する本体) | bnode046 |

## bytes 同一性の実測 (M3 / M11 の一次証拠)

- 901499: 投入 file 2031 bytes / `f60d3ce8…`。
  計算ノードの JSV copy `/var/opt/nec/nqsv/jsv/jobfile/0.901499.10/user_script` = 2031 bytes /
  **`f60d3ce8…` (完全一致)**。`qcat -i -b -n 100000` = 2032 bytes (末尾 `\n` 1 個追加)。
  `head -c 2031` した bytes の sha256 は投入 file と一致。
- 901512: 投入 file 357 bytes / `57e90896…`。JSV copy = 357 bytes / **`57e90896…` (完全一致)**。
  `qcat` = 358 bytes。
- 他 wave の dispatch script (901498): 投入 file 2077 bytes、`qcat` = 2078 bytes、
  先頭 2077 bytes は `cmp` で完全一致。

## 実行しなかった検査

- `user_script` の unlink / 差し替え (破壊的)。**権限層に拒否されたため実施せず、迂回もしていない。**
- `qattach` による実際の command 注入。属性 `qattach command = Enable` の実測にとどまる。
- 真正 job 内での兄弟プロセス起動実験。静的な脅威モデル分析のみ。
