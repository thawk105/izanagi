---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1140-t330-claim-authority
seq: 2
---

## {{D:claim-liveness-exclusion-scope}}. campaign claim の排他は生存プロセス単位とし、保証範囲を同一ノード・共有 out_root に限る

**決定:** claim record に必須 `protocol_digest` (64 桁小文字 hex) を持たせ、同一 protocol digest の
claim があり、その持ち主が**生存していると確認できたときだけ**拒否する。生存の判定は
同一 boot_id かつ `/proc/<pid>/stat` の第 22 field が record の `proc_starttime` と一致し、
かつ state field が `Z` でないの 3 条件をすべて満たす場合に限る。pid 再利用 (starttime 不一致)、
zombie (`Z`)、`/proc` 不在はいずれも DEAD として**通す**。別 boot_id は判定不能として通す。
claim root を列挙できない、`/proc` が permission / I-O で読めない、既存 record が破損している
場合は通さず error にする。claim の release・stale 自動削除・期限切れ回収は導入しない。

排他の**保証範囲は「同一ノード・同一 boot・共有 out_root」に限る**。この機構を
「protocol 単位の global な排他」と表現してはならない。別ノードの持ち主の生死は `/proc` からは
判定できず、別 out_root を与えられた実行同士はそもそも同じ claim root を見ない。

**理由:**
- 排他の単位を run 識別子から protocol へ移す必要があるが、寿命まで protocol 単位にすると
  床値 campaign が 1 回で永久停止する。同 campaign は固定 protocol を pilot mode で繰り返し
  投入する運用であり、claim leaf は release も stale 回収も持たない。
- 生存判定に必要な材料 (pid・proc_starttime・boot_id) は claim record に既に入っている。
  親の実測では `/proc/<pid>/stat` の第 22 field は他ユーザーの process でも読めた。
- pid だけでは pid 再利用で偽の LIVE が出る。starttime との組で消える。
  reaping されない crash owner が zombie として残ると starttime も一致してしまうため、
  state field も見る必要がある。
- 判定できないものを「生きている」と扱うと、裁定が退けた永久停止と同じ結果になる。
  判定できないことは記録し、拒否の根拠にはしない。

**却下した選択肢:**
- protocol 単位の永久 claim — 床値 campaign を 1 回で永久に止める。回復手段が claim ファイルの
  手動削除だけになり、それは leaf が「持たない」と明言した経路である。
- 別ノードの生死を scheduler へ問い合わせる — クラスタ全体で正しく効く唯一の案だが、
  Python から scheduler を叩く経路の新設を伴い、混ぜると生存プロセス単位の検証が薄まる。
  独立した次の判断として分ける。
- 双方拒否を短命 lock で直列化して必ず一方を通す — 「release も期限切れ回収も持たない」という
  leaf の設計原則に抵触し、scope も広がる。双方拒否は正当な逐次投入では起きず、
  両者が死ねば次の投入が通るため永久停止しない。

## {{D:submitter-receipt-authority-scope}}. submitter 所有 receipt を理由付きで authority と認め、hostname は authority に数えない

**決定:** floor の submit receipt (`pegasus-floor-submit-receipt/v1`) を、
scheduler が付ける `PBS_JOBID` と束縛されているという理由付きで authority として明示的に認め、
`job_script_sha256` と `nonce` の照合を Python 側にも入れる。照合は site 判定・calibration
検証・subprocess・環境変数の直読みを持たない pure leaf に置き、既存の静的 admission も
同じ leaf の consumer にする。receipt の不在・空・truncate・schema 不一致は、
claim・output・WAL のいずれの副作用よりも前に拒否する。

**hostname の一致は authority ではなく drift の検出として計上する。** 拒否条件にも
「どのノードで測ったか」の証明にも使わない。

receipt を読む gate は `schema_version` を**最初に**検査してから他の field を読む。

**理由:**
- 同じ照合は shell wrapper の中に既にあるが、wrapper を通らない呼び手 (Python の直呼び) には
  無かった。効かせたい先はそこである。
- 恒真ではない、という限界は正確に記録する必要がある。呼び手が用意できない値は
  実行時の PBS 環境が本物であることに依存しており、照合そのものは環境変数同士の一致である。
- 非特権のまま UTS namespace を作れば hostname も FQDN も呼び手が変更でき、boot_id は変わらない。
  live な OS 状態は呼び手の namespace 権限の外にあることを実測しない限り authority に数えない。
- receipt schema は 2 系統あり、`nonce` という同名 key が片方にしか存在しない。
  schema を先に見ないと別系統の receipt を誤って受理する。

**却下した選択肢:**
- hostname だけ入れて残りを別タスクへ送る — authority でないものを authority として台帳に載せる
  ことになり、直そうとしている恒真ゲートを 1 つ増やす。
- 既存の静的 admission 関数をそのまま呼ぶ — 循環 import になり、compute site と active
  calibration を要求するため、login ノードや通常の単体テストから呼ぶと receipt が正しくても落ちる。
- oracle 経路にも同じ receipt gate を配線する — oracle を起動して floor receipt を運ぶ実 producer が
  存在せず、配線すれば正当な実行が常に拒否される。producer が実在してから別途判断する。
