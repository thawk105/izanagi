# 段 4 裁定と plan v2 — [T-205]

親が段 3 の 2 レンズ (`s3-review-a-correctness.md` = 正しさ境界 / `s3-review-b-integrity.md` = 整合・実効性) を
real/refuted・採用/不採用・scope 内/外に裁定し、段 5 へ渡す確定設計と変異事前登録を固定する。
**本ファイルが段 5・段 6 の正本**であり、`s2-plan.md` は本ファイルが上書きした箇所については無効とする。

## 0. 裁定表

| ID | レンズ | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-R1 前方訂正の受理集合拡大 | A | **real (最重要)** | 採用 (設計変更) | 内 |
| A-R2 message-file の沈黙 + `NameError` | A | **real** | 採用 | 内 |
| A-R3 / B-R5 docs 予算の破綻 | A+B | **real** | 採用 (**B の代案**) | 内 |
| A-R4 / B-R3 並列度と受入基準の不整合 | A+B | **real** | 採用 (**P5 を改訂**) | 内 |
| A-R5 / B-R6 baseline 手順が実行不能 | A+B | **real** | 採用 | 内 |
| A-R6 不変条件が定義上成立しない | A | **real** | 採用 (分解) | 内 |
| A-R7 免除件数の意味 | A | **real** | 採用 | 内 |
| A-R8 変異の帰属不成立 3 本 | A | **real** | 採用 | 内 |
| A-R9 `--message-f` 接頭辞省略で queue 詰まり | A | **real** | 採用 | 内 |
| A-R10 / B-R7 rc=16 の台帳混入と誤分類 | A+B | **real** | 採用 (誤分類のみ実装) | 内 |
| B-R1 `/tmp` 隔離 clone で dispatch が壊れる | B | **real** | **不採用 (既存欠陥・別 T)** | **外** |
| B-R2 commit 順序の矛盾 | B | **real** | 採用 | 内 |
| B-R4 schema v2 一方向 bump が in-flight を殺す | B | **real** | 採用 | 内 |
| B-R8 `-mpytest` の穴 | B | **real** | 採用 | 内 |
| B-R9 空集合と `tips` 未定義 | B | **real** | 採用 | 内 |
| B-R10 needle 不変条件が守るべき条件を検査していない | B | **real** | 採用 | 内 |
| B-R11 `_default_dispatch` 無テスト | B | **real (小)** | 採用 | 内 |
| B-R12 commit ごとに 1 PBS job | B | **real (運用)** | **不採用 (残余リスク記録)** | 外 |

### B-R1 を scope 外とした根拠 (親の実測)

`tools/dev_waves/checker.py:623-626` が `create_isolated_checkout(..., os.path.join(temporary, "repo"))` で作る
`/tmp` clone を、`:634` の `run_check_specs` が全 check の cwd に使う。その check 集合
(`tools/dev_waves/cli.py:187-194`) には **`CheckSpec("orchestrator", (python, "tools/run_tests.py", "orchestrator/tests"), ...)`**
が既に含まれる。`run_tests.py` は login node で dispatch する実装なので、**同じ経路の破壊は provenance 以前に
`orchestrator` check で既に成立している**。よって B-R1 は本 wave が新設する欠陥ではなく、
`dev_waves` supervisor の隔離 clone 置き場に関する既存欠陥である (DW-G03 の独立 2 例が揃った状態)。

本 wave では (i) C-0 の責務分界表に「`/tmp` 隔離 clone 経由は第一層が保証しない」を逐語で書き、
(ii) B-R7 の rc=16 誤分類だけを直し、(iii) clone 置き場の是正を**新規 T として worklog へ起票**する。
supervisor の設計変更は受理集合と実行場所を変えるためユーザー裁定事項であり、本 wave の scope に入れない。

### B-R12 を不採用とした根拠

