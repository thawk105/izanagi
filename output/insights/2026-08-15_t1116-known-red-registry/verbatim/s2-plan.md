## 総括

- **P1 は現 scope では成立しない。実装は段 4 で NO-GO 裁定へ返すべきである。**
- (a)〜(e) は任意追加を難しくするが、AI が作った entry を人間が批准した事実までは証明しない。
- `refs/remotes/origin/main` の到達可能性はローカルで検査できるが、remote-tracking ref 自体がローカルで変更可能なので trust root にはならない。
- 現在は `main` が `origin/main` より 92 commit 先行しており、実用上も push まで全 entry が無効になる。
- 真の最小要件は、ユーザーだけが保持する鍵による entry 単位の署名、または同等の外部承認 attestation である。現 repo に鍵・署名 verifier はない。
- ユーザーが「origin に公開された registry blob 全体を批准と定義する」と明示裁定する場合に限り、以下の条件付きプランは実装可能である。
- checker receipt は `v1→v2`、受入 receipt は `v3→v4` とし、新 status `ratified-known-red-only` を使う。
- registry 不在時の受理集合・rc・分類は不変だが、schema bump により receipt bytes 自体は同一ではない。
- read-only 指示に従い pytest は実行していない。

## P1 の評価

| 案 | 判定 | 理由 |
|---|---|---|
| (a) `tested_main` に存在 | 必須だが不足 | 同じ wave が自分を救済することは防ぐ。一方、AI が registry 追加 wave を land させ、次 wave から効かせることは防げない。 |
| (b) `expires_on` | 必須だが不足 | `9999-12-31` を許せば実質恒久。`ratified_on` と最大有効期間も必要。 |
| (c) hard cap 5 | 妥当 | 肥大を有限化する。期限切れ entry も件数へ含めるべき。批准そのものの証明にはならない。 |
| (d) D/worklog 参照 | 監査情報として有用、authority として不足 | Markdown の存在確認は可能だが、D371 が指摘する通り、その文面を書くのも AI である。 |
| (e) `_PINNED_GUARD_PATHS` | 補助のみ | [check_codex_hooks.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_codex_hooks.py:296) は working bytes と HEAD blob の一致を検査する。書込み拒否リストではない。[guard_write.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/hooks/guard_write.py:154) が直接保護するのは `hooks/` 等で、registry path は対象外である。 |

`refs/remotes/origin/main` は次の検査なら実装できる。

- registry の `tested_main` blob SHA を求める。
- `refs/remotes/origin/main:<registry-path>` の blob SHA と完全一致させる。
- D/worklog 参照も同 remote tree に実在させる。

しかし、これは「公開済み registry snapshot」を示すだけである。

- `refs/remotes/origin/main` はローカル ref であり、`git update-ref` 等による変更を暗号学的に区別できない。
- 一度の batch push が全 entry の一括承認になる。
- 現在の ref は `a2cb460d...`、main は `330f67d0...` で 92 commit 先行している。
- 現行 commit に署名はなく、対象 source 内に `verify-tag`、`verify-commit`、SSH allowed-signers 等の trust root は 0 件だった。

したがって「批准済み」を文字どおり成立させる最小追加は、ユーザー管理秘密鍵で canonical entry を署名し、repo 外で既知の公開鍵または fingerprint により検証することである。鍵 bootstrap を現在の AI-authored commit に同梱すると循環するため、ユーザーによる鍵提供・初期 pin が別途必要になる。

段 4 の選択肢は次の三つになる。

1. 推奨: 署名 attestation を scope に追加して rebrief する。
2. 弱い代替: 「origin に公開された exact registry blob」を批准と定義する、とユーザーが明示裁定する。
3. registry 実装を中止する。

以下は 2 を採った場合の条件付き実装プランである。

## 条件付き registry schema

新規 [acceptance_red_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/acceptance_red_registry.json:1):

```json
{
  "schema_version": "izanagi-acceptance-red-registry/v1",
  "entries": []
}
```

非空時の entry は次の exact shape とする。

```json
{
  "nodeid": "orchestrator/tests/test_x.py::test_x",
  "ratified_on": "2026-08-15",
  "expires_on": "2026-09-14",
  "ratification": {
    "decision_id": "DNNN",
    "worklog_entry": 561
  }
}
```

