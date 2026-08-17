# [T-338] RF producer 実装 wave — 逐語と裁定 (2026-08-17)

`authority: none` / `default_effect: no-state-change` — 可変状態の正本は `docs/worklog.md` 末尾、
設計判断の正本は `docs/decisions.md` の当該 D である。本 dir は wave の一次資料 (逐語) を置く。
branch `worktree-dev-wave-t338-rf-producer`。凍結記録であり、後から書き換えない。

- `package.md` — 裁定パッケージ (ユーザー裁定 3 問と親の推奨)。
- `verbatim/s1-brief.md` — 段 1 brief (親)。M1〜M9 の実測と (P1)〜(P5) の provisional 裁定。
- `verbatim/s2-plan.md` — 段 2 プラン起草 (codex、read-only、reasoning=max)。
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (正しさ境界と受理集合)。総括 NO-GO。
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (既裁定との整合と実効性)。総括 NO-GO。
- `verbatim/s4-adjudication.md` — 段 4 裁定 (親)。所見 20 件を全件 real と裁定 (refuted 0 件)。

## 結論

**依頼された RF producer + attempt registry は実装していない。** 段 2 の起草子と段 3 の敵対レンズ
2 本が独立に NO-GO を返し、親は所見を全件 real と裁定した。実装差分はゼロである。

**pilot は依然として投入不可。** `pilot_submission = forbidden` と D292 の解除権威は維持している。
本 wave は投入 gate を実装しておらず、投入権限を与えていない。

## この wave が確定させたこと

1. **producer を止めている閂は公表層ではなく投入 gate である。** D481 は閂を公表層実装だと同定し
   切り離した。切り離しは正しいが、閂はもう 1 つあった。受領証を永続化する関数は
   `PreregBinding` を必須 keyword-only で受けねばならず (record-items-v2 §6.10)、その名前は
   D264 が投入 gate の完成まで非 export と定め、D282 の `preserved` がそれを維持している。
2. **残余は D264 が名指しで却下した形である。** 投入不能と非 export を引いた残余 (attempt registry
   + 純粋な組み立て関数 + 否定検査) は、同 D の「台帳だけが『producer 実装済み』へ進む半実装は、
   直前の wave が blocker と判定した形である」に一致する。
3. **`declared_use_class = "dry"` は qsub 事実を免除しない。** D282 pin 済み schema の `attempt` は
   `qsub_result` / `performance_started_marker` / `cluster_slot_or_null` を必須とし、種別による
   免除規定を持たない。親 brief の (P2) はこの点で反証された。
4. **D229 決定 (8) の必須 kill 3 件は producer 段では達成できない。** 敵対レンズ 2 本が独立に
   同じ結論へ到達した。本 wave はこの 3 件を「kill 済み」と記録しない。
5. **起動命令が名指しした既存機構は 2 件とも実在しない。** `s8b_floor_stats.py` は自らの保証境界と
   して attempt registry を保証しないと明記し、`s8b_floor_campaign.py` のそれは私有 runner クラスの
   私有メソッドで床値 protocol に束縛され export されていない。
6. **命令が課した D496 関門は発火しない。** 承認済み出力契約 (D282 pin 済み受領証 schema と
   record-items-v2) の双方で `floor` / `床値` の出現は 0 件であり、schema は 3 arm
   (`stock` / `mode1` / `modeX`) を同一受領証内で必須とする。RF は床値表の引き当てではなく
   同一 campaign 内の対測定であって、D496 が求める形と一致する。

## 親が訂正した自分の実測

- **M4** — 「`floor` 文字列 0 件だから床値表に依存しない」は承認済み出力契約の範囲でのみ成立する。
  新規 module の設置先 package は import graph 上 calibrator を引く。敵対レンズ 2 本が独立に反証した。
- **M6** — 固定三つ組は 6 件ではなく **7 件** (`approved_blobs` 6 role + `target_core`)。
  pin の権威経路は test ではなく `approval_payload.py` の `load_approval_payload` と
  `blobref.read_pinned_blob` である。
- **M2** — 「再利用不能」は直接再利用の範囲に限る。原子公開などの primitive まで否定するのは過剰。

## この wave が主張しないこと

- pilot 投入の解禁。解除条件の中身も定めていない (D292 の境界を動かさない)。
- コード・テスト・schema・凍結 artifact・certified 選択・材料レポート・proof chain・受理集合の変更。
  実装差分はゼロである。
- D229 決定 (8) の必須 kill が達成されたこと。3 件とも producer 段では達成できないと記録した。
- 再利用先の確定。次 wave の段 1 要件として残した。
