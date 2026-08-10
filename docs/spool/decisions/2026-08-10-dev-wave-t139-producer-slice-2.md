---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t139-producer-slice
seq: 2
---

## {{D:t139-stage2-approval-payload}}. 追補 A 一式の承認を機械可読 payload として canonical 台帳へ固定する

**決定:** 2026-08-09 に一括承認された追補 A 一式 (再発行版・判定写像・erratum・record-items) の
承認事実を、次の payload として canonical 台帳へ固定する。この payload を fold した commit を
`F_e` と呼び、後続 wave が発行する approval manifest はこの `F_e` を
`approval_fold_commit` として literal で持つ。

```text
target_core:
  path   = output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit = 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9

approved_blobs:
  addendum_a
    path   = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md
    commit = 622bd786191d40bda388596fa2adbf119ee84c9a
    sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec
  derivation_map
    path   = output/insights/2026-08-08_t139-r4-env-probe/derivation-map.md
    commit = 7ec088163dee920f0b8e1e9783faa6e36b22b730
    sha256 = bf5b6783b5a1a0b6c495618fe5292a968e44712d857cf84bdc436dcf027f6025
  erratum
    path   = output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md
    commit = 1d235e0e455020cf54e66cf83304961910c369d8
    sha256 = a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3
  record_items
    path   = output/insights/2026-08-08_t139-addendum-a/record-items.md
    commit = 1d235e0e455020cf54e66cf83304961910c369d8
    sha256 = 1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3

erratum_application_order = [t139-core-s15-exactkey-v1]
composed_sha256           = d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82

superseded (承認されていない。同じ core 三つ組を本文に持つ旧版):
  path   = output/insights/2026-08-08_t139-addendum-a/addendum-a.md
  sha256 = 1f5612587ffeacd39285a28fb1b2e35df6e904689ec30bcc4877e85223146bdd
```

**理由:**

- 承認済み erratum は「resolver は approval manifest から `approval_fold_commit` と blob identity を
  取得する。caller の引数や受領証の自己申告からは取らない」を要求し、
  「manifest が存在しない状態で本 erratum を適用してはならない」と明記する。
  その manifest はまだ実体化していない。
- **manifest は自分自身の fold commit の SHA を literal で持てない。**したがって承認 payload を
  先に fold して `F_e` を確定し、その子孫に manifest を置く二段構成が構造的に必要である。
  本決定はその第 1 段にあたる。
- 承認済み追補 A を名乗る blob は 2 つ実在し、**どちらも同じ core 三つ組を本文に記す**。
  path だけ、あるいは本文の従属先だけで判別すると旧版が gate を通る。
  したがって payload は blob digest で pin し、旧版を非承認として名指しする。
- 合成後 digest は親が一次資料から独立に算出した
  (`F` の core blob 450 行に対し erratum の 2 operation を適用して SHA-256 を取った)。
  同じ値を本 wave の Codex 実装がテストで再現しており、手計算だけを根拠にしていない。

**却下した選択肢:**

- 裁定記録 (worklog エントリ) をそのまま trust root にする — 散文であり blob digest を持たないため、
  resolver が承認済み blob の identity を台帳から検証できない。
- manifest と payload を同一 commit へ入れる — 自己参照になり構成できない。
- caller が承認済み blob の三つ組を引数で渡す形 — どの決定がその blob を承認したかを
  resolver が再導出できず、trust root にならない。

## {{D:t139-erratum-validator-registry}}. erratum 固有の不変条件は `erratum_id` 別 validator に持たせ、未知 ID は fail-closed にする

**決定:** 凍結 core へ erratum を適用する実装は、**erratum 文書ごとに固有の受理述語**を
`erratum_id` で引く registry に持たせる。registry に無い `erratum_id` は解決失敗とする。
非重複検査・適用順序・合成後 digest の照合は erratum に依存しない共通処理として分離する。

**理由:**

- 承認済み erratum の §3 が課す検査 (operation 数がちょうど 2、対象行の `old_sha256` 一致、
  特定トークンの出現がちょうど 2 件でありその 2 行が operation 行と一致、差分が 1 トークン) は
  **その erratum 固有の主張**であり、他の erratum には当てはまらない。
- 実際、同じ core に対する第 2 の erratum が既に承認済みである。
  固有検査を全 erratum へ一律に課す実装は、その第 2 erratum を必ず誤って拒否する。
  承認済み erratum 自身が singleton 契約を捨てて exact set へ改めたのは、この事態を避けるためである。
- 未知 ID で**検査を飛ばして通す**設計は、erratum を 1 枚足すだけで受理述語を書き換える
  一般経路を開く。fail-closed だけが安全側である。

**却下した選択肢:**

- 固有検査を全 erratum へ一律適用 — 承認済みの第 2 erratum を構造的に拒否する。
- 未知 ID は共通検査だけで通す — 凍結文書の受理述語を後から緩める経路になる。
- 検査対象トークンを operation から推論する — 規則が文書に書かれておらず、実装依存の推測になる。

## {{D:t139-reference-binding-not-a-gate}}. 参照束縛の純関数は投入 gate と明示的に分離し、gate API を export しない

**決定:** 凍結 blob への参照束縛 (blob 読取・erratum 適用・追補 envelope の exact-key 抽出) を
実装する module は、**投入 gate ではない**ことを docstring で宣言し、
`resolve_effective_preregistration` / `PreregBinding` / `submit_pilot` / `verify_receipt` の
4 名前を export しない。これを機械検査で固定する。

**理由:**

- 事前登録 core の投入 gate は、承認 manifest・祖先検査・受領証照合を伴う 3 段の順序検査である。
  その部品だけが先に存在すると、**部品を組み合わせただけの経路が gate を通ったように見える**。
- 台帳だけが「producer 実装済み」へ進む半実装は、直前の wave が blocker と判定した形である。
  宣言を docstring に置き、export を機械検査で固定することで、記録と実体の乖離を防ぐ。
- 期待集合を caller が選べる汎用 API は、`a13` を欠く閉集合を渡す経路を残す。
  承認済み閉集合には**期待集合を引数に取らない専用入口**を置く。

**却下した選択肢:**

- gate API の空実装や恒真 deny stub を先に置く — 実装済みと誤認され、後から受理条件だけが凍結される。
- 汎用 API だけを提供する — caller が閉集合を選べる経路が残る。
