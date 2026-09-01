## 総括

D1195 の実装残差はある。現行 BFS は存在するが、解析不能 edge の黙殺と、閉包を切り詰めても生存する負例のため、「逆到達閉包から生成経路不在を導いた」という成果物上の主張まで正しさゲートが届いていない。

## 所見

### 1. 「不在を導く」と「実行時に遮断する」は無条件には同じでない

- **主張:** D1195/D1171 が求めるのは構造的な経路削除ではなく、導出済み閉包を実行時に遮断して、その走の限定範囲で生成がなかったと導く方式である。この限定解釈なら両者は接続できるが、前提として遮断目録が宣言した閉包と一致していなければならない。
- **根拠 path:line:** `verbatim/D1195.md:3-4`、`verbatim/D1171.md:3-7`。逆辺 BFS は `orchestrator/campaign/p3_b4_wiring_probe.py:1099-1120`、code 登録と call 前例外は `同:557-610`、走後の ledger 照合は `同:2019-2033`。
- **残差か否か:** この動的解釈自体は残差ではない。ただし、下記 2・4 のため現行成果物はその前提を証明できておらず、段2の「限定範囲内の生成経路不在を導く」`s2-plan.md:13-14` は早い。
- **直し方:** 該当なし。前提となる閉包導出の残差を下記の範囲で直す。

### 2. 未解決 call が閉包の外へ黙って落ちる

- **主張:** 解析対象 module 内に実際には seed へ到達する動的 caller があっても、callee edge を解決できないとその caller は `reasons` に入らず、その caller に記録された解析 issue も検査されない。したがって「解析集合内で seed に到達する関数は閉包に含まれる」という証拠文言は現状では成立しない。
- **根拠 path:line:** visitor は動的 import、非 literal `getattr`、未解決 local callable を issue にする一方、解決できた callee だけを edge にする `orchestrator/campaign/p3_b4_wiring_probe.py:789-823`。`_build_inventory` は先に `reasons` を導出し、その `reasons` に入った symbol だけの issue を検査する `同:1140-1150`。既存検査も、すでに閉包内の `pipeline.evaluate` へ人工 issue を付けるだけである `orchestrator/tests/test_p3_b4_wiring_probe.py:338-350`。
- **残差か否か:** **D1195 の実装残差。** D1171 が除外するとしたのは module 外または3権威点へ到達しない生成器である `verbatim/D1171.md:6-7`。解析 module 内で実際には seed へ到達する未解決 caller は、その明示済み除外に含まれない。
- **直し方:** `_build_inventory` で `reasons` に入った関数だけを検査する順序をやめ、宣言した解析 graph に影響する未解決 binding を閉包導出前に fail-closed にする。既存の unresolved-issue 負例は「現在の `reasons` 外にある動的 caller」を対象に修正する。

### 3. 候補集合は固定 root の静的 import 閉包であり、runtime import 閉包ではない

- **主張:** 候補集合は `_RUNTIME_IMPORT_ROOTS` と6 module の宣言から始まり、campaign source catalog 上の module-level import を推移的に追って決まる。関数内 import は探索から明示的に除かれる。これは D1171 が認めた固定 module 集合であり、集合自体は残差ではない。
- **根拠 path:line:** root は `orchestrator/campaign/p3_b4_wiring_probe.py:58-83`、catalog は `同:952-962`、関数本体を探索しない visitor は `同:965-999`、queue による集合構築は `同:1003-1022`。外部 module と非到達 producer の非被覆は `同:7-11,2113-2116` および `verbatim/prereg-10.md:24-25`。
- **残差か否か:** 候補集合の限定そのものは**残差ではない**。完全性を主張しない D1195 の許容範囲である。
- **直し方:** 該当なし。

### 4. 「exact runtime import closure」の検査は自分で作った集合との一致で恒真

