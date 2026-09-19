# 既裁定の逐語 (この wave のユーザー依頼文と、拘束する既存裁定)

## 1. ユーザー依頼文 (2026-09-19、/dev-wave 引数、逐語)

受入全走の worker 時間を、受理集合・assertion・hold・成分粒度を変えずに削る。対象 =
orchestrator/tests/acceptance_duration_ledger.json の file 別上位のうち base 構築系 (test_s8b_oracle_driver.py の t080 e2e
= R4 [T-2786] / [T-2766] の所有) を除く 6 file: test_s8b_floor_campaign.py (528 node 2,368 秒)、test_s8b_ratified_verify.py
(945 秒)、test_p3_b4_producer_auth_experiment.py (50 node 832 秒)、test_t1259_qsub_env_delivery_probe.py (550
秒)、test_run_tests_preflight.py (544 秒)、test_codex_reasoning_ab.py (643 node 482 秒)。段 1 で各 file の setup / call を
`--durations` で分け、費用が fixture の複製・実 repo 走査・python subprocess
起動・同一入力の再構築のどれかを同定し、局所修正 (function → module/session scope 化、同一入力の 1 回構築と
deepcopy、subprocess を in-process 呼出しへ、実 repo 読取りは shared base 1 回) だけを Codex author (D95)
で入れる。検査の省略・stub 化・hold 変更・古い判定の再利用・parametrize 縮約は提示しない (D2068 の却下 3 案も)。効果は同
job の A/B (修正前後を同一計算ノード・同時刻で 3 対以上) で測り、変異 matrix で修正した test file の kill
集合が修正前と同一であることを示す。目標値は置かず、削れた秒数と残る律速を報告する。scope 外 = 新
gate・framework・並列度変更・launcher 改修。

## 2. D2068 (docs/decisions.md、2026-09-16) — t080 fixture の index 化高速案は現時点で採らない (要旨と却下 3 案の逐語)

**決定:** t080 e2e の base 構築を速くする 3 案 —
(A) 複製する git 可視 output を固定 whitelist へ限定する、
(B) 実 repo の object store 全体を alternates で借りる、
(C) 必要 blob だけを fixture 内へ移送して独立 index を組む —
を**いずれも採らない**。意味を変えない圧縮設定の変更も採らない。

(理由の要旨) (A) は受理集合を変える (非除外 output の可視 file に三軸 conjunction が入った場合の拒否経路を消す)。
(B) は観測を変え既存 assert が検出しない (alternates 経由で見える recorded commit が ancestry 判定を変えうる)。
(C) は効果の符号が未確認。login node の単発測定は根拠にならない (同一内容の複製が 28 倍振れた)。
受入高速化の判断に使う測定は、同一 tree 内で方式を交互に測った対比較に限る。

**却下した選択肢 (逐語):**
- 効果未確認のまま (C) を land する — 受入全走は共有資源であり、単発 A/B では目標の 25.5 秒を
  走間変動から分離できない。
- テストを削除・保留登録して速くする — D747 と、保留を既定の答えにしないというユーザー裁定に反する。
- 「成長比例を断った」と記録する — どの案も全件処理を残すので事実に反する。

## 3. D95 (要旨) — dev-wave の実装面 (orchestrator/ tools/ hooks/ 配下の非 Markdown、test を含む) は Codex `role=author` が書く。親は直接編集しない。

## 4. DW-O14 (docs/dev-wave/operations.md、逐語)

対象実装まで読み、resolver や `current_head` 等の正規注入 seam がないか確認する。
monkeypatch は最後の手段とする（D78）。
正例で許す差し替えは本数でなく位置で決める。検査対象の機構を構成する呼び出しは禁止、
その外側の既存定型 seam は許可、実物へ委譲する観測 wrapper は差し替えでない。
本数で列挙すると指定 fixture 内部の既存 patch と矛盾し、制約に合わせてコードを曲げる案を招く。

## 5. 記憶 (ユーザー裁定の要旨、2026-08-11〜23) — テスト時間の規律

- 開発を進めるほどテストが遅くなる構造を作らない。全体 5 分が絶対上限。直列化・長時間 job は禁止。
- 保留 (hold) は既定の答えにしない。「テストが間違っていればテストを直す。テストされているものが間違っていればそれを直す。リワードハック禁止」。
- 性能主張には同時刻の対照が要る。1 走の前後比較は無効。
- 新 test が実 root / 共有 ccbench を読むなら、読取りを shared base の構築 (key ごとに session に 1 回) に閉じ込め、各 test は copy を使う (T-2724 の実測: 長い reader の登録は real-repo gate を飢えさせる)。
