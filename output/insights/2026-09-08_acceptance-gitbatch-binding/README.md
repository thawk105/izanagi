# 受入全走の高速化 — contract-loader binding の blob 取得を 62 process から 2 process へ

- authority: none (可変状態の正本は worklog と decisions。本書は一次資料の置き場)
- default_effect: no-state-change
- wave: `dev-wave-acceptance-gitbatch-20260908` / branch `worktree-dev-wave-acceptance-gitbatch-20260908`
- base main: `34af5a571def179d1c841ce6e8a1cbcaeb9e9771`
- 実測日: 2026-09-08 (Pegasus login pegasus02、焦点走・変異は dispatch 経由)
- 一次資料: `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/*/junit.xml` (受入走の junit)、本 dir の `mutation-spec.json` / `mutation-ledger.json`

依頼は「受入全走の高速化。テスト所要時間が伸びている。並列化・分散化・賢い手で短縮、過剰実装・過剰ガードレールならオフ・削除も検討」。
**本 wave が land したのは、enforcement source closure 62 path の blob 取得を 1 path 1 git process から `ls-tree` + OID 指定 `cat-file --batch` の
2 process へ改める変更と、それに伴う wiring probe の許可形の更新・test 追加である。** 受理集合は変えていない。計算ノードでの効果は
本 wave の受入走の junit で読む (§5)。

## 1. 何が遅かったか

受入走の junit (直近 10 日) を集計すると、直列総仕事量 W (testcase duration 総和) は 09-05 昼 ≈ 15,000 秒から 09-08 ≈ 25,000〜29,000 秒へ
増えていた。**同じ node 20,873 本の和が 17,091 → 24,247 秒 (+42%)** で、新規 node の寄与は 1,093 秒だけ。「test が増えた」のではなく
既存 test が重くなっていた。増分は `test_autonomous_trial_completeness` (+1,269 秒)、`test_p3_b4_raw_record_producer` (+974)、
`test_p3_b4_closed_critic` (+769)、`test_trial_registry` (+703)、`test_layer3_report` (+472) などに集中し、典型は「11 秒 → 60 秒」「8 秒 → 40 秒」の
加法的 +30〜50 秒で、fixture は `tmp_path` だけだった。

login で 1 本を profile した (`test_p3_b4_raw_record_producer.py::test_m10_empty_red_section_is_rejected_instead_of_marking_both_arms_true`、47.5 秒):

| 内訳 | 秒 |
|---|---:|
| `contract_loader_binding._run_git` (git subprocess **704 回**) | 36.4 |
| うち `capture_contract_loader_binding` 5 回 / `verify_committed_contract_loader_binding` 4 回 / `verify_live_contract_loader_binding` 1 回 | 18.9 / 14.9 / 4.9 (入れ子で重複計上) |
| `_read_regular_file_no_follow` 372 回 (posix.open 3.6 秒) | 4.3 |
| fsync 56 回 | 2.4 |

`_blob` が closure 62 path × 1 process (`git cat-file blob <commit>:<path>`) を、admission 検査のたびに繰り返していた。呼び出し元は
`artifact_admission.require_admitted_campaign` (`_verify_committed_loader_binding`、`_require_verifier_epoch_for_purpose`)、`ident.py` の
campaign lock 検証、`p3_b4_closed_critic._load_stable_snapshot`。

**09-05 20:48 の走から W が増えた事実と、この module の最終 commit (09-03) は日付が合わない。** caller 側にも 09-04〜06 の変更は無い。
本 wave は「+42% の帰属」を主張しない。主張するのは「現在の費用構造」と「改修後の実測」だけである。

## 2. login での 3 形の実測 (62 path 1 回分、load ≈ 21〜27)

| 形 | 所要 |
|---|---|
| 現行: 逐次 62 process (`cat-file blob <commit>:<path>`) | 5.37 / 6.80 / 6.02 秒 |
| 1 process `cat-file --batch`、stdin に `<commit>:<path>` 62 行 | 1.566 / 1.289 / 0.904 秒 (別回 0.647 / 0.618 / 0.940 / 0.751) |
| **`ls-tree -r -z <commit> -- :(literal)<path>` x62 (0.03〜0.06 秒) + OID 指定 `cat-file --batch`** | **0.081 / 0.089 / 0.071 / 0.091 秒** |
| 参考: 単発 `rev-parse` / `cat-file blob` 1 件 | 0.036〜0.047 秒 |

3 形の sha256 62 件は完全一致した。`<commit>:<path>` 形は spec ごとに tree を辿り直すため 1 process でも遅い。
62 path の mode は全件 100644 / type blob。

## 3. 何をしたか

