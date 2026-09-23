# [T-2860] 段 1 brief (親、2026-09-23)

- **研究前進:** 論文ストーリー B-6 の材料「K2 手動 loop」を 3 巡から 4 巡へ伸ばし、B-6 (d)「同 job stock 対照は未達」を、4 巡目の同 job stock 対照 (certified・source STOCK) と critic-4 の還流つきの一次資料で更新する。完了判定 = critic-4 逐語・AO 3 event・層 3 材料レポート・4 巡 results 稿・README の stale 注記が repo に着地。
- **scope:** (1) critic-4 を登録 role `critic` で 1 回 (再抽選なし)。入力は round 3 の `build_critic_input_3.py` と同型 (parent_disclosures + digest_path + evaluated_variant)。(2) planner-5 / coder-5 / critic-4 の AO を `p3_s4_loop.py --record-agent-output` で login から取り込む。(3) `layer3_report` で材料レポート。(4) insight。(5) `docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md` (新 file、3 巡稿は不変)。(6) `docs/paper-story/README.md` の results 表へ 1 行と stale 注記 (B-6 (d))。
- **scope 外:** 計算ノード投入、実装面の変更、新しい gate・検査・台帳・一般化、fig12b ([T-2808])、手順書 §7 ([T-2861])、2026-09-22 版の本文編集 (凍結物)、K2 を必須経路へ戻す記述、B-6 全体の充足判定。
- **確定裁定:** D2211 項 1 (K2 は論文の必須経路へ戻さない)、D2194 項 2 (4 巡目入力 = 択 A)、D2172 項 3、D2205、D2187。
- **不変条件:** 原本 `dev-wave-t2795-k2-pair-resubmit/submit-tree-r4` (lock 済み、HEAD `8fd2a2f5c`) は読むだけ (HEAD を進めない・削除しない・file を足さない)。規律 2・3・6・7。3 巡稿・fig12・2026-09-22 版の bytes は変えない。
- **(P1) 親の provisional 裁定・攻撃対象:** AO の取込み先は原本 campaign dir ではなく、job dir に作る byte 写し (`ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/`、原本・MANIFEST と sha256 照合) とする。理由: 取込みは `runs/agent_outputs.jsonl` を新設し、T-2853 が同じ原本を並行に写すので「原本は動かさない」を字義どおり守る。round 3 は原本 dir へ取り込んだ (差分を記録に明記する)。
- **(P2)** 層 3 は wave 木のコード (main `3886a1fd3`) で `--output-root <写し>/output`、`--generated-from-head 8fd2a2f5c…`。写しの `env/pegasus/calibration/*.json` は原本 tree の同 dir 直下 *.json の byte 複製 (走査は直下 *.json のみ)。
- **(P3)** critic-4 の入力開示は round 3 と同型: 本走 (job 16312、候補 5 と同 job stock) の実測、同じ campaign ID の別走 (pair 初投入 13339・pair 再投入 16269) と round 1〜3 (別 ID 409e13f8) の存在・値・記録 path、非同時刻であり優劣の根拠にしない旨、critic が読むのは byte 写し (原本と sha 一致) である旨。
- **(P4)** AO 3 event とも variant = 候補 `fceb937ae6c5`、`--agent-wal-ref` = 本走 WAL 全 10 record の canonical ref、`--agent-prompt` 付き (round 3 と同型)。critic 出力が 4 見出し契約を満たさず取込みが拒否されたら、再抽選せず記録して止める。
- **(P5)** B-6 (d) の更新は README の「最新スナップショット以後に確定したこと」へ積む (版は凍結物、D1858: 積むことは新版を要求しない)。
- **成果物の形:** insight `output/insights/2026-09-23/t2860-k2-round4-reflux/` (README、verbatim/critic-4.md、materials/critic-input-4.json・critic-prompt-4.md・wal-refs-r4.json、layer3_report.json、reviews/)。WAL・lock・digest・AO jsonl は repo へ複製しない。
- **段構成:** 軽量版。段 2・3 省略 (設計択一なし・正しさ防壁に触れない・受理集合不変)。一次資料から事実を再抽出する docs wave なので段 6 の read-only レビュー 1 本は残す。実装面差分ゼロ → 変異 matrix 免除、受入全走は行う。
- **受入・実測環境:** 計算ノード投入なし。login で取込み・層 3。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
- **分割:** 親が直列 (critic 1 本の後に取込み)。並列子なし。
