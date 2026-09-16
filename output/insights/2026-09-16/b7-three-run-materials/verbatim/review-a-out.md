## 数値の検算

- **重大度: should-fix** — [§2.5、326行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md:326) の「この対は **2 度**解析されている」は、同段落と一次資料が記録する **3 度**（9/13、9/14、9/15）と不一致。
  **放置時の影響:** 下流の執筆で解析回数が1回過少になる。

- **重大度: nit** — §3 限定6、364行の「**3 行**をプールした効果」は、主表の **4 行・4対比較**と不一致。「3走行」との混同。
  **放置時の影響:** 表の比較単位の説明が実数とずれる。性能値・受理集合は変わらない。

それ以外の照合結果：

- 生標本 **8 arm × 5＝40値**は、値・記載順とも一致。[T-1998] は `result.json` と WAL の双方とも一致。
- median 8件、効果4件、abort率8件は一致。効果を再計算し、A-2/A-6 の小数点以下4桁への丸め、[T-1998] の全桁転記、符号・桁区切りを確認。
- A-2 の標本標準偏差・CV・95% CI半幅は各4件一致し、標本からの再計算も一致。A-6 の母標準偏差/median は丸め後 **1.18%／1.06%**。[T-1998] の `cv` 2件も記録と一致。
- 共通設定、genome、掲載された commit・digest・host・request・日時・schema は指定資料と一致。復号した `performance_common` も両 attempt で一致。
- `result.json` は **23 key**、WAL の `verify_done` は **8件**、provenance の `external_inputs` は **12件**。
- [T-1998] の時刻差は **707秒**。記録された Elapse **712秒**との差 **5秒**も稿の説明どおり。

## field 名と JSON path

- **重大度: should-fix** — [§4.2、471行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md:471) の「同名 field」は正確でない。実在する名前は `attempt_id`、`study`、`schema_version`、`source_commit`、`protocol_sha256`、`policy_sha256`、`request_ids`。`attempt`・`schema`・`request` という同名のトップレベル field はない。
  **放置時の影響:** 下流の転記・抽出が存在しない JSON key を参照する。

その他の主要 field は実在する。WAL 内の正確な path は `payload.tps`、`payload.cv`、`payload.unstable`、`payload.leading_indicators.abort_rate`、`payload.verdict`、`payload.certified`、`payload.anomalies`、`payload.workload.tag`。`bench_done`／`verify_done` は `stage` の値である。

## SHA-256 の再計算

再計算した範囲に不一致は**無い**。

- §4.1：射影対象の **10ファイルすべて一致**。
- §4.3：`result.json`、`reservation.json`、campaign WAL の **3件すべて一致**。
- 両 certification の `policy_bytes_base64` を復号し、公開 `policy_sha256` とも一致。

**未検算:** §4.1 の raw manifest 2ファイルと、§4.3 の campaign lock は指定された読み取り対象外なので、現物のハッシュを再計算していない。lock の掲載値と `result.lock_sha256` の一致は確認した。`artifact-manifest.json`／`COMPLETE.json` への帰属も対象外のため未確認。

## 引用の逐語性

- **重大度: should-fix** — [§1.4、190行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md:190) の事前登録§9の引用は、途中の次の一文を省略表示なしで削除して接続している。

  > 版はどちらも GNU 11.4.0 だが、版の一致は header 閉包の一致ではない。

  **放置時の影響:** 下流が非連続の抜粋を逐語引用として再利用し、compiler版とheader閉包の区別を落とす。

ほかに§2.4の事前登録§7引用は、箇条書きの接続と末尾句点の省略があり、原文そのままの転記ではない。意味の変更は確認しなかった。指定資料にない裁定文・既存稿からの引用は逐語性を確認していない。

## 出所の帰属

- **重大度: should-fix** — [§1.4、188行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md:188) から§4.2への参照は、**arm別 source bytes digest の束縛**と **repository/gitlink の束縛**を混同している。`reservation.source_binding` が持つのは `repository_commit` と `ccbench_gitlink_commit` だけ。arm別 digest は WAL の `stage="build_start"` の `payload.build_admission.source.source_bytes_sha256` にあり、投入時の一致の記述は T-2557 README §1 にある。
  **放置時の影響:** arm別source identityの根拠を、必要なdigestを持たない記録へ誘導する。

A-6 の abort率を事後解析へ帰属させる点、[T-1998] の正しさを WAL へ帰属させる点、producer の `complete` と consumer の `accepted` を分ける点は正しい。

## 入口 README の 1 行

不一致は**無い**。

本文を数え、**限定19件、3走行、4対比較、8 arm**を確認した。稿のファイル名、対象attempt、事前登録v1、判定列の `observed-positive`／`reject`／`accepted` と producer `complete` の区別も本文と整合する。

## 総括

**主要な性能値・40標本・再計算した13ファイルのSHA-256に不一致は無い。** 修正対象は解析回数、表の行数、field名、引用の無表示省略、source identityの参照先。射影外の資料は未検証として区別した。ファイル変更・測定・テスト実行は行っていない。