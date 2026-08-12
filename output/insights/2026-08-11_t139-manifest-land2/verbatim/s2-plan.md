## 総括

**NO-GO** — 現行 brief のまま段 5 へ進めることには反対する。scope 1 単独と scope 2 の #1、#2 の実行防壁までは設計可能だが、次が blocker である。

1. **§S7 #3 の実 consumer が本 session の scope にない。** TOCTOU 対象は `a03` raw、run log、intent、correctness evidence などの `fileRecord` だが、それを読む semantic validator は明示的に後続 session へ送られている。[record-items-v2.md:719–726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:719) 未使用の安全読取 API を追加しても #3 を閉じたことにはならない。
2. **(P2) の「Git digest を受領証へ記録する」field が承認済み schema に存在しない。** top-level と `preregistration` は閉じており、`toolchain.compiler_sha256` は compiler identity であって Git ではない。[receipt-schema-v1.json:194–208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:194) [receipt-schema-v1.json:257–289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:257) `PreregBinding` 内部への保持は可能だが、正式受領証への記録は設計メモ止まりにする必要がある。
3. **(P1) の B lane は所有ファイルと量が不足している。** 完全な #2 には `blobref.py`、D264 の説明整合には `__init__.py` も必要で、B 合計は約 2,000 行に達する。さらに現行 `compose_core` は内部で Git 読取を行うため、A から pure-bytes 合成 API を受け取るまでは resolver の統合を完了できない。

これは `dev-wave` の `DW-O13` に従って、gate の入力と実 callsite の実在を先に確認した結果である。

### 承認値の照合結果

| 項目 | 現 test | D282 / v2 | 結果 |
|---|---|---|---|
| `EXPECTED_TWO_ERRATA_COMPOSED_SHA256` | `dfb821a5…678c` | `e0b0caea…8e0c` | **不一致**。現値は未承認 1-operation 草案の値 |
| `EXPECTED_S7_OPERATION_LINE_SHA256` | `225268a9…8e89` の単一 `str` | `(225268a9…8e89, a7852ad9…9952)` | 第 1 operation だけ一致、第 2 が欠落 |
| `_S7_NEW_TEXT_SHA256` | `92fd7175…01a4` | `(92fd7175…01a4, b8741cc9…b37fe)` | 第 1 replacement だけ一致 |

実 core の 221・333 行をそれぞれ静的に hash し、上記 2 digest と一致することも確認した。承認 v2 artifact 自体の SHA-256 は `deedd71b…4df2` で D282 と一致する。[test_t139_preregistration_binding.py:71–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:71) [D282:12919–12925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12919)

なお brief は「6 blob」と書きながら 7 個を列挙している。[s1-brief.md:30–31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s1-brief.md:30) 実装上の正本は D282 の **target core 1 + approved blob 6 = 7 三つ組**とする。

## file:line 実装プラン

新規 file は現在存在しないため、以下の `new:Lx–Ly` は予定レイアウトであり、既存行を装った引用ではない。既存 file の行番号はすべて実読済みである。

### Scope 1 — erratum v2

1. [erratum.py:20–39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:20)

   - 出現 token を 1 行専用の `_S7_OLD_TEXT` から `較正` へ変更する。
   - 221/333 行の locator、old digest、new digest を index 別の固定表にする。
   - `ApprovedErratumId` を 2 ID の `Literal`、`DraftErratumId` を Python 3.10 で空型を表せる `NoReturn` alias にする。
   - `APPROVED_ERRATA` を 2 ID、`DRAFT_ERRATA: frozenset[DraftErratumId] = frozenset()` とする。`Literal[()]` は空集合型ではないので使わない。

2. [erratum.py:94–114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:94)、[erratum.py:202–329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:202)

   - `ErratumOperation` に `new_sha256: str | None`、`ErratumDocument` に `expected_composed_sha256: str | None` を追加する。
   - S15 旧形式との互換を保ちつつ、S7 v2 だけは top-level key を exact `{operations, expected_composed_sha256}`、operation key を exact 6、locator key を exact 3 にする。
   - duplicate、未知 key、欠落 key、重複 index を parse 段階で拒否する。

