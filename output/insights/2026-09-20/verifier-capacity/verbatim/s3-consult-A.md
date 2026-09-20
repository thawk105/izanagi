## 指摘

以下、`plan` は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/codex/s2-plan.md)、`brief` は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/s1-brief.md)、`facts` は [facts.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/refs/facts.md)。コードの行番号は指定 worktree の現行ファイルを指す。

1. **観点1 — packed 化の退避と genesis の集計条件を明文化する。重み: should**  
   `plan:65–68`、`dsg.py:258–287`。first-writer、異なる writer の各 write occurrence、版の辞書式順序を保存する方針は正しい。ただし現行の `genesis_commits` は **write がない txn も一度数える**。write ordinal だけでは、その note の位置を再現できない。また範囲外 write を途中で見つけて旧 builder を呼ぶ場合、既に加算した integrity を残すと二重計上になる。  
   **修正案:** txn 開始イベントと write イベントを含む順序を定義し、退避時は producer・versions・integrity をすべて未構築状態へ戻す契約と、その境界 test を追加する。

2. **観点1 — txid 直接 index は成立するが、last-wins の辺を固定する test が不足。重み: should**  
   `plan:107–113,180,187`、`parse.py:719–753`、`test_verifier.py:780–795,2804–2816`。現行 compact graph の辺端点は winner の txid だけなので、穴があっても `U≤2N` と source root 保存で直接 index は使える。dup も winner 選択を変えなければ同じ辺になる。しかし既存 dup test は拒否と旧新並列一致を確認するだけで、消えた旧 writer の辺までは固定しない。  
   **修正案:** 同一／別ファイルの last-wins により旧 writer が消え、旧版 read が orphan になる例を追加し、辺集合・全 stats・integrity を literal で固定する。欠番を含む cycle と destination-only node も同じ検査対象にする。

3. **観点2 — JSON bytes 一致は全 integrity 同一性の代用にならない。重み: must-fix**  
   `brief:27`、`plan:171,228–231`、`report.py:112–132`、`model.py:442–447,450–467`。`result_to_dict` は `expected_commits`、`observed_commits`、`proof_surfaces` の生値を出さない。これらが違っても `clean` と notes が同じなら JSON は一致する。また fixture 全件＋校正3 sは有限の回帰証拠であり、任意入力の辺集合・SCC 同一性の証明にはならない。  
   **修正案:** JSON 全体比較に加え、非 wire integrity field と小さい境界 trace の全隣接・SCC を比較し、「一般的な不変性の論証」と「測った入力の一致」を受入記録で分ける。

4. **観点2 — A 推奨は妥当。B の影響を witness 以外にも明記する。重み: should**  
   `plan:135–149`、`dsg.py:364–382,439–456,489,525–545,573–592`、`test_verifier.py:1837–1842,2647–2669`。set 順は Tarjan の探索・同サイズ SCC の報告順・BFS の witness 選択へ伝播する。選ばれる cycle が変われば reasons と G 分類も変わりうる。一方、WW reasons 自体は既に key 順、WR/RW reasons は read 行順であり、未整列 set の直接列挙ではない。  
   B でも**辺集合・SCC・integrity を保存するなら verifier の受理集合は変わらない**。しかし anomaly digest、報告上限で残る witness、下流の constraint class は別問題で、裁定パッケージが必要。D1817 は WW 理由の局所整列であり、全隣接の canonical 化を要求していない。  
   **修正案:** A を採用し、同一性の実測条件に Python 実装・版・整数幅を記録する。B は別裁定へ分離する。

5. **観点3 — task 完全性と source replay 完全性が混同されている。重み: must-fix**  
   `plan:86–90,247`、`dsg.py:99–107`。既存 task の件数・index 集合検査は保存される。しかし、その後の破壊的な `run_src` 再利用と source 範囲 replay について、全範囲をちょうど一度処理したことの実行時検査は明記されず、リスク表では「test」に留まる。task が全部届いていても、リンク／範囲の欠落は辺を落とせる。なお本案は親 replay の分割なので、追加の「worker bucket 受領検査」があるわけではない。  
   **修正案:** CSR 公開前に、予定範囲の件数・index 集合一致、全 run の一意到達、消費候補数の一致を検査する契約を追加する。不一致時は部分 CSR を捨て、破壊済み run を再利用せず全 task を再計算する。

6. **観点3 — freeze の親側復元は書かれているが、子の GC 状態と initializer 順序が未定義。重み: should**  
   `plan:78,192,217`、`dsg.py:94–96,325–345`、`test_verifier.py:2293`。pool 生成前 freeze／shutdown 後 finally は方向として妥当。ただし fork は最初の submit で起こる。親で GC を disable するなら子もその状態を継承するため、initializer での扱いを決める必要がある。freeze された state/header を子が参照すること自体は避けられず、refcount CoW は残る。  
   **修正案:** 「親の状態保存→必要なら disable→freeze→submit/fork→子 initializer で GC 方針適用→shutdown→親だけ所有分を復元」の順序と、constructor／submit／initializer／future failure 各点の復元 test を明記する。

