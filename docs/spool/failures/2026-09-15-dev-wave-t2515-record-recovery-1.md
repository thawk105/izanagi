---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-t2515-record-recovery
seq: 1
---

## 再発

### F500

- **再発: 2026-09-10 (条件関門・同日の別呼出し)** — 同じ `tools/pegasus/certify_calibration.sh` の
  **条件関門**が裸の `python3` で起動され、計算ノードの既定 interpreter (intelpython 3.9) で
  `orchestrator/verifier/parse.py` の 3.10 構文を import した時点で
  `TypeError: unsupported operand type(s) for |: 'type' and '_LiteralGenericAlias'` になった。
  request `988653.nqsv` (rr95) / `988654.nqsv` (rr5) の 2 本で同一 traceback、21 秒・`rc=1`。
  **本エントリの既載 2026-09-10 再発 (pristine source verifier) とは別の呼出し・別の観測**である。
  同 script は既に python3.10 の smoke 選定ブロックを持っていたが、それが**関門より後ろ**に
  置かれていたため効いていなかった。当時の対処は、選定ブロックを内容を変えずに関門より前へ移し、
  関門の argv 先頭を `"$CALIBRATE_PYTHON"` にすること (関門自体は弱めていない)。
  なお条件関門そのものは後続の D1936 項 6 が整合撤去したため、現行 main に当該呼出しは無い。
  **検知が遅れた理由**: 既存 unit test は job body の shell を静的に読むだけで、関門が実際に
  どの interpreter で起動されるかを見ていなかった。login node では `python3` が 3.10 に
  解決されるため、仮に実行しても再現しない — **計算ノードでしか出ない差**である。
  実測できた時点は 4 つで、`892707.nqsv` の成功 (2026-08-06、関門導入前)、
  3.10 専用式の投入 `3c9932591` (2026-08-20)、関門の全 driver 義務化 `0218acc61` (2026-09-01)、
  発現 (2026-09-10)。**「2026-08-06 以降ずっと故障していた」とは言えない**
  (本エントリ自身が別の認証投入と失敗を記録している)。
  一次資料: `output/insights/2026-09-10/t2515-rr95-rr5-calibration/README.md` の 2026-09-15 追記と
  同 dir の `job-evidence/988653-rr95-condition-gate.stderr`、`original-verbatim/`。

### F766

- **再発: 2026-09-10** — 受入全走が 2 巡とも赤になったとき、親は `docs/failures.md` を
  `t1259` と `TimeoutExpired` という**字面**で検索し「この事象の F は存在しない」と判定して
  wave を止め、ユーザー裁定へ返した。実際には F57 (全走の並列が外部 process 一般の
  wall-clock gate を押し出し git の timeout にも及ぶ) と F862 (real-repo inventory 未登録 node が
  worker へ散る誤分類型) が実在し、後者が本件の主因の記述だった。
  **本エントリの根本原因 (1)「台帳を主題ではなくファイル名で引いて正しい族を見落とす」の再発**である。
  根本原因 (2) の hold 登録循環はこの回では再現していない。
  独立レンズの相談 2 件が両方とも指摘して訂正された。
  再発検知は既存のとおり — `DW-O18` の「F 不在」を主張する前に、**事象の型**
  (並列度・wall-clock・外部 process・timeout) で台帳を引く。file 名と例外名だけの検索で
  不在を結論しない。
  一次資料: `output/insights/2026-09-10/t2515-rr95-rr5-calibration/original-verbatim/`。

### F355

- **再発: 2026-09-10** — `tools/dev_wave_wait.py producer` が、producer process が生存し
  対象 job も RUN 中の状態で rc=0 を返す事象を 1 wave で **3 回**観測した (焦点再レビュー・
  焦点走・変異本走)。いずれも
  `producer: /proc/<pid>/stat を読めないため pid-only へ縮退します` を出した直後で、
  2026-09-02 の観測と同じ縮退経路の署名である。**原因は切り分けていない。**
  `DW-C00` の「完了は `.done` 非空で決める」に従い 3 回とも未完了と判定して待ち手を張り直したので、
  誤って先へ進んだ回は無い。機構は変更していない。
  **本記録を回収した 2026-09-15 の wave でも、段 2 / 段 3 の待ち手 3 本すべてで同じ縮退
  メッセージが出た。** ただし 3 本とも `.done` が非空 (`0`) で成果物も実在し、実際には完了していた。
  縮退メッセージの出現と偽完了は独立に扱う。

### F320

- **再発: 2026-09-15** — 2026-08-20 の supersede が入れた恒久対応
  (`tools/dev_wave_submodule_init.py` と `DW-C01` の pointer) が**在るのに**再発した。
  新規 worktree で同 tool が `runtime-io-failure: {'label': 'submodule', 'kind': 'update-no-fetch'}`
  の rc=1 を返したが、親はこれを止まる理由と扱わず先へ進んだ。続けて `git submodule status` を
  **非再帰**で叩き、top-level 2 行に `-` が無いことだけを見て「pin 一致で clean」と判定した。
  入れ子の googletest は `-` 接頭辞のまま残り、受入が
  `stage=preflight-submodule-ready rc=2` で走行ゼロ・log 未生成のまま落ちた
  (lease claim 前の preflight なので lease 窓は失っていない)。
  他の稼働 worktree の `git submodule status --recursive` と照合して差を特定し、
  tool と同じ argv `git -c protocol.file.allow=always submodule update --init --recursive --no-fetch`
  を前景で叩いて rc=0、googletest が `f8d7d77c` で checkout されたことを確認して再投入した。
  **初回の rc=1 は、他 session の `git worktree add` が 10 本並行していた時間帯の一過性**で、
  同じ argv が後で成功している。
  **恒久対応の存在は、その rc を読まない運用を防がない。** 検証は必ず `--recursive` で行い、
  全行に `-` / `U` 接頭辞が無いことを確認する。非再帰の status を clean の根拠にしない。

## supersede 追記

- F934 **supersede: 2026-09-10** — 一次資料の「認定 attempt 12 件すべてに `condition-gate.jsonl` が無く、この関門は認定経路で一度も実走していない」は、request `988706.nqsv` (rr95) と `988708.nqsv` (rr5) が構造化記録を出したことで、確認できた範囲の初回実走として限定訂正する。両 job の判定は手動実走と同一 (`supply-effectuation: configure-failed` / `runtime-meaning: materialized-branch-invalid`) で診断を追認した。**拒否原因が解消したという意味ではなく、2026-09-14 の別 driver 再発もそのまま残る。** 証拠は `output/insights/2026-09-10/t2515-rr95-rr5-calibration/job-evidence/988706-rr95-condition-gate.jsonl` と `988708-rr5-condition-gate.jsonl`。
