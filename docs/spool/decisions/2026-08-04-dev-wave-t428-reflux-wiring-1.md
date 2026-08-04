---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t428-reflux-wiring
seq: 1
---

## {{D:trigger-wire-only-acceptance}}. trigger-gating 候補受理を固定 5-bit wire と binding/v1 に閉じる — raw mask は専用 WAL record に隔離し、provenance / report には nonce 付き commitment だけを残す

**決定 (D96 手続。境界テストと同一変更単位):** trigger-gating 軸の E 段候補受理を
「構造検疫を通る任意の 1 行 C++」から「5 文字 wire (LSB-first、bit 順は
`axis_trigger_gating.GATEABLE_REASONS`)」へ縮小する。受理面は 5 面を同時に閉じる。

1. **proposal schema**: coder 契約 mode を閉じた列挙にし、trigger mode の required key は
   `{axis, wire}`。`implementation` は未知 key として拒否し、key 閉包後に
   `reflux_ir.parse_wire` で値域も閉じる。未知 mode・trigger mode と `require_coder_value`
   の併用は設定誤りとして拒否する。
2. **唯一経路化**: driver は `TriggerGateIR` だけを保持し、materialize へ渡る C++ は
   `parse_wire → emit_predicate` の出力だけとする。旧「構文契約 grep」は受理 gate から
   emitter 出力への内部 drift assertion へ格下げする。
3. **汎用 sink の membership**: `p3_s4_loop.quarantine` は trigger marker の入力に限り、
   全 32 mask の `emit_predicate` 出力との byte-exact 一致 (strip 同値) を要求する。
   機械所有経路 (偵察 sweep、S1 直接比較、extime 較正) は正準述語を渡しており通過する —
   これらは E 段候補表現の外であり、emitter への完全移行は別の変更単位とする。
   sort / backoff の marker は挙動不変。
4. **binding/v1**: attempt ごとに raw binding (mask、predicate_sha256、nonce、source =
   {src_token, source_bytes_sha256} | null) を**専用 WAL record にのみ**書き、build_start
   payload・provenance entry・formal report には canonical JSON の sha256 commitment
   だけを残す。nonce (32 bytes) により候補 32 点の辞書攻撃で commitment から mask を
   復元できない。replay・`records_by_stage`・artifact admission は同一 validator で
   record の存在・key 閉包・mask 値域・predicate_sha256 再計算一致・source と admission
   receipt の一致・commitment 一致を検査する。`variant_id` の preimage は変えない
   (materialize 済み source の src_token が既に候補内容を決定的に束縛しており、mask を
   足すと同一 source identity の二重会計になる)。
5. **epoch**: `search_config` に binding schema marker を加え、campaign ID を意図的に
   分離する。admission は proposal 駆動 trigger campaign (E 段 loop・自律 trial) にだけ
   marker と binding を要求し、marker 有り binding 欠落・marker 無しの post-policy
   proposal 駆動・mixed・unknown を拒否する。既存 trigger 系 campaign の列挙 (E-loop 1 件 =
   exact overlay 分類済み、機械 sweep 6 件 = proposal 経路なし) により遡及被害ゼロを
   実測した。将来発見される正当な pre-cutover artifact は exact hash の個別 grandfather
   登録だけを許し、field 欠落による包括 legacy 化を禁じる。

**主張の範囲 (正直な非主張):** 本決定で名乗るのは「D121 決定 (7) P1 のうち **E 段候補表現の
閉包**」であり、D149 の emitter 監査と合わせて P1 を充足する。ただし (a) binding の
mask↔source の意味結合は producer 時の byte-exact hole 照合までで、mask と predicate_sha256 を
**整合を保ったまま連動改変**する攻撃は replay/admission の構造検証では検出できない
(検出には凍結 witness 表 = freeze 族の新設が要り、別裁定)。(a') 同じ理由で admission の
campaign 分類 (proposal 駆動 / 機械 sweep) も内部整合の検査であり、artifact tree 全体を
再構成できる敵対者が receipt・lock・WAL を一貫して作り直す偽装は検出射程外である
(receipt は認証でなく内部整合 — build_admission の既定義を継承)。(b) 機械所有の trigger
materializer 経路は候補表現の外に残る。(c) crash-resume の WAL topology 二重 build_start、SourceEvidence の
ABA、formal report schema への binding receipt 化、epoch による予算リセットの一般則は本決定の
射程外で、裁定パッケージとして返す。

**役割契約:** coder agent 定義の出力を wire に変更した (遮断設計は不変)。pin
(manifest / adapter / review_ledger) は起草者と別の実装単位が、親の独立レビュー証跡
(insights の stage5-agent-review.md) を経て更新した。adapter JSON は sandbox 制約により、
検査器 renderer の期待 bytes を親が review して適用した。

**却下した選択肢:**
- coder の C++ を受けて emit_predicate 出力と byte 照合する — 自由 C++ の parser と二重
  schema・開示面を温存する。
- mask を variant_id の preimage へ足す — src_token 経由の決定的束縛と二重会計になる。
- raw mask を build_start payload / provenance / report へ直接書く — 偵察 firewall (D48) と
  開示境界に逆行し、D121 P2 の recipient 設計を未裁定のまま逆方向に固定する。
- marker 欠落 artifact の包括 legacy 化 — downgrade 攻撃と区別できない。
- 全 trigger campaign への binding 遡及要求 — 機械 sweep 6 件が proposal 経路を持たないまま
  拒否へ反転する。

**研究状態への影響:** trigger-gating E 段の受理集合は任意 1 行 C++ から 32 encodings へ縮小
する (00000 は kUnset のみ true の退化点、11111 は ident_all であり真 stock ではない)。
凍結成果物・既存 certified 選択・proof chain の歴史分類は不変。`MAX_APPROVED_GENERATIONS = 1`
と cap-lift FAIL は不変。
