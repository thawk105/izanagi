---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2814-cleanup-command
seq: 2
---

## 再発

### F728

- **再発: 2026-09-21** — [T-2814] wave の Codex fix 子 2 巡目・3 巡目が `orchestrator/tests/test_check_docs.py` を `cat` / 広い `sed -n` で読み、5749・5772 行の非 NFC fixture が stdout JSONL に乗って `event_invalid` → `evidence_status=invalid` → 未受理 (作業自体は正しく終端 commit 済み、`codex_exit_code=0`)。親の prompt は「全文 cat しない、`sed -n` で読む」と書いたが行番号を名指ししていなかった。4 巡目 (監査子) の prompt に「5749・5772 行を含む出力禁止」を書いて再投入した。恒久対処 [T-2041] (択 (a) 採用、D1216) は見送り台帳のまま — 回避で通り研究実走の blocker ではないので再訪条件に該当しない (見送り追記のみ)。

## supersede 追記

- F1034 **supersede: 2026-09-21** — 恒久対応末尾の「`/cleanup-branches` §2・§3 への反映は [T-2814] で別 wave が行う」は実施済み: §2 に「未追跡 `output/` (`exploration/`・`env/`) は該当 wave の insight「証拠の所在」節で repo 外原本か確かめ、原本なら候補にせず残置・報告」、§3 に「§5 で引き渡す dirty 撤去 script も本節に従い、退避を撤去の前提にする (tar の `-C` を `-T` の前、`ls-files -o` の list 数を tar の非 dir entry 数が下回れば撤去しない)」、Codex overlay `.agents/skills/cleanup-branches/SKILL.md` にも同 2 項 (一次資料 `output/insights/2026-09-21/t2814-cleanup-command/README.md`)。
