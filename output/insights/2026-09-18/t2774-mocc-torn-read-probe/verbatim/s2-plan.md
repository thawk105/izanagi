## 結論と参照範囲

腕 A は **N=42、6 本×7 batch**、腕 B は **各 arm K=24、2 node に各 12 組を配分し、各 node 内で stock／診断を交互実行**する案を推奨する。

P1 の「validation の間隙だけで、本文の不整合なしに長さ 2・両辺 rw の cycle が commit されうる」は、条件付きで現物と整合する。一方、親 brief の次の二点は訂正が必要である。

- `supported ⇔ (ii)のみ`／`contradicted ⇔ (i)も発生`という対応は成立しない。discriminator が比較するのは、報告された rw 辺についての **reader version と先頭 8 byte の producer の対応**である。
- 診断 arm の `0/K` は、機構の必要性や根因確定を意味しない。有限標本での未再現と、その率の上限を示す。

以下、`M:行` は指定された `verbatim/mocc-transaction-e9e477ca.cc`、`V/` は親 job dir の `verbatim/`、その他は指定 worktree 相対パスを表す。資料は指定射影だけを参照した。編集・build・pytest・compute 実走は行っていない。確率値のみ標準ライブラリで算出した。

## 1. P1：二つの観測間隙の検算

**(i) cold 読み。** `M:320` で旧版 T0 を取得し、`M:322` で非 `W_LOCKED` を観測しても、その後の writer の施錠を検査する行は body copy 前後にない。body copy は `M:347–348`、版の再読は `M:350`、一致時の脱出は `M:351–352` である。writer の payload copy `M:1169–1170` が counter 検査後に入り、publish `M:1195–1196` が再読より後なら、T0 のまま loop を抜けることを既存検査は排除しない。

これは「旧版に新しい stamp／混合した body が対応しうる」という静的被覆の欠落である。実際の copy 命令列と重なりは未実測であり、毎回 body が混合するという主張ではない。

**(ii) validation。** `M:1010–1013` は保存した版と現在版の epoch/tid を比較し、`M:1024–1025` は別 load で writer counter を検査する。この間に writer が publish と unlock を終えると、旧版比較と解放済み counter の両方を通る。`M:1038` の現在版の再取得は `max_rset_` 更新であり、一致検査ではない。

P1 の順序論証は、次の前提を補うと成立する。

| 対象 | 必要な前提・現物との対応 |
|---|---|
| transaction の内容 | W は y の旧版を読み x を更新、R は x の旧版を読み y を更新する。x と y は異なり、互いの read key は自分の write set に含めない。 |
| read phase | 両者の旧 payload 読取は相手の更新前に終了する。したがって (i) は不要。 |
| W の validation | W が x を保持し、R がまだ y を施錠していない間に y の版・counter 検査を終える。 |
| R の validation | R が y を保持し、x の `M:1010–1013` が T0 を受理した後、`M:1024` より前に W の `M:1195` と `M:1207` が終了する。 |
| 最後の版取得 | R は `M:1038` で W の新版を最大版へ取り込める。これは abort 条件ではなく、R の commit TID を W より大きくしうる。 |
| commit | validation が true なら `M:1215–1220` から writePhase へ進む。W→R は y、R→W は x の rw 辺になる。 |

成立を妨げる、または頻度を下げる要因は以下である。

- **hot／RLL 読みの施錠。** `M:280–309` で read lock を取得する場合、想定した「相手の read key が未施錠」という前提が崩れる。RLL は失敗 read と hot read を含む（`M:915–978`）。
- **CLL の順序修復。** `M:739` の sort、`M:834–858` の unlock、`M:860–878` の RLL 先行取得が、複数 key の場合の順序を変えうる。ただし、cold・RLL 空・各 write set 一要素なら、CLL sort 自体は上記の存在例を排除しない。
- **cold read の待機時 abort。** `M:331–334` は既存 CLL と key 順序によって abort する。上記存在例では read を相手の施錠前に完了させるため、この条件は不要である。
- **`NO_WAIT_LOCKING_IN_VALIDATION=1`。** pilot の configure に存在する（`tools/pegasus/mocc_trace_pilot.sh:1696`）が、指定された transaction.cc にはこの名前の条件分岐がない。`M:884–887` は通常の lock 呼出である。少なくとも今回の二つの read 検査を原子的にはしない。lock 実装内部への影響は指定射影だけでは未確認。
- **epoch／版の変化。** `M:1012–1013` より前の版変化は abort させる。global epoch の進行だけを理由に、この二つの load の間隙を再検査する処理はない（`M:1003–1006,1127–1131`）。同 epoch の存在例を妨げない。
- **追加の操作。** 固定 cell は最大 10 操作なので、他 key の競合・版変更・施錠で abort しうる。最小存在例から固定 cell の発生率は導けない。

