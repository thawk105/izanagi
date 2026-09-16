## 所見一覧 (real / refuted、各 1 行の成果物影響つき)

**P1 は現行 CLI を呼ぶ形として成立する。ただし、段 2 の argv はそのまま投入できない。投入元の非書込み条件と、計算ノードの単独性確認が未充足である。**

| ID | 分類 | 所見と成果物への影響 |
|---|---|---|
| A1 | **real** | CLI は投入元 CCBench を patch し、Git 管理情報も更新する。放置すると README の「指定領域以外へ書かない」が事実と異なる。 |
| A2 | **real** | `_assert_single_tenant()` は競合 `ycsb_*.exe` の検査に限られる。放置すると他の高負荷処理がある測定を「単独性確認済み」と記録しうる。 |
| A3 | **real** | prefix の永続記録と `compiler_input_dependency_prefix_roots` を混同している。放置すると receipt が証明する依存 provenance を過大表示する。 |
| A4 | **real** | 同版・共通 prefix は A-5 と同じ依存 binary を意味しない。放置すると今回の緑を A-5 環境との等価性まで一般化する。 |
| A5 | **real** | 前回の直接 DNS 失敗は proxy 経路の不通を示さない。放置すると取得成功・失敗の原因を誤って帰属する。 |
| A6 | **real** | 親の関門・build 回数と時間上限の読みが誤っている。放置すると walltime 終了を関門固有の赤と誤認しうる。 |
| A7 | **real** | screening baseline の meaning は `unestablished`。放置すると WAL の間接証拠を「両腕の直接 green record」と誤記する。 |
| A8 | **real** | dispatch rc=16 は未実行を意味しない。放置すると完走後の証拠収集障害でも再測定し、「1 走」の記録を失う。 |
| A9 | **refuted** | 「A-5 改修が正規 CLI 利用の必須条件」は成立しない。現行 `main` と generic dispatch で到達できる。 |
| A10 | **refuted** | 「`-I` が `IZANAGI_*` を消す」は誤り。任意環境変数の読取りは残り、供給は失われない。 |
| A11 | **refuted** | 「bench lock は job 固有にする必要がある」は支持できない。固有化すると既定 lock を使う他 job との協調排他を失う。 |
| A12 | **refuted** | 「`TMPDIR=/scr` だけで関門判定が変わる」は支持できない。一時名・lock・証拠回収の差はあるが、追加の関門改修理由にはならない。 |

## (P1) 投入形の裁定案

**(a) の入口解釈を支持し、現状の不変条件を維持するなら (c) の最小 launcher を採る。(b) の A-5 改修は不要。**

[backoff_sweep.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/backoff_sweep.py:511) の `main` は既存の `--screening` と `--screening-fixed-us` を `run_workload` に転送する。generic は argv を直接実行するため、内部関数だけを呼ぶ probe とは違い、今回要求された CLI 入口を通る。

一方、A-5 は現物でも次の制約を持つ。

- [job body:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/a5_second_boot_backoff_sweep.sh:581) は workload だけを渡し、`--screening` を付けない。
- 同 file:607–608、641–653 の finalize は **8 genome 全 commit・abort ゼロ**を要求する。
- [submitter:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/submit_a5_second_boot_backoff_sweep.sh:92) は `write-heavy balanced` の 2 workload を投入する。

したがって A-5 をそのまま使うと、本件の「1 workload・2 genome・1 走」から外れる。「既存 A-5 投入 script を使用した」とは記録せず、**「既存 generic dispatcher から現行 screening CLI を実行した」**と記すべきである。

ただし、直接 argv のままでは A1 が残る。[backoff_sweep.py:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/backoff_sweep.py:433) は投入元を `patchharness.applied` に渡し、[patchharness.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/patchharness.py:255) が実際に変更する。checkout も同 file:362–374 で元 repository の worktree 管理情報を更新する。

推奨する job dir の launcher は、同じ 1 job 内で次だけを行う。

1. 割当ノードで単独性を確認し、その観測を stdout に残す。
2. exact HEAD と CCBench pin の独立した実行木を用意する。
3. 決めた環境を供給し、現行 CLI を 1 回だけ呼ぶ。

元 repository の管理情報も保護するなら、A-5 の共有 Git worktree をそのまま写すだけでは足りない。前回 [probe PBS:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:258) の独立 clone が近い先例である。

