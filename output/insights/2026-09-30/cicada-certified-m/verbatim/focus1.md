## 所見ごとの判定

判定は静的検査に基づきます。適用、build、実走は行っていません。

| 所見 | 判定 | 根拠 file:line | 残る問題 |
|---|---|---|---|
| S1 | partial | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:303)、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:409) | stock では offset を拒否し、E-max では hunk 別に記録する実装。U1 報告の stock offset 0、E-max 18 hunk の適用結果は、この段では独立に再実測していない。 |
| A1 | closed | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:120)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:433) | `API_EXTRA_REGISTER` は外部 read と対応しない read set 要素に限られ、登録漏れを二重に数えない。同じ key の反復については後述。 |
| A2/B1 | closed | [壊し B](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-early-reclaim.patch:8)、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:373) | FIRED に両計数があり、`rts_raised=1` の EVENT 件数とも比較する。発火の実走は未確認。 |
| A3/B3 | partial | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:109)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:363)、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:276) | 5 本の等式は追加されたが、B と API の等式はなお照合漏れに対して独立でない。 |
| A4 | closed | [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:30)、[壊し U](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-drop-published-write.patch:17) | 改訂裁定どおり期待 kind は `U_MISSING_W` だけ。設置対公開の発火は、この壊しの証拠に含められない。 |
| B2 | regressed | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:293)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:325) | 指定された命令順には直ったが、新たに偽の緑を許す窓ができた。詳細は F1。 |
| B4 | closed | [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:358) | CUSTOM は `custom-diagnostic` に固定され、`pass` を返さない。 |
| B5 | closed | [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:434)、[同](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:731)、[同](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:754) | 対照は genome・stack・target・cell flags・thread・patch SHA-256 列・実行 argv の一致を要求する。除外された `group_commit` 等は起動器が固定し、別条件の対照を借りる経路は見つからなかった。IDENT 省略も SMOKE の合格と patch bytes を照合する。 |

### F1 世代加算直後の snapshot が進行中の事象を見逃す

**重大度: must-fix。** [事象側](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:293) は世代を一度加算してから owner を消す。[読み手](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:325) は世代が等しければ登録し、[終了時](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:113) もその世代だけを比較する。

失敗例: 事象が世代を加算した直後に停止する。読み手は新世代と旧 owner・旧 status を取得して `g1 == g2` で登録する。その後、事象が owner と版状態を変えても世代は増えないため、終了照合も通り得る。**影響:** 「登録から終了まで回収・再利用されていない」という B の主張に偽の緑が生じる。**推奨対処:** 進行中を識別できる世代プロトコルにし、登録時と終了時の双方でその状態を拒否する。

### F2 母集団の二つの等式が照合実行を証明しない

**重大度: must-fix。** B の `tx_end_reads_nonempty` と `b_end_checked_*` は、各終端 site で同じ `read_set_.empty()` を挟んで連続計数する（例: [writePhase](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:549)）。API の `api_checked` は照合地点ではなく `read()` のスコープ終了時のデストラクタで増える（[M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:363)）。起動器はこれらを [等式](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:284) に使う。

失敗例: 成功した read の照合経路を欠落させても、`api_checked` は増え、等式は通る。forwarding の `ERROR_PREEMPTIVE_ABORT` や早期 return でも同じ計数になる。終了前に read set が消えれば、B の両辺がともに 0 になり得る。commit と begin の等式、`tx_reconnoiter=0` は別途有効だが、この漏れは検出しない。**影響:** 「照合済み＝母集団」の証拠としては不足する。**推奨対処:** API は実際の呼び出し別照合の完了点で、B の対象は照合側と独立した保存記録から数える。

同じ key を 2 回読む通常経路は [再読分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:380) に入り、外部 read は追加されない。外部 read の多重集合照合（[M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:120)）による反復 key の偽違反・見逃しは、指定された point read 範囲では見つからなかった。ただし呼び出し単位の帰属を実走で確認した結果ではない。

### F3 E-max の offset 記録だけでは hunk の意味上の位置を保証しない

**重大度: should。** [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:421) は E-max で offset を記録し fuzz を拒否する。U1 報告の 18 hunk はすべて `transaction.cc` で、offset は +660〜+940 行。文脈が別の同形箇所にも一致すれば、適用成功と offset の記録だけでは意図した関数内の位置を証明できない。

失敗例: TRACE 専用 hunk が別の一致箇所に当たり、TRACE=0 のバイナリ同一性は保たれる一方、TRACE=1 の照合 site がずれる。件数等式はそのずれを必ず検出する設計ではない。**影響:** E-max の合格結果を意図した計装位置の証拠にできない。**推奨対処:** 計算ノードで適用後の 18 hunk を関数・前後文脈に照合し、TRACE=1 の件数と TRACE=0 同一性を併記する。

## 総括

**NO-GO。** B の snapshot に偽の緑を許す窓があり、母集団の B・API 等式も照合完了を証明しない。
A1、A2/B1、A4、B4、B5 の静的修正は確認した。S1 の適用結果と各発火は実走未確認。
F1・F2 を修正し、E-max の適用位置を確認してから計算ノードの結果で再判定する。