**42 走との整合：** `max_rset_` の更新と commit TID の最大値＋1（`M:1038,1118–1131`）は、5 件すべての「長さ 2・両辺 rw・別 thid・同 epoch・tid 差 1」と整合するが、その形は (ii) 固有の証拠ではない（`V/t1892-results.md:110–126`）。

## 2. discriminator の対応表と証拠の上限

`orchestrator/campaign/mocc_g2_discriminator.py` は、標準 trace の W 行から `(key, version) → producer` を作る（`:284–298`）。comparison の expected は **reader version** をこの表で引いた producer、または genesis である（`:575–592`）。rw 辺の overwriter と expected producer は同一とは限らない。

observed は witness の L 行から取得した producer（`:342–362`）であり、C++ 側では保存済み `read.body_` の先頭 stamp を decode する（`M:68–97`）。比較と結論の生成は `:600–624`、結論の意味と限界は `:629–653` に明示されている。

| 結論 | 確定する被覆 | (i)／(ii) との関係 | 分岐 2・3について排除できる範囲 |
|---|---|---|---|
| `supported` | blockers がなく、報告された全 comparison で expected と observed が一致。 | 正常な旧 payload 読取＋(ii) と整合する。(i) の時間的重なりや stamp 以外の混合は排除しない。(ii) の発生自体は観測していない。 | 比較対象の reader-version 投影を stamp が裏づける。hook 全体の正しさ、writer version、commit order、verifier の版順序仮定を証明しない。 |
| `contradicted` | 少なくとも一つの comparison で producer が不一致。 | (i) による旧版／新 stamp の組合せと整合する。ただし不一致だけでは「observed が新版」とは限らず、producer の書込版も確認して記述する。(ii) だけで全 body が正常という限定モデルでは、この不一致を説明できない。 | 実装での版／stamp 不整合と、hook の投影誤りを単独では分離しない。verifier 仮定も全面排除しない。 |
| `indeterminate` | blockers により比較が成立しない。 | (i)・(ii) の肯定／否定に使えない。 | 分岐を排除しない。blocker の逐語を保存する。 |
| `no-g2` | blockers がなく、当該 verifier 結果の cycle が 0。 | 今回の走では識別対象の G2 が得られない。(i)・(ii) の不在は含意しない。 | 分岐を排除しない。T-1943 の扱いと同じ（`V/t1943-RESULT.md:17–21`）。 |

したがって、親 brief の「⇔」を残すなら、次に限定する。

> 有効な G2 入力について、`supported` ⇔ 比較対象すべてで stamp producer が標準 trace の reader-version producer と一致。`contradicted` ⇔ 比較対象に一つ以上の不一致がある。

先頭 stamp は `id_` 領域の整列した 8 byte である（`V/operational-facts.md:17`）。x86 の整列 8 byte load の原子性を前提としても、**64 byte の payload 全体と版を一括して観測したことにはならない**。一致していても残りの byte の混合は検出しない。また `M:347–348` は TupleBody copy、stamp の記録は `M:87` の後段 decode なので、指定 source だけで共有領域からの copy の機械命令幅まで確認したとは書かない。

`limits.writer_version_verified=false`、`commit_order_verified=false`、`mocc_root_cause_verified=false`（discriminator `:648–653`）を、そのまま insight の主張上限に引き継ぐ。

## 3. 腕 A：投入・待機・収集・集計

