---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t244-p3-origin-ledger
seq: 1
title: [T-244] D121 P3 の origin ledger は敵対 2 レンズが独立に NO-GO を返し、実装を差し戻した (docs のみ、branch worktree-wave-t244-p3-origin-ledger、実装差分なしのため変異 matrix と受入全走は対象外)
---

## 本文

- **段 3 の敵対 2 レンズが独立に NO-GO を返した。** real 17 件・疑い 1 件・nit 1 件。
  裁定は {{D:p3-origin-ledger-deferred}}、裁定パッケージ 7 件は
  `output/insights/2026-08-04_t244-p3-origin-ledger/s4-adjudication.md`
  - レンズ A (状態機械の網羅) の決め手は **A-1** (別 origin_id / 別 root で予算が新品になる) と
    **A-2** (batch 必須化と単一 slot FSM が両立せず、単一 in-flight が恒真化する)
  - レンズ B (主張過大) の決め手は **B-2** (`DW-G04` の発火 artifact / 計測 ID が書けない) と
    **B-3** (`DW-O13` — `origin_id` が実在 field と結び付かない)
  - **両レンズが独立に同じ結論へ到達した**: 予算を origin へ束縛する設計は、origin 識別の規則を
    決めない限り成立しない。その規則は設計本文 §⑤ が未解決として残した項目である
- **走行中にユーザー裁定が land した (エントリ (161))。** 択一 1 (予算値) が
  「下限式から再導出する」で確定し、P10 の 3 点が揃った。**裁定パッケージ U-F (floor 制約の必須化) は
  これで実質決着した**が、差し戻しの判断は変わらない — origin 識別と batch 表現は P10 の外にある
- **親の実測誤りを 3 件記録する。** いずれも子が拾い、親が追認した
  1. brief の「4 性質は既存テスト未被覆」は repo 全体への一般化として誤り。資格審査側の既存テストが
     重複投入・厳密一致 idempotent な crash / finalize・生存成果物からの台帳欠落拒否を撃っていた
  2. 親が段 2 実行中に書いた erratum の「先行実装とほぼ同型」も過大。同型なのは 4 crash 窓のうち
     1 件だけで、verifier red 後の窓に対応する event は先行実装に無い
  3. 同 erratum の「台帳を消せば常に新品になる」も一般化として誤り。生存成果物を持つ consumer は
     台帳欠落を拒否する実テストを持つ
- **段 2 の子は先行実装 (資格審査側の hash-chain 台帳) を自力で発見した。** 親は段 2 の実行中に
  独立に同じものへ到達し、brief へ erratum を足して段 3 のレンズへ渡した。**親が先に見落としていた
  面を、待機時間の再検査と子の探索が独立に拾った**
- **反証されなかった親の実測** (レンズ B が 4 件とも試みて反証できず): 凍結 manifest は `output/` の
  23 path のみで source leaf 新設は凍結 bytes に触れない、P10 の狭い意味での裁定状況、
  consumer 未結線ゆえ現成果物 4 種は不変
- 実装差分ゼロのため**変異 matrix と受入全走は対象外**。段 5・6 は `DW-S04` に従って飛ばした

## 次の一手差分

### 更新

- [T-244] **P1・P3 は実装を差し戻し → 裁定パッケージ 7 件がユーザー裁定待ち**:
  段 3 の 2 レンズが独立に NO-GO。**U-A** origin_id を authority manifest digest へ束縛するか、
  **U-B** 同一の科学的 cell へ複数 origin を発行しない機械規則をどう書くか、
  **U-C** authority root を単一に固定するか、**U-D** 軸 (iii) 必須化を受けて batch を ledger の
  第一級にするか、の 4 件が実装の前提。**U-E** anchor を committed bytes 照合まで強めるか、
  **U-F** floor 制約の必須化 (エントリ (161) の裁定で実質決着)、**U-G** P3 充足を leaf 単体で
  数えないか、は同 wave で併せて裁定するのが安い。U-A〜U-D が決まれば実装 wave を再起票できる。
  設計メモ・敵対レビュー 2 本・変異事前登録候補 6 件は
  `output/insights/2026-08-04_t244-p3-origin-ledger/` に凍結済み
  base: 77e62bdb00cb45d240921e41f62a190abacd7e4bdfb1ee3dc08a43304a344dbf
