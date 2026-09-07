## 総括

計画は成立する。単位 A は旧 v3/v3/v2 を完全に独立した legacy 分岐として保存し、新 v4/full-v4/v3 のみを追加受理する。  
単位 B は `.py` 本体を触らず、policy の `tracked_destination` と test golden だけで完結する。推奨宛先は `output/insights/2026-09-07_t2364-paper-story-a2-certification`。  
`protocol_sha256` は `136b823e…d9f4` のまま、policy bytes SHA-256 だけが `67dce5a7…0487` へ変わる。  
D1198 適用済みを表す単一 field は存在しないため、manifest-bound condition-gate receipt の `use_class="paper"` / `admitted=true` から導出する。  
投入器は `preregister` を内包するので、親が standalone `preregister` を先に実行してはいけない。  
read-only 静的調査のみで、pytest は実行していない。

## 単位 A のプラン

受理側: 変更前は legacy `certification-result/v3` + `raw-manifest/v3` + `cell-result/v2` だけを受理するが、変更後はその受理集合を変えず、別分岐で current `certification-result/v4` + `full-raw-manifest/v4` + `cell-result/v3` を受理する。  
拒否側: schema の混在、partial manifest、bytes pin 不一致、閉包欠落、condition receipt 不成立、src_token の不一致は、出力を一つも publish せず拒否する。

- [plot_a2_certification.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:28) の schema 定数を legacy/current profile に分ける。受理する組は次の二つだけとし、v3 cert + full-v4 manifest などの交差や `paper-story-a2-raw-manifest/v4|v5` partial 系は明示的に拒否する。

  - legacy: `paper-story-a2-certification-result/v3` / `paper-story-a2-raw-manifest/v3` / `paper-story-a2-cell-result/v2`
  - current full: `paper-story-a2-certification-result/v4` / `paper-story-a2-full-raw-manifest/v4` / `paper-story-a2-cell-result/v3`

- [plot_a2_certification.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:92) は bytes pin を先に検査した後、cert/manifest の組を一括 routing する。`expected_hashes` は exact key set `{certification, raw_manifest}`、各値は lowercase 64 hex とし、`None`・空値・片側だけを拒否する。

- [plot_a2_certification.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:530) に `--certification-sha256` と `--raw-manifest-sha256` を追加する。既定値は現在の frozen 2 pin のままにし、CLI は常に二つの値から `expected_hashes` を構築する。新成果物を既定 pin のまま指定すれば必ず SHA mismatch になるため、pin 無しの新成果物受理経路は生じない。再現 argv にも両 pin を記録する。

- current certification の `policy_bytes_base64` を strict base64 decode し、`policy_sha256` と照合する。producer の [load_policy:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:339) と同じ validator を一時 file 経由で使い、policy の workload/cell exact shape を再検証する。これにより repository の将来の live policy ではなく、成果物自身が pin した policy から次を導出できる。

  - workload order、label、rratio: policy `workloads`。[producer:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:480)
  - cell order、role、genome: policy `cells`。[producer:497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:497)
  - measurement root の省略値: `durable_measurement_base / certification.attempt_id`。
  - cert `cells[]` は policy の id/workload/role/genome と exact order で一致させる。

- legacy 分岐では [plotter:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:32) の現行 `WORKLOADS` / `CELLS` を `LEGACY_*` として残し、10-file closure と順序を変えない。任意の legacy bytes pin を与えた場合にも embedded policy から別 cell を採用しないため、旧受理集合を広げない。

- [plotter:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:133) の current full closure は exact 12 files とする。

  - 4 raw cell
  - 2 WAL
  - 2 campaign lock
  - 2 campaign claim
  - 2 `receipts/condition-gate-<workload>.admissions.jsonl`

  producer がこの閉包を生成する箇所は [producer:3597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3597) と [producer:3688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3688)。不足・余剰・非 canonical path・非 SHA 値を拒否する。