規則:

- root 必須 field: `schema_version: string`、`entries: array`。任意 field は 0。
- entry 必須 field: `nodeid: string`、`ratified_on: string`、`expires_on: string`、`ratification: object`。任意 field は 0。
- `ratification` 必須 field: `decision_id: string`、`worklog_entry: integer`。任意 field は 0。
- entry 数は 0〜5。期限切れも cap に数える。
- `nodeid` は非空、NFC、制御文字なし、repository-relative `.py` path と `::` selector を持つ。照合は辞書の完全一致だけで、glob/prefix/regex API は作らない。
- entry は `nodeid` 昇順、重複なし。
- 日付は canonical `YYYY-MM-DD`。`ratified_on <= expires_on`、有効期間は最大 30 日。
- UTC の `checked_on` に対し `ratified_on <= checked_on <= expires_on` の日だけ active。期限切れは valid-but-inactive とし、救済しない。
- `decision_id` は `D[1-9][0-9]*`、`worklog_entry` は bool でない正整数。双方が `tested_main` と公開 snapshot に一意に実在することを検査する。
- JSON duplicate key、未知 field、非 canonical field 順、非 canonical JSON bytes、64 KiB 超過は拒否する。

fail-closed 境界:

- Git tree に registry path が**存在しない場合だけ**空 registry とする。
- path が存在するのに blob でない、mode 不正、読取失敗、oversize、schema 不正、参照不在、公開 blob 不一致なら `InvalidInput` とし checker rc=2。
- 不正 registry を空集合へ変換してはならない。
- `git ls-tree -z` の rc=0かつ空出力を「不存在」とし、Git command 自体の失敗と区別する。

## 分類と status

| rerun | active exact entry | classification |
|---|---:|---|
| `rerun_rc == 1` | 任意 | `non-attributable` |
| `rerun_rc == 0` | あり | `ratified-known-red` |
| `rerun_rc == 0` | なし | `attributable` |

status は次の優先順位で決める。

1. nodeid なし: `green`, rc=0
2. attributable が 1 件以上: `attributable-red`, rc=1
3. ratified が 1 件以上: `ratified-known-red-only`, rc=0
4. それ以外: `non-attributable-only`, rc=0

これにより I1 と I5 を保ち、既存 status の意味も拡張しない。ratified と non-attributable の混在は `ratified-known-red-only` とする。

## receipt schema 差分

### Checker receipt

`izanagi-acceptance-red-check/v1` から `v2` へ上げる。root exact field 集合は従来 9 fieldに `registry` を加える。

```text
collections, log_path, log_sha256, nodes, registry,
schema_version, status, submodules, tested_main, wave_tip
```

`registry` の exact field:

```text
blob_sha, checked_on, entries_used, loader_blob_sha, origin_main
```

- `blob_sha`: tested_main registry blob SHA。path 不在なら `null`。
- `checked_on`: expiry 判定に用いた UTC 日。
- `entries_used`: `ratified-known-red` に分類した nodeid の昇順・重複なし配列。
- `loader_blob_sha`: `tested_tip:tools/acceptance_red_registry.py` の blob SHA。
- `origin_main`: weak P1 を採る場合に検証した remote snapshot SHA。救済 0 件なら `null`。

`nodes` の field 集合は変えず、classification enum に `ratified-known-red` を追加する。consumer は classification と `rerun_rc` の組も検査し、`entries_used` が ratified nodeid 集合と完全一致することを要求する。

### 受入 receipt

`dev-wave-acceptance-receipt/v3` から `v4` へ上げ、root exact field 集合へ次を追加する。

```text
ratified_nodeids
red_registry_blob_sha
red_registry_loader_blob_sha
red_registry_origin_main
```

- `red_nodeids` は従来どおり `non-attributable` だけを保持する。
- `ratified_nodeids` は ratified だけを保持する。
- 両配列は昇順・重複なし・互いに素。
- `child-green`: 両配列空、3 SHA field は `null`。
- `non-attributable-only`: `red_nodeids` 非空、`ratified_nodeids` 空。
- `ratified-known-red-only`: `ratified_nodeids` 非空、`red_nodeids` は空でも非空でもよい。
- red verdict では loader blob を `tested_tip` に、registry blob を `tested_main` に、origin snapshot 上の registry blobを同じ SHA に束縛する。

