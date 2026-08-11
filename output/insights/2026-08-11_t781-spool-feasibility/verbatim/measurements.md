# 実測台帳 (M1〜M14) — [T-781] 案 A 実現可能性

実施日 2026-08-11、Pegasus (login `pegasus02`、計算ノード `bnode042` / `bnode046`)。
値はすべて実物から採取した。probe は repo 外
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/` に置いた。

| # | 事実 | 根拠 |
|---|---|---|
| M1 | scheduler は PBS ではなく **NEC NQSV R1.16** (`/opt/nec/nqsv/bin`)。`/etc/pbs.conf` 不在 | `qstat --version` |
| M2 | **`qcat -i <ReqID>` が spool 済み request script を返す** (自分の request、rc=0) | 901498 / 901499 / 901501 / 901512 |
| M3 | 出力 = 投入 bytes + 末尾 `\n` **1 個ちょうど** (2077→2078、2031→2032、357→358 の 3 例)。先頭部 sha256 は投入ファイルと一致。非 ASCII 保存 | `cmp` / `sha256sum` |
| M4 | 既定は末尾表示。全文には `-b -n <大きい数>` が要る | 最初の取得が末尾のみだった |
| M5 | request 消滅後は取得不可 — `NQSopenjfl: [BSV ENOREQ] No such request.` | 完了済 900530 |
| M6 | **HLD 状態では rc=0 のまま空 1 byte (`\n`) を返す** | 901501 (HLD→QUE で 225 bytes に変化) |
| M7 | `qstat -f` に script bytes・hash・`-v` 環境変数は現れない | 901498 の全文 |
| M8 | `qsub -U k=v` は User Attributes として保持され 40 hex を格納できる | 901501 / 901512 |
| M9 | **`qalter` に `-U` が無い** (`Invalid argument flag: -U`)。一方 **`qalter -N` は rc=0 で成功** = request 名は所有者が事後変更できる | 901501 |
| M10 | 計算ノードで `qcat` が使える (rc=0) | 901499 / 901512 |
| M11 | 実行中スクリプトは `/var/opt/nec/nqsv/jsv/jobfile/0.<req>.10/user_script` に **root:root `-r-xr-xr-x`** で存在し、sha256 は投入ファイルと**完全一致** (+1 byte なし) | 901499 (2031 bytes)、901512 (357 bytes、`57e90896…` 一致) |
| M12 | その親 dir は **`drwx------ tanab SFC`** (sticky bit なし)。所有者は dir に新規 file を作成・削除できる (`touch` rc=0 → `rm` rc=0) | 901512 Q3/Q4 |
| M13 | 計算ノードから **`qstat -f` は正規化 ID (`901512.nqsv`) なら rc=0**。probe 1 の rc=1 は raw `0:901499.nqsv` を渡したため | 901512 Q6 |
| M14 | **job 内から `qstat -f` で User Attributes を読める** (`izanagi_source_commit = 0c336b8e…`) | 901512 Q7 |

## 推論 (実測ではない、と明示する)

- **I1**: M12 より、root 所有 0555 の `user_script` は所有者が unlink して差し替えられる
  (POSIX: unlink には dir の書き込み権限だけが要る。sticky bit なし)。
  **破壊的検査は権限層に拒否されたため実施していない。** 従って JSV 直読経路 (M11) は
  改竄可能とみなすのが安全側であり、独立証拠として使えない。
- **I2**: `qcat` / `qstat` は server へ問い合わせるため、同じ経路の改竄手段は所有者側に無い
  (M9 が示すのは name/stdout path は変えられるが script bytes と user attribute は変えられないこと)。
