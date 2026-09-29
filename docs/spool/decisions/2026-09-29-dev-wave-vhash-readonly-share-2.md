---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-readonly-share
seq: 2
---

## {{D:vhash-readonly-share-decomposition}}. read-only tx の影響を、条件間の総差と観測走の時刻分割の 2 本で測り、どちらも因果の内訳と呼ばない

**決定:**
- Cicada の read-only (ro) tx の比率を、YCSB の読み比 (ro は読み比の 10 乗で間接に決まる) ではなく、計器 patch 内の実行時 flag `izanagi_ronly_pct` (既定 −1 = 生成のまま、新しい手続きの初回 `begin()` だけで抽選) で独立に動かす。長い tx の worker の種別も `izanagi_long_kind` で update / ro に固定する。新しい macro は作らず既存 2 macro の下に置く。
- 回収境界の遅れの分け方を、(i) D-F = 条件間の総差と交互作用 (Lag(r, L) − Lag(r, none) − Lag(0, L) + Lag(0, none))、(ii) D-C = 観測走の公開間隔を「最後の flag 機会まで・ro が flag を上げない分・公開検出まで」に分ける時刻分割、の 2 本にする。前者は ro 比率を上げると update 数・版の生成・abort も変わる総差、後者は介入の模擬ではないので、どちらも「ro のせい」の因果的な内訳・境界の前進量とは書かない。
- forwarding を ro に許した場合の見積りは「観測鎖・先頭 K 版・既読区間に限定した楽観的適格率」と呼び、固定 snapshot の要否の割合 f との関係は独立を仮定した感度曲線として示す。上限とは書かない。
- 計器の公開ごとの記録は、事象の時点の公開世代で slot に書き (tx の begin 時点で固定しない)、全 flag が立っているのを leader が採取したら公開の前に世代を進める。遅れて揃った公開は検出時に 1 つ進め、別計数する。
- `patches/ledger.json` には entry を足さない (D18 第 4 類の ability probe 専用で entry 数 1 を要求する)。`patches/README.md` の既存 entry を更新する。

**理由:**
- md_2 の A (skew 0・読み 50%) と B (skew 0.9・読み 95%) の比較は skew・読み比・ro 比率を同時に変えていた。本 wave の読み比 50%・ro 0% の対照では skew の差だけで同じ境界年齢の bucket 差が出た (一次資料 `output/insights/2026-09-29/vhash-readonly-share/README.md` §6.1)。軸を独立にしないと主因を取り違える。
- 段 3 相談と段 6 レビューが、恒等式で閉じる分解や楽観の見積りを因果・上限と読ませる危険を指摘した。
- 計器の世代を begin 時点で固定した版は、smoke の短い走で公開間隔の 60〜84% を「世代不一致」で除外した ({{F:vlife-generation-fixed-at-begin}})。

**却下した選択肢:**
- ycsb_rratio を変えて ro 比率を動かす — update tx の形も同時に変わる。
- ro commit に実際に flag を上げさせる診断 build で (b) を直接測る — 依頼が「実装はしない」とした。正しさ (固定 snapshot の意味・GC の安全) の検討なしに有効化しない。
