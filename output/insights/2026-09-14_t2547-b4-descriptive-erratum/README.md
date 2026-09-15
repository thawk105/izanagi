# [T-2547] B-4 を記述統計へ限定する事前登録追補 — 逐語と裁定

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t2547-b4-descriptive-erratum` の一次資料を凍結したものである。

## この wave が着地させたもの

`docs/phase3-b4-reflux-ablation-preregistration.md` の §5.1「n と検定単位」bullet 直後へ、
D1936 項 8 に従う追記ブロックを 1 つ足した。docs のみ。実装面の差分はゼロ。

**追記が確定させたのは、人が本書に基づく B-4 について報告に書いてよい主張の上限だけである。**
機械が生成する材料レポートの値・分類・参照は 1 つも変わらない。実走の許可でもない。

## 収録物

| file | 内容 |
|---|---|
| `census-verbatim.md` | 適格な赤 precursor の在庫実測の逐語 (0 件)。**撤回した論拠 3 件も明記** |
| `stage1-brief.md` | 親の段 1 brief |
| `stage2-plan.md` | 段 2 plan (codex read-only)。挿入位置・追補草案・凍結境界の確認 |
| `stage3-consult-sol.md` | 段 3 敵対相談 (正しさ境界) |
| `stage3-consult-luna.md` | 段 3 敵対相談 (裁定整合と実効性) |
| `stage4-ruling.md` | 親の段 4 裁定 (所見 11 件の real / refuted と採否) |
| `stage6-review-sol.md` | 段 6 敵対レビュー (正しさ防壁と凍結境界) |
| `stage6-review-luna.md` | 段 6 敵対レビュー (裁定整合と 6 か月後の読者) |
| `stage6-fix-correspondence.md` | 段 6 所見の closed / partial / regressed 対応表と親の処置 |

## 独立検証で確かめた凍結境界

段 6 sol が、追補の前後で §5.1.1 の抽出 bytes が完全一致することを実装から直接確かめた。

```
size: 21,833 bytes (追補前後で一致)
raw SHA256:      0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30
semantic SHA256: 5d0b189bd68391b4a6876bd24400230e7186f6bc1fe374ea298d44edebcfd1a7
```

3 経路 (`p3_b4_analysis_prereg_consumer.py` の `_locate_section`、
`p3_b4_analysis_path.py` の `preregistration_section_5_1_1_bytes`、
`p3_b4_admission_record.py` の §5 固定表 parser) のいずれも、追補を抽出範囲に含まない。

**ただし文書全体の sha256 は変わる。** `p3_b4_admission_record.py` は宣言 commit の全文 sha256 と
HEAD blob 一致を要求するため、「§5.1 は pin されていない」と一般化してはならない。
admission record は 3 driver 分いずれも不在なので、無効化される既存 admission は 0 件である。

## 閉じていないこと

- **適格な赤 precursor の在庫取得。** 0 件のままである。供給源と適格条件は変えない方針を維持する。
- **少数の適格赤を得たときに §5.1.1 の選択関数 (適格行が n 未満なら実走しない) とどう両立させるか。**
  D1936 項 8 の「適格な少数の赤 precursor を使う」と、同じ凍結節の選択関数・D1880 の 201 行契約の
  関係が未解決である。**ユーザー裁定へ返す。この wave では解かない。**
- **「前回計数 (2026-09-10) 以降 0 件のままである」の証明。** 今回 0 件は再読取りが支持するが、
  履歴の不変は証明していない (`census-verbatim.md` の撤回節を参照)。
