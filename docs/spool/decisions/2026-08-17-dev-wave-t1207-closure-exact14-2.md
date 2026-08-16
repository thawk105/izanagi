---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1207-closure-exact14
seq: 2
---

## {{D:enforcement-closure-exact14}}. enforcement source closure を exact 14 path へ広げ、verifier の dispatch 面と report 面を束縛する

**決定:**

1. **閉包を exact 14 path にする。** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` へ
   `orchestrator/verifier/__init__.py` と `orchestrator/verifier/report.py` をこの順で末尾へ加える。
   D442 決定 1 の「exact 12 path」を supersede する。既存 12 path の順序と綴りは変えない
   (順序は epoch preimage に効く)。検証の意味論 (記録 commit の blob と現在の disk bytes の一致)、
   停止点、fail-closed は変えない。これは 2026-08-16 のユーザー裁定 (択 (c)) の実装であり、
   D442 が「却下した選択肢」に挙げた exact 13 以上を批准された裁定として採る。
2. **識別子・wire key・hash domain は変えない。** `contract_loader_*` は歴史的名称として残し、
   `campaign-verifier-epoch/v1` の domain 文字列も据え置く (D442 決定 2 を継承)。
   実 corpus の physical な campaign lock は 32 本すべて v1 で v2 は 0 本という実測に基づき、
   壊れる既存成果物が無い今の窓で広げる。
3. **scope 診断を実際の束縛範囲と一致させる。** identity scope は exact 14 path と
   dispatch 面・report 面の包含を明記し、excluded scope は brace 短縮をやめて
   `orchestrator/verifier/__main__.py`、`orchestrator/verifier/cli.py`、
   package 外の `orchestrator/verify.py` を実 path で列挙する。D442 決定 3 を supersede する。
4. **閉包の完全性を test-only の package census で守る。** 閉包は固定 exact list なので、
   verifier package へ module を 1 つ足して `__init__.py` の 1 行でそれを読ませれば、
   epoch を変えずに dispatch 先を差し替えられる。実 package directory を走査して
   `.py` が exact 8 件であり、うち 6 件が閉包 member、2 件が意図的除外であることを検査する。
   新 module の追加は赤で止まり、閉包へ入れるか意図的除外かをユーザー裁定へ返す。
   これは repo 不変条件のテストであって成果物の受理集合を変える gate ではない。

**理由:**

- 従来は E1 lock を作った後に `__init__.py` の 1 行を書き換えるだけで、
  `pipeline.py` が呼ぶ enforcement dispatch の解決先を別実装へ向けられた。
  同様に `report.py` の 1 行で rejection payload の `certified` field を実結果から離せた。
  どちらも exact 12 の閉包検査を緑のまま通ることを実測した。
- 実 corpus に v2 lock が 0 本である今が費用最小の窓である。成果物が積まれてから広げると
  既存成果物を壊す。

**名乗ってよい範囲 (これを超えて書いてはならない):**

> `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が
> 実際に完了した呼出しについて、**各 path を検査が読み取ったそれぞれの時点の** enforcement
> source closure exact 14 path の disk bytes は、その呼出しが authority に採用した
> `contract_loader_commit` の同 path Git blob と一致した。
> exact 12 から増えた保証は、後続の source 検査が `orchestrator/verifier/__init__.py` と
> `orchestrator/verifier/report.py` の**記録後 drift** も拒否することに限る。

D442 と D268 の制限箇条書きはすべて継承する。加えて次を明記する。

- **「gate を無効化できる」とは名乗らない。** 実証したのは (a) exact 12 の閉包検査が
  両 file の変更を見ないこと、(b) dispatch の解決先と rejection payload がその 2 file から
  制御できること、までである。棄却判定そのもの (`vr.certified`) は `core.py` 由来で閉包内にある。
  anomaly を含む run が certified 集合へ入ることは実証していない。
- **弱化してから作る fresh lock は exact 14 でも拒否しない。** 本閉包が検出するのは
  lock 記録後の drift だけである。
- **fixed-list 外の module は永久に閉包外である。** census テストは追加を赤で止めるが、
  runtime の束縛ではない。
- **certified sink の支配点は無い。** 低層 WAL writer と `pipeline.evaluate` の COMMIT は
  verifier receipt を要求せず、ident の停止点を通らずに書ける。
- **epoch の cross-version 認証は無い。** 同じ `campaign-verifier-epoch/v1` domain が
  12-path grammar と 14-path grammar の双方を歴史上指す。旧定義の `E1` を新閉包の
  certified 選択から排除する機構は存在しない。
- **別閉包は追随しない。** T126 qualification の code identity は verifier では `core.py` しか
  含まない。

**受理集合の変化:**

- 既存 artifact は不変。physical な v2 lock は 0 本のままである。
- v2 wire の受理言語は exact-12 key から **exact-14 key への置換**であって部分集合化ではない。
  旧 exact-12 map は拒否になる。
- 閉包 14 path のいずれかに未 commit 差分がある working tree からの certified 実行は、
  `ident` の停止点で拒否される。dispatch 面と report 面がこの対象へ加わったことが本決定の目的である。

**却下した選択肢:**

- **exact 16 (CLI と `__main__.py` と wrapper を含む)。** 批准された裁定が名指ししたのは
  dispatch 面と report 面の 2 file である。閉包を広げる判断は脅威モデルの選択そのものであり、
  親が独断で 1 点を選ばない。
- **domain を `/v2` へ上げる。** 変更面が `E1` prefix を固定する下流の golden まで広がり、
  批准された裁定の範囲を超える。cross-version の曖昧さは裁定パッケージへ返す。
- **oracle 側で現行 scope の exact 一致を要求する。** 受理集合を変える新設 gate であり本裁定の範囲外。
- **census を runtime gate にする。** 閉包 member 判定を実行時の directory 走査へ変えると、
  epoch が checkout の file 集合に依存して非決定になる。test-only に留める。
