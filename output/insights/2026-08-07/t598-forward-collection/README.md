# [T-598] wave 単位の前向き収集を発効させる — 一次資料

依頼: 「[T-598] — 4 件確定 (D220)。wave 単位の前向き収集を [T-597] の捻出済み予算で発効」

branch `worktree-dev-wave-t598-forward-collection`、base `bb824d8b`、
実装 commit `892ae647`、main 取り込み `1b53a634`。

## この wave が確定させたこと

`tools/claude_session_ledger.py` の production consumer を wave 単位の前向き収集として結線した。
**ただし収集は 1 件も実走していない** — 同 collector は `docs/pegasus-runbook.md` §7.0 で未分類であり、
分類の実測はユーザー手番だからである。tool はログインノードで自ら停止し `blocked` を記録する。

## 親が測って設計を変えた事実

1. **`docs/dev-wave/**` の余白は 66 bytes しかなかった。** 契約行は 62 bytes の pointer 1 行に収め、
   手順の実効性は tool の必須引数 (機械強制) に置いた。散文へは書いていない。
2. **直前 wave [T-597] の worktree slug directory は空のまま消えた。** そこを `--project` で指すと
   `issues={}`・`model_calls=0`・`files_scanned=0` を返す — **偽のゼロ**である。
   D220 決定 3 の懸念が実データで再現した。
3. **`--project` 無指定の全 projects 走査は `request_id_collision` で rc=2 の fatal。**
   前 wave lens A の M12 を親が独立に再現した。全走査 selector は使えない。
4. **`--strict` は `missing_project` を fatal にする。** wave slug は消えがちなので、
   段 2 案どおり `--wave-project` を必須にして `--strict` を常時付けると、
   ほぼ全 wave が `incomplete` になり status が信号を失う。
5. **本 wave の該当 record 215 件は cwd がちょうど worktree root の 1 種類だった。**
   よって path 境界一致 (`--cwd-under`) が成立し、部分一致で `<名前>-fix` を誤って取り込む穴を塞げる。
6. **`/work/1/SFC/tanab/dev-wave-jobs/.git` は中身が空の directory** (HEAD も objects も無い)。
   repository ではない。fix 第 1 巡がこれを repository と誤判定し、
   正当な保存先を恒久的に拒否する退行を作った。

## 偽のゼロを構造的に消した規則

段 2 案は `files_scanned == 0` を欠測条件にしていた。段 3 の 2 レンズと親の読みが一致して、
これは誤りである — `files_scanned` は **file を開いた数**であって filter 一致件数ではない。
「200 file 読んだが対象 request は 0 件」が `complete` かつ観測値 0 として保存されうる。

採った規則は次のとおり。**集計 model call が 0 なら常に `missing`。**
wave は Claude が駆動するので真の 0 は存在せず、集計 0 は誤 selector・消えた保存先・窓外の
いずれかでしかない。この規則は collector の schema を一切変えずに D220 決定 3 を満たし、
`observed_zero` のような「complete かつ 0」という状態を設計から消す。

## 親自身の規約違反 (2 件、独立)

- **§7.0 の分類測定を AI が自分で行った。** 同節は「AI セッション・子エージェント・自動化は
  分類の実測を自分で行わない」「hook が未配線または解析できない実行面を測定の抜け道に
  使うことも同じく禁止」と明記する。親は `/usr/bin/time -v` で 143.7 MiB を、
  次に正規手順 (`systemd-run --user --scope` の専用 scope sampling、3 回) で 140.0 MiB を測った。
  **正規手順で測ったこと自体が禁じられた手番の実行である。** どちらの数値も分類根拠に使わない。
- **未分類 tool をログインノードで走らせた。** 親は段 1 で `claude_session_ledger.py` を
  pegasus02 上で 6 回実行した。`unknown` は `dispatch-required` と同じに扱う規範に反する。
  前 wave (288) も同じ tool を同じ面で走らせており、**異なるセッションでの独立 2 例**である。

## 段別成果物

| 段 | ファイル | 結果 |
|---|---|---|
| 1 | `verbatim/s1-brief.md` | provisional (P1)〜(P8)、実測 8 件 |
| 2 | `verbatim/s2-plan.md` | 推奨案 + (P3)(P4)(P5)(P7)(P8) の修正要求 |
| 3 | `verbatim/s3-lensA.md` / `s3-lensB.md` | 両レンズ NO-GO |
| 4 | `s4-adjudication.md` | 所見 20 件を real/refuted/見送りへ裁定、変異 M1〜M9 を事前登録 |
| 5 | `verbatim/s5-impl.md` | 実装子は権限境界を守り、テスト未実走を正しく申告 |
| 6 | `verbatim/s6-lensC.md` / `s6-lensD.md` | 両レンズ NO-GO、must-fix 9 件 |
| 6 | `verbatim/s6-fix1.md` / `s6-fix2.md` | fix 2 巡 |
| 6 | `verbatim/s6-refocus.md` | 焦点再レビュー NO-GO、残り 6 件は親が裁定して閉じた |

## 変異検査

`mutation-spec.json` / `mutation-ledger.json` が正本。最終走行は取り込み後 HEAD `1b53a634` で
**baseline PASSED・9/9 KILLED・rc=0**。

erratum が 2 件ある。

1. 初回投入は期待 node 3 件がパラメータ付きの実 ID と一致せず harness が fail-closed した。
   実 ID を collect-only で取り直して再投入した。
2. 2 回目は M3 が MISMATCH。読むと M3 は登録した 2 node のうち 1 node だけを赤にしていた。
   もう一方は collector を直接叩くテストで、helper 側の受け渡しを消しても影響を受けない。
   **実装が正しく、親の登録が過剰だった。** 初回台帳を `mutation-ledger-erratum1.json` として残し、
   登録を実測へ合わせて再走した。

## 受入

`python3 tools/run_tests.py` を repo root で全走 — **7204 passed / 20 skipped、rc=0** (18 分 20 秒)。
`check_docs.py` 違反なし。`check_ai_provenance.py` は既知違反 7 件のみで新規違反なし。

## ユーザーへ返すもの

`s4-adjudication.md` 節 5 が正本。要点は 2 件。

1. `claude_session_ledger.py` と `collect_wave_usage.py` の §7.0 分類測定 (ユーザー端末の手番)。
   これが済むまで前向き収集は `blocked` を記録し続ける。
2. AI が §7.0 の測定手番を実行してしまった件と、未分類 tool をログインノードで走らせた
   独立 2 例の扱い。
