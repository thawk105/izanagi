## 所見

以下、`brief`・`scripts` は指定 job dir の `brief.md`・`materials/t1505-scripts.sh`、`driver` は `orchestrator/campaign/paper_story_a1_paired.py`、`前回稿` は指定の attempt-0001 results 稿を指す。静的検査のみ実施した。

1. **real — 最優先：既存 submit は過去 attempt の bench 到達で拒否する。**  
   `driver:3234` の `_assert_no_prior_v3_bench_start` は intent 作成・qsub より前に呼ばれ、同 study の bench-go、ready 3 本、bench-start のいずれかを検出すると拒否する（`driver:2901`）。attempt-0001 の `barrier/bench-go.json:28` は対象 study を記録し、bench-start 3 本も現存する。現 checkout は指定 HEAD `a99425b66258911973785b11fd7d194884aeec64` で、driver の差分はゼロだった。抜粋 `materials/code-run-submit-head.py:24` の呼出し先に、この重要な前提がある。  
   **影響：brief:47 の「attempt-0002 は成立」は誤り。materialize に達する前に submit が拒否され、attempt-0002 の測定値・completion receipt は得られない。**

2. **real — 手順の順序と shell の成功判定が不足している。**  
   前回記録 `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:23` は再帰 submodule 初期化、CCBench pin／tracked-clean、lock、hydrate 前後の clean を明記する。brief:85 は detached／lock のみ。さらに scripts:15、29、42、59 は実処理の rc を `.done` に書くが、正常に書ければ shell 自身は成功終了し得る。submit script は hydrate 成功を確認しない。旧 HEAD・attempt-0001・旧 job dir も残った参照用 script である。  
   **影響：親が shell rc だけを信用すると、hydrate 失敗後の submit や、complete 失敗後の materialize に進み、落ちた層の記録も誤る。**

3. **refuted — hydrate に独自の pin 検査を新設する必要はない。ただし現在の cache 健全性は根拠不足。**  
   `tools/pegasus/fetch_third_party.py:629` は hydrate 前に `_verify_cache` を呼び、同:541、374 が source の pin 等を検査する。既存 `verify` CLI もある（同:703）。既定 staging root は `.gitignore:25` で除外済み。ただし「前回成功」は今回の cache 実在・健全性の証明ではない。  
   **影響：新しい受理条件は不要。既存検査の今回の出力を残さなければ、依存条件の同一性を追跡できない。**

4. **real — 親 tree の clean は CCBench の clean を証明しない。**  
   job body は `PBS_O_WORKDIR` の HEAD と親 porcelain を検査する（`tools/pegasus/paper_story_a1_paired.sh:134`、143）。v3 は submodule を無視するため、CCBench は別途 canonical pin／tracked-clean を検査する（同:365、373）。gflags／glog は既定 root、残り 3 source は別の供給 root を読む（同:1237、1382）。  
   **影響：親 porcelain 0 行だけで条件一致と記録すると、実際には job preflight で拒否され得る。**

5. **real — attempt dir の不在だけでは投入前提にならない。**  
   `_validate_attempt_root` は canonical absolute path 等の検査であり、投入可否全体ではない（`driver:2468`）。v3 は隣接する `attempt-0002.intent.json` の不在も要求する（同:2922、3225）。durable base の検索・書込権限も必要。base は submit が作成可能なので「事前に必ず存在する」は一般的な必須条件ではないが、今回は既存 base を使う。attempt root 自体は事前作成しない。  
   **影響：残存 intent、権限、path の問題で測定前に拒否される。残骸削除による再投入は行えない。**

6. **根拠不足 — idle 65 host から 3 job の即時開始は導けない。**  
   brief:46 の queue／load snapshot は割当可能性や自分の同時実行制約を証明しない。加えて timeout は submit 時刻からではなく、各 job が ready を書いた後の 600 秒である（`driver:6236`、6240）。queue 待ちに加え、依存 build・arm build・verify の到達差も含む。前回記録:43–46 の request 作成、job 開始、ready は別時刻であり、brief の「8〜28 秒」も起点の再照合が必要。  
   **影響：開始保証として記録すると、barrier 失敗の原因・時系列を誤る。timeout は本数ごとの到達状況から記述すべき。**

