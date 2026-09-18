指定資料はすべて読めました。変更・build・pytest・benchmark は実行していません。

以下、`B`＝親 brief、`P`＝s2-plan、`D設計`＝t2757-design-README、`T`＝射影された e9e477ca の transaction.cc、`IP`＝計装 patch。番号は各ファイルの行番号です。

## 所見 1: P3 と plan は、実証の合格と variant の認証を混同している

**real/refuted の判定材料:** **real、must-fix。**

B:43 の「cycle 3,754 が出たので integrity clean は恒偽」は成立しません。旧 JSON 要約:123–136 は `version_dups` を掲載しておらず、cycle と integrity は別軸です（`model.py:475–480,511–520`）。

しかし、P:338–348 の「規律2を維持するため全36走で別 integrity clean」も、必要性の論証になっていません。規律2は異常 variant の認証・採用を禁じます。故意に壊した観測用 variant の異常を保持したまま、検出器の実証を合格にすることまで禁じてはいません。旧実証も非 certified な負例を含めて all_pass です（旧 JSON:70,108–163）。

さらに hot-update/t4 には、**balanced のまま version が重複する具体的順序**があります。

1. A と B が同じ x をそれぞれ取得・早期解放する。
2. 両者が publish 前の同じ版を validation で読む（T:1000）。
3. 同じ epoch と適合する `mrctid_` の下で、両者が同じ `maxtid` を選ぶ（T:1118–1132）。
4. その後の再取得は直列でも、既に選んだ同じ版を順に publish する（P:78–85、T:1195）。

発生頻度は**不確実**ですが、全走 clean を要求すると、この許容された負例挙動だけで実証全体が赤になります。「必ず赤」とまでは言えません。

一方、P3 のように観測 t4 の **全 integrity 項目を一括免除**する根拠も不足しています。version 重複の論証から framing 不正・欠落まで免除できません。

**是正案（逐語）:**

> 実証の all_pass と各 variant の certified を分離する。全36走で終了・欠落・trace構造の完全性を要求し、異常 variant の certified を上書きしない。受入必須25走では既定の別 integrity clean を維持する。観測のみの t1 3走も別 integrity clean とし、観測のみの t4 8走に限り、負例の lock 欠落から生じ得る version_dups を記録対象として許容する。他の integrity 項目は一括免除しない。この例外は設計§7の変更として段4で明示裁定する。裁定前は現行契約を変更しない。

P:345 の共通 check を採るなら、名前も `all_runs_integrity_matches_acceptance_contract` など、実際の契約に合わせるべきです。

## 所見 2: cold/default-U の沈黙は成立するが、trace の等式だけでは前提を証明できない

**real/refuted の判定材料:** 温度上昇による反例は **refuted**。B の実走証拠の説明は **real、should（plan で修正済み）**。

e9e477ca の `ycsb.hh:59–74,128–133` を追加確認しました。指定 U は一操作の WRITE から `update()` を直接呼びます。`update()` は read set を検索しますが追加しません（T:434,477）。初期温度は `tuple.hh:80` の 0 です。

温度上昇も epoch reset も、`construct_RLL()` の read 要素かつ `failed_verification_` の内側です（T:915–953）。`TEMPERATURE_RESET_OPT=1` では leader 側の一括 reset 本体もありません（e9e477ca `util.cc:208–220`）。したがって、この U の新規プロセスでは default の温度を上げる経路は閉じています。cold 21 も到達温度の上限20を超えます（T:941–950）。

B:33 の `non_insert_writes == txns` は R 行ゼロを意味しません。P:281 の直接 `read_rows` 計数は必要です。ただし commit trace は abort した試行の read set まで証明しません。静的論証との併用が必要です。

**是正案（逐語）:**

> default-U の温度0維持は、固定 producer・U の操作生成・初期化・read_set_ 非追加から静的に導く。実走では txns>0、read_rows=0、non_insert_writes=txns、certified を確認する。これらの集計値だけで全試行の内部状態を証明したとは書かない。

## 所見 3: hot/t1 の入口を含む三 reason は発火する

