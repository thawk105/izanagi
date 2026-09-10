# 段 6 焦点再レビュー (R5 closure) — Claude 子 opus / read-only の逐語

親注記: pytest 未実走 (DW-O05)。判定は条件付き GO。新規所見 FR-1 は親が実測で追認した
(下記「親の追認」節)。FR-2 は fix 第 2 巡で閉じ、変異 R7b は KILLED になった。
FR-3 が指摘した並行変異は親の変異 harness であり、走行後の tree clean を実測で確認済み。

読了完了（4 ファイルすべて）。**pytest は一切走らせていない。以下は静的検査のみで、いかなる箇所も「緑」を主張しない。**

以下 `TD` = `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py`、`TT` = 同 worktree の `orchestrator/tests/test_pegasus_test_dispatch.py`。**行番号はすべて git index (`git show :<path>`) の内容**である。理由は次項。

---

## 0. 先に報告すべき異常 — レビュー対象 worktree が**レビュー中に書き換えられている**

- 10:09〜10:11 JST の読取で、作業ツリーの `TD:4415` が `expected_group=bound_policy.queue`、`TD:5311` が `expected_group=snapshot_policy.queue` になっていた。これは事前登録変異 **R4 と R5 が同時に注入された状態**である。
- 直後の再 grep では両方とも `.account` に戻っていた。`stat` は `TD` の mtime = `2026-07-31 10:11:15`(当時の現在時刻 10:11:42、**27 秒前**)。`git diff`(worktree vs index) は空、index 側は一貫して `.account`。
- 結論: 本 worktree で**変異キャンペーンが並行実行中**である。私は以降すべての判定を index の内容に固定した。親への含意は 3 点 — (a) この窓の間に取った受入計測は信用できない、(b) 変異が cumulative に適用されていたなら「単一変異」規律 (`DW-M01`) が破れており kill 帰属が無効、(c) 完了時にツリーが元へ戻ることを `git diff` で確認する必要がある。

---

## 1. 所見別 closed / partial / regressed 表