対応案 (定型手順を「wave 末に 1 回」へ変更) は `docs/dev-wave/operations.md` の `DW-O17` を編集する必要があるが、
同ディレクトリは 23983/24000 bytes で余白 17 bytes しかなく、予算引き上げは T-127 のユーザー裁定で禁止されている。
かつ commit ごとの job (queue 待ち実測 6〜86 秒) は、置換前のログインノード 130〜150 秒 × 同数より
共有資源の消費が小さい。**残余リスクとして D105 に逐語で記録**して閉じる。

## 1. 確定設計 (plan v2) — `s2-plan.md` からの差分だけを書く

### W-1 (改訂・**B-R5 の代案を採用**): `docs/ai-provenance.md` は削除ゼロで ~200 bytes だけ増やす

`s2-plan.md` の「458 bytes の新節 + 223 bytes の削減」は**破棄する**。代わりに
`## 実装面の Codex author 契約` 節の末尾 (`:63` の bullet の直後、`:64` の空行の前) へ次だけを足す。

    - Codex が実行不能な期間はユーザー裁定を得て `AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>` を
      最終 trailer block に置き、同じ block の `AI-Agent` に `role=author` を持たせることで前段を免除する。
      checker は免除を stdout へ出す。運用規則と抑止は D105。

- **既存本文を 1 行も削らない。** A-R3 の「56 bytes 不足」も B-R5 の「歯止め条項を削る向きが逆」も同時に消える。
- 挿入後の byte 数は段 5 の実装子ではなく**親が commit 前に `wc -c docs/ai-provenance.md` で 9000 以下を実測**する。
- `WAIVER_POLICY_LITERAL` は `AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>` とし、上記本文と逐語一致させる。
- 運用規則 (恒久経路・機械上限なし・免除件数の公開義務・却下案・残余リスク) は**予算表対象外の `docs/decisions.md` D105** に置く。

### W-3 (改訂 1・**A-R1**): 前方訂正の受理集合を広げない

`tools/check_ai_provenance.py:657` の連言へ `and not correction.waiver.exact` を追加する。
すなわち **waiver 行を持つ commit は forward correction の担い手になれない**。

- 採用理由: 「waived=False 版の findings で `:663` を評価する」案 (A-R1 の代替案) は `CommitAudit` に
  二重の findings を持たせることになり、どちらが正本かの二義性を作る。担い手資格の側で閉じるほうが
  受理集合の変化が「狭くなる方向だけ」に限定され、証明が 1 行で済む。
- 不変条件: この変更により forward correction の受理集合は**現行と同じか狭くなる**。広がらないことを
  A-R1 の反例 (実装面 path + claude-only author + waiver の correction commit) で固定する。

### W-3 (改訂 2・**A-R7**): 免除件数は実発火だけを数える

`validate_implementation_author` の戻り値を `tuple[list[str], bool]` (`findings`, `waived_applied`) にする。
`waived_applied` は **`if waived: return []` を実際に通ったときだけ True**。計上はこの bool に基づく。

- 既存 4 呼出 (`test_check_ai_provenance.py:605,614,617,623`) は戻り値形が変わるので**同じ変更単位で更新する** (D96)。
- docs-only commit に waiver を付けても計上されない = 件数が「免除発火数」の意味を持つ。

### W-3 (改訂 3・**A-R2**): message-file 経路でも免除を出す

`main()` の `corrected` 初期化 (`:762`) の隣に `waived: list[ImplementationWaived] = []` を置く。
message-file 分岐でも `waiver.exact` かつ `waived_applied` なら 1 件積む (label は `args.message_file`)。
出力ループは両分岐共通で `if findings:` の**前**に置く。

### C-2 (改訂・**A-R9**): 免除判定は raw token 集合を作らない

`tools/run_tests.py:111-114` / `:381-396` の raw token allowlist は**移植しない**。
site gate は `parser.parse_args()` の後に置き、判定は `args.message_file is not None` だけとする。
これを C-2(f)「意図的に移植しない」の 4 点目として明記する。

### C-3 (改訂・**B-R8**): 新分岐は `_is_sanctioned` の早期 return より前