**推奨は N=42。** 既存推定値 `p=5/42` を仮に固定すると、1 件以上の検出確率は N=24 で 95.23%、N=42 で 99.51%。N=42 は expected G2 も約 5 件となり、複数 comparison の形を見る本題に適する。追加費用は 6 本×3 batch である。

ただし歴史的推定の両側 95% CI は `[0.039806, 0.256317]` と広く（`V/t1892-results.md:53–60`）、今回の witness 有効条件への移植も仮定である。95%／99.5%を保証値とは書かない。

投入計画は次の順とする。

1. unit 1 の関連試験後、修正を含む clean な source を固定する。
2. 再生死確認を 1 request 実行する。これは N から除外して別掲する。`4936.nqsv` も実験分母に入れない。
3. 再生死確認の完了は「serializable」ではなく、所定の verifier／discriminator まで到達し、成果物が解釈可能であることとする。G2 による rc=1 も到達成功に含める。
4. 同じ source で 6 request×7 batch を実行する。途中の no-g2／G2 による本数変更はしない。

投入 argv は既存経路を使う。

```text
bash tools/pegasus/submit_mocc_trace.sh
  --repo-root <worktree>
  --attempts-root <job-dir>/attempts-A
  --t1943-g2-discriminator
```

`<job-dir>` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe`。

各 request に `dev_wave_wait.py compute` を **1 本だけ**割り当てる。

```text
python3.10 tools/dev_wave_wait.py compute
  --request-id <request>
  --done-file <worktree>/output/env/pegasus/mocc-trace/job-staging/<raw-PBS_JOBID>/job-result.json
  --accounting-file <job-dir>/attempts-A/submissions/<nonce>/pbs-job.stderr
  --receipt-file <job-dir>/wait-A/<request>.json
```

done-file は失敗時に存在しないため、会計の `Ended Request Time:` との OR 完了を使う（`V/operational-facts.md:21–23`）。`raw-PBS_JOBID` は `0:4936.nqsv` のような実際の値を使い、request 表記から無断で再構成しない。

**G2 の rc=1 は観測結果であり、欠測ではない。** pilot は discriminator の後でも verifier 非ゼロで failure にする（`tools/pegasus/mocc_trace_pilot.sh:2238–2335`）。`job-result.json` の存在を分母条件にしてはならない。各走について request、verifier rc/verdict、G2 の有無、discriminator conclusion/blockers/comparisons、その他 stage 失敗を別列にする。

成果物は終端後に `job-staging/<raw-PBS_JOBID>/` 全体を `<job-dir>/evidence-A/<ordinal>/` へ退避する。標準 trace、witness、manifest、raw JSON、failure、stdout/stderr と submit receipt を保存する。元 manifest の絶対パスを都合よく書き換えず、退避先対応と digest を別に記録する。

集計は **unit 2 の Codex author が job-dir runner に `--summarize-a` を実装**する。親は集計 script を書かない。固定 request 一覧を入力にし、失敗を黙って除外せず、N・判定可能数・G2 数・欠測・四結論の件数を出す。これは結果整理であり、新しい受理 gate や repo 共通台帳にはしない。

衝突資源の評価は次のとおり。

| 資源 | 現物と運用 |
|---|---|
| attempts | 128-bit nonce＋create-only directory（submit `:321–335`）。通常の同時投入で同名にならず、衝突時は停止。 |
| job-staging／scratch | PBS_JOBID 別、create-only（pilot `:47–79`）。別 request は別 directory。 |
| third-party | job-private hydrate（pilot `:1533–1537`）。共有 cache の fetch／更新は batch 中に行わない。 |
| CCBench checkout | scratch の別 path に `worktree add --detach`（pilot `:1681–1683`）。共有 HEAD を変更しない。 |
| Git 管理領域 | 同じ submodule の worktree metadata は共有する。論理的な checkout 衝突は避けるが、同時 add/remove の失敗可能性までゼロとはしない。歴史的 42 走では source-materialization 失敗なし（`V/t1892-results.md:83–84`）。 |
| outer worktree | source 検査が読む共有入力。全 batch 終了まで編集・commit・切替をしない。 |

時間は歴史的 batch span 102–689 秒より、7 batch 合計約 **12–81 分＋再生死確認＋queue 待ち**。並列 6 は投入 fan-out であり、同時実行 6 の保証ではない（`V/t1892-results.md:86–105`）。

## 4. scope 0：hydrate interpreter の局所修正と契約 test

原因は `fetch_third_party.py:52–64,93–103` の driver import と、`orchestrator/verifier/parse.py:71` の実行時 union alias の組合せである。job 4936 は hydrate JSON 0 byte、rc=2 で停止した（`V/job-4936-failure-evidence.md:3–16,34–39`）。

修正場所は **pilot の現行 `:1533` と `:1534` の間**。`HYDRATE_PY`、`hydrate_py_rejected` を使い、checker/verifier の marker を複製しない。

import 判定は `source_digest` ではなく、実際の依存先 **`orchestrator.campaign.silo_ladder_rung1`** を選ぶ。fetch の二つの import root（`:55–60`）に合わせる。挿入案は以下。

```bash
# BEGIN T2774 HYDRATE INTERPRETER GATE
HYDRATE_PY=""
hydrate_py_rejected=""
for py_name in python3 python3.10 python3.11 python3.12; do
  py_cmd=$(command -v -- "$py_name") || continue
  py_resolved=$(realpath -e -- "$py_cmd") || continue
  [[ -x "$py_resolved" ]] || continue
  if (
    cd "$REPO_ROOT" &&
    PYTHONPATH="$REPO_ROOT/orchestrator:$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    "$py_resolved" -c \
      'import sys; import orchestrator.campaign.silo_ladder_rung1; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      "$REPO_ROOT"
  ) >/dev/null 2>&1; then
    HYDRATE_PY="$py_resolved"
    break
  fi
  hydrate_py_rejected+="${hydrate_py_rejected:+ }$py_name=$py_resolved"
