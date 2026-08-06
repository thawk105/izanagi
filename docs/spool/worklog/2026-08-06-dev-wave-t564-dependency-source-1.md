---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t564-dependency-source
seq: 1
title: [T-564] 依存 source の所在を home の外へ移し、certify job の復旧を実測した — 新しい較正 1 本を取得したが活性化は名乗らない (コード + 成果物 + docs、受入 6774 passed / 20 skipped、変異 5/5 KILLED、job 892707.nqsv、branch worktree-dev-wave-t564-dependency-source)
---

## 本文

- **ユーザーは択一 (b) を採る前提で source を先に用意していた。** 親は
  `/work/SFC/tanab/github/{gflags,glog}` が pin 済み HEAD と一致し porcelain が空であることを
  実測してから着手した。
- **ユーザーは対話中に「凍結証拠が変わっても実害はない」と述べた。** 親はこれを
  *この点を blocking 裁定として上げない*根拠としてのみ扱い、検知力を落とす根拠には使わなかった。
  実際、過去 campaign の記録ファイルは 1 byte も変えていない。動かしたのは検査の根拠だけである
  ({{D:dependency-source-out-of-home}})。
- **段 3 の敵対 2 レンズが独立に NO-GO を返し、所見 10 件はすべて real だった。** refuted は 0 件。
  最も効いたのは「テストが緑でも job が動かなければ何も達成していない」というレンズ B の指摘で、
  親 brief にあった実ジョブ受理手順の欠落を land 前に埋められた。
- **段 6 のレビュー 2 本も NO-GO で、must-fix 8 件のうち 5 件が親自身の裁定と docs の誤りだった。**
  - 最重要は**親の段 4 設計そのものの穴**である。検査を「evidence 側 = 歴史値」「t126 側 = 現行値」へ
    分担させたため、変更前にはあった**各テスト単独での検知力**が失われていた。単独 nodeid 実行では
    一方向の drift を受理してしまう。共有 golden module に定数の正本を 1 箇所置き、
    両テストがそれぞれ単独で 3 条件を検査する形へ直した。**検出力は「増加」ではなく「保存」**である。
  - 親は変異 M1・M4 を「単一理由」と登録していたが、fix 後は 2 node が独立に拒否する形が正しいので
    **この記載を撤回**した。冗長ではなく、fix の目的そのものである。
  - 親は probe の射程を「専有 1 ノード」「非 symlink」と書いていたが、`-b 1` は 1 node allocation で
    あって専有証拠ではなく、非 symlink も末端 directory だけの性質だった。**採用した表記は
    `/work/SFC → /work/1/SFC` という祖先 alias に依存する**と限定を明記し直した。
  - 親は「`calibrate_rc=0` = certify job 完走」と書いていたが、calibrator 成功後にも cleanup 段があり、
    そこが失敗すれば scheduler 終了値は非 0 になりうる。名乗りの段階を分け直した。
  - 親の段 1 brief は「受入全走 6752 件で赤 4 件 = pin 閉包」と一般化していた。これは
    **「受入 test が観測した pin 閉包」**であって、PBS job script・手動 CLI・production 経路の
    閉包ではない。production consumer 2 本 (`qualification/identity.py` と `submission.py`) が
    棚卸しから漏れていたのもレンズ B が拾った。
- **現行 bytes の pin は親が変更前 bytes から独立に算出して実装子へ与えた。** 実装子が
  自分の書いたファイルから算出すると誤った編集にも一致する自己成就 pin になる。
  段 6 のレビュー A が独立に再計算して一致を確認し、自己成就の疑いを refuted と判定した。
- **certify job の成功が既存テストの潜在的な非決定を顕在化させた。** 較正が 2 本になったことで、
  `registered/` を `next(glob(...))` で 1 本選んでいた箇所が filesystem 列挙順に依存するようになった。
  選ばれた較正の `samples_mhz` は corpus 全体の ±2% 基準に使われる。環境契約が現に指す較正を
  明示的に読む形へ直し、参照 bytes の sha256 検証も足した。**緩めたのではなく強めた。**
  これは受入を再走させたから見つかった — 成果物を commit しただけで land していたら残っていた。
- **scheduler の `.o` / `.e` は投入 directory (repo 直下) へ返る。** `submit_certify.sh` は
  `qsub` に `-o` / `-e` を渡さず、job は `PBS_O_WORKDIR` を repo root と解釈するため cwd を
  変えられない。前回 job と同じく job-staging directory へ移して clean 化した。恒久対応は返す。
