---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-parallel-dispatch
seq: 1
title: 計算ノード job の並行投入規範を新設した — 親の初稿はユーザー指摘で撤回、敵対 2 本が blocker 4 件 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-parallel-dispatch)
---

## 本文

- **依頼はユーザーの直接指示**: 「Pegasus での開発・実験で、並行して計算ノードへ投げられるものは
  並行で投げた方が良い。計算ノードのスペックはどれも一緒だから。規約が甘くて愚直なことを
  やりかねない場合はメモしておいてほしい」。規範を {{D:compute-job-fanout}} として正本化し、
  runbook へ §7.5 を新設した。**実装面 0 byte。**

- **規約の穴は実在した。** runbook の「並列」の記述はすべて job の内側 (OpenMP / MPI /
  pytest の worker 数 / build の `-j`) についてで、**job どうしを同時に走らせてよいかの規範が
  1 行も無かった。**過去の並列化 survey (worklog (191)) も依頼文自体が「コア数を使い切る
  並列化」で、job 間 fan-out を探索軸に含めていない。

- **親の初稿はユーザー指摘で撤回した (wave 中の中断)。** 初稿は §7.5 の判定 1 の根拠に
  「ノード間 1.8 倍」を置いていたが、ユーザーから「stock silo とかを別の計算ノードへ投げて
  性能がめっちゃズレますとか絶対に経験ないやろ」と指摘された。**指摘は正しい。**
  1.8 倍は pytest 全走 wall-clock の値 (bnode002 116.25 / bnode009 200.72 / bnode010 214.34 秒) で、
  プロセス生成とファイル I/O が支配する作業である。**CC ベンチをノードを変えて測った実測は
  本 repo に存在しない** (登録 calibration も bnode011 単独)。未測定量を根拠に計測面の fan-out を
  既定禁止へ倒していた。判定手順を廃止し、直列にする理由を具体的な機序だけに限定した。

- **敵対レビュー 2 本 (read-only codex、並行投入) はいずれも NO-GO。**
  レンズ A (`sol`、危険な許可を攻める) = blocker 2 / must-fix 5、
  レンズ B (`luna`、守れない規則と取りこぼしを攻める) = blocker 2 / must-fix 5 / nit 1。
  **レンズ A の 1 件目が親の残した誤りを正した** — 「`hostname` を記録すれば後から効果を
  分離できる」は偽である。**処置と node が一対一に対応する配置は、差がどれだけ小さくても
  処置差と node 差を推定上分離できない。**これは実測主張ではなく識別可能性からの演繹であり、
  ユーザー指摘 (差は未測定) と両立する。job 内で比較が閉じる fan-out は無条件で許し、
  job 間で性能値を比較する fan-out は protocol が node を block / randomization 因子として
  定義した場合だけ許す形へ直した。

- **レンズが見つけた事実誤りを 3 件直した。** (i) D130 の 9161.6 秒は「順番待ちだけ」の
  分離実測ではなく**削減量の上限側の目安**である。(ii) 受入全走の隣の `output/` 偽赤の正本は
  **F136** であり、F57 (subprocess wall-clock flake) は full 単独でも再発していて根本原因が
  未確定である。両者を混ぜて F57 に背負わせていた。(iii) 共有状態の禁止を「create-only の
  同名 path」に絞っていたが、campaign lock・WAL・build claim・`output/` の親を走査する
  consumer が抜ける。read / write 集合全体での判定へ広げた。

- **取りこぼしを 1 件回収した。** 8c trial は `p3_autonomous_workload_trial.py` の
  `for workload in selected:` で **workload 単位に逐次**である。**依頼の例そのもの**だが、
  現行は journal・provider・build context・wall 予算を共有するのでそのままは割れない。
  候補として §7.5 と {{T:s8c-workload-fanout}} へ記録した。履歴監査・pytest・build は
  job 内で並列化済みなので候補から除外した。

- **refute した所見が 3 件。** (i) レンズ B の「probe が `pgrep` でシステム全体を見るので
  並行 job 自体が結論を変える」— `pgrep` は自ノードしか見えず、gen_S は 1 request が node の
  CPU 48 を使い切るので自分の request どうしは同居しない。**fan-out はむしろ同居より安全**で
  ある旨を §7.5 へ書いた。(ii) レンズ B の「受入全走の隣の禁止を `output/` を触る job へ狭めよ」—
  採らない。全走 1 回の空費は高く、広く守る側のコストは低い。
  (iii) **レンズ A の blocker 2 (変異 fan-out は D130 の 4 条件と D131 の共通前提 6 件が
  閉じるまで禁止) を撤回した。**