これは**新しい一時 launcher の実装**ではある。production の screening 入口や関門を新設するものではないが、「実装作業までゼロ」とは呼べない。親 brief が要求する Codex author とレビューを適用し、production 無編集・repo の実装差分ゼロは維持する。

[D1786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/docs/decisions.md:54122) はこの選択と矛盾しない。新しい投入実行体を repo に登録せず、既存 dispatcher を使う。ただし、禁止された実行体を repo 外へ複製して迂回する許可ではない。

## 環境の等価性

A-5 と P1 は**同じ関門実装を使うが、実行環境と証拠一式は等価ではない**。

| 段 | 現物との差と成果物への意味 |
|---|---|
| 前提検査 | A-5:179–238、261–406 は入力・HEAD・allocation・boot・reservation を照合する。generic の request hash・hostname・会計照合はその全部を代替しない。A-5 の実行証明とは呼べない。 |
| Python 選定 | A-5:199–208 は検査した実体を直接使う。generic:892–913 が選ぶ interpreter と任意 argv 内の interpreter は別。段 2 の `python3.10` 明示は改善だが、launcher でも実際に使う実体を検査・記録する。 |
| env 消去 | A-5:221–231 は unset、generic:1442–1452 は allowlist。後者へ prefix・proxy 等を明示再供給する形は成立する。 |
| 依存 build | A-5:524–568 は pinned-clean source から job 内 build。P1 は既存 install prefix を使う。header・library・build provenance の同一性は未証明。 |
| `ENV_TAG` | A-5:570–577 は検査用ローカル変数。CLI も `p2_2.py:235–253` の site/contract 解決と required attestation を通るため、変数の export は不要。 |
| output root | A-5:240–255 は未作成 root を要求。`layout.py:323–367,412–447` は既存 root も許す。今回の新規 attempt は親が未使用 root で確保する必要がある。 |
| TMPDIR | A-5:257–258 は job 固有 0700 directory。P1 は `/scr` 直下。関門式は変わらないが、証拠回収と lock の範囲は同じではない。 |
| bench lock | A-5:259 は job 固有、P1 は既定共有 lock。同じ lock を使うプロセス間の排他範囲が変わる。 |
| sweep 起動 | A-5:581–583 の通常 sweep に対し、P1 は既存 screening 分岐を選ぶ。これは今回意図した入力変更である。 |
| finalize | A-5:641–653 は対象外。今回の WAL・child rc・stdout を用いた 2 点 screening の判定を行う。 |

**P3: prefix の読みは限定付きで支持する。**

既存 install の version file は gflags `2.2.2`、glog `0.5.0`。静的 archive の存在と、両 archive の作成・更新日時が 2026-08-25 であることも確認した。ただし、これだけで policy の exact source pin や A-5 の build options と同じ binary とは証明できない。

記録先は次のとおりである。

- [buildcache.py:2624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/buildcache.py:2624) は ambient `CMAKE_PREFIX_PATH` を正準化する。
- 同 file:1330、2681–2685 はそれを `preimage.dependency_prefix` として build digest に含める。
- 同 file:3050–3057 はその preimage を **`completion.json`** に保存する。
- `compiler_input_dependency_prefix_roots` は同 file:688–689 にあるとおり **live validation 用で、completion/receipt に保存する field ではない**。さらに今回の呼出しでは source snapshot 条件が揃わず、2633–2636 により空になる。

したがって段 2 の訂正方向は正しいが、親の「receipt の prefix roots に記録」は field 名と意味を訂正すべきである。prefix の**パス**が identity に入ることは、既存依存 archive の内容まで個別に束縛することではない。

supply 比較では、要求側・対照側が同じ ambient prefix を継承する。[condition_meaning_gate.py:1581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/condition_meaning_gate.py:1581) の subprocess に環境置換はなく、同 file:2465–2535 が両側を preprocess する。このため、**A-5 との prefix 相違そのものが、今回の比較の左右差になるわけではない**。

ただし「比較結果には一切影響しない」は強すぎる。prefix は include 内容・configure 成否・link 対象を選ぶ。判定はその依存環境を条件として成立する。stock 比較では非 inert 用の `dependency-closure-drift` 判定を通らず、preprocess 同一性または root-location-only の判定へ進む点も現物で確認した。同 file:2625–2698。

link 成功の先例が無いことは未測定の限界として扱い、別の試走は追加しない。本題の build で失敗したら **`build-error` と linker 詳細**を保存する。「同版だから成功する」「link 赤は必ず外部 infra 原因」とは先取りしない。

**proxy 経路は直接 DNS と別である。**

