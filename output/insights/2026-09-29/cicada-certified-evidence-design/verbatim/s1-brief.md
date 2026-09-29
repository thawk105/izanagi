# 段 1 brief — md_24: Cicada の certified 証拠面の設計と推奨 (設計のみ・実装なし)

wave `dev-wave-cicada-certified-evidence-design`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-evidence-design` (HEAD = local main `8fe87f852`)。台帳 item = worklog「次の一手」[T-2874] の (2)。

**研究前進:** VHash 論文の「forwarding + GC 接続を入れた Cicada 実装は serializable を保つ」を書けるかの分岐を、ユーザーが裁定できる形 (2 案・費用・書ける文の差・推奨) にする。完了 = 一次資料 `output/insights/2026-09-29/cicada-certified-evidence-design/README.md` + spool fragment (推奨とユーザー判断点)。一般論証 (D2292) は小モデル仕様 v1 が対象で、実装の条件 W* と GC 接続 G4〜G7 の安全性を主張しない。実装の正しさは実走検査だけが担い、今は indeterminate が上限 (D2279 項 4)。

**確定済みの裁定:** D2279 (Cicada は X/P/I の対象外、名前だけ足すのは却下)、D2287 / D2295 (forwarding は read 相だけ、GC 保護は tx 開始時の読み取り下限を途中で上げない)、D2292、D38 / D41 (X / P の意味)、D2232 項 4 (別 CC で existence を認定に使うときの 2 点)、D1464。

**親の実測 (攻撃対象):**
- certified = 巡回 0 ∧ integrity 数値 0 ∧ commit witness 一致 ∧ X・P の emitter が compiled source の literal `#if TRACE` 内に「在る」(文面検査、発火は証明しない) — `orchestrator/verifier/model.py:77-82, 507-522, 568-571`。I は連言外 (現 pin に emitter 無し)。`_PROOF_SURFACE_PROTOCOLS = {silo, si, mocc}` (`model.py:37`)。
- campaign は protocol に依らず trace/perf 両 build を作り `certified` 以外を reject (`orchestrator/campaign/pipeline.py:2117-2118, 732-743`)。cicada は `genome.py` の SPACES に在るが、証拠面の対象外・`source_digest.py` の ALLOWLIST 外 (silo / mocc だけ)・pin に trace hook 無し (out-of-tree patch)。
- 既存計装 `patches/instr-cicada-trace.patch` は読んだ時点の wts を保存し、commit 時の食い違いを stderr の数だけで出す (判定に入らない)。
- 実物で「既読版の回収・再利用」が起きた: D2295 の仮裁定 P5 で 3,938 件中 159 件 (`output/insights/2026-09-29/vhash-gc-connection-prototype/README.md` §3.3)。その検査は待機区間だけで、待機後〜commit・同じ wts の再利用を見ない (同 §7)。
- 費用の基準 (stock、thread 4、1 秒): cell K 175,139 txn で trace 78.8 MB・判定 4.67 s、cell R 917,498 txn で 196 MB・13.1 s (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/runs/j1-c/`)。

**親の provisional 裁定 (攻撃対象):**
- (P1) 観測した run の certified に要るのは「trace が実行を忠実に写す」ことの証拠だけ。版順は物理の鎖順でなくてよい (多版履歴は、ある版順で直列化グラフが非巡回なら 1SR — BHG の MVSG 定理)。よって書き込みの設置順 (O) は certified の必須でなく診断。
- (P2) Cicada 固有の忠実性の脅威と証拠面: B = 読み束縛 (読んだ版 object が tx 終了までに回収・再利用されていない。TRACE 専用の世代番号を読んだ時点で控え、tx の最後に照合)、U = 公開封印 (status が pending から 1 回だけ committed になり、その版の wts = C 行の版)、P = write set の partial_sort の置換保存 (Silo の P をそのまま移す)、I = 任意 (Silo でも連言外)。X (lock 被覆) は Cicada に対応物が無く、「公開後の版が不変」が相当する。
- (P3) 各 read の可視区間・rts 更新と検証の順序・read-only の snapshot 境界は、観測 run の certified には不要で、帰属 (規律 3) の診断。ただし read-only の rts を C 行に残せば「wts 順で直列化される」追加の検査 (ts 順適合) が安く書ける。
- (P4) Silo の「文面に在る」より強く、各 run で「照合した回数 = R 行数」を自己申告させ判定器が突き合わせる (恒真な保証を避ける)。
- (P5) 範囲は YCSB の point read / update。TPC-C の certified は item (4) (不在の読み・scan・並行 delete) と D2232 項 4 の 2 点の確認が先。`REUSE_VERSION=0` (delete で解放) は B を世代番号で照合できないので対象外にするか TRACE 専用の隔離が要る。
- (P6) campaign 側の trace 供給は要点だけ設計し、実装案に含めない (DW-G04: 今それを使う campaign の登録が無い)。
- (P7) 推奨の仮置き: 「実装する (最小版 = B・U・P + 判定器の protocol 別の門、YCSB 限定)」。VHash の新規性の芯 U0 (回収境界の前進) の典型的な失敗 (早すぎる回収) が、今の検査器の盲点そのものだから。

**不変条件:** 新規の計測・実装なし。patches/・external/ccbench・orchestrator/verifier/ は読むだけ。書くのは一次資料と fragment だけ。追加記録はすべて `#if TRACE` 内で、TRACE=0 の命令列を変えない設計にする。正しさの門を緩める提案をしない。

**分割:** 段 2 codex (read-only) が独立に設計案を file:line で起草 → 段 3 で 2 レンズ (実装する側 = 設計の穴・正しさの十分性 / しない側 = 過剰・費用・論文の主張で足りるか) → 段 4 親裁定 → 親が一次資料を書く → 段 6 独立 read-only review 1 本 → 記録 → land。
