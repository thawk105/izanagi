## 総括

NO-GO — (P3) は成立するが、(P2) は累積有意水準のリセットを許し、(P4) の「gate 完成」は未定義の series / intent authority と未実装の A 級制約を完成扱いしている。

## 1. (P3) の成否

(P3) の「`cmake_cache` を拒否専用にする」部分は成立する。

根拠は `materials/record-items-v2-s0-s3.md:84-85` の次の規定である。

> producer が申告した派生値は、受理集合を狭める方向にだけ使う。  
> 不一致を拒否理由にし、一致は受理の正の根拠にしない。

したがって §8 の「受理条件の入力に使わない」は、申告値が不十分な raw evidence を合格へ救済してはならない、という意味に固定できる。形式化すると次になる。

```text
R(raw)       = configure argv / correctness argv と compile_commands 実体だけから再計算した raw 合格
C(raw, d)    = 申告 cmake_cache d が raw 再計算値と一致
V(raw, d)    = R(raw) AND C(raw, d)

必須性質:
  V(raw, d) -> R(raw)              # 申告値は raw 不合格を救済しない
  exists raw,d: R AND C AND V      # 正例があり、恒真 deny でない
  exists raw,d: R AND NOT C AND NOT V
                                      # 申告値は拒否方向には実際に効く
```

実装予定箇所は次の形にする。

- `orchestrator/preregistration/receipt_compile.py:20-55` 新規: `RecomputedCompileMode` と raw parser。
- 同 `:57-115`: `_derive_compile_mode_from_raw(*, argv, compile_commands_bytes) -> RecomputedCompileMode`。申告値を引数に取らない。
- 同 `:117-135`: `_reject_declared_compile_mode_mismatch(*, recomputed, declared) -> None`。返り値を受理判定へ渡さない。
- 同 `:137-175`: `verify_compile_evidence(...) -> RecomputedCompileMode`。raw 再計算を先に完了し、その後で申告不一致を拒否する。
- 性能側は schema の `configure_argv`、correctness 側は `argv` を読む。後者に `configure_argv` は存在しない (`receipt-schema-v1.json:94-171,805-825`)。

否定検査は次の三本を一組にする。

- `orchestrator/tests/test_t139_receipt_declared_inputs.py:20-45` 新規: raw 二脚が正しく申告も一致する正例が通る。
- 同 `:47-80`: 申告値を正しいまま保ち、`compile_commands` から必須 TU または macro を消す。`raw_compile_evidence_incomplete` で拒否させる。申告値を fallback または OR 条件として使う実装なら誤って通るため、恒真ではない。
- 同 `:82-110`: semantic helper を schema 前段から直接呼び、raw は有効だが申告だけ不一致の入力が `declared_compile_mode_mismatch` になることを確かめる。これで拒否専用の使用も実在する。
- mutation 条件として「raw 導出を `cmake_cache` からの導出へ置換」「`R AND C` を `R OR C` へ置換」の双方が二本目で kill されることを要求する。

`cmake_cache.trace` を 0 から 1 へ変えた receipt が落ちる、というテストだけでは不可である。schema 自体が性能側を 0、correctness 側を 1 に固定しているため (`receipt-schema-v1.json:54-70`)、semantic consumer を一度も検査せず成功する恒真テストになる。

なお、§6.3 は第 3 脚を「`cmake_cache` の申告値」と書く一方、§7.1(12) は略記で「CMakeCache」と書く (`materials/record-items-v2-s4-s10.md:469-477,642`)。canonical decision には「raw は二脚、申告値は拒否専用」と明記し、engine ごとの解釈分岐を閉じる必要がある。

## 2. (P1) の階級分け (§6.1〜§6.10 と §7.1 の全件)

基準は D205 の「測定・検証・台帳の正しさに直接効くものだけを採る」 (`materials/D205.md:3-8`) と、D320 の「正しさ gate、admission、変異検査は対象外で不変」 (`materials/D320.md:7-13,24-25`) である。

