# 逐語の defang と正規化 (DW-S07 / D88 (6) と同型)

本 dir の file は probe の実走出力と子の報告の**原文**である。編集は下記の defang 1 種だけで、それ以外は 1 byte も変えていない。

## defang 契約

三軸語 (holdout の未既知性検索) は rratio / skew / rmw の canonical encoding が**同一 file 内で conjunction** したときに 1 hit と数える。
`probe-ledger.md` は、標本 wave の 1 つ (t2810) が job dir に残した三軸語走査 log の JSON を「証拠行」として引用しており、その中に 3 軸の正規表現がそのまま入る。
そのまま凍結すると DW-S07 の gate が自己発火するため、次の規則で可逆に無害化した。

- **置換規則:** 三軸 key (`ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw`) の直後の半角 `=` を全角 `＝` へ 1:1 で置き換える (可逆、可視文字は key と値を保つ)。
- **置換箇所:** 合計 9 箇所 (`ycsb_rratio=` 3、`ycsb_zipf_skew=` 3、`ycsb_rmw=` 3)。

| file | 生成元 | 原文 SHA-256 | 原文 bytes | defang 後 SHA-256 | defang 後 bytes | defang 箇所 |
|---|---|---|---|---|---|---|
| `probe-ledger.md` | `probe/login_check_event_ledger.py` の実走 (as-of 固定、`probe-out/f2/ledger.md`) | `dfef738c3875636ff09f0b2c4d46c7aab8cbf34401c7377bc459575b68bfd814` | 1,118,497 | `ae9d6f79a6213a0264489fdea61e1287f0762acc72d3c41b3992d7dcea339c67` | 1,118,515 | 9 |
| `probe-receipts.md` | `probe/login_check_receipt_replay.py` の実走 (`probe-out/fa/receipts.md`) | `dbfa2154eb740dc3045c38390e76cb42e1be16cb10546e2a955732e80bbcc84a` | 620,080 | 同じ (未編集) | 620,080 | 0 |
| `probe-waves.jsonl` | 同 ledger の wave 同定 (`probe-out/f2/waves.jsonl`) | `7dba8269e4f613d37cd9bc9ea96c13ab5ada226bad7a15f551afbb80d8cc5ce9` | 15,414 | 同じ (未編集) | 15,414 | 0 |

**復元法:** `probe-ledger.md` の `ycsb_rratio＝` / `ycsb_zipf_skew＝` / `ycsb_rmw＝` を半角 `=` に戻すと原文 SHA-256 に一致する。原文そのものは job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall/probe-out/f2/ledger.md`) にも残してある。

**defang 後の機械確認:** `python3 -m orchestrator.campaign.s8b_holdout_freeze search` を再走し、`conjunction_hits` から本 dir の file が消えたことを確認した (hit は main に着地済みの既存 4 file だけ = D2120 項 2 (d) の既知の帰結、rc=1)。走査 log は job dir の `verbatim/axis-scan-prerecord.log` (defang 前、hit 5 件) と `verbatim/axis-scan-after-defang.log` (defang 後、hit 4 件)。

## その他の正規化

- 行末空白の正規化は下節のとおり 1 file に当てた。

## 行末空白の可逆最小正規化 (DW-S07)

codex の報告は Markdown の改行のために行末へ半角空白 2 つを置く。`git diff --check` が抵触するため、
**行末の空白と tab を削る**最小の正規化を 1 回だけ当てた (可視文字は不変、削った位置は行末のみなので復元は「該当行の末尾に空白 2 つを戻す」)。

| file | 原文 SHA-256 | 原文 bytes | 正規化後 SHA-256 | 正規化後 bytes | 変更行数 |
|---|---|---|---|---|---|
| `s3-consult-A.md` | `da295d0236589b90129fc095d3d8e649b61d959611859a1d5b91a736ab59a91c` | 18,911 | `5bda3c7f765e04a286548864262b5ac94618f40a68855e8fcffc7ca3efc37f7f` | 18,835 | 38 |

原文は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall/codex/s3-consult-A.md`) にそのまま残してある。他の verbatim file は行末空白がなく未編集である。