3. [erratum.py:397–448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:397)

   `_validate_t139_core_s7_stresscheck_v1` を v2 の検査 1〜12へ置換する。

   - operation 数 2、index 集合 `{1,2}`。
   - locator と old/new digest の index 別固定値一致。
   - core の `較正` が exact 2 件で、対象行が exact `{221,333}`。
   - old/new が各 1 行、old bytes が core と一致。
   - new bytes と `new_sha256` が一致し、適用後 `較正` が 0 件。
   - index 2 の表行が `| a12 |` で始まり、列数不変。
   - S15/S7 全 locator の非重複は既存共通検査を維持する。

4. [erratum.py:477–509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:477)

   - 最終合成値を caller 値だけでなく S7 文書内の `expected_composed_sha256` とも照合する。
   - B lane が同じ trusted Git fd で全 blob を先に読めるよう、`compose_core_from_blobs(core_blob, erratum_blobs, *, expected_composed_sha256)` を追加する。
   - 既存 `compose_core` は互換 wrapper とし、この pure API を呼ぶ。

5. [test_t139_preregistration_binding.py:42–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:42)

   - `DRAFT_ERRATUM_*` を承認済み path、commit `d0e76451…78d9`、SHA `deedd71b…4df2` の `S7_ERRATUM_*` へ改名・差替え。
   - composed 値を `e0b0…8e0c`、target-line/new-line digest を 2 要素 tuple にする。

6. [test_t139_preregistration_binding.py:401–567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:401)、[同:801–863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:801)

   - 1/3 operation、index 欠落・重複、333 行欠落、locator swap、各 new digest 改変、未知/duplicate key、表形状改変、文書内 composed digest 改変を負例にする。
   - real ref 2 枚を monkeypatch なしで読み、locator `{404,424}` と `{221,333}`、合成 `e0b0…8e0c` を検査する。
   - registry は approved exact 2、draft empty を固定する。

### Scope 2 — manifest / resolver

1. [blobref.py:21–31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:21)、[blobref.py:138–192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:138)

   - ambient `PATH` を allowlist から除く。
   - `/usr/bin/git` を trust-rooted absolute path とする。repo 内先例も同じ固定 path を使う。[dev_wave_land.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/tools/dev_wave_land.py:54)
   - `O_NOFOLLOW|O_CLOEXEC` で開き、`fstat` で regular・所有者・group/other 非書込を確認。同じ fd から SHA-256 を計算する。
   - resolver の全処理中 fd を保持し、`/proc/self/fd/<n>` + `pass_fds=(n,)` で hash した inode 自体を実行する。`PATH` は固定 system path に置換する。
   - `GitRuntimeIdentity{resolved_path, sha256, size, st_dev, st_ino}` を内部 binding に保持する。

2. [blobref.py:89–135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:89)

   - public `read_pinned_blob` は trusted Git context を自前生成する互換 wrapper。
   - resolver 用に同じ context を再利用する内部 `_read_pinned_blob_with_runtime` を追加する。
   - worktree path は従来どおり開かない。`ls-tree` と `cat-file`、regular blob mode 検査 [blobref.py:235–262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:235) を維持する。

3. `orchestrator/preregistration/manifest.py`（新規予定）

   - `new:L1–L45`: `F_r`、decision kind、`docs/decisions.md` の pinned refを定義する。F_r 時点の同 file SHA-256 は静的算出で `ec588bb6…9cf`。
   - `new:L46–L150`: UTF-8/LF、fence 外の D282 heading exact 1、D282 節内で先頭行が指定 decision kind の `text` fence exact 1を抽出する。
   - `new:L151–L270`: payload の top-level/nested exact key grammar。見つからない、複数、欠落、未知、duplicate、indent 不正をすべて fail-closed。
   - `new:L271–L340`: duplicate-key 拒否付き manifest JSON parser。7 三つ組、erratum order、composed digest、旧 record pair、operational boundary を `ApprovalPayload` と exact 比較する。

4. `output/insights/2026-08-11_t139-manifest-land2/approval-manifest-v1.json`（新規予定）

   exact key は次だけとする。

   - `schema_version`
   - `decision_kind`
   - `approval_fold_commit`
   - `target_core`
   - `approved_blobs`
   - `erratum_application_order`
   - `composed_sha256`
   - `not_approved_as_record_items_root`
   - `operational_boundary`