- §6.1 — A: attempt 欠落、dangling 参照、検証割当ての重複は標本集合と台帳の正しさを直接変える。
- §6.2 — A: planned と actual の双射、失敗 prefix、置換 slot は結果を見た後の補完・選別を防ぐ。
- §6.3 — A: trace と性能測定の分離および build 実体は絶対規律 1 と correctness を直接支える。
- §6.4 — A: 実 argv、待機、run log の照合は何を実測したかを決める。
- §6.5 — A: 観測窓と CPU busy の raw 再計算は環境適格性と測定の公正を決める。
- §6.6 — A: schedule のゼロからの再導出は結果依存の順序変更を防ぐ。
- §6.7 — A【親と不一致】: 全履歴性が `(family_root, ordinal)` の再利用と累積有意水準リセットを防ぐ機構そのものであり、byte provenance だけではない。
- §6.8 — A: pilot の exact 8 slot、main の J 件、予備 slot 非合算は標本数を直接決める。
- §6.9 — A: phase cap、deadline、単調時刻は失敗分類と適格 attempt の集合を変える。
- §6.10 — A【親と不一致】: 唯一 writer、pointer 実在、同一 snapshot は raw 証拠のすり替えや attempt 脱落を防ぎ、検証の正しさに直接効く。
- §7.1(1) — A: attempt 帰結に従属する correctness / liveness / telemetry 件数は証拠完全性そのもの。
- §7.1(2) — A: ordinal と predecessor の双方向条件は実行順序の正しさを決める。
- §7.1(3) — A: ID、erratum、binary rehash、dependency pin の一意性は参照先の曖昧化を防ぐ。
- §7.1(4) — A: a07 / a08 / a09 との一致は事前登録した測定条件を固定する。
- §7.1(5) — A: 36 × slot と schedule の一対一性は標本完全性を決める。
- §7.1(6) — A: allocation role 別 phase 閉包と cap は実行経路の適格性を決める。
- §7.1(7) — A: binary rehash の到達点と verification の 0 件条件は測定 binary の同一性を検証する。
- §7.1(8) — A: reason_code の再導出は失敗 attempt の隠蔽、置換、clean 偽装を防ぐ。
- §7.1(9) — A: attempt slot と allocation role の整合は性能 attempt と検証 attempt の混同を防ぐ。
- §7.1(10) — A: `/proc/stat` 実列と malformed reason の再計算は環境観測の正しさを決める。
- §7.1(11) — A: TU path、argv、base tree の再導出は測った source と build の同一性を決める。
- §7.1(12) — A: raw compile evidence と申告値の整合は trace / perf 分離を検証する。
- §7.1(13) — A: argv と run log map の exact 照合は計画した workload が実際に走ったことを検証する。
- §7.1(14) — A【親と不一致】: pointer、hash、同一 snapshot、symlink 拒否は raw 証拠の ABA・付け替えを防ぐ。
- §7.1(15) — A: monotonic ordering は待機、観測窓、run、marker の実順序を決める。
- §7.1(16) — A: intent と開始 marker の create-only 性は失敗投入の削除・後付けを防ぐ。
- §7.1(17) — A【親と不一致】: a13 の全履歴検査は累積有意水準リセットを直接防ぐ。
- §7.1(18) — A: 時間予算算術と cap は適格な割当て集合を直接決める。
- §7.1(19) — B【親と一致】: schema digest の manifest pin は schema bytes の provenance であり、validator が D282 固定 schema を直接読む限り科学的述語を追加しない。
- §7.1(20) — A: duplicate key を許すと parser ごとに別の attempt、時刻、理由を読むため、検証の意味が分岐する。

したがって B 級は §7.1(19) と conformance-vector index の digest pin に限られる。§6.7 と §6.10、ならびに対応する §7.1(14)(17) を B とした親分類は誤りである。特に単一 snapshot は D162 が独立の必須決定として置いている (`materials/D162.md:18-29`)。

## 3. (P2) が失うもの

