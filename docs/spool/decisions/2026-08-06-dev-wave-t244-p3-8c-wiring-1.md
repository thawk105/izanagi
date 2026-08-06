---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t244-p3-8c-wiring
seq: 1
---

## {{D:s8c-wiring-not-fireable}}. 8c への origin ledger 結線は実装しない — 束縛を供給する経路が無く、batch 最低 2 行と 1 generation = 1 実行が構造的に噛み合わない

**決定:** U-6 が結線先に定めた 8c 自律 trial への origin ledger 結線を、実装せず設計メモと
裁定パッケージ 5 件に留める。ユーザー再裁定待ちへ戻し、親は不採用にしない。

**根拠となる実測 (この wave で現物確認した新事実):**

- **authority は 1 batch あたり最低 2 member row を強制する。** 予算 policy の parser は
  `batch_member_row_count_min` を `minimum=2` で読むため、どの authority 値を選んでも
  `member_row_count=1` の batch は作れない。一方 8c は 1 generation につき harness を 1 回だけ
  呼び、承認上限は 1 generation (D114) である。**「1 回の実行」と「最低 2 行」が噛み合わない。**
  台帳に記録されていたのは `batch_distinct_candidate_count_min <= batch_member_row_count_min`
  の関係だけで、下限 2 そのものは未記録だった。
- **`--no-build` の harness は実行せず `dry-pass` を返す。** ledger の seal outcome は
  `accepted` / `rejected` / `tombstoned` の 3 値に閉じ、前 2 者は evidence digest を、
  `rejected` はさらに constraint digest を必須とする。現行 harness の戻り値には
  そのどれの正本も存在しない。よって結線しても書けるのは未実行行 (tombstone) だけであり、
  sealed query counter は 0 のままで query floor を満たさない。
- **束縛を供給する経路がどこにも無い。** 本番 authority は空 (D183)、CLI に束縛引数は無く、
  headless provider への caller 注入は拒否される。非本番の store seam は private のみ。
  残る発火経路は「この wave が新しく書くテストが private 関数を直接呼ぶ」だけで、
  `DW-G04` の「既存 artifact path」に当たらない。

**理由:**

- `DW-G04` は、発火条件を満たす既存 artifact path か計測 ID を段 1 brief に書けない条件付き機能を
  設計メモに留めると定める。前 wave が origin-proofs sidecar と report v3 を却下したのと同型の
  判定であり、同じ基準を結線にも適用する。
- 敵対 2 レンズが独立に NO-GO を返した。片方は「実装せず設計メモへ戻せ」、もう片方は
  「member 行数・束縛・crash 回収を再設計せよ」と主張したが、後者を全部行っても束縛の供給経路は
  生まれない。よって前者を採る。
- 結線案の seam には公開の抜け道があった — fixture caller が束縛だけを渡して ledger client を
  省略すると既定解決で本番 ledger に落ちる。module 再束縛も private sentinel も要らない。
  さらに束縛が campaign / launch admission と結ばれておらず、正規 scope 内に未束縛の第二権限を
  持ち込める。これらは結線を land する前に閉じる必要がある。

**却下した選択肢:**

- **本番 authority へ entry を 1 件書いて発火させる** — 予算値が未裁定のまま本番 provisioning を
  解禁することになり、D183 に反する。
- **非本番の pilot ledger store を CLI から指定できるようにする** — 公開 API が本番 store 固定で
  あるという現行の防壁を、pilot のために store 差替え seam へ変える。予算 root を作り直せる穴の
  再演になる。
- **`--no-build` 限定で全 member を tombstone として seal する** — 予算を消費して 1 行も実行しない
  記録を作るだけで、将来の consumer が member 行数を候補数と誤読する余地を残す
  (D198 が分離した論点に逆行する)。
- **結線先を変える** — 8c を結線先とする裁定そのものをやり直すことになるため、親が決めず裁定へ返す。

**名乗りの上限:** この wave が名乗ってよいのは「結線を実装可能性の観点から実測し、
発火 gate 不成立と判定して実装せず、新事実と裁定パッケージを返した」までである。
結線の完了・予算束縛・生死の追加取得・本番 provisioning は名乗らない。
D114 の承認上限 1、D166 の P4 FAIL、D183 は不変である。