- D1198 の直接 boolean は cert/manifest に存在しない。根拠は次の chain なので、[plotter:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:169) の current 入力 loader で receipt 2 本を hash 検査して読む。

  - gate 実行と `use_class="paper"`: [producer:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:682)
  - campaign より前の receipt 保存: [producer:3441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3441)
  - receipt の `use_class="paper"` / `admitted=true` exact 検査: [producer:962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:962)
  - manifest pin と再検査: [producer:4044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4044)
  - tracked materialization: [producer:4479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4479)

- current raw/WAL/cert/receipt 間では、既存検査に加えて次を要求する。

  | 検査面 | legacy | current full |
  |---|---|---|
  | bytes/schema | 現行 pin と exact v3/v3/v2 | CLI pin と exact v4/full-v4/v3 |
  | authority identity | study/attempt/protocol/current_pin | 同じ 4 項目 + embedded policy hash/protocol |
  | closure | exact 10 files | exact 12 files |
  | raw/WAL | build_attempt、variant、samples、median、CV | legacy 全項目 + build-start/admission の `src_token` |
  | source identity | field 無し | receipt/raw/WAL/cert の token 一致、stock=`stock`、adopted≠`stock`、cert status=`bound` |
  | science | median/effect 再計算 | 同じ再計算 |
  | scheduler claim | request suffix、host、時刻、campaign | 同じ |
  | correctness | 1 legacy + 5 performance、全 cell certified | 同じ |

  current の token authority は [producer:2477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:2477) と [producer:3132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3132) に対応させる。

- [plotter:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:326) の caption は workload/cell/adopted backoff を data から組み立てる。[plotter:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:344) の固定 D1198 文を除き、legacy は従来文を byte-exact に維持、current は「manifest-bound admitted paper receipts を全 policy cell で確認した」と記す。

- [plotter:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:451) の provenance `gate_note` も `data["gate_note"]` から出す。描画ループと effect crosscheck の [plotter:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:252)、[plotter:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:351) は `measurement_conditions.workloads` と cells から順序を得る。

- 新版には「producer が full certification 全体を evidence から exact 再導出した」という対応 field がない。これは既知の T-2366 欠落であるため、plotter 自身の WAL/raw/cert median・effect crosscheck は残し、producer の materialize 成功を全 report 再導出の証明とは扱わない。

- [test_plot_a2_certification.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:24) 以下の legacy fixture/test は保持する。追加 test は current positive、schema 交差、partial schema、12-file closure、receipt missing/hash/canonical/admitted、四者 token mismatch、source role mismatch、policy/cert cell mismatch、動的 gate caption、CLI explicit pin と旧 pin fallbackを対象にする。[test:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:338) の CLI helper と [test:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:375) の reproduction argv 期待値は hash 引数込みへ更新する。frozen hash/caption test [test:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:400) と [test:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:432) は変更しない。

## 単位 B のプラン

受理側: policy の bounded relative `tracked_destination` を未存在の新 leaf へ変え、新 attempt を同じ protocol identity で materialize できるようにする。  
拒否側: 旧 frozen destination、既存 destination、absolute/`..` path、3 本目の policy は引き続き拒否する。

推奨宛先を `output/insights/2026-09-07_t2364-paper-story-a2-certification` と確定する。この path と attempt `t2364-20260907a` は静的確認時点で未存在。

[producer:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:290) の `_protocol_preimage` は `tracked_destination` と `durable_measurement_base` を含まない。[producer:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:551) では raw policy bytes と protocol preimage を別々に hash する。静的再計算結果は以下。