7. **観点4 — PID 消費の留保は解消できるが、T126 identity の帰結は未点検。重み: should**  
   `plan:169,178,196,252`、`commit_receipt.py:534–579,605–611`、`core.py:248–266,311–316`。指定された receipt／core に `_LAST_*_WORKER_PIDS` の参照はない。認証は capability の発行 PID と authority に依存し、診断 PID 集合とは別である。成功時は採用 outcome、再計算時は親 PID とする設計は既存 test と整合する。新 file 禁止も守られている。  
   既存 campaign lock の drift は D1552 抜粋とも一致するが、T126 code identity の再利用・再発行範囲は plan にない。該当実装は今回の射影外なので確認済みとは言えない。  
   **修正案:** 段4資料に campaign lock と T126 の旧 identity／新 identity／再利用可否の対応表を追加し、「新規 lock は影響なし」を「改修後 bytes で新規生成できる」に限定する。

8. **観点5 — Private_Dirty の残差だけでは CoW を同定できない。重み: must-fix**  
   `brief:37`、`plan:49–53,80,158`、`dsg.py:120–129,170–183`。worker は出力配列以外にも source dict、配列容器、decode object、転送中コピーを作る。出力 payload を差し引いた Private_Dirty の増分にも新規 allocation が残るため、MemAvailable 低下との一致だけでは親ページの CoW と区別できない。`Private_Dirty / parent RSS >1` も原因固有の閾値ではない。swap と fallback は同時発生しうるので二者択一でもない。  
   **修正案:** 現行の指標は「私有記憶量増大」の証拠とし、出力を分離した対照 probe で共有入力走査による増分を測る。swap／worker 終了／pool failure／fallback は独立したフラグと時系列で報告し、未分離なら原因未同定とする。

9. **観点5 — profile 契約と採否閾値の接続、対象入力がまだ不足。重み: must-fix**  
   `brief:43,50`、`plan:49,70,80,102,112,155–165,261`、`facts:9–16,25–26`。brief の profile 項目だけでは `parent_rss_at_fork`、fallback 回数、phase peak の開始／終了境界まで保証されない。閾値は提案と明記されており採用済みではないが、両6 s入力は balanced／read-heavy で、未完走型の write-heavy は候補比較の必須入力に入っていない。また facts の完走行は **6件**であり、plan:261 の「7件」は誤り。12 verdict の一覧と read-heavy 10 s の保全情報も射影では確定できない。  
   **修正案:** 段4で入力 manifest と観測 schema・派生式を一括固定し、write-heavy の候補比較を加える。未着 profile／未確定入力がある間は採否を保留する。

10. **観点6 — 「3 s に固定」「永久に得られない」は実測の射程を超える。重み: should**  
    `brief:8,15,38`、`facts:10,13,16`、`plan:230–235`。現行でも write-heavy／balanced の6 sは完走している。10 s×3 workload の成功が示すのは、その fixed-5 trace と環境での容量改善まで。600 s 校正規則、seed の記録・変更、最終対象候補での再検証、さらに長い trace の容量は別である。plan:235 の限定は妥当。  
    **修正案:** brief の成果物影響を「保全済み fixed-5 trace の容量障害を除く。B-8 完了は主張しない」に置き換える。

## brief の誤り

- **P3(a), brief:37:** `18.8×2³⁰ / 47,250,018 ≈ 427 B/write`、`85.6×2³⁰ / 594,786,279 ≈ 155 B/edge`。いずれも報告された maxrss 全体の比率で、producer／隣接単体の単価ではない。commit tuple と txid は txn 内で共有される（`dsg.py:258–285`）。
- **P3(c), brief:37:** facts:11 の6 s比較値は **817 s**で、816 sではない。「主 process CPU」という表現も、facts:18 の worker CPU 合算という説明と区別が必要。
- **P3(b)(c):** CoW、OOM、swap／圧縮 memory は未同定の仮説。SIGKILL・timeout・maxrss だけでは確定できない。
- **P5(ii)(iv), brief:39:** 「配列だけ読む」「txid は dense」は全入力の前提として成立しない。plan の header 参照の留保と密度 guard が必要。
- **brief:15:** 「長さは3 sに固定」「永久に得られない」は根拠を超える。

## 段 4 で親が決めるべき裁定項目

- **P2:** A＝set 由来順を保存／B＝canonical 化と digest 変更を承認。**推奨: A**。
- **同一性の受入:** JSON hash のみ／非 wire integrity・境界 trace の全辺・SCC も比較。**推奨: 後者**。
- **P3:** 私有記憶量増大を CoW 確定と扱う／対照 probe まで原因未同定とする。**推奨: 後者**。
- **freeze:** 配列化と一括採用／子 GC 契約と追加効果を確認して独立採否。**推奨: 独立採否**。
- **着手条件:** 現在の入力記述で開始／12件一覧・10 s保全情報・観測式・source 完全性契約を固定して開始。**推奨: 後者**。
- **達成範囲:** B-8 の長時間検証達成／固定入力に対する容量改善。**推奨: 容量改善に限定**。

## 総括

(v) は任意の厳密全順序で健全で、完全な全辺を検査すれば Tarjan と同じ `([], 0)` を返せる。  
非発火時の全 Tarjan、正例の入口 spy、integrity を迂回しない方針も妥当。  
実装前の必須修正は、source replay 完全性、非 wire 同一性、原因判別、計測契約の確定。  
A を維持し、各案を実測条件付きで採否する方針を支持する。  
指定資料の静的点検のみ実施。書込み・pytest・profile 実走は行っていない。