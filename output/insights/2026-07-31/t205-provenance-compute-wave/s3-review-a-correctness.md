# 段 3 敵対レンズ A (正しさ境界と防壁の射程) — Claude opus, read-only

対象 = `s1-brief.md` + `s2-plan.md`。判定と所見は子の出力を凍結したもので、採否は段 4 で親が裁定する。

## 判定

**NO-GO** — 段 5 開始前に plan の修正が必須 (R1 が brief 不変条件の反証、R3 で gating commit が機械的に赤、R5/R6 で受入手順が実行不能または恒真)。

## real 所見

### R1 [real / 最重要] waiver は forward correction の受理集合を**実際に**広げる — plan W-3(f) の論証は非 sequitur

根拠: `tools/check_ai_provenance.py:663` の `and not correction.normal_findings` / `s2-plan.md:146-151, 172-173` /
既存テスト `orchestrator/tests/test_check_ai_provenance.py:1839-1850` (`codex-author` param) と `:1854-1877`。

失敗シナリオ: 既存テストが逐語で固定している形がそのまま反例になる。correction commit が `tools/correction.py` を触り
`AI-Agent: product=claude; model=fable-5; reasoning=xhigh; role=author` だけを持つとき、現行は `normal_findings` に
「実装面に Codex role=author がない」が入り `not correction.normal_findings` が False → **前方訂正は不成立** (rc=1)。
同じ message に `AI-Agent-Waiver:` を 1 行足すと `validate_implementation_author(..., waived=True)` が `[]` を返して
`normal_findings` が空になり、**前方訂正が成立して `6b64d21` の欠落 finding が抑止され rc=0 になる**。

plan は「`:657-666` の判定に `waiver` を一切参照させない」から広がらないと論じるが、広がる経路は `waiver` の直接参照ではなく
`normal_findings` の**中身が waived の関数である**こと。参照の有無は無関係。

成果物影響: 前方訂正は「履歴上の provenance 欠落を訂正済みとして stdout/台帳に記録する」唯一の経路。waiver 1 行で
その連言条件 (自身の通常 green) が緩む = **受理集合が拡大**し、`docs/ai-provenance.md:95-96` が公表している契約と実装が食い違う。

修正案: `:577-583` で waived 適用前後の findings を両方 `CommitAudit` に持たせ `:663` の述語は **waived=False 版**で評価する。
または `:657` の連言に `and not correction.waiver.exact` を足し「waiver 付き commit は前方訂正の担い手になれない」を明示する。
plan `:208` の test vector も上記反例に差し替える。

### R2 [real] `--message-file` 経路の免除は完全に沈黙し、かつ plan 逐語実装で `NameError`

根拠: `s2-plan.md:175-177` と `:179-188` / production `tools/check_ai_provenance.py:762` (`corrected` だけが分岐前に初期化)。

失敗シナリオ: waiver が実際に使われるのは commit を作る瞬間 = `--message-file` preflight。そこで免除件数が 1 行も出ない。
ユーザー裁定「免除件数を stdout に出して沈黙させない」が最も必要な場所で不成立。加えて plan (h) を逐語実装すると
message-file 分岐で `waived` が未定義のまま `for record in waived:` に到達し、`try/except` の外なので **traceback で落ちる**。

修正案: `:762` の隣に `waived: list[ImplementationWaived] = []` を初期化し、message-file 分岐でも `waiver.exact` なら 1 件積む
(SHA 不在なので label は `args.message_file`)。出力ループは分岐共通。

### R3 [real] docs 予算の算術が閉じない — 実測 **56 bytes 不足**で `check_docs.py` が赤 (W は wave の gating commit)

| 項目 | plan の主張 | 実測 |
|---|---|---|
| waiver 本文 | 458 bytes | **459** (+ 区切り空行 1 = 純増 **460**) |
| 現況 / 上限 | 8752 / 9000 | 一致 (必要削減 = **212**) |
| `:107-123` fence 統合 | 93 bytes | **上限 26** (```` ```bash ```` 8 + ```` ``` ```` 4 + 空行 1 の 2 組) |
| `:128-130` 圧縮 | 130 bytes | 該当 3 行は 402 bytes (= 32% 削減) |

fence 行だけを畳んで得られるのは 26 bytes。93 に届かせるには `:113` (30 bytes) と `:119` (58 bytes) の説明文を消すしかなく、
その場合は 116。**93 はどちらの解釈でも再現しない**。指定 2 項目の合計は 26 + 130 = 156。212 − 156 = **56 bytes 不足**。
plan の「残 margin 13 bytes」は成立しない。