`hooks/guard_bash.py` の provenance 分岐は `:502` の `_is_sanctioned` 早期 allow より**前**に評価する。
`test_hooks.py` の positive control に `python3 -mpytest tools/check_ai_provenance.py` の**拒否**を必ず含める
(現在は `:517` で拒否されているものが、sanctioned 追加で許可に反転する穴)。

### A (改訂・**B-R4**): schema は v1/v2 の両受理

`_job_run` は `{"pegasus-dispatch-request/v1", "pegasus-dispatch-request/v2"}` を受理する。
v1 は `task="tests"` + `request["pytest_args"]` として読む。未知の schema_version だけを `DispatchError` にする。
これで queue 待ち中に A が land しても in-flight job が死なない。

### D (改訂 1・**A-R4 / B-R3**): 並列度は site 由来、受入基準は倍率

**P5 を改訂する。** `AUDIT_WORKERS` を固定 16 ではなく `min(site_policy.available_cpus(), 32)` の
既定関数にする (`site_policy.available_cpus()` は `orchestrator/campaign/site_policy.py:79` に実在、cgroup/affinity 尊重)。

- 改訂理由: (i) 両レンズが独立に「D103 決定 6 は `available_cpus()` の `OSError` 捕捉 1 件の例外宣言であって
  並列度決定を縛らない」と実測した、(ii) 4.58 秒は **48 並列 + bitset** の arm の値であり 16 固定では構成上出ない、
  (iii) runbook §7 のユーザー裁定「計算ノードでは割り当てられた資源を最大限使い、最大並列で回す」に従うのが筋。
- 上限 32 を置く理由: insight §11 で 32→48 は 5.23→5.23 秒 (改善ゼロ)。git subprocess の fork/exec が律速なので
  48 まで開けても得がなく、共有ノードでの process 生成圧だけが増える。
- **env による上書きは作らない** (D103 の却下項目 = escape hatch)。テストは module 属性の monkeypatch で切り替える。
- **受入基準**: 「逐次 (`AUDIT_WORKERS=1`, `ancestry=None`) 比 **≥4.5 倍**、かつ findings/corrected が完全一致」。
  4.58 秒は 48 並列 + bitset の**参照値**として括弧書きで引くだけとし、合否判定に使わない。

### D (改訂 2・**B-R9**): 空集合 guard と `tips` の確定

- `_audit_history` の冒頭に `if not commits: return HistoryAudit([], [], [])` を置く (現行 rc=0 を保存)。
- `_build_ancestry` の pickaxe は **`*commits` をそのまま rev として渡す** (「tips を選ぶ」実装は作らない)。
  レンズ A の実測どおり `--stdin` は祖先閉包を返すので `P ∩ closure` は同じであり、実装ミスの余地だけが消える。
  argv 長は 609 × 41 ≈ 25 KB で `ARG_MAX` 内。

### D (改訂 3・**A-R5 / A-R6 / B-R6**): 受入の不変条件を 2 本に分解する

brief `:30` の「findings と forward-correction が baseline と完全一致」は W を含む wave では**定義上成立しない**ので、
次の 2 本へ置き換える。

- **(i) D 限定の byte 一致**: range を `<policy>..72849d3` (wave 開始点まで) に限定し、
  baseline (wave 開始時の checker) と現行 checker の stdout / stderr / rc を byte 比較する。
  waiver commit が range 外なので完全一致が成立し、かつ D の新設コードパス (bitset + thread pool) は全 commit で通る。
- **(ii) W の受理集合変化の明示列挙**: 変わった集合 (waiver 受理、免除発火、前方訂正の担い手資格の縮小) を
  境界テストで固定し、**D105 に逐語列挙**する。「完全一致」を W に掛けない。
- **baseline の作り方 (A-R5)**: `git show <base>:tools/check_ai_provenance.py > $TMP/baseline.py` は
  `REPO = Path(__file__).resolve().parent.parent` が job tmp を指すため**使わない**。
  insight §11 と同じ作法で、module を import して `provenance.REPO` を差し替える使い捨て probe を job tmp に置く。
  repo 内へ一時ファイルを置かない (未追跡ファイルが land を止めた T-200 の前例)。

