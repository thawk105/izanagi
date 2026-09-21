## 対応表判定

以下、`J/`＝指定 job directory、`V/`＝その `verbatim/`、その他は worktree 相対パス。

| 所見 | 判定 | 根拠 |
|---|---|---|
| 1 | **closed** | `V/DW-M07-M08.after2.md:3,17`。「対象commit」は直前のDW-M07と同じ対象を指すと読める。`PYTHONPATH=. python3`は単独で貼り付ける完全なコマンドではないが、「自走harness」と実行対象fileの文脈があり、`orchestrator/tests/README.md:107–109`のfile実行規約と整合する。復元後の`--porcelain`空確認は、参照を残した`V/DW-O19.md:3–7`の変異前clean・単一変異diff・checkout復元・commit bytes照合に**追加**されている。 |
| 2 | **partial** | `J/brief-v2.md:4`は1分／2分の同一視を撤回しており、その部分は解消。ただしmtimeから「≤90秒」および「両者はこのmtimeの粗い読み」とする根拠は不足。下記所見1。 |
| 3 | **closed** | 元の反証を維持。`V/test_check_docs_run_harness.py.txt:15–24`と`orchestrator/tests/skiputil.py:24–32`から、collect-onlyの一致では実行時skipの扱いまで保証できない。 |
| 4 | **closed** | `J/brief-v2.md:9`で「具体例の明示、新しい防壁ではない」へ訂正済み。依頼の名指し要求も`V/origin.md:7–8`にあるため、削除不要。 |
| 5 | **closed** | `J/brief-v2.md:8`で意図的な非固定と明記。fig13の出力は`orchestrator/tests/test_plot_b10_waiting_grid_forest.py:677,688,692`、別harnessは`V/test_check_docs_run_harness.py.txt:11–23`で実際に異なる。 |
| 6 | **closed** | `V/DW-M07-M08.after2.md:16–17`。skipはpytest依存条件の列挙として読め、完全一致・復元義務の緩和なし。 |
| 7 | **closed** | 今回は独立再集計できた。L1.5＝**9689／9696**、M08＝**1178 bytes**、予算検査の`findings=[]`。分類は`tools/check_docs.py:5304–5315`、集計は同`:5346–5366`。 |
| 8 | **closed** | `J/brief-v2.md:11`は「節ID在庫・dispatch配置・層予算」に修正され、前巡の表現上の指摘に応えている。`tools/check_docs.py:856–858,5292`、`orchestrator/tests/test_check_docs.py:2811–2822`とも整合。 |
| 9 | **closed** | `J/brief-v2.md:9`は空振り回数を未実測と明記。skiputilによるERROR化の説明も、上記harnessとskiputilの実装に一致する。 |
| 10 | **closed** | `V/DW-M07-M08.after2.md:17`は手順とfallbackの具体化。新gate・台帳・判定方式の追加ではなく、`V/origin.md:10`の範囲内。 |
| 11 | **closed** | 前巡で欠けていたentry・比率・先行commitの記録は`V/worklog-1774-head.md:1,10,16`、fold・tested_tipは`V/FOLDED-5133-5134.txt:1–2`で確認できる。ただし19〜24%は記録値の照合であり、元の12 waveを独立再解析した結果ではない。 |
| 12 | **closed** | `V/D2195.md:3`は失敗集合とcollection集合の一致、`V/DW-M07-M08.after2.md:17`は全nodeの照合可能性と変異ごとの失敗観測を分離している。`J/brief-v2.md:12`はこの相違を正しく説明する。worklogへの追記実施までは今回の射影で未確認。 |

削減は、commit diffの削除行・追加行から本文を別々に再構成して検算した。空白除去後の差分は次の4箇所のみで、親のsemantic_diffと一致した。

- 追加：`対象commitの木へ`
- 追加：`` `PYTHONPATH=.python3`の ``（空白除去後の表記）
- 置換：`の` → `で`
- 追加：`` と`--porcelain`空 ``

F71・F33・DW-O19、停止条件、完全一致、fallback列挙、diagnostic別枠、新旧両走の義務はすべて残っている。実際の増減は**追加65 bytes − 空白58 bytes − 改行6 bytes＝純増1 byte**。

M08は**1170→1177→1178 bytes**。上限3定数は両commitで同一で、fixの変更ファイルも`docs/dev-wave/mutation.md`だけだった。改訂抜粋・HEAD blob・作業木本文も一致した。

## 所見

1. **real / should — mtimeの時刻差を実行時間の上限としている。**
   `J/brief-v2.md:4`、`V/fig13-probe-mtimes.txt:1–6`。時刻差90秒は確認できるが、script更新時刻は実行開始時刻ではなく、初回logはそれ以前に存在する。1分／2分という記述の算出由来もこの資料では証明できない。
   **放置時の影響:** ファイル更新時刻の差が、20変異全体の実測時間・上限として再引用される。

2. **real / nit — 削減内訳の改行数が誤っている。**
   `J/brief-v2.md:10`、`V/commit-956cce1c9.txt:27–40`。段落内改行の削減は9ではなく6。追加は正確には65 bytesで、総量9689という結論は正しい。
   **放置時の影響:** D782の削減内訳を再計算した際に説明と一致しない。

3. **refuted / nit相当 — 詰め書きの不揃いを修正必須の欠陥とは数えない。**
   `V/mutation.md.before:14–26,30–53`、`V/DW-M07-M08.after2.md:15–18`。節間の体裁差は既存で、今回も語の結合による条件の変化はない。`FAIL / ERROR`と`conftest / autouse`の区切りも保持されている。
   **放置時の影響:** 視認性の差に留まり、手順の誤読を具体的には認めない。

## 改訂 docs への訂正

**DW-M08本文：なし。**

briefは次のとおり訂正する。

`brief-v2.md:4`のmtime説明：

> fig13 job dir の mtime は `login_probe.py` が20:19:35、`login-probe-2.log` / `mutation-spec-v3-final.observed.json` が20:21:05で、差は90秒（2026-09-20）。初回 `login-probe.log` は20:19:03。これはファイル更新時刻の差であり、20変異全体の実行時間上限や、1分／2分という記述の算出由来は確認できない。両記述は統一しない。

`brief-v2.md:10`の削減内訳：

> 収容65 bytesは、DW-M08内の空白58 bytesと段落内改行6 bytesの削減で捻出し、純増1 byteに収めた。

## 総括

**GO（手順の収容として）。** 002f926f4＋956cce1c9で前巡の手順上の不足は解消し、義務を維持したまま予算内に収まっている。「実装しない」へ戻す理由はない。

briefには上記2点の訂正が必要だが、DW-M08への追加は不要で、残7 bytesを消費しない。静的検査と予算再集計のみ実施し、pytest・受入全走の合格は主張しない。