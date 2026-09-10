## 所見 (real/refuted + 成果物影響)

1. **real / must-fix — M2 の単一理由性が成立していない。** write bit 除去を no-op にすると、保護後検査が `post-oracle-write-bits-remain` で `yield` 前に拒否します。[M2 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1410) の同一 bytes 書込みと最終 assertion には到達しません。  
   成果物影響: 現在の M2 は D984 の実効書込み禁止を単一理由で証明する変異として登録できません。

2. **real / nit — `chmod` 成功から `changed.append()` までに狭い非同期例外窓がある。** 通常の `OSError` / `NotImplementedError` では対象 node は変更されず、先行 node は復元されます。一方、成功直後に `KeyboardInterrupt` や `MemoryError` が入ると、その node は `changed` に無いため復元されません。[helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:581)  
   成果物影響: build は開始または完了せず、job-local scratch が部分的に読取専用で残り得ます。受理済み測定成果物への影響はありません。

3. **refuted — 判定根への通常の path-based 書込み漏れはない。** root、全サブ directory、全既存 node の write bit が落ち、再走査でも残存 write bit を拒否します。  
   成果物影響: 標準 `masstree_build` が判定済み材料を再生成して採用される経路は閉じています。

4. **refuted — 正常な up-to-date build と `<base>` 配下の sibling build は巻き添えにならない。** 保護列挙は `masstree-src` だけを起点とし、親は含みません。  
   成果物影響: mimalloc、googletest、subbuild、stamp の正常な生成場所は維持されています。

5. **refuted — build 後検査、束縛なし argv、identity、receipt schema は後退していない。** `protected_root` は build 前専用で、build 後の `effective_root` は再取得されています。`buildcache.py` の commit 差分は build arm だけです。  
   成果物影響: 既存 post-oracle 証明と generic build の互換性は維持されています。

6. **refuted — 新設 5 node は焦点機序を stub で迂回していない。** CMake subprocess は fake ですが、M1/M2 は実 buildcache 分岐と実 helper、M2は実 filesystem 書込み、M3/M4は実 chmod context を通ります。  
   成果物影響: 焦点機序についての偽緑は認めません。ただし実 protected CMake build は本レビューでも未実測です。

## 書込み不能化の網羅性 — 止まる path と止まらない path

[custom command](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/external/ccbench/cmake/ThirdParty.cmake:66) は `masstree_SOURCE_DIR` を作業 directory として `bootstrap.sh`、`configure`、`make`、`ar`、`ranlib` を実行します。

| 操作 | 判定 |
|---|---|
| 既存 `config.h`、archive、object への truncate / append | file 自身の write bit 除去で停止 |
| root 直下の `config.log`、`autom4te.cache`、`*.o` 新規作成 | root 自身が列挙末尾に入り、write bit 除去されるため停止 |
| サブ directory 内の `.deps/`、dependency file、新規一時 file | 各 directory の write bit 除去で停止 |
| root 内の unlink / rename | 親 directory が書込み不能なので停止 |
| `<base>/mimalloc-build`、`googletest-build`、subbuild、stamp | 保護対象外で、意図どおり継続可能 |
| `<base>` からの `masstree-src` entry 自体の rename / replacement | 停止しない。ただし標準 custom command の書込み集合ではなく、同一 uid の非協調 actor という明記済み限界 |
| owner による chmod 巻戻し、privileged actor、事前に開いた writable fd | 停止しない。明記済み discretionary-mode 限界 |

列挙は子を先、directory を後、root を最後に積みます。[permission_nodes](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:507) 保護時には親 directory がまだ通過可能で、復元時も write permission は不要です。execute bit は一切落とさないため、同じ後順で子から root まで復元できます。

`chmod` 自身が同期的に失敗した node は `changed` に入らず、先に成功した node だけが復元されます。保護後の再走査や identity 検査が失敗した場合は全 node が `changed` 済みなので全復元が試行されます。

## 正常経路と過剰拒否

