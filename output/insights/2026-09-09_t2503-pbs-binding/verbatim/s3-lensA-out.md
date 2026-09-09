## 1. 束縛が意味するもの

- 所見: 修正後に証明できるのは「Python preflight が読み直した runtime path の bytes が、その時点の worktree `.pbs` と一致した」までであり、「実際に解釈・実行された job body 全体が committed body と同一」は証明できない。job body 自身が `$0` を hash し、その body が設定した環境変数を Python が信頼する自己証明だからである。また比較用 hash と receipt 用 hash は別々に読み直されるため、途中変更があれば比較を通った digest と記録 digest が異なり得る。
- real か refuted か: **real**。
- 根拠 file:line: [job body:65-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:65) が `$0` を自己照合し、[job body:104-110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:104) がその path を Python へ渡す。[probe.py:2336-2343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2336) は比較後に runtime spool を再度 hash する。
- 提案: T-2503 の主張を「Python preflight 時点の runtime-spool/worktree `.pbs` 一致」に狭める。「実行された body の同一性」まで必要なら外部 launcher または scheduler 側の不変な証拠が必要で、これは **scope 外の裁定候補**。

## 2. Python 側照合が追加で守るもの

- 所見: Python 側照合が「何も追加しない」という攻撃は成立しない。shell の hash 後に spool または worktree が持続的に変化した場合と、`.pbs` を経由せず `_execution_binding` が直接呼ばれた場合を追加で拒否する。ただし前項の実行済み命令列までは証明しない。
- real か refuted か: **refuted**。
- 根拠 file:line: shell の最終照合は [job body:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:80)、Python の再読込はそれより後の [probe.py:2336-2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2336)。`main` も `_execution_binding` を直接呼ぶ [probe.py:2644-2659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2644)。
- 提案: 削除せず、「shell 後の再照合と standalone preflight の fail-closed」を守る検査と位置づける。

## 3. [恒真ゲート]

- 所見: 正常かつ不変な実行では、shell が `runtime == committed` と `worktree == committed` を確認済みなので、修正後の Python 比較は条件付きで冗長になる。ただし shell と Python の間に状態変更が可能なため、「現実に起こりうる全入力で必ず真」という恒真性はない。
- real か refuted か: **refuted** — 普遍的な恒真ゲートではない。ただし安定した通常経路では独立情報を追加しない。
- 根拠 file:line: [job body:68-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:68) の二つの等値確認と、後続プロセスで再度 open/hash する [probe.py:2336-2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2336) の間には時間差がある。
- 提案: 「独立な provenance 証明」ではなく「後段での再確認」と明記する。

## 4. 負例の検出力

- 所見: plan を文字どおり実装すれば、比較対象を `.py` に戻す変異は確実に区別される。(a) `.py == .pbs` は独立 bytes と明示 assert で排除、(b) HEAD・dirty・nodefile の先行失敗は例外文言が異なるため完全一致 regex を通らない、(c) `_execution_binding` を直接呼び、目的文言は現在比較行にしか存在しない。比較行を削除しても `pytest.raises` が満たされない。
- real か refuted か: **refuted**。
- 根拠 file:line: 独立 bytes は [plan:37-46](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:37)、直接呼出しと完全一致は [plan:64-78](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:64)。先行関門の固有文言は [probe.py:2305-2335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2305)、目的文言は [probe.py:2338-2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2338)。
- 提案: helper の独立 literal、bytes 不一致 assert、直接呼出し、完全一致文言を実装時に落とさない。静的評価であり、pytest の成否は未実測。

## 5. 正例の実体性

- 所見: monkeypatch による迂回はない。plan が差し替えるのは `probe.socket.gethostname` だけで、正例は本物の `_execution_binding` を直接呼ぶ。ただし正例の二つの hash assert は比較行固有の副作用を観測しない。比較行を削除しても同じ dict は生成可能であり、当該行を固定する oracle は負例側である。
- real か refuted か: 迂回の疑いは **refuted**。正例単独が比較行を実証するという主張は **real な過大主張**。
- 根拠 file:line: hostname patch は [plan:48-58](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:48)、正例 assert は [plan:82-98](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:82)。比較後の dict 生成は [probe.py:2340-2351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2340)。
- 提案: 正例は「一致入力で関数全体が返すこと」、比較行の存在と対象は負例が担保する、と説明を狭める。追加テストは不要。

## 6. [テスト代表性]

- 所見: login node 上の単体テストは計算ノードの PBS 統合挙動を代表しない。hostname は合成値、PBS 環境は手設定、nodefile は単一の通常ファイル、spool は repo 外の tmp file であり、scheduler spool の所有権・可変性・`$0` の意味・symlinkやmountを含む `realpath` 挙動を通らない。job body の shell 関門も実行しない。
- real か refuted か: **real**。
- 根拠 file:line: 合成環境は [plan:48-58](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:48)。実環境では [job body:29-45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:29) が複数 path と hostname/nodefile を解決し、[job body:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:65) が `$0` を spool とみなす。
- 提案: 本 wave の受入を「Python 回帰と対象変異の検出」に限定する。計算ノード実挙動の確認は既定どおり再実測まで未解消とし、この wave へ新たな投入を追加しない。