5. `orchestrator/preregistration/resolver.py`（新規予定）

   - `new:L1–L75`: error 型、封印付き frozen `PreregBinding`。public constructor では生成できない形にする。
   - `new:L76–L145`: trusted Git context で `measurement_head` を exact 1 回導出し、shallow/replace/graft を拒否する。
   - `new:L146–L220`: `F_r` decisions → payload を先に読み、その後 manifest を読む。`F_r ≤ manifest commit ≤ measurement_head` を要求する。
   - `new:L221–L315`: caller の core/addendum claim を authority にせず、manifest/payload 由来 refs との一致だけを見る。全 7 blob を同じ Git runtime で解決し、旧 record を `record_items` role で明示拒否する。
   - `new:L316–L370`: addendum exact 13、A の pure-bytes compose、composed digest、operational boundary を照合後だけ binding を返す。
   - D234 の署名を保つため、API は `approval_manifest_ref` を追加しつつ `core_ref` / `addendum_a` / `addendum_b` を claim として比較する。[D234:11027–11053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:11027)

6. [__init__.py:1–28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/__init__.py:1)

   - docstring の「未実装」は「内部実装中だが gate 未完成のため package root 非公開」へ直す。
   - resolver/binding を import せず、`__all__` を一切増やさない。
   - 既存の `__all__` + `hasattr` 検査 [test_t139_preregistration_binding.py:865–876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:865) が D264 を機械保証し続ける。

### #3 の安全読取 API

`read_pinned_blob` は Git object を読むので、raw file の TOCTOU 修正先ではない。別の `orchestrator/preregistration/snapshot.py` を置くべきである。

予定 `new:L35–L130`:

1. repo-relative component を検証。
2. root と各親を `os.open(..., O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC, dir_fd=...)` で順に開く。
3. leaf を `O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC` で exact 1 回開く。
4. `os.fstat(fd)` で regular、size 上限と申告 size を検査。
5. `with os.fdopen(fd, "rb", closefd=True) as stream:` 内で bounded readし、同じ `bytes` に対して hash と parser callback を実行する。
6. read 前後の `(dev, ino, size, mtime_ns, ctime_ns)` を同じ fd で比較する。
7. `O_NOFOLLOW` 等が無い platform は fail-closed。

ただし本 session ではこの API を `fileRecord` consumer へ結線できない。したがって実装するなら「基礎 API 完成」であって、§S7 #3 完了とは記録しない。

## A. 分割の可否

親の列挙だけなら A/B の file intersection は空だが、B の所有面が不足している。

安全な再分割は次のとおり。

- **A:** `erratum.py`、既存 T139 test。pure-bytes compose API の署名を先に固定。
- **B0:** `blobref.py`、新 Git trust test。
- **B1:** `manifest.py`、approval manifest artifact、新 manifest test。
- **B2:** `resolver.py`、`__init__.py`、新 resolver test。A/B0/B1 統合後に着手。
- **B3:** `snapshot.py` と test。semantic validator と同じ session へ送る。

したがって「A/B の 2 本を最後まで完全並列、B は現 API 署名だけでよい」には反対する。A と B0/B1 は並列可能だが、B2 は A の新 pure-bytes API を待つ。

## B. 行数見積り

| 種別 | file | 見積り |
|---|---|---:|
| production | `erratum.py` | +140 |
| production | `blobref.py` | +130 |
| production | 新 `manifest.py` | 300–340 |
| production | 新 `resolver.py`（binding 込み） | 250–300 |
| production/data | 新 approval manifest JSON | 55–75 |
| production | `__init__.py` | +3 |
| production、条件付き | 新 `snapshot.py` | 120–150 |
| test | 既存 T139 test | +190–230 |
| test | 新 Git trust test | 170–220 |
| test | 新 manifest test | 300–380 |
| test | 新 resolver test | 350–450 |
| test、条件付き | 新 snapshot test | 160–210 |

合計は production 約 **900–1,140 行**、test 約 **1,010–1,490 行**。1 worker / 3600 秒で security-sensitive な全量を書くには大きすぎる。上記 A/B0/B1/B2 の刻みなら、各 worker はおおむね 300〜750 行に収まる。

## C. 既存被覆と純増検出力

