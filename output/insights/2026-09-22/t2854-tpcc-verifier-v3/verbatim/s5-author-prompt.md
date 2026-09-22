単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (R1〜R11 と変異の事前登録。plan と食い違う箇所はこちらが正): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md
- 段 2 plan (file:line の実装計画。段 4 裁定で上書きされた部分を除いて従う): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s2-plan.md
- 親 brief (不変条件 1〜9、段 4 R10 の訂正付きで読む): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md
- 段 3 相談 (参考。採否は段 4 裁定の表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s3-consult-A.md、同 dir の s3-consult-B.md
- 依頼文と並走 wave の返信の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/verbatim/request-t2854.md
- 設計: output/insights/2026-09-21/tpcc-trace-certification-design/README.md の §3.1〜§3.3、§6.1 (この worktree 内の相対 path)

## あなたの役割と権限

あなたは Codex `role=author` の実装子である。作業 tree はこの worktree (cwd) で、編集してよいのは次の 5 file だけ:
`orchestrator/verifier/model.py`、`orchestrator/verifier/parse.py`、`orchestrator/verifier/dsg.py`、`orchestrator/verifier/core.py`、
`orchestrator/tests/test_verifier.py`。docs・insight・他の file は編集しない。commit・push・branch 操作はしない (親が行う)。
`orchestrator/verifier/report.py` は読むだけで編集禁止 (凍結証拠が bytes を束縛)。新しい module・test file・fixture directory は作らない。

## 実装すること

TPC-C 用の trace 形式 v3 (C 行 10 token、R/W/X/I 行に表番号) を verifier が読み、object 経路と compact 経路 (packed / tuple) の両方で
object を (table, key_hex) として扱い、cycle の anomaly に表と取引種別を載せる。段 4 裁定 R1〜R9 をすべて満たすこと。要点:

- R1: v3 の run は certified にしない (`Integrity.v3_existence_unverified`、`clean()` への組込み、core の notes 1 行)。cycle は従来どおり
  non-serializable で構造化して返す。v2 は不変。
- R2: schema 混在は、同一 file 内は `_parse_file` がその C 行で ParseError、file 跨ぎは既存の failure 先行処理の後に 1 つの helper で
  sorted path 順に照合 (compact と legacy が同じ helper を呼ぶ)。merge での再検査はしない。
- R3・R4: 新しい整数 field (table、tx_type、nS、nQ) は `0|[1-9][0-9]*` の正規形だけ受理、table 0..10、tx_type 1..5、nS = nQ = 0、
  v3 の W op は U / I / D。v2 の既存変換・検査は変えない。
- R5〜R7: plan §1・§3〜§5 の identity・派生型・`core.result_to_dict_v3`・X/I tuple と notes。
- R8: 試験 (test_verifier.py に追加、既存の `_tmp_trace` 形の合成 fixture)。R8 の (a)〜(e) をすべて含める。
- R9: production 4 file の差分は追加 + 削除で 550 行以内、test_verifier.py は 800 行以内。超えるなら理由を報告。

## 現行の受理・拒否挙動 (変更前、あなたが変えてよい範囲の明示)

- 変更前: C が 5 token は「trace v1 C record is not supported」で ParseError、7 token 以外は「expected exactly 7 fields」で ParseError。
  つまり v3 (10 token) は全部 ParseError。v2 の R/W/X/I/E/P/A の受理・integrity 判定は test_verifier.py の既存試験が固定している。
- 変更後に広げてよい受理は「段 4 R2〜R4 を満たす v3」だけ。v2 の受理・拒否集合、verdict、integrity 値、notes 文言、result_to_dict の
  bytes、witness の選択順は 1 byte も変えない。既存 message 文言 (「expected exactly 7 fields」を含む) を保つ。

## 検査と報告の義務 (DW-S05-C)

- 既存テストの期待値を変えない。反転・緩和・skip・xfail・削除をしない。赤なら実装側を直す。期待値が誤りだと考えるなら実装を変えず
  報告して止まる。
- テストを甘くして緑にしない (fixture への現行 hash の差し込み等をしない)。機構の正例・負例は実体を通す (依存先を stub しない)。
  legacy 経路との比較でパーサを差し替える場合は、検査対象の機構の外側の既存 seam だけを差し替え、必ず復元する (既存例
  test_verifier.py の `_capacity_tuple_result` 付近と同じ流儀)。
- 期待値へ揮発 payload (tmp path、pid、tree hash 等) を焼き込まない。
- 自分で実走した範囲を報告に書く: `python3 -m pytest -q orchestrator/tests/test_verifier.py -p no:cacheprovider` の結果 (passed / failed
  件数と失敗 nodeid)、および `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` (素の自走 runner) の結果。実走できなければ
  「実装済み・未実走」と書き、緑と書かない。
- test_verifier.py 末尾の `_run()` は `test_` で始まる module 関数を**引数なしで**呼ぶ自走 runner である。新しい試験は pytest の
  fixture 引数 (tmp_path・monkeypatch 等)・`pytest.mark.parametrize`・pytest 専用 API に依存させず、既存試験と同じく引数なしの関数に
  する (一時 dir は `_tmp_trace`、差し替えは try/finally で復元)。これ以外に関数を列挙・登録する meta test が要るかも自分で確かめる。
- 報告に次を静的に列挙する: 所有外の caller (orchestrator/ と tools/ の import・呼出し)、共有 fixture、consumer test への波及
  (特に orchestrator/tests/test_campaign.py の EdgeReason / Anomaly 生成、test_reflux_result_evidence.py、critic/digest.py)。
- 変異の事前登録 (段 4 裁定の M1〜M15) の各変異について、実装後の位置 (file:line と置換前後の 1 行) と、それを殺すはずの試験の
  nodeid を表で返す。同じ入力を別層が先に拒否して赤の理由が 1 つにならない変異があれば、その理由を書く。

## 出力形式

Markdown。「変更の要約 (file ごとの差分行数)」「段 4 裁定 R1〜R9 の充足 (項目ごとに file:line)」「追加した試験の一覧」「自走結果」
「波及の静的列挙」「変異の位置表 (M1〜M15)」「未解決・懸念」、最後に `## 総括` (5〜10 行)。