## 7. site fixture と fixture 順序

- 所見: plan は `site_policy.socket` と `probe.socket` を取り違えていない。test module は fixture setup 前に probe を importし、function-scope autouse は `site_policy` module 属性だけを差し替える。提案テストは test body で `probe.socket.gethostname` を明示 patch するため、その後に勝つ。提案には module-scope fixture 自体がなく、module-scope が function-scope autouse より先行する規則による迂回もない。
- real か refuted か: **refuted**。
- 根拠 file:line: probe の module-scope import は [test:19-25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:19)。fixture の scope と対象は [conftest:239-255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:239)。plan もこの差を明記する [plan:121-126](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:121)。
- 提案: `probe.socket.gethostname` の明示 patch を helper 内に維持する。

## 8. 規律 2 / 3

- 所見: plan に正しさゲートの緩和はない。tuple の値と順序、5 path の dirty 検査、`runtime_sha256` key、例外型・文言を維持し、例外の握り潰しも追加しない。
- real か refuted か: **refuted**。
- 根拠 file:line: 変更境界は [plan:15-24](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:15)、不変条件は [brief:37-44](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md:37)。現行 key 生成は [probe.py:2340-2349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2340)。
- 提案: plan どおり定数化と対象訂正だけに留める。

## 9. 親 brief の P1 と P2

- 所見: P1 の履歴説明は一次資料と一致する。`5e12db6ce` では tuple index 1 が `.pbs`、`0218acc61` では `condition_meaning_gate.py` の先頭追加により index 1 が `.py` になり、比較行は残った。P2 も対象変異に対する静的設計として成立するが、まだ plan であり実装・実走済み事実ではない。
- real か refuted か: **refuted**。
- 根拠 file:line: 現在のずれは [probe.py:2290-2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2290)。履歴一次資料は `5e12db6ce:tools/...probe.py:2018-2066` と `0218acc61:tools/...probe.py:2210-2259`。未実走の明記は [plan:133-137](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:133)。
- 提案: P2 を「予定された mutation oracle」と呼び、実装・正規 runner 実測後まで「検出済み」とは書かない。

## 10. [捏造/幻覚] brief の実測値と pin 不在

- 所見: 現行 `.py` の SHA-256 `d7607e0a...ce802` と blob `32644847...2ef0` 自体は再計算と一致した。しかし「repo 内 hit 0」「FROZEN_MANIFEST に t316 なし」と、2 receipt の内容は射影資料に一次資料がなく再検証不能である。plan が brief の記述をそのまま再引用しており、独立裏取りにはなっていない。また「次の計算ノード走行で必ず当該文言になる」は shell/Python の多数の先行拒否経路を無視した過大一般化である。
- real か refuted か: **real** — 主張が偽と確定したのではなく、一次資料不在と断定過剰が real。
- 根拠 file:line: pin と receipt の断定は [brief:20-24](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md:20)、[brief:42-44](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md:42)。plan は [plan:110-119](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md:110) で再引用するのみ。先行拒否は [job body:8-63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:8) と [probe.py:2305-2335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2305)。
- 提案: 親で保持している repo-wide search と receipt 読取結果を一次証拠として再提示する。「必ず赤」は「先行関門を通過した現在 bytes の経路では当該比較で拒否」に狭める。

## 11. 受入台帳と job body 照合

- 所見: 「未知 node は実行拒否せず順序用の unknown cost として扱う」と「job body が committed `.pbs` と spool を既に照合する」は一次資料で確認できる。
- real か refuted か: **refuted**。
- 根拠 file:line: duration 不在は `None` になる [conftest:1571-1591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:1571)。未知 unit は既定 cost で並べられる [conftest:1631-1664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:1631)。spool/commit 照合は [job body:65-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:65)。
- 提案: この二点は修正理由として使用可能。ただし job body 照合の意味は第1項の狭い境界に留める。

## 12. [ドリフト] shell と Python の bound path 集合

- 所見: 既存の別の実ドリフトとして、Python は `condition_meaning_gate.py` を bound path に含めるが、job body の `BOUND_PATHS` は含めない。さらに probe は `_execution_binding` より前の module import 時にそのファイルを読み込む。そのため dirty な condition gate は Python の dirty 拒否より前に import-time code を実行し得る。
- real か refuted か: **real、scope 外**。
- 根拠 file:line: import は [probe.py:33-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:33)、Python の5件集合は [probe.py:2290-2296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2290)、その検査は後段の [probe.py:2330-2335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2330)。shell の4件集合は [job body:54-59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54)。
- 提案: T-2503 へ混ぜず、実在する pre-import 束縛差として親の裁定候補へ返す。

## 総括

対象を `.pbs` の名前付き定数へ直す案と、提案された負例には、対象変異を逃す blocking flaw は見つからない。real 所見は、束縛の意味を「実行された job body の同一性」まで広げられないこと、正例単独では比較行を固定しないこと、login node test が PBS 統合を代表しないこと、pin・receipt の一次証拠が射影されていないこと、そして scope 外の既存 bound-path ドリフトである。

pytest は実走しておらず、テスト結果の成否は報告していない。