## 所見対応表 (closed / partial / regressed)

行番号はすべて [fix 後の現物 launcher](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/run_screening_liveness.sh) を指す。v1 との diff で判定した。

| 所見 | 判定 | 対応行・残件 |
|---|---|---|
| A-R1 | closed | L10–16 で PBS_JOBID 必須検査を削除。L87 で一意 scratch を確保し、失敗は rc=2。 |
| A-R2 | closed | L63、71–73。root 名前除外を廃止し、数値 UID 比較と PID/PPID=2 除外へ変更。裁定2に一致。 |
| A-R3 | closed | L9、12–15 で時刻・実行 identity を記録。PBS_JOBID 原値は出さず、実 job 帰属を dispatcher 証拠へ委ねる裁定1・5による閉鎖。 |
| A-R4 | closed | L13、63、71。表示名・幅20・`$USER` に依存しない。 |
| A-R5 | partial | L65 の注記と L79 の拒否理由は適切。「別 job 同居」と断定しない README 記述は親側に残る。 |
| B-R1 | closed | A-R1 と同じ。欠落する PBS_JOBID への依存を解消。 |
| B-R2 | closed | L103 に `-I -B -u`。 |
| B-R3 | partial | L89–90、117–121。cleanup は Git 登録を撤去しない。一覧は cleanup 前であり、終了後の親による再検査・必要な復旧は残る。 |
| B-R4 | partial | L29 の未存在検査は維持。原子的予約ではなく、検査後の root 作成競合は残る。 |
| B-R5 | partial | L113、116、118 に検査 rc を追加。検査失敗でも L121 は CLI rc を返すため、成功判定には親の証拠照合が必要。 |
| A should-fix：PBS_JOBID 原値 | closed | A-R3 と同じ。裁定1によって出力責務を変更。 |
| A should-fix：表示幅依存 | closed | L13、63、71 で解消。 |
| A should-fix：README の解釈・A-5 環境同一性 | partial | L57 で Python 実体、L65 で UID の限界を記録。README と A-5 との同一性確認は未確認。 |
| A nit：identity | closed | L14–15 に HEAD・pin・cwd・uid・PID・USER・HOME。 |
| B should-fix：`-u` | closed | L103。 |
| B should-fix：Python 選定時の環境 | closed | L32–44 の PATH 固定・unset 後に L46–57 の選定を実施。 |
| B nit：tree 検査 rc | closed | L113、116、118。CLI rc 保持も維持。 |

**裁定1〜5と食い違う閉じ方はない。** A の当初要求「PBS_JOBID を届ける」「root を除外する」は、親の裁定で明示的に変更されている。regressed は認めない。

## 回帰

- hostname、HEAD/pin、tracked-clean、絶対かつ未存在の root、`/scr`、GIT_* 消去は L16–30 に維持。
- PATH・prefix・proxy・official root・lock の設定は裁定どおり。scratch 名の変更以外に値の意図しない変更はない。
- L87 の `mktemp` は `|| fail 2` で捕捉され、ERR trap を誤発火させない。EXIT trap 登録は作成成功後の L90。
- L13 の `id -u`、L63 の `ps` が失敗すれば ERR trap により rc=2。これは前処理失敗として妥当。
- `ps -eo uid,pid,ppid,pcpu,pmem,etime,comm --sort=-pcpu` は procps の列指定として整合する。awk は UID=$1、PID=$2、PPID=$3、CPU=$4 でずれがない。
- pgrep の rc=1 許容・自 PID 除外・CLI 前の rc=3 は L66–81 に維持。空の awk 結果自体はエラーにならない。
- L105–108 の ERR trap 解除、`set +e`、CLI rc 保存、および L121 の返却を維持。終了後検査の失敗は CLI rc を上書きしない。
- CLI → 終了後検査 → EXIT cleanup の順序を維持。
- clone・build の直接実行、監視、sleep loop、network probe、関門介入の追加なし。CLI 起動は1回。**117行 → 121行**で上限以内。

軽微な堅牢性上の留保として、追加された L14 の `$(pwd -P)` は `printf` の引数なので、その失敗が外側の終了 rc へ確実に伝わる構造ではない。正常な cwd では問題ないが、cwd 取得失敗時の identity 出力保証は弱い。今回の投入を阻害する所見とはしない。

`bash -n` は **rc=0**。現物の SHA-256 は以下で、fix 報告と一致した。

```text
009a4d8a21c5d1c8694c40343b1079f286aa1bc6101cfa28f9f0ac95a48b888f
```

## clean env での到達性

dispatcher の保持キーと環境構築を確認した。**allowlist 外の必須環境変数への依存は残っていない。**

- PBS_JOBID は参照しない。
- USER・HOME は L15 の `${USER:-}`・`${HOME:-}` による記録だけで、欠落しても nounset で停止しない。
- SELF_UID は `id -u` で取得する。
- TMPDIR・IZANAGI_*・prefix・proxy は launcher 内で設定する。
- 初期コマンドは継承 PATH、Python 選定以降は L33 の固定 PATH を使う。

したがって、clean env による既知の必然的停止は解消した。Python 3.10、必要コマンド、prefix、書込可能な `/scr` 等が計算ノードに存在することは未実測であり、CLI 到達を実証したわけではない。

観測の意味は、ユーザー名による「他ユーザー」から、namespace 内の数値による「他 UID」へ変更された。L72 の表示名と L65 の注記もこの変更に一致する。

## userns での述語

親の実測前提では、自 process の `ps uid` と同じ namespace 内の `id -u` が一致するため、L71 の自己除外は成立する。他ユーザーと host root の 65534 は除外されず、裁定どおり拒否候補に残る。

提示された userns 構成は PID namespace の変更ではないため、PID/PPID=2 による kernel thread 除外は UID mapping に影響されない。L73 は指定された述語を実装している。

ただし、計算ノードの `/proc` 可読性と `ps` の実際の成功は**未実測**。読取制限によって `ps` が非ゼロ終了すれば L63 で rc=2。部分的な不可視性が成功扱いになる場合まで、このコードは検出しない。

拒否は別 job の存在証明ではなく、通過も全実行期間の単独性証明ではない。

## 出力

必要な分類材料は揃っている。

| 内容 | 行 |
|---|---|
| 段名・時刻 | L5、各 `stage` 呼出し |
| 開始 identity | L12–15 |
| Python realpath | L57 |
| 単独性観測・拒否理由 | L60–79 |
| 設定環境値 | L98–100 |
| `-I -B -u` と exact argv | L103–104 |
| CLI rc | L111 |
| 終了後 tree 検査 rc 3件 | L113、116、118 |
| root 一覧・終了時刻 | L119–120 |

L4 で stderr を統合し、`-u` は Python 出力のバッファリング問題を軽減する。ただし子 process 間の厳密な時系列や、WAL・dispatch result・receipt を要する失敗分類まで stdout 単独で保証するものではない。

## GO / NO-GO

**GO — 指定された1回の投入に進むための静的レビューとして。**

必須修正は閉じており、新たな投入阻害要因は見つからない。実行成功や成果物の緑判定は未確認で、残る partial は親の終了後検査・証拠照合で扱う必要がある。

## 総括

現物 diff で裁定1〜5への適合を確認した。必須修正は closed、既知の証拠上・運用上の限界は partial、regressed はなし。

実走・編集・commit・job 投入は行っていない。