(P2) は不成立である。現 tip と一つの祖先関係だけでは、次を検出できない。

- 過去の予約行を削除し、後の commit で同じ `(family_root, ordinal)` を再利用する。
- 台帳を一度 truncate して過去の予約または tombstone を落とし、現在だけ canonical に戻す。
- 古い行を編集・並べ替えた後、現在 tip で正しい一行へ復元する。
- ledger path を rename / copy / delete-and-recreate し、現在 path の導入だけを新しい初出として扱わせる。
- 一時的に重複 ordinal を作り、測定 head より前に片方を削除する。
- release / tombstone を一度追加し、後に消して現在 tip の `k = 1` だけを成立させる。
- noncanonical JSON、duplicate key、LF 不整合を過去世代だけに置き、現在世代で正規化する。
- resolver だけが履歴を見る一方、receipt validator または report が receipt の `reservation_commit` を信用する consumer 分岐を作る。

承認文書自身がこの攻撃を逐語で記録している。

- `materials/record-items-v2-s0-s3.md:65`: 前版の現 tip 検査は「過去行を削除して同じ `(family_root, ordinal)` を再利用した履歴を受理した」。
- `materials/record-items-v2-s4-s10.md:525-536`: 全世代走査、byte-prefix、全履歴一意性、初出再導出、各 consumer の独立再走を要求。
- `materials/D500.md:36-42`: 親系列 ID による累積有意水準リセットの kill には「族の根から測定 head までの全履歴 validator」が必要。

具体的な reset 経路は次である。

```text
H0: (F,1) を持つ台帳で series S1 を実行
H1: 台帳を削除、truncate、rename のいずれかで過去の使用を現在集合から外す
H2: (F,1) を再作成し、別 parent_series_id の S2 を申告
```

H2 の現 tip には一行しかなく、`k = 1` も成立し、初出 commit のどれかが measurement head の祖先であることも成立する。一方、H0 と H2 の間の削除・再導入を見ないので「同じ予約を二度使った」事実を失う。

さらに、現行契約には `series_id` / `parent_series_id` を alpha reservation から導出する写像がまだない。これは `materials/t139-v1-v5-package.md:209-217` が未解決事項として明記している。この写像を追加しない限り、全履歴を復活させても parent ID の自己申告変更を単独では kill できない。

## 4. gate 3 段の実装地図 (file:line)

以下は (P2) を撤回し、series / intent authority を先に canonical decision で固定した場合の実装地図である。新規ファイルの行番号は予定範囲である。

| 段 | 新規入口 | 実装と再利用 |
|---|---|---|
| 承認 manifest 解決 | `approval_manifest.py:35-210` `resolve_approval_manifest(repository_root, *, measurement_head) -> ApprovalManifest` | 最初に `approval_payload.py:166-171` の `load_approval_payload` を実行し、その後で manifest を読む。三つ組集合、erratum 順序、合成 digest、保証境界、`approval_fold_commit` を D282 と exact 比較する。blob 読取は `blobref.py:93-169`、追補閉包は `addendum_envelope.py:114-186`、合成は `erratum.py:661-709` を再利用。 |
| 祖先検査 | `git_history.py:30-175` `resolve_measurement_head(...) -> str` / `require_commit_ancestor(..., ancestor, descendant) -> None` | `measurement_head` は一度だけ実 checkout から導出する。`D234_FOLD_COMMIT = 88d68f9127b31df5aafc3d59607896626a1652e8` を literal にし、D234 (iii) と core / addendum の head 祖先性を別々に検査する。`trial_registry.py:817-892` は先例だが、巨大な S8c import graph と safe-history 差があるため直接 import せず、`blobref.py:172-410` の衛生化 Git 実行面を公開 helper へ抽出して再利用する。 |
| 受領証照合 | `receipt_validator.py:40-260` `verify_receipt(*, binding: PreregBinding, receipt: PathLike) -> None` | mapping を受けず、永続 path から読む。duplicate key 拒否、D282 固定 schema、binding の全三つ組と head、全 semantic 制約、attempt authority、alpha 全履歴を再計算する。T-126 の raw-path 起点構造は `qualification/collector.py:1439-1515`、stable read は `qualification/artifacts.py:77-112` を参照する。 |

