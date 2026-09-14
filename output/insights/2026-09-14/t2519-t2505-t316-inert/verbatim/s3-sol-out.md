## 親の分析への攻撃

**(A)(B) は有力な原因候補だが、今回の原因を「特定した」という断定は成立しない。** [親分析](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/analysis-1-configure-failed.md:88)の結論を、検証待ちの仮説へ戻すべきである。

以下、G＝[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py)、P＝[t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py)とする。

- **事実1・2は入力の構造を示す。今回発生した stderr は示さない。** option 不在・変数供給から、今回の subprocess が成功し、未使用警告で落ちたところまでを導けない。
- **事実3・4は別 job の先例である。** 類似原因の優先順位を上げるが、今回の原因を識別しない。また事実4の引用にある3件は `BACKOFF_FIXED` と provenance 変数2件であり、(B) の3件とは異なる。`RULE_LAUNCH_COMPILE` の警告発生を裏付けていない。
- **事実5は対照実験になっていない。** driver、source、compiler、configure 引数等が異なる緑の記録から、今回の赤を(A)(B)に分解し、それぞれ単独で原因だったとは判定できない。

**requested／stock の帰属も未確定。** G:1889で requested、G:1894で stock を順番に configure する。requested が失敗すれば stock は未実行である。「両側に同じ引数を渡す」と「両側で警告が発生した」は別の主張になる。

同じ `configure-failed` になる未排除経路は、次のとおり。

| 経路 | 現物 |
|---|---|
| CMake の解決・実行権限確認の失敗 | G:1626、1876 |
| configure 前の CMake 読取り・identity 確認の失敗 | G:1498、1712 |
| subprocess 起動失敗 | G:1604 |
| CMake 非ゼロ終了 | G:1610 |
| 成功したが、未使用変数以外も含む stderr が非空 | G:1617 |
| 両 configure 後の CMake 再解決失敗 | G:1977 |

依存 build 済みという事実は一部の候補を弱めるが、CCBench 側の依存探索成功や、その後の実行ファイル状態まで保証しない。

**引用・説明にも修正点がある。**

- 親分析:31の `configure` は、現物では **P:1850から1865**。ASTで数えるとリスト要素28件、先頭5件を除く引数23件であり、「22引数」と一致しない。
- 親分析:113の「receipt は reason code しか保持せず（D1849）」は不正確。P:334の summary は digest・status・comparison も保持する。今回失われたのは、P:1967で例外となりP:1922の summary 生成へ戻らないためである。D1849は診断情報全般の保存禁止ではない。
- 再読時の親分析:19では関数名が `_configure_compile_commands` に修正され、現物と一致していた。旧記載の `_run_configure` を現行の誤りとしては扱わない。

## 偽の緑への滑り

**段2のCLI診断案そのものを、ゲート迂回とは認定できない。** G:4198で同じ supply evaluator、G:4205で family admission を呼び、G:4213は admission に従って終了する。

ただしCLIには、P:374の **t316固有の新旧2契約の組・driver・meaning状態の検証**がない。したがってCLIのrc=0をt316実経路の緑へ読み替えることはできない。[段2計画:57–60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s2-plan-out.md:57)は、この読み替えを明示的に禁じているため、現案への攻撃は不成立である。

**拒否時に既存 `detail` をjob stderrへ出す案も、記述どおりならD1849／D1625に反しない。**

- receiptへevidence mappingを追加しない。
- P:1967の拒否と例外を維持する。
- P:374のexactな組の検証を変更しない。

ただし、それだけでは赤のreceiptにsupply entryが残るようにはならず、briefの完了条件を満たす修正ではない。また、[brief:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md:53)の「probeのbytesを変えない」とは衝突する。採用するなら段4でその局所変更を明示し、新commitで別走として束縛する必要がある。

親分析が退けた「要求defineを関門から落とす」「関門だけpatch木にする」は、A-2の警告と整合する。これらを次走の便宜的修正へ復活させてはならない。

## 規律 3 と scope の境界

**今回発生した赤の直接証拠を取得する行為は、本題の実測・原因切り分けに属する。** 仮想リスク向けの新しいgate・検査・台帳・一般化ではない。既存 `evidence.detail` を採取することは、失敗理由を根拠付きで返す要求に沿う。

ただし、後続CLI走で得たstderrは**後続走の直接証拠**であり、失われたjob `996644` のstderr逐語にはならない。「同条件で仮説を再現した」と「初回の原因を直接観測した」を区別すべきである。

また、原因取得からpatch設計・受理規則変更までを自動的に正当化することはできない。[段2計画:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s2-plan-out.md:58)の「必要な環境修正等」は、判明した具体的原因に照らしてscopeを判断する必要がある。

## 完了判定の判定

| 対象 | 一次資料から導ける条件と今回の判定 |
|---|---|
| **T-2505** | 台帳は「t316 driver 自身が `stock-inert-preprocess-root-location-only` の緑に到達する環境」を、commit束縛した計算ノードprobeで実測することを要求する。今回のconfigure赤では**未完**。旧契約の緑やCLIの緑でも不足する。 |
| **T-2519** | 台帳・D1936項17は「既存機構でinert要求がstock同等の緑へ到達する**か**」の先行実測を求める。緑限定とも、原因究明・configure修復・比較到達を必須とも書いていない。今回の赤は、指定条件での未到達という有効な回答になる。 |
| **D1856の解除** | 「13 macroの実行時意味witness」と「patch stack適用木のinert緑の計算ノード実測」の両方が必要。今回では解除できない。 |
| **brief独自の完了条件** | receiptのsupply entry・reason・comparisonの記録を要求している。P:1967の例外でsummary生成へ戻らず、P:2568でblocked observationになるため、**未達**。 |

根拠は[台帳本文](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md:12)、[D1936項17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1936-item17.md:18)、[D1856](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1856.md:3)。

**T-2519について段2の「未完」は保守的な提案であり、逐語から必然する判定ではない。** 原因究明や比較到達を完了の必須条件へ追加するなら厳しすぎる。一方、親の「既存機構＝t316」とする一意の読み替えにも根拠がない。段4では、今回の限定された赤をT-2519の先行実測として充足扱いにするかを、対象範囲とともに裁定すべきである。

## 成立しなかった攻撃

- rc=0でもstderr非空なら赤になるという説明は、G:1617と一致していた。
- 段2のCLI診断案、stderr局所出力案について、D1625の受理集合を緩める証拠はなかった。
- 親分析はA-2の「検査した木とbuildする木を一致させる」条件を維持しており、偽の緑を直接勧めてはいない。
- 実測記録は、恒久的な未到達か今回固有かを未確定としている。段2も26.3秒／32秒を次走時間の保証としておらず、全ノード・将来commitへの一般化は認められなかった。

ただし親分析:90–93の「必ず」「両側でも警告が出る」、同:109の無限定な「到達しない」は、観測範囲を越える。**今回の1 allocation・bnode040・束縛commitでは未到達**へ限定すべきである。brief:14の「唯一の計算ノードdriver」も、親分析自身の事実5が別driverの計算ノード緑を挙げており、無限定の表現として整合しない。

指定資料の読取りと静的検査のみを行った。変更・commit・ジョブ操作・テスト実走は行っていない。

## 総括

原因「特定」を撤回して(A)(B)を仮説とし、後続診断の証拠を初回jobへ遡及させない。  
T-2505は未完。T-2519は赤を含む先行実測の充足範囲を裁定し、D1856解除・brief完了とは分ける。  
直接証拠の取得はscope内とし、CLI緑の代用は禁止。stderr局所変更を採る場合はbytes不変条件の変更を明示する。