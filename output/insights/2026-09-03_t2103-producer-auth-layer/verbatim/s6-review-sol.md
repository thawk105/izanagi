## 総括

must-fix は 8 件です。最大の問題は、baseline 関数呼び出しは 2 回分存在しても実際の候補境界を通らない case があり、さらに raw POS-1 と raw C1 baseline が既存 `incomplete_set` 拒否を受けても `SURVIVED` と記録されることです。したがって、予定されている raw 候補 3 kill と raw 勝者の decision は支持されません。

既知の `BASE_COMMIT` による `contract-loader-drift` は所見から除外しました。追加実走はしていません。親記録どおり既存 tracked file と既存期待値の変更はありません。

## must-fix

- **MF-1: baseline は全 case で実測されていない。** [test_p3_b4_producer_auth_experiment.py:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:529) は issuer/raw の実 probe を `prototype_enabled` 時だけ呼ぶため、issuer の C0/R/D/POS と raw の C0/D/POS baseline は候補境界を一度も通らず、既定の全 false observation を返します。  
  放置時: baseline 拒否が `SURVIVED` 扱いとなり、増分 kill 数と候補順位が変わり得ます。

- **MF-2: raw の正常経路が既存拒否でも緑になる。** [test_p3_b4_producer_auth_experiment.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:266) の `_assembly_probe` は publication だけを発行して attempt artifact を生成せずに assembly を呼び、既存 producer は欠落 artifact を拒否しますが、[同:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:284) は `producer_auth_mismatch` 以外を単に false へ潰しています。  
  放置時: raw POS-1 は既存拒否なのに受理扱いとなり、raw C1 baseline も拒否を隠されるため、raw の増分 3 kill と raw 勝者が偽陽性になります。

- **MF-3: `existing_gate_rejected` が観測値ではなく case 名から作られている。** [test_p3_b4_producer_auth_experiment.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:543) は raw-R だけを無条件に既存拒否とし、probe が返した他の既存拒否を受け取る表現を持ちません。  
  放置時: baseline 拒否後に prototype guard が先に拒否した case が候補の KILLED に混入し、受理集合と帰属が変わります。

- **MF-4: R/D の一部は登録した入力を production 経路へ投入していない。** [test_p3_b4_producer_auth_experiment.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:499) は issuer の R/D と raw-D で rogue file を別ディレクトリへ書くだけで probe に渡さず、[同:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:365) は frozen-R と frozen-D の双方を同じ post-assembly 差し替えとして実行しています。  
  放置時: 分子に入る issuer/frozen の R 結果と、対照である D 結果が別の入力位置の値になり、decision と残存穴の記述が変わります。

- **MF-5: prereg は独立した承認物ではなく、検証対象コードから走行直前に生成される。** [test_p3_b4_producer_auth_experiment.py:1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1048) は `canonical_preregistration_bytes()` の出力をそのまま「承認済み」入力にし、[p3_b4_producer_auth_experiment.py:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:930) の prereg 内容には trust anchor 自体もありません。  
  放置時: mutation、期待 matrix、anchor をコードと同時に変更して再生成でき、測定前固定という decision の前提が消えます。

- **MF-6: ABORTED case をゼロ kill として decision を出せる。** [p3_b4_producer_auth_experiment.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:627) は six-case completeness を検査せず `incremental_kill` の合計だけで必ず leader を作ります。  
  放置時: 破棄失敗や欠測が SURVIVED 相当のゼロとして順位へ入り、不完全な比較から勝者が選ばれます。

- **MF-7: 変更閉包が experiment module を数えていない。** [p3_b4_producer_auth_experiment.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:309) の production file 数は `1/1/3` ですが、全候補の実 callsite が runtime に experiment module を import するため、裁定 A6 に従えば少なくとも `2/2/4` です。  
  放置時: report の変更費用が各候補 1 file 過少になります。今回は共通加算なので現在の tie 順序自体は変わりません。

- **MF-8: R/D の exact byte 単一性が検査されていない。** [p3_b4_producer_auth_experiment.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:223) は R/D を `true`/`false` の短い token として登録しますが、[test_p3_b4_producer_auth_experiment.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:970) の W07 検査は C0/C1 だけを対象にしています。  
  放置時: prereg bytes と実際の構造変換がずれたり複数箇所候補が存在しても走行でき、case outcome と単一理由性が変わります。

## 恒真な保証と機構を通らない緑

frozen の述語自体には恒真部分は見当たりません。[p3_b4_producer_auth_experiment.py:540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:540) は digest と固定 anchor の不一致だけを拒否し、具体的に `producer_sha256="0"*64` なら偽側へ入り拒否されます。C0/C1 の実 producer byte 変更も同じ拒否入力です。

一方、機構を通らない緑は MF-1、MF-2、MF-4 にあります。特に [test_p3_b4_producer_auth_experiment.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1023) の raw POS-1 は「正常 assembly 成功」ではなく「producer guard 以外の拒否」を `not _assembly_probe` として受理しています。

trust anchor に結果依存の循環更新経路は見当たりません。固定 mapping を case 前に検査しています。ただし MF-5 のとおり、anchor は独立 prereg に凍結されていません。

## 帰属と単一理由性

`classify_case` の式単体は baseline rejection を優先し、候補本人の guard だけを KILLED にする正しい形です。[p3_b4_producer_auth_experiment.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:601) 問題は入力 observation が MF-1からMF-4 のとおり実測を表していない点です。

W01-W09 の一対一性は未成立です。[test_p3_b4_producer_auth_experiment.py:852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:852) が確認するのは、9 個の文字列が重複せず callable を指すことだけで、mutant の適用も failing node 集合の計測もありません。

静的にも複数落ちが確定する例があります。

- W01 を repository guard の `!=` 反転と解釈すると、[同:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:858) の W01 node と [同:1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1012) の W09 node がともに落ちます。
- W06 で D を decision input に戻すと、[同:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:939) の W06 node に加え、[同:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:841) の report node も落ちます。
- W05 で frozen を存在確認へ戻すと、W05 node に加えて frozen C0/C1 を含む full-comparison node も落ちます。
- W03/W04/W07/W08 は executable mutant が無いため、「ちょうど 1 node」を確認した実績がゼロです。W09 は正例であり、そもそも適用する mutant が定義されていません。

放置時: wave 自身の欠陥検出力を一対一と誤認し、比較規則や guard が壊れても decision を承認できます。

## 裁定 §2 の未実装項目

- §2.2: trust anchor の「承認済み prereg への凍結」が未実装です。
- §2.3: 全組み合わせの実 baseline と、実際に観測した既存 gate 拒否への帰属が未実装です。
- §2.4: experiment module を含む変更閉包と、欠測時に decision を出さない規則が未実装です。
- §2.10: 独立した承認済み prereg からの再導出ではなく、registry から自己生成しています。
- §2.11: R/D の exact old/new bytes と対象 file 内一意出現の機械確認が未実装です。

C1 の 2 process、digest-only frozen predicate、C1/R の 6 件限定、C0/D/POS の分母外化、固定 3-key tie-break、production file の恒久無変更は静的には実装されています。

## nit

- [p3_b4_producer_auth_experiment.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_producer_auth_experiment.py:894) は scratch 例外文字列を report reason にそのまま入れるため、ABORTED report には絶対 path が混入し得ます。  
  放置時: 比較値・受理集合・decision は変わりませんが、report bytes の再現性だけが失われます。