### B (改訂・**B-R10 / B-R1 / B-R12**): docs に書く内容

- brief の不変条件の文言を「repo 内出現回数を変えない」→
  **「`docs/ai-provenance.md` 内の各 needle の count を 1 に保ち、`_implementation_policy_commit()` の返す epoch SHA を動かさない」**へ訂正する。
- C-0 の責務分界表に「`tools/dev_waves/checker.py` の `/tmp` 隔離 clone 経由は第一層が保証しない」を明記する。
- runbook §7 の強制の層に「hook が閉じるのは綴り差だけ」を明記する (B-R8 の反転を含む)。
- `hooks/README.md` は**現物の列挙節を作らず**、「Pegasus 層と sanctioned exact path の正本は `hooks/guard_bash.py`、
  射程と限界は runbook §7」という 1 段落のポインタだけ足す (B の推奨 (a) を採用。二重管理 = [ドリフト] を作らない)。

### 未確定事項の裁定 (plan risk 10)

- **(a) `hooks/README.md`**: 更新する (ポインタ 1 段落のみ)。
- **(b) D の本数**: **1 本 (D105)** にまとめる。3 つの受理集合変更は単一判断の帰結。ただし却下案は 3 つそれぞれについて書き、
  R1 (既存欠陥・別 T)、A-R10/B-R7 (rc=16 の台帳意味論)、B-R12 (commit ごとの job) を残余リスクとして逐語で残す。
- **(c) walltime**: `00:30:00` 据え置き。`elapstim_req` は確保上限であって消費ポイントの決定項でなく、
  短縮しても支配項の queue 待ちは縮まない。理由を D105 に 1 行残す。

## 2. 凍結する界面 (段 5 の 2 owner が並行するための契約)

1. **dispatch 署名**: `dispatch_compute.dispatch(args: Sequence[str], *, task: str = "tests", repo_root=None, environ=None, ...) -> int`
2. **waiver literal**: `AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>` (物理 1 行、最終 trailer block)
3. **infra rc**: `PEGASUS_DISPATCH_RC = 16` (`tools/run_tests.py:110` と同値。meta-test で照合)
4. **task enum**: `{"tests", "provenance"}` の閉集合。`DEFAULT_TASK = "tests"`

## 3. commit 戦略 (**B-R2** を採用。段 5 着手後に親が改訂)

**W / A / C-2 / C-3 / D / B を 1 本の統合 commit にまとめ、worklog + insight の記録を後続 commit にする。**

段 4 当初は `W → A → C-2 → C-3 → D → B` の順次 commit を確定させたが、親が commit 手順を実際に追って
次の 2 つの矛盾を検出したため改訂する。

1. **鶏卵が閉じない**: 先頭 commit がどれであっても、それが実装面 (`tools/`) を含む Claude author の commit
   である以上、その時点の checker (waiver 未実装) が `--message-file` preflight で拒否する。
   waiver を含む W を先頭にすると、今度は checker が `dispatch(..., task="provenance")` を呼ぶのに
   task 引数が存在しない (A 未着地) 状態になる。
2. **B-R2 が指摘した「宣言だけが先に真になる窓」は、順序を入れ替えても隣接 commit 間に必ず残る。**

統合 commit なら (i) staged の新 checker が自分自身の message を `--message-file` で受理するので鶏卵が解け、
(ii) 防壁の宣言と実装が同一 commit に入るので恒真な保証の窓が存在せず、(iii) D96 の「新しい設計判断の記録と
境界テストを同じ変更単位で」を厳密に満たす。B-R2 の要求は「順序」ではなく「同時性」で満たす。

## 4. 段 5 の owner 分割 (素集合。plan の修正案を採用)