**real/refuted の判定材料:** 「CLL 記録が残るので入口検査が沈黙する」は **refuted、should（論証を明記）**。

IP:57–64 は writer 記録と lock pointer 一致を確認したうえで、次の **OR** を使います。

```cpp
!izanagi_cll_has_writer ||
we.rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED
```

pending 状態の counter=0 は、CLL が正しく残っていても入口違反です。t1 では他 worker の再取得がなく、payload 前と publish 前も counter=0 のままです（IP:79–82,107–111）。再取得は三つ目の検査後なので、非空 U の三 reason 正数は成立します（P:78–88）。

t4 では他 worker が counter=-1 にして検査を通過させ得ます。owner を識別できない限界は D1686:13–14 に明記されています。

**是正案（逐語）:**

> hot/t1 は CLL writer 記録が残っていても counter=0 により入口違反となり、再取得前の保持二検査も発火する。t4 の各 reason 正数は保証しない。counter=-1 は当該 worker の所有証明ではない。

## 所見 4: U の counter 収支は合うが、一般的な無 hang 証明ではない

**real/refuted の判定材料:** U の二重 unlock・循環待ちという反例は **refuted**。一般化は **real、should**。

現物の `lock.cc:968–980` は0から-1への CAS spin、`:995` は `counter_++` です。P:107 の遷移は一致します。

U では最初の CLL は空、validation の二度目は同じ writer 要素で return するため、canonical restore に到達しません（T:721,738–759,834–858）。`vioctr>100` にも入りません。read/node set の検査がなく、DELETE もないので validation は成功し、commit が RLL を消します（T:994–1050,1208）。RLL 空はこの帰納で説明できます。

pending 再取得時には実 lock を保持しておらず、取得後に別 lock を待たないため、U の lock 待ちに循環は構成できません。ただし公平性・starvation・実時間内終了は未証明です。

多操作では、pending の stale CLL 要素を T:840 で再解放し、T:854–857 で消せます。counter=1 が残れば後の再取得は永久 spin します。abort 前の relock も、この一般的破壊を修復しません。P:140 の限定は正しいです。

**是正案（逐語）:**

> balanced の静的論証は、新負例・RWLOCK・既存recordへのblind UPDATE一操作のUに限定する。abort側relockは構造検査対象であり、U実走での動的被覆を主張しない。120秒超過は timeout failure と記録するが、timeoutだけでdeadlockの根因を確定しない。36走全体の完走はcomputeで確認する。

## 所見 5: 受入25走の check は恒真ではない

**real/refuted の判定材料:** plan の恒真性疑義は **refuted**。親の集合記述は **real、should（plan で修正済み）**。

P:302–309 は stock に `certified`、`txns>0`、write正数を要求し、新負例の cold/default の「沈黙」も stock-U 型で定義しています。X/P=0だけの合格ではありません。`model.py:505–520` 自体も空 trace を認証しません。

受入集合は次の25走です（P:188–225、D設計:191–201）。

- stock-W/U：12走
- lockskip cold/default：4走
- permutation hot/cold t1：2走
- early-unlock hot/cold t1：2走
- hot-update hot t1：1走
- hot-update cold/default：4走

B:43 の列挙には lockskip cold/default t4 の2走が抜けています。また「t1負例」は観測のみの3走まで含む曖昧な表現です。

**是正案（逐語）:**

> 受入必須はmatrixで列挙した25走、観測のみは11走とする。「t1負例」などの略記で集合を再定義しない。空trace、writeゼロ、cold/default新負例の非certified、観測走の欠落・timeoutを入力変異で拒否する。

## 所見 6: 条件 gate の形は適合するが、TRACE 隔離の確認には組合せが一つ不足する

**real/refuted の判定材料:** exactly-one・名前解決の疑義は **refuted**。確認範囲の不足は **real、should**。

P:30–36 は裸 directive 一回で、両腕に pointer 宣言があります。gate の exact 行一致要求（`condition_meaning_gate.py:2935–2943`）と、非 template の discarded statement の名前解決に対応しています。