done
if [[ -z "$HYDRATE_PY" ]]; then
  hydrate_gate_message="no python3 >= 3.10 candidate can import orchestrator.campaign.silo_ladder_rung1 (rejected: ${hydrate_py_rejected:-none})"
  printf '%s\n' "$hydrate_gate_message" \
    >"$ATTEMPT_DIR/third-party-hydrate.stderr"
  write_failure 2 third_party "$hydrate_gate_message"
  exit 2
fi
# END T2774 HYDRATE INTERPRETER GATE
```

現行 `:1534` は次へ置換する。既存の引数・timeout・redirect は維持する。

```diff
-timeout 20 python3 "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT" \
+timeout 20 "$HYDRATE_PY" "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT" \
```

stage 名は既存の `third_party` とする。rejected 一覧は failure の message と既存 stderr に残し、新しい artifact 分類面を増やさない。`write_failure` 自体は stdlib-only なので今回変更しない（pilot `:124–140`）。

契約 test は `test_mocc_trace_hydrate_interpreter_gate_selects_and_fails_closed` **1 関数**を追加し、その中で以下のケースを実行する。

- 新しい BEGIN/END marker の exactly-one と順序を確認し、**gate だけでなく実 hydrate 呼出まで**を抽出する。終端は既存 `THIRD_PARTY_SOURCE_ROOT=$(python3 - ...` の直前。
- fake `python3` は `-c` import probe で失敗、fake `python3.10` は成功。hydrate 実行 argv を記録し、選択された interpreter が実際に使われることを確認する。
- 最初の候補が成功するケースも含め、後続候補が呼ばれないことを確認する。
- 全候補拒否では rc=2、stage=`third_party`、全拒否候補の `name=resolved-path`、hydrate 未実行を確認する。
- probe argv の module、`sys.version_info >= (3, 10)`、cwd/import roots、hydrate の cache/staging argv を確認する。

既存の型は test `:1515–1596,1994–2084,2087–2166`。job-private root の既存検査 `:1408–1418` はそのまま残す。

| 負例 | 対応する検出 |
|---|---|
| hydrate 呼出を素の `python3` に戻す | actual argv の interpreter 不一致、fake 旧版の hydrate 拒否。 |
| version 比較を外す | probe argv の明示的 version 条件検査。旧版 import 失敗ケースだけでは、この変異の歯にはならない。 |
| rejected の追記を外す | 全候補拒否ケースで一覧が欠落。 |
| 成功候補でも拒否する過剰拒否 | 正常候補で hydrate まで到達する正例。 |

fake interpreter は実 Python 3.9 の推移 import 再現ではない。実環境での鎖の確認は再生死確認 job が担当する。

`parse.py`、`fetch_third_party.py` は変更不要。既存 checker/verifier gate、discriminator の受理集合も変更しない。

## 5. 腕 B：診断 patch の設計と「縮小だけ」の意味

validation に **版→counter→版再読**を加える案を採る。`M:1036` の後、`max_rset_` 更新前への挿入案は次のとおり。

```diff
+    Tidword check_after_counter;
+    check_after_counter.obj_ =
+        __atomic_load_n(&((*itr).rcdptr_->tidword_.obj_), __ATOMIC_ACQUIRE);
+    if (check_after_counter.epoch != check.epoch ||
+        check_after_counter.tid != check.tid) {
+      (*itr).failed_verification_ = true;
+      this->status_ = TransactionStatus::aborted;
+#if ADD_ANALYSIS
+      ++result_->local_validation_failure_by_tid_;
+#endif
+      return false;
+    }
```

元の保存版との比較が先に成功しているため、`check` との比較は保存版との比較と同じ版一致条件になる。旧比較・counter 条件・write-set 例外・`max_rset_` の既存行は削除しない。

P1 の (ii) では unlock を観測した後の版再読が W の新版を検出するため、元の二つの load だけでは通っていたケースを追加拒否する。counter 検査後に別 writer が開始するケースまで「writer が存在しない」と保証するものではない。

cold 側について、依頼どおりの **再読案**は `M:348` の後、`:350` の前に置く。

```diff
+#ifdef RWLOCK
+      if (tuple->rwlock_.ldAcqCounter() == W_LOCKED) continue;
+#endif
```

順序は必ず `body→counter→版再読` とする。既存の版再読・break の後へ置いてはならない。

ただし、これは **abort 追加ではなく retry 追加**である。再試行で別版を読み、後に commit できるため、「実行全体の commit 集合が stock の部分集合」「commit 件数は増えない」は証明できない。説明できるのは「各 read snapshot に追加の受理条件を課す」ことまでである。

依頼の「abort を増やすだけ」を文字どおり優先するなら、cold 側の推奨は次の **abort 案**である。

```diff
+#ifdef RWLOCK
+      if (tuple->rwlock_.ldAcqCounter() == W_LOCKED) {
+        status_ = TransactionStatus::aborted;
+        return Status::ERROR_LOCK_FAILED;
+      }
+#endif
```

この案なら、既存の成功／失敗判定を緩めず、追加条件で現在の transaction attempt を終了する。abort の既存経路は `M:1059–1089`。ただしこちらもスケジューリングと後続再試行を変えるので、**実測 commit 総数の単調減少**までは含意しない。

**採否推奨：validation 再読＋cold abort 案を採用。** 親が cold retry を維持するなら、主張を「snapshot ごとの条件強化」に訂正する。二つを曖昧に混在させない。

配置上の条件は以下。

- patch 対象は `cc/mocc/transaction.cc` の上記二箇所だけ。
- `#if TRACE` の既存行、stamp、C/R/W/E/L/S の emission を変更しない。
- 指定された e9e477ca の写しには `#line` がない。新規追加も不要。T-2294 の X/P patch を重ねず、その `#line` 再生成問題を持ち込まない。
- patch は job dir の `probe/mocc-close-version-counter-gap.patch` に置く。D16 の上流還元判断、D1686 の X/P 被覆、D2134 の探索非解禁は変更しない。

二箇所を同時に変える対照からは、(i) と (ii) の寄与を個別には識別できない。追加 arm は本 wave では作らず、その限界を記す。

## 6. 腕 B：runner、dispatch、標本数と時間

unit 2 は `<job-dir>/probe/t2774_probe.py` を作る。骨格は `s3_mocc_lock_coverage.py:224–270,314–363,609–655`、隔離 checkout は `patchharness.py:346–383` を参照する。ただし、同 driver の X/P patch、負例 matrix、trace の自動削除（`:427`）は転用しない。

runner の具体的な流れは以下。

1. `--repo-root`、`--third-party-cache`、`--scratch-root`、`--patch`、`--output`、`--pairs`、`--block-id` を argv で受け取る。通常実行は compute に限定する。
2. job 固有 scratch を作り、`TMPDIR` をその配下に設定してから `checkout` を呼ぶ。`patchharness.py:362` はこの値を使う。
3. `sys.executable` で hydrate し、gflags/glog を job-private に準備する（既存 driver `:224–254`）。
4. full OID `e9e477ca1b55348ab4530de0b1cf663ce4555290` から、stock と診断用の二つの `checkout(..., base_dir=<submodule repo>)` を作る。診断側だけ `apply_patch`（`patchharness.py:204–211`）。
5. 同一 toolchain、同一 configure argv で二つの TRACE=1 binary を build。configure は pilot `:1689–1714` と一致させ、compiler は T-1943 と同じ gcc-11 系の policy 指定を使う。VAL_SIZE は変更しない。
6. hydrate 後の masstree に `config.h` がないため、同じ依存 source を使う `masstree_build` を先に完了させる。先例は `t2644.../verbatim/probe.md:238–251`。二つの build は同じ node 内で直列にする。
7. 各 node で stock／診断を隣接ペアにする。ペアごとに AB、BA と順序を交替し、一方の arm を先に全走しない。
8. 各走を独立 process・独立 trace/witness directory にし、verifier の raw JSON と rc を保存する。
9. raw 成果物を job dir に退避してから scratch を片づける。集計 JSON に node、順番、arm、patch/binary/source SHA、argv、走数、G2、欠測、所要時間を記録する。

固定 workload argv は pilot `:1973–1980` の綴りをそのまま使う。

```text
-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9
-ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3
```

両 arm で `IZANAGI_TRACE_DIR` を各走の directory に設定する。腕 A との条件差を減らすため、固定 cell の両 arm とも witness を同じ条件で有効にし、`IZANAGI_MOCC_G2_WITNESS_DIR` も個別にする（pilot `:2009–2013`）。診断 binary を既存 discriminator の束縛へ無理に通すことはせず、腕 B の一次集計は verifier に限定する。

verifier は選択済み Python、実装上は `sys.executable` で起動する。

```text
python3.10 -m orchestrator.verifier <trace-dir>
  --json --protocol mocc --ccbench-root <corresponding-source>
```

既存 pilot 同様、取得できた実 commit count を `--expected-commits` に渡す。rc=1 は有効な anomaly 観測として保存し、serializable に変換しない。rc=2/3、timeout、JSON 不正、空 trace は no-g2 にせず、判定不能／失敗として別計数する。runner の完了状態と各走の正しさ verdict は別項目にする。

generic dispatch は worktree を cwd にして、各 node 用に次を一回ずつ投入する。

```text
python3.10 tools/pegasus/dispatch_compute.py
  --task generic
  --walltime 01:30:00
  --queue-wait-timeout 3600
  --overall-grace 4200
  --
  python3.10 -B <job-dir>/probe/t2774_probe.py
  --repo-root <worktree>
  --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
  --scratch-root /scr
  --patch <job-dir>/probe/mocc-close-version-counter-gap.patch
  --pairs 12
  --block-id B1
  --output <job-dir>/arm-B/B1/result.json
```

B2 は block-id/output を変える。dispatcher の generic は argv をそのまま実行し、独自 env を伝播しない（`dispatch_compute.py:154–159,1660–1673`）。したがって Python executable も argv に必要で、cache/scratch を親 env だけで渡してはならない。

`PBS_JOBID` 不在でも実行可能にし、親が dispatch receipt と B1/B2 を結びつける。hostname と開始時刻を保存する。先例の compute-visible 探索（probe `:101–120`）を使うなら best-effort と明記し、同 host の最新 file を厳密な request identity としない。

overall deadline が投入時刻起算なので、queue 3600 秒と full walltime の両方を確保するなら grace 600 秒だけでは不足しうる。ここでは queue 予算＋後処理 600 秒として **4200 秒**を推奨する（`V/operational-facts.md:5–6`）。

`--selftest` は login で実走可能な軽量 mode とし、build・hydrate・checkout・benchmark を呼ばず、synthetic な成功、G2、rc 不整合、JSON 欠損、timeout を分類する。G2 が欠測へ消えないこと、欠測が no-g2 へ化けないことを検査する。先例の selftest／compute 分離は probe `:322–340`。本計画では未実測で、親が実行する。

**K=24 の解釈。** stock の真の率を仮に 5/42 とすれば期待 G2 は 2.86 件。診断側 0/24 の片側 95% 上限は

```text
1 − 0.05^(1/24) = 0.11735
```

であり、約 0.119 ではなく約 **0.117**。歴史的点推定よりわずかに低いだけで、同時対照より「率が下がった」とするには不足しうる。例えば stock 3/24、診断 0/24 の独立標本による片側 Fisher 値は約 0.117。node 内相関を無視した単純な参考値でも有意差には届かない。

したがって K=24 は**探索的対照の予算**として採用し、結果を見た無制限追加はしない。stock も 0/24 なら、今回の対照は根因識別に届かなかったと記す。

所要は 1 node 当たり 24 走。build 2–4 分、warm-up 約 13 秒、各走 3 秒＋verify 2 分未満という既存見積なら約 **51–54 分＋退避・準備**。2 node を並行利用し、walltime は各 90 分とする。verify が長引く場合は実測に従い欠測を記録し、時間内完走を保証しない。

## 7. 温度と仮説 cell の扱い

既定 threshold=10 は `V/t2757-README-s2-s3.md:14`。温度は単なるアクセス回数ではなく、`failed_verification_` の read に対して abort 後に上昇する（`M:915–953,1069–1071`）。

reset と競合を無視した単純モデルでは、temp=t からの上昇確率は `2^-t` なので、0→10 に要する対象失敗回数の期待値は

```text
1 + 2 + … + 512 = 1023
```

となる。48 thread・skew 0.9 の 3 秒で集中 key がこの程度の失敗機会を持つことは静的には排除できず、**hot record は存在しうる**。ただし epoch reset 条件（`M:925–936`）、競合、RLL による安定化があるため、到達数・割合は不確実である。

さらに温度未到達でも、RLL の失敗 read は次の試行で施錠経路へ入る（`M:280–291,970–973`）。したがって「hot key が増えるほど cold の (i) が増える」とは限らない。施錠付き read 比率が上がると (i) の曝露は減る。既存 trace から hot/cold の実測比率は得られず、本 wave では新規計数行を足さない。

P2 は「小 value ほど増える」を採用しない点に同意する。ただし「validation の間隙は value size と無関係」も、**判定条件に直接 value size がない**という意味に限定する。実行時間や競合配置への間接効果までゼロとはいえない。

仮説 cell は **今回は追加しない案を推奨**する。追加する場合は既存 binary を再利用し、例えば records=1000 と skew=0.99 を一つずつ変更した 1–2 cell を各 arm 6 走とする。各 cell 12 走なので、追加費用は最大約 25 node-minutes、2 cell で約 50 node-minutes。統計的な頻度比較ではなく観測に限る。

`EXACT_WORKLOAD` の完全一致を変えず、これらには discriminator を適用しない（discriminator `:28–57`）。value size と thread 数も同時に変えて三つの仮説を検証したとは書かない。

## 8. insight と fragment

insight の節構成案は次とする。成果物内の見出しも H2 に統一できる。

1. 問いと対象範囲：静的所見 (a)、(b) 除外、non-certifying。
2. 実行の束縛：source full OID、outer source、policy/compiler/configure、binary/patch/runner SHA、request と node。
3. 順序論証：cold と validation を分離し、P1 の前提と既存検査の被覆を記載。
4. 腕 A：全 request の結果、四結論、comparison ごとの expected/observed。
5. 腕 B：node・順序・arm ごとの結果、N/m/k、欠測、率と区間。
6. 仮説と温度：未計測の hot 比率、追加 cell の有無。
7. 解釈と限界：整合／未再現、stamp の射程、二箇所同時変更、有限標本、観測者効果。
8. CCBench 側の扱い：D16、上流 PR/push は人間判断、pin/certified は不変。
9. 再現資料：job-dir 原本の所在、digest、byte 数、必要な逐語投影。

主判定文は結果に応じて、例えば次に限定する。

> 固定 cell の G2 について、比較対象の reader-version 投影が payload stamp に支持された／矛盾した。validation の別読みによる静的候補とは整合するが、その実行順序を直接観測したものではない。

decisions fragment は **原則 0 本**。既裁定の実施記録は worklog と insight に置く。cold retry／abort の選択や「必要性」の主張上限を親が新しい設計判断として固定する場合だけ、取消し可能な親判断として 1 本にまとめ、ユーザーの既裁定に見せない。

failures fragment は T-548 回帰として 1 本。

- trigger：job `4936.nqsv`、hydrate `:1534`、rc=2、JSON 0 byte。
- 原因：driver import の追加に対し、先行 hydrate 呼出の interpreter が未追随。
- 既存被覆の不足：job-private root test は interpreter を検査せず、checker/verifier gate は hydrate より後なので保護しない。
- 修正：hydrate 直前の import＋version 選択と actual argv 契約 test。
- 実証：親が行う関連試験・変異結果・再生死確認 request を追記する。現時点で成功とは書かない。

## 9. 並列分割とレビューのレンズ

| 担当 | 所有する面 | 触らない面 |
|---|---|---|
| 段 5 unit 1 | repo の `mocc_trace_pilot.sh`、契約 test 1 本 | verifier、fetch、submitter、policy、discriminator、CCBench、probe |
| 段 5 unit 2 | job-dir の patch、runner、selftest、腕 A 集計 mode | repo 実装、`patches/`、登録簿、gitlink、T-2772 の所有面 |
| 親 | source 固定、投入、待ち手、成果物退避、insight／spool の統合 | 集計 script の新規作成、上流 PR/push |

unit 1 と unit 2 の実装は並行可能。ただし compute 実走中に unit 1 や親が outer source を変更しない。unit 2 の probe も投入前に digest を固定する。

段 6 のレビューは 2 本とする。

- **レンズ A：正しさと主張。** P1 の前提、`max_rset_` の意味、patch の追加拒否、cold retry/abort の差、stamp の被覆、discriminator と根因の非同値、0/K の解釈。
- **レンズ B：実行と収集。** gate から actual hydrate までの interpreter、marker 一意性、失敗記録、private staging、generic argv、warm-up、同 node の対照、rc=1 保全、request と成果物の対応、欠測と時間予算。

関連試験、変異 matrix、再生死確認、受入全走は親が実施する。本 plan の静的確認でそれらを代替しない。

## 総括

- **腕 A：N=42、6 本×7 batch。** 修正後の再生死確認 1 本を別枠で先行させる。条件付き検出力は約 99.51%、歴史的 batch span に基づく本体時間は約 12–81 分＋queue 待ち。
- **腕 B：各 arm K=24。** 2 compute job に各 12 ペアを配り、各 node 内で stock／診断を交互実行する。各 job 約 51–54 分＋準備・退避、walltime 90 分。
- **診断 patch：採用推奨。** validation の版再読を追加し、厳密な「追加 abort」を優先するなら cold 側は abort 案。指定の retry 案を採る場合は「abort のみ増加」という説明を撤回し、snapshot の条件強化に限定する。
- **親 brief への異議：** P1 の存在論証は条件付きで支持するが、discriminator との「⇔」は不可。`0/K` から必要性・根因確定への昇格も不可。P2 の value size の影響は未実測。P3 は node ごとに両 arm を置き、build 二つの費用と queue を含む deadline を見込む必要がある。
- **予算：** 本 plan 1、段 3 consult 2、段 5 author 2、段 6 review 2で **Codex 子は基本 7 本＋必要な fix**。新規 compute は **44 pilot job（再生死確認1＋腕A42を含めると43）ではなく、正確に pilot 43 本＋腕B generic 2 本＝45 本**。既失敗の4936は別。queue 待ちを除き、compute を直列化すると約 1–2.5 時間、腕A/Bを資源の範囲で並行させれば短縮できる。関連試験・受入・変異実証の job 数と時間は別枠で、指定資料からは確定できない。
