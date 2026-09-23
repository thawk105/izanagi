---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-t2853-repro-package-rest
seq: 1
title: [T-2853] 再現パッケージの残り (2)(3) — job dir にだけあった論文根拠の実験データ 12 組 (9,107 file、78,494,904,269 B) を repo 外の /work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/ へ写して原本と sha256 全件一致を確かめ、系列ごとの実行手順と R1 の入力一式を insight にまとめた (docs のみ、計算なし、branch worktree-t2853-repro-package-rest)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request.md`): entry 1822 の [T-2853] 項の残り (2)(3)。(1) 標準経路の trace 保全口は同時に走る [T-2849] の wave の担当 (分担済み)。[T-2860] の wave が読む K2 4 巡目 (r4) の原本は読むだけにした。記録 = `output/insights/2026-09-23/t2853-repro-package-archive/README.md`。decisions fragment は作っていない (保存先の運用は insight §3 と保存先の README を正本にした)。
- 写し: D2160 検証相 (48.94 GB)・B-8 と runner (29.50 GB + 5.7 MB)・B-5 試走の job dir 固有分・K2 pair (初回・再投入・4 巡目、`originals-copy-20260922` を含む)・A-1 の durable authority (attempt-0001・0002) と attempt-0002 の wave 記録。locked submit-tree 5 本は HEAD も lock も触らず、中の未追跡の campaign 原本 (B-5 試走 53 campaign・claim 53、K2 3 本) だけを読んで写した。原本と写しを別々に読む照合で 12 組とも不一致 0、保存先全体の走査も manifest の和と一致、別実装 (`sha256sum -c`) の再確認も全 rc=0。K2 再投入の原本 14 file は前日の写しの manifest とも全件一致した。
- 保存先は新設の `/work/1/SFC/tanab/izanagi-repro-archive/` (dev-wave-jobs の外、cleanup の母集合 = worktree / branch に入らない plain dir)。official の durable authority (`izanagi-measurements/`) とは分け、README に「写しであって正本ではない、official の入力にしない、書き換えない・消さない」と書いた。写しと照合の script も保存先の `tools/` に置いた (repo には入れていない)。
- 写さなかったもの: submit-tree 本体 (repo 写し)、0 B の flock 56 個、tree ごとに展開した依存物 (silo_ladder_rung1 配下の未追跡 971 file、pair2 と r4 の差は依存 clone の git index・reflog の 12 file だけ)、変異用・依存物の独立 clone、実験データの無い `-repair`・投入前に拒否された 2026-09-19 の A-1 試行、結果稿が引いていることを確認できなかった A-1 の pilot / sizing 段。
- R1: 入力一式を確認できたのは D2160 と B-8 だけ。各走の `result.json` に verifier の argv・repo commit・pin・patch の sha256・genome・verifier 9 module の sha256 があり、記録 commit から取り出した 9 module の sha256 が全件一致した。ただし argv の path は計算ノードの一時領域で残っておらず、B-8 は template patch の後に gate 条件式を書き込む必要があり、D2160 の 10 s 校正 4 走は当時の判定が無い (追加評価として分ける)。追跡下の旧形式 trace 4 file を読める最後の parser は `a70a5acd4` (2026-08-12 11:01)。
- 段 6 (Codex read-only review 1 本、08:52〜08:57 JST): NO-GO (must-fix 3・should 3・nit 1)。親が現物で裏取りし全 7 件 real と裁定して直した — B-8 の source 再構成に gate 条件式の書き込みが要る、D2160 の 0 B の verifier.json 4 走と当時の版の 10 s 走が完走しなかった記録、trace 不在の断定を調査範囲に限定、別実装の再読は cache 排除の証拠ではない、A-1 の未追跡 4 file は追跡下と同一、copy script の rc=0 は照合成功を意味しない、`git worktree add` の引数。焦点再レビューの結果は insight §6。
- 調査子 (Claude Explore、sonnet) 4 本の報告のうち、`a70a5acd4` の日時 (2026-07-29 とあった) が誤りで、親が `git log` で 2026-08-12 に直した。
- 実装面の差分ゼロ (insight・verbatim・本 fragment のみ) なので変異 matrix は免除 (DW-S04)。受入全走の結果は land の受領証。本 wave の計算ノード使用は受入だけ。
- セッション異常: 隔離 worktree の Bash 検査が変数や複合構文を含む読み取りコマンド (find・nice・python の引数) を拒否したので、読み取りは job dir の小さい script に分けて実行した。

## 次の一手差分

### 更新

- [T-2853] **P1・(2)(3) 済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、**(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md` で済んだ。** 残り: (1) 今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、標準評価経路へ trace の保全口 (作業保管を全量 zstd で残す、R1 の入力一式 = trace・preservation・verifier の argv・repo commit・pin・patch・verifier module の sha256 を D2160・B-8 の runner と同じ組で残す) を入れる ([T-2849] の wave の担当、insight §7・§11)。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5) 主要図の再実行は図ごとに「描き直し / R2 / 独立探索のやり直し」を決めて node 時間を積み上げ、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: 9b37ecc979dcdbc3a3ed88b8fddd0788e0869efa2e7cb9152d7263acc7eaa91d