- **親が子の所見を鵜呑みにして誤った禁止を書き、ユーザーの問い (「rulings で裁定可能か」) を
  きっかけに自分で撤回した。** レンズ A の blocker 2 をそのまま採用して §7.5 と決定本文へ
  「fan-out は現時点では禁止」と書いたが、**D130 / D131 の条件群は「harness 自体を計算ノードの
  1 ジョブへ束ねる」経路への条件**であり、fan-out には掛からない。現行
  `--runner-mode dispatch` は harness がログインノードに居て各変異の pytest だけを投げる形
  (§7.4 の呼出しがそれ) なので、fan-out でも harness はログインに並ぶ。lock は
  `_lock_path_for` が `sha256(str(repo))` を鍵にする node-local `/tmp` のファイルで
  (`tools/mutation_harness.py:1814-1816`)、作業木が別なら鍵も別である。
  **効果が最大の項目に誤った恒久禁止を置きかけた** — 子の所見も一次資料で裏取りする
  (F1 と同型)。正しい状態は「未実装・要設計」であり、残件は spec 分割・ledger 併合・
  期待 node の分割整合・同時 dispatch 負荷・`mutation_worktree.py` の container 固定名による
  `--scratch-root` 分離の 5 点で、いずれも未実測である。

- **セッション事象:** この撤回の前に受入全走を 1 度投入したが、lease 待ち行列 (先行 7 枚) の
  段階で `holder_self: false` を確認して producer を落とした (待ち手は rc=70 で fail-closed)。
  **lease は未取得**なので他 wave へ影響していない。訂正後の tip で投げ直した。

- **副産物: runbook の誤記を 1 件訂正した。** §8 が「build / bench の計測は
  `_site_admits_measurement` が Pegasus を拒否したままであり ([T-277])」と書いていたが**逆**で、
  引用先の commit `6a51426c` がその拒否を**開いた** commit である。現行実装は
  `{OTHER, PEGASUS_COMPUTE}` を受理し、`test_site_admission_matrix` が exact 固定している。
  **計算ノードでの計測は site gate では止まっていない。**

- **実測 (この wave で取得)。** `qstat -Qf gen_S` = logical host `CPU Number` Min=Max=Std=48、
  `Submit Number Limit` と `Submit User Number Limit` は UNLIMITED (group 200)、
  `(Per-Req) Elapse Time Limit` 86400 秒、JSV 149。`qstat -Q` / `pegasusinfo` (11:40 頃) =
  gen_S TOT 135 / RUN 28 / HLD 107、Run Node 33 / 149。`rbudgetcheck` = SFC 残 5084.76 / 6000。

- **検査:** `python3 tools/check_docs.py` rc=0 (runbook §7.0 の dispatch inventory 検査を含む)、
  `python3 tools/spool_fold.py --dry-run` rc=0 (`planned`)。
  **変異 matrix は免除** — 実装差分ゼロで kill を観測する面が無い ({{D:compute-job-fanout}} は
  docs 規範であり機械 gate を 1 つも新設していない)。
  **受入全走は免除しない。**`docs/pegasus-runbook.md` を実 repo から読むテストが実在するため
  (`grep -rln pegasus-runbook orchestrator/tests/` = `test_check_docs.py`,
  `test_check_ai_provenance.py`, `test_calibrator_certify.py`, `test_schema_v2.py` の 4 file)、
  受入 lease を取って計算ノードで全走した。**結果値は本エントリに含まれない** —
  land は wave HEAD と tested tip の厳密一致を要求するので、走行後に値を足すと拒否される。
  値は wave の報告と handoff が持つ。

- **エージェント工数:** codex 子 2 本 (段 3 相当の敵対レンズ、`consult` sol / luna、
  reasoning=high、いずれも rc=0)。段 2 プランと段 5 実装子は docs-only のため不使用。

## 次の一手差分

### 新規

- {{T:mutation-fanout}} **P1・新規**: 変異本走の N-job fan-out を「第 3 の選択肢」として
  設計・実装する。D130 / D131 は「逐次 dispatch」と「1 job へ束ねて job 内直列」の 2 択しか
  比べておらず、**N 本同時投入は選択肢に入っていない**。束ねは順番待ちしか消さないが
  fan-out は内側も縮む。**D130 / D131 の未充足前提は着手条件ではない** — あれらは harness を
  計算ノードへ束ねる経路への条件で、harness がログインに並ぶ fan-out には掛からない
  (lock は作業木 path 由来の node-local 鍵)。**残件は設計 5 点** = spec の分割と期待 node の
  分割整合 / N 本の ledger 併合と `registered == recorded` の担保 / request・attempt・ledger 行の
  対応付け / 同時 dispatch 負荷とログイン admission / `mutation_worktree.py` の container 固定名
  (`.izanagi-mutation-worktree`) による `--scratch-root` の N 分離。いずれも未実測。
  **実装面のため Codex author 必須。**

- {{T:s8c-workload-fanout}} **P2・新規**: 8c trial の workload 単位 fan-out を評価する。
  `p3_autonomous_workload_trial.py` の `for workload in selected:` は逐次で、campaign root は
  分離できる構造だが `journal`・`active_providers`・`build_context`・`max_wall_s` を共有する。
  分けるには run root・provider / journal・receipt・wall 予算の分離と、部分成功・再投入の
  定義が要る。

- {{T:node-variance-protocol}} **P3・新規**: ノード間性能差を測る protocol を決める。
  現状は CC ベンチのノード間比較が存在せず、「同じだから並べてよい」も「違うから並べるな」も
  根拠が無い。同一 binary・同一 workload を N ノードへ同時投入すれば 1 回分の時間で分散が出る。
  **既存 protocol の通常運用ではなく新しい測定 protocol**として、目的・N・割付け・推定量・
  成果物へ流入させないことを事前固定してから実施する。
