---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2043-floor-receipt-observe
seq: 1
title: [T-2043] 床値 pilot を現行 main で 1 回投入し、受領書発行段が v3 の記録形で通ることを実機で観測した (insight のみ、branch worktree-dev-wave-t2043-floor-receipt-observe、実装面 0・変異 matrix 免除)
---

## 本文

- 一次資料は `output/insights/2026-09-01_t2043-floor-receipt/`。証拠 bundle は repo 外の
  `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2043-floor-receipt/evidence-bundle-965563/`
  (913 file・61703452 bytes、file ごとの sha256 付き構成 manifest)。
- **request `965563.nqsv`、mode pilot、source commit `3c1156056`、Elapse 3096 秒。**
  12 cell・96 session・除外 0 件で `driver_rc=0`、journal terminal `completed`。
- **依頼文の前提が 2 件、実測で覆った。**
  - 依頼は `dev-wave-t1942-floor-gate-recheck` を稼働中として編集面の重複検査を求めたが、
    **同 wave は着地済み**であった (entry 1151)。branch も worktree も残っておらず、重複はゼロ。
    代わりに同 wave が残した D1396 / D1397 / D1398 を制約として引き継いだ。
  - 依頼は「残るのは床値 job を 1 回投入して発行段を通す観測」と書くが、**発行段そのものは
    本日 11:30 に完走した `964035.nqsv` で既に通っていた**。未観測だったのはより狭く、
    **[T-2027] が入れた schema v3 の記録形で通すこと**である。964035 は v2 であり、
    根クラス 2 の 7 件を job id 入り path で記録していた。依頼の結論は正しく、理由が違った。
- **親の provisional 裁定が 1 件、投入前の実測で覆った。** 当初は dev-wave の作業木から投入する
  つもりだったが、`floor_campaign.sh` は job 開始時に投入元の HEAD が受領書の `source_commit` と
  一致し `output/` を除く作業ツリーが clean であることを要求する。投入から起動まで 26 分あり、
  その間その作業木では記録 commit を打てない。投入は使い捨ての作業木から行い、記録と land は
  wave の作業木で行う形へ分けた。
- **判定基準は結果を見る前に handoff へ固定し、緩めずに適用した。** 4 条件すべて PASS。
  不通過の述語 `external compiler input is unavailable` は走行証跡に 0 件。
  `floor-driver / run-linked` を単独の合格条件にしない前 wave の注意も引き継いだ。
- **主張しないこと (insight §「主張しないこと」に同じ)。** cross-job の再束縛は D1220 の限界に
  より閉じない。v3 manifest の job またぎの安定性も測っていない (比較対象が v2 で schema が違う)。
  official 走行の起動可否は動かしていない (D1396)。`eligible_for_refreeze` は `False` である。
  床値は結線された最小相対床 0.030 に一致しており、較正済みの床ではない。
- **投入経路で 1 件つまずいた。** `submit_floor.sh` は third-party staging root を消費するが
  自分では作らない。新しい作業木では `--dry-run` が rc=0 でも実投入が qsub 前に落ちる。
  `fetch_third_party.py hydrate` で解消した。この罠は本日 `tools/pegasus/README.md` へ
  追記されている (`6398dcd2d`) が、**床値の投入手順そのもの** (`docs/phase3-8b-restart-runbook.md`
  W-2) には無いままで、手順を正本として辿ると踏む。本走行が 3 例目のため、
  段 8 で同節へ前提物を 1 行足した。
- **待ち手を 1 本、自分の判定式の誤りで空転させた。** `qstat <id>` は request 不在でも
  rc=0 を返し「does not exist」を出力する。rc で終端を判定したため、job が 22:15 に終わった後も
  待ち手は回り続けた。実害は待ち時間だけで、成果物と判定には影響しない。
- 子は 1 本も起動していない。設計択一が割れず、正しさ防壁に触れず、受理集合を変えないため
  `DW-C00` の軽量版とした。実装面の差分はゼロで `DW-S04` に従い変異 matrix を免除した。
  受入全走は免除していない。
- F49 (ii) の有効性検査 3 点はすべて成立した (計算ノードが書いた checkpoint の実在、投入時の
  `qstat` 可視、PBS 会計 Elapse 3096 秒・ポイント 13126.50 → 13123.77)。

## 次の一手差分

### 完了

- [T-2043] 床値 job が binary admission receipt の発行段で落ちる赤は解けた。[T-2027] の
  schema v3 が根クラス 2 の 7 件を `dependency-prefix` 根へ移し、本 wave が現行 main から
  投入した `965563.nqsv` が 12 cell すべてで発行段を通ることを実機で確かめた。
  remaining: none
  base: 82553a2fa2061ab9d8cb13511c6e9e3a033b19768f7a288bad27c03779e7d24b
