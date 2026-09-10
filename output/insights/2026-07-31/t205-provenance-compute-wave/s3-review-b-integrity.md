# 段 3 敵対レンズ B (整合・実効性・権限・全層被覆) — Claude opus, read-only

対象 = `s1-brief.md` + `s2-plan.md`。判定と所見は子の出力を凍結したもので、採否は段 4 で親が裁定する。

## 判定

**NO-GO (条件付き)** — 中核設計は堅いが、成果物影響のある欠陥 6 点と裁定必須 1 点を段 4 で潰すまで段 5 へ渡せない。

## real 所見

### R1 [real・最重要] 第一層は `tools/dev_waves/checker.py` の /tmp 隔離 clone 経路を確実に壊す — C-0 の表に載っていない層

根拠: `tools/dev_waves/cli.py:193` (`CheckSpec("provenance", (python, "tools/task_run_check.py", "provenance-check"), timeout_s)`) /
`tools/dev_waves/checker.py:606` (`tempfile.TemporaryDirectory(prefix="dev-waves-check-")` = 既定 `/tmp`) /
`tools/dev_waves/git_state.py:531-560` `create_isolated_checkout` (local clone して detach) /
`checker.py:326-332` (`cwd=<clone>`、`env=_check_env()` は `HOME` 無し、`timeout=`) /
`tools/task_run_check.py:14,59,64` (`_REPO` は clone 側を指す)。

失敗シナリオ: pegasus02 で dev-wave 検証が走ると `current_site()` = `PEGASUS_LOGIN` → 新 gate が dispatch。
`repo_root` = `/tmp/dev-waves-check-*/repo` なので計算ノードで `_job_script:352` の `cd "$REPO"` が失敗
(`/tmp` は共有されない) → `write_failure cwd` → rc=16。`checker.py:335-337` は **rc の値を見ず spec 名だけ**で
理由を決めるため `ReasonCode.PROVENANCE_FAILED` になる。さらに timeout 時 `subprocess.run(timeout=)` は子を SIGKILL するので
`dispatch_compute.py:824-831` の SIGINT/SIGTERM ハンドラが走らず `qdel` されない → **孤児 PBS job が共有 queue に残る**。

成果物影響: dev-wave 検証の provenance slot が恒常赤 → wave が land 不能。`output/task-runs` の
`provenance-check` に `exit_status=16` と queue 待ち duration が入り開発観測台帳が [測定の交絡] を起こす。
infra 失敗が「provenance 違反」として receipt に残るのは D103 の rc 意味論の破壊。

修正案: C-0 の表にこの経路を追加した上で、(i) `cli.py:193` の provenance check を dispatch しない形へ変える、
(ii) checker 側に dispatch 免除の入口を 1 つ持つ (D103 却下の env escape hatch と衝突するので裁定必須)、
(iii) `_default_checks` から provenance を外し C-0 で「保証しない側」に明記する、のいずれかをユーザー裁定へ上げる。

### R2 [real] commit 順序が C-3 を C-2 より先に置き、1 commit だけ「恒真な保証」を作る

根拠: `s2-plan.md:510` 「2. A + C-3 (U2)。3. C-2 (U1)。」 対 `:512` 「依存グラフ: W → (A ∥ C-2) → C-3 → D → B」← **番号付き手順と逆**。
D103 決定 5 (`docs/decisions.md:4600-4607`) は sanctioned を「一次強制が fail-closed する entry point」の exact path 列挙と定める。

失敗シナリオ: C-3 だけ入った tree では checker が `_SANCTIONED_PATHS` に載る = 「自分で fail-closed する」と宣言した状態だが、
C-2 未着地なので実際は login node で 130〜150 秒走る。「拒否される綴り」と「素通しで重い処理が走る綴り」が同時に存在する。

成果物影響: 中間 commit の防壁主張が虚偽になる。修正案: 順序を **W → A → C-2 → C-3 → D → B** に固定し `:510` と `:512` を一致させる。

### R3 [real] `AUDIT_WORKERS = 16` と受入基準 4.58 秒が別 arm の実測 — 構造的に満たせない受入