両 OUTPUT が既に揃う通常経路では、再生成 custom command に明示 `DEPENDS` はなく、親裁定にも保存済み非 protected build の無書込み正例があります。protected 実 CMake build 自体は未実測ですが、静的機序との矛盾はありません。

親 directory は列挙されず、M4 test も保護中の `<base>` 直下 `mkdir` を実 filesystem で確認します。[M4 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_sort_swo_dependency_material.py:216)

symlink はこの platform で fail-closed になります。これは抽象的には受理集合を縮めますが、正常材料を拒否する実在根拠はありません。

- repo fixture の静的列挙は 103 descendant、内訳は regular file 102、directory 1、symlink・FIFO・socket・device・複数 hardlink 0。
- 保存済み実 build 証拠も regular 196、symlink 0 です。[保存済み証拠](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/docs/archive/worklog-phase3-0826-989.md:20)
- prompt 記載の親実測も実物 144 node、symlink 0 件です。

FIFO、socket、device は Linux 上で owner が chmod できれば write bit が落ちます。hardlink は regular file として扱われ、同一 inode の全 link からの path-based writeを止めます。正常材料にこれらがある証拠はありません。

build 後は material assert が残り、[buildcache.py:2824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2824)、`effective_root` を再取得して exact root、receipt、archive を再照合します。[buildcache.py:2828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2828) 保護用 `protected_root` の流用はありません。

`git diff HEAD^ HEAD` では `_v2_commands`、`_v2_identity`、receipt validator、completion schema に変更はありません。束縛なし branch は従来と同じ `_run(build_cmd, ...)` と同じ例外変換です。

## 変異 M1-M4 の単一理由性

| 変異 | 判定 | 根拠 |
|---|---|---|
| M1 | **refuted: 単一理由性あり** | exact 一致を恒真化すると build が開始され、既存の build 後 root mismatch は `pytest.raises(Exception)` に吸収されます。赤は `events == ["configure"]` の時点差だけです。 |
| M2 | **real: 単一理由性なし** | chmod no-op は [write-bit 残存検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:601) が `yield` 前に拒否します。同一 bytes 書込みの成否まで到達しません。 |
| M3 | **refuted: 単一理由性あり** | 復元を no-op にすると、他層は mode を戻さず、成功・consumer error 後の exact mode assertion だけが赤になります。 |
| M4 | **refuted: 単一理由性あり** | 親まで保護すると保護中の `<base>/new-dependency-src` 作成だけが失敗します。他の検査は介在しません。 |

M2 の再照準案は、chmod 自体の no-op ではなく、保護後検査を通過した直後かつ `yield` 直前に `restore_modes(changed)` を挿入する単一変異です。これなら build window だけが writable になり、同一 bytes 書込みは成功し、既存 hash/root 検査も通り、M2 の `rewrite_failures` assertion だけが赤になります。

## must-fix と nit の切り分け

- must-fix: M2 を現状のまま DW-M01 変異として登録しないこと。上記の build-window 早期復元変異へ再照準する必要があります。production helper 自体の修正は不要です。

- nit: `chmod` 成功と `changed.append()` 間の非同期例外窓。影響は失敗した job-local scratch の mode 残留に限られ、成果物は publish されません。今回の scope で追加防壁は推奨しません。

- must-fix ではない: protected 実 CMake build の未実走、symlink の fail-closed、同一 uid の chmod 巻戻し、process 間競合。いずれも開示済みか、正常材料に実在しない条件です。

## 総括

production 実装の書込み禁止、root 網羅、復元順、正常 sibling 経路、build 後再照合、generic 非変化には must-fix を認めません。

ただし M2 は内側の `post-oracle-write-bits-remain` に先取りされ、DW-M01 が要求する単一理由性を満たしません。したがって結論は「実装機序は妥当、変異証明束は M2 再照準まで未完」です。

本レビューは静的検査のみで、pytest は実走していません。file の変更もありません。