| ID | 判定 | 根拠 (file:line) と残り |
|---|---|---|
| **RA-1** (completion_unknown 分岐迂回) | **closed** | 束縛が `if clean_return:` の外へ出て `submit_path.exists()` 直下へ移動 (`TD:6742`)。unknown-completion 分岐は WAL witness で拒否される。red = `TT:2619`。 |
| **RA-2** (`submit-identified` 行と未照合) | **closed** | `TD:6472-6484` が行の `(qsub_request_id_raw, job_id_normalized)` を receipt と exact 比較。`_validate_scheduler_lookup_chain` の publish 側照合との非対称は解消。 |
| **RA-3** (gate 自身が攻撃者データ) | **partial（親裁定どおり scope 外だが実質は改善）** | `clean_return` は依然 `qsub-result.json` 由来 (`TD:6663-6666`)。ただし攻撃者が `completion_unknown` を反転して stdout witness を無効化しても、(i) `TD:6655-6661` の qsub-return WAL 整合検査で落ち、(ii) 落ちなくても `TD:6509` の `if not witnessed:` が閉じる。**単一 artifact 改竄に対しては全分岐で閉じた**。journal 全再構成を仮定する攻撃者に対しては未閉のまま（genesis anchor 不在は不変）。台帳の故障モデル明記は依然必要。 |
| **RA-4** (parse 失敗 silent return) | **closed** | `return` を廃し `stdout_identity = None` の棄権へ変更 (`TD:6497-6499`)。棄権時は他 witness 必須。red = `TT:2717`、positive = `TT:2742` 系。 |
| **RA-5** (検証済 bytes でなく disk 再読) | **partial（未変更・nit）** | `TD:6495` `read_text(encoding="utf-8")` は健在。TOCTOU 窓と `OSError`/`UnicodeDecodeError` が `DispatchError` へ変換されない点も同じ。ただし `if clean_return:` 内へ入ったので曝露は縮小。 |
| **RA-6** (他 resume 経路を塞いでいない) | **再確認して所見なし（ただし論拠が変わった）** | 第 2 節に writer 側からの遡及検証を書いた。witness ゼロの正規状態は構成できない。 |
| **RA-7** (monitor の封印不能 dispatch) | **refuted** | 第 3 節。`TD:4982-4989` に入口束縛が**実在**し、`DispatchPolicy` は `@dataclass(frozen=True)` で `account` を含む全 field 比較 (`TD:192-225`)。fix 子の申告は正しい。 |
| **RA-8** (retention 影響) | **記録のみ・nit（未変更、妥当）** | `TD:4402/4415` の経路は不変。RA-7 が refuted になったことで「本 wave が新規に poison を作る」主張はさらに弱くなる。 |
| **RA-9** (`expected_group` 出所) | **所見なし（不変）** | `TD:4313-4316` → `TD:2402-2409`。 |
| **RA-10** (診断文言の回帰) | **partial（未変更・nit）** | `_policy_bound_lookup_candidate` の条件順は fix で触っていない。文言回帰は依然あり、assert する既存 test も依然無い。 |
| **RA-11** (E3 の false rejection 無し) | **closed だが対象が増えた** | fix は matched candidate の **raw も** receipt と照合するようになった (`TD:6485-6493`)。writer 側 (`TD:5732-5737` が `lookup.request_id_raw` をそのまま receipt へ入れる) から遡って同値なので false rejection は増えない。 |
| **RA-12** (R6 正例の WAL 行は製品が書けない) | **記録のみ（未変更・真）** | `TT:1633-1667` の key 集合は依然 `raw/returncode/signal/timed_out/output_limited/completion_unknown` を欠く。 |
| **RA-13** (既存 test を静的に壊さない) | **再確認して同結論** | 第 4 節。加えて親の実測 (4069→4085 = +16 = 段 5 の 9 + fix の 7、失敗集合不変) と整合。 |
| **RA-14** (`create_qsub_result` と `O_EXCL`) | **scope 外（未変更）** | `TD:6772-6780` は健在。裁定パッケージ行き。 |
| **RB-1** (R4 の実効位置は到達する) | **不変（肯定的所見）** | `TD:4402-4416` / `TD:6531`。 |
| **RB-2** (R4 の red/positive 反転) | **記録のみ（未修正・真）** | 台帳の R4 行を「positive が主 killer」へ訂正する義務が残る。 |
| **RB-3** (第 2 連言項が論理的に死) | **closed（構造置換）** | 死んだ `or` 項は消え、tuple 比較 (`TD:6501`) になった。WAL witness (`TD:6478`) と lookup witness (`TD:6486`) では両成分が独立に生きる（行の内部整合を保証する検査が無いため）。stdout witness 側の冗長性だけは残るが、単独削除可能な行ではなくなった。 |
| **RB-4** (`except DispatchError: return` の escape hatch) | **closed** | RA-4 と同根。閉包範囲は「qsub.stdout が parse できる resume」に限らなくなった。 |
| **RB-5** (R6 fixture が非製品 WAL) | **記録のみ（未変更・真）** | `TT:1633-1667`。closure の証拠に数えない、は依然必要。 |
| **RB-6** (偽の緑の罠は無い) | **新 7 件でも再確認** | 新 test はすべて `TD.resume_dispatch` / `_monitor` 直呼び。`match=` 文字列 (`TT:1036/2619/2717/2807`) は fake 側から出ない。 |
| **RB-7** (post-condition assert が変異下で未評価) | **記録のみ（未修正・むしろ拡大）** | 新 red 4 件 (`TT:2619/2717/2807/1036`) も同じ `FakeScheduler([])` sentinel 依存で、変異下では `AssertionError` により赤くなり `assert scheduler.trace == []` は評価されない。 |
| **RB-8** (monkeypatch は正当) | **不変** | R8 pin (`TT` の `_record`) も同 module 内関数の差替で、返り値は本来実装と bit 同一。 |
| **RB-9** (positive control 十分) | **不変** | |
| **RB-10** (新 fixture が既存を壊さない) | **closed（新 fixture も同じ）** | `_qsub_artifacts(snapshot, policy, *, qsub_result=None)` (`TT:1509`) は keyword-only + 既定 None。呼出 17 件中 12 件は位置引数 2 個のまま無影響。`_timed_out_qsub` / `_unparsable_qsub_stdout` は新 5 test 専用。 |
| **RB-11** (未被覆の列挙) | **partial** | 1(死んだ連言項) と 2(escape hatch) は解消。3 (`TD:6495` の非 UTF-8) は**残る**。4 (`TD:5311` の冗長 gate) は RA-7 refuted により**悪化**（第 5 節 R8）。5・6 は不変。加えて新規 2 件（FR-2 と `TD:6740-6741` の重複検査：`"resume submit identity WAL is duplicated"` を assert する test は `TT` に 1 件も無い＝移送前から未被覆）。 |

---

## 2. F1 の 3 witness 合議は fail-closed か（writer 側からの遡及検証）

