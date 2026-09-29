## A 投入

投入は **A-6 policy を選んだ rr95 の 1 request** である。policy は 5 node、12 時間、job 名は `paper-a6-cert` と定める。`paper-a2-cert` は A-2 用の名前である。根拠: [A-6 policy](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a6_certification.v2.json:31)、[job 名の選択](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:374)、[brief](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:10)。

投入前に `035fc11fa` の detached worktree を brief 指定の `submit-tree` に作り、submodule を再帰初期化して `external/ccbench` の clean HEAD が `6810666` を解決することを確認する。checkout は job の終了と collect が済むまで保持する。submission receipt はその絶対 path と job body の bytes を後段でも検査する。根拠: [brief](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:10)、[pin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/pin.py:30)、[submitter](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/submit_paper_story_a2_certification.sh:165)、[receipt 検証](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:1522)。

```bash
git worktree add --detach /work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree 035fc11fa
git -C /work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree submodule update --init --recursive

cd /work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree
python3 tools/pegasus/fetch_third_party.py hydrate \
  --repo-root "$PWD" \
  --cache-root /work/1/SFC/tanab/izanagi-thirdparty-cache \
  --staging-root /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/thirdparty-src
```

`hydrate` の JSON にある `.source_root` を投入へ渡す。cache root そのものは source root ではない。staging と cache は重ねられない。根拠: [third-party 手順](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/README.md:296)、[hydrate の引数と出力](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/fetch_third_party.py:698)。

```bash
cd /work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree
bash tools/pegasus/submit_paper_story_a2_certification.sh \
  --policy orchestrator/campaign/paper_story_a6_certification.v2.json \
  --attempt-id a6-r2-20260929a \
  --ccbench-root /work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree/external/ccbench \
  --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps \
  --third-party-source-root /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/thirdparty-src
```

投入前に **login で確認できるもの** は、`python3.10` による module/policy 読込、login hostname、`qstat`・`qsub`・`check_quota` 等の存在、queue の ENA/ACT、checkout と CCBench の clean/pin、各 source path の実在・非 symlink、既存同名 request の不在、新 attempt leaf の未使用である。driver 自身もこれらを検査する。`qsub -v` は列挙済み変数だけを渡すため、trace archive root を追加する口はない。根拠: [submitter](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/submit_paper_story_a2_certification.sh:68)、[path と pin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/submit_paper_story_a2_certification.sh:172)、[request と環境変数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/submit_paper_story_a2_certification.sh:235)。

**計算ノードで初めて確定するもの** は PBS 環境・5 node の実割当て、予約時刻と job body hash、scratch の鮮度、依存 source のコピー後の状態、compiler/toolchain、patch 適用、condition gate の supply/meaning records、source evidence、4 sibling への verify fanout と実際の正しさ・性能結果である。根拠: [job body の環境・割当て](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/paper_story_a2_certification.sh:9)、[予約・preflight・run](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/paper_story_a2_certification.sh:182)、[patch と gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:681)、[source evidence と fanout](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:3763)。

`6810666` でこの driver を通した実績は brief 上ゼロなので、特に `silo-backoff-fixed.patch` の適用、`BACKOFF_FIXED` の意味 witness、source token の stock/adopted 役割、FetchContent と policy の束縛、4 sibling を要求する fanout は測定前停止の候補として記録する。login で静的な pin/path を確認できても、これらの実行結果の代用にはならない。根拠: [brief P7](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:16)、[gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:726)、[fanout 条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:325)。

## B 完走後

`cwd` は最後まで **submit-tree** とする。A-6 policy の相対指定はそこで解決し、submission receipt は同 checkout の policy 絶対 path、`submission_cwd`、job body hash を束縛する。`finish-group` は terminal な `qstat`、`compute-result.json`、`reservation.json` を要求し、成功時は completion と acquisition を両方作る。したがって通常は `record-acquisition` を重ねて実行しない。completion が既にあり acquisition だけが欠けた場合に限り、状態と既存 receipt を調べた上で同 CLI を使う。根拠: [submission receipt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/pegasus/submit_paper_story_a2_certification.sh:332)、[finish-group](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:2229)。

