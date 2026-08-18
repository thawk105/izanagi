---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: t1283-trusted-launcher
seq: 2
---

## {{D:acceptance-launcher-authority}}. 受入受領証の著者を候補外 launcher にし、bootstrap は SHA でなく構造的述語で自己限定する

**決定:** ユーザー裁定 [T-1283] (2026-08-18) の択 (b) + 暫定 (c) を次の範囲で実装する。

1. **著者の分離。** 受入受領証の内容は `tools/acceptance_launcher.py` が生成する。
   待ち手は launcher の source を Git blob から取り、`python3 -I -c` の stdin へ渡して実行し、
   保管と publish だけを担う。launcher が非 0 で終われば final receipt を publish しない。
2. **runner の実行。** launcher は `tested_tip:tools/run_tests.py` の blob bytes を同じ形で
   exec する。pathname から import しない。**この形は runner が `main(argv)` を公開している
   ことを暗黙に要求する。**
3. **schema。** outer acceptance receipt を `dev-wave-acceptance-receipt/v5` とし、
   `launcher_source_revision` / `launcher_blob_sha` / `launcher_executed_sha256` /
   `waiter_executed_sha256` / `runner_executed_sha256` を必須にする。v4 fallback を作らない。
4. **land の照合。** land は receipt の値を信用せず、Git tree から Git object ID と blob 内容の
   SHA-256 を独立に再計算して照合する。**`verdict == "child-green"` にも適用する。**
   `runner_executed_sha256` は `tested_tip` との一致だけを要求し、`tested_main` との等値は
   要求しない (runner を改訂した wave を恒久 land 不能にしないため)。
5. **bootstrap の自己限定。** `tested-tip-bootstrap` を許すのは、`tested_main` と
   `locked_main` の双方に launcher が存在せず、`tested_tip` に regular blob として存在する
   ときだけとする。**exact main SHA の pin は使わない。**
6. 既存の受理条件は 1 つも削らない。拒否は既存 `RC_AUDIT = 23` を使い、新 RC を作らない。

**閉じていない残余を決定の一部として明記する。** (i) 改変された tip 側待ち手は launcher を
起動せず受領証を自作できる、(ii) bounded / dispatch の内側の子は pathname を読み直すため
実行 bytes の束縛外にある、(iii) land verifier 自身も候補コードである。
**したがって本決定は F385 を閉じない。** いずれも [T-696] の協調境界に残す。

**理由:**
- 既存 `waiter_blob_sha` は発行側も land 側も同じ tip の tree から算出するため恒真である
  (D403 本文が自ら明記)。実測では受領証の 99.0% (全期間 103 本中 102 本) が `child-green` で、
  D487 決定 4 の main 束縛が発火したのは 1 本だけだった。穴は受入の主経路そのものにあった。
- 択 (a) (両経路で main==tip 等値を要求) は `tools/dev_wave_wait.py` と `tools/run_tests.py` を
  編集した wave をどの経路でも land 不能にする。ユーザーはこれを不採用とした。
- **exact main SHA の pin は使えない。** 本 wave の実測で main は 3 時間に 2 度動いた
  (`a160f4aa` → `8e76c41a` → `b30b95bd`)。並行 wave が常時 land する運用では、
  段 4 で pin した値は受入までに必ず stale になる。加えて pin だけでは一度限り性を担保しない
  — land は `tested_main` しか見ておらず、`_main_is_allowed` が `current != tested_main` を
  許すため、古い base の bootstrap 受領証が main へ launcher が入った後でも通り得た。
  構造的述語は SHA を含まないので stale にならず、本決定が land した瞬間に自己限定される。
- **runner の実行 bytes を自己申告させる形は採らない。** 段 3 の敵対レビューが、
  FD を束縛して pathname を実行する形には TOCTOU 窓があること、runner に marker を出させる形は
  既存テスト `test_acceptance_main_does_not_emit_nonacceptance_warning` (受入形で stdout と
  stderr がともに空であることを要求) を壊すことを実証した。blob bytes を exec する形は
  観測した bytes と実行した bytes を同一物にし、`tools/run_tests.py` を 1 行も編集しないので
  非帰属経路の runner 等値検査が本 wave 自身を弾く問題も同時に避ける。

**却下した選択肢:**
- **v4 / v5 の併存。** land が新 field を要求しない downgrade 経路が残り、F385 と同型の
  恒真ゲートを新設することになる。D487 決定 3 は 1 日前に同じ artifact で
  「v3 fallback・互換受理・警告 mode は作らない」を実行しており、その先例に従う。
- **D404 の一般則の改訂。** D404 は schema 世代交代による旧版締め出しを却下しているが、
  その具体的根拠 (並行 wave の巻き添え) は今回の母集団では実測により成立しない
  — v4 受領証を持つ wave 10 件は全件 land 済みで branch も消滅しており、稼働中 branch で
  v4 受領証を持つものは 0 件だった。**本決定は D404 の一般則には触れない。**
  ユーザーが逆を望むなら差し戻せるよう、この判断を明示して報告する。
- **親の固定起動点を launcher へ移すこと。** 起動権を wave tip の外へ出す唯一の形だが、
  lease の claim / release の主体が変わり D253 の待ち札意味論に触れる。同じ wave で
  2 つの正しさ防壁を同時に動かさないため次段へ送る
  ({{T:acceptance-launcher-outer-entrypoint}})。
- **D403 が却下した「受領証へ実行 bytes field を追加する」。** 2026-08-18 のユーザー裁定
  (択 (c)) が直接上書きするため、この点で D403 を supersede する。
  D403 の gate 自体 (投入前の待ち手 source 照合) は無改変で残す。