| 性質 | 既存被覆 | 本 wave の純増 |
|---|---|---|
| #1 payload と manifest の exact 一致 | D282/F_r/decision kind を読む test は **0 件** | missing/multiple fence、未知/欠落 key、7 三つ組、順序、digest、boundary、旧 record role の各改変を直接 kill |
| #2 ambient `PATH` の偽 Gitを使わない | `GIT_DIR` / `GIT_WORK_TREE` 不継承は既存 [test:701–713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:701)。`PATH` は未被覆 | PATH 先頭の偽 `git` が一度も呼ばれず、hash 済み fd の実体だけを全 Git operation が使うことを検出 |
| #3 path を二度開かず同じ bytes を hash/parse | Git tree symlink mode 拒否 [test:691–698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:691) は raw path の性質ではない。他 module には fd 再利用 [test_check_codex_output.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_check_codex_output.py:111) や component walk [test_trial_registry.py:2381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_trial_registry.py:2381) の先例があるが T139 を守らない | leaf exact 1 open、parent/leaf swap、symlink、FIFO、read 中 mutationを snapshot API で検出。ただし consumer 結線なしでは helper の検出力だけ |

## D. gate 入力の実在

| 検査 | 実在 field | 判定 |
|---|---|---|
| D282 三つ組・order・digest・boundary | D282 payload に実在 [docs/decisions.md:12881–12939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12881) | 実装可 |
| manifest identity | 受領証の `preregistration.approval_manifest: blobRef` [schema:257–288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:257) | 実装可 |
| 旧 record の拒否 | D282 に path + sha256 が実在。commit は無い [docs/decisions.md:12927–12931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12927) | pair だけを比較し、存在しない commit を捏造しない |
| Git executable identity | 正式 receipt に専用 field なし | binding 内部だけ。receipt 記録は設計メモ |
| raw snapshot | `fileRecord={path,size,sha256}` と多数の pointer に実在 [schema:17–35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:17) | 入力は実在するが current scope に consumer がない |
| measurement head | checkout から resolver が導出。receipt 側は `measurement_checkout.repository_head` [record-items-v2.md:190–195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:190) | 実装可 |

D75 対策として、Git identity を `toolchain` や `dependency_pins` に流用しない。内部名は `GitRuntimeIdentity`、raw file は `FileSnapshotRef`、Git blob は既存 `BlobRef` と分ける。また D234 の `fold_commit` と D282 の `approval_fold_commit` を混同しない。

## E. 受理集合の変化

- **変更前に通り、変更後に落ちる入力:** v1 草案の S7 erratum。operation は 221 行の 1 件、合成期待値は `dfb821a5…678c`。現 validator は operation 数 1と対象 phrase 1件を満たすが、v2 validator では operation 数不足で拒否される。
- **変更前に落ち、変更後に通る入力:** D282 の承認 v2。221/333 行の 2 operation、new digest 2件、S15 と合成して `e0b0caea…8e0c`。現 validator は operation 数 2を即拒否するが、改訂後は通る。
- **membership:** `t139-core-s7-stresscheck-v1` は draft から approved へ移る。ただし v1/v2 は同じ ID なので、ID membership だけでは旧草案を除外できない。resolver の blob SHA `deedd71b…4df2` 照合が必須である。

## F. (P2)〜(P5) の評価

- **P2: 反対。** ambient PATH で絶対 path を解決して digest を記録するだけでは、偽 Git の digest を記録して終わる。受領証 digest は実行防壁でもない。代案は「trusted absolute path・same-fd hash/exec・PATH 非継承」。正式 receipt への記録は field が決まるまで保留する。
- **P3: primitive には賛成、現 scope の完了主張には反対。** `O_NOFOLLOW` leaf だけでなく component-wise dirfd walk、regular `fstat`、bounded single buffer、before/after fd metadata が必要。`read_pinned_blob` は Git object readerなので直さず、raw snapshot APIを別設する。ただし current resolver には対象 raw が来ない。
- **P4: 条件付き賛成。** secure Git を前提に、F_r payloadを先に parseし、manifest commit の ancestry、exact role set、旧 record 明示拒否まで行えば追加署名は不要。manifest だけを根にしてはならない。
- **P5: 賛成。** 複数 session と非 export は矛盾しない。package root の import と `__all__` を増やさず、既存機械検査を維持する。

テストは指示どおり一切実行していない。上記の数値確認は file 読取、Git blob の静的読取、SHA-256 照合だけである。