| owner | 所有ファイル (これ以外を触らせない) | 担当 |
|---|---|---|
| **U1 checker** | `tools/check_ai_provenance.py`、`orchestrator/tests/test_check_ai_provenance.py` | W-3 / W-4 / C-2 / C-4 前半 / D 全部 |
| **U2 dispatch・hook** | `tools/pegasus/dispatch_compute.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py`、`hooks/guard_bash.py`、`orchestrator/tests/test_hooks.py`、`tools/run_tests.py` (`:831` の 1 行のみ)、`tools/dev_waves/checker.py` (`:335` の rc=16 分岐のみ) | A 全部 / C-3 / C-4 後半 / B-R7 / B-R11 |
| **親** | `docs/ai-provenance.md`、`docs/decisions.md`、`docs/pegasus-runbook.md`、`AGENTS.md`、`hooks/README.md`、`docs/worklog.md` | W-1 / W-2 / B 全部 |

**worktree 分離の扱い (DW-S05-A からの逸脱と根拠)**: `DW-S05-A` は codex の `workspace-write` sandbox が
cwd 全体を書けることへの対策として worktree 分離を要求する。本 wave の実装子は**ユーザー裁定により Claude 子**であり、
編集は Edit ツール単位で所有パスを prompt で厳格指定できる。所有集合が素集合である以上、同一 worktree での並行編集で
ファイル衝突は構造的に起きない。**親は両子の完了後に `git status --short` を取り、所有外の path が変更されていないことを
機械的に検査する**。これで `DW-S05-A` の目的 (所有の素集合性の保証) は達成される。

## 5. 変異事前登録 (DW-M01)

段 6 の fix 完了後、統合 commit に対して実施する。各変異は「無効化時の赤理由が一つに絞れること」を
段 6 の `DW-M07` で anchor 再検証してから走らせる。**期待 node は実効 gate を検査するものだけを登録する** (F60)。

| # | 変異位置 | 変異内容 | 期待 KILL node |
|---|---|---|---|
| M1 | `check_ai_provenance.py` `validate_implementation_author` | `if waived: return []` を削除 | `test_waiver_exact_line_exempts_implementation_author_gate` |
| M2 | 同 `_waiver_audit` | 物理 1 行性検査 (`len(raw_values) != 1`) を削除 | `test_waiver_boundary_rejects_malformed_and_out_of_block[two-lines]` |
| M3 | 同 `_waiver_audit` | final block の `role=author` 要求を削除 | `test_waiver_requires_own_role_author_ai_agent_line` |
| M4 | 同 `_audit_history` correction 成立条件 | `and not correction.waiver.exact` を削除 | `test_waiver_does_not_widen_forward_correction_acceptance` |
| M5 | 同 `_audit_history` 冒頭 | 空集合 guard を削除 | `test_audit_history_empty_range_returns_zero_findings` |
| M6 | 同 `_build_ancestry` | `--topo-order` を外す | `test_ancestry_bitset_matches_merge_base_oracle_for_every_pair` |
| M7 | 同 `_Ancestry.is_descendant` | 反射性 (`acc = 1 << i`) を削除 | 同上 |
| M8 | 同 `_audit_history` pool | `pool.map` を `as_completed` 順へ変更 | `test_audit_history_is_identical_across_worker_counts_and_ancestry` |
| M9 | 同 `main()` site gate | `PEGASUS_SUSPECT` の拒否を削除 | `test_suspect_history_audit_refuses_with_infra_rc_without_dispatch` |
| M10 | 同 `main()` site gate | `--message-file` 免除を削除 | `test_login_message_file_is_dispatch_exempt` |
| M11 | `dispatch_compute.py` `_dispatch_impl` | task enum 検査を削除 | `test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc` |
| M12 | 同 `_job_run` | schema_version の v1 受理を削除 | `test_job_run_accepts_v1_request_as_tests_task` |
| M13 | `hooks/guard_bash.py` | provenance 分岐を `_is_sanctioned` の後ろへ移動 | `test_bash_login_blocks_nonsanctioned_provenance_entrypoints[dash-m-pytest]` |
| M14 | `check_ai_provenance.py` 計上箇所 | `waived_applied` を `waiver.exact` へ戻す | `test_waived_count_excludes_docs_only_commits` |

