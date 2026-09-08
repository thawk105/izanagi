---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2380-b5-successor-freeze
seq: 2
---

## {{D:b5-anchor-control-sets-fixed-before-lookup}}. 軸 B5 の anchor 包含 control は索引別の member 集合を lookup の前に固定し、結果を見て外さない

**決定:** 軸 B5 の positive control (部分登録 §4.2〜§4.3) の対象 anchor 集合を、**索引ごとに** lookup の前に固定する。
membership は anchor が持つ鍵型 (DOI / arXiv ID) と索引の収録範囲についての事前知識だけで決め、
ID lookup や検索の結果で変えない。member の lookup が `不達` または `非収録` なら、部分登録のとおり
当該索引の走行と軸全体を `未完走` とし slot の control を未配置にする。member でない (slot, 索引) の組には
包含 control が無く、その不在は限界として実行記録と `RW3` の主張に併記する。索引を母集合から外すことも、
その索引の主 query・演算子 control を省くこともしない。member の control ID は `B5-ANC-<anchor ID>@<索引>`。
正本は `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md` §2.4〜§2.5 (E-1)。

**理由:**
- 部分登録の文面 (「1 件でも ID lookup が不達なら軸全体を `未完走`」) は、arXiv API が DOI を鍵に引けず
  OpenAlex が arXiv ID を鍵に引けないことと、1950 年代の Annals 論文や SIGMOD 論文が arXiv に無いことから、
  arXiv ID を持たない anchor を 1 つでも含めた時点で構造的に閉じない (D1207 の型)。
- 段 3 の敵対相談が、親の当初案 (`非収録` を見てから当該索引の control から外す) を「非収録を結果依存で
  除外でき、positive control を空集合化できる」と指摘した。集合を lookup 前に固定すれば、結果を見た除外の
  経路が無くなり、受理集合の拡大は「member でない組に control が無い」の 1 点に限られる。
- anchor は検索式に語彙的に届きやすいかで選ばない (D351 の逆向きの reward hack を避ける)。届きにくい anchor が
  control を不発にしたら、それは登録語彙の限界を示す正当な結果であり、語彙の意味的 amendment へ進む。

**却下した選択肢:**
- `非収録` を見てから control から外す (親の当初案) — 結果依存の除外で、control を恒真にできる。
- 全 anchor × 全索引を要求する部分登録の文面どおり — 構造的に閉じないため、宣言的除外でなく契約の改訂で閉じる (D1207)。
- 通りやすい anchor だけを選ぶ — 包含 control の意味を失う。

## {{D:dblp-anti-bot-challenge-is-unreachable}}. DBLP の anti-bot challenge は `不達` として扱い、challenge を模倣しない

**決定:** 文献検索の索引が anti-bot challenge (2026-09-07 に DBLP で観測した Anubis の JS 駆動 challenge) を返した場合、
その索引は `不達` (可用性の失敗) として記録し、challenge の JS や proof-of-work を模倣・自動化して通過しない。
UA と `Accept` header の変更、content negotiation、別入口の試行までは可用性の観測として行ってよい。
`不達` の帰結 (当該索引の走行と軸全体を `未完走`、索引を母集合から外さない) は 7.7.4 と部分登録 §4.2 のまま。

**理由:**
- challenge は索引側が自動アクセスを拒む意思表示であり、それを迂回して得た応答は取得時点の来歴 (D1206) として
  信頼できない。
- 7.7.4 は「使えなかった索引を黙って母集合から外さない」と要求する。`不達` を記録し、live preflight で再確認する
  経路が既にあり、迂回は要らない。
- 本 wave の観測: DBLP の `search/publ/api`、`doi/<DOI>`、`xml/release/` の 3 入口が UA (自前 / curl 既定 /
  ブラウザ風 / python-urllib) と `Accept` に依らず HTTP 200 `text/html` の challenge を返した。
  2026-08-27 の軸 3 索引実測は同 API に到達していたので、それ以降に変わった。

**却下した選択肢:**
- metarefresh 型 challenge を追従する — 1 回目の応答には meta refresh があったが 2 回目以降は JS 駆動で、
  追従は challenge の模倣になる。
- DBLP を母集合から外す — 7.7.4 違反。
