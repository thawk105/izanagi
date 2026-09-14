---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2497-role-sink-status
seq: 2
---

## {{D:role-sink-status-gate-boundary}}. role sink 非干渉 node の status 検査が守る範囲は登録した変異集合までとし、生存する弱化は塞がずに測って記録する

**決定:** `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
`test_role_sink_bytes_vary_only_at_declared_declassifications` へ足した
report status 検査について、次の 2 つの弱化が両 node を緑のまま通すことを実測値として記録し、
**これを塞ぐための追加の検査・gate・framework は置かない。**

- helper の述語を `report["cells"][0]["stop_reason"] not in {"supervisor-error", "role-invalid"}`
  へ書き換える形。負例の partial 2 形はどちらもこの述語で拒否されるため、
  **status を一度も読まない helper が両 node を緑にできる。**
- `run_wire` 内の helper 呼出しを `cell = report["cells"][0]` へ 1 行置換する形。
  helper 本体は残るので負例は通り、本 node は status を検査しなくなる。

**保証すると書いてよいのは次の 3 点だけである。**

1. helper は実 `run_trial` が返す partial report を拒否する (負例が partial の 2 形で実測)。
2. helper の述語本体を除去・弱化・受理拡大する 3 変異はいずれも負例が KILLED する。
3. 呼出し行を単に削除する変異は本 node が `NameError` で KILLED する。

**理由:**

- 本 wave が直した欠陥は「恒真な保証 — 謳うだけで発火しない検査」の型である。
  保証範囲を実際より広く書けば、同じ型の欠陥を記述の側で作り直すことになる。
- D387 が既に定めているとおり、gate と検査を同じ主体が変更できる限り、repo 内の挙動検査は
  意図的な弱体化への完全な防壁ではない。上記 2 形はその射程内であり、本 wave が作った欠陥ではない。
- 有限個の負例をいくつ足しても、それらを全部満たす別述語への書き換えは常に残る。
  負例を足し続ける設計は終わらない。**主張を測定へ置き換えるほうが安く、正直である。**
- 生存を「静的にそう見える」で済ませず、変異として登録して SURVIVED を実測した。
  注入 diff の sha256 は変異ごとに相異なり anchor は各 1 件だったので、注入は実在する。

**却下した選択肢:**

- 負例へ第 3・第 4 の partial 形を足して上記述語を殺す — 同じ regress が次の述語で再発する。
  依頼が明示的に scope 外とした「仮想リスク向けの検査追加」にも当たる。
- helper を production 側へ移して test から改変できなくする — production 変更は D1847 が禁じており、
  受理集合を変える大きな設計変更を nit の対策として持ち込むことになる。
- 生存を記録せず「負例で守られている」とだけ書く — 本 wave が直した欠陥そのものである。

## {{D:status-projection-is-the-inner-layer}}. report status の一貫性は production 側の completeness gate が既に担っており、test 側の status 検査は独立した第 2 層として位置づける

**決定:** role sink 非干渉 node へ足した status 検査は、**production 側の既存層を置き換えるものではなく、
利用点で完了性を明示する第 2 層である**と位置づける。「この検査が無ければ通っていた走がある」
という主張は、`orchestrator/campaign/autonomous_trial_completeness.py` の各 gate を通過する
本物の partial report を示せた場合にだけ書く。

実測した内側の層は次の 3 つである。いずれも `p3_autonomous_workload_trial.py:3902` から
`run_trial` の末尾で無条件に呼ばれる `assert_autonomous_trial_completeness()` の中にある。

- `_check_status_projection` (同 file 2886) — producer と同じ述語 (cells 数 /
  `fatal_error is None` / stop_reason / admission) を独立に再計算し、`report["status"]` と
  一致しなければ `[terminal-projection] report status must be 'complete'` で落とす。
  **`status` リテラルだけを反転する変異はここで死ぬ。**
- 同 file 2405 — journal に対応する terminal event を持たない `fatal_error` を拒否する。
  **report へ `fatal_error` を直接注入する変異はここで死ぬ。**
- `[workload-coverage]` — 欠けた workload が無いのに wall-budget terminal event があると拒否する。
  **wall budget 経路を強制する変異はここで死ぬ。**

**理由:**

- 変異で受理集合の縮小を示そうとして 3 回続けて内側の層に殺された。これは偶然ではなく、
  report の完了性について production 側に厚い層が既にあるという実測である。
  この事実を書かずに「穴を塞いだ」とだけ書くと、成果を過大に伝える。
- 4 度目の再照準 (`_run_pending_critics` 末尾への `raise` 注入) で、cell が完成し 4 role の
  payload も WAL も揃った後に `supervisor-error` が立つ経路を作り、内側 gate をすべて通過した
  本物の partial report を得た。このとき本 node は追加した検査で赤になり、
  呼出し接続を外すと緑になる。**縮小は実在するが、それを示すには内側の層を全部通す必要があった。**
- 単一理由性 (F820) の確認は、赤の**本文**を読まないと成立しない。rc と node 名だけでは
  内側の層に殺された変異を「自分の gate が効いた」と誤読する。

**却下した選択肢:**

- 内側の層があるから test 側の検査は不要とする — 内側の層が守るのは status と事実の**一貫性**で
  あって、trial が完了したことではない。本物の partial は現に返る。
- 差分が出るまで再照準を繰り返さず「差分は示せなかった」で閉じる — 3 回目までの結論であり、
  4 回目で実際に示せた。示せる証拠を探さずに限界を主張するのは怠慢である。
