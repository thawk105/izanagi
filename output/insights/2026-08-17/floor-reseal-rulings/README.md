# 床値 再封印の残る裁定を実装した — 材料 (2026-08-17)

wave = `dev-wave-t1218-floor-reseal-rulings` / branch `worktree-dev-wave-t1218-floor-reseal-rulings`

[T-1218] の実装 wave の一次資料。裁定の逐語控えは
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full3-28rulings.md` の第 6 項。

## 裁定と、この wave が実装したもの

裁定 = **案 3 (pin を進めれば新しい組で測り直せる) を採り、「環境契約 1 世代につき床値 1 件」の
機械化は入れず、versioned artifact を `FROZEN_MANIFEST` へは載せない**。

実装は次の 2 点だけである。

1. D444 決定 5 (target の `contract_sha256` が組 index に既出なら発行を拒否) を、
   index 不変条件 (`_index_protocol_record`) と issuer (`_reseal_protocol_at_root`) の両方から撤去した。
2. issuer に**組単位の発行前拒否**を置いた。target 組が走査済み index の key に既出なら、
   create-only writer を呼ぶ前に拒否する。artifact を作らないため、
   D444 決定 7 の「取り除くまで発行できない」文言は載せない。

`resolve_current_floor_protocol`、`FROZEN_MANIFEST` (23 key)、既存の凍結 bytes、
凍結チェーン検証の保留状態は 1 文字も変えていない。**実 artifact の発行も行っていない。**

## 段 1 の実測 (すべて read-only、実装差分ゼロ)

| # | 実測 | 値 |
|---|---|---|
| M-A1 | floor protocol index の件数 | 1 (legacy anchor `output/s8b-freeze/floor_protocol.json` のみ) |
| M-A2 | 封印済み protocol の組 | contract `e576e9cd…e242c01` / pin `d706650c…b40969` |
| M-A3 | HEAD gitlink (`external/ccbench`) | `511c9538…3b706ec` |
| M-A4 | 現行 env 契約 (`pegasus`) | `e576e9cd…e242c01` (封印時と同一) |
| M-A5 | `resolve_current_floor_protocol()` | legacy anchor を解決 (今日 PASS) |
| M-A6 | 案 3 の実行形 = (M-A4, M-A3) の組 | contract 据え置き・pin 前進 → D444 決定 5 が両方で拒否 |
| M-A7 | resolver の production consumer | `certified_writer_admission._admit_floor` |

**M-A6 が撤去の必要性の実測である。** 契約単位の封鎖は、裁定が採った案 3 の唯一の実行形を
機械拒否していた。撤去しなければ床値 protocol を今後 1 件も発行できない。

## 親が自分の案を撤回した経緯

段 1 の親案 (P1) は「resolver を『現行 (contract, HEAD pin) の組を優先し、無ければ現行 contract 単独
一致へ fallback』へ変える」だった。段 3 のレンズ A が blocker 2 件で NO-GO とし、親が一次資料で
裏を取って**段 4 で撤回した**。

- **D460 が禁じている。** D460 本文は resolver を「現行 env 契約の contract hash に一致する record を
  exact 1 件」と定め、理由節に「**選択条件に ccbench pin を入れてはならない**」と明記する。
  T-1218 の裁定は D444 決定 5 を落としただけで D460 には触れていない。
- **fail-closed より悪い状態を作る。** 実 driver `tools/pegasus/floor_campaign.sh` は固定 legacy path を
  `--protocol` に渡す。pin 優先 resolver を先に入れると、admission は versioned protocol を authority と
  して PASS し、実測は legacy protocol で走る **authority 分裂**が起こりうる。
- **所有が別タスクにある。** 2026-08-17 01:09 JST 着の裁定で、shell 層・driver 層の配線は [T-419] (3)、
  実凍結は [T-1255] と決まっている。

段 3 のもう 1 件の blocker (contract gate を丸ごと消すと組単位の発行前拒否まで失われる) も採用し、
狭い発行前拒否へ置換した。

## 敵対検証の結果

| 段 | 子 | 判定 |
|---|---|---|
| 段 3 | レンズ A (正しさ防壁) | NO-GO (blocker 2) |
| 段 3 | レンズ B (裁定整合・実効性) | GO (blocker 0、minor 3) |
| 段 6 | レンズ C (裁定との乖離・gate の歯) | **GO (所見ゼロ)** |
| 段 6 | レンズ D (回帰・波及) | **GO** (major 1 = 段 4 記載の既知残件と一致) |

段 6 の両レビューが独立に同じ順序制約へ到達した — **実 artifact の発行は consumer 配線より
先に行ってはならない**。レンズ D は `scan_floor_protocol_index` の全 consumer を辿り、
fail-open が 1 件も無いことを確認した。

## 変異 matrix

`mutation/` が正本。runner scope = `test_s8b_protocol_builder.py` + `test_s8b_floor_contract.py`
(`--force-dispatch`、`-rf`、dispatch runner)。

- **probe 走**: baseline PASSED、6 変異すべて赤、期待 node の完全集合を観測した。
- **本走 (round1)**: baseline PASSED、**KILLED 6 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0**。
  期待 node と完全一致。

| ID | 変異 | 期待 node 数 | 結果 |
|---|---|---|---|
| M1 | index へ contract 単位拒否を再挿入 | 2 | KILLED |
| M2 | issuer へ contract 単位拒否を再挿入 | 3 | KILLED |
| M3 | 組単位一意性を削除 | 1 | KILLED |
| M4 | 発行前 pair 拒否を削除 | 2 | KILLED |
| M5 | create-only writer を上書き可にする | 2 | KILLED |
| M6 (正例) | 発行前 pair 拒否を常時発火にする | 14 | KILLED |

M6 は過剰拒否の検出力を示す正例である。M3 と M4 が別々の層を守っていることは、
失敗 node 集合が重ならないことで確かめた。

## 親の実測

| 走行 | 結果 |
|---|---|
| 焦点走 (`test_s8b_protocol_builder` / `test_s8b_floor_contract` / `test_s8b_floor_campaign` / `test_frozen_artifacts`) | 466 passed, 4 skipped, 0 failed (397.30 秒、bounded local) |
| 床値 admission 回帰 (`test_campaign.py -k floor`) | 4 passed (計算ノード、request 914609.nqsv) |
| 全史 AI provenance 監査 | rc=0、3803 件、新規違反なし |

床値 admission 回帰は bounded local で 2 回とも `rc=16` (cgroup の memory.max を走行中に attest
できず scope 停止) になった。**テストの赤ではなく基盤の失敗であり、テストは 0 件実行されていない。**
`--force-dispatch` で計算ノードへ回して緑を得た。

## 残る限界 (land しても閉じていないもの)

1. **同一 contract の record が 2 件ある状態が到達可能になった。** その状態では
   `resolve_current_floor_protocol` が `count=2` で fail-closed になり、床値 admission が止まる。
   D460 の却下理由が前提にしていた「production では到達不能」は本 wave 以後は成り立たない。
2. **したがって実発行 ([T-1255]) は consumer 配線 ([T-419] (3)) より先に行ってはならない。**
   先行させると床値 submit の受理集合が空になり、pilot result・レポート・試行台帳が新規生成されなくなる。
3. 削除すれば同じ組を再発行できる (履歴不変条件の検査は凍結チェーン保留の対象)。
4. protocol 単位であって run 単位ではない ([T-1140] 問 1 が係属中)。
5. ratified pointer は sanctioned namespace 外を指せる ([T-1216] が所有)。
