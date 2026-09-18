## 評価結果と実行鎖

**must-fix は2件です。** plan の実装修正で既知の hydrate／未計装 source の断線は塞がります。ただし、待機先の ID と、待機終了を成功に変換する条件が不足しています。修正後も必ず停止する別の実装欠陥は、指定資料の静的読解では確認できませんでした。

以下、`pilot` は `tools/pegasus/mocc_trace_pilot.sh`、`submit` は `tools/pegasus/submit_mocc_trace.sh` を指します。テスト・compute 投入・ファイル変更は実施していません。

| 段 | 根拠 | 被覆と残る条件 |
|---|---|---|
| login → qsub | submit:254–290、372–383、508–531 | clean gate 後、mode・nonce・policy SHA・cache を渡す。返すのは qsub の request ID。 |
| policy parse → submit receipt pin | pilot:790–986、1093–1271 | stdlib の処理。今回の interpreter 修正とは独立。 |
| compiler gate | pilot:1493–1524 | 素の Python で `toolchain_binding` を import。4936 では通過済み。hydrate 修正後の「次の停止段」ではない。 |
| hydrate | pilot:1528–1555 | 選択 interpreter への変更は必要。cache 検証・clone・20秒 timeout は引き続き成立条件。 |
| gflags／glog | pilot:1557–1656 | hydrate の `source_root` 直下を使用。HEAD・clean 検査後、scratch の別 build/install directory に構築する。 |
| worktree → patch → TRACE=0 | pilot:1681–1746 | plan の挿入位置なら両 TRACE build に patch が届く。 |
| checker → watermark | pilot:1754–1892 | checker は選択 interpreter。D297 は OID 対の検査で、作業ツリー patch の同一性検査ではない。watermark は実 TRACE=0 binary を読む。 |
| TRACE=1 → witness | pilot:1895、1907–2018 | `IZANAGI_MOCC_G2_WITNESS=1` と絶対 witness directory を実プロセスへ渡す既存配線がある。 |
| manifests → verifier | pilot:2090–2232 | trace／witness manifest を先に生成。T1943 の verifier source を `BUILD_SOURCE` に替える plan は必要。 |
| discriminator | pilot:2292–2332 | 選択済み `VERIFIER_PY` で起動。二つの manifest が存在し、schema・葉集合・digest・workload が一致する必要がある。 |
| classification → policy finalization | pilot:2384–2488 | T1943 は receipt 前に分類検査。267741106 の `os.lstat`／`stat.S_ISDIR` は Python 3.9 で使える形。実 compute 通過は未実測。 |
| receipt → job-result → cleanup | pilot:2490–3400 | receipt 時点では source が存在する。job-result 後にも worktree 削除が残る。 |

discriminator の `Path.stat(follow_symlinks=False)`（同ファイル:141、180）は選択済み Python ≥3.10 で実行されます。素の Python 3.9 に残った同じ問題とは数えません。

## must-fix

**MF1 — qsub の request ID を、そのまま staging directory 名にする待機指定は4936の実績と一致しません。**

- **根拠:** plan「scope 3」の「返された PBS_JOBID をそのまま使う」。submit:516–527 は qsub 出力を `REQUEST_ID` として読むだけです。一方、pilot:57、76 は実行環境の `$PBS_JOBID` をそのまま directory 名にします。`operational-facts.md` は request `4936.nqsv` に対し `job-staging/0:4936.nqsv/` を記録しています。`0:` を除くのは qstat 用の pilot:1273 です。
- **放置時:** 正常終了しても指定 done file を発見できず、accounting だけで待機が終了するか、待機上限に達します。
- **是正案:** request ID と実行環境の PBS_JOBID を別変数として扱う。今回の Pegasus 実績に基づく指定は、request が `N.nqsv` なら `job-staging/0:N.nqsv/job-result.json`。既に `0:` 付きなら重ねて付けない。起動後は当該 directory の記録と submission nonce を照合する。一般則として qsub 出力と PBS_JOBID が同一だとは記述しない。