**束縛の位置（要求どおり）**: `_bind_resumed_submit_identity` の呼出は `TD:6742`。これより後に — WAL append `TD:6751`、qdel `TD:6867` / `TD:6919`、`monitor_job` `TD:6949`、`_recover_submission_identity` `TD:6798`。**append・qdel・monitor のいずれよりも前**である。呼出前に scheduler へ触れる箇所は無い（`_policy_bound_lookup_candidate` は WAL の純パース）。

**新規 scheduler 呼出 / 新規 WAL event = ゼロ**: fix 差分に `append_journal(` の追加は無く、`scheduler.run` を増やす経路も無い。`_bind_...` は WAL payload と `qsub.stdout` の読取のみ。

**witness ゼロの正規状態は構成できない**（`submit-receipt.json` の writer は 3 つだけ）:

1. `TD:5995` (`submit_and_monitor`, source=`qsub-result`) — identity は `parse_qsub_id(result.stdout)` (`TD:5844`) で得たもののみ。到達には `returncode==0 and not completion_unknown` が必要 → resume 側の `clean_return` も真、`qsub.stdout` は同一 bytes（`create_qsub_result` が同じ `result.stdout` を書く）→ **stdout witness が必ず立つ**。receipt→WAL 行の間で crash しても成立。
2. `TD:5732` (`_recover_submission_identity`) — identity は `lookup_scheduler_job` の戻り値のみ。matched の場合、`scheduler-lookup-result` 行は `TD:4909-4930` で**receipt 作成より前に**append 済み。行は `disposition="matched"`・`candidates` 長 1・`job_id_normalized` は receipt と同値なので、resume 側 filter (`TD:6711-6719`) が必ず拾う → **lookup witness が立つ**。WAL 再生経路 (`TD:4780-4801`) でも行は既存。
3. `TD:6779` (resume の再 parse) — `clean_return` かつ parse 成功が前提 → **stdout witness が立つ**。

したがって「receipt 有り・submit-identified 行なし・matched 行なし・(clean_return 偽 or stdout parse 不能)」という正規状態は**存在しない**。`if not witnessed:` (`TD:6509`) による liveness 回帰は見つからない。逆向き（witness 同士が正規に食い違う）も、上記のとおり各 writer が単一の identity 源しか持たないため構成できない（unknown-completion 時に stdout がたまたま parse 可能でも `if clean_return:` (`TD:6494`) が stdout witness を見に行かないので衝突しない）。

**残る例外は 1 つだけ**: `TD:6495` の `read_text` は `qsub.stdout` 不在・非 UTF-8 で `DispatchError` 以外を投げる（RA-5 / RB-11-3）。これは fix 前と同条件（`clean_return` のときだけ読む）なので新規劣化ではない。

---

## 3. F2 の事実誤認主張の検証 — **RA-7 は refuted**

- `monitor_job` 入口: `TD:4982-4987` が snapshot tree から policy を読み、`TD:4988` `if policy != snapshot_policy or policy.policy_sha256 != snapshot.policy_sha256: raise DispatchError("monitor policy differs from snapshot-bound policy")`。**RA-7 の前提「`monitor_job` 内に snapshot 束縛検査は無い」は事実誤認**。この検査は fix1 の差分に含まれていない（patch の最初の `test_dispatch.py` hunk が `@@ -5303`）ので、段 5 時点で既に存在していた。
- `DispatchPolicy` は `TD:192` `@dataclass(frozen=True)`、field は `TD:193-225`。`eq=False` 指定は無いので `!=` は `account` を含む全 field を比較する。
- ゆえに `policy.account == snapshot_policy.account` は `monitor_job` 内で恒真であり、`TD:5311` の `snapshot_policy.account` への差替は**意味論的に no-op**。「封印不能 dispatch」は現行コードで到達不能。fix 子の申告は正しい。
- 同型の入口束縛は `qsub_argv` (`TD:5574`) と `resume_dispatch` (`TD:6536`) にも存在する。

---

## 4. regressed の探索 — fix が新たに壊した箇所は**見つからない**