さらに `:128-130` は「観察データであり統制実験ではない/交絡するので優劣を断定しない」という**分析誤用の防止条項**であり、
32% 圧縮は plan の「内容は保存」と両立しない。waiver という利便機能のためにここを削るのは規律 5 (盛らない) の逆。

### R4 [real] 「16 固定」では 4.58 秒は出ない — 誤前提、かつ受入基準が構成上不成立

根拠: insight §11 の表。memory+threads の**唯一の実測 arm は 48 並列で 4.58 秒**。16 並列の実測は threads 単独の
**5.60 秒 (bitset なし)** だけで、memory+threads@16 の測定は存在しない。threads 単独で 16→32 は 5.60→5.23 (7% 改善) であり、
同 insight の prose「16 並列で頭打ち」は自分の表と 7% ずれる。plan `:27` の P5 賛成根拠はこの prose の引き写し。

成果物影響: plan `:482` (D-6 手順 3) は P5 の実装では**構成上不整合になる受入基準**。外挿値は 4.9 秒前後 (5.1 倍)。
brief `:26` の「実測 4.58 秒 = 5.5 倍を捨てる」も 48 並列の値を 16 固定案の成果物影響として引いている。

修正案: 受入基準を「baseline (逐次) 比 ≥4.5 倍、かつ findings/corrected 完全一致」に書き換え、4.58 は 48 並列の参照値として括弧書きにする。

### R5 [real] D-6 の baseline 比較手順は実行不能 — `REPO` が job tmp を指す

根拠: `tools/check_ai_provenance.py:20` `REPO = Path(__file__).resolve().parent.parent` / `s2-plan.md:480`。

失敗シナリオ: job tmp に置いた baseline は `REPO` = `$TMP` の親を指し、`_git(..., cwd=REPO)` が izanagi repo の外で走る。
最良で「not a git repository」→ rc=2、最悪で親ディレクトリが別 repo なら**無関係な履歴を監査して「違反なし」を返す恒真 baseline** になる。

修正案: insight §11 と同じ作法 (`:233-236` に前例) — module を import して `provenance.REPO` を差し替える使い捨て probe を job tmp に置く。
repo 内へ一時ファイルを置く案は、未追跡ファイルが land を止めた前例 (T-200) があるので採らない。

### R6 [real] 不変条件「findings と forward-correction が baseline と完全一致」は W を含む wave では**定義上**成立しない

根拠: `s1-brief.md:30` / `s2-plan.md:482`。

失敗シナリオ: W が land した時点で wave 自身の commit 群が `AI-Agent-Waiver` + claude-only author を持つ。
既定 range (`policy..HEAD`、**現在 609 commit**) を baseline checker で走らせるとそれらに finding が出て rc=1、新 checker は rc=0。
差分は「waiver の新出力行 (stdout)」だけでなく **stderr の finding 消失と rc** に及ぶ。
逆に差分を消すために range を wave 開始点で切ると、新設コードパスを一切通らない比較になり**受入が恒真化**する。

修正案: 不変条件を 2 本に分解する。(i) **D 限定**: `--range <policy>..72849d3` で baseline と「D のみ適用版」が findings/corrected/rc を byte 一致。
(ii) **W**: 受理集合の変化は単体テストの境界表で列挙し、「変わった集合」を D105 に明示列挙する。「完全一致」を W に掛けない。

### R7 [real] 免除件数が「免除発火数」ではなく「waiver 行の付与数」

根拠: `s2-plan.md:170-171` (`if a.waiver.exact` で計上) / `tools/check_ai_provenance.py:420`。
失敗シナリオ: docs-only commit に waiver 行を付けると `validate_implementation_author` は `:420` で早期 return しており
**免除は 1 bit も発火していない**のに計上される。D105 が「件数の公開が唯一の抑止」と書く以上、件数の意味が実体と違うことは
同じ D に書かないと後続が件数を根拠に誤判断する。
修正案: `validate_implementation_author` を `(findings, waived_applied: bool)` にして**実際に `if waived: return []` を通った時だけ**計上する。

### R8 [real] 変異の帰属が成立しないテストが 3 本

- `test_audit_workers_is_fixed_and_not_site_derived` (`s2-plan.md:472`): **ソース文字列 grep** であり、
  (a) `ThreadPoolExecutor()` を無引数で使う、(b) `os.cpu_count()` / `os.sched_getaffinity(0)` を使う、(c) `os.environ` から読む —
  のいずれの変異も **KILL しない**。恒真ゲート型。→ worker 内で同時実行数の高水位を記録し、`=1` で高水位 1、`=N` で >1 を assert する。
