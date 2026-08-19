---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t139-q1-canonical-decision-land
seq: 1
---

## {{D:t139-q1-canonical-predicate}}. T-139 の RF study 受理述語の四つの穴を canonical authority で閉じる

**決定 (1): D320 の既定を三つの対象に限って上書きする。** D320 が bytes 級 provenance 機構の新設・維持を既定で見送る定めは、次の三対象についてのみ個別裁定として上書きする。

- schema の `preregistration.approval_manifest` が参照する approval manifest 本体。
- D282 の `record_items` / `receipt_schema` の承認役割を後続で担う、新しい exact-byte approval payload。
- conformance vector index の期待 digest 三つ組 `(path, commit, sha256)`。

この上書きは D320 全体を supersede するものではなく、上記三対象以外の D320 の定めを変更しない。

**決定 (2): 追補 A の認証契約は参照束縛だけにする。** 追補 A の承認済み三つ組

`path = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md`、  
`commit = 622bd786191d40bda388596fa2adbf119ee84c9a`、  
`sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec`

に含まれる `a10`（607 行の見出し）および `a11`（755 行の見出し）を、承認 payload から参照束縛する。認証区間手続き・選択規則・終端条件はこの二節の参照先を authority とし、本決定本文で書き写したり書き直したりしない。

**決定 (3): 申告値を受理入力から常に除外する。** `arms.*.compile.trace_enabled`、`arms.*.compile.analysis_enabled`、`arms.*.compile.cmake_cache` は、いかなる場合も受理条件の入力に含めない。validator は申告値と独立に、schema の `argv` に現れる macro 定義、`compile_commands` の当該 TU の実 compile argv、実ファイル上の raw `CMakeCache.txt` を再読して三者を比較する。raw `CMakeCache.txt` の再 parse 結果を三者目とし、三者の不一致は拒否する。

申告値との一致検査は拒否条件としてのみ行う。不一致なら拒否し、一致しても申告値を受理の根拠または受理証拠にはしない。

**決定 (4): conformance vector index の trust edge を approval payload 側に置く。** vector index の期待 digest 三つ組は manifest 自身ではなく、有効な approval payload に置く。resolver は `approval_fold_commit` から有効な payload を解決し、その payload の三つ組と manifest の宣言を照合しなければならない。manifest 単独の自己 pin は受理の根拠にしない。

**決定 (5): Q1 と Q2 は一つの canonical decision に維持する。** 本決定が定めるのは Q1 の受理述語だけであり、Q2 の固定 envelope と namespaced projection の詳細はここでは追加しない。manifest の root は次の二段構成とする。

- `base_approval_fold_commit` は、D282 を canonical 台帳へ fold した commit `39d760985a5e37d20464c394760bf65596156566` を literal で持つ。
- `approval_fold_commit` は、「T-139 の承認 payload として現在有効な canonical decision を fold した commit」を意味する。初期値は `base_approval_fold_commit` と同じであり、将来の supersession 後は resolver が現在有効な decision の fold commit を解決する。

`approval_fold_commit` を単一の新規 literalへ固定して Q2 の後続 landを要求する構成にはしない。

本決定の効力は canonical 台帳への fold 後に発生する。本決定は受理述語と authority binding を定めるものであり、producer・resolver・writer・validator・vector の機械実装が完成したことは意味しない。

**理由:**

- `preregistration.approval_manifest` は schema の必須 field である一方、D282 と D291 の既存承認 role には approval manifest 本体がない。manifest・exact-byte payload・vector index の三つを承認境界へ置かなければ、受理述語は安定した authority を持てない。
- §7.1(12) は CMakeCache の再読を要求し、§8 は `arms.*.compile.trace_enabled` / `analysis_enabled` / `cmake_cache` を受理条件の入力に使うことを禁じている。schema にある CMakeCache 由来値は申告値だけなので、両要求を同時に満たすには、実ファイルの raw `CMakeCache.txt` を独立に再 parse するしかない。
- 申告値を「単独では」使わないと書くと、他の入力との併用を許す実装が残り、engine ごとに受理集合が分岐する。常に受理入力から除外し、一致は拒否条件に限定することで、この分岐を閉じる。
- 追補 A の `a10` / `a11` は認証区間・選択規則・終端条件を既に承認している。これらを本決定で再掲すると、数値契約や conformance vector の期待値を別の契約へ変える経路になる。
- manifest 自身に vector index の digest だけを pin させると、manifest と index を同時に差し替えた自己整合する偽の受領が可能になる。payload 側に trust edge を置くことで、manifest の宣言とは別の authority から照合できる。
- root を `approval_fold_commit` 一段だけにすると、新しい payload の fold 後でなければ manifest 契約を書けず、Q2 の landが Q1 の後続 landに依存する。既知の D282 fold commitを base とし、現在有効な承認 payloadを別名義で解決する二段構成なら、一本構成を保ったまま supersessionを扱える。

**却下した選択肢:**

- D320 全体を supersede する — 三対象を越えて既定を変更するため、裁定の scope を超える。
- approval manifest または vector index の承認を作らない — schema 必須 fieldと受理述語の authority bindingが閉じない。
- 追補 A の認証区間・選択規則・終端条件を本決定へ転記する — 承認済み数値契約を書き直し、受理集合と conformance vectorを動かす。
- 申告値を「単独では」受理入力に使わないとする — 他の入力との併用を許し、実装ごとに受理集合が分岐する。
- manifest 自身の vector pinだけを trust rootにする — manifestとindexの同時差替えによる自己整合を止められない。
- Q1 と Q2 を二本へ分ける、または rootを一つの新規 fold commitだけにする — 一本構成を変更するか、後続 landの循環依存を残す。
