結論は静的 **NO-GO 推奨**です。must-fix 候補の real/refuted 裁定は親に委ねます。probe・pytest・変異は実走していません。

レビュー中に `stage4-ruling.md` が 93 行から 110 行へ更新されたため全文を再読しました。最終確認時点では probe SHA-256 `faf18b0b...e817`、裁定 SHA-256 `f80b84c5...21917` で安定しています。

## 総括

**(1) must-fix 所見（親裁定前）**

1. **任意 path・symlink・共有名への receipt 書き込みにより I1/I4 を迂回できる。**  
   [liveness_probe.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:116)、[liveness_probe.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:125) — `--keep` は root 制約がなく、既存 `liveness-receipt.json` を追随・truncate する。最終ファイルを production authority への symlink にすれば authority 自体を上書きできる。同じ `--keep` を使う旧・新 probe も後勝ちで上書きする。F100/F115/F121/F128 型。  
   **成果物影響:** authority が壊れれば公開 ledger の台帳参照が全停止し、競合上書きなら receipt の event hash・counter・wire が別 run の値へ差し替わってレポートが誤った証跡を参照する。

2. **負 control が「重複 commitment 拒否」以外の全 ledger 例外を C-d PASS にする。**  
   [liveness_probe.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:90)-[93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:93) — disk-full、fsync、Git 観測、CAS、runtime 破損等の `RefluxOriginLedgerError` も `duplicate_rejected=True` になる。  
   **成果物影響:** distinct gate を観測していなくても receipt の `checks.C-d=true` と全 PASS が記録され、ledger の受理集合を実証したというレポートが偽緑になる。

3. **外部 preview JSON と実 driver 出力の束縛がない。**  
   [liveness_probe.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:118)-[122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:122) — `passed=true` と任意の小文字 hex 64 桁だけで通り、存在する `working_diff` の SHA-256 を再計算しない。JSON は wire も持たないため、`--wire` と preview の生成入力も束縛されない。重複キー・余分なキーも許す。  
   **成果物影響:** fabricated/stale preview でも receipt の C-c2 が true になり、任意 digest と無関係な wire が「実 driver 出力」として台帳・レポートへ参照される。

4. **preview を無制限に全読みし、login 可という環境裁定を満たさない。**  
   [liveness_probe.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:118) — 未使用の巨大 `working_diff` も `read_text` と `json.loads` で全保持する。[pegasus-runbook.md:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/docs/pegasus-runbook.md:358) の分類では入力 hard cap なしは `unknown`、すなわち `dispatch-required` である。  
   **成果物影響:** login で OOM・停止すれば receipt が欠落または不完全になり、D96 分割 wave の根拠レポートを生成できない。

5. **一時 repo の基底が `TMPDIR` 任せで、本 repo 外を保証しない。**  
   [liveness_probe.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:80)-[84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:84) — 通常例外では context manager が消すが、`TMPDIR` が repo/`output` 配下なら実行中は nested repo が現れ、SIGKILL 等では残る。  
   **成果物影響:** real output snapshot の受理集合へ一時 `.git`・authority・runtime files が混入し、受入レポートを F115 型の偽赤にする。

6. **probe 自身の Git bootstrap に timeout がない。**  
   [liveness_probe.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:53)-[56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:56) — ledger 内部の Git は 30 秒 timeout を持つが、この5系統の `git init/config/add/commit` は無期限。中止後に残れば共有 receipt へ遅延書き込みできる。  
   **成果物影響:** receipt・判定表が永遠に確定しないか、再投入後に旧 run の receipt が上書きし、参照する event hash が入れ替わる。

7. **失敗理由は表示されるが、未実行 check をすべて FAIL と偽っており構造化シグナルが不正確。**  
   [liveness_probe.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:108)-[124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:124) — preview parse error等でも C-a〜C-e を一律 `FAIL` とし、`NOT_RUN`、失敗段、分類済み reason code を持つ JSON artifactを返さない。  
   **成果物影響:** レポート上の C-a〜C-e 値が「未実行」から「ledger gate が失敗」へ変わり、次の修正先・失敗参照を誤らせる。

**(2) nit**

- [liveness_probe.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:129) は129行あり、[stage4-ruling.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/stage4-ruling.md:109) の100行以内を超える。成果物値への直接影響を書けないため nit。
- [liveness_probe.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:54)-[56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:56) は caller の `PATH` から `git` を解決する。通常の信頼済み実行環境なら許容可能だが、実行体 provenance は固定していない。
- レビュー中に `stage4-ruling.md` が更新された。最終 hash へ再束縛済みだが、親は別 hash の成果物へ本レビューを流用しないこと。

**(3) I1〜I6**

| 不変条件 | 静的判定 | 根拠 |
|---|---|---|
| I1 production authority 非接触 | **未保証** | ledger call graph は temp fixture に閉じ、`_production_store()` 到達はない。一方、line 125 の任意 symlink 出力で authority を上書き可能。 |
| I2 名乗り上限 | **守る** | docstring・stdout・receipt は ledger liveness と vocabulary-only outcome に限定。P3充足等は名乗らない。 |
| I3 `distinct_candidate_count=1` | **守る** | [liveness_probe.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:99)-[103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:103)。 |
| I4 既存 tracked file 非編集 | **現 snapshot は守る／実行時は未保証** | `git status` は wave 配下の未追跡5点だけで tracked 差分0。ただし任意 `--keep` と repo内 `TMPDIR` が実行時境界を破れる。 |
| I5 fixture seam・非production明記 | **守る** | [liveness_probe.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:4)、[84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:84)。 |
| I6 独立 commitment/identity 実装 | **守る** | canonical・origin/cell・salted preimage は [23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:23)、[38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:38)-[50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:50) で独立。禁止 helper は呼ばない。 |

追補 I7 の vocabulary-only 表記も docstring・stdout・receipt で守られている。

**(4) 副作用の静的棚卸し**

- 一時領域へ書くもの: nested Git repo、fixture authority、Git object/index/config、`.git/izanagi/reflux-origin-ledger/v2/` の lock・runtime head・origin event。
- 永続書き込み: `--keep/liveness-receipt.json`。既存ファイルを上書きし、symlinkを追随する。
- 起動する外部 process: `git init`、`git config` 2回、`git add`、`git commit`、および ledger の authority 観測用 Git subprocess。
- 正規 Git command からのネットワーク経路、pytest、build、bench、campaign 実走、qsub は静的にはない。
- preview 内容に対する `eval`、dynamic import、shell展開、path連結はない。`working_diff` 中の指示文字列は使用されない。
- cwd は fixture ledger の選択へ影響しないが、相対 `--preview-json`・`--keep` の解決には影響する。

**(5) fail-closed 性**

**不合格。** preview parse error、Git 不在、positive path の通常例外、一時領域不足の多くは rc=1 へ倒れる。しかし、負 control 中の任意 `RefluxOriginLedgerError` は C-d PASS に化けるため明確な silent green がある。さらに bootstrap Git は timeout せず、外部 preview は無制限読み込み、出力は共有名への非原子的上書きである。したがって land 前に少なくとも所見1〜6の親裁定と是正が必要です。