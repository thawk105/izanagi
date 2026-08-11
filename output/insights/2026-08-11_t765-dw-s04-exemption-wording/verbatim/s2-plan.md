静的検査のみ実施し、pytest は未実走です。したがって緑は主張しません。

## 1. 曖昧さの構造

現行文は [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79) の次です。

> 免除は実装差分ゼロの「実装しない」裁定の変異 matrix だけ。

問題は、`実装差分ゼロの` → `「実装しない」裁定の` → `変異 matrix` と、二つの連体助詞 `の` が head noun を明示せず連鎖することです。

1. 意図された読み  
   `[[「実装しない」と裁定された] かつ [実装差分ゼロの] wave] の変異 matrix`。二条件の積集合だけを免除する。

2. 不採用済みの読み  
   `実装差分ゼロの` を実際の適用条件、`「実装しない」裁定の` を matrix の種類・由来を表す説明と取る。この場合、「実装しない」という裁定が実際になくても、実装差分ゼロだけで免除できる。

3. 第三の読み  
   `[[実装差分ゼロの「実装しない」裁定] の変異 matrix]` と局所係りさせ、実装差分ゼロを wave ではなく裁定・裁定文書の属性と読む余地がある。また `裁定の変異 matrix` を「wave 全体の matrix」ではなく「裁定文を対象にした matrix」と読むこともでき、免除範囲を不当に狭め得る。

`だけ` の係り先については、直後の「受入全走は免除せず」が明示的な否定を置くため、受入全走まで免除する読みは [core.md:79–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79) で閉じています。

## 2. 置換案

### 推奨案

> 免除は「実装しない」裁定を受けて実装差分ゼロの wave の変異 matrix だけ。

- UTF-8: **101 bytes**。上限 102 bytes 以下。
- L1: `10,606 + (101−83) = 10,624 / 10,625`、余白 **1 byte**。
- `裁定を受けて` が実際の裁定を動詞で表し、`実装差分ゼロの wave` と連接するため、二つの裸の `の` の連鎖を除去する。
- `だけ` の head は引き続き `wave の変異 matrix`。他の義務を免除する文にはならない。

拡大・縮小の検算は次のとおりです。`C` は段4で実際に「実装しない」と裁定、`Z` は実装差分ゼロを表します。

| C | Z | 変異 matrix |
|---|---|---|
| 真 | 真 | 免除 |
| 真 | 偽 | 非免除 |
| 偽 | 真 | 非免除 |
| 偽 | 偽 | 非免除 |

したがって、実装差分ゼロだけの wave は新たに免除されず、従来意図された `C∧Z` wave は一件も失われません。

残る余地は、`て` が時間順・因果を含意し得ることですが、どちらの読みでも二事実の成立は必要であり、免除集合は変わりません。実務上の残リスクは L1 余白が1 byteしかない点です。

### 次点

> 免除は「実装しない」裁定かつ実装差分ゼロの wave の変異 matrix だけ。

- UTF-8: **95 bytes**。上限内。
- L1: `10,618 / 10,625`、余白 **7 bytes**。
- `かつ` が `C∧Z` を明示するため、真理値集合は推奨案と同じ。拡大も縮小もない。
- `wave の変異 matrix だけ` により、被免除物も維持される。

残る弱点は、`「実装しない」裁定かつ` が名詞止めで、「裁定を受けた／裁定済み」が省略されている点です。極端に逐語的には「裁定」と後続名詞句の並列にも取れるため、文法上は推奨案より一段弱いです。

なお、候補の `変異 matrix の免除は……wave だけ` は、対象 wave の限定は明快ですが、「免除される物は matrix だけ」という現行の全体限定をやや間接化します。そのため上記2案より下に置きます。

## 3. 文脈整合

- [core.md:74–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:74): 段4裁定、`DW-M01` への接続、受入全走の非免除は一切変わらない。
- [dev-wave.md:48–51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:48): `C` は「実装しない」と裁定して `4→7→8→9` を選ぶ場合に対応する。通常経路の段6にある変異 matrix・受入再走とも矛盾しない。
- [workers.md:63–66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/workers.md:63): 通常経路では親が matrix と受入を再走する。特殊経路では段6を飛ばすため、[core.md:79–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79) が例外と受入期限を直接担う。
- [mutation.md:5–56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/mutation.md:5): `DW-M01`〜`DW-M08` の事前登録、単一理由性、kill、復元、期待 node の契約は変更しない。変更するのは matrix 免除の入口条件だけ。
- 被免除物は推奨案でも `wave の変異 matrix だけ`。直後の受入全走非免除も無変更なので、免除の主語・対象が他の検査へ漏れない。