根拠: insight §11 の表 — threads 16 = 5.60 秒 / threads 48 = 5.23 秒 / **memory + threads 48 = 4.58 秒**。
同 insight の散文「16 並列で頭打ち」は自分の表と矛盾する (16→32 で 6.6% 改善)。**4.58 秒は 48 並列の行**。

失敗シナリオ: `s1-brief.md:26` と `s2-plan.md:482` を 16 並列実装の受入基準にすると、期待値 ≈ 4.9〜5.6 秒に対し
基準を満たさず、実装が正しくても赤になる。逆に「整合した」と書けば [測定の交絡] の捏造になる。

**加えて P5 の賛成根拠が誤り**: D103 決定 6 (`docs/decisions.md:4609-4615`) は `available_cpus()` の `OSError` 捕捉 1 件を
例外宣言した節であって新 gate の並列度決定を縛っていない。16 固定は runbook `:259` の裁定
「計算ノードでは割り当てられた資源を最大限使い、最大並列で回す」と正面から緊張する。

成果物影響: 受入判定 (段 7) の合否そのもの。
修正案: 段 4 で二択を裁定 — (a) 受入基準を「16 並列で 5.5〜6.0 秒、逐次比 4〜5 倍」に書き換える、
(b) `AUDIT_WORKERS` を `min(site_policy.available_cpus(), 32)` にして 4.58 秒基準を維持する。

### R4 [real] schema `/v2` への一方向 bump は in-flight job を殺す。「格上げ」ではなく退行

根拠: `dispatch_compute.py:376-397` (現行 `_job_run` は `schema_version` を**一切読まない**) /
`:359` (`exec "$selected" "$DISPATCHER" --job-run "$REQUEST"` の `$DISPATCHER` は**ジョブ起動時点の live repo** の実体) /
`:28` (`DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900.0`)。

失敗シナリオ: 本 wave 自身が該当する。W の受入で job を投げ、queue 待ち中に A が land すると、
計算ノードで起動した**新** `_job_run` が投入時の v1 request を拒否 → rc=16。今日の挙動は正常なので
plan の「silent failure から明示失敗への格上げ」は誤りで、bump が新たに壊している。

修正案: `_job_run` は v1/v2 の両方を受理し、v1 は `task="tests"` + `pytest_args` として読む 1 リリース分の互換を持つ。
互換を持たないなら「dispatch 中は A を commit しない」を段 4 brief に凍結する。

### R5 [real] docs 予算 223 bytes の捻出は「fence 統合」ではなく規範文 2 行の削除。しかも歯止めを削る向きが逆

根拠 (per-line 実測): `:113` = 30 bytes (「範囲監査では `<range>` を対象範囲に置き換える。」) /
`:119` = 58 bytes (「導入 commit から `HEAD` までの欠落、排他違反、フィールド順、値と role の形式は次で検査する。」) /
fence marker + 空行 8 行 = 計 28 bytes / `:128-130` = 402 bytes。
**fence marker と空行だけを畳んで得られるのは 28 bytes にすぎない。** 93 bytes を出すには `:113` と `:119` の両方を削除するしかない。
`:119` は checker が何を検査するかを述べた唯一の記述である。

`:128-130` の 130 bytes 圧縮 = 32% 削減。この段落は「provenance 記録から製品・モデルの優劣を断定するな」という
**解釈上の歯止め**であり、本 wave は Claude author の実装 commit を waiver で正規化する = 記録に系統バイアスを入れる改修である。
バイアス源を追加する commit で歯止めを削るのは向きが逆。

**算術も 2 bytes ずれている**: W-1(b) 本文の実測は **459 bytes** (plan は 458)。必要削減は 212、plan の 223 で余白は **11 bytes**。

修正案 (削除ゼロで解ける): `docs/ai-provenance.md` には **literal 1 行 + D105 への 1 文ポインタ**だけを置く (~200 bytes、余白 248 に収まる)。
運用規則は**予算表対象外**の `docs/decisions.md` D105 に置く。`WAIVER_POLICY_LITERAL` の exactly-once メタテストは
literal が `POLICY_PATH` に 1 回あれば成立するので検出力は落ちない。これで `:107-123` も `:128-130` も触らずに済み、
「余白 13 bytes」というリスク 1 そのものが消える。

