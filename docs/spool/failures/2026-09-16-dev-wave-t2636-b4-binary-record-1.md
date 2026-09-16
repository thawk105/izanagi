---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2636-b4-binary-record
seq: 1
---

## 新規

### {{F:generic-clean-env-drops-calibrated-tool}}. clean 環境の計算ノード投入は較正が束縛する道具を PATH から落とす [計測汚染] [手順漏れ]

- 事象: 既登録の汎用投入器で計算ノードへ build を投げたところ、toolchain preflight が
  `floor-toolchain-receipt-mismatch` で止まった。compiler は path も版数も較正と完全一致していた。
  食い違っていたのは cmake の版数だけで、較正は 3.25.0、job の実測は system の 3.22.1 だった。
- 根本原因: 汎用投入は `env_mode=clean` で `MODULEPATH` ごと環境を落とす。較正取得 job は
  既定 module 環境を持ち、そこが供給する cmake が PATH の先に来ていた。**環境が変わったのではなく、
  同じ機械の同じ道具が clean 環境から見えなくなっただけである。** 3.25.0 の実体は計算ノードにも
  login にも実在し、module file が同じ bin を PATH へ prepend している。
- 恒久対応: {{D:calibrated-toolchain-resolved-by-path-not-by-relaxing}}。実在する道具の directory を
  呼出し引数で受けて PATH の先頭へ置く。一致要求は緩めない。
- 再発検知: 較正束縛のある実測を clean 環境の汎用投入で行う wave は、段 1 で
  **較正 receipt の toolchain 全 leg と job 実測を突き合わせる**。compiler だけを見て一致と結論しない。
  安い probe を 1 本投げれば 10 分で分かる。

### {{F:single-line-failure-class-hides-cause-off-job}}. 1 行の失敗分類名だけが job log に出て、原因は job の外にしか残らない [手順漏れ]

- 事象: 計算ノードで 1 度しか走らせられない実装が落ちたとき、job log に出たのは
  `sort-swo-oracle-infrastructure-unavailable` という分類名 1 行だけだった。実体は
  作業領域へ永続化された private JSON の `floor-toolchain-receipt-mismatch` で、
  親がその file を探し当てるまで原因が分からなかった。分類名は sort 専用の機構を指す語で、
  実際には sort と無関係な toolchain 検査の失敗だったため、誤った方向を示唆した。
- 根本原因: 呼び手が例外を握って分類名だけを出し、その例外が指す診断成果物の所在を出さない。
  診断は書かれていたが、**job の外に置かれたので job log だけを見る人には届かない。**
- 恒久対応: 失敗時に診断 file の絶対 path と、読める場合はその内容を stderr へ出す。
  private JSON の schema と失敗分類は変えない。
- 再発検知: 計算ノードで 1 度しか走らせられない実装を作る wave は、段 5 の実装子契約へ
  「**失敗が job log だけで診断できるか**」を入れる。分類名 1 行で終わる経路を残さない。

### {{F:stale-unresolved-claim-read-as-current}}. 一次資料の「未確定」を現況と読み替え、凍結文書の記入済み欄を確かめなかった [誤前提] [手順漏れ]

- 事象: 段 1 の親 brief、段 2 の plan、段 3 の敵対レンズ 2 本が、**そろって同じ項目を「未確定」と扱った。**
  実際には事前登録 §5 表の 1 行目が既に埋まっており、記入者もレビュー者も記録されていた。
  段 4 で親が現物から拾って閉じたので下流へは出ていないが、**4 者が独立に同じ誤認をした。**
- 根本原因: 先行 wave の insight が「未確定」と書いた**当時の状態**を、現況として読み替えた。
  子 3 者は親 brief の枠を引き継いだため、独立レンズでも同じ誤認が再生産された。
  `DW-S01` は「一次資料の未了項目の前提を実測し」を既に義務づけている。
  **防壁が無いのではなく、守らなかった。**
- 恒久対応: 既存義務のとおり、brief が「未確定」と書く前に、その項目を定める凍結文書の現物を読む。
  入口への明文化は `docs/dev-wave/**` の L1 予算 (10,625 bytes) を 111 bytes 超えるため、
  安全義務を削らずには入らない。D782 の手順で本追記に留める。
- 再発検知: 段 3 のレンズ設計へ「**brief が未了と扱った項目は、凍結文書で実際に未記入か**」を入れる。
  本 wave では 2 レンズとも親の枠を引き継いだので、明示しない限り検出されない。
