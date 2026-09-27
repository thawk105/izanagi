# 段 6 レビュー裁定 (fix 1 巡目) — [T-1418]

対象: 統合 commit 6d2e14cdb (unit 木では 69084da7)。入力: out/s6-review-a.md (NO-GO)、out/s6-review-b.md (NO-GO)。

## 直す所見

- **F1 (A-1 / B-1、must-fix、real):** commit モードで runner 直後の HEAD・detached・bytes 再検査が、runner 結果に対する `_dispatch_orphan_stop(... result=result)` より前にある。dispatch が timeout / job 残存を返し、同時に再検査が失敗すると、hold を作らずに finally が H へ復元し、残存しうる job が読む木を変えてしまう。
  **直し方:** runner 結果を受けたら先に既存の `_dispatch_orphan_stop(... result=result)` を実行し (hold ならそのまま既存の保全経路へ)、hold でない場合にだけ runner 直後の再検査を行う。保全経路では既存どおり M の HEAD・bytes・clean を検査する。
  **test:** dispatch の結果が job 残存 (または timeout) を示し、かつ runner が touched bytes を変えた場合に、hold が作られ HEAD と作業木が H へ戻されないこと (復元されないこと) を確かめる。
  成果物影響: 残存 job が別の木を読み、変異結果の値が汚れる。
- **F2 (B-2、should、real):** runner 直後の再検査を直接検出する負例が無い。
  **test:** runner が detached のまま (a) HEAD を別 commit へ動かす、(b) touched file の bytes を変える、の各場合に、変異 record を記録する前に停止すること。file-swap モードの挙動は変えない。
  成果物影響: runner が M 以外を実行しても M の KILLED / SURVIVED として台帳に載りうる。
- **F3 (B-3、should、real):** 現行 T5 は runner 直後の再検査で先に拒否されるため、復元直前の detached 再確認 (M5) の単一理由の証拠にならない。
  **test の再照準:** runner が HEAD を attached (branch を M に向けて checkout) にした上で例外を出す (runner 直後の再検査に到達しない) 場合に、復元直前の detached 再確認が branch ref を動かさずに停止すること。既存 T5 の形は置き換えてよい (本 wave で足した test)。

## 直さない所見

- B-4 (policy 文言・復旧文言の重複、nit): 成果物影響なし。backlog (DW-G05)。
- B-5 (T9 の 8 組の縮約、nit): 裁定 T9 に沿っており成果物影響なし。
- B-6: 同意 (最小安全境界は維持)。
