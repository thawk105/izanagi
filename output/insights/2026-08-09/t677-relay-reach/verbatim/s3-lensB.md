通常完走の failed/error report 集約と、`pytest_unconfigure` が pytest summary 後に呼ばれる点は確認できた。以下は、プランを受理する前に閉じるべき穴である。pytest 実走は行っていない。

## 1 — nit : `pytest_terminal_summary` の押出し境界は 157 件ではなく 156 件目

(i) 主張

プランの実測値を使うと、48 KiB の digest を summary 前に出した場合、同じ平均行長なら 156 件目で開始 marker が 64 KiB 外へ出る。プランの「平均 157 failures」は 1 件ずれている。また pytest の summary 行長自体は CI／高 verbosity で無上限である。

(ii) 一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:21-29`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/acceptance-2.log:1023-1134`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/terminal.py:1289-1395,1542-1575`

計算は `49,152 + (11,663 - 11,501) + N × (11,501 / 110)`。155 件では約 65,519.95 bytes、156 件では約 65,624.51 bytes となる。

(iii) 成果物への影響: 現行の `pytest_unconfigure` 案の受理集合は変えないが、段 4 の裁定根拠と境界値参照が誤る。

(iv) 具体的な対処案

「実測 artifact に限った閾値は 156 件目」と訂正し、行長が可変・無上限であることを明記する。現行案の根拠は `unconfigure` 後に summary が無いことへ限定する。

## 2 — must-fix : E2E が hook を `-p` で強制ロードし、実 argv と conftest 自動 discovery を検査していない

(i) 主張

プランの E2E は `-p orchestrator.tests.conftest` を付け、一時 test file を `tmp_path` 外部に置く。これは実際の acceptance で `conftest.py` が自動発見されることを証明しない。プラン自身の「既存自動 discovery だけを使う」という不変条件とも矛盾する。

(ii) 一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:191-219`、`tools/run_tests.py:367-385,1816-1868`、`pytest.ini:12-14`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/findpaths.py:303-326`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/__init__.py:640-714`

実 acceptance は `python -m pytest orchestrator/tests -n N --dist loadgroup` 相当で、`--force-dispatch` は `tools/run_tests.py:149-155` で pytest argv から除去される。mutation harness は `-p no:cacheprovider` を追加するが、`tools/mutation_harness.py:1888-1894` にある targeted recipe である。

(iii) 成果物への影響: E2E が緑でも、実 acceptance／mutation harness で hook が未ロードとなり、受入判定・材料レポートへ digest が現れない経路が残る。

(iv) 具体的な対処案

E2E は `-p orchestrator.tests.conftest` を外し、`orchestrator/tests` 配下を実際の conftest 親として走らせる。少なくとも以下を分けて固定する。

- `tools/run_tests.py` が組む実 argv
- `-p no:cacheprovider` 付き targeted recipe
- `--force-dispatch` を外側 runner に渡す経路

## 3 — must-fix : 49 KiB は dispatcher の実中継 byte budget ではない

(i) 主張

プランは producer の digest bytes だけを測るが、dispatcher は 64 KiB の tail を取った後、各行へ `| ` を追加し、begin/end frame も出力する。digest に改行が多い場合、実際の terminal 出力は producer bytes より大きくなる。