### R6 [real] D-6 の baseline 手順は動かない。差分の事前宣言も誤り

根拠: `tools/check_ai_provenance.py:20` (`REPO = Path(__file__).resolve().parent.parent`) と
`s2-plan.md:480` (`git show <base>:tools/check_ai_provenance.py > $TMP/baseline_checker.py`)。

失敗シナリオ: `$TMP/baseline_checker.py` を実行すると `REPO` = `$TMP` の親になり `_git(cwd=REPO)` が実 repo を指さない → rc=2。
さらに「waiver の新出力行だけが差分」も誤り: baseline checker は waiver を知らないので W の commit を
「実装面に Codex role=author がない」で赤にする。差分は stdout の追加行だけでなく
**stderr の finding 消失・rc 1→0・末尾行の文言変化**を含む。

成果物影響: brief の不変条件を検証する唯一の手続きが機能しない = 恒真な受入。
修正案: (i) baseline は `git worktree add --detach <base>` した作業ツリーで走らせる、
(ii) 比較 range を **wave 開始点 `72849d3` まで**に限定して waiver commit を範囲外にし byte 完全一致を成立させる、
(iii) plan D-3 が production に残す逐次 oracle (`ancestry=None` + `AUDIT_WORKERS=1`) を同一 process 内 oracle として使い、
実 609 commit で findings 完全一致を assert する。

### R7 [real] `rc=16` は `tools/dev_waves/checker.py:336` で `PROVENANCE_FAILED` に誤分類される

根拠: `checker.py:335-339` が returncode の**値を見ず spec 名だけ**で理由を決める。
失敗シナリオ: queue 満杯・`qstat` 権限エラー・receipt 永続失敗のいずれでも rc=16 が返り、
dev-wave receipt に「provenance 違反」として記録される。D103 の rc 意味論が消費側で潰れる。
修正案: `checker.py:335` に `returncode == 16` を infra 側 (`CHECK_FAILED`) へ落とす分岐を足す (所有外なので段 4 で scope 判断)。
入れないなら D105 に残余リスクとして逐語で書く。

### R8 [real] `_SANCTIONED_PATHS` 追加の効果が plan の説明と違う。「反転」は起きていないが pytest 拒否に穴が開く

根拠: `hooks/guard_bash.py:497-552` を実際に辿ると、`python3 tools/check_ai_provenance.py` は
`:506` tools/pegasus 判定・`:509` pytest・`:514` `-m pytest`・`:520-545` builder/ycsb のどれにも該当せず
`:552 return None` = **現状すでに許可されている**。したがって plan の「反転を明示しないと実装子が hook で拒否してしまう」は事実誤認。

**plan が書いていない実際の副作用**: `_SANCTIONED_PATHS` に入ると `:502` で segment 全体が早期 allow になる。
`_script_target:449-457` は python head の第 1 非 option 引数も候補に含めるため
`python3 -mpytest tools/check_ai_provenance.py` が現在は `:517` で拒否されるのに**許可される**。
(分離形 `python3 -m pytest tools/check_ai_provenance.py` は第 1 非 option 引数が `"pytest"` なので拒否のまま。)

成果物影響: ログインノードで pytest が 1 形態だけ通る = D103 決定 5 の穴。受理集合の変更なので D96 手続の対象。
修正案: C-3 の新分岐を `:502` の早期 return より前に置くか、pytest 判定を `_is_sanctioned` より先に評価する。
最低限 `test_hooks.py:743` の positive control に `python3 -mpytest tools/check_ai_provenance.py` の**拒否**を足す。

### R9 [real] `_build_ancestry` の空集合と `tips` 未定義

根拠: `s2-plan.md:400-418` の `tips` はコメントだけで計算方法が本文に無い。`_commit_range` は `--range HEAD..HEAD` で `[]` を返しうる。
失敗シナリオ: 現行 `_audit_history([])` は rc=0。`rev-list --stdin` に空入力を与えると git が非 0 → `RuntimeError` → **rc=2 への退行**。
`tips` を誤って「最初の 1 件」等にすると mask が過小になり **CAB policy 適用済み commit を未適用と誤判定して findings が消える**。
修正案: `_audit_history` 冒頭に空 guard。`tips` は「`*commits` をそのまま渡す」と本文で確定させる (609×41 ≈ 25 KB < ARG_MAX)。

