# 探索の独立反復の試走 — 発効束・smoke の実測・投入 ([T-2850] 残り (1)、2026-09-23)

- 位置づけ: 実装記録と実測。規則の正本は事前登録 v1 `docs/search-repetition-trial-preregistration.md` (D2231) と追補 1 `docs/search-repetition-trial-preregistration-addendum-1.md`、
  発効の判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: `worktree-t2850-trial-run` (起点 local main `65fd1422f`、開始 gate fresh rc 0)。repo の実装差分はゼロ。投入の繋ぎ (glue) は repo 外で Codex author が書いた。
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-run/` (brief・段 3/4/6 の資料・glue・submit-tree・台帳・materials・evidence・見積り)。

## 1. 発効束

`bundle/t2850-trial-effect-bundle.json` が事前登録 §10 の実値である。data file は同じ dir にある: 親の指示文 (`t2850-llm-parent-template.md`) と起動時の header / resume、
試走の 18 job の spec と投入順 (`trial-schedule-wh.json`)、固定 commit の実装・検査器・役割定義 29 file の SHA-256 (`files-sha256-at-7ea9aa09d.txt`)、glue の SHA-256、
2 課題の見積り (`cost-estimate-v1-two-workloads.json`、ユーザーが縮小を選ぶ前の値)。

## 2. smoke の実測 (試走の標本ではない。cohort `t2850-smoke-v1`・`t2850-smoke-v2`、系列番号 9)

| 回 | job | 結果 | job Elapse |
|---|---|---|---:|
| 1 | LLM・wh (21114)、block job・rh (21115) | job body が 10 s で拒否: `CCBench P3 S4 campaign pin mismatch` (submit-tree の CCBench が gitlink `e9e477ca` のままで、loop の campaign pin `511c9538` と違った) | 10 s + 10 s |
| 2 | LLM・wh・B 1・A 1・N_eval 1 (21150) | 完走 (driver_rc 0)。唯一の原提案で planner が `axis: single-parameter-magnitude` を返し、巡 tool の検査で reject (規則どおり A を消費)。**親は背景の待ち手を起動して応答を終え、`claude -p` がそこで終了した** | 2,057 s |
| 2 | block job・rh・stock 1・参照 1 (21151) | walltime 44 分で打ち切り。rh の stock 1 session は 741 s (verify 5 本 135〜139 s)、参照点 `p2_2_flag_opt` は 1,873 s を超えても終わらなかった | 2,649 s |
| 3 | LLM・wh・B 2・A 3・N_eval 1 (21345)、再開型の親起動器 | 完走 (`b-complete`)。原提案 2 回とも certified (提案値 2 µs・20 µs)、critic 1 回、役割呼び出し 5 回がすべて `claude-opus-5` に解決。1 機会の親の待ち 315 s・886 s (後者は critic を含む) | 4,032 s |

- write-heavy の 1 session: stock 244〜258 s (verify 210 s)、候補 491〜519 s (verify 465〜472 s)、bench は 16 s、job の準備は 27〜30 s。
- 1 回目の拒否を受けて、glue に submit-tree の準備 (CCBench を campaign pin に detached、`fetch_third_party.py hydrate` の `source_root` を渡す) を足した。
- 2 回目の親の終了を受けて、親の運用を「起動器が request の公開ごとに同じ session を `--session-id` / `--resume` で起こし、親は 1 機会分だけ処理して応答を終える」に変えた。
  並走の B-5 本走 wave も同じ事象を実測し、前景の `sleep` も Bash の防壁が拒否することを共有してくれた。
- smoke の計算は計約 2.44 node 時間 (glue の自走テスト 3 回 各 8 s を含む)。

## 3. 見積りとユーザーの計算確認

- 2 課題 (事前登録どおり) の見積り: 110.9〜252.2 node 時間 (中心 182.9)。事前登録 §9.1 の試算 128.7〜145.4 との差は主に read-heavy の検証費で、候補の 1 session は 741 s (stock と同じと置いた下側) から
  約 2,210 s (固定 5 µs の既存記録 433 s/本 × 5 からの換算) の幅に入る。計算は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-run/estimate/estimate_v1.py`。
- ユーザーは最初の問いに「こんなに必要なの？…200時間って何よ？絶対におかしい」と返した。親は投入せず、費用の 9 割以上が評価ごとの正しさの検証 (3 秒の trace 5 本の直列性検査) で、
  bench は全体で約 2.7 node 時間しかないこと、評価の回数 (系列ごとに stock 1・初期点 2・探索 10・測り直し 5) を示した。ユーザーは「write-heavy だけで試走」を選んだ。
- write-heavy だけの試走: 42.4〜60.6 node 時間 (中心 47.6)、LLM の直列時間 1.9〜19.5 時間 (中心 6.5)。

## 4. 段 3・段 6 の所見と裁定

- 段 3 (Codex read-only 相談 2 本): どちらも NO-GO、must-fix 計 5 (重複を除き 4) をすべて real と判定。smoke を試走と別の系列番号にする (seed preimage に cohort が入らない)、
  §10 の実値を確認前に揃える、smoke で測れる範囲の具体化、18 job で 1 つの cohort root を共有する (endpoint の失格の波及)。裁定は job dir の `s4-ruling.md`。
- 段 6 (Codex read-only レビュー 2 本): 正しさレンズ NO-GO (must-fix 2: 親の起動前に request の期限を確かめる、費用記録 `--costs` を必須にする)、過剰・削除レンズ GO (hydrate 直後の重複 verify を削る)。
  fix は 3 巡 (準備 script・hydrate の source_root・qstat の消滅判定 / 再開型の親起動器 / write-heavy だけの spec)。投入順はレビューと親がそれぞれ独立に再計算して一致した。
