---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-b2-descriptor-prereg
seq: 2
---

## 新規

### {{F:prior-wave-answered-same-question}}. 同じ問いへ既に答えた先行 wave を段 7 まで見つけられず、成果物を書き直した [手順漏れ] [コンテキスト浪費]

- 事象: B-2 (descriptor 条件付き合成の因果証拠) の設計・事前登録 wave が、現在地の実測と
  裁定パッケージを書き上げた段 7 の記録中に、**同日の先行 wave が同じ問いへ既に答えていた**ことに
  気づいた (`output/insights/2026-08-26_8b-b2-precheck-package.md`、worklog エントリ 981)。
  先行 package は実走入口の閉塞を層 (a)〜(f) に分けて確定済みで、再訪条件まで列挙していた。
  親の成果物は §1〜§3 と §5 の大半がその再掲になっていた。**差分だけを残す形へ全面的に
  書き直した。** 純増は 1 点 (判定規則に残る generation/search 固有の読み替えの穴) だけだった。
- 根本原因: `DW-S01` の既存被覆検索は「検査・テストを増やす wave では対象 vector の既存被覆を
  機構名でなく性質で先に検索し、純増検出力だけを書く」と、**検査を増やす wave に限定**して
  書かれていた。本 wave は docs・設計の wave だったため、親はこの義務が自分に掛かると読まなかった。
  さらに親が段 1 で読んだのは worklog の**末尾エントリだけ**であり (クラス 3 の起動手順どおり)、
  先行 wave はその 1 つ手前の rotation で `docs/archive/` へ移っていた。
  **起動手順が読む範囲と、既存被覆が住む範囲がずれている。**
- 恒久対応: `docs/dev-wave/core.md` の `DW-S01` を、成果物の種類によらず「依頼の問いそのものの
  既存被覆を worklog archive まで性質で検索する」義務へ広げた。
- 再発検知: 段 1 brief に、依頼の問いで `docs/archive/worklog-*.md` を検索した結果
  (該当なしなら「該当なし」) を 1 行書く。書けない brief で子を起動しない。
