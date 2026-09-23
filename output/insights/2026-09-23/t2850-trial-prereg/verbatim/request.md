# 依頼の逐語 (/dev-wave の引数、2026-09-23 08:3x JST)

[T-2850] (P1、VLDB 差分分析 P3) 探索の独立反復と費用・成果曲線の「試走」の事前登録を、計算なしの docs として書く。一次資料 =
  output/insights/2026-09-21/vldb-direction/gap-analysis.md §4 P3 と同 dir の codex-consult-1.md の優先 2、比較基盤の設計 = D2220 と
  output/insights/2026-09-22/t2849-comparison-harness-design/README.md、B-5 との関係 =
  docs/b5-generator-contrast-preregistration.md。決めるもの = 試走の規模
  (プロトコル・課題・手法・独立探索数・候補数)、候補評価数を揃えた比較と経過時間を揃えた比較の分離、記録項目
  (有効候補率・最初の有用候補までの時間・検証時間・node 時間・人間の介入、複製と compile 失敗も費用に含める)、B・A・系列数・費用上限・比較の族
  (T-2849 の本文がここで決めると指定)、本比較の規模を試走の探索間分散から決める規則。生成・選択に T-2851 の留保条件を使わない
  (docs/unseen-condition-transfer-preregistration.md §2.1・§2.3・§3、D2223)。実走・runner 実装・計算投入は含めない (実走は稼働中の T-2849
  実装の着地後に別 wave で計算確認を取って行う)。稼働 wave の実装 file は触らない。本題の文書だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。規律 2 は緩めない。着手直前の local main から fresh worktree を作る。