- **`submit_matches` 重複検査の前倒し** (`TD:6740-6741`): 旧 `if not submit_matches: append / elif len != 1: raise` は raise 条件が `len>=2` のみ。新 `if len(...)>1: raise` と**受理集合は同値**。発火位置が append より前になっただけ。副作用: 「重複 + receipt 不一致」の同時入力で診断文言が重複側になるが、これを assert する test は無い。
- **束縛が `_policy_bound_lookup_candidate` の後ろへ移った**: 「偽 receipt + 壊れた matched candidate」を同時に持つ入力では E3 の文言が先に出る。そのような入力を作る test は `TT` に無い（R1/R2 red は matched 行を持たず `TT:2495/2529` の `differs from the qsub.stdout` に到達する）。
- **`_qsub_artifacts` の keyword-only 拡張**: `TT:1509`。既存 12 caller は位置引数 2 個で無影響、新 5 caller のみ `qsub_result=`。
- **新 fixture**: `_timed_out_qsub` / `_unparsable_qsub_stdout` は `create_qsub_result` の `result` を差し替えるだけで、`_append_qsub_return` は `qsub-result.json` の実値から組むので WAL 整合 (`TD:6655-6661`) を保つ。既存 test は使用しない。
- **段 5 の 9 件**: R1/R2 red は witness が stdout のみ → 同一文言。R1/R2 positive は stdout 一致で受理。R6 red (`TT:2832`) は `_policy_bound_lookup_candidate` が束縛より前で raise → 同一文言。R6 positive (`TT:2861`) は candidate が `request_id_raw=JOB_ID_RAW` / `job_id_normalized=JOB_ID` (`TT:1655-1656`) で receipt と一致 → 新 lookup witness を通る。R3/R4/R5 系は E1 に触れない。**静的に赤へ転じる既存 test は見つからない**（実測ではない）。
- `dataclasses` は `TT:6` で import 済み、`Sequence`/`Mapping` は `TD:9` で import 済み。

---

## 5. 新規所見

### [FR-1] blocking（本 wave 由来でない・裁定パッケージ行き） — 3 つの「policy differs from snapshot-bound policy」gate は `policy_path` まで比較するため、**製品経路では常に発火する**
- `TD:601` `policy_path=policy_path.resolve(strict=True)` が `DispatchPolicy` の第 1 field (`TD:194`) に入り、`@dataclass(frozen=True)` の `__eq__` に参加する。
- 製品は `tools/pegasus/submit_tests.py:359` (`load_policy()` = repo 側 `<repo>/tools/pegasus/test_dispatch_policy.json`) の policy をそのまま `submit_and_monitor` へ渡す (`submit_tests.py:370-374`)。一方 snapshot 側は `<dispatch_dir>/snapshot/tools/pegasus/test_dispatch_policy.json`。**`policy_path` が必ず異なる**ので `policy != snapshot_policy` は真。
- 発火点: `qsub_argv` `TD:5570-5576`（submit の最初）、`monitor_job` `TD:4988`、`resume_dispatch` `TD:6536`（`submit_tests.py:412-418` の CLI resume も同じ）。つまり**製品 dispatcher は submit も resume もできない**。
- 被覆が無い理由: `TT` の `_synthetic_snapshot` は `_write_policy(source, ...)` (`TT:259-263`) で snapshot root 内に policy を書いて同じ path から load するため、テストでは常に一致する (`TT:383` `snapshot_root=source`)。裁定 11 の「製品 dispatcher 未経由」と整合し、実測でも露見しない。
- 成果物影響: **書ける**。F2 の「monitor は snapshot 束縛」という主張は正しいが、その束縛は同時に製品経路を全拒否している。台帳へ「E2/F2 の group 束縛は製品経路で到達検証されていない、かつ現行の入口 gate は製品 policy を拒否する」を明記しないと、RA-7 refuted が「monitor は健全」と読まれる。

### [FR-2] blocking（記録面） — 3 witness のうち **lookup witness だけが変異で守られていない**
- `TD:6485-6493`（比較と `witnessed = True`）を殺す test が無い。`TT` 全体で `"matched scheduler-lookup WAL candidate"` を `match=` する test はゼロ（grep 済み、hit 0）。
- 理由: `_append_matched_lookup_result` (`TT:1642-1667`) は常に `request_id_raw=JOB_ID_RAW` を書き、resume 側 filter (`TD:6716-6718`) が normalized 一致を要求するため、「normalized は一致するが raw が違う候補」を作る test が存在しない。
- さらに `witnessed = True` (`TD:6493`) の削除変異も生き残る: matched 行を持つ唯一の positive (`TT:2861`) は同時に stdout witness も持つため。
- 対照的に WAL witness は `TT:2619/2717`(比較) と `TT:2642`系(unknown-completion positive、witness が WAL 行のみ)で、stdout witness は `TT:2495/2529` と R1/R2 positive で、それぞれ両側とも pin されている。
- 成果物影響: **書ける**。台帳に「3 witness 合議」と書くなら「うち 1 witness は非被覆」を併記する必要がある。閉じるなら test 1 件（raw だけ食い違う matched candidate）で足りる。

