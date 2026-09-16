# 段 4 裁定 追補 5 (erratum-5) — 凍結 evidence の `pbs_job` binding を歴史値へ移す

**正本の関係:** 追補 1〜4 に続く。衝突したら**番号の大きい追補が優先**する。

**発生:** 単位 B は追補 4 を閉じたが、**所有外の凍結 evidence 契約テストで赤**になり、
禁止に従って変更せず報告して止めた。**B の判断は正しい。**

赤の実体 — `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1263-1275`
`test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`:

- 凍結 evidence `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` は 8 path を束縛する。
  `driver` / `verifier_module` / `policy` の 3 つは**歴史値**として扱われ
  (`binding == historical` かつ `binding != current`)、残る 5 つは
  **`binding[key]["sha256"] == current_sha`** を要求する。
- `pbs_job` = `tools/pegasus/silo_ladder_rung1.sh` はその「現行と一致」側にあった。
  単位 B が同 shell を付け替えたので不一致になった。

## 親が実測した 2 値

| 値 | sha256 | 出所 |
|---|---|---|
| 歴史値 (凍結 evidence の `pbs_job`) | `318c2b12fb3fa71b3587c81f201db640393d2adae2214fd6aca4a9222ab2f57c` | 凍結 evidence を直接読んだ |
| 変更前 main の同 shell | `318c2b12fb3fa71b3587c81f201db640393d2adae2214fd6aca4a9222ab2f57c` | `git show main:tools/pegasus/silo_ladder_rung1.sh` |
| **変更後の同 shell (現行値)** | `117b3bb4a4789b00b2b2e8335ee78a6f329125e26aa42c6002283fd0ed894f0e` | B の worktree の現物 |

**歴史値と変更前 main が完全一致する** — つまり凍結 binding はこれまで live file を追いかけていた。

**親は B の差分を現物で確認した。** 変更は `silo_ladder_rung1.sh:440-455` の 2 箇所だけで、
`gflags_source_path` / `glog_source_path` を読む inline python を staging root の解決へ置き換えた
ものである。`*_expected_head` の読み、HEAD 照合、dirty 拒否、build/install、prefix 供給は
いずれも残っている。**現行値 `117b3bb4…` はこの差分を親がレビューしたうえで pin する。**

## 追補の決定

### (1) D200 の先例どおり、**凍結 evidence は 1 byte も書き換えない。検査の根拠だけを移す。**

D200 の逐語:

> 凍結 evidence は過去の走行が使った bytes の記録であり、**書き換えは歴史の改竄**である。
> したがって動かすのは検査の根拠だけとする。
> 「凍結 evidence と一致」を検知の根拠にしたままだと、共有 policy を正当に更新するたびに
> 歴史記録の側を書き換える圧力が生まれる。現行 bytes の明示 pin へ根拠を移すことで、
> **検知力を保存したまま**この圧力を断つ。

`pbs_job` を `policy` と同じ扱いにする。

- `historical_sha256_by_key` に `"pbs_job"` を足し、値は
  **`318c2b12fb3fa71b3587c81f201db640393d2adae2214fd6aca4a9222ab2f57c`**。
- あわせて `policy` と同型の**現行 bytes pin** を置く。
  **`117b3bb4a4789b00b2b2e8335ee78a6f329125e26aa42c6002283fd0ed894f0e`**。
  診断文は `policy` の既存文言に倣い、「意図的な更新にはこの golden の更新が要る」と書く。
- **検知力を落とさない。** 移設後も「任意の 1 byte の変更で赤になる」が成立していること。
  `binding != current` の assert も残す。

### (2) 定数の置き場所

`policy` の 2 定数は `orchestrator/tests/pegasus_policy_expected_goldens.py` にある。
`pbs_job` の 2 定数は **同 file には置かない** (同 file は policy 専用の docstring を持つ)。
`test_silo_ladder_rung1_evidence.py` の module 先頭に、既存の
`EXPECTED_HISTORICAL_VERIFIER_MODULE_SHA256` / `HISTORICAL_SILO_EVIDENCE_IDENTITY` と
**同じ場所・同じ書式**で置く。

### (3) 所有の追加

`orchestrator/tests/test_silo_ladder_rung1_evidence.py` を**単位 B の所有**に足す。

### (4) 値を自分で算出してはならない

**親が上の 2 値を与える。実装子は編集後 file から sha256 を算出して埋めてはならない** (D200)。
照合に使うのは構わないが、一致しなければ実装が誤りなので報告して止める。

### (5) floor 全走の赤は本追補の対象外

B が報告した `test_pegasus_floor_tools.py` の全走失敗
(`test_floor_time_resolver_bound_counts_matches_not_lifetime_history`、
`test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]`) は、
**選択再走で 4 passed / rc=0 になっている**。時間境界を検査する node であり、
login node の負荷に依存する**非帰属赤の疑いが濃い**。

**単位 B はこれに触らない。** 親が段 6 の受入全走で `DW-O18` に従って判定する。

### (6) 段 8 候補 (追補 3・4 に追加)

**凍結 evidence が「現行 bytes と一致」で束縛している path は、path 検索では出るが
「凍結 pin」とは読めない形をしている** (evidence は `output/` 配下の JSON で、
test 側は key 名で引いている)。段 1 の pin 閉包で
「編集する path が凍結 evidence の binding に載っていないか」を引く手順が要る。
本 wave では追補 3 (行番号 pin)・追補 4 (本数 pin)・追補 5 (evidence binding) の 3 回、
実装後の実走で初めて出た。