7. **real — raw／公開 result の差について brief に誤記がある。**  
   brief:42 は「`materialization_evidence` 1 key だけ」とするが、前回稿:346 は `limitations` の追加も記す。今回、両 JSON の現物を構造比較し、差が `limitations` と `materialization_evidence`、`workloads` は同一であることを確認した。  
   **影響：統計値は変わらなくても、公開時の限定・検証済み範囲を raw に誤って帰属させる。**

8. **real — 証拠複製と失敗時成果物の分岐を明記すべき。**  
   brief:27 の「受領証複製」だけでは raw result の保存が確定しない。complete 成功後に materialize が拒否された場合は、**記録 insight へ raw result・raw receipt・関連受領証を byte 複製し、原本／複製の SHA-256 を照合する形を既定**とする。公開 leaf や materialization 成功とは呼ばない。guard が拒否した場合は迂回せず、原文絶対 path＋SHA-256＋拒否本文を引用する。submit で止まる今回の見込みでは、存在しない results を作らない。  
   **影響：分岐がなければ、存在しない一次資料への参照や、記録用複製を公開成功と読む混同が生じる。**

9. **real — F1／F29 対策は必要。F36 の名称対応は refuted。**  
   `docs/failures.md:232` は前回 insight の件数取り違えと標本表の手打ちを記録する。数表は JSON／WAL から生成し再照合する。F29（同:1180）は、部分抜粋から経路全体の成立を推測した今回の submit 見落としにも当てはまる。一方、F36（同:1850）は自己 hash ではなく未実測欄・予測値の先書きである。MANIFEST は自身を hash 対象に含めず、commit 後検査を先に成功と書かない。  
   **影響：値の取り違え、循環する hash 記録、未実施検査の成功扱いが台帳へ固定される。**

10. **refuted — 図なし P3 は過剰な制限ではない。並記表で十分。**  
    brief:29、62 の方針は scope に合う。ただし図の backlog 化を必須成果物にする必要はない。固定 seed は attempt 間で引き直さず（事前登録:108）、同じ配置の別走として記述する。「独立再現」の認可を統計的独立性の証明に広げない。D1993 項6（`docs/decisions.md:60373`）の原文対象と、今回のプール禁止の直接根拠である brief:17 も区別する。  
    **影響：表自体は受理集合を変えないが、横断集計や「再現成功」の語を足すと許可された記述範囲を超える。**

## 投入直前チェックリスト

**現状は所見1で停止する。以下は、その阻害が別途正当に解消された場合の準備確認であり、今 submit を実行する提案ではない。**

各コマンドは単独実行し、stdout・stderr・rc を親が保存する。`$T` は新 submit-tree、`$J` は今回 job dir、`$B` は登録済み durable base、`$A` は `$B/attempt-0002` を表す。