**正例 (受理集合の過剰縮小を検出、DW-M01 後段)**: M4 の修正が「waiver 無しの正常な forward correction」まで
拒否していないことを `test_forward_correction_without_waiver_is_still_accepted` で固定する。

### 段 6 fix 後の期待 node 更新 (DW-M07 の anchor 再検証で確定した差分)

fix 子 2 本と両レビューの実測により、上表の期待 node を次のとおり改める。原因はいずれも一意なので
`DW-M01` の単一理由性は満たす (レビュー B の N3 が指摘した「期待 node 欄が 1 個しかない」問題の是正)。

- **M4**: 期待 node は 2 本になった — `test_waiver_does_not_widen_forward_correction_acceptance` に加え、
  fix で新設した `test_waiver_disqualified_correction_carrier_explains_the_reason` も落ちる。
  U1 の変異 probe で rc 1→0 と `forward-corrected=1` の出現を実測済み。
- **M8**: 期待 node を **`test_audit_history_findings_follow_input_order_under_skewed_latency` (新設) へ差し替える**。
  旧 `test_audit_history_is_identical_across_worker_counts_and_ancestry` は M8 に対し**確率的**であり
  (完了順が偶然入力順と一致すると生存する)、帰属が決定的でない。新 node は後の commit ほど速く終わる
  非対称遅延を入れ、実完了順が入力順の完全な逆 (`[5,4,3,2,1,0]`) でも findings が入力順であることを実測する。
- **M2 / M3 / M14**: 期待 node は複数落ちる (M2 は `[body-plus-valid]`、M3 は `[split-blocks]`、
  M14 は stdout テストも)。原因は一意。
- **M13**: 期待 node に `test_provenance_script_borrow_does_not_lend_sanctioned_status` を追加する
  (借用抑止が `_is_sanctioned` の後ろへ動くと末尾 assert も同時に赤くなる。原因は同一)。
  U2 の変異 probe で「負例 7 形のうち `dash-m-pytest` だけが ALLOW へ反転」を実測済み。
- **M11**: レビュー B の N2 のとおり、`if task not in TASKS: raise ValueError` を消しても直後の
  `TASKS[task]` が `KeyError` を投げ同じく INFRA_RC になる。**この変異は受理集合を変えず例外クラス名だけを
  変える**ので、`DW-M03` に従い kill ではなく **diagnostic sensitivity pin として別枠に記録する**。

**A-R8 で指摘された恒真テストの是正 (登録の前提)**:
- `AUDIT_WORKERS` はソース文字列 grep でなく、**worker 内の同時実行高水位を記録して `=1` で 1、`>1` の設定で 2 以上**を assert する。
- `test_waiver_does_not_widen_forward_correction_acceptance` の vector は A-R1 の反例 (実装面 path + claude-only author + waiver) を必ず含む。
- `test_waived_count_*` の vector は「実装面 path + claude-only author + waiver で finding が消える」形を必ず含む。

## 6. 段 5 実装子への必須指示 (DW-S05-B / DW-S05-C + 本 wave 固有)

- **docs を編集しない。commit しない。** 所有ファイル以外を触らない。
- 緑を主張するなら走らせた nodeid を併記する。**ただしログインノード `pegasus02` では pytest を一切走らせない** —
  実測は親が計算ノードへ dispatch する。子は静的検査 (`python3 -m py_compile`) までとし、走らせていないものを緑と書かない。
- **未裁定の意味論の択一を残さない** (F54)。本ファイルで裁定済みの設計に従い、迷ったら実装せず報告する。
- 親が管理する退避 artifact はない (F53)。tree の現状が正本である。
- 期待して赤くなる finding 集合を事前指定し、それ以外は回帰として報告する。
- 所有外の caller・共有 fixture・consumer test への波及可能性を完了報告に静的に列挙する。
- 指示にない受理集合の拡大・縮小をしない。変更前の受理・拒否挙動を報告に明記する。