checker receipt hashだけでは land が中間 receipt の内容を読めないため、loader・registry・origin の identity は受入 receiptにも投影する。親案の `ratified_nodeids` だけでは executable dependency の pin が閉じない。

## file:line 実装プラン

1. 新規 `tools/acceptance_red_registry.py:1`

   追加する主な型・関数:

   ```python
   class AcceptanceRedRegistryError(RuntimeError): ...

   @dataclass(frozen=True)
   class KnownRedEntry:
       nodeid: str
       ratified_on: date
       expires_on: date
       decision_id: str
       worklog_entry: int

   @dataclass(frozen=True)
   class AcceptanceRedRegistry:
       entries: tuple[KnownRedEntry, ...]
       active_entries: tuple[KnownRedEntry, ...]

   def load_acceptance_red_registry(
       raw: bytes, *, checked_on: date
   ) -> AcceptanceRedRegistry: ...
   ```

   duplicate key 拒否、64 KiB、exact field、canonical bytes、5件 cap、日付、重複・整列を一元化する。filesystem は読まず Git blob bytes だけを受ける。

2. 新規 `tools/acceptance_red_registry.json:1`

   上記 v1 schema の空 registry を置く。本 wave では entry 0 件。

3. [check_acceptance_reds.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:22)

   `_SCHEMA_VERSION = "izanagi-acceptance-red-check/v2"` へ更新する。

4. [check_acceptance_reds.py:1160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:1160) の直前

   ```python
   @dataclass(frozen=True)
   class _RegistrySnapshot: ...

   def _load_tested_main_registry(
       repo: Path,
       tested_main: str,
       *,
       checked_on: date,
       command_runner: CommandRunner,
   ) -> _RegistrySnapshot: ...

   def _verify_ratification_references(
       repo: Path,
       tested_main: str,
       registry: AcceptanceRedRegistry,
       *,
       command_runner: CommandRunner,
   ) -> None: ...
   ```

   `ls-tree → cat-file -s → cat-file blob` で tested_main からだけ読む。weak P1 採用時は origin snapshot の registry blob 完全一致もここで検査する。

5. [check_acceptance_reds.py:1160-1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:1160)

   `_probe_nodes` に `registry: AcceptanceRedRegistry` を追加し、return tuple に `ratified` を追加する。

6. [check_acceptance_reds.py:1257-1258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:1257)

   `rerun_rc == 0` のときだけ exact active lookup を行い、ratified または attributable へ分ける。`rerun_rc == 1` の経路は触らない。

7. [check_acceptance_reds.py:1395-1405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:1395)

   `check_acceptance_reds(..., checked_on: date | None = None)` を追加する。CLI flag は追加せず、production は UTC 当日、テストだけ注入する。

8. [check_acceptance_reds.py:1409-1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_acceptance_reds.py:1409)

   registry を一度だけロードし、三分類・新 status・checker v2 の `registry` 証拠を生成する。

9. [dev_wave_wait.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_wait.py:231)、[dev_wave_wait.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_wait.py:240)

   acceptance を v4、red-check を v2 へ更新する。

10. [dev_wave_wait.py:335-342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_wait.py:335)

    `_RedCheckResult` に `ratified_nodeids` と registry の3 identityを追加する。

11. [dev_wave_wait.py:2259-2324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_wait.py:2259)

    `_acceptance_receipt_bytes` に新 verdict の整合条件を追加し、v4 field を書く。

12. [dev_wave_wait.py:2439-2505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_wait.py:2439)

    `_verify_red_check_receipt` の root/nested exact field、status、classification、rerun rc、entries_used の完全一致を更新する。loader blob は tested_tip、registry blob は tested_main に独立照合する。

13. [dev_wave_wait.py:2838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_wait.py:2838)

    hard-coded `verdict = "non-attributable-only"` を `verdict = red_check.checker_status` へ変える。verifier が許す二 status 以外は到達不能にする。

14. [dev_wave_land.py:62-88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:62)

    schema を v4 に上げ、exact root field 集合へ4 fieldを追加する。