**MF2 — scope 3 の成功判定に、待機終了と job 終了の区別、`failure.json` の否定条件がありません。**

- **根拠:** `dev_wave_wait.py:2028–2033、2068–2069` は「非空 done file **または** accounting 終了」で成功を返し、JSON の意味を検査しません。pilot:3367–3382 は job-result を書いた後、3389–3391 で worktree を削除します。その失敗は ERR trap により後から failure を残し得ます。plan の5条件にはこの終端確認がありません。
- **放置時:** accounting だけを得た失敗 job、または job-result 作成後に失敗した job を、pipeline 完走として記録し得ます。
- **是正案:** 待ち手の終了後に親の判定 script を実行し、終端 accounting を確認してから次節の条件を評価する。`indeterminate`、`failure.json`、必要 artifact 不在・不一致は失敗。queue timeout は「未完了」とし、修正の成功にも実装欠陥にも数えない。

## 完了判定の修正案

親の小さな Python 判定 script では、以下を条件式の逐語案とします。JSON 読取り・必要キー欠落・digest 計算の例外も判定失敗にします。

ここで各 `*_ok` は省略可能な条件ではありません。

- `terminal_ok`: 当該 request の終端 accounting を確認し、job script の終了コードが0。
- `receipt_digest_ok`: receipt 実 bytes、sidecar、job-result の receipt digest が一致。
- `patch_binding_ok`: patch の repo path・実 bytes SHA、二つの SHA sidecar、numstat の単一 touch path が receipt binding と一致。
- `result_binding_ok`: discriminator 実 bytes の SHA・結論が receipt と一致し、既存 manifest／binary／workload の束縛も一致。
- `classification_ok`: 分類 manifest が存在し、実 artifact がそれぞれ一意に登録され、追加5ファイルも指定分類に属する。

```python
success = (
    terminal_ok
    and not (attempt_dir / "failure.json").exists()
    and job_result["schema_version"] == "mocc-trace-pilot-job-result/v2"
    and receipt["schema_version"] == "mocc-trace-pilot-receipt/t1943-g2-v2"
    and receipt["status"] == "completed"
    and receipt_digest_ok
    and patch_binding_ok
    and result_binding_ok
    and classification_ok
    and receipt["gates"]["trace0_preprocess_identity_rc"] == "0"
    and receipt["gates"]["workload_rc"] == "0"
    and receipt["gates"]["verifier_rc"] in {"0", "1"}
    and receipt["gates"]["discriminator_rc"] == "0"
    and discriminator["conclusion"] in {
        "no-g2", "supported", "contradicted"
    }
)
```

**verifier rc=1 と job script の終了コード1は別です。** 前者は pilot:2239–2243、2278–2284、2985 で受理され、正常な finalization 後は3400行で job script 自体が0終了します。rc=0 の certified 経路と rc=1 の completed anomaly 経路を、どちらもこの成功条件に含めます。

cleanup 後に `BUILD_SOURCE` を親から再読する条件は追加しません。patched source の再読は receipt writer が source の存在中に行い、親は残された source digest sidecar と receipt の一致を確認します。

## should

**S1 — cache の「5 directory が存在する」は、T-548 後の hydrate 通過を覆いません。**

- **根拠:** fetch:334–441 は `.git` の実 directory、metadata、HEAD、clean、origin URL 等を検査します。621–694 は検証後に `--no-hardlinks --no-checkout` clone と再検証を行います。pilot:1534 の timeout は20秒です。
- **放置時:** interpreter 修正後も hydrate の cache 検証または timeout で止まり、patch 段へ到達しない可能性が残ります。
- **是正案:** 投入準備で現行 fetch の `verify` 契約に対する結果を記録する。これは既存契約の確認に留め、fetch の受理条件は変えない。20秒内の hydrate 完了は実 job の確認項目とする。

