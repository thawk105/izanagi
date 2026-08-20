---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1441-unit3-d574-audit
seq: 1
---

## {{D:t1441-b1-compile-commands-macro-name-fix}}. T-338単位3のB1実装をD574決定(3)の三者比較が実際に機能する状態へ修正する

**決定:** `orchestrator/submission_gate/_semantic_validator.py`の`_validate_compile_legs`
(D574決定(3)が要求する schema argv・compile_commands実体・raw CMakeCache.txtの三者比較を
実装するB1本体) について、compile_commands脚が検索するmacro名を`"CCBENCH_TRACE"`/
`"CCBENCH_ADD_ANALYSIS"`から`"TRACE"`/`"ADD_ANALYSIS"`へ修正する。schema argv脚
(`configure_argv`/`argv`) とraw CMakeCache脚は無改修のまま`CCBENCH_`プレフィックス付きを
維持する。

**理由:**
- `external/ccbench/cmake/Options.cmake`の`ccbench_universal_definitions`は、CMakeキャッシュ
  変数`CCBENCH_TRACE`/`CCBENCH_ADD_ANALYSIS`を`TRACE=`/`ADD_ANALYSIS=`というプレフィックス
  なしの名前へリネームしてコンパイラへ渡す (`ProtocolHelpers.cmake`の`target_compile_definitions`
  経由)。したがって実際の`compile_commands.json`には`-DTRACE=`/`-DADD_ANALYSIS=`が現れ、
  修正前が検索していた`-DCCBENCH_TRACE=`/`-DCCBENCH_ADD_ANALYSIS=`は決して現れない。
- 修正前の実装は、正当なCCBenchビルドから生成された受領証を含め、compile_commands脚が
  常に拒否する状態だった。これはD509裁定パッケージV1が言及した「semantic validatorを
  常時拒否 (受理集合が空)」の状態そのものであり、D574決定(3)が字面上要求する三者比較の
  「構造」はあっても「機能」していなかった。
- schema argv脚 (CMake configureコマンドライン形式、`cmake -S . -B build -DCCBENCH_TRACE=0`)
  は、CMakeキャッシュ変数への直接代入構文であるため`CCBENCH_`プレフィックス付きが正しく、
  こちらは修正不要と判定した。configure時の変数名とコンパイラマクロ名が異なるという
  CCBench側の構造 (`ccbench_add_protocol`によるリネーム) を、修正前の実装は考慮していなかった。
- 段6敵対レビュー2本 (裁定準拠監査レンズ・回帰境界条件レンズ) がいずれもreal所見なしと判定し、
  変異事前登録2件 (compile_commands脚の各macro名を旧値へ戻す変異) が本走で2/2 KILLED・
  SURVIVED 0・MISMATCH 0となったことで、修正が意図どおり機能することを確認した。

**却下した選択肢:**
- 修正せず監査結果のみ記録してユーザー裁定へ返す — ユーザー裁定 (Q-B=択(a)) は「別waveとして
  直ちに監査する」ことを求めており、監査の結果 (D574決定(3)を満たしていない) が判明した場合の
  fix自体は、修正内容が小規模・設計択一の余地がない明確なバグ修正であったため、本wave内で
  完結させる方が規律5 (段階導入・盛らない、不要な追加waveの起票を避ける) に照らして適切と
  判断した。
- correctness_evidence脚のminItems制約や`ReceiptSchema`のdocument再ハッシュ欠如も同時に
  修正する — いずれもD574決定(3)自体が要求する三者比較の欠陥ではなく、別契約 (§7.1(1)の
  correctness_evidence必須件数、schema loaderの構築経路) に属する。scope creepを避け、
  次のtaskへ切り出して記録するに留めた (worklog fragment参照)。