- **名乗りの上限を段階で固定した。** 名乗るのは「依存段の通過」「certify job の完走」
  「accepted calibration の publish」まで。**活性化・登録は名乗らない** — `env_contract` の
  参照は旧較正のままで、切替は活性化権限の裁定に属する。**final receipt の検収も未実施**で、
  collector はログインノード直実行を禁じられており正規経路は別タスクの裁定待ちである。
- 受入全走は計算ノードで 3 回。前提実測 (変異あり) が 4 failed / 6728 passed、
  certify 成果物取り込み後が 1 failed / 6773 passed (上記の corpus 登録漏れ)、
  fix 後の tip `ae9582b5` で **6774 passed / 20 skipped** (request 892735.nqsv、1164.83s)。
  land 直前の merge 後 tip でも再走した。
- 変異は事前登録 5 件で **5/5 KILLED・node 集合完全一致・SURVIVED 0**。初回走行 (anchor `a6f6f37f`)
  と fix 後の再走 (anchor `ae9582b5`) で結果は同一。**MISMATCH 0 件で erratum なし。**
- 逐語と台帳は `output/insights/2026-08-06_t564-dependency-source/`。

## 次の一手差分

### 完了

- [T-564] 択一 (b) を採って依存 source の所在を `/work/SFC/tanab/github/{gflags,glog}` へ移し、
  境界テストを D96 の手続で追随させた。certify job 892707.nqsv は依存段を通過して完走し、
  `gflags source path missing` の blocker は除去された。
  remaining: none
  base: d123cb30c7fbc5dcab340163410d886711cbd199739502e7452fed477d69f3e6

### 更新

- [T-419] **P1・取得は達成、独立検証と登録は未達**: 着手条件 (ii) accepted publish receipt は
  certify job 892707.nqsv が満たした (`calibrate_rc=0`、
  `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` を publish)。
  **(iii)(iv) は未達のまま。** (iii) 別 process の完全独立検証は未実装、(iv) 例外集合の空化は
  登録が前提で、登録は [T-529] の活性化権限が前提である。
  **活性化は名乗らない** — `env_contract` の `calibration_ref` は旧較正
  `calibration-753f535a8d024727.json` を指したままである。
  **final receipt の検収も未実施** — collector はログインノード直実行を禁じられており、
  正規経路は入力 cap と測定経路の裁定を踏まえた後になる。
  一次資料 = `output/insights/2026-08-06_t564-dependency-source/README.md`
  base: 9cfe8467c8c92863cd37890b67124828b9532e164bd3dd6353dae75ba2850828

### 新規

- {{T:production-current-history-binding-test}} **P2・新規**: production の
  `validate_current_bindings` は凍結 evidence を現行 bytes と等値比較して拒否するが、
  その境界を固定するテストが無い。`test_collect_fixture_bundle_publishes_without_self_rejection` は
  production validator を monkeypatch しているため証拠にならない。`driver` binding が歴史値に
  なった時点から存在する状態で、[T-564] の新規回帰ではない。current-only が意図なら直接テストを、
  歴史 artifact も受理すべきなら production の scope 拡張を要する。
- {{T:submit-certify-scheduler-output}} **P2・新規**: `submit_certify.sh` が `qsub` へ
  repo 外の `-o` / `-e` を渡さないため、job のたびに `.o<ID>` / `.e<ID>` が repo 直下へ返り、
  次の submit を dirty gate が、land を clean 要求が塞ぐ。repo を submit directory にする job は
  `-o` / `-e` をファイル path で渡す規範が runbook にあるのに従っていない。
  現状は毎回手で job-staging へ移して凌いでいる。
- {{T:submit-certify-repo-root-binding}} **P3・新規**: `submit_certify.sh` の `--repo-root` と
  job 側の `PBS_O_WORKDIR` 解釈が分離しうる。別 directory から `--repo-root` を使うと、
  submitter が clean / hash 検査した木と job が実行する木が食い違う。
  submitter が qsub 前に `cd "$REPO_ROOT"` するか、物理 path 不一致を拒否する。
- {{T:dependency-source-hydrate}} **P3・新規**: 依存 source の所在を機体固有の絶対 path で
  repo に書く結合そのものの除去。[T-564] の択一 (c) にあたり、`fetch_third_party.py` の
  対象を FetchContent 3 source から gflags / glog へ広げる。可搬性と [T-443]/[T-444] の
  source proof を同時に改善しうる。