`orchestrator/campaign/contract_loader_binding.py` に ordered generator `_iter_blobs(root, commit, relative_paths)` を置いた。

1. 全 relative を `_relative_parts` で検査し、encoded bytes に NUL があれば subprocess を起動せず `contract-loader-git-error`。
2. `ls-tree -r -z <commit> -- :(literal)<relative>...` (重複除去、timeout = `GIT_TIMEOUT_SECONDS * n`)。出力を NUL で分割し、
   `<mode> SP <type> SP <oid> TAB <raw path>` へ exact 分割。raw path は `os.fsencode(relative)` と bytes で照合 (unquote しない)。
   期待 path の不在・期待外 entry・重複・type が `blob` 以外・oid 形式不正 → `contract-loader-git-error`。mode は拒否理由にしない。
3. `cat-file --batch` に tuple 順 (重複込み) の `<oid>\n` を stdin で渡す (timeout = `GIT_TIMEOUT_SECONDS * n`)。header は 3 field exact、
   **oid は期待 oid と exact 一致**、type は `blob`、size は非負 decimal、body の直後に protocol LF、最後に offset == len(stdout)。
   `missing` / 未知 status / 途中 EOF / 余剰 bytes → `contract-loader-git-error`。
4. 4 公開関数は generator を消費し、非対称 (capture: disk == blob → digest、live: digest → disk == blob、committed: digest のみ、blobs: 明示 path 順) を保つ。
   `_blob(root, commit, relative)` は互換 wrapper として残す。`subprocess.run` の spawn site は `_run_git` 1 か所のまま (`input_bytes` / `timeout_seconds` kwarg を追加)。

**受理集合と拒否集合は不変。拒否の優先順位 (どの path・どの理由が先に raise されるか) は契約外とした** (設計判断の正本は decisions)。
process 内 cache・memo は導入していない。

段 6 のレビューで `p3_b4_wiring_probe._allow_read_only_git` が旧 argv 形しか許可せず、新しい `ls-tree` で `ProbeIsolationError` になることが
見つかった (親が login で `test_actual_main_positive_baseline_all_drivers[base]` の赤を実測)。許可形を production が発行する exact argv
(`ls-tree -r -z <40hex> -- :(literal)...`、`cat-file --batch`) に合わせ、旧形 `cat-file blob` は削除した。焦点再レビューは、この allowlist が
`-C` より前の global option (`--git-dir=` 等) を検査していない (旧 allowlist 以来の既存の穴) と指摘し、harden prelude 全体を exact 比較する形へ直した。

## 4. login A/B (同 test、旧コードと新コードを交互に、load ≈ 3.7〜5.9)

| 標本 | 旧 (逐次) | 新 (batch) |
|---|---|---|
| 1 | 30.9 秒 (cold) | 9.6 秒 |
| 2 | 11.3 秒 | 6.4 秒 |
| 3 | 17.9 秒 | 4.6 秒 |
| git subprocess 回数 | 802 | 142 |

中央値 17.9 → 6.4 秒。残る非 git 部分 (disk 読取・fsync・tmp copy ≈ 11 秒の下限) は本変更で減らない。
public capture 1 回の process 数は 4 (`rev-parse --show-toplevel` / `rev-parse HEAD` / `ls-tree` / `cat-file --batch`)。
所有 test の「3 process」は `_validated_root` を固定した条件である。

## 5. 計算ノードでの効果

受入走は一度 main `c12e25078` の `.codex/worktrees/*` gitlink 事故 (受入の tree 指紋が `git submodule status` で落ちる) で
投入できず、その間に **受入形でない全 suite 走行 (dispatch、1 node × 48 worker、n=1)** で W を測った。詳細は `measurements.md`。
事故は別 session の `48837186c` / `cf837838a` で是正され、本 wave はそれを取り込んで受入へ進んだ。

| 対象 | 改修前 中央値 (09-08 受入 47 走) | 改修後 (n=1) | 比 |
|---|---:|---:|---:|
| W 全体 | 28,734 秒 | 17,236 秒 | 0.60 |
| `test_autonomous_trial_completeness` / `test_p3_b4_closed_critic` / `test_trial_registry` / `test_layer3_report` | 1,879 / 1,264 / 2,092 / 850 | 229 / 93 / 347 / 29 | 0.12 / 0.07 / 0.17 / 0.03 |
| 対照 `test_s8b_oracle_driver` / `test_s8b_floor_campaign` (binding を通らない) | 2,489 / 2,042 | 2,665 / 1,932 | 1.07 / 0.95 |
| profile した node | 56.0 秒 | 5.7 秒 | 0.10 |