予定 signature は次のとおり。

```python
def resolve_approval_manifest(
    repository_root: str | os.PathLike[str],
    *,
    measurement_head: str,
) -> ApprovalManifest: ...

def resolve_effective_preregistration(
    repository_root: str | os.PathLike[str],
    *,
    core_ref: BlobRef,
    addendum_a: BlobRef,
    addendum_b: BlobRef | None = None,
) -> PreregBinding: ...

def verify_alpha_reservation_history(
    repository_root: str | os.PathLike[str],
    *,
    family_root: str,
    measurement_head: str,
    ledger_path: str,
) -> AlphaReservationProof: ...

def verify_receipt(
    *,
    binding: PreregBinding,
    receipt: str | os.PathLike[str],
) -> None: ...

def publish_receipt(
    destination: str | os.PathLike[str],
    receipt: Mapping[str, object],
    *,
    binding: PreregBinding,
) -> Path: ...

def submit_pilot(*, binding: PreregBinding) -> str: ...
```

`PreregBinding` は `binding.py:35-105` の private seal 付き immutable class とし、caller が直接構築できないようにする。`binding.py:108-290` の resolver は次を順番どおり行う。

1. measurement HEAD を一度だけ導出。
2. D282 payload を読む。
3. approval manifest を解決して D282 と exact 比較。
4. caller の core / addendum ref が manifest の承認値と一致することを確認。
5. D234 fold → core commit、core / addendum / manifest commit → measurement HEAD の祖先性を確認。
6. a01〜a13 exact 閉包と二 erratum の合成 digest を再計算。
7. alpha 全履歴を独立走査。
8. private seal 付き binding を発行。

approval manifest の予定 path は `output/insights/2026-08-18_t338-submission-gate/approval-manifest-v1.json` とする。ただし exact key、固定 path、現在 HEAD の blob を採るか固定 commit の blob を採るかは acceptance authority に関わるため、実装前の canonical decision で固定しなければならない。

D264 の四名前 export は最終 integration commit だけで行う。

- それ以前の commit: 現行 `orchestrator/preregistration/__init__.py:1-28` と `test_t139_preregistration_binding.py:904-916` の非 export を維持。
- 最終 commit: `PreregBinding`、`resolve_effective_preregistration`、`submit_pilot`、`verify_receipt` の四つを同時に import / `__all__` へ追加し、同じ commit で negative export test を all-or-none test に置換。
- `submit_main` は今回 export しない。
- 正例 vector が成功させる対象は resolver と `verify_receipt` である。`submit_pilot` は全 gate 検査後に D292 の operational latch へ到達し、現在は qsub を行わず `SubmissionForbiddenError` になる。この「gate 合格」と「投入権限なし」の二段を canonical decision が明示しない場合、deny stub 禁止との区別がつかないため最終 export は行えない。

## 5. 再利用先の棚卸し (file:line)

| 候補 | 判定 | 根拠 |
|---|---|---|
| `qualification/attempt_ledger.py` | 設計の主土台として使うが、`SeriesAttemptLedger` は直接使わない | `:169-309` の hash-chain replay、`:312-373` の連番 create-only event は有用。一方 `:194-200,312-323,375-473` は `t126-only`、64 桁 T-126 series ID、一初回＋最大一 retry、`QualificationWriteCapability` に固定される。T-139 用 `preregistration/attempt_registry.py` へ state transition と exact-set replay を移植する。 |
| `qualification/series.py` | 使わない | `:66-240` は subject/reference 二者、SPRT bit 列、round FSM に固定され、`:243-378` も in-memory event list と T-126 schema を前提とする。T-139 の三 arm、13 slot、verification allocation、stage terminal receipt とは状態空間が違う。 |
| `campaign/s8b_holdout_admission.py` | O_EXCL / fsync の低位パターンだけ使い、module や台帳を直接使わない | `_write_exclusive` は `:681-703`、lock は `:340-435` にあり有用。しかし module 自身が `:2-11,2262-2274` で「現在状態だけ」「削除・再構成を検出しない」と明記する。shared root `:312-329` は Git common dir 外で、repo 相対 `fileRecord` 要件 (`record-items-v2-s0-s3.md:117-128`) とも直接は合わない。 |
| `qualification/identity.py` | 直接使わず、検証パターンだけ参照 | stable fd hash は `:82-109`、Git / toolchain 再導出は `:112-236` にあるが、T-126 script path、protocol、subject/reference、policy に固定される。T-139 identity は approval binding、`family_root`、stage、D496 の構成集合を含めて新規導出する必要がある。 |