- `test_waiver_does_not_widen_forward_correction_acceptance` (`:208`): R1 の反例を vector に含めない限り、
  `if waived: return []` を削る変異も現行設計の穴も KILL しない。含めれば**現行 plan 設計が落ちる** (それが正しい)。
- `test_waiver_count_is_reported_on_stdout_on_both_green_and_red` (`:210`): 免除対象 commit に実装面 path が無いと
  `if waived: return []` を削る変異が生き残る。「実装面 path + claude-only author + waiver で finding が消える」を必ず vector に入れる。

### R9 [real] `--message-file` の dispatch 免除を raw token 集合で実装すると commit が queue で詰まる

根拠: 手本の `tools/run_tests.py:111-114` と `:381-396` は raw token allowlist。checker の `argparse` は `allow_abbrev` 既定 True。
失敗シナリオ: `python3 tools/check_ai_provenance.py --message-f .git/COMMIT_EDITMSG` (argparse は一意接頭辞として受理) が
raw token 照合を外れ、**commit 直前の preflight が計算ノードへ qsub される**。queue 待ちは実測 6〜86 秒。commit 経路が queue に依存する。
修正案: 免除判定は `parse_args()` の**後**で `args.message_file is not None` に基づいて行い、raw token 集合を作らない。
手本の該当箇所を移植しないことを plan C-2(f) の「意図的に移植しない」リストへ追加する。

### R10 [real] rc=16 が task_run 台帳の `exit_status` に混入し、監査結果と infra 失敗が機械的に区別できなくなる

根拠: `tools/task_run_check.py:63,69` (rc 素通し) / `tools/task_runs/schema.py:440` は `exit_status` の意味論を持たない。
失敗シナリオ: 台帳に `suite_kind=provenance-check, exit_status=16` が並ぶ。消費側は非 0 を「検査違反」と読む。
docs の注記は**発火しない保証** = 恒真ゲート。
修正案: 最低限 D105 に「台帳の 16 は infra であり違反ではない — 機械判別はしない」を D103 決定 5 と同じ書きぶりで限界として明記する。

## 攻撃したが破れなかった点 (実測付き)

1. **`--stdin` の閉包性**: 実測 `echo HEAD | git rev-list --topo-order --parents --stdin | wc -l` = **948** = `git rev-list HEAD | wc -l`。
   `--stdin` は渡した rev の**祖先閉包**を返す。「`--ancestry-path` 集合の祖先が閉包外へ出て `index.get(parent)` が正常系で多発する」
   という想定は**成立しない**。None は shallow/graft のみで、本 repo は非 shallow。
2. **`--topo-order` の逆順走査で親が先に確定するか**: 実測で 948 行・**違反 0**。octopus merge **0 本**、root **1 本**。
   plan D-1 の構築順は本 repo で健全。
3. **pickaxe の tip 非依存性**: `-S` の採否は各 commit と親の diff で決まり `--full-history` が簡約を無効化する。
   tip 依存が生じうる経路は除外 rev (`^A`) を渡した時だけで、畳んだ呼出も per-commit 呼出も**正 rev のみ**。
   実測でもヒット 5 件に merge は 1 件も含まれない。`P ∩ ancestors(c)` の同値性は破れなかった。
4. **既存 CAB テスト 4 本への当たり**: `..._full_history_merge_that_keeps_or_drops_policy` は merge 自身が hit かに依らず
   **祖先の policy-side commit が hit** だから成立する形で、bitset でも同じ commit が乗る。`..._needle_count_changes_zero_two_one` は
   0→2 と 2→1 の両方が mask に入る。`..._rename_in_and_out` は `--no-renames` を argv で保持する限り同値。
   `..._separate_lineage` も同値。
5. **`test_cab_policy_git_error_fails_closed_with_rc2`**: intercept 条件は畳んだ argv でも満たされる。
   `_build_ancestry` がループ前に走るので RuntimeError の型・文言・rc=2 は保存される。
6. **`test_forward_correction_merge_base_rc128_fails_closed_with_rc2`**: epoch を両方 `None` に潰しているので残る
   `merge-base` は `:634` の 1 本だけ。plan の据え置きで赤にならない (静的検査のみ、**テストは実走していない**)。
7. **`validate_implementation_author` 単体の受理集合**: `waived` の挿入位置では (i) 実装面 path 0 件、(ii) AI-Agent 無し/`none`、
   (iii) codex author 有り の 3 経路すべてが waived を読まない。**この関数単体では受理集合は 1 bit も動かない**。破れたのは関数の外 (R1)。
