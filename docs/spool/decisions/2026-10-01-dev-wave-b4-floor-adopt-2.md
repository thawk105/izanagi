---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-10-01
wave: dev-wave-b4-floor-adopt
seq: 2
---

## {{D:b4-floor-adopt-defer-entry}}. B-4 床値は集約を採用し pin 値を確定する。§5 floor セルへの記入は、記入で止まる test を直す実装 wave が同じ commit で行う

**決定 (D1641 決定 1・2 の委任の下で AI が行う採用裁定):**

1. **採用する。** B-4 床値として集約
   `output/env/pegasus/floor-pair/t2288-f1/b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json`
   (sha256 `4896a1fd1735667c62a6ce8200d3f70faf9bc0d08e0afe7c6970e61f69d7dbdf`、床値 `436449544102615 / 2^52` ≈ 0.09691) を受理する。
   §5 floor セルへ書く値はこの path と hash の `artifact_path=<path>; sha256=<hash>` で確定し、後から集約・統計関数・対象集合を
   選び直さない。
2. **記入は本裁定では行わない。** 記入した木では、spec が束縛する追跡外の binary
   (`output/env/pegasus/binaries/7cdf0dc3…`、checkout ごとに `place` する ignored file) を置いていない checkout で、resolver が pin を
   拒否し材料レポートが評価器の前で止まる。B-4 系の test は 34 failed + 2 errors になった (記入を戻した木では同じ 4 file が 259 passed)。
   直すには test の変更が要る。
3. **記入の手順を次のとおりに定める。** 実装 wave (Codex author) が、(a) 材料レポート系と raw record producer の test が
   実文書の floor 状態に依存しないよう文書入力を fixture へ切り替え、(b) 実文書を読む回帰 test
   (`test_resolver_real_preregistration_is_absent` ほか) を登録後の期待へ更新し、(c) 実文書を消費する checkout には既存の
   `b4_binary_record place` で binary を置く。floor セルの記入はその wave の同じ commit で行い、記入値は決定 1 のものに限る。
   製品コードの受理条件 (binary の実在・hash・receipt・calibration の検査) は変えない。
4. **floor_domain_error への影響。** 欄が `未記入` の間は従来どおり floor 不在が評価器へ渡り、分析に到達すれば
   `floor_domain_error` → protocol violation になる。pin が検証を通れば正確な分数の floor が渡り、floor 欠落による固定は外れる
   (他の理由 enum・分岐・B-4 の未実走は変わらない)。pin が拒否されれば材料レポートは `authoritative_floor_rejected` で止まり
   verdict を出さない。事前登録 §11.0 の 2026-09-08 追記の「拒否時も floor 不在が渡る」は現行コードと一致しないが、本決定では
   事前登録を編集しない。B-4 の「未実走・記述統計に限定」は変わらない。
5. **submit-tree。** 撤去の可否を問われた `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree` は既に存在せず、
   撤去対象は無い。

**理由:**
- D1641 決定 3 の受理条件 (1 窓・1 セル n = 62 (D1695)、欠測 0、2 窓の分離約 231.6〜231.8 h、上限 < 1) を窓 JSONL と集約の実物で
  確かめた。期待 spec 3 組は実 file と D2138 項 7 の表に全桁一致し、spec の凍結 commit `0b4fbd7a6` は最初の測定より前である。
  probe・同一 binary 対・事前無作為化は前 wave の証拠確認者の記録に依る。
- 記入を強行すると main の受入が赤になり、binary を置いていない checkout で材料レポート (Phase 3 主経路の片翼) が生成できない。
  依頼の範囲 (docs のみ、所有は floor セルだけ) では直せない。
- 採用と記入を分けても事前登録に反しない。値と対象集合は結果を見たうえで変えておらず、記入は事前登録の発効でもない。
- 読み取り専用の codex 2 本 (正しさ境界・整合のレンズと、実効性・過剰のレンズ) が記入保留を支持した。逐語は
  `output/insights/2026-10-01/t2288-floor-adoption/`。

**却下した選択肢:**
- **本 wave で記入し、壊れる test を実装子に直させる** — 依頼の所有と「docs のみ」を超える。
- **floor 消費時に binary の検査を省く、または pin の拒否を `None` (floor 不在) に戻す** — 今拒否している入力を受理する方向で、
  規律 2 に反する。
- **binary を置いた自分の作業木だけで記入して land する** — 他の checkout と受入で同じ赤が出る。
- **不採用** — D1641 決定 3 の不採用条件 (欠測 5% 超、上限 1 以上) に当たらず、測定と集約に不備が見つかっていない。