15. [dev_wave_land.py:520-640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:520)

    新 verdict branch、二 nodeid 集合の整列・重複・素性、checker/loader/registry/origin identity を検査する。checker blob 検査条件は両 red verdict の集合にする。

16. [dev_wave_land.py:134-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:134)、[dev_wave_land.py:218-222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:218)、[dev_wave_land.py:646-662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/dev_wave_land.py:646)

    `_AcceptanceVerification`、`LandResult`、`as_json()` に ratified nodeid を別 fieldで伝播させる。ここを外すと land 後の出力で区別が失われる。

17. [check_codex_hooks.py:33-47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_codex_hooks.py:33)

    loader と JSON を `_COPY_PATHS`、`_PINNED_GUARD_PATHS` に追加する。ただし「人間だけが書ける」とは記録しない。

18. `docs/spool/decisions/<T-1116-fragment>.md:1`

    P1 の最終ユーザー裁定を記録し、D371 の「registry を作らない」と D389 の却下案を明示的に部分 supersede する。P1未裁定のまま作成しない。

19. `docs/spool/worklog/<T-1116-fragment>.md:1`

    実際に採った authority、schema、変異・実測結果だけを段 7 で記録する。

## consumer 閉包

実コード上の wire schema は2種で、producer/consumer pin が各1本ずつある。第三の schema は新設 registry JSONであり、receipt ではない。

| schema | producer | consumer / pin |
|---|---|---|
| checker receipt | `check_acceptance_reds.py:22,1452-1475` | `dev_wave_wait.py:240,2439-2505` |
| acceptance receipt | `dev_wave_wait.py:231,2300-2324` | `dev_wave_land.py:62,66-88,499,520-650` |
| registry JSON | 新 loader + tested_main blob | checker、wait の blob照合、land の受入 receipt照合 |

限定 grep の結果:

- checker schema literal の追加 production consumer: **0件**。
- acceptance schema literal の追加 production consumer: **0件**。
- checker path の実行・pin は `dev_wave_wait.py:2415,2493-2499` と `dev_wave_land.py:620-641` のみ。
- 見落としやすい hard-coded consumer は `dev_wave_wait.py:2838` の1件。
- 見落としやすい downstream 投影は `dev_wave_land.py:134-160,218-222,646-662` の3範囲。
- テスト側 literal pin は `test_dev_wave_wait.py:505,931,1483,6731`、land helper は `test_dev_wave_land.py:237`。fixture 更新が必要。

## 追加テスト

既存の rc=0/1/2 一般契約や通常の非帰属判定は再テストしない。追加分は次の新しい検出力に限定する。

- `test_acceptance_red_registry.py::test_canonical_empty_registry_is_valid`  
  empty bootstrap を loader が誤って拒否したとき赤。

- `test_acceptance_red_registry.py::test_registry_negative_corpus_fails_closed`  
  duplicate key、未知 field、非 canonical bytes、日付不正、30日超、重複、未整列、6件目を受理したとき赤。

- `test_check_acceptance_reds.py::test_active_exact_registry_entry_reclassifies_rerun_green`  
  exact active entry があるのに ratified にならない、または `rerun_rc==1` まで ratified に変えたとき赤。

- `test_check_acceptance_reds.py::test_registry_is_read_from_tested_main_not_wave_tip`  
  wave tip だけに entry を足して自己救済できたとき赤。

- `test_check_acceptance_reds.py::test_missing_or_empty_registry_preserves_existing_classification`  
  bootstrap で受理集合・status・rcが変わったとき赤。

- `test_check_acceptance_reds.py::test_malformed_registry_fails_closed_before_probe`  
  不正 registry を空扱いした、または probe を走らせたとき赤。

- `test_check_acceptance_reds.py::test_expired_registry_entry_stays_attributable`  
  期限切れ entry が救済したとき赤。

- `test_check_acceptance_reds.py::test_registry_matching_is_exact_not_prefix`  
  path、prefix、glob風文字列で別 nodeid が救済されたとき赤。

- `test_check_acceptance_reds.py::test_nonempty_registry_requires_published_exact_blob`  
  weak P1 採用時、origin側が missing・古い・別 blobでも救済したとき赤。

- `test_dev_wave_wait.py::test_ratified_red_check_receipt_requires_exact_registry_evidence`  
  status、classification、rerun rc、entries_used、blob SHA の矛盾を通したとき赤。