8. **thread 安全性の追加走査**: index を書きうる `git diff --cached` は message-file 経路 (単一スレッド) にしかなく `index.lock` 競合は起きない。
   `_isolated_parsed_trailers` は呼出ごとに `TemporaryDirectory`。`re` の内部キャッシュ・`subprocess` の fd はスレッド安全。
   `Future.result()` は元例外型をそのまま再送出するので `main():787` の except 節は無改修で効く。
9. **counter を持つ既存テストの race**: `nonlocal parser_calls` は 3 箇所だけで、いずれも 1 commit range か message-file 経路。
10. **`test_check_wrapper_records_fixed_suite_kind_and_duration`**: `TC.subprocess.call` を monkeypatch しており実 checker を起動しない。
11. **`docs/decisions.md` に byte 予算は無い** (実サイズ 464 KB)。効くのは重複見出し検査だけ (現最大 D104)。
12. **waiver 本文と 2 つの needle の衝突**: 実測で `docs/ai-provenance.md` 内の count は各 **1**。plan の waiver 本文はどちらの完全一致文字列も含まない。

## nit / backlog

- **[nit → brief の誤前提]** brief `:31-32` の「両 needle の repo 内出現回数を既存テストが固定」は誤り。同テストは
  **CAB needle だけ**、しかも `docs/ai-provenance.md` 内の count のみ。`IMPLEMENTATION_POLICY_NEEDLE` の exactly-once を
  固定するテストは存在しない。さらに「repo 内出現回数」は `s2-plan.md` 自身が実装 needle を含むため insight を commit した時点で既に増える。
  不変条件は「`docs/ai-provenance.md` 内の各 needle の count を 1 に保つ」へ書き直すべき。
- **[nit]** commit 数: 既定 range の**監査対象は 609 commit** (実測)。948 は `ancestors(HEAD)` = bitset の次元。
  plan のメモリ見積り (948×948 bit ≈ 112 KB) は正しいが、argv 長の対象は 609 (25 KB)。insight の 596 → 609 (+2%)。
- **[nit]** 空 `commits` で `_build_ancestry` を通すと tips が空になり pickaxe が **rev 無し = HEAD 既定**で全履歴を走る。
  mask は index が空なので 0 で無害だが、commit の無い repo では rc=128 → RuntimeError → **rc=2** となり現行の rc=0 と食い違う。
- **[nit]** 逐次実装は最初の例外で以降を処理しないが `pool.map` は全 task を eager 投入するので**例外後も残り全 commit が実行される**。
  findings の同一性は保たれるが、git 障害時の subprocess 発行数が 3 本から約 2000 本へ増える。
- **[nit]** hook 第二層の `_PROVENANCE_EXEMPT_FLAGS` を exact token 集合にすると `--message-file=path` と接頭辞省略形が拒否される。
  fail-closed 方向なので害は小さいが C-0 の「綴り差だけを閉じる」主張とはずれる。
- **[backlog]** dev-wave supervisor の `provenance` check が queue 依存になる。平均は改善だが**分散が非有界**。

## 総括

攻撃の主目標だった **D の bitset 等価性は破れなかった** — `--stdin` の閉包性、`--topo-order` 逆順の親先行 (948 行・違反 0)、
octopus 不在、pickaxe の tip 非依存性を実測とコード読解で確認し、既存 CAB テスト 4 本と intercept テスト 2 本のいずれも
bitset 版を通すと判断した (テストは実走していない — 静的検査のみ)。plan の D は技術的に最も堅い部分である。

破れたのは **W (waiver) と受入設計**である。最大は R1: waiver は `validate_implementation_author` 単体では受理集合を
1 bit も動かさないが、`_audit_history:663` の `not correction.normal_findings` を経由して**前方訂正の受理集合を確かに広げる**。
plan の「waiver を参照させないから広がらない」は参照の有無と因果を取り違えており、brief の不変条件を破る。

次に R3: waiver 本文は実測 459 bytes、必要削減は 212 bytes、指定 2 項目で得られるのは 156 bytes で **56 bytes 不足**。
W は wave の gating commit なので、これが赤だと A/C/D が 1 本も land しない。

受入側も 2 つ壊れている。R5 (`REPO` が job tmp を指すので baseline が別 repo を監査する) と
R6 (waiver を入れた wave で「baseline と完全一致」は定義上不可能、range を切って回避すると恒真化)。
R4 の 4.58 秒も 48 並列の値であり 16 固定では出ない。

段 4 で最低限求めるもの: (1) R1 の反例を含む test vector と、それを通す設計変更、(2) `wc -c` で検証済みの逐語 diff、
(3) 「完全一致」を D 限定へ縮めた受入手順、(4) R8 の 3 テストを実際に KILL する形へ書き直すこと。
