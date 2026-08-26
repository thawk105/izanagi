---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1721-noncertifying-a1
seq: 1
title: [T-1721] 非認証成果物型は lock-only certified gate を閉じられず作れないと実測し、停止して再開 scope を確定した (docs のみ、branch worktree-dev-wave-t1721-noncertifying-a1、実装面の差分ゼロのため変異 matrix 免除)
---

## 本文

- 依頼は D1028 に従い「認証権限を持たない成果物型の確定」と「A-1 対測定の投入器」を
  同じ変更単位で作ること。あわせて、稼働中 wave `dev-wave-t1629-ratification-broker` と
  編集面が重なる恐れが高いので起動時に重複検査を行い、重なるなら scope を型側へ寄せるか
  着手を見送って報告すること、と指示された。

- **重複検査の結果、指示された 2 つの逃げ道はどちらも取れなかった。** 重なるのは型側であり、
  重ならないのは投入器側で、D1028 は投入器のみの先行を名指しで禁じている。代わりに
  「新規 module を enforcement source closure へ足さない」を段 1 の不変条件へ置き、
  判定を既存閉包 file の中で閉じることで 1 file も共有しない形を試みた。

- **その方針は段 2・3 で反証された。** 決定的なのは、campaign lock だけを読んで certified epoch を
  出す consumer 経路である。この経路は編集禁止の 3 file だけで判定が閉じており、
  編集可能面を 1 つも通らない。

- **一次証拠を親が独立に再現した。** repo 外の temp directory にだけ書く read-only probe で、
  `search_config` に `artifact_class: "non-certifying"` と `promotion_prohibited: true` を
  入れた inner identity を、公開情報だけで組んだ v2 authority で包み直し、
  `require_campaign_verifier_epoch(..., purpose=CERTIFIED_ACCEPTANCE)` を当てた。
  結果は `state=E1`、`reason_code=recorded-closure`、`epoch=E1:ab51c89f52ff51fe61e81...`。
  **未批准 closure から作った非認証宣言つき lock が certified 受入を通った。**
  段 3 の子が別 context で同じ probe を組み、同じ epoch 値を得ている。2 独立実行で同値である。
  base `dd66213` と main 取り込み後の `a0a0cdf46` の双方で再現した。

- v2 authority の材料はすべて公開だった。closure map は批准を検査しない公開関数が返し、
  activation state も公開関数が返す。非認証 run に固有の秘密も発行 capability も要らない。

- **停止は D1028 の不採用ではなく D1038 の停止条件の発火である。** D1038 は
  「field の除去や付け替えで昇格できる作りしか取れないなら、作らない」を着手条件に置いている。
  D1028 の本文は「型と consumer を同時に作ると、型が実際に昇格不能かを consumer 側で検査できる」
  と書いており、**検査した結果が「昇格不能にできない」だった**場合の指示は無い。
  3 台帳を全文検索し、この事実がどこにも記録されていないことを確認した。裁定パッケージで返す。

- **段 3 が段 2 の分割を否定した。** 型と投入器だけを作っても A-1 の有効な成果物まで経路が
  通らない。A-1 の campaign config へ型を結線する手当てが無く、集計器は終端 stage を固定しており、
  scheduler completion receipt の producer は tracked tree の全数検索で 0 件、
  materialize の呼び手も存在しない。再開 scope は 8 項目へ広がる。

- **投入器側の調査は完了して保全した。** F634 の恒久対応 (段 1 で実行器の tracked file を
  全数検索する) は発火し、着手前に不在を検出した。acquisition receipt の必須 field と述語
  (段 3 が段 2 の表から落ちていた述語を 5 件補った)、qsub の argv と環境変数、
  create-only の実装法、既存 submitter 8 本との作法比較まで確定している。
  **型が作れるようになった時点でそのまま使える。**

- 親が段 1 で書いた誤りを 3 件訂正した。`declared_use_class` の所在、予約 key と campaign id の
  関係の表現、批准 gate が落ちる層 (台帳の記述と実測が違い、実測は
  `enforcement-source-closure-unratified` だった)。詳細は insight の訂正節。

- codex 子は本 repo で pytest を実走できないため、子の出力を緑として記録していない。
  probe はすべて親が実走し、repo 内へは 1 byte も書いていない。

- 設計判断は {{D:noncertifying-type-blocked-by-lock-only-gate}}、
  {{D:noncertifying-type-waits-for-ratification-broker-landing}}、
  {{D:noncertifying-scope-is-one-land-unit-through-final-reader}}。
  失敗は {{F:promotion-prohibited-marker-was-vacuous}}、
  {{F:lock-only-epoch-gate-bypasses-ratification}}、および F634 の再発。

## 次の一手差分

### 更新

- [T-1721] **P1・ユーザー再裁定待ち**: 非認証成果物型は lock-only certified gate を閉じられず
  現行の所有制約下では作れないと実測した (親 probe で再現、段 3 の子と同値)。D1038 の停止条件の
  発火であり D1028 の不採用ではない。返す問いは 4 つ — (1) 終端を「作らない」で確定させるか、
  稼働 wave の land 後に一体で再設計するか (wave 推奨 = 後者。D1028 が却下した着地待ちには
  当たらないという読み方でよいかの確認を含む) (2) 再開 scope を 8 項目へ広げることを認めるか
  (wave 推奨 = 認める) (3) 昇格不能性に署名された identity 束縛を要求するか (bytes 級の
  署名機構新設は既定で見送りという方針と向きが違う) (4) 恒真だった既存 marker を実効化するか
  据え置くか (wave 推奨 = 実効化)。裁定パッケージは
  `output/insights/2026-08-27_t1721-noncertifying-a1/ruling-package.md`。
  投入器の完全契約は同 insight に保全済みで、型が作れれば即使える。
  base: ebf9349464d71d15cb8b911cb6a000fa780b43bbdec575ea9f917b2891c86452