### R10 [real] brief の不変条件「needle の repo 内出現回数を変えない」は過大表現 — 守るべき条件を検査していない

根拠: `test_check_ai_provenance.py:665-669` が固定するのは `CO_AUTHORED_BY_POLICY_NEEDLE` **だけ**、しかも
`docs/ai-provenance.md` 内の count のみ。`IMPLEMENTATION_POLICY_NEEDLE` の出現回数を固定するテストは repo 内に存在しない。
失敗シナリオ: 実際に守るべき不変条件 = `_implementation_policy_commit()` が返す epoch SHA が動かないこと、が検査されない。
既存 needle 行 (`:53`) に触れれば `-S` が変化を拾い、削除すれば epoch が消えて
**実装面 gate 全体が無効化 (`implementation_epoch is None` で全 commit 素通し)** される。
成果物影響: 受理集合が黙って全開になる最悪型。
修正案: W-4 に `test_implementation_policy_epoch_sha_is_unchanged_by_waiver_section` を足し、
`_implementation_policy_commit()` が実 repo で非 None かつ既知 SHA と一致することを assert する。brief の文言も直す。

### R11 [real (小)] `_default_dispatch` は完全に無テストで `task="tests"` 追加はどのテストにも捕まらない

根拠: grep 全走で `_default_dispatch` は `run_tests.py:826` (定義) と `:939` (参照) のみ。seam テストは全て fake を注入する。
修正案: U2 の新規テストに 1 本、`dispatch_compute.dispatch` を monkeypatch して `task="tests"` が渡ることを固定する。

### R12 [real (運用)] 第一層は「commit ごとに 1 PBS job」を生み、wave の壁時計が scheduler 律速になる

根拠: `AGENTS.md:28` / `CLAUDE.md:121` が「commit を作った後は checker」を定型手順として固定。
plan の免除は `--message-file` のみで `--range HEAD^!` (実行 0.2 秒) も dispatch する。queue 待ちは実測 6〜86 秒、上限 900 秒。
修正案: (i) 定型手順を「wave 末に 1 回」へ改める、または (ii) `--range` の選択 commit 数が閾値未満なら local 実行を許す免除を D105 で裁定する。
(ii) は引数由来の閉集合免除なので D103 却下項目 (env escape hatch) には当たらない。

## 攻撃したが破れなかった点

- **trailer key の衝突 (P1)**: `RAW_AI_AGENT_CORRECTION` は `re.escape(CORRECTION_KEY)` の直後に `[ \t]*:` を要求するので
  `AI-Agent-Waiver:` に前方一致しない。`_ai_agent_values:212-220` は完全一致、`_parsed_trailers` も casefold 完全一致 key。**破れなかった。**
- **CAB needle の exactly-once**: W-1(b) には「最終 trailer block に置き」しか現れず部分一致では count が増えない。**plan の判断は正しい。**
- **`test_cab_policy_git_error_fails_closed_with_rc2`**: plan D-1 の畳んだ argv は intercept 条件を両方満たす。fail-closed rc=2 は維持。**破れなかった。**
- **`test_forward_correction_merge_base_rc128_fails_closed_with_rc2`**: 両 epoch を `None` に monkeypatch しているため残る
  `merge-base` は `:634` の 1 本のみ。plan D-2 が据え置くので検出力は保存される。**破れなかった。**
- **`captured.out` 逐語一致テスト**: `waived` が空なら 1 行も出さない設計なので無傷。**破れなかった。**
- **`tools/codex_reasoning_ab.py` の hash 群**: すべて pin 済み commit object から読む。W の編集で赤にならない。**plan の非該当判定は実測で裏が取れた。**
- **receipt/request schema の consumer**: `collect_receipt.py` / `make_acquisition_receipt.py` は `pegasus-dispatch-receipt` を読まない。
  テスト側の `pytest_args` 参照は 1 fixture のみ。**「consumer 不在」は実測で確認。**
