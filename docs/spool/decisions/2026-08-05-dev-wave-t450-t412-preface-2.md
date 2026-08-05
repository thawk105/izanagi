---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t450-t412-preface
seq: 2
---

## {{D:acceptance-deletion-gate-fail-closed}}. [T-412] 前置 — 受入形の未 stage 削除検査を trigger 非依存の fail-closed にし、[T-450] の `DW-O15` 削除を同じ変更単位で入れる

**決定 (1): deletion preflight を受入形で trigger 非依存の fail-closed にする。** D97 決定 1(b) が
定めた「bypass は `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS=1` のみ、`final` trigger では不可」を
supersede する。`tools/run_tests.py` から同 env の定数と全 bypass 分岐を削除し、git 検査が
成立しない場合 (実行不能 / rc≠0 / decode 失敗) も受入形では rc=13 とする。
`tools/pegasus/dispatch_compute.py` の tests task env allowlist からも同 key を外し、
親 dispatcher が生成する request に載らないようにする。`_is_acceptance_run` は変更しない —
targeted run を gate の外に置く正本であり、これを広げると開発の常用経路が止まる。

**決定 (2): 受理集合の変化を両方向で記録する (D96 の手続義務)。** deletion preflight は
**縮小のみ**で、受理から拒否へ移るのは 2 系統 (受入形 × 未 stage 削除 × legacy env=`1` × 非 final、
および受入形 × git 検査失敗 × 非 final) だけである。一方 `tools/check_docs.py` の
`_OPERATION_NUMBERS` から 15 を外す変更は**非単調**である — `DW-O15` を持つ文書集合を新たに拒否し、
持たない集合を新たに受理する。「縮小のみ」は deletion preflight 単体の性質であって、
本変更単位全体の性質ではない。境界テストは同じ変更単位で追随させた。

**決定 (3): 「残余義務の完全機械化」は達成していないと明記し、`DW-O11` 第 2 文を残す。**
段 3 の敵対レンズ 2 本が独立に示したとおり、(a) `PYTEST_ADDOPTS` が非空だと `_is_acceptance_run`
は偽になるのに pytest は既定 target 全体を走るため、受入形の判定を外れたまま全走できる、
(b) 受入結果と landed tip を結ぶ receipt が存在せず、land helper 自身が tested SHA を受入証明と
みなさないと明記している、(c) 意図しない削除を**復元**しても緑になるため「stage が緑への唯一経路」
も偽である。したがって剪定で回収できる bytes は **0** であり、`DW-O11` は削除せず、
「git 検査不能」と「復旧・stage・復元」を含む形へ**是正**した (223 bytes、削除前と同値以下)。

**決定 (4): task-run 台帳の bypass 使用 field は不要として閉じる。** D97 の「既知の残余」が挙げた
3 limb のうち、bypass 使用 field は本決定で reader ごと bypass が消えるため、実装しても
全 run で false にしかならない恒真な監査 field になる。残る 2 limb (隔離 checkout への
modules cache 複製、rc 13/14 の診断粒度) は従来どおり据え置く。

**却下した案:** (a) `exploratory-full` mode を新設して stage 前の全走を残す — API 設計であり、
`DW-G04` の発火 path を本 wave で書けない。`git add -A` は commit ではなく `git reset` で戻せるため、
探索用途は stage 後でも同一 tree を測れる。(b) bypass を存置したまま「機械化した」と記録する —
escape hatch を残した機械化は規律 2 が名指しする reward hack の形である。(c) 受入 receipt と
land 結線まで本変更単位へ含める — 受理集合を大きく変える設計であり、段 2 / 3 の攻撃を経ていない。
(d) 計算ノード側 `_job_run` が request の `environment` を allowlist で再検査する — 別機構
(機械をまたぐデータの信頼境界) であり、未知 key を拒否するか黙って落とすかの択一が未検討で、
稼働中 job を落としうる。(a) 以外はいずれも裁定パッケージへ送る。

**研究状態への影響:** certified 選択・レポート・proof chain の値は変わらない。変わるのは、
受入形の全走が「未 stage 削除を含む木」や「git 検査が成立しない環境」で緑を返せなくなることと、
dev-wave 文書予算が正味 55 bytes 空くことである。
