---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t782-reviewed-spec-issuance
seq: 3
---

## 再発

### F151

- **再発: 2026-08-26** — 段 1 の前提実測で、floor protocol が固定順の完全一致で強制している
  承認凍結 4 行を、同名 field を持つだけの oracle spec の権威としても引用し、handoff の
  追測へ「repo 内権威から導出できる」と書いた。実際には oracle spec の validator は
  重複の無い非空文字列列を任意に受理し、承認経路の positive fixture は別の値を意図的に通している。
  同じ追測で実行環境タグ・時計数・環境契約 hash・CCBench pin も「導出できる」に分類したが、
  これらも spec validator は型しか見ておらず、拘束は実走時の driver で初めて起きる。
  **前回は裁定同士を話題文で同一視した取り違えだったが、今回は同名 field を根拠に
  別 module の凍結表を権威として移植した**もので、照合を名前で行い実際の述語で行わなかった点は
  同じである。段 3 の 2 レンズが独立に指摘し、親が承認経路の pin 済み fixture の逐語 bytes で
  裏を取って確定した。恒久対応は同 wave の決定 (spec の各軸を導出可否でなく拘束層で分類する) と、
  memory `consumer-exact-predicates-must-all-be-checked` の適用対象を
  「同名 field を共有する別 module の凍結表」まで広げることである。

### F301

- **再発: 2026-08-26** — 段 1 brief の不変条件へ「凍結 bytes の pin 閉包を全件列挙した」と書いたが、
  実行した検索は成果物 path を key にしたものだけで、**検査値そのものを literal で持つ側**を
  探していなかった。落ちていたのは承認経路の positive fixture が持つ逐語 byte 列と、
  そこから導かれる spec hash・schedule hash の定数である。段 3 のレンズが指摘し、親が実在確認した。
  **前回までの 2 例は識別子 key の検索漏れと編集面 path key の検索漏れだったが、今回は
  どちらの key でも見つからない「検査値の literal snapshot」**であり、pin 閉包の検索方向が
  3 種類あることが実測された。恒久対応は、段 1 の凍結節で列挙するときに
  識別子 key・編集面 path key・検査値 literal の 3 方向を別々に回し、
  1 方向しか回していない列挙を「全件」と書かないことである。
