---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1354-off-arm-noninterference
seq: 1
title: [T-1354] off arm の launch contract 非干渉性を generation 1 で機械検査し、閉じた範囲だけを主張へ縮小した (コード + テスト、branch worktree-dev-wave-t1354-off-arm-noninterference、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **command 前提を覆す新事実 (F35 の型)。** 引数は「[T-1347] の事前登録側は実施済みで、
  残っているのは実装面だけ」としたが、実装面の中核も 2026-08-22 に land 済みだった。
  commit `cd0a10a6` ([T-1472] 由来、archive entry 813) が `off` arm の workload 中立化、
  `arm_binding_digest_sha256` の payload からの除去、provider 向け invocation ID の分離、
  critic 中立化を入れている。worklog の `[T-1354]` は entry 650 からの stale carry だった。
  `git log -S <識別子>` で検出した。
- **それでも残っていた隙間。** 8c 事前登録 §4 は非干渉性を 3 領域へ分解して規定する。
  (i) role 入力 bytes は先行実装が閉じていた。(ii)「provider へ送る request の本体」には
  **機械検査が存在せず**、(iii) の除外 field 列挙も存在しなかった。本 wave はここを埋めた。
- **段 3 は敵対 2 レンズとも NO-GO。** 両者が独立に「`_runner` 境界は remote provider request の
  境界ではない」「generation 1 だけでは G=2 の事前登録を満たさない」を挙げた。
  親はこれを real と裁定し、**実装を広げる代わりに wave の主張を縮小した**。
  絶対規律 2 が守るのは正しさの gate であり、検査の届く範囲より広い主張をしない訂正は
  規律を強める方向である。設計判断は {{D:offarm-noninterference-claim-scope}} と
  {{D:transport-metadata-exclusion-is-candidate-only}} に記録した。
- **条件 2 は open のまま。** 証拠契約 `s8c_preregistration_evidence_contract.v1.json` の
  condition_number 2 は arm binding の単射性しか required_evidence に持たず、非干渉性を表す
  field を 1 つも持たない。評価器へ接続するには証拠契約の改訂 = 受理意味の変更が要り、
  `DECIDER_VERSION` の bump と次世代 record の発行を伴うため、既成事実にせず裁定へ返した。
- **env の非決定性を実測で見つけて閉じた。** `CLAUDE_ENV_ALLOWLIST` は `frozenset` であり、
  str の hash 乱択化で反復順が process ごとに変わる。親が 4 process で測って 4 通りの順序を
  観測した。env は dict のまま subprocess へ渡され envp 順に反映されるため、
  **同一入力でも request の envp 順が run ごとに変わっていた**。固定順化した
  ({{D:projected-provider-env-order-must-be-deterministic}})。同じ allowlist を使う s8b 側の
  provider は未変更で、s8b freeze への影響を独立裁定するため別 wave の残件とした。
- **段 6 も敵対 2 レンズとも NO-GO で、最上位所見が一致した。** audit invocation ID の期待値を
  production の helper から作っており、実装と期待が同じ関数を通るため両方同時に壊れて一致しうる
  自己 oracle だった。あわせて journal event を role を key にした dict で集めており、
  同一 role の重複 event が最後の 1 件へ畳み込まれていた。fix 1 巡で 4 件を閉じ、
  焦点再レビューが F1〜F4 すべて closed と判定した。
- **変異の事前登録を実測で 2 度組み直した。** 段 4 で登録した 8 変異のうち 5 件を段 6 レンズ A が
  「import 時 assert・既存 guard・既存テストに mask される」と静的に反証した (F277 再発)。
  実測するとさらに悪く、集合だけを変える単層変異は MISMATCH ですらなく **pytest の
  collection error** になり、失敗 node が 1 つも出ずに harness が `PARSE_ERROR` で止まった。
  両層変異へ組み直して観測 node を集め直した。最終的な帰属は
  **M1〜M4 の 4 件が新設 2 テストだけで kill**、M5 が新設 + 既存 3 件、M6 / M7 が既存 4 件との
  冗長 gate である。冗長 gate の 2 件は「既存の受理条件が弱まっていないこと」の証拠として残し、
  新設検査の検出力証拠からは外した。
- **親が F540 の禁止事項を破った。** 8 子中 6 子が `evidence_status=invalid` で不採用になり、
  親は保全成果物を `check_codex_output.py` の緑を根拠に採用へ回した。F540 は
  「不採用の成果物を採用へ回してはならない」と明示している。段 7 で気づき、段 6 の関門 3 子を
  別 `--job-id` で再投入して 2 子が受理された (レンズ A は 2 回目も不採用)。
  段 2 plan と段 3 レンズ A は再投入していない — 実装が commit 済みで結論を遡って変えられないため。
  この 2 つの成果物は不採用 receipt に立っている。詳細は
  {{F:rejected-artifact-adopted-by-content-check}} と F540 の再発記録。
  なお F540 の既知 2 原因 (web 検索の重複キー、非 NFC) は 8 子すべてで実測して否定した。
- **F540 の再投入手順自体の穴も出た。** 再投入までに fix が commit 済みで、prompt が指す
  差分 bundle が現行 bytes と食い違い、受理されたレンズが「署名対象を確定できない」型の
  NO-GO を返した ({{F:resubmitted-prompt-goes-stale-after-tree-advances}})。
- **変異 matrix の実測値。** baseline PASSED (83.5 秒)、7 変異すべて KILLED、
  期待 node は全件が完全集合として一致した (SURVIVED 0・MISMATCH 0・PARSE_ERROR 0)。
  帰属は M1〜M4 が新設 2 テストだけ、M5 が新設 + 既存 3 件、M6 / M7 が既存 4 件との冗長 gate。
- **変異本走中に worklog / decisions fragment を worktree へ書いて harness を止めた** (F106 の
  4 度目の再発)。防壁は fail-closed で働き、実害は退避と `--resume` の一手間だけである。
- **最終判定。** 段 6 の 2 レンズと焦点再レビューが残した唯一の NO-GO 理由は変異帰属の不足で
  あり、これは静的推定だった。親が変異を実測して裏取りし、DW-O16 に従って裁定で閉じた。
  実測値 (M1〜M4 が新設検査に排他的に帰属) は静的推定の 3/8 を上回る。
  受理版レンズ B は「実装 semantics に新しい blocker は無い」と明記している。

## 次の一手差分

### 更新

- [T-1347] **P2・事前登録側は実施済み (2026-08-18 の再凍結)、実装は領域ごとに部分実施**:
  role payload の契約を非干渉性として書き直した。領域 (i) は [T-1472] が、領域 (ii) の
  supervisor から Claude CLI への launch contract 部分は本 wave が閉じた。
  **残件 = 実 CLI の outbound request bytes の観測点設計、除外 2 field の role 不可視性の証明、
  凍結事前登録本文への除外 field 列挙 (再凍結セレモニーを伴う)、generation 2 以降の
  結果依存チャネルの扱い、条件 2 評価器への接続。** いずれもユーザー裁定を要する。
  base: 21fbaad984b5929ab56ae3af4f304d3f4200d1033b6f32dd6b4a4c2ab721ebf1

- [T-1354] **P2・実装面は部分完了、残件はユーザー裁定側へ移った**: role payload の閉じた key
  集合から作業種別名を落とす件と descriptor binding の digest 経路は [T-1472] が land 済みで
  あることを実測で確認した。本 wave は残っていた領域 (ii) の負の対照を置き、
  領域 (iii) の除外 field をコード側の候補列挙として明示した。
  **残件 = {{D:offarm-noninterference-claim-scope}} が open と記録した 5 項目。**
  実装として残るのは s8b 側 provider の env 固定順だけで、s8b freeze への影響が
  独立裁定を要するため別 wave とする。
  base: c573215a6214cce0d56b531ca16b66842911a96b018f583563a5a398134fb92b

### 新規

- {{T:s8c-condition2-evidence-contract-scope}} **P1・ユーザー裁定待ち**: 8c 条件 2 の証拠契約は
  arm binding の単射性しか要求せず、非干渉性を表す field を持たない。狭い regression のまま
  条件 2 を open に据え置くか、証拠契約を改訂して評価器を非干渉性へ接続するかを決める。
  後者は受理意味の変更であり `DECIDER_VERSION` の bump と次世代 record の発行を伴う。

- {{T:provider-request-boundary-definition}} **P1・ユーザー裁定待ち**: 事前登録 §4 の
  「provider へ送る request の本体」を、Claude CLI へ渡す argv / stdin と定義するか、
  CLI が組み立てる remote serialization bytes と定義するかを決める。後者なら CLI を
  black box のまま使えず、送信直前 bytes を捕獲する provider adapter の設計が要る。

- {{T:offarm-generation2-result-channel}} **P1・ユーザー裁定待ち**: generation 2 以降の
  結果依存チャネル (harness_result の metrics / outcome、critic feedback) の扱い。
  許容限界として事前登録へ明記するか、中立化機構を設計するか。現状の黙示的除外のままでは
  G=2 の非干渉性は成立しない。archive entry 813 が残した裁定待ちを引き継ぐ。

- {{T:transport-metadata-exclusion-refreeze}} **P2・ユーザー裁定待ち**: 除外 2 field
  (mcp config path、neutral cwd) の role 不可視性を証明したうえで、凍結事前登録本文へ
  exact field と根拠を反映する手番。証明できるまで本文へ書かない。

- {{T:cross-cell-env-authority}} **P2・新規**: 正式 6 cell が共有する sealed canonical env を
  導入するか、実走後の env digest の cross-cell 比較を admission 条件にするか。
  各 provider が構築時に `os.environ` を読むため、cell 間の env 同一性は production で
  強制されていない。

- {{T:s8b-provider-env-order}} **P2・新規**: `s8b_prediction_runner` の同型 provider は
  allowlist の反復順で env を作り続けており、同一入力でも envp 順が run ごとに変わる。
  固定順化は容易だが s8b freeze の bytes への影響を独立に裁定してから行う。

- {{T:evidence-invalid-reason-in-receipt}} **P2・新規**: `_evidence_status()` がどの条件で
  invalid を返したかを receipt の attempt record へ 1 field 記録する。F540 が恒久対応として
  挙げたまま未実施であり、本 wave で 8 子中 6 子が同症状になって診断できなかった。
  tool の出力契約を変えるため裁定を経る。