(ii) 一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:115-126,189-209`、`tools/pegasus/dispatch_compute.py:687-704,759-804`、`orchestrator/tests/test_pegasus_dispatch_compute.py:287-313`

`_utf8_tail` の 65,536 bytes 制限は prefix 前の `relayed_tail` にだけ適用され、`_prefix_relay_lines` と frame はその後に追加される。

(iii) 成果物への影響: producer E2E が緑でも、実中継の表示量が契約値を超え、digest の完全性または末尾 64 KiB 保証の参照が不正確になる。

(iv) 具体的な対処案

E2E で producer stdout だけでなく、`_relay_scheduler_logs` 相当の prefix/frame 後の bytes も測る。digest の予算を「source bytes」ではなく「実中継後 bytes」で定義するか、改行数にも上限を置く。改行なし超長行・大量改行・末尾 multibyte 文字を入力に含める。

## 4 — must-fix : ASCII、UTF-8 会計、ANSI 制御文字の仕様が未確定

(i) 主張

プランは「全出力 ASCII」としながら、会計は `longreprtext.encode("utf-8", errors="backslashreplace")` と定義している。通常の日本語はこの指定では escape されず UTF-8 のまま出る。また ANSI escape、CR、DEL などの ASCII 制御文字を除去する規則がない。

(ii) 一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:83-115,140-147`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/reports.py:103-115`、`tools/pegasus/dispatch_compute.py:701-704`、`orchestrator/tests/test_pegasus_dispatch_compute.py:316-338`

pytest の `longreprtext` は描画結果をそのまま返す。既存 relay test も日本語 `界` を 3 bytes として扱っているが、digest 側の escape 後サイズは検査していない。

(iii) 成果物への影響: 日本語で ASCII 不変条件を破るか、ANSI／CR により人間向け terminal の marker・accounting 行が視覚的に壊れ、材料レポートの診断参照が不正確になる。

(iv) 具体的な対処案

canonical renderer を先に定義する。非 ASCII、C0／DEL、backslash、quote、改行を明示的に escape し、`source_bytes` と `rendered_bytes` を別会計にする。日本語 3-byte 境界、ANSI、CR、改行なし超長行を E2E に追加する。

## 5 — must-fix : xdist の worker crash／INTERNALERROR は通常 report 集約の保証外

(i) 主張

通常の failed/error report はプランどおり controller の `stats` に集まる。しかし worker が test 実行前に落ちた場合、または worker の `pytest_internalerror` の場合、必ずしも `stats["failed"]`／`["error"]` に入らない。

collection error 自体は `stats["error"]` に入るため、この部分は穴ではない。

(ii) 一次資料

通常経路: `/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:280-298`、`xdist/workermanage.py:424-431`、`xdist/dsession.py:326-330`、`_pytest/terminal.py:625-637,800-805`

crash 経路: `/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:238-267,432-452`、`xdist/dsession.py:220-236`、`xdist/plugin.py:93-110`

実行時の並列度は `tools/run_tests.py:206-220,1816-1848` で、通常は最大 32 または `IZANAGI_TEST_NPROC` の上書きであり、プランの E2E は `-n 2` に限られる。

(iii) 成果物への影響: worker 起動／collection crash では xdist summary だけが赤くなり digest が出ず、受入赤の原因が未帰属のまま試行台帳・材料レポートへ進む。

(iv) 具体的な対処案

`-n 2` と実 acceptance の並列度を分けて検査し、worker が test 実行前に落ちるケース、`pytest_internalerror`、`--max-worker-restart=0` を追加する。digest へ xdist の worker-loss summary を取り込むか、worker-loss を明示的な `INFRA` 成果物として scope 外と裁定する。

## 6 — must-fix : SIGKILL・OOM・walltime・rc=16 は pytest hook の到達範囲外

(i) 主張

`pytest_unconfigure` は Python プロセスが正常に `config._ensure_unconfigure()` まで到達した場合だけ呼ばれる。SIGKILL、OOM kill、PBS walltime 打ち切りでは hook は実行できない。`run_tests.py` が pytest 起動前に rc=16 を返す場合は child stdout 自体が存在しない。

同程度の頻度であることは未測定だが、これらはコードと runbook が明示的に扱う現実の failure class であり、110 failed の実測と同一視してはいけない。

(ii) 一次資料

`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/main.py:359-373`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/__init__.py:1207-1219`、`tools/pegasus/dispatch_compute.py:450-455,1630-1634,1774-1816`、`tools/run_tests.py:1693-1707,1749-1752,1794-1833`、`tools/README.md:27-34`

