## 攻撃 (成立/不成立を明記)

1. **成立：最終行の禁止は受入にも及ぶ。**  
   [依頼原文の最終行](/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt:53)は「計算ノードは使わない。」であり、実験・性能測定だけに限定する語はない。依頼は実装・生死確認・land 前の条件まで扱っている。そこから受入だけを除外する根拠は見つからない。「land に必要だから許される」という解釈は、必要条件から資源使用の許可を作り出してしまう。

2. **成立：login から起動しても、計算ノード使用である。**  
   `run_tests.py` は shard 分割を `acceptance_shards.run_parallel` に渡し、各 shard は `dispatch_compute.dispatch` を呼ぶ。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/tools/run_tests.py:2332)上、login の collection と計算ノードの試験実行は別である。README の「明示 shard 3、login で走る経路」は、禁止に抵触しない根拠にはならず、訂正が必要。

3. **成立：「少額なので確認不要」は今回の禁止を解除しない。**  
   [D2219 項1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/decisions.md:71255)は、受入・焦点走・変異も同じ計算資源として数えると明示する。通常の「2 node 時間未満なら確認不要」は、個別依頼に使用禁止がない場合の運用である。今回の明示禁止を AI が狭めれば、ユーザーが残した資源配分の決定権を侵す。実行済みの node 時間は、後から解釈を訂正しても戻らない。

4. **成立：受入必須と使用禁止の衝突は、正式停止の理由になる。**  
   [DW-S04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/core.md:97)の受入要件は残る。本 wave は実装変更と `docs/dev-wave/**` の変更を含み、[D2316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/decisions.md:74477)の縮小受入例外にも該当しない。したがって、受入を省いて land することもできない。[DW-STOP](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/core.md:35)は「裁定/権限待ち」「許可範囲で復旧不能」を正式停止として認めている。

5. **成立：受入全走を通せば残件が全部閉じる、とは言えない。**  
   [README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/output/insights/2026-09-30/codex-astra-ultra/README.md:49)では変異 matrix が未実施で、焦点走は guard をすり抜けた参考値とされている。DW-S04 の変異免除は実装差分ゼロの wave に限る。現資料では、受入全走が緑でも変異の未了は別に残る。

6. **不成立：3 shard が巨額の浪費や研究 job の具体的な妨害になる、という攻撃。**  
   今回の所要・競合状況の実測はない。D2219 の受入約0.25 node時間は過去の単価であり、今回の確定値ではない。A を拒否する根拠は明示禁止への抵触で十分で、被害額を誇張する必要はない。

## (B) の実害

- **切り替えの反映は遅れる。** [D2229 決定4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/decisions.md:71735)と今回の依頼に従えば、local main への着地後に作られる wave から新しい権威を使う。B では、その反映と委任検出の改修配布が保留になる。ユーザーの実装依頼は未完了として残る。
- **「他への影響は全部 land 待ち」は不成立。** README によれば、repo 外の `next_tasks_consult.sh` は既に改訂・疎通済みである。B でもこの変更は残り、repo 側との切り替え時点が分かれる。ただし、そこから具体的な動作破綻が起きる証拠はない。
- **再開時の手戻りはありうる。** main の前進に伴う取り込み・再検証と、未実施の受入・変異が残る。遅延の費用はゼロではない。
- **既存成果を失う根拠はない。** 実装差分、生死確認、受領証、委任・guard の観測は保持できる。land の延期自体は既存の測定値を書き換えず、観測の価値も消さない。今回の即時切り替えが研究結果の成立や期限を左右するという証拠も、確認資料にはない。

## 総括

**現指示のまま案 (A) は通せない。案 (B) として land を保留し、成果と未検証事項を保持するのが妥当。** B の主な実害は反映の遅延と再開時の手戻りであり、既存成果の喪失ではない。

再開には、計算ノード使用についてユーザーが明示的に指示を変更するか、禁止と必要な検証要件をともに満たす経路の確認が要る。今回の静的確認では、その代替経路は確認できていない。