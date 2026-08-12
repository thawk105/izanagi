---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t968-floor-rep-integrity
seq: 1
---

## 新規

### {{F:mutation-anchor-nonexistent}}. 事前登録した変異 4 件が、注入不能・帰属不成立・受理集合不変のいずれかで無効だった [テスト代表性] [恒真ゲート]

- 事象: 段 4 で登録した変異 13 件のうち、M4 の anchor (`all` を `any` へ) は実コードに存在せず、
  M1 は期待した median 混入 assert に到達する前に前段 assert で落ち、M7 (precedence 順序入替) は
  成果物の値・受理集合・参照を一切変えず、M12 の `returncode=True` は fail-open を作らなかった。
  4 件とも「登録できたつもりで検出力を測れていない」状態だった。
- 根本原因: 親が変異位置をプランの記述から採り、**注入対象の逐語がコードに実在するか、
  その変異が受理集合を実際に変えるかをコードで裏取りしていなかった**。`DW-M01` が要求する
  単一理由性の確認を、位置の存在確認で代用した。
- 恒久対応: 変異 spec を実ファイルからの逐語抽出で生成し、生成器が anchor の一意性
  (出現 1 件) を機械 assert する (本 wave の `make_spec.py` が該当。抽出は行範囲指定で、
  spec に literal を手書きしない)。受理集合を変えない変異は `DW-M03` に従い
  diagnostic sensitivity pin へ降格し、kill に数えない。
- 再発検知: 段 3 の敵対レンズに「登録変異が本当に注入でき、受理集合か fail-closed 挙動を
  変えるか」を明示の攻撃面として与える (本 wave のレンズ B が 4 件すべてを静的に検出した)。
  `DW-M08` の probe + erratum 経路で初回走の実測 node 集合を残し、完全集合へ再登録して再走する。
