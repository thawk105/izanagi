## C-01 — 受理集合・拒否集合の同値

**severity:** blocker  
**自己判定:** refuted。plan の信頼境界である安定した repository/disk と信頼済み `/usr/bin/git` を前提に、受理・拒否集合が変わる経路は静的には見つからない。

旧実装は path ごとに `cat-file blob <commit>:<path>` を実行していた（[unitA.patch:222](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/unitA.patch:222)）。新実装は次をすべて拒否している。

- raw path の期待外・重複・不在、non-blob、OID 不正: [contract_loader_binding.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:393)
- batch header の OID 不一致、type、size、body/LF framing: [contract_loader_binding.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:456)
- 余剰出力: [contract_loader_binding.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:505)
- NUL path は Git 起動前に正規化拒否: [contract_loader_binding.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:356)

mode は意図どおり判定に使わず、type が blob なら 100755/120000 も committed では受理する。capture/live では従来どおり disk reader が実際の非 regular file を拒否する。

**修正案:** 実装修正なし。C-05 の未網羅 test を追加する。

## C-02 — generator の途中消費による fail-open

**severity:** blocker  
**自己判定:** refuted。全 batch record を `parsed` へ格納し、exact EOF を確認した後にだけ `yield from parsed` へ進む（[contract_loader_binding.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:456)、[contract_loader_binding.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:505)）。したがって最初の yield 時点で全 response は検査済みである。

queries は元の `relatives` 全件から作られ、各 query について必ず一つの parsed entry が作られる。capture/live/committed/blobs の clean path はいずれも iterator を完走する（同ファイル:518-594）。例外を握りつぶす `except` もない。

**修正案:** 不要。将来 streaming yield に変更する場合は、途中消費を明示的に攻撃する回帰 test を同時追加する。

## C-03 — spawn site、env、harden、timeout

**severity:** blocker  
**自己判定:** refuted。

`subprocess.run` は `_run_git` 内の一か所だけである（[contract_loader_binding.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:252)）。`input=input_bytes` の追加後も限定 env、`GIT_NO_REPLACE_OBJECTS`、固定 `/usr/bin/git`、harden argv、`--no-replace-objects` は同じ spawn に残っている（同ファイル:272-307、[unitA.patch:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/unitA.patch:26)）。

timeout は ls-tree が unique path 数、cat-file が重複込み query 数で倍率化される（同ファイル:371-453）。3 unique/4 query の差と、n=1/62 の変化も test が固定している（[test_t671_source_binding.py:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:825)、[test_t671_source_binding.py:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:1359)）。

**修正案:** 実装修正なし。

## C-04 — drift 検査と非対称性

**severity:** blocker  
**自己判定:** refuted。

- capture: disk==blob の後に digest を記録: [contract_loader_binding.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:518)
- live: digest 一致後に disk==blob: 同ファイル:535-555
- committed: digest のみで disk を読まない: 同ファイル:558-574
- blobs: 明示された tuple 順で digest: 同ファイル:577-594

clean capture/live の disk reader 全124回と、capture 単独62回が別々に記録される（[test_t671_source_binding.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:437)、[test_t671_source_binding.py:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:1537)）。

**修正案:** 不要。

## C-05 — ls-tree framing の test 防壁が不足

**severity:** should-fix  
**自己判定:** real。実装は正しいが、厳密 parser の一部が所有 test に固定されていない。

現 test は missing/unexpected/duplicate と tree/commit を検査するが（[test_t671_source_binding.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:922)）、次の分岐に直接対応する負例がない。

- 最終 NUL 不在: [contract_loader_binding.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:393)
- TAB 不在、field 数不正、空 raw path、空 mode: 同ファイル:401-413
- malformed ls-tree OID: 同ファイル:430-434

特に「全期待 entry の後に、NUL 終端されていない期待外 entry」を返すケースでは、最終 NUL 検査を削除する変異が `entries.pop()` により期待外 entry を捨てて受理し得る。既存 unexpected test は期待外 entry も NUL 終端しているため、この変異を殺せない。