結論として、attempt registry は次の混成にする。

- 意味層: `attempt_ledger.py:169-373` の replay / hash-chain / exact event index を T-139 用に適応。
- 永続化層: S8b `:681-703` の O_EXCL、全量 write、fsync のパターンを generic helper として新規実装。
- 読取層: `artifacts.py:77-112,541-629` の stable read、duplicate-key JSON / JSONL の考え方を再利用。
- identity 層: caller の `series_id` を信用せず、binding と固定構成集合から導出する。

ただし canonical registry root、`series_id` / `parent_series_id` の導出、intent discovery の閉集合は未裁定である。これらを決めず、receipt に列挙された `intent_ref` だけを見ると、receipt と intent の双方から失敗 attempt を落とす攻撃を検出できない。§6.1 の exact coverage は実装不能である。

## 6. 規模の独立再見積り

既存コードを静的に測った基準は次である。

- `approval_payload.py`: 587 行、raise 41。
- `blobref.py`: 410 行、raise 51。
- `qualification/collector.py`: 1,883 行、raise 122。
- `qualification/attempt_ledger.py`: 473 行、raise 39。
- `qualification/series.py`: 378 行、raise 24。
- `qualification/identity.py`: 236 行、raise 26。

この密度からの production 行数は次になる。tests、fixtures、manifest JSON、decision / worklog は含めない。

| 層 | 見積り |
|---|---:|
| manifest parser、binding、D234 祖先検査 | 500〜700 |
| stable receipt IO、schema、pointer 読取 | 260〜400 |
| §6 / §7.1 の A 級 semantic validator と P3 | 1,050〜1,500 |
| §6.7 全履歴 validator | 260〜380 |
| attempt registry discovery と series identity | 320〜480 |
| writer、gate 入口、export / policy latch | 180〜280 |
| 合計 | **2,570〜3,740** |

親の P2 をそのまま採り、alpha を現 tip だけにし、未定義の attempt authority も実装しない「完成していない版」でも約 **2,070〜3,020 行**である。

したがって親の 1,200〜2,700 行は、下限では約 870 行、完成版の上限では約 1,040 行少ない。差の主因は、親が §6.7 / §6.10 / §7.1(14)(17) を B 級へ落としたことと、§6.1 を成立させる attempt discovery / series authority を計上していないことである。

実施したのは `rg`、`nl`、`wc`、AST による静的行数・分岐数確認だけである。pytest、build、`tools/run_tests.py` は実走しておらず、緑とは判定していない。

## 7. 段 5 の分割

親の A / B / C 三分割では C の vectors が A の binding と B の validator に依存するため、A/C 並列は成立しない。次の六単位なら編集 path は素集合になる。

1. Manifest / binding / Git 基盤

   所有 path:

   - `orchestrator/preregistration/approval_manifest.py`
   - `orchestrator/preregistration/git_history.py`
   - `orchestrator/preregistration/binding.py`
   - `orchestrator/preregistration/blobref.py`
   - `orchestrator/tests/test_t139_approval_manifest.py`
   - `orchestrator/tests/test_t139_preregistration_resolver.py`
   - `orchestrator/tests/test_t139_approval_payload.py`
   - `output/insights/2026-08-18_t338-submission-gate/approval-manifest-v1.json`