構造上の断線は見つかりません。fetch:728–729 は gflags/glog を sources に加え、760 は staging root を返します。pilot:1557–1558 はその直下を参照します。ただし fetch が読む共通 policy と pilot policy の pin 一致、および現在の cache の実内容は「5 directory」の記録だけでは確定しません。

**S2 — receipt の空引数契約を実装条件として明記してください。**

- **根拠:** plan:261–264 は三引数を追加し、T1943 分岐内で検査する設計ですが、mode 別の空値の意味が明文化されていません。pilot:2542 は argv 全体を tuple 分解します。
- **放置時:** general fixture の引数不足で receipt 全体が停止したり、T1943 の欠落値を記録だけで通す実装になり得ます。
- **是正案:** 全 mode で三引数を渡す。T1943 は非空 patch path・64桁 digest 二つと実 bytes／sidecar 一致を必須にする。general は三値を空に初期化し、patch を読まず、binding と追加 artifact を出さない。既存 v4 正例でこの経路を保持する。

source 再読は可能です。EXIT trap の登録は788行、通常経路の明示削除は3389行です。「3389行が EXIT trap」という説明だけは訂正が必要です。

**S3 — receipt 内の test 識別子に、参照であることを持たせてください。**

- **根拠:** plan:251–257、D297、D1686。説明文では区別していますが、receipt 単体の `trace0_identity_witness` には実行状態がありません。
- **放置時:** receipt の引用が、当該 compute job で patch 同一性 test を実行したという主張に読めます。
- **是正案:** 例えば `trace0_identity_test_reference` に改名し、`trace0_identity_test_executed_in_job: false` を添える。`trace0_built_from_patched_source: true` は build の配線事実として保持可能です。親が実行する既存 test の結果は insight に別記する。

**S4 — job-staging は worktree 外へ移りません。land 前の取扱いを定めてください。**

- **根拠:** pilot:57、76、submit:262–265。対象 path の `git check-ignore -v` は一致なしでした。
- **放置時:** `--attempts-root` を外へ出しても job-staging は untracked として残り、一般の clean 条件を要求する land 手順では止まり得ます。
- **是正案:** 「worktree は汚れない」を「submission 記録は外部、job artifacts は worktree 内の owned prefix」に訂正する。submit gate 自体はこの prefix を許します。land 前に既存運用での保持・移設方法を確定し、原本 path を insight と整合させる。今回だけのために `.gitignore` を広げる必要はありません。

## nit と過剰部分の整理

**N1 — patch 失敗途中の artifact による二重の分類失敗は、現経路では起きません。**

- **根拠:** manifest writer は pilot:635 で先に実行され、T1943 validator は2385行。patch block の明示 `exit 2` と EXIT cleanup は validator を呼びません。
- **成果物への影響:** 中途生成物は残りますが、numstat 失敗を分類失敗で上書きする経路ではありません。
- **是正案:** 5ファイルを writer に登録する plan を維持する。失敗時 validator や全 artifact の先行生成は追加しない。

**N2 — 空 stdout は出力捕捉の記録にはなりますが、apply 成功証明にはなりません。**

- **根拠:** plan の先行 truncate と `git apply --check`／`apply` の redirect。
- **成果物への影響:** 正常に無出力だったという operational diagnostic が残るだけです。
- **是正案:** 5 artifact 契約を維持するならその意味を明記する。削るなら stdout の生成・redirect・manifest・receipt・test を一緒に削る。通常は空ですが、常に空と保証する記述も避ける。

**N3 — general-mode の5 filename 登録は既存検査の追随であり、過剰な新 gate ではありません。**

- **根拠:** pilot:622–631、test:3918–3957。
- **成果物への影響:** 正常 general mode の artifact／receipt は変わりません。
- **是正案:** plan を採用。無生成の誤登録 entry も検出する既存方式に揃えます。

**N4 — interpreter 修正を fetch／parse 全体へ広げる必要はありません。**