CCBench の `ThirdParty.cmake:35–55,109–115,135–142` は HTTPS の Git repository を FetchContent で取得する。Git は通常 `http_proxy`・`https_proxy` を利用し、HTTPS は HTTP proxy への CONNECT 経由になる。対象ホストの直接 DNS 失敗だけでは、この経路の失敗は導けない。[Git 公式文書](https://git-scm.com/docs/git-config#Documentation/git-config.txt-httpproxy)、[curl 公式解説](https://everything.curl.dev/usingcurl/proxies/http.html)。

前回について確定できる事実は以下である。

- `probe.py:557–580` は `socket.getaddrinfo` と直接 socket 接続を検査している。
- [前回 sweep evidence:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/sweep.json:119) の失敗は、その `getaddrinfo` に対応する。
- PBS:215 は third-party cache 変数を export するが、production prepare はその変数を読まない。実測 commit `c3447612…` の buildcache も確認した。
- PBS は proxy を明示 export していないが、proxy を消去する clean env でもない。

**推定:** 計算ノード側から継承した proxy 環境などを Git が使った可能性が高い。runbook:824–835 に計算ノードの profile が proxy を設定する先例がある。一方、前回 evidence には実効 proxy 環境や Git transport の記録がなく、継承元までは確定できない。「cache 変数が offline 取得を成立させた」という説明はコードから支持されない。

今回の明示 proxy 供給は妥当だが、当該 job での取得成功は本走で判定する。

**`-I`、lock、単独性。**

`/usr/bin/env IZANAGI_CONSULT_ENV_CHECK=visible python3.10 -I -B ...` の書込みを伴わない確認では、`isolated=1`、`ignore_environment=1` でも値を読めた。A10 は refuted。

[lock.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/lock.py:24) の既定 lock は HOME から解決され、generic は HOME を継承する。同一ユーザーの同じ lock を使う job と競合し、blocking 取得で待ちうる。共有 HOME の配置なら別ノードの job と待ち合う可能性もあるが、今回の実測はない。これを理由に job 固有化する必要はない。待ち時間は walltime に含まれる。

単独性は別問題である。[runner.py:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/calibrator/runner.py:382) の検査対象は `ycsb_.*\.exe`。他の計算・build は対象外で、`settle()` も271–290行で時間切れ後に続行する。required attestation は機体特性の照合であり、専有 allocation の証明ではない。

batch では、割当ノードが決まる前の確認では満たせない。**同じ 1 job 内で、CLI 起動前に割当ノードの pgrep・load average・競合負荷の観測を行い、競合があれば計測を開始しない**形を採る。「投入前」は scheduler への割当要求前と計測開始前を区別して親 brief に明記する。新たな全般的検査機構への拡張は不要である。

## 所要と walltime

段 2 の回数訂正を支持する。

| 対象 | 検算 |
|---|---|
| prepare | driver・baseline・候補の **3 回** |
| supply request | driver 2 件＋screening 各 1 件の **4 件** |
| 完全 build | trace/perf 各 2 genome の **4 build** |
| throughput 時間窓 | `3秒 × 5 reps × 2 genome = 30秒`。最大 3 rounds なら90秒。初期化・終了処理は別 |
| correctness | baseline と、screening 棄却されなかった候補に legacy 検証 |

根拠は `backoff_sweep.py:444–451`、`screening_driver.py:197–210`、`pipeline.py:2017–2018,2594`、`p2_2.py:54–57`。

**通常 10–30 分、walltime 90 分は事前予算として採用可能だが、完走上限ではない。** 20.2 秒は過去の単一観測からの外挿である。prepare は configure/target 各900秒で、3回分だけでも90分に達する。関門の120秒は各 subprocess の上限であり、通常 build の timeout は既定 `None`。

[dispatcher:3932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/dispatch_compute.py:3932) 以降の式は次のとおり。

- 初期期限：`submitted_at + 5400 + 3600`
- 最初の正常な RUN 観測後：`run_observed_at + 5400 + 3600` に再設定
- `queue-wait-timeout=3600`：RUN 未観測の待ちを制限
- 終端後：別に既定60秒の成果物収集猶予

したがって段 2 の「queue 待ち込みで監視段は概ね3時間30分」は妥当。ただし poll・scheduler 操作・cleanup を含む厳密な全処理上限ではない。**`overall-grace` は PBS の90分 walltime を延長しない。**

## 1 走だけの制約

**再投入可否は rc の名前ではなく、本題の CLI が実行されたかで分ける**裁定を推奨する。

| 状況 | 裁定案 |
|---|---|
| submission disabled、投入前失敗、未開始と証明された queue timeout | 本題未実行。記録を残し、原因解消後の投入を許す。 |
| rc=16 だが child の実行有無が不明 | 再投入しない。receipt・result・stdout・WAL を先に照合する。 |
| CLI 起動後の proxy 不通・prepare 失敗・link 失敗 | 今回の赤として終了する。緑が出るまで再投入する運用は「1 走」と扱わない。 |
| bench/commit 後の会計・ログ・receipt 障害 | 証拠回収を試みる。再測定で置き換えない。 |
| production 内の既定 remeasurement | 同じ1回の CLI に含まれる既存動作として数える。 |

`dispatch_compute.py:4148–4164` には、child 終了後の receipt 永続化失敗でも rc=16 を返す実経路がある。したがって「infra 赤なら未走として再投入」は refuted。赤を成果物にする親 brief の方針を維持する。

## 親 brief の誤り

| 前提 | 裁定 |
|---|---|
| 1 CLI | **支持。** bootstrap と既存 `main` を確認した。 |
| 2 A-5 | **支持。** さらに submitter 自体が2 workload固定である。 |
| 3 generic | 概ね支持。ただし allowlist の locale は任意の `LC_*` ではなく `LANGUAGE/LC_ALL/LC_CTYPE` 等の列挙。これは nit。 |
| 4 環境 | **訂正必須。** prefix の永続記録は `completion.preimage.dependency_prefix`。一時 validation roots field と混同しない。直接 DNS と proxy の経路も分ける。 |
| 5 既存 prefix | 版・静的 archive・2026-08-25 の日時は支持。同版から exact pin build・同一 binary・link 成功までは導けない。 |
| 6 calibration | 現行コードの照合経路は支持。ただし strict attestation は driver gate の後にあるため、「driver gate まで到達」だけでは通過証明にならない。 |
| 7 request と関門 | 今回の新規 baseline について支持。「無条件」は全 caller・再開状態へ一般化しない。候補には terminal state の early return がある。 |
| 8 単独性 | **不足。** pgrep の対象範囲を超えて単独性を主張できない。18 RUN / 0 QUE も割当ノードの競合不在を示さない。 |

ほかに次を訂正する。

- **P1 と書込み不変条件は両立していない。** 終了時の revert は投入中の非書込みを意味しない。
- **P5 の「関門×2・build×2・各時間以内」は誤り。** 段 2 の回数と予算表現へ直す。
- **「screening が赤のまま」は現在の実測結果ではない。** 正確には「最後に観測した screening は赤で、供給実装後は未測定」。
- **緑の意味は stock supply 緑・family admission の間接証拠。** `backoff_sweep.py:325–327` の baseline declaration は `None` となり、`condition_meaning_gate.py:3335–3341` は meaning を `unestablished` にする。4098–4108行の admission はこれを許す。

## must-fix / should-fix / nit

**must-fix**

- 投入元を実際に変更する P1 と、非書込み不変条件の衝突を解消する。
- 同じ割当ノードで計測前の単独性を確認する手順を具体化する。pgrep のみを専有確認と呼ばない。
- prefix の保存 field、baseline meaning、時間上限、DNS 観測の射程を成果物の主張へ正しく反映する。
- rc=16 を含む再投入の条件を、実行開始の証拠に基づいて固定する。

**should-fix**

- 生成済み `completion.json` を証拠として回収し、既存 prefix のパスが build identity に入ったことを追跡可能にする。
- README に実行木、実際の Python、lock path、A-5 との差を記す。
- launcher を採る場合、その bytes と実行結果を今回の証拠へ含める。

**nit**

- generic の locale allowlist の略記。
- `/scr` 直下か job 固有 directory かという整理上の好み。
- 未観測の link 故障を先回りして新しい試走・検査機構を足す要求。

## 総括

**現行 CLI＋generic dispatch の入口解釈は採用できる。A-5 改修は要らない。現状の argv は、実行木の隔離と単独性確認を具体化してから投入すべきである。**

既存 prefix と明示 proxy は、限定した生死確認の入力として採用可能。ただし、得られる結論は**その環境での baseline stock supply と family admission の通過**であり、A-5 環境との等価性や両腕の直接 green record ではない。

指定7資料を読了。静的検査と任意環境変数の読取り確認のみを行った。pytest・build・計測・編集・job 投入は実施していない。