- **主張:** `test_static_preflight_covers_exact_runtime_import_closure` は runtime の実 import census を測っていない。`runtime.modules` は渡された `preflight` の各要素を import して作った mapping なので、`set(runtime.modules) == set(static)` は構成上必ず成立する。D1171 の「自分で定義した集合との一致にすぎず恒真」が検査名と中心 assertion に再発している。
- **根拠 path:line:** `runtime.modules` の構築は `orchestrator/campaign/p3_b4_wiring_probe.py:1180-1188`。その同値を exact runtime closure と称して検査するのは `orchestrator/tests/test_p3_b4_wiring_probe.py:152-164`。D1171 の却下理由は `verbatim/D1171.md:12-13`。
- **残差か否か:** **D1195 の検査・成果物文言の残差。** 公開 JSON の「exact analyzed set」という限定は正しいが、この検査を runtime closure の裏付けには数えられない。
- **直し方:** 既存検査の名称と主張を「preflight mapping と import 対象の一致」まで狭め、D1195 の閉包充足根拠から runtime closure という評価を外す。

### 5. seed 除去負例と producer 直接呼出し負例は閉包全体を拘束しない

- **主張:** seed 除去3件は各 seed の全閉包を検査せず、第一 seed では `pipeline.evaluate` 一点、残る2 seed では seed 自身だけを見る。producer 直接呼出し9件は inventory→profile hook の発火を検査するが、第一権威点 `require_certified_writer_authorization` 自身を含まない。したがって閉包導出層と profile/隔離層は独立には検査されていない。
- **根拠 path:line:** seed 除去は `orchestrator/tests/test_p3_b4_wiring_probe.py:287-320`。期待 producer 部分集合は `同:323-335`、直接発火9件は `同:353-408`、main 経由負例は `同:411-439`。第一権威点の test 内検索は `同:292` の除去操作1一致行だけで、直接発火対象には現れない。schema も inventory と generation seeds の対応を検査せず、manifest 検査へ進む `orchestrator/campaign/p3_b4_wiring_probe.py:1861-1892`。positive baseline は seed 数が3であることしか確認しない `orchestrator/tests/test_p3_b4_wiring_probe.py:1071`。
- **具体的な生存変異:** `_build_inventory` の `for symbol in sorted(reasons)` `orchestrator/campaign/p3_b4_wiring_probe.py:1143` で、`symbol == _GENERATION_SEEDS[0]` だけを `continue` する。閉包の反射性が壊れ、第一権威点の直接 call が遮断目録から消える。それでも `pipeline.evaluate` の seed 除去差分は維持され、直接発火9件にも第一 seed はなく、inventory hash は切り詰めた値から自己計算される `同:2036,2118-2121`。静的には既存焦点検査を生存する。
- **残差か否か:** **D1195 の検査残差。**
- **直し方:** 新規 gate は作らず、既存の seed 除去・inventory 負例を、全 seed の反射性と、解析 graph の各 `callee∈closure ⇒ caller∈closure` を直接拘束する形へ修正する。既存 producer 発火表にも3権威点自身を含める。

### 6. 「閉包が閉じた」と読める別語彙の hit がある

- **主張:** literal な “complete closure” はないが、別語彙では過大に読める箇所が残る。
- **根拠 path:line:**
  - `orchestrator/campaign/p3_b4_wiring_probe.py:2109-2112` は「解析集合内で seed に到達する関数は reverse closure に含まれる」と無条件に書く。所見2の未解決 caller はこの文言に反する。
  - `orchestrator/tests/test_p3_b4_wiring_probe.py:152` は “covers exact runtime import closure” と称するが、所見4のとおり自己一致である。
  - `verbatim/prereg-10.md:7-10` は「outcome を生成しないことを…機構で保証する」と書く。`同:24-25` の完全性限定は全称主張を避けているが、閉包導出そのものの検査穴までは救わない。
  - `s2-plan.md:13-14` は inventory 非発火から限定範囲内の「生成経路不在」を成立済みとする。
