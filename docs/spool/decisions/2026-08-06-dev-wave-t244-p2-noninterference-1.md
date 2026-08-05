---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t244-p2-noninterference
seq: 1
---

## {{D:critic-candidate-label-projection}}. [T-244] P2 の critic 境界へ campaign-local pseudonym を置く — U-1〜U-3 の実装可能な中核だけを入れ、origin 束縛と gate 化と artifact 搭載は返す

**背景:** 2026-08-05 の [T-244] P2 wave は「payload を不変に保ったまま書ける検査は字面部分一致
tripwire に限られ、現行 baseline の実漏洩に一度も発火しない」と実測して**実装しない**と裁定し、
択一を U-1〜U-5 として返した。ユーザー裁定は U-1 = (i) critic の候補識別子を origin scope の
不透明 ID へ置換、U-2 = (ii) auditor の diff + digest を明示的 declassification として会計、
U-3 = IR schema identity は emitter source + 32 golden の複合、で確定した。本 D はその実装 wave の
決定を記録する。受理集合 (critic recipient 境界で許される値) が変わるため D96 の手続に従う。

**決定 (1): critic が観測する候補識別子を campaign-local な不透明ラベルへ射影する。**
現行 production の critic は `harness_result.variant` と `critic_digest` の双方から候補由来の
識別子を観測できる。32 点しかない候補 universe では 12 hex の ID も表引きで wire に復元できる
(親が現行 tip で再実測し、diffq 経路 32/32 一意・wire 字面 0/32 を確認した)。

- WAL / provenance の実 ID は**変えない**。射影は critic 境界だけに置く。
- ラベルは campaign 内の WAL 初出順に振る。stock は ordinal に数えない。
- `src_token` / `build_attempt_id` / `build_admission_receipt_sha256` も同じラベルに従属する
  派生ラベルへ射影する。**親 brief はこの 2 チャネルを棚卸しから落としており、段 3 が是正した。**
- 射影は critic-facing API の**必須引数**とする。既定値で生描画へ落ちる opt-in にしない
  (opt-in にすると既存 consumer 7 箇所が生 ID のまま残り、検査が恒真化する)。
  生描画が要る診断経路は明示 sentinel を渡す。

**決定 (2): 未知の非空候補 ID は例外ではなく固定 sentinel へ射影する。**
段 4 では例外で拒否すると裁定したが、実測すると public な exploratory / custom drive 経路の
受理集合が狭まり、既存 3 テストが `complete` → `partial` に落ちた。sentinel は候補に依存しない
定数なので漏洩せず、受理集合も現行のまま保たれる。**生値への fallback は禁止する。**

**決定 (3): auditor 開示は自己申告 annotation として会計する。gate 化はしない。**
policy ID・policy digest・開示 JSON pointer・各値の digest・sunset 条件を attempt journal の
role-attempt event へ載せる。auditor を呼ばない pre-audit reject 経路は空 list とする。
**これは会計であって強制ではない。** completeness 側の必須化と report schema の版上げは
波及が大きいので本 wave では行わず、裁定パッケージへ返す。

**決定 (4): IR schema identity の preimage は emitter source + 32 golden とし、production 定数に置く。**
production は独立 golden module を import しない (既存の独立性検査を壊さない) ため、
golden 側は literal digest として持ち、実 golden との一致は検証層が確かめる。
production が import 時に自分の source を読む形は採らない (配布形態で壊れる)。
名前は checkout 限定の回帰検出器と分かる形にし、**artifact の schema identity としては搭載しない。**

**決定 (5): role payload の `SCHEMA_VERSION` を上げる。** 候補欄の改名と digest の nullable 化は
role payload の意味変更であり、D118 決定 (4) が同じ状況で版を上げた先例に倣う。
report schema の版は据え置く。

**決定 (6): 関係検査は「宣言した declassification を除いた sink 等価性」として置く。**
secret を候補 wire、公開入力を**候補が決まる前に確定する入力**に限り、
harness の outcome / metrics / rejection の class と件数は公開入力に含めず、
明示的な declassification として宣言してから比較で除く。除外は宣言した selector からのみ生成し、
行の見出し一致で理由・証拠を無条件に消す形にはしない (それでは証拠欄経由の漏洩を検出できない)。
**非空虚性の負例を同時に置く** — 証拠欄へ候補由来の値を入れると比較が赤くなることを固定する。

**名乗りの上限:** 名乗ってよいのは 8c critic recipient 境界の campaign-local pseudonymization、
宣言済み declassification を除いた critic sink 等価性の regression 検査 (no-build 経路)、
auditor 開示の自己申告 annotation、IR emitter・golden の変更検出 ID までである。
**origin-scope ID、non-interference、indistinguishability、P2 の充足・部分充足、cap-lift、
build 経路の閉鎖、proof chain 保全、U-1 / U-2 / U-3 の完了は名乗らない。**

**却下した案:** keyed hash による ID 置換 (32 点 codebook で再識別でき campaign 間 linkability も残る)、
WAL キー自体の匿名化 (D51 provenance を壊す)、描画済み digest への正規表現・部分文字列置換
(未知の identity channel を黙って通す)、production runtime gate 化
(`_invoke` 冒頭の無条件 fail-closed は terminal report を作れない経路を残す)、
production から独立 golden を import する形 (独立 oracle でなくなる)。

**研究状態への影響:** 変わるのは critic へ渡る候補識別子文字列、role payload の schema 版と bytes、
attempt journal / report / receipt の bytes である。**official の受理集合は空のままで、
certified 選択・材料レポート・proof chain・凍結 bytes の現在値は変わらない。**
P2 は引き続き FAIL、D114 の `MAX_APPROVED_GENERATIONS = 1` も不変。
材料正本 = `output/insights/2026-08-06_t244-p2-noninterference/`。