対照 2 module が ≈ 1.0 なので低下は本変更に帰属できる。**最遅 shard wall (D1620 の測定面) の改善は、受入走が取れるまで主張しない。**
改修前の所在: 最遅 shard wall 中央値 286 秒 / p75 350 秒。読み方は D1714 に従い、最長単体でなく最遅 shard の wall と対象 module の W を併記する。

## 6. 変異検査

spec: `mutation-spec.json` (sha256 `42222d980fc16a5388331948c988f5a8f591dc79b988a3b2634568828d41f896`)、台帳: `mutation-ledger.json`。
runner は D1712 に従い所有 test `orchestrator/tests/test_t671_source_binding.py` に絞った (dispatch、`-q -rf`)。
期待 node は fix 後の最終 commit で login probe (junit) により完全集合として確定した。
本走 (dispatch、固定 HEAD `66a2ea966`、baseline PASSED): **KILLED 7 (期待 node 完全一致 7/7)、SURVIVED 4 (事前登録どおり)、MISMATCH 0、TIMEOUT 0。**

| 変異 | 期待 | 期待 node 数 | 本走 |
|---|---|---|---|
| M2 batch header の OID 照合削除 | KILLED | 1 (`..._rejects_reordered_batch_oids_even_with_permuted_digests`) | 事前登録どおり |
| M3 `_blob` を逐次 `cat-file blob` へ後退 | KILLED | 1 (`test_blob_compatibility_wrapper_uses_one_batch_query`) | 事前登録どおり |
| M4 header の type 検査削除 | KILLED | 1 (`..._rejects_malformed_header_or_status[tree-object]`) | 事前登録どおり |
| M5 exact EOF 検査削除 | KILLED | 1 (`..._rejects_extra_output_after_last_record`) | 事前登録どおり |
| M6 committed の digest 比較削除 | KILLED | 63 | 事前登録どおり |
| M7 live の disk 比較削除 | KILLED | 64 | 事前登録どおり |
| M8 ls-tree の path 不在検査削除 | KILLED | 2 | 事前登録どおり |
| M9 body EOF 検査の緩和 (`>=` → `>`) | SURVIVED (等価) | 0 | 事前登録どおり |
| M10 record LF 検査の緩和 (空を許す) | SURVIVED (等価) | 0 | 事前登録どおり |
| M12 M9 + M10 の両層同時 | SURVIVED (等価) | 0 | 事前登録どおり |
| M11 `tuple(x)` → `tuple(iter(x))` | SURVIVED (等価、harness の正例) | 0 | 事前登録どおり |

### erratum (DW-M02 / DW-M08)

- M9 / M10 / M12 は初回登録で KILLED 期待だった。login probe で 3 件とも 0 赤。理由は第 3 層 (exact EOF 検査) の `offset = body_end + 1` が
  末尾 LF 欠落を必ず `offset != len(stdout)` で拒否するためで、M9 / M10 は受理集合に対して等価な冗長 gate である。SURVIVED 期待へ改めて登録した。
- M1 (`_run_git` の stdin plumbing 削除) は 263 node を落とす (login probe、junit と `FAILED` 行が一致)。dispatch の中継は stdout 末尾 64 KB
  (うち failure digest 48 KB) なので約 117 行が上限で、263 node の完全集合を harness で照合できない。matrix から外し、login probe の junit
  (`mutation-probe-login.json`、`probe-junit-M1-stdin-plumbing-removed.xml`) を補助証拠として残す。stdin 配線は M2〜M7 の全 test が
  暗黙に通る経路でもある。

## 7. 段 3 / 段 6 の所見 (real / refuted)

段 3 (2 レンズ、blocker 9): 主要な real は「`<commit>:<path>` 形は応答が path に束縛されず逆順 + 逆対応 digest で誤受理し得る」(→ ls-tree + OID 照合)、
「timeout 10 秒が per-process から集約へ変わる」(→ `GIT_TIMEOUT_SECONDS * n`)、「拒否の優先順位と NUL の扱いが変わる」(→ 契約を狭めて明示)、
「もう 1 つの `_run_git` fake」「所要時間台帳の更新義務」。refuted は scope 膨張、spawn site / env の脱落。
段 6 (2 レンズ + 焦点 1): real は wiring probe の許可形 (D-01)、call-site meta-test の第三 caller (D-02)、ls-tree framing の負例 (C-05)、
fake の到達 marker (C-06)、prelude の非 exact (E-01)。逐語は `verbatim/` に置く。

## 8. 非主張

- 本 wave は受入 wall の短縮を、受入走の junit を読むまで主張しない。
- W の +42% がこの module に帰属するとは主張しない (日付が合わない)。
- collection 固定費 (D1728)、t080 base、不要 test 削除は触っていない。次の一手は worklog に置く。
