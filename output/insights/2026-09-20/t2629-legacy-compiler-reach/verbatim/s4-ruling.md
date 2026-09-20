# 段 4 裁定 — [T-2629] 旧分岐の compiler 非対称

相談 `codex/s3-consult.md` (2 レンズ 1 本、must-fix 5 / should 3 / nit 2) を親が現物で検算した結果と、plan v2。

## 所見の裁定

| # | 区分 | 裁定 | 検算 (親) | 採否 |
|---|---|---|---|---|
| A1 | must-fix | **real** | AST で `buildcache.build` / `build_v2` の直接呼び手を再走査。production の legacy `build()` 直接呼び手は 7 箇所 (backoff_profile:857、between_run_floor:336、pegasus_floor_scoping:218、s1_verify_extime_calibration:390、s2_verify_calibration:356/357、s3_lock_coverage:258、s5_permutation_coverage:293)。evidence 側 / build 側の compiler は全て同一 (site 解決を両方に渡す、または両方既定) → 対称 | 採用。README に直接経路表を併記し、閉包の範囲を「certified 入口 3 API の 28 呼び出し箇所 (中継 3 + 外側 25、外側に手動 test 1) + legacy `build()` 直接呼び手 7 (+ manual_probes / probes 5)」と書く |
| A2 | must-fix | **real** | `g++-13` 不在は login `pegasus02` (2026-09-20) と compute `bnode009` (2026-09-14) の観測。全 node・将来の PATH は未観測 | 採用。R-b は「観測した node・日時・PATH での拒否」に限定。`g++-13` が解決可能になった場合の残る検査 (R-c と v1 の toolchain 非束縛) を限界に書く |
| A3 | should | real | repo 内 (tracked) の campaign WAL 30 本を検索: env_tag は全部 `linux-baremetal` (3086 record)、`build-error` abort 30 件の内訳 = compile error (rc=2) 9、`ccbench_commit 不一致` 1、error 本文なし 20。compiler 不在 (`not found` / `CMAKE_CXX_COMPILER`) は 0。`g++-13` の出現 463 件は全部 configure argv | 採用。「worklog / failures に記載なし + repo 内 WAL 30 本に該当なし。Pegasus の durable output root 配下の WAL は未検索」と書く |
| A4 | nit | 支持 | `site_policy.py:30〜46` は hostname `bnode[0-9]+` を compute に分類し環境値に依存しない | 採用。前提 (未注入経路・hostname 安定・manifest 無し) を README に明記 |
| A5 | nit | real | 25 = 外側の集計 (中継 3 を除く)。手確認 3 件を含めると外側 25 + 中継 3 = 28 | 採用。件数の表記を直す |
| B1 | must-fix | **real** | `pipeline.py:1858〜1860` の事前 evidence 失敗 reason は `identity-error`。`model.py:207〜214` で `identity-error` は retryable、`build-error` は非 retryable。`s1_direct_comparison.py:1005〜1018` は逆に `build-error` を retryable 扱い | 採用。**P2 の根拠「reason が変わるだけで成果物不変」を撤回。** (ii) は failure stage・WAL reason・再試行分類を変え、条件次第で R-c の拒否範囲も変える。採らない理由は「到達する呼び手が無く必要性を確認できない + 再試行意味論を変える」に改める |
| B2 | must-fix | **real** | SourceEvidence に compiler 名は無く、`_recheck_source_evidence` は build compiler で再計算した evidence 全体 (`src_token`、`source_bytes_sha256`、proof snapshot、verification_variant) の exact 一致を要求 | 採用。R-c を「build compiler で再計算した source evidence が事前 evidence と異なれば拒否」に限定。「compiler 差は全て拒否」とは書かない。同一 identity・異なる toolchain の性能値 (v1 の非束縛) は D293 の領域で本 wave は保証しない |
| B3 | should | real | `_run` (`buildcache.py:3791〜3821`) は heavy-work gate → `subprocess.run` (OSError 未捕捉) → rc≠0 で RuntimeError。cmake 自体の不在は FileNotFoundError が素通り (`pipeline.py:2024` の except に入らず、`loop.py:795` の Exception 隔離で eval-exception) | 採用。拒否順序表を site gate / cmake 起動失敗 / cmake 非 0 / cache-hit の evidence 再計算に分ける |
| B4 | must-fix | **real** | `build_admission.py:675〜678`: stock admission (receipt 無し) は `src_token == STOCK` ∧ `tracked_clean` ∧ `ccbench_commit == CURRENT_PIN`。`pin.CURRENT_PIN = "511c953"`、worktree の submodule HEAD `511c9538e4e8…` と一致。login では site compiler = 既定 `g++-13` なので evidence は両 cell とも失敗する | 採用。probe を下の plan v2 の形に限定 |
| B5 | should | real | D293 の対象は床値 campaign の compiler 解決 + toolchain 束縛の同時 land 条件 | 採用。(i) を採らない理由を「必要性未確認 + 床値では D293 の同時束縛条件」と分けて書く |

