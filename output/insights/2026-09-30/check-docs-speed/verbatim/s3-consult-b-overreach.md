1. **重大度: high｜根拠:** [profile 要約](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/profile-base-summary.txt)、[brief P3](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/brief.md)。O1〜O5 の「節約秒数」は実測値ではない。cProfile の累積時間には親子関数の重複があり、72 秒から約 30 秒という予測はまだ支持できない。**推奨:** 各案を順に入れ、同一計算ノードで未計測実行の wall と peak RSS を測る。採否は増分効果で決める。

2. **重大度: medium｜根拠:** [check_docs.py:1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1381)、[check_docs.py:2971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2971)、[check_docs.py:3121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3121)、[profile 要約](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/profile-base-summary.txt)。O1 は約 193 万回の先頭からの改行再計数、O2 は同じ entry 本文の ID 再解析を減らすため、優先度が高い。O5 も comment がない行なら同値の早道で、試す費用が小さい。**推奨:** O1・O2・O5 を先行する。O1 の索引は小さな上限付き cache とし、offset の境界を旧実装と照合する。

3. **重大度: medium｜根拠:** [check_docs.py:1953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1953)、[check_docs.py:2038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2038)、[check_docs.py:2338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2338)、[test_check_docs.py:11711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:11711)。O3 の約 5 秒は上限に近い見積り。raw slice と digest は全 parsed carry で作るが、照合に使うのは参照先 ID が一致しなかった後だけである。ただし既存 test は全 reference の digest を直接検査する。**推奨:** O3 を必須案から外し、先行案の再計測後に判断する。digest の遅延計算は有望な次案だが、既存 test の期待値と逐次性を保つ設計を先に確認する。

4. **重大度: medium｜根拠:** [check_docs.py:2536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2536)、[check_docs.py:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3190)。O4 の memo は約 135 万組の比較ループ自体を残し、見込む効果も最大で数秒程度。**推奨:** 初回実装から外す。将来索引化するなら、異常入力で出す全ペアの所見と順序を維持する必要があるため、隣接ペアだけの検査へ単純に置き換えない。

5. **重大度: medium｜根拠:** [brief P2](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/brief.md)、[check_docs.py:6650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:6650)、[T-1222 記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/output/insights/2026-08-17/t1222-growth-leak-fix/README.md)。main 全域の無制限解析 cache を避ける判断は妥当だが、**200〜400 MB は実測に基づく値として扱えない**。本文の読取 cache は既に存在し、追加索引の保持量を別に測る必要がある。**推奨:** O1 は数ファイル分の上限付き索引で始め、peak RSS を測る。安全確認のための `_safe_read_text` の毎回の判定は維持する。

6. **重大度: medium｜根拠:** [brief 成果物・E1〜E3](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/brief.md)、[依頼原文](/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_5.txt)。合成文字列だけの新旧等価性 test は成長比例にならず、既存 exact pin を変える必要もない。ただし旧実装の逐語複製を各関数分増やすと保守費用が大きい。E2 の「全 node を二重実行」は、依頼の「全 fixture」を確認する手段として過剰になり得る。**推奨:** 新設 test は O1・O2・O5 の境界と所見順序を守る最小限にする。E2 は checker を実際に呼ぶ全 fixture を漏れなく列挙して新旧比較し、通常の全 suite は既定 gate で走らせる。選定方法と対象 node を記録する。

7. **重大度: medium｜根拠:** [brief E1〜E3・分割](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/brief.md)、[common.txt §5](/work/1/SFC/tanab/tmp/speedup-2026-09-29/common.txt)。E1 の負例比較と E3 の交互計測は適切。ABAB 各 5 回、故障注入の新旧実行、E2、受入を合わせた「1 node 時間未満」には内訳がなく、現時点では確認できない。本体・test と repo 外 probe の二分割は所有面が分かれており妥当。**推奨:** 投入前に各実行の回数と未計測 wall の見積りを足し、E1 は代表的な失敗経路を維持する。E3 は結果のばらつきも示す。

8. **重大度: low｜根拠:** [profile 要約](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/profile-base-summary.txt)、[brief 実測](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/brief.md)。計算ノードで取り直した profile は login 側の stat 律速を訂正する根拠になる。一方、1 走の cProfile は約 1.8 億 function call に計測負荷を加え、細かな関数の順位や未計測 wall への換算を歪め得る。**推奨:** 律速の候補として使い、一般化と効果判定は同時刻の未計測 ABAB に限る。

## 総括

- **採用する最小集合:** O1・O2・O5。各増分の wall と peak RSS を確認する。
- **初回から落とす案:** O3・O4。再計測で残る取り分を見て再判断する。carry 95.9 万件の走査そのものと archive のペア比較の索引化は、所見順序を保つ設計が必要な「次の一手」とする。
- **検証計画:** E1 と E3 は維持する。E2 は全 fixture の被覆を明示したうえで対象を絞る。総 node 時間は実行回数と未計測 wall から再見積りする。今回は指定どおり静的検査のみで、テストと計測は実行していない。