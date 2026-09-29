## 所見対応表

| 所見 | 状態 | fix 後の根拠 |
|---|---|---|
| A1 合否と分類の二経路 | **closed** | [起動器:952](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:952) で BCV の合否を `bcv_stock_checks` に統一し、[同:977](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:977) で run error・verifier error・returncode を確認する。「巡回なし」も [同:1024](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1024) で `stock_pass` を通る。 |
| A2 巡回 stock の分類欠落 | **closed** | [起動器:1036](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1036) に専用分類があり、[同:1260](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1260) で保存済み witness の参照先を記録する。診断異常は巡回分類より先に判定され、R6 の扱いに沿う。 |
| B3 追加 run の例外による元 record 消失・commit 不明での追加 | **closed** | [起動器:1272](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1272) は整数の commit 数が 1,000 未満のときだけ追加する。元 record は [同:1437](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1437) で先に保存され、追加 run の例外は [同:1294](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1294) で別 key に入る。 |

### C1 stock の分類が指定された四分類を尽くさない

**重大度:** should
**根拠:** [起動器:1024–1041](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1024) は合格・診断異常・巡回検出・不成立のほかに「不合格」を返す。例えば integrity 数値が非 0 で診断値が 0 の run はこの第五分類になる。
**放置時の影響:** 一次資料で「不合格」をどう扱うかが未定義になり、巡回を伴う integrity 異常も巡回分類に入り得る。
**推奨対処:** 構造的な検査失敗を「不成立」に割り当て、巡回分類に必要な integrity 条件を明示する。

### C2 B2 の不採用根拠は fix 後の L0 に引き継げない

**重大度:** should
**根拠:** J1 は L0 と重なる W4 cell を [起動器:153–160](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:153) で固定的に除外する。親裁定が引用した 52,899・32,799 commit は **fix 前** の [L0 要約](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/l0-result-summary.md) の値であり、投入済みの fix 後 L0 の結果は未着である。
**放置時の影響:** 取り直した L0 の該当 run が 1,000 commit 未満なら、R4 の第二尺度が欠落する。
**推奨対処:** fix 後 L0 の二つの W4 commit 数を確認し、該当時は元 run との対応を保存して tuple 1,000 を追加する。

## 総括

- 差分上、build 束縛、FLAGS 照合、診断行の厳密な parse、正例の帰属と stock 対照、既存 md_3 / md_17 job の経路は変更されていない。
- 診断行の欠損は [起動器:360](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:360) で例外となり、新たに 0 と扱う経路は見つからなかった。
- B1 は、段 6 裁定が記す段 5 の再走許可が有効なら不採用でよい。コード上も同一 job の対照 run を名指しする。
- B4 は親が J2 投入前の計算を担うという裁定として整合する。B5 の保留も J1 のメモリ実測待ちとして妥当である。
- **現時点では、四分類に従う確定的な実走結果の記録には使わない。** C1 を解消し、fix 後 L0 の結果で C2 を判定する必要がある。build・実走の成否はこの静的検査では確認していない。