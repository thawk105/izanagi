結論から言う。現行プランのまま段 4 で P1/P6 を採用してはいけない。blocker は 3 件ある。

以下は静的読解だけの結果であり、pytest・checker・mutation は実行していない。したがって「緑」は主張しない。

## 1. tip 側 checker は一文字で自己無効化できる

深刻度: blocker

根拠:

- プランは tip の `[tools/check_ai_provenance.py]` を実行すると明記している。[s2-plan.md:21](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/s2-plan.md:21>)
- checker は finding がある場合、最終的に `return 1` するだけである。[tools/check_ai_provenance.py:2097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:2097) [tools/check_ai_provenance.py:2113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:2113)
- 必要な最小 diff は一文字で足りる。

```diff
-        return 1
+        return 0
```

これで違反は stderr に表示されても、land は出力を解釈せず rc=0 として通す。正規の全テストを誠実に走らせれば別層で検出され得るが、land 関門自身には検出能力がない。

main 側実行体の deadlock については親の指摘が正しい。

- registry は checker のソース内定数である。[tools/check_ai_provenance.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:148)
- `_audit_history()` はその実行体の `_known_violation_registry()` を読む。[tools/check_ai_provenance.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:1070)
- repo も `__file__` から固定される。[tools/check_ai_provenance.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:29)
- したがって旧 main checker は、tip にだけ追加された known-violation を知らず、その登録 wave 自身を通常 land 経路では通せない。

結論は、**tip 側が正しさゲートを緩める方向、main 側が過剰拒否・deadlock の方向**である。P1 の二択はどちらも不適切である。

成果物影響: main の provenance 受理集合が実質的に旧 land と同じまで広がり、著者・trailer 違反 commit を参照するレポートや台帳が正当化されたように見える。

修正案: checker の実行ロジックを main または別の immutable trust root に置き、tip が変更できるのは検証済みの宣言的 known-violation 台帳だけに分離する。checker 自身を更新する wave には、通常 wave と別の明示的 bootstrap 手順を設ける。

## 2. tip checker の実行は「判定」ではなく任意の副作用を追加し、受理集合を広げ得る

深刻度: blocker

根拠:

- 提案は `shell=False` と `close_fds=True` を指定するだけで、filesystem sandbox はない。[s2-plan.md:22](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/s2-plan.md:22>)
- main の最初の clean 検査は ignored path を列挙しない。[tools/dev_wave_land.py:713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:713)
- ignored target collision の検査は、提案関門より後の `_verify_target_collisions()` で初めて行われる。[tools/dev_wave_land.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:851) [tools/dev_wave_land.py:1893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1893)

したがって tip checker は `git worktree list` 等で main を発見し、衝突する ignored file を消して rc=0 を返せる。この入力は現行 land なら collision で拒否されるが、新関門付きでは削除後に受理される。これは形式的にも「受理集合を狭めるだけ」という [parent-brief-v2.md:67](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/parent-brief-v2.md:67>) の不変条件への反例である。

また `checker.is_symlink() or not checker.is_file()` 型では leaf symlink しか拒否できず、`tools/` 自体が symlink の場合は外部 checker をたどる。プランの symlink テストも leaf だけしか規定していない。[s2-plan.md:91](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/s2-plan.md:91>)

成果物影響: 従来なら拒否された衝突入力が通り、ignored な生証拠・レポート材料が削除または置換された状態で canonical 台帳参照が land し得る。

修正案: audit を main/wave に書けない隔離環境で実行する。少なくとも全 path component の `lstat`/`O_NOFOLLOW` 束縛、checker blob SHA の照合、audit 前後の HEAD・cleanliness・target collision 再照合が必要である。

## 3. P6 は 38 秒ではなく、global lock 内に scheduler の最大待ち時間を入れる

深刻度: blocker

根拠:

- lock は [tools/dev_wave_land.py:1673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1673) で取得され、提案関門はその後、解放は [tools/dev_wave_land.py:1953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1953) である。
- checker は headroom 不足時に `_default_dispatch()` へ入る。[tools/check_ai_provenance.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:1285) [tools/check_ai_provenance.py:1982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:1982)
- dispatch の既定 queue wait は 900 秒、walltime は 40 分、さらに grace 300 秒である。[tools/pegasus/dispatch_compute.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/pegasus/dispatch_compute.py:28) [tools/pegasus/dispatch_compute.py:1630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/pegasus/dispatch_compute.py:1630)
- 親の raw 出力は local budget と memory peak を示すが、38.3 秒という elapsed 値自体を含まない。[prov-baseline.txt:1](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/prov-baseline.txt:1>) [prov-baseline.txt:43](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/prov-baseline.txt:43>)

よって P6 は観測値一件を上限として誤一般化している。8 wave 並行時、1 wave が最大十数分から数十分 lock を占有し、他は `lock-busy` へ落ちる。

提示された「lock 前に監査し、lock 内で tip SHA を再照合」は方向として正しいが、そのままでは証明不足である。