- `test_dev_wave_wait.py::test_ratified_verdict_is_forwarded_to_acceptance_receipt`  
  `dev_wave_wait.py:2838` が再び literal 固定になったとき赤。

- `test_dev_wave_land.py::test_land_accepts_ratified_receipt_and_keeps_nodeids_separate`  
  正しい v4 を拒否した、または二集合を混同したとき赤。

- `test_dev_wave_land.py::test_land_rejects_each_ratified_receipt_inconsistency`  
  空 ratified、重複、未整列、集合重複、status不一致、loader/registry SHA不一致、未知 field を通したとき赤。

`test_codex_hooks.py:32-38` の期待 tuple は更新するが、既存 `test_pinned_guard_paths_are_exact_and_independent_of_copy_paths` が検出済みなので同型テストは増やさない。

## 事前登録変異

| 対象 | 1行変異 | 落ちるべき test node |
|---|---|---|
| `check_acceptance_reds.py:1409-1425` | registry revision を `tested_main` から `wave_tip` へ変更 | `test_check_acceptance_reds.py::test_registry_is_read_from_tested_main_not_wave_tip` |
| `acceptance_red_registry.py:80-120` 新規 expiry 判定 | `expires_on < checked_on` の inactive 化を削除 | `test_check_acceptance_reds.py::test_expired_registry_entry_stays_attributable` |
| `check_acceptance_reds.py:1160` 直前の新 loader wrapper | `except AcceptanceRedRegistryError: raise InvalidInput` を `return empty_snapshot` へ変更 | `test_check_acceptance_reds.py::test_malformed_registry_fails_closed_before_probe` |
| `check_acceptance_reds.py:1257-1258` | `logged_nodeid in active_nodeids` を `startswith` に変更 | `test_check_acceptance_reds.py::test_registry_matching_is_exact_not_prefix` |
| `dev_wave_wait.py:2479-2505` | `entries_used == ratified_nodeids` の検査を削除 | `test_dev_wave_wait.py::test_ratified_red_check_receipt_requires_exact_registry_evidence` |
| `dev_wave_land.py:582-602` 付近の新 branch | 空の `ratified_nodeids` を許可 | `test_dev_wave_land.py::test_land_rejects_each_ratified_receipt_inconsistency` |

## Bootstrap のコード経路

現時点で proposed loader/JSON path は worktree と `main` tree の双方に 0 件である。

1. checker は wave tip の filesystem ではなく `tested_main` を `git ls-tree` する。
2. 本 wave の `tested_main` には registry path がないため、正規の missing branchから empty snapshotになる。
3. `_probe_nodes` の active exact map は空。
4. `rerun_rc==0` は従来どおり attributable、`rerun_rc==1` は従来どおり non-attributable。
5. `green`、`attributable-red`、`non-attributable-only` の選択と rc は従来どおり。
6. 新 `ratified-known-red-only` へ到達する経路は存在しない。
7. land 後の次 waveでは tested_main に空 registry が現れるが、active entry 0件なので同じ結果になる。

したがって受理集合・分類・rcは同一である。一方、checker v2・受入 v4 と空 field追加により receipt bytes は変わる。「1 bitも変わらない」が bytes 同一を意味するなら P2 の版上げと両立せず、別裁定が必要である。

## 却下すべき設計

- `authority: user`、D番号、worklog番号の存在だけを批准証明と呼ぶ。
- `_PINNED_GUARD_PATHS` を書込み禁止機構と説明する。
- ローカル `refs/remotes/origin/main` 到達だけを、追加裁定なしに人間批准と扱う。
- registry を wave tipまたは working treeから読む。
- 不在と読取不能・schema不正を同じ empty fallback にする。
- glob、prefix、regex、path単位の登録を許す。
- `expires_on` だけを置き、最大有効期間を設けない。
- checker v1 / acceptance v3 を据え置いたまま field/status の意味を変える。
- `non-attributable-only` を ratified に流用する。
- checker scriptだけを pinし、新 loader の executable blobを proof chainから外す。
- compatibility のため v1/v2、v3/v4を曖昧に同時受理する。
- CLI flag、環境変数、`--force` で registry検査を飛ばせるようにする。