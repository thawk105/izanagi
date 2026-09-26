# 段 1 brief — [T-2838] 択 A (2026-09-26 14:13 JST)

- 研究前進: 土台 (開発基盤)。受入門番の偽 leader による閉門 (9/19 以降の leaders 起因閉門 2049.3 分のうち記録上の走行 ≤ 1 が 1003.0 分、一次資料 §3.4) を数え方の統一で消し、択 B 再提示の材料 (同じ probe の取り直し) を揃える。完了判定 = 雛形 1 本の設置・記憶の指し先更新・採用前一致実測 1 回・採用後の取り直し 1 回が記録に載ること。
- 確定済みユーザー裁定: D2211 項 4 (択 A だけ採る、写し元は repo 外 1 本・記憶が指す、閾値の変更でなく記憶正本の徹底、採用前に argv 一致を 1 回実測)、D2219 項 5 (A の後に同じ probe で閉門内訳を取り直し、長い待ちが残れば B を改めて提示。今は B を採らない)、択 C・D・別枠は採らない。
- scope: (1) `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` を置く。(2) 記憶 `acceptance-gate-no-workers-threshold` と索引行が雛形を指す。(3) 採用前の一致実測。(4) 採用後の probe 取り直し。(5) insight + worklog fragment に記録。
- scope 外: 閾値 (maxl=1, maxload=60, maxpigz=2)・周期 (100〜140 秒)・2 連続 + 0〜45 秒再カウント・lease TTL・待ち手・lease primitive の変更、repo への script/台帳/gate/検査の追加、他 wave の job dir の既存 script の書き換え、択 B の実施。
- 不変条件: 雛形の leader 行は裁定の正規表現を逐語で使う。条件値の行 (`maxl=1; maxload=60; maxpigz=2`) と leader 行の形は probe (`gate_wait_probe.py` の conditions()) が読む形を保つ。
- (P1) 親の provisional 裁定・攻撃対象: 雛形は親が既存の門番 script (dev-wave-t2273-shard0-local-copy/run-acceptance-gated.sh、9/26 13:07、既に裁定の正規表現と同じ leader 行・同じ条件値) を写し、JOBDIR/WT/SLUG の 3 値を placeholder にし、先頭コメントを写し方の説明に替えるだけにする。論理を変えないので、job dir の launcher は親が書く運用 (DW-C01・DW-O01) の範囲とみなし Codex 実装子を立てない。
- (P2) 採用前一致の実測方法: 正規表現とは独立に `/proc/<pid>/cmdline` を引数単位で読み「argv[0] が python*、ある引数の basename が dev_wave_wait.py、次の引数が acceptance」を真の leader とし、同時刻の `ps -eo args` に対する正規表現の一致と突き合わせる。見逃し 0・誤検出 0 を採用条件にする。静的補強: job dir 直下 sh の受入起動形の全数集計 (9/19 以降、正規表現が拾わない形 0 件。例外は 8/21 の python3.10 形 2 本)。
- (P3) 採用後の取り直し: 同じ probe (verbatim/gate_wait_probe.py.md の逐語) を `--since 2026-09-21` かつ本 wave の受入後で締めて走らせ、§3.3/§3.4 と同じ表 (閉門理由、leaders 起因 × 走行数 × 数え方) を取る。雛形経由の門番 log は本 wave 自身の 1 本程度で、採用効果の判定には足りないことを明記し、B 再提示の材料として「次に取り直す時の argv」を記録する。
- 受入・実測環境: 受入は Pegasus 計算ノード (worklog の所在どおり)、門番は本 wave が雛形を写して使う (親の実データ dogfood)。probe は login read-only。
- 成果物: `output/insights/2026-09-26/t2838-gate-argv-unify/README.md` (+ verbatim)、worklog fragment、記憶更新 (repo 外)。decisions は新設判断なし (既裁定の実施)。
- 並列分割: なし (子は段 6 の read-only レビュー 1 本だけ。一次資料から数値を再抽出する docs-only のため)。
- 既存被覆: 記憶 2026-09-20 追補 (argv 先頭一致) と一次資料 §7 が対象。純増は「写し元 1 本の設置」と「実測 2 回」だけ。