一点、親 brief の P1「実装差分＝コード・テスト」は不完全です。[dev-wave.md:34–37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:34) では、実装面に probe、harness、script、機械設定も含みます。docs-only が実装差分ゼロという今回の結論は変わりませんが、段4記録では完全な定義を使うべきです。

## 4. Consumer 棚卸し

| Consumer | 行動・検査 | 影響 |
|---|---|---|
| 段4 manager | [dev-wave.md:64–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:64) が `DW-S04` を無条件読取 | 意図した判定だけが明確化される |
| 変異実行契約 | [mutation.md:5–56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/mutation.md:5) | 文面の逐語は読まない。変更不要 |
| 通常段6 | [workers.md:63–66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/workers.md:63) | 通常経路の matrix・受入義務は不変 |
| 設計判断 | [decisions.md:11131–11150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/decisions.md:11131) の D237 | 本文の意味は維持。ただし見出し「実装差分ゼロの wave」が単独十分条件に見える既存リスクは残る |
| 最新裁定 | [worklog.md:3397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/worklog.md:3397) | `Z` 単独への一般化を明示的に不採用。今回の文面と一致 |
| byte・節検査 | [check_docs.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:248)、[check_docs.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:552)、[check_docs.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:605) | `DW-S04` を L1 として数える |
| H2 slice | [check_docs.py:3682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:3682)、[check_docs.py:3770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:3770) | 見出し・改行を変えないため1:1検査は不変 |
| L1上限 | [check_docs.py:3798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:3798) | 推奨案は静的計算上10,624で上限内 |
| meta-test | [test_check_docs.py:2009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/orchestrator/tests/test_check_docs.py:2009)、[test_check_docs.py:2633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/orchestrator/tests/test_check_docs.py:2633) | 定数・層分類・超過拒否だけを pin。本文 literal は pin しない |

壊れる whole-file SHA、exact 行 pin、production per-file cap、最長行検査は**無い**です。機械 consumer が固定するのは `DW-S04` の存在・L1分類・byte slice と層合計だけで、本文の意味や逐語ではありません。

D237 の短い見出しや [T-642記録:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/output/insights/2026-08-08_t642-dw-s04-acceptance-scope/README.md:5) は旧い `Z` 単独読みを誘発し得ますが、歴史記録なので遡及編集対象ではありません。段7の worklog／insights には「`C∧Z`、Z単独は不可」を逐語で残す必要があります。

## 5. 本 wave 自身

P2 は、段4で現在の plan を採用する限り**結論は正しい**です。ただし理由を次のように固定すべきです。

- `Z=true`: docs-only で、[dev-wave.md:34–37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:34) の実装面差分はゼロ。
- `C=false`: 文面を実際に置換し、段6の焦点レビューも行う計画であり、[dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:49) の「実装しない」裁定・`4→7→8→9` 経路ではない。
- よって `C∧Z=false` で、matrix は免除されない。受入全走も [core.md:79–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79) により必須。

ただし、本文の意味を kill できる既存機械 gate はありません。例えば「裁定」条件を削除しても、H2とbyte予算を守れば `check_docs` は通ります。これを KILLED や緑として記録してはいけません。

`DW-M01` の単一理由性を満たせる実効 gate は L1予算です。段4では次を事前登録できます。

- 対象: [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79) の推奨101-byte文。
- 変異: 104-byteの意味等価案  
  `免除は段 4 で「実装しない」と裁定し実装差分ゼロの wave の変異 matrix だけ。`
- 期待: L1が `10,627 / 10,625` となり、L1超過だけで赤。
- 焦点 node: 実repoの `check_docs` を読む [test_check_docs.py:8737–8745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/orchestrator/tests/test_check_docs.py:8737) 一つに限定すれば、期待失敗 node も一つにできる。

これはbyte gateの単一理由性だけを裏取ります。曖昧さ解消そのものは機械変異では証明不能なので、代替証拠は、真理値表、異なる2レンズの敵対レビュー、consumer棚卸し、段7での逐語凍結です。実走と結果記録は親の担当です。

## 総括

`免除は「実装しない」裁定を受けて実装差分ゼロの wave の変異 matrix だけ。` — **101 bytes**（L1 10,624 / 10,625）。  
残リスクは意味 pin 不在、L1余白1 byte、D237/T-642の旧い短縮表現。pytest・変異は本子では未実走です。