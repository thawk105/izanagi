# [T-139] R4 環境 probe — 段 1 brief

```text
authority: none
default_effect: no-state-change
```

## 確定済みユーザー裁定 (逐語裏取り済み)

`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §47 (2026-08-08「推奨通りで」):
**R1〜R7 全問推奨どおり + 凍結は段階 1 のまま probe 後一括再提出**、
**R4 (a) gen_S 環境 probe 先行・導出写像を先に凍結**、**→ 環境 probe wave が起票可**。

## scope (成果物影響つき、`DW-G05`)

**IN**

1. **導出写像の凍結** (docs、probe より前に commit)。入れないと実測後の裁量が入り、
   `a03` の許容範囲が「観測に合わせて選んだ値」になる → 恒真化禁止 (core §14) に抵触し、
   pilot の受理集合が事後選択で決まる。
2. **環境 probe の実装** (`.sh` + `.pbs` + admission registry entry + test)。入れないと
   `a03` を支持する測定が 0 件のままで、`[0,1.0]` の可否が実走で初めて判明する
   (外れれば割当て 2〜26 本を失う)。
3. **gen_S での 1 本実走と実測** — (i) 待機 30 / 60 秒末尾 10 秒の `/proc/stat` counter、
   (ii) `CCBENCH_TRACE=1` build が通る witness、(iii) compiler の realpath・`--version`・bytes digest。
   (ii) が無いと検証割当て (trace-enabled build) の成立に先例が無い。(iii) が無いと `a08` の
   compiler identity が数値で pin されず、build identity の exact 比較が発火しない。
4. **追補 A の再発行** (`a03` の許容範囲を実測確定、`a08` へ compiler 期待値を追記)。
5. **erratum・record-items の整合再確認**と、**凍結承認パッケージの再提出** (段階 1 のまま)。

**OUT** (裁定済みの境界)

- fold・凍結・発効 (ユーザー承認へ返す = 本 wave の終端)。
- producer / resolver / validator / consumer の実装、機械可読 schema の発行 (R6 = producer wave)。
- exec broker (R7 = (a) 予備置換なし)。
- 凍結 core の編集 (bytes 不変)。

## 不変条件

- **導出写像の凍結 commit は qsub より前**。順序を worklog へ実行順で記録する (`DW-O12`)。
- 凍結 core `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` の bytes 不変。
  実測: sha256 `ac939af4…` が作業木で一致、fold commit `88d68f91` 実在。
- **probe は本 study のデータではない** (`DW-G01` 生死実験先行)。事前登録を汚さない。
  probe の出力を pilot / 本走の raw として使わない。
- **規律 1**: `CCBENCH_TRACE=1` build は「通るか」の witness であり、性能値を取らない。
  性能側の観測は trace-disabled build でのみ行う。
- 段階 1 (承認待ち) で終える。

## 実測済みの前提 (brief 前、`DW-S01`)

| 前提 | 実測 |
|---|---|
| 既存 36 行は `load1` であって `/proc/stat` ではない | `limited-screen.tsv` の列 = `run/pre_load1/post_load1/pass`。**確認** |
| 既存 probe は待機を置いていない | `t139_positive_control_probe.sh` に `sleep` の hit **0 件**。**確認** |
| 既存 probe の build は TRACE=0 | `COMMON` に `-DCCBENCH_TRACE=0` 固定 (394 行)。**確認** |
| `/proc/stat` 差分読取の既存被覆 | `t419_probe_causality.py` に per-CPU 差分・減少検出が実在 (再利用先)。`a03` は集計 `cpu` 行を使うので**純増**は「集計行 + 窓長検査 + 8 列固定」 |
| 新 probe は hook の admission 対象 | `tools/pegasus/admission_registry.json` (29 entry) と test の `_PEGASUS_EXPECTED_CLASSES` の**両方**に entry が要る。`qsub`/`qstat`/`qdel` は sanctioned head |
| 待機秒数 / driver | `a02` = arm 間 30・block 間 60。`a07` = `thread_num=48 -extime=3` |
| gen_S | 21 本実行中・専有保証なし (`Exclusive submit = OFF`)。1 CPU / 48 physical core / HT 無効 |

## provisional 裁定 (親の暫定。**攻撃対象**)

- **(P1) 導出写像。** 全観測窓の最大値を `U` として
  `上限 = max(1.0, ceil_{0.1}(U) + 0.5)` core-equivalents、下限 `0.0` 固定。
  `上限 > 4.0` になったら**閾値を作らず**、環境不適合として R4 (d) の材料をユーザーへ返す。
  意図: probe は「緩める方向にだけ」働き、既にレビュー済みの `1.0` より厳しくしない
  (静かな 1 割当てを見て締めると 26 割当てでの偽陰性を増やす)。
- **(P2) 代表性。** 観測窓は**先行 run のある待機の末尾**に置く。無負荷の待機だけを測ると
  自 run の後始末残渣が入らず、`U` を過小に見積もる。probe は 48 thread の実 run →
  30 秒待機 → 窓、および → 60 秒待機 → 窓を繰り返す。preflight 相当の窓も 1 つ取る。
- **(P3) 反復数。** 30 秒側・60 秒側それぞれ 6 窓以上。walltime は 1 時間 (既存 probe と同枠)。
- **(P4) compiler digest。** `command -v` → `realpath -e` → `--version` 逐語 → 実行体 bytes の
  SHA-256。`gcc` / `g++` の両方。module 環境を受領証へ逐語で残す。
- **(P5) TRACE=1 witness。** 3 arm ではなく `stock` 1 本で足りる (build が通るかの witness)。
  `CMakeCache.txt` の `CCBENCH_TRACE:STRING=1` / `CCBENCH_ADD_ANALYSIS:STRING=1` を exact 照合する。
- **(P6) 失敗時の終端。** probe が落ちる・窓が malformed・`U` が cap 超過のいずれでも、
  **閾値を推定で埋めない。**未確定のまま理由を書いて承認パッケージへ返す。

## 分割方針

段 2 = codex プラン 1 本。段 3 = 敵対 2 レンズ (統計/受理集合、実行環境/実装)。
段 5 = 実装子 1 本 (probe + registry + test)。段 6 = 敵対レビュー 2 本 + 焦点再レビュー。
**受理集合が変わるため軽量版は採らない** (`DW-C00`)。
