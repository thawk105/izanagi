# 段 1 brief — [T-2853] R2 fig8b (fig8 を含む) の測り直し

- 研究前進: 再現パッケージの R2 のうち fig8b 単位 (output/insights/2026-09-27/t2853-repro-rest/README.md §3.3) を実測で埋める。
  論文図 fig8b (B-10 静的右 tail、cohort 1 主結果 + cohort 2 独立再現) の測定設計を、固定 genome・LLM なしで Pegasus 計算ノードで 1 回測り直し、
  同じ生成器で描いて原 cohort の値と別 attempt として並べる。完了判定 = 2 group × 3 job が completion.json まで到達 (または失敗を分類して記録)、
  group ごとの集団報告、R2 図、原値との対照表を insight に記録し local main へ取り込む。
- scope: 投入・待機・集団報告・描画・記録だけ。repo のコード変更なし。gate・検査・台帳・一般化の追加はしない (依頼)。
- 確定済みユーザー裁定: D2212 項 4 (1 タスク合計 2 node 時間以上で確認)、repro-rest §3.3 で fig8b = 1.40 node 時間 ((a) Elapse) は確認不要と確定、
  依頼: 元の cohort と合成せず別 attempt として並記 (プールしない)、正しさ検査は元と同じく job 内、trace 保全 opt-in (D2233) は使えるなら有効、
  driver 変更が要る/実測単価で 2 node 時間超なら段 4 で見積りを示して停止。D2050 (2 本目以後の cohort は地位を結果前に明記)。
- 不変条件: 規律 1 (検証 = trace 有効 build、計測 = trace 無効 build の別走 — job body の既存経路のまま)、規律 2 (anomaly は即 reject、検査を緩めない)、
  規律 7 (旧 cohort の記録・判定を上書きしない、R2 は新しい有限履歴の判定)。原 cohort の成果物 (/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/) は読むだけ。
- (P1) 親の provisional 裁定・攻撃対象: 「元の driver」は `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal`。
  依頼が名指しした `submit_b10_backoff_shape.sh` は fig13 (待ち方 grid) の driver で、fig8/fig8b の元 group 名 `b10-backoff-grid-*` と手順書
  docs/b10-backoff-static-tail-submission.md §2 がこれを示す。依頼の意図 (元の driver) に合わせ誤記として扱う。
- (P2) 投入 checkout は cohort 2 の source commit `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` (reservation.json の repository_commit、CCBench gitlink 511c9538、
  事前登録 commit も 8737cacb4) の detached submit-tree を group ごとに 1 本 (計 2 本、repo 外 /work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/ 下)。
  理由: 現行 main は pin.CURRENT_PIN = 6810666 で、511c953..6810666 の CCBench 差分は cc/mocc/transaction.cc だけ (silo source は同一) だが、
  記録上の repo_stock_pin が変わり生成器 plot_b10_static_tail_formal.py の固定検査 (`repo_stock_pin == "511c953"`) で描けない。
  cohort 1 の 0600887d9 は T-548 前 (third-party 供給経路が違う) で、今日の計算ノードで起動するかが未実測。8737cacb4 以後の job body 変更は凍結 tree pin の更新だけ。
  代替: (A') group 1 を 0600887d9 + prereg cad6f46d8、group 2 を 8737cacb4 で各 cohort を忠実に再現 / (B) 現行 main (生成器が描けない)。
- (P3) trace 保全 opt-in は有効にしない: submit_b10_backoff_grid.sh の qsub -v は固定列挙で IZANAGI_TRACE_ARCHIVE_ROOT を渡さず、8737cacb4 は D2233 以前。
  有効化には driver 変更が要る → 依頼の条件「使えるなら」を満たさないので使わず、理由を記録する (phase3.md も「job body での opt-in の有効化は残り」)。
- (P4) 描画: 生成器の bytes は変えない。repo 外の使い捨て wrapper (Codex author が書く) が生成器を import し、cohort の定数 (group id・入力 sha256・日付・report dir)
  と図中の役割表示だけを R2 用に差し替えて v2 (2 block) を描く。wrapper の陽性対照 = 原 metadata のまま描いた図が既存 fig8b と同じ値 (artist series 一致)。
  結果前の登録: R2 の verdict が not-observed-in-any-workload 以外等で生成器が拒否したら、図は描かず表だけ記録する (検査を緩めて描かない)。
- (P5) 地位の明記: 投入前に insight §0 に「R2 attempt は fig8b の cohort 1/2 のどちらの置換でも第 3 cohort でもなく、事前登録の verdict に合成しない別 attempt。
  原 cohort の稿・図は不変、R2 の値は並記だけ」を書いて commit し、その後に投入する (D2050 の原則)。
- 成果物: output/insights/2026-09-28/t2853-r2-fig8b/README.md (+ verbatim/)、spool fragment (worklog / phase3 の T-2853 行)、R2 図と group report は repo 外
  /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/ (出力親、祖先に .git なし実測済み)。
- 分割: 投入は 2 group を同時に (6 job = 6 node 同時)。wrapper (描画 + 原値対照表) は job 待ちの間に Codex author 1 本。段 6 は一次資料から値を書き起こすので read-only review 1 本。
- 受入・実測環境: 計測 = Pegasus gen_S (job body の既存 on-node 競合 probe が単独性を見る)。login 側は投入前に qstat・pegasusinfo を確認。repo コード変更なしなので受入全走は不要 (見込み)。
- 見積り: 6 job × 約 840 s = 1.40 node 時間 ((a) Elapse)。walltime 上限は job 当たり 5 h だが消費見込みではない。
