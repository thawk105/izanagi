## 攻撃した仮説と結果

1. 偽の緑: condition gate テストは実体を通っており refuted。ただし driver の M3 検査は未実装かつ未テストで real。
2. 恒真な保証: 空集合でも通る等の恒真 assertion は見つからず refuted。重複検出は nit。
3. 既存テストの弱体化: 反転、緩和、skip、削除は見つからず refuted。
4. prebuild 情報なしの挙動保存: 静的には bytes 同一と言え、refuted。
5. job body の拒否穴: K2 env の全状態を分類したが、K2 identity だけを通す vector はなく refuted。
6. 規律 6: 本文内容から分岐、argv、path 解決への新規 influence はなく refuted。

撤回済み A-2 は所見に採用していない。

## real 所見 (must-fix)

- [real] driver 入口の manifest/coder-role 相互必須が未実装で、M3 テストも欠落している。

  `parse_args` 後に要求された検査がなく、manifest は解決されます (`orchestrator/campaign/p3_s4_loop.py:2378`, `:2428-2430`)。その後 `_prepare_knowledge_campaign` が manifest digest を campaign identity に入れ、受領証も書きます (`:1340-1371`, `:2489-2494`)。しかし coder role がない場合、`knowledge_input` を意図的に `None` へ落として loader に渡します (`:2529-2537`)。loader は結果として「両方なし」と判定し、非 K2 schema を選びます (`:2114-2143`)。

  再現 argv は `--run-iteration P --knowledge-manifest M`、`--coder-role` 省略です。これは裁定の確認済み fail-open と同一で、裁定は run-iteration に限定した argparse 直後の拒否を要求しています (`stage4-ruling.md:33-48`, `:110-111`, `:138`)。

  job 契約の正例は Python stub が `-m` argv を保存するだけで、driver を実行しません (`orchestrator/tests/test_p3_s4_loop_job_contract.py:1181-1212`, `:1275-1301`)。これは M6 の shell 配線テストとしては正しい一方、M3 の代替にはなりません。統合 diff の driver テスト追加は condition gate の2件だけです (`snapshot-integrated.diff:103-256`)。

  放置時の成果物影響: K2 manifest digest と知識受領証を持つ campaign に、K2 schema、anomaly、参照 index 検査を通らない proposal が BUILD_START と certified 選択へ入れます。

- [real] 検査中に live source が snapshot から変化しており、snapshot は「本 wave の全変更」ではありません。

  snapshot の helper は `source_root` と `genome` を受け、`buildcache._v2_commands` から token を抽出します (`snapshot-integrated.diff:23-62`)。一方、現在の source はそれらを受けず、`_normalize_fetchcontent_source_dirs` と直接組み立てを使用します (`orchestrator/campaign/p3_s4_loop.py:330-360`)。呼び出し側も snapshot (`snapshot-integrated.diff:89-98`) と live source (`p3_s4_loop.py:1726-1734`) で異なります。

  放置時の成果物影響: review レポートと受入判断が、実際に commit される実装とは異なる bytes を参照します。snapshot を再生成して最終 bytes を再確認する必要があります。

## refuted 所見

- [refuted] condition gate テストは両層を stub 化していません。テストは `_require_condition_gate` を実体へ戻し、停止用に `_run_process` だけを差し替えています (`snapshot-integrated.diff:152-175`)。実体は `capture_define_inputs` と `evaluate_define_supply_effectuation` を順に呼びます (`p3_s4_loop.py:363-385`)。capture は引数を immutable tuple に保存し (`condition_meaning_gate.py:802-841`)、supply 実体は configure context を作成します (`:2498-2553`)。probe はその実体内の configure 実行点 (`:1663-1675`) で停止します。

  token 比較も単なる自己一致ではなく、個数5と名前集合を別途要求しています (`snapshot-integrated.diff:220-235`)。空集合化では緑になりません。

  放置時の成果物影響: なし。少なくとも M1/M2 が狙う configure argv 配線は実体経路で検査されています。

- [refuted] prebuild 情報がない経路では helper 自体を呼ばず、従来形の `_require_condition_gate(sub, genome)` を呼びます (`p3_s4_loop.py:1723-1724`)。新しい既定値 `configure_args=()` (`:363-366`) は、旧来の `capture_define_inputs` の既定値と同一です (`condition_meaning_gate.py:802-807`)。空 tuple は configure argv へ何も追加しません (`:1656-1670`)。

  放置時の成果物影響: なし。linux-baremetal を含む receipt なし経路の configure argv、gate record、受理集合は変わりません。

- [refuted] job body の K2 env 受理集合に抜けはありません。M=manifest、R=role、C=classification、D=de-novo、P=proposal とすると:

  - K2 受理: M/R/P が非空、C/D は未設定または非空。
  - K2 拒否: M/R/C/D のどれかが設定済みで、MまたはRが未設定・空、C/Dが設定済み空、またはPが未設定・空。
  - 非 K2 proposal: M/R/C/D が全て未設定、Pが非空。
  - fixture: M/R/C/D が全て未設定、Pが未設定または空。

  設定済み検出、必須値検査、proposal 必須検査は `tools/pegasus/p3_s4_loop_pegasus.sh:54-97`、安全な array 展開は `:580-592` です。従って job body 経由で K2 identity を持ちながら K2 consumer を省く env vector はありません。

- [refuted] 既存テストの弱体化はありません。job 契約テストの変更は追加で、既存 proposal fragment は K2 argv を含むよう強化されています (`snapshot-integrated.diff:257-398`)。新規 runtime 検査も actual shell body の rc、stderr、結果ファイル不在、driver argv を確認しています (`test_p3_s4_loop_job_contract.py:1009-1329`)。

- [refuted] 規律 6 の新規違反はありません。job body は manifest、role、proposal の本文を読みません。env 値を引用済み argv 要素として転送するだけです (`p3_s4_loop_pegasus.sh:77-96`, `:580-586`)。driver の K2 分岐は role 出力本文ではなく明示 CLI role で選ばれ、role 出力は schema と semantic 検査後に proposal 部分だけが抽出されます (`p3_s4_loop.py:2045-2070`)。

## nit / backlog

- M4-M6 は静的 fragment mutation と runtime/argv 検査の双方が同じ変異を赤にします (`test_p3_s4_loop_job_contract.py:650-676`, `:1055-1113`, `:1275-1301`)。恒真ではなく防御の重複ですが、「別の検査も赤にするか」への答えは yes です。成果物の値、受理集合、参照への影響を1行で示せないため nit とします。

- condition 正例は `dependency_prefix` を helper に直接注入します (`snapshot-integrated.diff:204-228`)。実 job は `CMAKE_PREFIX_PATH` を環境へ export し、main から `dependency_prefix` を明示転送していません。subprocess は環境を継承するため (`condition_meaning_gate.py:1554-1569`) 現行動作を破る根拠はありませんが、job からの exact argv を証明する E2E ではありません。成果物影響を特定できないため nit です。

## 総括

must-fix は2件です。特に driver の manifest-only fail-open は裁定済みの正しさ境界が未実装のままで、受入不可です。job body の env 拒否、condition gate の実体経路、receipt なし経路、規律 6 には別の穴を確認できませんでした。

テストは指示どおり実行していません。書き込みも行っていません。