```bash
cd /work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree
bash tools/pegasus/submit_paper_story_a2_certification.sh finish-group \
  --policy orchestrator/campaign/paper_story_a6_certification.v2.json \
  --attempt-id a6-r2-20260929a

# acquisition だけが欠け、completion が正当に存在する場合のみ
python3.10 -B -m orchestrator.campaign.paper_story_a2_certification \
  --policy orchestrator/campaign/paper_story_a6_certification.v2.json \
  record-acquisition \
  --attempt-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-r2-20260929a \
  --current-pin 6810666

python3.10 -B -m orchestrator.campaign.paper_story_a2_certification \
  --policy orchestrator/campaign/paper_story_a6_certification.v2.json \
  collect \
  --attempt-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-r2-20260929a \
  --current-pin 6810666 \
  --acquisition-receipt /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-r2-20260929a/receipts/acquisition.json \
  --repo-root /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/collect-root
```

`collect-root` は**先に存在する空 directory** にする。`materialize` は `repo-root` に git checkout を要求せず、policy の `tracked_destination` をその下の新 leaf として作る。ただし単なる path 検査だけではない。durable base 全体の attempt census と、同じ `(study, policy_sha256, current_pin)` を持つ兄弟の結果 footprint を検査する。既存の `a6-20260908b` と `a6-20260909b` は pin が `511c953` なので、予定の `6810666` attempt とは cohort が異なる。根拠: [materialize](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:4811)、[cohort 選択](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:1293)、[旧 preregistration](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/preregistration.json)、[5-node 実績の preregistration](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260909b/preregistration.json)。

`reject` は性能 verdict であり collect の正常な結果として `rc=0`、`indeterminate` は materialize できても `rc=2` となる。job が早期停止して `compute-result` や reservation を残せなければ `finish-group` 自体が失敗し得る。その場合は receipt・scheduler log・欠落物と理由を insight に記し、certification や図を捏造しない。根拠: [driver rc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:3185)、[finish-group 必須物](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:2260)、[collect](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:5045)。

## C 図と表

repo 外 wrapper は生成器を import し、R2 の `certification.json` と `raw-manifest.json` の**実 bytes の SHA-256** を `{"certification": ..., "raw_manifest": ...}` として `main(argv, expected_hashes=...)` に渡す。出力 prefix は `fig11_` で始める。元 attempt の入力には既存の canonical hash 表をそのまま使える。根拠: [hash override](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:129)、[main と prefix](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:619)、[既存 fig11 provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json:19)。

A-6 caption では「formal certification attempt」「one attempt」「historical concordance」などの**地位・役割語だけ**を R2 の別 attempt に合わせる。5 標本、median/effect、CI、正しさの別走、限定の意味は変えない。wrapper が `_caption` を差し替えるなら、出現回数を固定して逸脱時は停止し、provenance の caption 再検査にも同じ差し替えを適用する必要がある。生成器本体の `validate_repo_closure` は元の `_caption` を再計算するため、R2 provenance を素のまま検査すると不一致になり得る。再現 command も wrapper 呼出しを指す形に記録する。根拠: [A-6 caption](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:654)、[publish と closure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:897)、[fig8b の先例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-28/t2853-r2-fig8b/README.md:239)。

R2 入力で失敗し得る検査は、current-full schema と埋込 policy grammar（`HISTORICAL_CURRENT_POLICY_VIEWS` は既知の旧 A-2 組だけを例外扱い）、全 cell の `source_binding_status=bound`、manifest の 6 file closure、condition receipt と source token、WAL/raw/認証値・5 標本・正しさの一致、外部 file hash、caption と artist の closure、レイアウトである。`indeterminate` や欠けた raw は通常の図入力にならない。検査を外して描かず、拒否箇所を記す。根拠: [policy view](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:201)、[closure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:278)、[値の照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:402)、[publish 前 layout](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:897)。

陽性対照は、元 attempt を wrapper で原 metadata のまま描き、`artist_series` を既存 fig11 provenance と完全一致させること。負例は certification hash の不一致、欠けた外部 file、改変した condition receipt 等で描画拒否と図未作成を確認すること。対照表は `load_measurements(original_root, original_cert, original_manifest)` と `load_measurements(R2_root, R2_cert, R2_manifest, R2_hashes)` を別々に呼び、`cells` の stock/adopted 各 5 標本・中央値・平均/CI、`effects.rr95`、`outer_status`、pin・request・source commit を並記する。標本や verdict は合成しない。根拠: [load_measurements の戻り値](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:512)、[既存 artist と入力](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json:19)、[依頼](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/request.md:3)。

## D 見積り

