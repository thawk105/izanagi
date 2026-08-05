# [T-471] 事前登録 erratum 1 — §6 spec manifest の射程と計測器の残存限界 (2026-08-05)

- `authority: none` / `default_effect: no-state-change`
- 本文書は `preregistration.md` の erratum である。初回凍結文は消さず、判定式・arm・代入規則も
  変更しない。足すのは**射程の明示**だけである。

## 1. §6 の「spec manifest (exact path + sha256)」の射程

### 何が起きたか

凍結 §2 は「driver はこの 2 case を定数として持ち、**spec を走査・順位付けしてはならない**」と
定めた。一方 §6 は環境タグとして「spec manifest (exact path + sha256)」を要求している。
この 2 つは緊張関係にある — driver が spec を走査しないなら、driver の evidence には
選択した 2 case の spec しか載らない。

実測 attempt `rbound-a1` の evidence では `spec_manifest` が **2 件** (C2 と C1 の出所 spec) である。
凍結時点の inventory は **46 件**であった。

### 射程の確定

**§2 が優先する。** §6 の「spec manifest」は wave 全体として次の 2 つで充足しているとみなす。

1. 46 本の inventory とその走査方法・最大 case の導出は `preregistration.md` §2 が記録している
   (schema 一致で走査した旨、件数、basename glob では漏れる例も含む)。
2. driver の evidence は、実際に測った 2 case の spec について exact path + sha256 を記録している
   (C2 = `1ecd2111…`、C1 = `d22d6904…`)。これは「測った対象の同定」としては完全である。

すなわち driver の evidence 単体が 46 件を持たないことは、**採用停止事由としない**。
ただし次を認める: 46 件の一覧を機械可読な形で attempt 証拠へ焼き込んでいないため、
**将来 spec が増えたときに、この attempt の envelope が古くなったことを機械的に検出する
consumer は存在しない。** 陳腐化の検出は人手に残る。これは既知の未充足であり、
[T-360] consumer 側の照合契約 (段 3 レンズ B #4) として裁定へ返す。

## 2. 計測器の残存限界 (意図的に閉じていない)

段 6 の焦点再レビューは、fix 後も次が静的検査を素通りしうると指摘した。親はこれらを
**real と認めたうえで、追加の検出器を実装しない**と裁定した。

| 残存する bypass | 内容 |
|---|---|
| 偽 arm setup | 作成 loop を変異させても、記録される `E_by_parent` は凍結定数のままになりうる |
| 偽 source bytes | `_load_source` の第 2 引数 (source bytes) までデータフローを追っていない |
| 非交互化 | AST 検査は二重 loop の存在を見るだけで、その body が計測することまでは確認しない |
| 必須タグの構造欠落 | validator が exact schema ではないため、一部 key の欠落を通しうる |
| 凍結 case の同定 | `CASES` の値を変えても静的テストが素通りする経路が残る |

### 裁定の理由

1. これらはすべて「**将来 driver が改変された場合に**偽の値が出せる」という形の指摘であり、
   実際に走った attempt `rbound-a1` の値が偽である証拠ではない。
2. 親は代わりに、**実際の attempt の忠実性を生証拠から直接検算**した (`RESULT.md` §5)。
   交互化は生 trial 500 件の arm 列が exact round-robin と完全一致、harness は
   before = after = 実ファイル = HEAD blob 内容、E を偽った setup では出ないはずの
   entry あたり限界コストの一致 (0.2141〜0.2216 ms/entry) を確認した。
3. 本 wave の公表値は**上限ではなく診断値**である (`preregistration.md` §0)。
   結論 (`RESULT.md` §3) は R の値に依存しない。したがって計測器を更に硬くしても、
   台帳へ載る結論は変わらない。**閉じるコストが得られる保証を上回る。**

### この裁定が誤りになる条件

本 driver を**再利用して別の値を出し、それを設計判断の根拠にする**場合、上の bypass は
実害になる。その時点で driver を使い捨てから常設へ格上げする判断が要り、
本 erratum の裁定は無効になる。再利用する者はここから読み直すこと。