- **残差か否か:** **D1195 の成果物残差。** 非完全性の注記は存在するが、宣言範囲内の閉包成立を過大に述べている。
- **直し方:** 所見2・5の既存機構と負例を直した後に現行文言を維持するか、それまでは “statically resolved edges represented in this inventory” 相当に範囲を狭める。runtime closure を称する検査名は修正する。

### 7. 規律2への影響

- **主張:** この wave を「残差なし」で閉じると、コードを直接弱めなくても、第一権威点を inventory から落とす回帰を検出できない状態を D1195 充足済みとして固定する経路が生まれる。これは「遮断・負例・検査を弱めない」という親の規律2に反する。
- **根拠 path:line:** 規律2は `brief.md:30-34`。生存変異の根拠は所見5の `p3_b4_wiring_probe.py:1143`、`test_p3_b4_wiring_probe.py:287-320,353-365,1071`。
- **残差か否か:** **D1195 の残差。**
- **直し方:** 所見5の既存負例を閉包の反射性・推移的逆辺閉包まで拘束してから決着する。

## 親裁定への評価

- **(P1-1) 反証。** 3 seed、逆辺 BFS、profile 遮断という部品は存在する `p3_b4_wiring_probe.py:84-88,1099-1160,557-610`。しかし未解決 caller が無検査で閉包外へ落ちる `同:789-823,1140-1150` うえ、第一 seed を inventory から落とす変異を既存負例が検出しない。D1195 が要求する意味まで「機構が着地」とは言えない。
- **(P1-2) 同意。** 非完全性は module docstring `p3_b4_wiring_probe.py:7-11`、JSON 除外文言 `同:2113-2116,2140-2142`、事前登録 `verbatim/prereg-10.md:17-25` に明記される。ただし宣言範囲内の過大表現は所見6の残差。
- **(P1-3) 反証。** 所見2・4・5・6が D1195 の実装／検査／成果物残差である。
- **(P1-4) 未確認。** 射影された実装・検査では `_reason_paths` 系統以外を確認できなかったが、識別子検索は異名の別導出法を排除せず、repo 全体も今回の射影外である。この限界は `s2-plan.md:32` の判断に同意する。実装・検査内の `_GENERATION_SEEDS` は7一致行・8出現。

## 全件検索の記録

対象は指定された8ファイルすべて。いずれも打ち切りなし。pytest は実行していない。

- `rg -n '_GENERATION_SEEDS' <implementation,test>`  
  **7一致行、8出現**。
- `rg -n 'require_certified_writer_authorization|_GENERATION_SEEDS\[0\]' <test>`  
  **1一致行** (`test_p3_b4_wiring_probe.py:292`)。第一権威点の直接発火検査はない。
- `rg -n 'reverse closure|_reason_paths|reason_path|reverse\.setdefault|逆到達閉包' <implementation,test>`  
  **6一致行**。
- `rg -n -i '保証|guarantee|assur|runtime.import.closure|exact.runtime|all.four.checks|zero.interdiction|生成しない|生成も.*ない|生成.*0|不在' <8射影ファイル>`  
  **25一致行**。所見6の substantive hit を含む。
- `rg -n -i 'not covered|not claimed|outside (the )?(exact )?analy|reaching none|完全性は主張しない|完全目録ではない|覆わない|閉包の外に経路が残りうる|全称で主張' <8射影ファイル>`  
  **17一致行**。
- `rg -n -i '_RUNTIME_IMPORT_ROOTS|_MODULE_RELATIVE_PATHS|_campaign_source_catalog|_static_import_dependencies|_load_static_modules|analyzed_modules|exact analyzed|module set|module 集合|候補集合|固定 module' <8射影ファイル>`  
  **46一致行**。
- `rg -n -i 'negative|負例|seed|producer|inventory|reason_path|interdict|遮断|KILLED|SURVIVED|MISMATCH' <8射影ファイル>`  
  **172一致行**。
- `rg -n -i 'dynamic import|non-literal getattr|unresolved local assignment|sys\.modules callable|issues' <implementation,test>`  
  **28一致行**。