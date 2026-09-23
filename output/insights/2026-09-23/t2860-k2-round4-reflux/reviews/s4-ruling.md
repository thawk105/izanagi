# [T-2860] 段 4 裁定 (親、2026-09-23、critic-4 起動前 = 結果を見る前)

段 2・3 は省略 (軽量版: 設計択一が割れない・正しさ防壁に触れない・受理集合を変えない)。裁定 inbox は 2026-09-22-rulings-full31 まで再走査し K2 の新裁定なし。

- **P1 採用:** AO の取込み先は job dir の byte 写し `ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/`。
  写しは原本 (lock 済み submit-tree-r4) から作り、原本・`originals-copy-20260922/MANIFEST.sha256` と sha256 で照合してから使う。
  やらない理由の最も強い形: round 3 は原本 dir へ取り込んでおり、AO と原本の同居が崩れる。→ 退ける。層 3 レポートは WAL・lock・受領証の sha を束縛し、
  写しは原本と byte 一致なので材料の同一性は同じ強さで言える。原本への file 追加は「原本は動かさない」(依頼) と T-2853 の並行複製に反する。差は記録に明記する。
- **P2 採用:** 層 3 は wave 木のコード、`--output-root <ao-root>/output`、`--generated-from-head 8fd2a2f5c775954d6a32cee019ac7ce276298e4d`。
  `env/pegasus/calibration/*.json` (直下のみ) を原本 tree から byte 複製。round 3 は `--output-root <submit-tree>/output` で、較正の読取り範囲は同じ dir 直下。
- **P3 採用:** critic-4 入力は round 3 と同型の開示。critic は byte 写しを読む (原本と sha 一致の旨を開示)。pair 再投入 16269 の結果を開示するのは、
  round 3 が同 ID 別 tree の走を開示した型に従うため (4 巡目の生成入力には入れていない — D2194 項 2 / T-2795 段 4 P1 — ことは不変)。
- **P4 採用:** 3 AO とも variant `fceb937ae6c5`、refs = 本走 WAL 全 10 record、`--agent-prompt` 付き。critic 出力の 4 見出し契約不成立で取込みが拒否されたら、再抽選せず記録して止める。
  critic の結論内容 (帰属・推奨) で取込みを止めない。規律 6 の指示めいた文字列が出たら従わず insight に構造化して記録する。
- **P5 採用:** B-6 (d) は README の stale 注記に積む。2026-09-22 版は編集しない。
- **成果物影響 (DW-G05):** 放置すると層 3 材料レポートに 4 巡目の `mechanism_hypotheses` が無く、B-6 の材料が「同 job stock 対照は未達」のまま古くなる。
- **変異 matrix:** 実装面差分ゼロのため免除。受入全走は段 7 前に行う。
- **段 6:** read-only codex レビュー 1 本 (数値・sha・量化を一次資料と 1 対 1 照合) + 必要なら焦点再レビュー (上限 3 巡)。
