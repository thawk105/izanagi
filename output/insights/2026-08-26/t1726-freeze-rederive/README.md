# 受入 receipt verifier の freeze 再導出昇格 — 逐語凍結と実測

authority: none
default_effect: no-state-change

wave: `dev-wave-t1726-freeze-rederive` / base main `33cb632164575ddead33e9af2d9d048dc106d811`
実装 commit: `689063256e582e6c3a77df45c9449270108a2323`

可変状態の正本は worklog 末尾と現行 phase doc であり、この文書はプロセス監査用の凍結スナップショットである。

## 何を直したか

`orchestrator/campaign/s8c_acceptance_receipt.py` は receipt・trial report・attempt journal の
run-start を互いに突き合わせるだけで、凍結された条件を一度も読まなかった。
nested condition・cell・descriptor を同じ誤値で自己整合させた receipt を H1 として通せる。

v2/v3 の検証経路へ `[receipt-freeze-arm-binding]` を新設し、
ratified legacy freeze から条件を再導出して照合するようにした。

## 訂正した親の前提 (段 3 の敵対相談が実測で覆した)

- **成果物影響は親 brief の記述より小さい。** 現 checkout では全 receipt が構造的に
  `certifying=false` へ固定され (`s8c_acceptance_receipt.py:393-396`)、
  `layer3_report` は `certifying is True` を要求する (`layer3_report.py:623-624`)。
  よって誤値 receipt が現在の certified 選択や論文数値を決める到達可能経路はない。
  穴は潜在的であり、certifying を有効化する将来世代で発火する。
- **段 2 のプランは実装不能だった。** ratified legacy freeze を検証対象 repository から読む設計は、
  凍結 artifact を複製しない正当な receipt 生成経路を `legacy-read` で拒否する。
  権威 root を verifier 自身の checkout へ分離して回避した。
- **追加予定の照合 1 本は恒真だった。** expected arm binding digest の照合は、
  既存 gate と expected content digest 一致から決定論的に従い、受理集合を 1 bit も狭めない。
  足さない裁定にした。

## scope 外として裁定パッケージへ回した real 所見

- receipt が名乗る `measurement_head` が ancestor / registry 記録 head へ束縛されていない。
  本 wave の条件再導出は measurement_head に依存しない — on/swapped は commit を使わず、
  off は commit 先の bytes が in-source 期待値と一致しなければ落ちる — ため、
  別 commit を選んでも誤条件は通らない。provenance の穴であり別軸。
- `cells=[]` と C02 reason 保持の組み合わせで、実行 descriptor が不在のまま
  expected digest の自己申告を verified receipt にできる。
- 発行側 `trial_registry` の受入経路にも同じ authority 断絶が残る。
  producer / issuer / verifier が共有する軽量 authority leaf の新設が要る。
- `VerifiedAcceptanceReceipt` は公開 dataclass で seal も引数のため gate 外で生成できる。
  ただし唯一の consumer は `require_current_verified_receipt` を通し、
  同関数は再検証結果 `current` を返すため偽造した中身は届かない
  (`s8c_acceptance_receipt.py:1188-1193`)。本 wave 由来でもない。

## 親が実測した値

| 対象 | 値 |
|---|---|
| `import s8c_acceptance_receipt` 単体 | 0.034s / `sys.modules` 105 件 / stdlib のみ |
| lazy 連鎖 (v2/v3 検証時のみ) | 0.334s / orchestrator module +36 |
| 変更 test file 単独走 (fix 前) | 19 passed / 4.17s |
| 変更 test file 単独走 (fix 後) | 23 passed / 3.90s |
| consumer 焦点走 5 file (fix 前) | 410 passed / 42.48s |
| consumer 焦点走 5 file (fix 後) | 410 passed / 31.99s |
| `check_ai_provenance.py` | 5960 件・新規違反なし |

consumer 焦点走の対象は変更 production module 名で `orchestrator/tests/` を引いた参照関係で決めた
(`test_s8c_acceptance_receipt.py` / `test_layer3_report.py` / `test_trial_registry.py` /
`test_ccbench_spawn_sites.py` / `test_reflux_originless_compatibility.py`)。

## 子の工数

codex 9 本、すべて `launcher_rc=0`・`gpt-5.6-sol`・`effort=xhigh`。
model call は plan 21 / consult 14+32 / author 51 / review 8+28 / focus 14 / fix 23+8。

段 5・段 6 の実装子と fix 子はいずれも pytest を実走できなかった
(Pegasus dispatch `rc=16`、login node の cgroup 上限)。実走はすべて親が代替した。

## 変異 matrix

**baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0・TIMEOUT 0。**

spec は `mutation-spec.json`、本走の台帳は `mutation-ledger.json`、
probe 巡の台帳は `mutation-probe-ledger.json`。
probe 巡 (全件 SURVIVED 期待) で観測 node を実測してから、その完全集合で本走した。
期待 node を手で書かず実測から採ったのは、呼出し回数を数える種類の test による副次 kill を
取りこぼさないためである。

| 変異 | 落ちた node 数 | 期待との一致 |
|---|---:|---|
| M1 条件再導出の照合を無効化 | 1 | 一致 |
| M2 legacy entry の key 集合 assert を無効化 | 1 | 一致 |
| M3 derangement の exact 比較を無効化 | 1 | 一致 |
| M4 binding の measurement_head 比較を無効化 | 1 | 一致 |
| M5 権威 root を検証対象側へ戻す (過剰拒否の対照) | 15 | 一致 |

`M5` は受理集合を縮小する wave に要る**過剰拒否の対照**である。
権威 root を検証対象側へ戻すと、段 3 が名指しした編集禁止の正例
`test_trial_registry.py::test_p5_six_complete_terminal_reports_pass_acceptance` を含む
15 node が落ちる。現設計がその落とし穴を実際に回避していることの実測裏付けになる。

`M2` は正規 loader と hash 固定の下では発火しない **verifier authority drift gate** であり、
receipt 受理集合の検出力ではない。`DW-M08` の diagnostic sensitivity pin として別枠で数える。

## 逐語

`verbatim/` に段 1〜段 6 の子成果物 11 本を凍結した
(brief / plan / 敵対相談 2 / 裁定 / 実装 / レビュー 2 / fix 2 / 焦点再レビュー)。
placeholder `{{` と結合用ダイアクリティカルマーク U+0300 台の走査は 0 件。

## 運用で踏んだ罠

- 変異 harness の共有木事後検査が `rc=125` で落ちた。観測 root に共有 checkout
  `/work/1/SFC/tanab/izanagi` が入り、走行中に別 wave が触れたためである。
  `--source-repo` へ独立 clone を渡して構造的に断った。
- その clone の submodule 初期化は `protocol.file.allow` の既定で拒否される。
  local path を URL にする場合は `-c protocol.file.allow=always` が要る。
- 収集段が `rc=16` (`receipt scheduler_logs.stdout.path がない`) で落ちた。
  同時刻の `qstat -Q` は gen_S に 101 件 (QUE 35 / RUN 47 / HLD 17)。
  変異ではなく scheduler 混雑であり、`--resume` で再開した。