dispatch は timeout／job 終了時に partial log を relay できるが、digest marker が生成される保証はない。OOM は cgroup signal として `tools/run_tests.py:1436-1464` で別扱いされる。

(iii) 成果物への影響: rc=16／途中 kill を通常の test failure と同じ受入集合へ混ぜると、試行台帳の原因分類と certified 選択前の材料レポートを誤帰属する。

(iv) 具体的な対処案

段 4 の裁定パッケージに以下を分離して返す。

- pytest セッションが完走した場合の digest 保証
- worker／job が途中終了した場合の `INFRA` 証拠（receipt、scheduler log path、kill reason）
- pytest 起動前 rc=16 の「digest 対象外・受入保留」規則

job-level まで保証するなら、dispatcher または job wrapper の durable checkpoint／partial-log path が必要であり、brief の out-of-scope を変更する裁定が要る。

## 7 — must-fix : nested xdist subprocess の timeout cleanup と資源予算が未契約

(i) 主張

E2E は outer acceptance の xdist worker 内でさらに `-n 2` の pytest を起動する。プランは wall 5 秒、hard timeout 15 秒だけを示し、timeout 時の process group cleanup と nested worker の回収を定義していない。

(ii) 一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:189-211`、`tools/run_tests.py:206-220,1816-1868`、`orchestrator/tests/conftest.py:1-28`、`tools/mutation_harness.py:1098-1113,1132-1157`

既存 mutation harness は `start_new_session=True` と process group の TERM/KILL、`wait` を実装している。一方、現在の conftest は TMPDIR を変更せず、tmpfs は memory cgroup へ直結すると明記している。

(iii) 成果物への影響: E2E の hang／child 残留が outer acceptance の wall、cgroup memory、受入 lease を消費し、TIMEOUT／OOM を新たに発生させて台帳と受入結果を汚染する。

(iv) 具体的な対処案

既存 mutation harness の process-group cleanup を契約として再利用する。5 秒は未実測値として扱い、実際の outer `-n`、compute/login の cgroup、実効 TMPDIR で別途測定する。timeout 後に全 descendant が消滅したことも検査する。

## 8 — nit : より安い代案との比較がなく、現行案の過剰性を裁定できない

(i) 主張

現行案は digest renderer、selection tier、SHA-256 manifest、複数の accounting、nested xdist E2E を新設する。到達保証だけなら、以下の低コスト案もある。

- 2 MiB の収集 tail から dispatcher が digest marker を抽出して末尾へ再配置する
- full log の path・sha256 だけを relay し、人間が receipt から読む
- digest を一行の固定長 marker に縮める
- relay limit を増やす

(ii) 一次資料

`tools/pegasus/dispatch_compute.py:664-684,1728-1773`、`tools/pegasus/dispatch_compute.py:35,741-804`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:43-81,117-147`

(iii) 成果物への影響: 現案をそのまま採ると変更面・受入 wall・診断テスト負担が増えるが、代案を比較しないまま scope と実装コストを固定する。

(iv) 具体的な対処案

段 4 で比較表を裁定する。relay limit 増量だけでは pytest summary が無上限なので保証にならず、path relay は shared filesystem／保持期間に依存し、一行 marker は per-failure 本体・manifest を失う。これらの欠点を明記したうえで、producer-only rich digest を採用する根拠を確定する。

## 総括

must-fix は次の 6 点。

- 実 acceptance／mutation argv と自動 conftest discovery を通る E2E にする。
- dispatcher の prefix/frame 後の実中継 bytes を予算検査する。
- 日本語、ANSI、制御文字の canonical escaping と会計を確定する。
- xdist worker crash／INTERNALERROR／実際の並列度を検査する。
- SIGKILL・OOM・walltime・rc=16 を `INFRA` 経路として裁定する。
- nested subprocess の process-group cleanup と cgroup/TMPDIR 資源契約を追加する。