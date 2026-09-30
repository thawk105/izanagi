単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (正本、「plan v2」の単位 A と変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s4-ruling.md
- 段 2 plan (行番号つきの変更箇所表。「単位 A」節): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s2-plan.md
- 外部 script の原本: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/next_tasks_consult.sh.orig

作業する worktree (cwd、書込みはここだけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/astra-ultra-unit-a (base 3cb51f201)。

# 役割と所有

あなたは dev-wave 段 5 の実装子 (Codex role=author、単位 A) である。**sub-agent を spawn しない (collaboration tool を使わない)。**
編集してよい path はこれだけ: tools/check_docs.py、orchestrator/tests/test_check_docs.py、orchestrator/tests/test_dev_wave_launch_authority.py、
tools/dev_waves/effort_levels.py、orchestrator/tests/test_effort_levels.py、orchestrator/tests/test_dev_wave_codex.py、
tmp-next-tasks/next_tasks_consult.sh (新規の一時 file。起動器が子 branch に終端 commit するが、wave へは展開せず親が repo 外へ設置する)。
docs は編集しない。自分では commit しない。

# やること

s4-ruling.md「plan v2」単位 A の 1〜5 をそのとおり実装する。要点:
1. DW-O01 model literal を `gpt-6-astra` へ (docs は既に astra、commit 241f0c960)。D2229 決定 2 の pin (drift 負例の置換元、literal 期待値、
   全段導出 model、docs 独立照合) を全部追随。
2. effort pin 5 節 (DW-S02/S03/S05-A/S06-A/S06-C) を `ultra` へ。check_docs 本体・finding 表示値・独立 literal・負例の置換元・decoy の「正しい値」役を
   s2-plan の表どおり。旧 medium を拒否する負例を 5 節分 (小さい parametrize)。合成 fixture の意図的な medium/high/low、V1/V2 過去形式 fixture、
   `REASONING_XHIGH_*` の名前は変えない。**親はまだ docs/dev-wave/workers.md を ultra にしていない** (段 5 後に親が変える)。
3. `CODEX_REASONING_EFFORTS` に "ultra" を追加し docstring を改訂 (裁定の文言)。`CLAUDE_EFFORTS` は不変。test_effort_levels は Claude の厳密 tuple を維持。
4. test_dev_wave_codex の plan/consult 転送 matrix に ultra の正例を最小追加 (既存の値は残す)。
5. `DEV_WAVE_L1_5_BYTES_MAX` を 9_696 → 9_788 にし、test_check_docs の pin (2777・3504・4017 行付近) を意味を確かめて追随 (3504 行の三項式は
   L1 と L1.5 のどちらの値かを読んでから)。
6. tmp-next-tasks/next_tasks_consult.sh に原本を基にした改訂全文: `CONSULT_EFFORT` 既定 high→ultra (コメント更新)、codex 分岐に `-m gpt-6-astra`、
   GUARD 節に「sub-agent を spawn しない (collaboration tool を使わない)」1 行。締切 1800 秒は維持。`bash -n` で構文検査。

# 期待赤 (親 docs 未 land による)

この木の docs/dev-wave/workers.md はまだ medium なので、あなたの変更後、実 repo を読む check_docs 系テストは「effort pin の不一致 (DW-S02/S03/S05-A/S06-A/S06-C
の 5 件)」と、L1.5 footprint が 9_788 と一致しない (workers.md の 5 bytes 分、footprint 9793 > 9788) finding を出すのが期待赤。これ以外の赤は回帰として報告する。

# 検査と報告 (必須)

- 緑には実走 nodeid・範囲を併記。実走不能なら「実装済み・未実走」と書き、`closed` と書かない。
- テスト新設・改名は親の名指しを網羅と見なさず、制約 meta-test (test file 列挙・所要台帳・hold 契約など) を自ら洗い出し走らせる。
  `orchestrator/tests/test_check_docs.py` は growth hold で自走不可の場合がある。そのときは pin の byte 一致を直接照合して報告。
- fixture へ現行 hash を差し込む等、テストを甘くして緑にしない。機構の正例・負例は実体を名指しし依存先を stub しない。
- 期待値へ揮発 payload を焼き込まない。
- 報告に、所有外 caller・共有 fixture・consumer test への波及を静的列挙。
- 指示外の受理集合変更をしない。変更前の受理・拒否挙動を明記。
- 既存テストの期待値を「付け替え」以外の目的で緩めない (反転・skip・削除禁止)。

# 出力形式

markdown。「## 変更 file と要旨」「## 実走したテスト (nodeid・結果)」「## 期待赤と回帰」「## 波及の静的列挙」「## 変異事前登録 m1〜m3・m7 の位置確認」「## 総括」。