2. Receipt IO / schema

   所有 path:

   - `orchestrator/preregistration/receipt_io.py`
   - `orchestrator/preregistration/receipt_schema.py`
   - `orchestrator/tests/test_t139_receipt_io.py`
   - `orchestrator/tests/test_t139_receipt_schema.py`

3. Semantic validator / P3

   所有 path:

   - `orchestrator/preregistration/receipt_compile.py`
   - `orchestrator/preregistration/receipt_semantics.py`
   - `orchestrator/preregistration/receipt_validator.py`
   - `orchestrator/tests/test_t139_receipt_semantics.py`
   - `orchestrator/tests/test_t139_receipt_declared_inputs.py`

4. Alpha history / attempt authority

   所有 path:

   - `orchestrator/preregistration/alpha_history.py`
   - `orchestrator/preregistration/attempt_registry.py`
   - `orchestrator/tests/test_t139_alpha_history.py`
   - `orchestrator/tests/test_t139_attempt_registry.py`

5. Writer / conformance vectors

   所有 path:

   - `orchestrator/preregistration/receipt_writer.py`
   - `orchestrator/tests/t139_receipt_vectors.py`
   - `orchestrator/tests/test_t139_receipt_conformance.py`
   - `orchestrator/tests/test_t139_receipt_writer.py`

6. Integration / D264 export

   所有 path:

   - `orchestrator/preregistration/gate.py`
   - `orchestrator/preregistration/__init__.py`
   - `orchestrator/tests/test_t139_gate_integration.py`
   - `orchestrator/tests/test_t139_preregistration_binding.py`

依存順は `1 || 2`、次に `3` と `4`、その後 `5`、最後に `6` である。四名前 export は単位 6 の最終 commit だけで行う。canonical decision、worklog、phase doc は親専有とし、実装単位へ混ぜない。

## 8. 親 brief の誤り (あれば。無ければ「なし」と書く)

1. `(P2)` は不成立。承認文書が現 tip 検査による同じ予約の再利用を既知の穴として明記している (`record-items-v2-s0-s3.md:65`)。

2. `(P1)` は §6.7 と §6.10 を誤分類している。前者は alpha reset、後者は raw evidence と attempt 完全性に直接効くため A 級である。

3. `(P4)` の「gate 完成」は不正確。§7 は §6 と §7.1 の全項目を semantic validator の必須責務とする (`record-items-v2-s4-s10.md:607-613,615-650`)。A 級を外して保証境界へ書くだけでは完成にならない。

4. brief `:12` の「Q2 は producer 段でないため非閂」は誤り。D500 は parent-series reset の kill を全履歴 validator の責務とする (`materials/D500.md:36-42`)。本 wave はその validator を完成させる wave なので直接の受入条件である。

5. `series_id` authority、intent / receipt discovery、単一 binding への入力写像が未解決のままである (`t139-v1-v5-package.md:209-217`)。この状態では §6.1 の「全 durable intent の exact 被覆」を実装できない。

6. `(P3)` の結論自体は成立するが、否定検査が未設計である。schema enum を反転するだけの検査は schema 前段で落ちる恒真検査になる。また correctness 側の field は `configure_argv` ではなく `argv` である。

7. manifest の exact grammar、固定 path、発見方法が未定義である。D282 は照合する意味集合を定めるが、新 manifest 自体の exact object schema は定めていない。

8. `submit_pilot` の扱いが未定義である。qsub まで到達する正例は D292 違反、一行 deny は D264 違反になる。三段 gate 合格後の operational deny を恒真 stub と区別する規定が必要である。

9. 段 5 の A/C 並列案は依存関係を逆に見ている。vectors は resolver、binding、semantic validator の確定後でなければ期待理由や正例を固定できない。

10. 1,200〜2,700 行の見積りは、attempt authority と科学的に必要な全履歴層を計上しておらず過小である。