- `_verify_heads()` は再照合時の HEAD が T だと確認するだけである。[tools/dev_wave_land.py:500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:500)
- `_verify_audit()` は申告された A..T commit 列を検証するだけで、checker が何を監査したかは受け取らない。[tools/dev_wave_land.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:932)
- checker は裸の `HEAD` を内部解決し、結果に SHA を出さない。[tools/check_ai_provenance.py:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:850)
- dispatch request も `repo_root` と argv だけで、計算ノードは起動時の live worktree を読む。[tools/pegasus/dispatch_compute.py:1374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/pegasus/dispatch_compute.py:1374) [tools/pegasus/dispatch_compute.py:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/pegasus/dispatch_compute.py:567)

成果物影響: 値を書き換えないまま全 land が滞留し、certified 結果・レポート・spool fragment の canonical 参照が長時間未着地または stale になる。

修正案: audit は lock 外で行い、結果を `audited_tip_sha=T`、trusted checker blob、実行 mode、rc に束縛する。dispatch request にも expected HEAD/blob を入れ、計算ノード側で照合する。lock 内では既存 `_verify_heads()`・`_verify_audit()` と receipt の T を比較する。この束縛があれば、同じ commit SHA は同じ tree を表すため正しさを保てる。

## 4. P3 は「終了した subprocess」にだけ正しい。timeout は赤に定義されていない

深刻度: must-fix

根拠:

| 事象 | 静的な帰結 |
|---|---|
| exec 起動 `OSError` | プランどおり `_Reject(RC_PROVENANCE)` 化すれば拒否 |
| rc=1/2/16、signal/OOM の負 rc | `returncode != 0` なので拒否 |
| 非 UTF-8 stderr/stdout | `_detail()` が `backslashreplace` なので拒否理由へ安全に畳める。[tools/dev_wave_land.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:190) |
| timeout/hang | `subprocess.run` に timeout がなく、赤にも緑にもならず lock を保持し続ける |
| `TimeoutExpired` 等の想定外例外 | `land()` 最上位は `_Reject` しか捕捉しないため JSON/RC 契約外へ漏れる。[tools/dev_wave_land.py:1955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1955) |

checker の local bounded scope 自身も `process.wait()` に timeout がない。[tools/check_ai_provenance.py:1810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:1810)

これは「通ってしまう」fail-open ではない。想定外例外では inner `finally` により lock は解放されるが、structured rejection が失われる。hang では解放にも到達しない。

成果物影響: 違反成果物は受理されないが、land receipt が欠落し、台帳・レポートの終端状態が「拒否」ではなく不明／滞留になる。

修正案: lock 外実行に移したうえで、timeout・process-group 停止・dispatch cleanup を定義し、`OSError`、`TimeoutExpired`、signal、出力上限超過をすべて `RC_PROVENANCE` の structured rejection にする。非 UTF-8・負 rc のテストも追加する。

## 5. pre-FF 配置は新規部分適用を防ぐが、active fold recovery を凍結する

深刻度: must-fix

根拠:

- 通常の赤では、提案位置は FF より前なので main/spool は land 自身には変更されず、lock FD は閉じられる。この部分の P2 は正しい。
- ただし `active_plan` は関門より前に読み込まれ、部分 canonical dirt が許可される。[tools/dev_wave_land.py:1687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1687)
- recovery 本体は提案関門より後の [tools/dev_wave_land.py:1735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1735) から [tools/dev_wave_land.py:1783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1783) にある。
- durable transaction state は canonical 書換え前に作られる。[tools/spool_fold.py:2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/spool_fold.py:2037) [tools/spool_fold.py:2053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/spool_fold.py:2053)

したがって関門が赤だと、main は既に tip、transaction state・canonical・fragment は before/after 混在のまま recovery に入れない。既存テストはまさにこの recovery を保証している。[orchestrator/tests/test_dev_wave_land.py:2041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:2041)

また関門を FF 後へ移す案は安全でない。fragment 0 件なら FF 後にそのまま return し、rollback はない。[tools/dev_wave_land.py:1921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1921) [tools/dev_wave_land.py:1936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1936) rollback は fold 例外内にしかない。[tools/dev_wave_land.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1533)

成果物影響: worklog/decisions/failures canonical と fragment GC が混在状態に残り、main tip とレポート・台帳参照が一致しない。

修正案: initial FF 前の監査成功を tip SHA とともに transaction state へ束縛し、resume はその receipt を再検証して続行できるようにする。旧 active transaction に receipt がない場合の rollback／手動停止方針も明記する。

## 6. stub は現行 64 テストを盲目にする。提案テストは一部だけ救う

深刻度: must-fix

根拠:

- 現行 fixture は `check_docs.py` の成功 stub だけを base commit に入れる。[orchestrator/tests/test_dev_wave_land.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:119)
- プランは同じ場所へ常時 rc=0 の provenance stub を追加する。[s2-plan.md:71](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/s2-plan.md:71>)
- 現行ファイルには静的に 64 個の `test_*` があり、末尾 runner は全 `test_*` を自動収集する。[orchestrator/tests/test_dev_wave_land.py:2866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:2866)

