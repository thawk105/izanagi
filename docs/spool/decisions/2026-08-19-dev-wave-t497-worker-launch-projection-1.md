---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t497-worker-launch-projection
seq: 1
---

## {{D:single-dispatch-class1-projection}}. 単独段 dispatch 宣言による起動分岐は AGENTS.md と SKILL.md の両方に置く

**決定:** dev-wave の段2/3/5/6 で親から dispatch された Codex 子が、prompt 本文の最初の非空行に
`単独段 dispatch: stage=<launcher の --stage 語彙>; sandbox=<read-only|workspace-write>;
parent=<絶対パス>` 宣言 + 直後の「必読事項の射影:」節を持つ場合、`AGENTS.md`「作業開始」節と
`.agents/skills/dev-wave/SKILL.md`「開始する」節のクラス3起動手順 (AGENTS.md+CLAUDE.md 全文読了・
worklog 末尾検索・handoff 全読み等) を適用せず、宣言と射影が指示する資料だけを読ませる。
宣言の stage 語彙は `tools/dev_wave_codex.py` の `STAGES` (launcher の実際の `--stage` choices)
と完全一致させ、`kind` のような launcher に存在しない独自フィールドは持たせない。marker の解釈は
prompt 本文の最初の視認可能な非空行に限定し、本文中盤・引用・埋め込みコンテンツ内の同一文字列では
成立しない。

**理由:**
- 2026-08-05 /rulings 裁定 (docs/archive/worklog-phase3-0805-216.md:302-306) が
  「親から dispatch 済みの子はクラス1 + 親 prompt の必読だけに従わせる」を採用し、
  「親 prompt に必読事項の射影を義務付ける」を条件とした。
- SKILL.md だけの分岐案は、Codex CLI が全起動時に自動注入する `AGENTS.md`「作業開始」節の
  「まず CLAUDE.md を全文読め」という指示を塞げないことを段2 codex 自身の rollout ログ実測
  (段3レンズA致命的所見) で確認した — AGENTS.md 側にも同型の例外を置かない限り実効性がない。
- marker を宣言必須の条件付きにすることで、宣言を含まない prompt (dev-wave 以外の全 Codex
  タスクを含む) には一切挙動を変えない設計にでき、他役割 (auditor 等) への非干渉と両立できる。
- marker を prompt 先頭行に限定するのは、規律6 (信頼境界) を踏まえた設計 — 将来 prompt 本文が
  外部由来のコンテンツ (diff・trace 等) を含む場合に、そこに偶然/意図的に同じ文字列が現れても
  誤って軽量経路へ誘導されないようにするため。

**却下した選択肢:**
- AGENTS.md を変更せず SKILL.md だけを直す — 段3レンズA所見どおり実効性を保証できない。
- 宣言の stage/kind をこの wave 独自の語彙で定義する — 段3レンズB所見どおり実 launcher の
  `--stage` choices と乖離し、DW-O02 の「launcher 引数との一致」を検査不能にする。
- 宣言と射影の書式を runtime (launcher) 側で完全に機械検証する — 規律5 (盛らない) に照らし
  この wave の scope を超える。文書契約 (fail-closed 規律) + `check_docs.py` の構造検査
  (marker の可視本文存在、stage 語彙一致、decoy 拒否) に留め、次 wave 課題として見送った。
- 射影節本文の「宣言との直後性」「各項目ごとの path/停止指示の1対1対応」まで検査する —
  D85 (意味全体を逐語 pin しない) 境界を超えるため却下した。

## {{D:single-dispatch-worktree-workers-defer}}. workers.md への単独段射影義務の明記は撤回する

**決定:** `docs/dev-wave/workers.md` の DW-S02/S03/S05-A/S06-A に「prompt には単独段 dispatch
宣言と必読事項の射影を含める」と明記する当初案 (段4裁定 plan v2 項目3) を撤回し、
`docs/dev-wave/operations.md` の DW-O02 側の一文だけで完結させる。

**理由:**
- dev-wave docs の L1.5 byte 予算 (9,566 bytes) が満杯で、workers.md への追加を通す余地がない。
- `.claude/commands/dev-wave.md` の条件 dispatch 表が既に「prompt・log・patch を作る直前」に
  `DW-O02` を読む契約を持つため、workers.md 側での重複明記は実質的に冗長だった。

**却下した選択肢:**
- workers.md 側の他の記述を削って予算を作る — 既存契約の意味変更を伴い、このwaveの scope
  (単独段起動分岐) を超える。