**修正案:** 上記 malformed raw bytes を literal で組む parameterized test を追加する。最終 NUL の負例は「valid expected entries + unterminated unexpected entry」とし、fake の exact argv と call 数も assert する。

## C-06 — artifact admission の2 fake に明示到達 marker がない

**severity:** should-fix  
**自己判定:** real。書き換え自体は意図を保つが、fake 到達を test 自身が明示的に証明していない。

`redirected_git_view` は到達記録がなく（[test_artifact_admission.py:2331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_artifact_admission.py:2331)）、`missing_blob` も injection marker を持たない（同ファイル:2390-2404）。後者の `match="git command"` は変更前から緩められてはいないが、別の早期 Git failure でも一致し得る。

一方、新規所有 test の batch fake は `calls` を marker として exact argv、stdin、call 数まで検査している（[test_t671_source_binding.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:235)）。

**修正案:** 各 fake に `reached` または call list を持たせる。missing test は ls-tree branch が一度だけ発火したこと、例外 message に対象 path が含まれることも assert する。

## C-07 — 所有 test の恒真性

**severity:** blocker  
**自己判定:** refuted。

新規 test は旧実装に存在しない `_iter_blobs` を直接通すだけでなく、public capture の exact 3 process、batch stdin 62行、OID逆順と digest permutation、n=1/62 の timeout 差を検査する（[test_t671_source_binding.py:1086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:1086)、同ファイル:1359-1410、1537-1620）。旧逐次実装では同じ call 台帳にならない。

fake response は literal bytes、標準の `os.fsencode`、独立した `hashlib.sha256` で構成され、production parser/encoder を使っていない。逆順 test の digest も response と同じ permutation になっている（同ファイル:1121-1124）。

**修正案:** C-05/C-06 の防壁追加以外は不要。

## C-08 — test_artifact_admission.py の2 fake の意図

**severity:** blocker  
**自己判定:** refuted。

top-level fake は `rev-parse --show-toplevel` だけを偽 repository に差し替え、その他の kwargs を透過する（[test_artifact_admission.py:2329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_artifact_admission.py:2329)）。期待値 `match="Git top-level"` も維持されている。

missing fake は実 ls-tree 出力から対象 raw path の entry 一件だけを除去する。末尾の空要素も join するため NUL 終端は保存され、他 entry は変えない（同ファイル:2390-2399）。期待値 `match="git command"` も旧 test から緩められていない（[unitA.patch:523](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/unitA.patch:523)）。

**修正案:** 意図の修正は不要。到達証明だけ C-06 のとおり追加する。

## 段3レンズA対応表

| ID | 状態 | 根拠 |
|---|---|---|
| A-01 | closed | ls-tree path→OID と batch header OID の exact 照合が実装され、digest permutation を伴う逆順 test もある。 |
| A-02 | closed | ls-tree は unique paths、cat-file は重複込み queries に対して `10*n`。n=1/62 と3/4の差を固定。 |
| A-03 | closed | 拒否優先順位は plan-v2 で契約外。NUL は subprocess 前に `contract-loader-git-error` へ正規化される。 |
| A-05 | partial | 指定された主要負例、OID逆順、mode、literal path、marker は概ね追加済み。ただし C-05 の ls-tree framing と C-06 の2 fake marker が不足。 |
| A-07 | closed | type blob を基準にし、mode 100755/120000 の committed 正例がある。capture/live の disk 非 regular 拒否も既存 reader と呼出順で維持。 |

## 検査の区分

本レビューは指定 file の静的検査のみで、pytest は実行していない。[author.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/artifacts/dev-wave-acceptance-gitbatch-20260908/author.md:9) の実走件数・結果は独立検証しておらず、本レビューでは「緑」と認定しない。

## 総括

- real blocker 0件、real should-fix 2件。
- 最重要1: ls-tree 最終 NUL と malformed entry の test 防壁が不足する。
- 最重要2: artifact admission の2 fake に明示到達 marker がない。
- 最重要3: 実装本体の受理集合、OID束縛、generator完走、drift非対称には静的な blocker を認めない。