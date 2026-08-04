静的レビューの結果、実装本体に consumer の受理集合変化、publish bypass、恒真ゲート化は見つかりませんでした。must-fix は実装ではなく、M1 の変異方法に 1 件あります。pytest・変異は実走していません。

### 挙動保存

- **refuted — consumer の非同値入力は見つからない。** 外側 `try` は canonical 呼び出しを含んだままで、`AttestationError` は従来どおり `False` になります。[execution_guard.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:158)、[execution_guard.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:174)、[execution_guard.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:177)

  - `TypeError` / `ValueError` / `StatisticsError`: 旧実装は外側で `False`、新実装は内側で `False`。
  - `AttestationError`: 内側を通過して外側で `False`。
  - それ以外: 旧実装・新実装とも伝播。
  - 内側で先に捕捉しても戻り値は同じです。

- **refuted — 型・変換条件の drift はない。** `isinstance(..., Mapping)`、`type(samples) is list`、非空、`type(tolerance) in (int, float)`、中央値と各 observed sample の `float()` 化は旧ハンクから逐語的に移っています。[execution_guard.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:185)

- **refuted — issuer との意図しない共通化はない。** issuer は独立した `_recorded_verdict` のままで、working diff に変更はありません。[env_attestation.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:564)

### Gate の到達性

- **refuted — `_certify_main` 内の publish bypass はない。** gate は品質理由算出後・唯一の `status` 算出前にあります。[cli.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:607)

- rejected は [cli.py:625](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:625) で return。
- `registered/` 作成と publish はその後の [cli.py:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:629)〜[cli.py:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:638)。
- gate 前後の例外は [cli.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:656) の rejection 経路に入り、publish へ復帰しません。
- `status` の再計算はありません。
- 非 certify 分岐は通常 calibration を書くだけで `registered/` publish を行いません。

### 恒真性

- **refuted — 自己比較全体は恒真ではない。** 同じ sample list を expected/observed に使っても、各要素を中央値と比較するため外れ値は落ちます。[execution_guard.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:194)

  実 artifact は 48 要素、中央値 `2101`、2% 帯は `[2058.98, 2143.02]`。index 40 の `3080.935` は中央値との差 `979.935` で帯外です。[calibration-753f535a8d024727.json:1443](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1443)、[同:1484](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484)、[同:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1493)

- **real — singleton は自明に通る限定領域。** `samples_mhz=[x]` なら中央値も `x` なので、任意の有効 tolerance で差はゼロです。schema は非空だけを要求し、最小件数を要求していません。[schema_v2.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:227)  
  ただし production probe は可視 CPU ごとに 1 標本を作るため、単一 CPU なら完全な自己観測です。[env_attestation.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:423) 現行成果物の受理集合を誤らせる具体経路はなく、must-fix にはしません。

- **real — 大 tolerance による実質的な恒真化余地は残るが既裁定 U-3。** CLI は `100` を許します。[cli.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:485) 正の標本では 100% 帯が `[0, 2×median]` となるため、通常形の分布はほぼ無条件に通せます。ただし `[100,100,300]` のように `2×median` を超える標本は落ちるので、数学的な恒真ではありません。tolerance の権威束縛は段 4 で再登録前 blocker U-3 として scope 外に裁定済みです。

- **refuted — object identity による bypass はない。** expected と observed が同一 mapping／同一 list でも、identity 比較ではなく中央値からの全要素偏差を評価します。上の実 artifact が反例です。

### 変異の kill 予測

| 変異 | 静的予測 |
|---|---|
| M1 | **意味的な no-op（`append` を `pass` にする、または `if` 全体を削除）なら kill。** 帯外 fixture が accepted・publish され、[test_calibrator_certify.py:500](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:500) の `rc != 0` が最初に落ちます。 |
| M2 | **kill。** median-only では外れ値 fixture が publish され同じ line 500 が落ちます。加えて `pegasus-shaped-one-outlier` が [test_execution_guard.py:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:478)、既知例外が消えて [test_env_contract.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:463) で落ちます。 |
| M4 | **kill。** M2 と同じ 3 箇所が落ちます。golden vector は最初の `want=False` で検出します。 |

M1 を指示どおり append 行だけ文字通り削除すると、[cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608) の `if` が空になり `IndentationError` です。これは test node による acceptance-set kill ではなく collection failure なので、変異証拠として数えてはいけません。

### 診断

- **real / nit。** rejection には reason code しか追加されず、中央値、帯、帯外 index/value/delta は構造化されません。[cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608)
- 一方、rejected `calibration.json` には元の `attestation_profile` と全 samples が残るため、情報自体は再計算可能です。[cli.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:450)  
  certified 選択の受理集合・参照・台帳値は変わらず、段 4 でも report 診断追加は nit と裁定済みなので、DW-G05 により must-fix にはしません。

## 総括

- **(a) must-fix**
  - 実装本体: なし。
  - 変異手順: **real / must-fix** — [cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608) の M1 は append 行の文字通り削除ではなく、構文を保つ no-op にすること。**成果物影響:** collection failure を kill と数えると、変異 matrix・試行台帳・材料レポートに「publish gate が acceptance-set 変化で検出された」という偽の証拠が残る。
- **既裁定の real residual**
  - [cli.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:485) — tolerance 権威未束縛。将来これを無視して再登録すれば runtime receipt の受理集合が広がるが、U-3 として再登録前 blocker 済み。
- **(b) nit**
  - [cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608) — 帯外 index/value/delta の構造化診断がない。
  - [schema_v2.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:227) — singleton は自明に self-pass するが、現行の自己整合性という受理条件には違反しない。
- **(c) refuted**
  - consumer の例外捕捉、Mapping/list 厳格性、float 失敗挙動が変わったという攻撃。
  - gate を飛ばして `_certify_main` の publish に到達できるという攻撃。
  - 自己比較または同一 object で述語が常時 true になるという攻撃。実 Pegasus artifact が実反例。
  - issuer が canonical 述語へ統合されたという攻撃。
- **(d) kill 予測**
  - M1: 有効な no-op 変異なら `test_cli_effective_clock_self_failure_is_quality_rejected_before_publish` が kill。文字通りの行削除は無効な構文 kill。
  - M2: CLI 負例、golden vector、registry exact-exception の 3 テストが kill。
  - M4: 同じ 3 テストが kill。
  - 以上はすべて静的予測であり、テスト・変異の実走結果ではありません。