## 「実装面の変更は不要」の検証

**既存 CLI の能力は確認できたが、診断 job 全体についての「実装面ゼロ」は立証されていない。**

[plan:51–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s2-plan-out.md:51)の実行には、以下が必要になる。

- 計算ノードで動かす投入本文と、CLI の出力を保存する shell 手順。
- pinned source／stock コピー、gflags・glog の build/install、依存 cache の指定。
- t316 と同じ compiler、CMake、configure 引数、環境の再現。

既存 [PBS:109–112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:109)は probe の起動に固定され、CLI 切替口がない。依存 build は [probe:1842–1848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py:1842)の内部処理であり、その install 先は終了時に削除される（同:2630）。既存 PBS への CLI 追記も、実行時 PBS のハッシュ照合（PBS:77–81）をそのままでは通らない。

**新たに組み立てる PBS／shell／harness は、使い捨てでも repo 外でも、依頼が定義する実装面に当たる。** 環境変数の指定や既存 build の実行だけをコード変更と数える必要はないが、それらを新しい診断経路として接続する実行本文は別である。plan は「gate の改修不要」と「診断経路の実装不要」を混同している。

新しい実行可能物を一切足さず、**同等環境で同じ診断を得る具体的経路は、指定資料内にはない**。既存 CLI 単体で `evidence.detail` を出せることは確認できる（[gate:4198–4213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py:4198)）が、repo 全域に経路が存在しないとまでは断定しない。

## 追加 job の費用対効果

**今回の停止を記録するだけなら追加 job は不要。原因に即した対処を選び、本題の実測を続けるなら診断の価値はある。ただし、独立した CLI job が必須とはいえない。**

親の原因特定に足りないものを一行でいうと、**当該走行が「rc=0＋未使用変数警告」で停止したことを示す、失敗箇所・終了コード・stderr がない。**

[親分析:87–92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/analysis-1-configure-failed.md:87)は有力な構造的説明だが、[gate:1604–1622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py:1604)では起動失敗、非ゼロ終了、成功時 stderr が同じ理由コードになる。他 job の警告は今回の停止原因の直接証拠ではない。追加 CLI job も、取得できるのは**再現走の証拠**であり、実測1の失われた stderr そのものではない。

追加 job なしで閉じる場合、成果物に書ける範囲は次のとおり。

| 成果物 | 書けること | 書けないこと |
|---|---|---|
| insight | commit・ノード・job に限定した条件関門到達、`configure-failed`、比較未到達、有力な原因仮説 | 今回の stderr／rc、原因の実測確定、恒久的な到達不能 |
| worklog | 一走の実施、部分成果、未達条件と阻害要因 | 両タスク完了、新契約の緑を実測済み |
| decisions | 親が実際に下した継続・分割・保留の判断 | 未観測の原因を確定事実にすること、D1856 の解除 |

継続するなら、新規 CLI harness の作成・同等性確認・その後の t316 再走と、plan:70 の局所的な stderr 出力を伴う t316 再走を比較すべきである。**「既存 CLI だから最安」という優先順位は未立証**である。

## T-2519 / T-2505 を閉じられるか

**現時点では完了判定と残作業を分けるべきである。共通の実測1を双方から参照することはできる。**

- T-2519 は「既存機構でinert要求がstock同等の緑へ到達する**か**」の実測を求める。
- T-2505 は「t316 driver 自身が `stock-inert-preprocess-root-location-only` の**緑に到達する環境**」を求める。  
  出典：[台帳:15–26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md:15)。

実測1は「**inert 比較そのものの手前で落ちている**」（[measurement:73–75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md:73)）。したがって、依頼の「満たせないと段1で分かった時点で分ける」に沿い、今回の共通一走で両件を満了できるという前提は取り下げる。将来、一走で双方の証拠を得られる可能性まで否定する必要はない。

T-2505 は明確に未完。T-2519 は限定された否定的観測を得たが、これを全面完了とする根拠は足りない。ただし、**T-2519 に緑を必須とする新条件を追加するのも誤り**である。

台帳には「当該 commit の t316／`BACKOFF_FIXED=-1` は outside 条件関門で configure 赤。inert 比較未到達。T-2505 の新契約緑は未実測。T-2519 は先行観測を取得し、到達性判断を残す」と記すのが妥当である。

## 親 brief の誤り

1. **赤でも同じ receipt 形式が得られるという期待が過大。**  
   [brief:17–18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md:17)は supply entry と `comparison` を完了条件にし、「緑でも赤でも実測は成立」とする。しかし admission 拒否は [probe:1967–1972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py:1967)で例外となり、summary 生成（同:1922–1924）へ戻らない。S6 全体は blocked observation に置換される（同:2568–2569）。

   **期待は条件付きなら成立する。** family が返り、S6 の返却・保存まで進めば summary は残る。今回の admission 拒否経路では最初から残らない。D1849 の `.get("comparison")` は summary 関数の赤 record 対応であり、実経路でその関数へ到達する保証ではない。

2. **「一走で両方満たせる」は反証された。**  
   [brief:45–48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md:45)の P1-1 は完了の断定として撤回が必要。P1-2 の「条件関門まで到達」は成立したので、全体を誤り扱いしてはいけない。

3. **bytes 不変を継続実測にも絶対適用すると、必要な診断まで禁止する。**  
   [brief:53–54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md:53)は実測1の条件として有効。ただし局所的な観測出力を採るなら、ここを明示的に改訂し、新 commit の別観測として扱う必要がある。受理集合の維持と bytes 不変は別の条件である。

また、親分析:112–114の情報欠落をすべて D1849 に帰す説明は不正確である。**evidence mapping の省略と、例外による supply entry 全体の喪失は別問題**である。

## scope の滑り

**gate・検査・台帳・一般化を追加する方向への明白な逸脱は確認できない。** plan:70 の失敗 detail 出力は、現に発生した停止の診断であり、仮想リスク対策ではない。

止めるべき境界は、[plan:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s2-plan-out.md:58)の「原因に必要な環境修正等」を無限定に実行するところである。未使用引数削除、警告抑制、検査側だけの patch 適用は単なる環境整備とはいえない。検査した木・要求と、実際に build する木・要求の一致を維持できる具体案として裁定する必要がある。

逆方向では、[親分析:107–108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/analysis-1-configure-failed.md:107)の「直し方の設計択一は scope 外」を理由に、**両タスク完了として閉じるのは狭めすぎ**である。今回を部分成果として閉じ、未完項を残すことと、本題を完遂したとすることを区別すべきである。

## 成立しなかった攻撃

- 既存 CLI は詳細を出せない、という攻撃は不成立。supply の `canonical_json()` を出力する。
- plan が CLI の緑で T-2505 を閉じようとしている、という攻撃は不成立。t316 実経路の再測定を明記している。
- 局所 stderr 出力案が D1849 や D1625 を必ず破る、という攻撃は不成立。提案どおりなら receipt mapping と受理集合を変更しない。
- 無改変 t316 は条件関門へ到達できない、という攻撃は実測1に反する。

静的検査のみ実施した。テスト・job は実行していない。

## 総括

「実装面ゼロ」を撤回し、具体的な CLI 診断経路と局所出力付き t316 再走のどちらが必要最小かを裁定する。  
両タスクの完了判定を分け、実測1は configure 赤・比較未到達として残す。  
継続実測に必要な局所変更と、受理条件緩和・検査対象のすり替えとの境界を具体案で確定する。