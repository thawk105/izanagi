---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1143-epoch-closure
seq: 2
---

## {{D:epoch-closure-verifier-twelve}}. enforcement source closure を exact 12 path へ広げ、verifier 実装を epoch へ束縛する

**決定:**

1. **閉包を exact 12 path にする。** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` へ
   `orchestrator/verifier/core.py` / `dsg.py` / `model.py` / `parse.py` を末尾へ加える。
   D268 決定 1 の「exact 8 path」を supersede する。既存 8 path の順序は変えない
   (順序は epoch preimage に効く)。検証の意味論 (記録 commit の blob と現在の disk bytes の
   一致)、停止点、fail-closed は変えない。
2. **識別子・wire key・hash domain は変えない。** `contract_loader_*` は歴史的名称として残す
   (D268 決定 2 を継承)。`campaign-verifier-epoch/v1` の domain 文字列も据え置く。
   実 corpus に v2 lock が 0 本なので旧定義と新定義が同居する実物が無く、domain を上げると
   `E1` prefix を固定する layer3 / S1 / S8b の golden まで変更面が広がるためである。
3. **`campaign_verifier_epoch` の scope 診断を真になる文言へ直す。** identity scope は
   exact 12 path と verifier 実装 4 file の包含を明記し、excluded scope は verifier package の
   うち束縛しない `__init__.py` / `__main__.py` / `cli.py` / `report.py` を exact に列挙する。

**理由:**

- 従来は E1 lock を作った後に verifier の実装 bytes だけを書き換えても epoch が変わらなかった。
  正しさ判定の実体が identity の外にあり、anomaly を含む run が同じ epoch の certified 集合へ
  入りうる状態は規律 2 に抵触する。
- 実 corpus の `output/**/campaign.lock` は 32 本すべて v1 で v2 は 0 本である (実測)。
  壊れる既存成果物が無い今が費用最小の窓であり、成果物が積まれてから広げるより安い。

**名乗ってよい範囲 (これを超えて書いてはならない):**

> `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が
> 実際に完了した呼出しについて、**各 path を検査が読み取ったそれぞれの時点の** enforcement
> source closure exact 12 path の disk bytes は、その呼出しが authority に採用した
> `contract_loader_commit` の同 path Git blob と一致した。

D268 の制限箇条書きはすべて継承する。加えて次を明記する。

- **verifier package の dispatch 面は閉じていない。** `pipeline.py` は
  `orchestrator/verifier/__init__.py` の再 export を通じて `verify_trace_dir` を解決する。
  この shim を別実装へ向ければ、束縛した 4 file の bytes を 1 byte も変えずに正しさゲートを
  無効化できる。`report.py` / `cli.py` / `__main__.py` と wrapper `orchestrator/verify.py` も
  閉包外である。
- **弱化してから作る fresh lock は拒否しない。** 本閉包が検出するのは lock 記録後の drift だけで
  ある。verifier を弱めて commit し、その bytes で新しい lock を作れば、新しい `E1` として
  受理される。「規律 2 の穴を塞いだ」とは名乗らない。
- **epoch の cross-version 認証は無い。** oracle の artifact validator は scope を非空文字列
  としか検査せず、judge は `state=E1` と `certified_eligible=true` だけで採用する。
  旧定義の `E1` を新閉包の certified 選択から排除する機構は存在しない。
- **別閉包は追随しない。** T126 qualification の code identity は verifier では `core.py` しか
  含まず、`dsg/model/parse` の変更に反応しない。

**受理集合の変化:**

- 既存 artifact は不変。v2 lock は 0 本のままである。
- v2 wire の受理言語は exact-8 key から **exact-12 key への置換**であって部分集合化ではない。
  旧 exact-8 map は拒否になる。
- 閉包 12 path のいずれかに未 commit 差分がある working tree からの certified 実行は、
  `ident` の停止点で拒否される。verifier 4 file がこの対象へ加わったことが本決定の目的である。

**却下した選択肢:**

- **`__init__.py` を含む exact 13 以上。** 段 2 プランと段 3・段 6 の敵対レビューがいずれも
  推したが、批准された裁定文が名指ししたのは 4 file である。12 / 13 / 14 / 16 の選択は
  脅威モデルの選択そのものであり、親が独断で 1 点を選ばずユーザー裁定へ返す。
- **domain を `/v2` へ上げる。** 上記 2 のとおり変更面が裁定の範囲を超える。
- **oracle 側で現行 scope の exact 一致を要求する。** 受理集合を変える新設 gate であり、
  本裁定の範囲外。択一として裁定へ返す。