- 実時刻：`date --iso-8601=seconds`
- 既存 bench 到達証拠：`cat "$B/attempt-0001/barrier/bench-go.json"`
- queue の RUN／QUE／HLD・稼働状態：`qstat -Q`
- gen_S の資源・実行制約：`qstat -Qf gen_S`
- 自分の他 job を含む request 一覧：`qstat`
- cache の実在・登録 pin 検証：`python3 -B "$T/tools/pegasus/fetch_third_party.py" verify --repo-root "$T" --cache-root /work/1/SFC/tanab/izanagi-thirdparty-cache`
- hydrate 2 箇所の結果：`cat "$J/hydrate.done" "$J/hydrate-default.json" "$J/hydrate.json"`
- detached／locked の確認：`git -C "$T" worktree list --porcelain`
- 再帰 submodule の状態：`git -C "$T" submodule status --recursive`
- expected-head と照合する完全 HEAD：`git -C "$T" rev-parse HEAD`
- hydrate 後の親 clean：`git -C "$T" status --porcelain --untracked-files=all --ignore-submodules=all`
- staging の ignore 根拠：`git -C "$T" check-ignore -v output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/gflags/CMakeLists.txt`
- CCBench canonical pin：`git -C "$T/external/ccbench" rev-parse HEAD`
- CCBench tracked-clean：`git -C "$T/external/ccbench" status --porcelain --untracked-files=no`
- durable base の経路・権限：`namei -l "$B"`
- canonical path・書込／検索権限・残存 namespace：`python3 -B -c 'import os,pathlib,sys; b,a=map(pathlib.Path,sys.argv[1:]); print({"base_real":str(b.resolve()),"base_wx":os.access(b,os.W_OK|os.X_OK),"attempt_real":str(a.resolve()),"attempt_lexists":os.path.lexists(a),"intent_lexists":os.path.lexists(str(a)+".intent.json")})' "$B" "$A"`
- 空き容量：`df -h "$B"`
- inode 空き：`df -i "$B"`

権限・空き容量の読取確認は、実際の作成成功の保証ではない。queue snapshot にも開始保証の意味を持たせない。

## 段 4 への提案

- **現 brief の投入可能という前提を撤回し、submit 前の静的阻害として記録する。** 拒否予測を実走 rc と書かず、未投入・intent 未作成・測定値なしを区別する。
- 成果物(1)〜(4)を結果依存にする。測定前停止なら記録 insight／裁定・worklog が中心。results 表へ成功行を追加せず、必要なら停止記録への案内を置く。
- 実行可能になった場合の順序を明文化する：detached tree → 再帰初期化 → lock → cache verify → hydrate 2 箇所 → 各 rc／pin／clean／HEAD 照合 → submit 1 回 → receipt に束縛した監視 → 終端証拠確認 → complete → 成功時のみ materialize。各層の失敗で後続の成功経路を止める。
- barrier 失敗時は「観測した拒否本文」「bench 開始有無」「§6.4 の該当理由」「2026-09-19 裁定により再投入しない」を別欄にする。原因が未確定なら scheduler 原因と断定しない。
- 最小追加記録は、workload 別の request 作成・scheduler 開始・ready・bench-start 時刻と出所。queue 待ちと開始後の準備時間を分ける。
- 条件照合表は policy／source 契約／patch／job body／依存 pin、CCBench、build 条件、3 workload key、n、seed・順序、環境契約を含める。実 host・toolchain・binary hash は取得後に記載する。
- 並記表は `workload | attempt | n | 対差平均 | h | B | 登録分類 | valid | 一次資料` の6行とし、総計行を設けない。禁止表現は **「合算60対」「プール平均」「2 attempt の平均」「統合区間」「総合効果」「勝率」「○勝○敗」「再現成功」「安定性を確認」**。各 attempt 内の登録済み「対差平均」は禁止対象ではない。
- raw の byte 複製を既定、guard 拒否時は path＋hash 引用を代替とする。実行 script の repo 複製は前回同様に避け、argv と出力を記録する。
- 図なし P3 と独立した一次資料レビューは維持。全標本表の重複掲載や図 backlog の追加は必須にしない。

**裁定パッケージ候補（scope 外）：**

- 独立再現の認可と、同 study の bench 到達後を一律拒否する既存 submit gate の整合。
- attempt 別の公開先を持たない materialize 契約の扱い。
- いずれも過去証拠の移動・削除、study／base の変更、gate 緩和で今回だけ通さない。

## 総括

現 brief は投入不可である。既存 submit の過去 bench 到達検査が attempt-0001 を検出する。  
まずこの静的阻害を記録し、1 回限りの submit を失敗確認のために消費しないことを提案する。  
hydrate の停止条件、queue／ready 時刻、raw 証拠保存を補えば、手順と記録の欠落は縮められる。  
本レビューでは書込み・submit・pytest を実行していない。