### [FR-3] blocking（手続き面） — 第 0 節の並行変異汚染。受入計測とレビュー対象の同一性が保証されていない。

---

## 6. 変異判定

| ID | 判定 | 根拠 |
|---|---|---|
| R1 (E1 id 照合削除) | 殺せる（帰属は弱い） | `TT:2495`。変異下は `FakeScheduler` sentinel の `AssertionError` で赤（RB-7 と同型）。 |
| R2 (normalized のみ比較) | 殺せる | `TT:2529`。tuple 比較 (`TD:6501`) の raw 成分を落とすと通過 → sentinel。 |
| R3 (E2 group 照合削除/反転) | 殺せる | `TD:3248-3251` / `TT:961` `TT:990`。fix は無関係。 |
| R4 (`TD:4415`→`bound_policy.queue`) | 殺せる（RB-2 のとおり positive が主 killer） | 実 FS の 2 件。帰属記述の訂正は未了。 |
| R5 (`TD:5311`→`.queue`) | 殺せる（診断 pin） | `TT:990` の positive。`policy == snapshot_policy` が強制されるので `policy.queue` でも `snapshot_policy.queue` でも同結果。 |
| R6 (E3 の group 検査削除) | 殺せる（純増検出力ゼロは不変） | `TT:2836`。 |
| **R7**（F1 の witness 合議削除） | 殺せる（帰属は弱い） | `TT:2619`(WAL witness 比較)、`TT:2717`(棄権後の合議)、`TT:2807`(`if not witnessed:`)。ただし**lookup witness 分岐だけは殺せない = FR-2**。 |
| **R8**（monitor の `expected_group` を caller `policy` へ戻す） | **殺せない** | `TD:4988` の入口束縛により `policy.account == snapshot_policy.account` が恒真。pin test (`TT` の R8 pin) は変異下でも同一値を観測して緑のまま。fix 子の申告どおりで、原理的に構成不能。 |
| R8a（入口束縛 `TD:4988` の削除） | 殺せる（帰属は弱い） | `TT:1036` `match="monitor policy differs from snapshot-bound policy"`。変異下は sentinel `AssertionError` で赤になり、`assert scheduler.trace == []` / `filesystem.final is None` は評価されない。 |

**殺せない変異: R8（登録済み）と、FR-2 が指す `TD:6485-6493`（lookup witness 分岐、登録外の新規未被覆）。**

---

## 判定

**条件付き GO（実装の差戻しは要求しない）。**
1. F1 は closed（RA-1/RA-2/RA-4/RB-3/RB-4 を閉じ、束縛は append・qdel・monitor より前、新 scheduler 呼出・新 WAL event ともゼロ、witness ゼロの正規状態は writer 側から構成不能）。
2. F2 は「partial」ではなく **RA-7 が refuted**（`TD:4988` の入口束縛は実在し全 field 比較）。ゆえに `TD:5311` の変更は no-op で **R8 は殺せない** — 裁定 2 の「冗長 gate・closure に数えない」枠のままなら受容可。
3. 出荷前に必須の 3 条件: (a) 並行変異でツリーが汚染されているので `git diff` 空を確認してから受入を確定する [FR-3]、(b) 台帳に「3 witness のうち lookup witness は非被覆」と R8 unkillable を明記する [FR-2]、(c) `policy_path` 込み比較による製品経路全拒否 [FR-1] を裁定パッケージへ返す。

---

## 総括

fix 第 1 巡は E1 の弱点（束縛先の選択）を正しく直した — 3 witness 合議は writer 側から遡っても liveness を壊さず、束縛は qdel・monitor・WAL append のいずれよりも前に置かれ、scheduler 呼出も WAL event も増えていない。
RA-7 は fix 子の言うとおり事実誤認で、`monitor_job:4988` の入口束縛が既に caller policy の乖離を全 field で拒否しているため、封印不能 dispatch も登録変異 R8 も構成できない。
一方で新設の 3 witness のうち **lookup witness だけは比較も `witnessed` も殺す test が無く**、fix が主張する「合議」は 2/3 しか pin されていない。
さらに副産物として、`policy_path` が `DispatchPolicy` の等価比較に入るため 3 つの snapshot 束縛 gate が**製品経路では常に発火する**（テストは snapshot 内 policy を使うので永久に露見しない）ことを発見した。
最後に、本レビュー中に対象ファイルが変異注入状態（R4+R5 同時）で観測された。受入の確定前にツリーの復元確認が要る。