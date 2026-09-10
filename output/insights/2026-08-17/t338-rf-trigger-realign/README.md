# [T-338] RF 発火条件 / pilot 解禁条件の組み直し (2026-08-17)

`authority: none` / `default_effect: no-state-change` — 可変状態の正本は `docs/worklog.md` 末尾、
設計判断の正本は `docs/decisions.md` の当該 D である。本 dir は wave の一次資料 (逐語) を置く。

- `verbatim/s1-brief.md` — 段 1 brief (親)。M1〜M9 の実測と (P1)〜(P5) の provisional 裁定。
- `verbatim/s2-plan.md` — 段 2 プラン起草 (codex、read-only、reasoning=max)。
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (正しさ境界と絶対規律 2)。総括 NO-GO。
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (整合と実効性)。総括 NO-GO。
- `verbatim/s4-adjudication.md` — 段 4 裁定 (親)。real / refuted と採否。

## この wave が確定させたこと

1. **D162 決定 (10) の発火条件 (ii) から attestation を落とすことは、評価領域を D282 pin 済み
   receipt へ束縛する限り、受理を 1 つも広げない重複列挙の削除である。** 根拠は現物の実測 —
   D282 の承認 payload が pin する
   `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json` の sha256 は
   `d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e` で pin と exact 一致し、
   同 schema は `definitions/environment` の `required` に `attestation_mode`
   (`{"const": "required"}`) と `attestations` (`minItems: 2`) を持つ。
   束縛を書かずに列挙だけを外せば受理拡大になる。本 wave は束縛を書く方を選んだ。
2. **連鎖を実際に外しているのは attestation 側ではなく、pilot と公表層の依存辺を切る側である。**
   (ii) を満たす計測は既存の `892042` ではなく pilot receipt であり (D229 決定 (6))、
   その receipt は schema 上 attestation を持つ。
3. **「land しても実装 wave は進まない」は成り立たない。** 次の実装 wave
   (RF producer + attempt registry) は `pilot_submission` に依存しない。producer を止めていた
   D162 決定 (11) の閂 (種別 field の名前が決まるまで新しい producer を land しない) は
   2026-08-05 に [T-479] 択 (b) で解除済みである (archive worklog (199))。
4. **残る 3 項 (環境タグ・測定 checkout・pin) は「存在」検査では恒真である。** D282 pin 済み
   schema がいずれも必須にするため、存在だけを見る (ii) は何も拒否しない。したがって (ii) は
   「producer の自己申告以外の経路で計測時の実体と照合できること」を要求する形へ書き直した。
5. **解除条件の中身は本 wave でも定めない。** D292 が意図的に未定義に保った境界であり、
   実装前に完全条件を凍結すると「実装が条件に合わないとき条件側を緩める圧力」が生まれる。
   本 wave が挙げた 3 点は非網羅的な実装 backlog であって、必要条件でも十分条件でもない。

## この wave が主張しないこと

- pilot 投入の解禁。`pilot_submission = forbidden` と D292 の解除権威は維持している。
- コード・テスト・schema・凍結 artifact・certified 選択・材料レポート・proof chain・受理集合の変更。
  実装差分はゼロである。
- D291 の bytes の変更。同 D の payload は固定 commit の blob から読まれ、各節は sha256 で
  pin されている。本 wave の追記は resolver が読む bytes を 1 byte も変えない。