実走していないため緑とは言わないが、静的には、この成功 stub のまま関門呼出しを丸ごと削除しても現行 64 本は差を観測しない。

一方、プランの新規テスト 1〜3を記述どおり実装すれば削除変異は検出できる。

- テスト1は rc=73 が land して期待値と食い違う。
- テスト2は marker が作られない。
- テスト3は二回目が `already-landed` になる。

ただしテスト2は「audit が lock 内」を正例として固定しており、blocker 3 の危険設計をテストで凍結する。[s2-plan.md:87](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/s2-plan.md:87>) また、環境変数内部 bypass、timeout、起動例外、負 rc、非 UTF-8、active transaction、ancestor symlink は未被覆である。

成果物影響: call 削除または内部 bypass が生存すると、provenance 赤 commit が main 履歴と台帳参照へ再び入る。

修正案: lock テストを「audit 中は global lock を取得可能」に反転し、実装前 mutation matrix に call 削除、`returncode` 無視、env bypass、main executor、timeout、`-9`、非 UTF-8、active recovery、ancestor symlink を個別登録する。CLI rc=29とJSONも固定する。

## 7. 「同型の3本目」という一般化と実測根拠が崩れている

深刻度: must-fix

根拠:

- 既存の直接 rc 判定 2 本自体は実在する。[tools/dev_wave_land.py:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1363) [tools/dev_wave_land.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1387)
- しかし両者は `_fold_main_locked()` の広い例外捕捉と rollback の内側にある。[tools/dev_wave_land.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1533)
- `--message-file` は checker の site/dispatch gateを通常通らない。[tools/check_ai_provenance.py:1935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:1935)
- 新しい full-history 呼出しだけが local bounded scope／queue dispatch／長時間待機を持つ。したがって例外・latency・transaction 境界が別物であり、「同じ型の3本目」ではない。
- 「`pipefail`・『パイプ』で hit ゼロ」は再現しない。例えば [tools/strip_claude_session_trailers.sh:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/strip_claude_session_trailers.sh:39) や [tools/pegasus/certify_calibration.sh:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/pegasus/certify_calibration.sh:12) に literal hit がある。これらが F37 を閉じるわけではないが、「ゼロ」という根拠は誤りである。
- F37 自身が provenance dispatch の queue-wait-timeout を既に記録している。[docs/failures.md:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/docs/failures.md:850)
- 38.3 秒は raw baseline に記録されず、単一 local 観測にすぎない。dispatch 20 秒の一件も上限ではない。

成果物影響: 誤った被覆率と latency 一般化を根拠に段 4 が unsafe な lock/trust-root 設計を採用し、後続の台帳・レポート着地を停止または偽受理させる。

修正案:検索語ではなく「検査 rc が状態変更を支配する全 consumer」を意味検索し、local/dispatch/queue timeout/例外/rollback を別 vector として列挙する。時間は最低でも経路別の bound として扱い、単発値を lock 予算にしない。

## 8. W2 は文言追加だけでは再び儀式化できる

深刻度: nit

根拠:

- 現行 `DW-S01` は既に「性質で既存被覆を検索し、純増検出力だけを書く」と要求する。[docs/dev-wave/core.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/docs/dev-wave/core.md:31)
- 提案文は probe へ射程を広げる点では有効だが、検索 query・hit・既存被覆で足りない理由を成果物へ残す義務がない。[s2-plan.md:109](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/s2-plan.md:109>)

成果物影響: 文言を読んだことだけで通過でき、レポートの中核証拠が再び既存 production test より弱い親 probe に置換され得る。

修正案: brief に「検索した性質／対象範囲／hit／既存被覆で足りるか」の短い必須欄を置き、probe 新設時だけその根拠を要求する。

## P1〜P6 の判定

| 裁定 | 判定 |
|---|---|
| P1 | 不採用。main 側 deadlock は real だが、tip 側は明確にゲートを緩める |
| P2 | pre-FF は採用、global lock 内は不採用。active recovery も要再設計 |
| P3 | 「終了後の非0は全て赤」は採用。timeoutを含まない現定義は不採用 |
| P4 | 採用。29 は現行 `0,10,11,20..28` と衝突せず、`RC_AUDIT` と原因も異なる |
| P5 | CLI flag が無い点だけは採用。tip checker/helper 自体が実効 escape hatch なので未達 |
| P6 | 不採用。38.3秒は上限でなく、dispatch の queue/run 待ちを落としている |

## 総括

(a) **blocker あり、3 件**。現行 P1/P6 のまま実装へ進めない。

(b) 最も危険なのは、**land 対象 tip が自分を裁く checker と、場合によっては land helper 自身まで変更できること**である。一文字の rc 変更で関門が消える。

(c) 親が段 4 で裁定すべき択一は次である。

- **A:** cooperative な事故防止器にすぎないことを明記し、tip checker＋lock 内実行の残余 risk を受容する。
- **B:** wave を止めて scope を広げ、immutable checker engine＋宣言的 tip registry＋lock 外の SHA-bound audit receipt を設計する。

正しさ境界のレンズでは **B を選ぶべき**である。