一次資料 `a6-20260909b/jobs/rr95/scheduler/job.stderr` は request `986046.nqsv`、`Number of Jobs: 5`、`Elapse: 1057S` を記録し、job `0001`〜`0004` は compute body を走らず終了した。同じ request の **5 node を 1 回だけ**数え、`5 × 1057 / 3600 = 1.4681 node 時間`。予約記録は 43,200 秒、compute result は `driver_rc=0` を示す。根拠: [会計 stderr](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260909b/jobs/rr95/scheduler/job.stderr)、[reservation](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260909b/jobs/rr95/reservation.json)、[compute result](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260909b/jobs/rr95/compute-result.json)。

予定は本走 1 request ≈ **1.47**、受入 1 回 ≈ **0.25**、合計 **1.72 node 時間**。D2219 の「開発検査も含め、Elapse 単価で数える」に沿い、現時点の P3 判定は妥当。ただし 2 時間までの余白は 0.282 node 時間、5 node の本走 Elapse 換算で約 **203 秒**しかない。新 pin での cache miss・起動時失敗後の再投入・追加の計算ノード検査を予定へ入れるなら投入前に合計を再見積りし、2 以上なら確認が必要である。根拠: [brief P3](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:12)、[D2219 項1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/decisions.md:71255)。

## E §0

投入前に insight §0 を書いて commit し、次を固定する。

- `a6-r2-20260929a` は**現行 driver・現行 5-node policy・現行 pin `6810666` の再現パッケージの別 attempt**。元 `a6-20260908b` の置換・追認・合算ではない。結果稿 §3.2 の「反復 attempt は行わない」という元系列の決定を改訂しない。根拠: [brief](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:3)、[結果稿 §3.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/paper-story/results/2026-09-18-a6-certification-reject.md:233)。

- 結果を見る前に attempt 数を 1、停止基準を「この request の結果を、成功・reject・indeterminate・未完走のまま報告」と定める。起動時停止を再投入する扱いも、行うなら**結果前に条件と上限を明記**する。実行基盤の副産物を後から A-6 attempt に昇格させなかった D1870 と混同しない。根拠: [D1870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/decisions.md:56707)、[結果稿 §3.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/paper-story/results/2026-09-18-a6-certification-reject.md:241)、[fig8b §0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-28/t2853-r2-fig8b/README.md:20)。

- 正しさは job 内の別 build・別走で判定し、anomaly は reject。図が生成器に拒否されたら理由を掲載する。元稿・元 attempt・既存 fig11 の bytes は維持し、R2 の数値は insight の表と図にだけ置く。根拠: [brief](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:8)、[fig8b §0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-28/t2853-r2-fig8b/README.md:35)。

## brief への指摘

1. **P5 は概ね正しいが、理由が不足する。** `collect-root` に git は不要。ただし materialize は durable base の cohort 衝突も調べる。今回は旧 2 attempt と pin が違うため通る見込みであり、「repo 外だから通る」だけではない。根拠: [brief P5](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:14)、[cohort 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/orchestrator/campaign/paper_story_a2_certification.py:1293)。

2. **P6 の caption 差し替えには provenance の閉包対応が要る。** `validate_repo_closure` は元の `_caption` を再計算する。wrapper の差し替え後 provenance を素の生成器だけで再検査する設計は失敗し得る。根拠: [brief P6](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:15)、[closure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:932)。

3. **結果稿の「図は無い」は現行 repo の状態と食い違う。** 現在は fig11 の PNG・PDF・provenance があり、陽性対照に使える。結果稿は元結果の記述として bytes 不変で扱う。根拠: [結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/paper-story/results/2026-09-18-a6-certification-reject.md:311)、[既存 fig11 provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json:1)。

4. **P3 は予算上の確約ではない。** 既存 5-node 実績からの妥当な一点見積りだが、203 秒の余白しかない。特に `6810666` 初回の失敗を受けた再投入を予定に含めるなら、2 node 時間の線を再判定する。根拠: [brief P3/P7](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:12)、[D2219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/docs/decisions.md:71260)。

## 総括

静的検査では、**別 checkout・別 attempt・repo 外 collect と wrapper** で元成果物を保ったまま進められる。投入前に §0 と再投入条件を固定し、実行後は receipt chain の結果をそのまま報告する。今回の依頼どおり、テスト・script・測定は実行していない。根拠: [依頼](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/request.md:3)、[brief](/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/s1-brief.md:3)。