- **根拠:** pilot:1539–1541 は `json`、`os`、`sys` のみ。F1027 の停止点は driver の推移 import。
- **成果物への影響:** `THIRD_PARTY_SOURCE_ROOT` 読取りを素の Python 3.9 に残しても、確認した本文には3.10専用処理がありません。
- **是正案:** 局所的な HYDRATE_PY 採用を維持。`CCBENCH_BASE` は cleanup 用に保持し、verifier 引数だけ分岐する。general mode の patch 適用拡張、objdump gate、consumer の schema 拡張は不要です。

**N5 — author 1本は妥当ですが、3600秒内の完了保証はありません。**

- **根拠:** plan の編集3ファイル、finalization fixture:3354–3554、receipt test:4566以降。
- **成果物への影響:** 静的に上限超過を断定できず、これ自体による成果物欠落は未確認です。
- **是正案:** 単独所有を維持し、hydrate → patch/source → receipt/schema の順に作業する。時間切れなら同じ所有面を逐次引き継ぎ、pilot と大型 test file を並列編集しない。実走待機・全受入・insight は親の作業時間に分ける。基本4本に収まらない場合は追加 fix の実数を報告する。

## 投入順序・実測値・文書成果物

待ち上限は `dev_wave_wait.py:228、1652–1654` の既定 **21600秒＝6時間**を明示採用する案が妥当です。これは queue 待ちを含む親の待機予算で、PBS の実行枠3600秒とは別です。期限に達しても再投入せず、当該 request の状態を記録します。

実装 commit と関連契約確認後に1本投入し、待機中に親の受入全走を進める順序を推奨します。ただし、変異検査を含め live source を変更する作業は投入元 worktree で並行しないこと。並行受入は同 commit の別 checkout を使うか、変更を伴う検査を投入前に済ませます。

一次資料との突合結果は次のとおりです。

| 記述 | 評価 |
|---|---|
| 4936の投入形 | operational-facts と一致。request ID と PBS_JOBID の混同だけ要修正。 |
| done path | `0:4936.nqsv` の記録と pilot の directory 構築が一致。 |
| cache に5 directory | 存在・前 runner の使用実績。現行 hydrate 契約適合と所要時間は別。 |
| gen_S queued 80／running 32 | 今回の依頼本文の時刻付き情報。指定 operational-facts 本文には当該数値がなく、現在値として再確認したものではない。 |
| T-1943の151秒 | T-548前の到達実績。分類段は失敗しており、今回の完走時間の実績ではない。 |
| 267741106 | 現物は3.9互換の stat 呼出。compute 上の分類通過実績はまだない。 |

insight の骨子は本題に沿っています。追加するのは **request ID／PBS_JOBID／nonce の対応、終端確認、実行時間とqueue時間の分離、cache/hydrate結果、分類段の実測結果**です。rc=0 の1走だけなら、rc=1 は fixture の被覆として記し、compute 実測に数えません。

F1027 fragment は hydrate 修正の実施・検知結果に限定します。後段で止まった場合は「hydrate 到達／通過」と「pipeline 未完走」を分け、恒久対応全体の完了を先取りしません。schema v2 の decisions fragment は1件で十分です。D14・D297・D1686 の再裁定や G2 根因の議論は追加不要です。

## 総括

- **must-fix：2件** — request ID／PBS_JOBID の区別と、終端・failure を含む成功判定。
- **plan の3変更＋verifier配線で生死確認が finalization まで通る見込み：不確実。** 静的に確定した次の停止段はありません。現行 cache の hydrate 契約適合・20秒制限、patched build、267741106 の実 compute 通過が未実測です。
- **待ち手へ渡す done file の確定 path 形：**
  `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2780-mocc-pilot-discriminator/output/env/pegasus/mocc-trace/job-staging/<実行環境のPBS_JOBID>/job-result.json`
  今回の Pegasus 実績では、request `N.nqsv` に対して **`<PBS_JOBID> = 0:N.nqsv`** です。