scope 外の real 所見: なし (全所見が本 wave の記述・probe 設計の修正で閉じる)。

## provisional 裁定の確定

- **(P1) 条件付き支持 → 確定:** 修正しない。限界として閉じ、確認した呼び手の範囲を明記する (裁定 D2044 項 24 の形)。
  修正候補 (i)〜(iii) はいずれも採らない: (i) 障壁を外す方向で床値では D293 の同時束縛条件が要り、必要性が未確認。
  (ii) B1 のとおり再試行意味論を変え「不変」でない。(iii) 依頼が scope 外と明示。
- **(P2) 反証 → 撤回:** 「reason が変わるだけ」は誤り。上の理由に置き換える。
- 実装面の差分ゼロ (probe は repo に残さない) → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。

## plan v2 — probe (段 5、Codex author 1 本)

`tools/t2629_legacy_compiler_reach_probe.py` (≤150 行、untracked、job dir へ退避)。production の関数を stub 無しで呼び、返り値と例外を JSON に記録する。

| key | 呼ぶもの | 記録 |
|---|---|---|
| `env` | `socket.gethostname()`、`datetime.now(UTC)`、`site_policy.current_site()`、`buildcache.compilers_for_current_site()`、`(DEFAULT_CC, DEFAULT_CXX)`、`os.environ["PATH"]`、`shutil.which` (`g++-13`/`g++`/`gcc-13`/`gcc`/`cmake`) と `os.path.realpath`、`g++ --version` 先頭行、NQSV 系 env の有無 | 全 node へ一般化しない (A2) |
| `authorization_linux_baremetal` / `authorization_pegasus` | `auth = env_contract.authorize(tag)` (失敗は `stage: "authorize"`) → `execution_guard.require_certified_writer_authorization(auth, env_tag=tag, clocks_per_us=c.clocks_per_us, numactl=list(c.numactl), env_contract=None)` (失敗は `stage: "guard"`) | pegasus 正例は「認可関数が通る」であり full attestation ではない (B4) |
| `evidence_site_cxx` / `evidence_default_cxx` | `genome = Genome("silo", {**_BASE, "BACK_OFF": 1})` (p3_kickoff の STOCK_G と同定義)、`commit = pin.CURRENT_PIN`、`sub = buildcache._ccbench_dir()`、`source_digest.resolve_evidence(genome, commit, ccbench_dir=sub, cxx=cxx)` | site cxx == 既定なら後者は `"same-as-site"` で省く (B4)。observed は `cxx`、`src_token`、`tracked_clean`、`ccbench_commit`、`source_root` |
| `legacy_build_trace` | site 側 evidence が取れた場合だけ: `build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)` → `derive_build_admission(ctx, ev)` → `require_build_admission(adm, expected_policy=ctx.policy, expected_source=ev)` → **cc/cxx 無しで** `buildcache.build(genome, commit, trace=True, cache_root=<専用の空 dir>, ccbench_dir=sub, src_token=ev.src_token, admission=adm, build_context=ctx, source_evidence=ev)` | 例外の `stage` (`build_run_context` / `derive` / `require` / `build`) と本文 (stderr 末尾を含む)。site evidence 不在なら `SkippedNoEvidence`。login では heavy-work gate の拒否が先に来るので R-b の configure 実測に数えない (B4) |
| `limitations` | probe 自身が書く | — |

削った項目: `recheck_default_cxx` (cache-hit 経路の `_recheck_source_evidence(cxx=既定)` は `resolve_evidence(cxx=既定)` と同じ RuntimeError で、`evidence_default_cxx` と結論が同じ。静的確認として README に書く、B4 (e))。

probe が測るもの: 実 site・compiler 解決・認可の拒否/通過・evidence の成否・fresh build の例外。**測らないもの:** pipeline の WAL abort 変換、cache-hit 経路、2 compiler 間の R-c 不一致 (これらは静的確認)。

## 段 6 以降

- 段 6: 独立 read-only レビュー 1 本 (README 草稿 + probe JSON + 本裁定)。実装面差分ゼロなので 2 本目は省く (DW-C00 軽量版)。
- 段 7: insight `output/insights/2026-09-20/t2629-legacy-compiler-reach/README.md`、decisions fragment ({{D:...}}: 修正しない・限界として閉じる・呼び手範囲・保証境界)、worklog fragment (T-2629 完了)。
- 受入全走 → land。