ただし P:501–502 が実測するのは **macro=0、TRACE=0**。これでは ON 側の `TRACE != 0` を誤って `true` にした変異を検出できません。TRACE 隔離を名乗るなら **macro=1、TRACE=0** も対象です。

`[[maybe_unused]]` は警告抑制であり、TLS symbol 消失の証明ではありません。最適化後の `.text` 一致・symbol 不在は期待できますが、今回は未実測です。無patch↔計装のみの論理行比較と、新負例OFFのbinary比較を分けた P:97 は適切です（D1687:3–15）。

**是正案（逐語）:**

> TRACE=0では新macroの0/1双方について診断symbol・TLS状態が残らないことを確認する。新負例のbinary同一性と、無patch↔計装のみのD1687論理行列同一性は別の証拠として記録する。

## 所見 7: 保証名は限定されているが、時間予算は上限の裏付けを持たない

**real/refuted の判定材料:** 保証名の過大化は **refuted**。P6の確度は **real、should**。

P:253–262 の保証名と P:489 の限定は D2134項4に沿っています。`hot_path_evidence` という key 単独から4 site被覆を主張してはいません。method の文字列検査自体は実行証拠ではなく、hot/t1 の実測 check と合わせて意味を持ちます。

時間について、login の合成trace一点から compute の速度方向、U/t4の300〜800万txn、総20〜25分は導けません。P:520–526 の留保と、最大待ち時間の和36,720秒という検算は正しいです。regime分割も一走の900秒不足は解決しません（P:528）。

**是正案（逐語）:**

> 20〜25分は未検証の見積であり、computeの速度方向とU/t4のtxn数は不確実とする。RUN timeout、verifier timeout、job walltime超過を区別して記録し、部分JSONをall_passへ昇格させない。分割・予算変更後も失敗した初回の証拠を保持する。

## 所見 8: 親 brief の「6件確定」と一部アンカーは不正確

**real/refuted の判定材料:** **real、nit。**

B:30 の「現物で実測」「6件の確定」は、静的読解、未実測のhang、別waveの稼働情報を混ぜています。B:35 自身がhang未実測と認めています。型・温度・Uのコード上の根拠は確認できましたが、全6件の実証完了ではありません。

主要な登録アンカーは概ね一致します。細部では：

- `_DIRECT_SAFE_ALLOWLIST` の定義開始は `test_ccbench_spawn_sites.py:45`。B:36の42ではありません。
- `allowed_non_variant_tokens` は `test_p3_s4_loop.py:7867`。
- P:557 が批判する R行の等式は B:31ではなく **B:33**。
- 旧 `_verify` の現行定義開始は `s3_mocc_lock_coverage.py:387`。P:161等の391は関数途中です。

なお、旧 `_run_checked` は timeoutを `RuntimeError` に包みます（旧driver:105–111）。新 `_verify` が再利用する際は cause を識別しないと、計画した `timed_out` を正しく保存できません。

**是正案（逐語）:**

> §3は「未確定6項目の現状整理」と改題し、静的確認済み・compute未確認・別wave対応中を区別する。参照は関数名と現行行番号を併記する。新verifier wrapperは旧helperの例外causeからtimeoutを識別し、その経路を模擬検査する。

## 総括

- **must-fix:** P3の例外範囲とplanの全36走clean要件を、variant認証と実証合格を分けて段4で確定する。cycleをversion重複の証拠にせず、観測t4の全integrity一括免除もしない。
- **P3の当否:** 限定した例外は規律2の緩和ではありません。ただし現行設計§7からの変更なので、黙って採用できません。親の根拠と対象集合は修正が必要です。
- **hangの判定:** 新負例のU限定ではcounter収支と循環待ち不在の静的論証は成立。starvation・120秒内終了・36走全体の完走は未確認です。多操作への一般化は不可です。
- **親briefへの異議:** integrityの推論、受入集合の抜け、R行ゼロの証明、「6件実測確定」、時間見積の確度を訂正すべきです。cold/default沈黙とhot/t1三reason発火には、今回の読解で反例を見つけませんでした。