| pin / path | 現在 | 変更後 | 編集 |
|---|---|---|---|
| production `tracked_destination` | `…/2026-08-24_paper-story-a2-certification` | `…/2026-09-07_t2364-paper-story-a2-certification` | [policy:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.v2.json:9) |
| test fixture destination | 旧 path | 新 path | [test:984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:984) |
| policy bytes SHA-256 | `42bfee487c9e517b9876fbb41f8a4b4de53266ced1543263087bbd637ecc897e` | `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` | [test:1763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:1763) の2 assertion |
| protocol SHA-256 | `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4` | 不変 | [test:1771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:1771) は変更しない |
| frozen cert 内 `policy_sha256` / `policy_bytes_base64` | 旧値・旧 path | 不変 | frozen [certification.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-08-24_paper-story-a2-certification/certification.json:1) |
| frozen plotter test の path/hash pin | 旧成果物 | 不変 | [plot test:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:400) |

`git grep` の path 検索で得たその他の一致は、凍結 figure provenance、results、過去 README/decisions/worklog が旧成果物を指す履歴参照であり、変更対象ではない。値検索で得た live golden は [test:1768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:1768) と [test:1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:1770) の二箇所だけである。

変更直後に赤になる既存 node は `test_p1_a2_default_policy_bytes_and_protocol_are_unchanged`。張り直す golden は同 node の policy raw SHA と `policy.bytes_sha256` の二 assertionで、protocol golden は張り直さない。fixture path [test:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:987) は既存 test を赤にしないが、live policy と同じ宛先を試験するため更新する。

`orchestrator/campaign/paper_story_a2_certification.py` は編集不要。loader は任意の bounded relative destination を既に許可し [producer:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:370)、materializer はその値を fresh-leaf 検査へ使う [producer:4448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4448)。

## 単位 C の投入手順

親が実行する外部 command の順序は `submit（内部で preregister → qsub submit）→ finish-group → collect`。standalone `preregister` を先に実行すると、submitter が同じ attempt root を `exist_ok=False` で再作成して失敗する。[submitter:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:231)

1. 単位 A/B を取り込み、commit 後の投入専用 HEAD で次を実行する。

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema

tools/pegasus/submit_paper_story_a2_certification.sh \
  --attempt-id t2364-20260907a \
  --ccbench-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/external/ccbench \
  --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps
```

内部 preregistration の実 argv は次だが、親は個別実行しない。

```bash
python3.10 -B -m orchestrator.campaign.paper_story_a2_certification \
  preregister \
  --attempt-id t2364-20260907a \
  --current-pin 511c953
```

`--attempt-id`、`--ccbench-root`、`--dependency-prefix-source` は submit mode では必須。[submitter:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:57)、[submitter:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:166)  
`--policy` は省略し、canonical A-2 policy を選ばせる。D1644 経路は clean canonical CCBench を受け取り、isolated checkout に patch を当て [producer:599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:599)、その patch 済み木で src_token を解決する [producer:3441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3441)。したがって両 path 引数は省略できない。

2. 二つの request が terminal になった後、同じ login node の同じ HEAD で実行する。

```bash
tools/pegasus/submit_paper_story_a2_certification.sh \
  finish-group \
  --attempt-id t2364-20260907a
```

finish mode では CCBench/dependency 引数は不要で、preregistration から `attempt_root` と pin を再取得する。[submitter:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:111)

3. `receipts/acquisition.json` ができた後に materialize する。

```bash
python3.10 -B -m orchestrator.campaign.paper_story_a2_certification \
  collect \
  --attempt-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a \
  --current-pin 511c953 \
  --acquisition-receipt /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/receipts/acquisition.json \
  --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema
