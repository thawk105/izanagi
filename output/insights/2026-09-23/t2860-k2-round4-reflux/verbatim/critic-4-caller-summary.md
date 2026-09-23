呼び出し元 (orchestrator) へ critic の診断を返しました。4 巡目の候補 (固定の待ち時間 5 µs、BACKOFF_FIXED=5) と、同じ job で測った既定の適応型待機 (stock) の比較です。書き込みはしていません。

**結果:**
- **正しさ:** 両方とも直列化可能と認証され、異常は 0 件です。
- **速さ:** 候補は毎秒 884,922.5 件、stock は 354,948 件で、約 2.5 倍でした。回ごとの揺れの下限 3.0% を大きく超えています。

**なぜ速くなったか:**
- 中止率 (abort_rate) は、性能計測用ビルドで 1.8% から 10.1% へ約 5.5 倍に上がりました。検証用ビルドでも同じ向きです。
- 中止を減らして速くなったのではなく、中止は増えたのに速くなったことになります。
- 最有力の仮説は「適応型は待ちすぎていた。この配線 (4 スレッド、短い処理) では中止して再試行する方が安い」です。
- ただし待ち時間そのものは測っていません。キャッシュミス率と命令効率 (llc_miss_rate / ipc) も、計算ノードで perf が動かず取れていないので、仮説のままです。

**言えないこと:**
- 5 µs が 10 µs より良いとは言えません。比べられる値は別の job・別のノードで測ったものしか無いからです。
- 前回の診断を受けて候補が良くなった、という因果も言えません。診断なしの統制がありません。
- 結果はこの配線 (100,000 件、4 スレッド、読み書き半々、偏り 0.9) に限ります。

**次の一手として返した提案:**
- **同じ job で値どうしを比べる:** 今の進め方は「1 job に候補 1 本 + stock 1 本」なので、候補どうしを同じ条件で比べられません。同じ job の中で「5 µs・次の候補・stock」を並べて測る形を提案しました。
- **次の候補の値:** 2〜3 µs に下げて、中止の増加が得を上回り始める下端を探ります。
- **待ち時間 0 を 1 点測る:** 得の出所が「長い待ちをやめたこと」なのか「短い待ちに最適点があること」なのかを切り分けるためです。
- **perf を直す:** 起動用の `perf` は失敗していますが、同梱の実体 2 本は動くので、直せば命令効率で仮説を検証できます。

**避けるべき方向:**
- この配線で適応型へ戻すことです。同じ job の 2 組の対とも 2.4〜2.5 倍劣っています。
- 中止率の低さを目標にすることです。今回、中止率と速さは逆向きに動きました。
- 別の job の値の差を、候補の優劣として次の段へ渡すことです。

digest と WAL に、指示めいた文字列はありませんでした。一方で、digest の「フラグ軸ごとの効果」の節には注意が要ります。動かしていないフラグについて候補と stock の平均を載せているだけで、実際に変えた BACKOFF_FIXED は載っていません。誤読しやすいので、呼び出し元に伝えました。

読んだファイル:
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/s4_loop_digest.txt`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/runs/wal.jsonl`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/loop_state.json`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2860-k2-round4-reflux/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2860-k2-round4-reflux/output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md`