- **`_job_run` 経由の任意 command 昇格**: `_read_json_object:364` が symlink を拒否、`submission_dir.mkdir(mode=0o700)`、
  `_job_run:404-405` が `bnode` hostname を独立 assert。`--range` の任意 revspec も単一 argv で shell を経ない。**破れなかった。**
  ただし enum の閉じ具合は**権限境界ではない** — `task="tests"` は pytest → 任意 conftest 読み込みで既に任意コード実行に等価。
  「閉じた enum だから安全」は規律上の価値に表現を弱めるべき (nit)。
- **`.gitignore:25` に `output/pegasus-dispatch/`** があり dispatch が dirty tree を作る経路は無い。**破れなかった。**
- **`--help` の扱い**: gate は `parse_args()` の後なので argparse が `SystemExit(0)` で先に処理する。**破れなかった。**
- **import allowlist meta-test は `check_ai_provenance.py` に無い**。C-2 の `site_policy` import は既存テストを壊さない
  (`run_tests.py:46-51` に同型の先例あり)。

## nit / backlog

- plan `:260-261` の `_interpreter_probe_source` 既定引数の理由は**誤引用**。真の理由は
  `test_pegasus_dispatch_compute.py:329,437` が無引数で呼ぶこと (`dispatch_compute.py:803` が唯一の production 呼出)。
- plan `:278` の `:256-258` は実際には `docs/pegasus-runbook.md:255-257`。
- `--task` は `nargs=REMAINDER` より前に置けば機能するが `-- --task provenance` の順だと `args` 側へ落ちる。runbook に明記すべき。
- `_check_env()` は `HOME` を渡さない。R1 の経路では `qsub` が別要因でも失敗しうる。
- `s1-brief.md:19` の A の成果物影響は、手 `qsub` でも回避できるので A 単独の必然性の根拠にならない。
  **A の必然性は「C の第一層に投げ先が要る」ことにある** — DW-G05 の文言をそう直すべき。
- `s1-brief.md:23` の C「無いと機械強制がゼロ」は**正確**だった (R8 の通り guard_bash はどの分岐でも checker を捕まえない)。
- D96 を厳密に取るなら `test_site_policy.py:253-257` の変更 module tuple に `tools/check_ai_provenance.py` を足すのが筋。

## 未確定事項への推奨

- **(a) `hooks/README.md`**: 更新する。ただし現物の列挙節は作らない (二重管理 = [ドリフト])。
  「Pegasus 層と sanctioned exact path の正本は `hooks/guard_bash.py`、射程と限界は runbook §7」という 1 段落のポインタだけ足す。
- **(b) D の本数**: 1 本 (D105) にまとめる。D96 が要求するのは記録を起こすことであって本数ではない。
  3 つの受理集合変更は単一判断の帰結。ただし**却下案は 3 つそれぞれについて書く**。R1・R7・R12 の残余リスクも同 D へ。
- **(c) walltime**: `00:30:00` 据え置き。`elapstim_req` は確保の上限であって消費ポイントの決定項ではなく、
  短くしても支配項の queue 待ちは縮まない。task 別 walltime という可変軸を足す価値がない。

## 総括

W と D の中核設計は堅い。plan が挙げた既存テスト 3 本の制約は実測で裏が取れ、trailer key の衝突・needle の exactly-once・
receipt consumer・`codex_reasoning_ab` の hash pin・`.gitignore` — いずれも攻撃したが破れなかった。

一方で段 5 へそのまま渡せない欠陥が 6 点ある。最大は **R1** (第一層が `/tmp` 隔離 clone から起動される経路を C-0 が数えておらず、
そこでは dispatch が構造的に失敗し、infra 失敗が `PROVENANCE_FAILED` として台帳に載り (R7)、timeout で孤児 PBS job を残す)。
次いで **R2** (hook の sanctioned 宣言が fail-closed 実装より 1 commit 先行)、**R3** (16 並列と 48 並列で取った 4.58 秒の不整合、
および P5 賛成根拠の D103 決定 6 誤読)、**R4** (schema v2 一方向 bump が本 wave 自身の in-flight job を殺す)、
**R6** (D-6 baseline が `REPO` 解決の都合で動かない)。

**R5** は最も安く直せる: doc には literal 1 行と D105 ポインタだけを置けば削除ゼロで収まり、
「余白 11〜13 bytes」という運用不能な設計とリスク 1 がまるごと消える。