```

投入前の要求は次のとおり。

- Pegasus login node、`gen_S` が ENA/ACT、同 study の可視 request が無いこと。[submitter:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:101)、[submitter:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:142)
- repository の tracked tree が clean で、submit 時 HEAD を以後維持すること。[submitter:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:159)
- `external/ccbench` は initialized submodule、HEAD `511c9538e4e8efa54b45cda62e72389ed3b706ec`、tracked clean、symlink でないこと。[submitter:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:177)
- 親 repository の submodule gitlink も同 commit を指すこと。静的確認時点の `git submodule status` は先頭空白で一致している。
- dependency prefix `/work/1/SFC/tanab/izanagi-a2-deps` は実 directory、非 symlink。
- 新 tracked destination と attempt root が存在しないこと。

投入から collect まで tracked file や HEAD を変更しない。少なくとも compute preflight までは共有 repository の HEAD と clean 状態を機械検査する [producer:4576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4576)。jobs 終了後も finish-group は job body bytes を submission receipt と照合する [producer:1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1223)。ただし任意の tracked file に対する「終了後から collect まで」の全 HEAD barrier は実装されていないため、運用上も固定する。

所要は queue 待ち + 各 request 最大 6 時間。二 workload は別 request なので並走可能であり、12 時間直列とは限らない。queue 待ち時間は投影資料から確定できない。

失敗時の attempt-id 扱いは次のとおり。

- preregistration 前の queue/tool/path 検査失敗: root は作られないので同 ID を再利用可能。
- preregistration 後の submit/job 失敗: `automatic_retry=false`、attempt/raw/receipt は create-only のため新 ID が必要。[producer:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:821)、[producer:873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:873)
- request がまだ terminal でないだけの finish-group 失敗: receipt 未作成なら同 attempt に finish-group を再実行可能。
- collect が publish 前に失敗: staging は削除されるので、identity/policy を変えず原因を直せる場合は同 attempt で再実行可能。destination が既に publish 済み、または測定自体を取り直す場合は新 ID が必要。

## 親 brief への反論

- [brief:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-09-07_t2365-a2-plot-schema/s1-brief.md:22) の D1693 要約は過度に一般化されている。実際の D1693 は A-6 の FetchContent configure 文法とその golden 張り直しに関する裁定であり [decisions:51632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/docs/decisions.md:51632)、A-2 destination 変更そのものの裁定ではない。旧成果物を変更しない結論は正しい。
- [brief:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-09-07_t2365-a2-plot-schema/s1-brief.md:63) の「byte hash golden 1 本」は値としては一つだが、assertion site は二箇所である。さらに path-based fixture pin [test:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:987) の更新も必要。
- [brief:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-09-07_t2365-a2-plot-schema/s1-brief.md:66) の P1-3 は一部不可能。measurement root、raw-manifest sibling、workload/cell は選択済み certification から導出できるが、最初にどの certification を選ぶか自体は成果物から自己導出できない。旧 certification を既定 seed として残すか、`--certification` を明示する必要がある。
- D1198 適用状態を表す単一成果物 field は存在しない。`GATE_NOTE` は cert field から直接コピーできず、manifest-bound condition admission receipt の chain から導出する必要がある。
- [brief:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-09-07_t2365-a2-plot-schema/s1-brief.md:84) の投入 command は不完全。submit mode は `--ccbench-root` と `--dependency-prefix-source` の両方を要求する。
- P1-1、P1-2、P1-4、および materialize の fresh-leaf 問題の認識には反論なし。

## 実装子への申し送り

- 単位 A の所有 file は `tools/plotting/plot_a2_certification.py` と `orchestrator/tests/test_plot_a2_certification.py` のみ。
- 単位 B の所有 file は `orchestrator/campaign/paper_story_a2_certification.v2.json` と `orchestrator/tests/test_paper_story_a2_certification.py` のみ。producer `.py` は触らない。
- 単位 C は実装子を持たず、親が投入する。
- A/B の編集 file は交わらないため並行実装可能。ただし B を commit して新宛先を確定してから submitし、A を取り込んでから新成果物の図を生成する。
- 単位 A の期待赤は、新 v4/full-v4/v3 positive、schema-cross、receipt/source-token、explicit CLI pin、動的 gate-note の新規 test。既存 legacy test は変更後も維持対象。
- 単位 B の既存期待赤は `test_p1_a2_default_policy_bytes_and_protocol_are_unchanged` 一 node。fixture destination 更新自体は既存 test を赤にしない。
- 本段ではテストを実行していない。