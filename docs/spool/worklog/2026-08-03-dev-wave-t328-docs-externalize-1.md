---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t328-docs-externalize
seq: 1
title: "[T-328] docs/dev-wave/** の外出しは D94 が既に却下していた — 実装せずユーザー再裁定へ返し、[T-282] を実測で閉じた (docs のみ、branch worktree-dev-wave-t328-docs-externalize、全走 = Pegasus gen_S 計算ノード request 878402 で 5226 passed / 19 skipped、変異 matrix = 対象外)"
---

## 本文

- **裁定済み択 (b) の前提が成立しないと確定したので実装しなかった。** ユーザー裁定は
  「`docs/dev-wave/**` の逼迫を、縮約でなく入口 + 条件付き reference への外出しで解く (先例 D110)。
  予算上限は上げない。滞留 7 ID の候補も同じ枠へ載せる」だったが、**この 3 条件は同時に成立しない**。
  候補の統合には実測で 1,463 bytes 要り、空きは 2 bytes しかない。縮約が除外され、
  陳腐化節の削除がユーザー裁定事項 (D94 決定 2) である以上、bytes を作る手段は上限を上げるしかない
- **決定的だったのは D94。** 却下案 (a)「ファイル再編・新規 reference ファイル — 読了削減 0 で
  総量予算と checker 改修だけ増える」が本 wave の scope そのものを 2026-07-28 に却下していた。
  **dev-wave の読み込み契約は leaf 節単位でファイル全読ではない**ため、節をどのファイルへ移しても
  読了 payload は変わらない。D110 (provenance) が効いたのは入口が全 commit で全文読まれる構造
  だったからで、**先例は dev-wave へ移らない**。この事実は [T-328] の裁定パッケージに書かれておらず、
  ユーザー裁定の時点で参照されていない。`DW-S01` の F31 (裁定要約でなく decision 本文を優先) に従い
  段 4 で再裁定へ戻した
- **敵対レンズ 2 本が独立に NO-GO。** レンズ A は読量を経路別に数え直し、
  通常実装 +1,667 / docs-only +1,307 / 凍結成果物 +1,667 bytes と**全経路で増える**ことを示した
  (再読を含む下限では +4,951 / +2,535 / +4,951)。レンズ B は「25,200 を名前だけ残して横断 27,200 を
  新設するのは 2,000 bytes の引き上げそのもの」と判定した。real 所見は A が 10 件、B が 14 件。
  refuted は現行 byte 実測表 (レンズ B が独立に再計数して一致)、`DW-G05` の campaign 数値への波及、
  「`DW-Oxx` は role 名 key」という親のカテゴリ誤り
- **レンズ A の A-4 が親の不変条件を 1 つ壊した。** `tools/check_docs.py` は leaf から別 living doc への
  **間接委譲を検査しないと自認している**ため、親が段 1 で置いた「規範 detail の逃がしを機械拒否する」は
  外出しを採っても達成できない。閉包を強めるか、命題を「直接 dispatch と物理実体だけを閉じる」へ
  弱めるかの裁定が別に要る
- **滞留候補そのものにも反証が出た。** (i) [T-328](c)「変異 harness の `flock` は repo 単位で
  並行 wave を跨ぐ」は**前提が誤り** — 親が独立実測し、lock 鍵は `sha256(str(repo))` かつ `--repo` は
  worktree root 一致必須なので **worktree ごとに別 lock** である。並行 wave は競合しない。
  (ii) [T-264](a) を段 1 で stale と判定したのは**親の誤り**で撤回する — `DW-O05` は read-only 子に
  しか発火せず、workspace-write 実装子への「テスト実走は親」義務は現行のどの節にも無い。
  (iii) [T-279](96)-1 の `nohup` 逐語は現行 `DW-O01` の foreground wrapper と衝突する。
  本 wave の親は harness の background 機構だけを使い `nohup`・`&` を重ねない形で codex 子 3 本とも
  成功しており、統合するならこの形が正しい
- **[T-282] を実測で閉じた。** 恒久 tool は置かず、job tmp の一回限り PBS script で全走前後の
  snapshot を同一 job・同一ノードで取った。結果は (i) **repo 残留ゼロ** (`git status -uall` の
  前後差分なし)、(ii) `/tmp` 残留 226 entry / 5,740,811,165 bytes のうち 99.3% は pytest 自身の
  `tmp_path` 木、izanagi 側は `izanagi-t126-submit-stage.*` の 39.5 MB が支配的で残り 186 件は計 166 KB、
  (iii) **job を跨いでは持ち越さない** (直後に別 job を同じ `bnode005` へ投げて不在を確認)。
  計算ノードの `/tmp` は tmpfs でなく nvme 上 xfs なのでメモリも圧迫しない。`<unclassified>` は 0 件
- **測定中に偽赤を踏んだ ({{F:raw-qsub-interpreter-false-red}})。** 生 qsub から
  `python3 tools/run_tests.py` を呼ぶと計算ノードの既定 `python3` が 3.10 未満で
  **116 failed / 2,085 errors**、interpreter を固定しても孫 process が PATH の `python3` を拾って
  **19 failed** が残った。PATH shim を置いて緑になった。正規経路で同一ファイルを単独再走すると
  248 passed / rc=0 で 19 赤は再現しない
- 逐語一式は `output/insights/2026-08-03_t328-devwave-docs-externalize/`。
  子は 3 本とも `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`。
  **実装差分が無いため変異 matrix は対象外**で、全走は [T-282] 実測のためのものである
  (受入全走ではない)
- 作業物の置き場をユーザー是正に従い `/work/1/SFC/tanab/dev-wave-jobs/` へ移した
  (背景 job 既定の `~/.claude/jobs` を Pegasus の home に残さない)

## 次の一手差分

### 完了

- [T-282] 全走前後の prefix 別 snapshot を実測し、repo 残留ゼロ・`/tmp` 残留は job 内に閉じることを
  確定した。恒久 tool は置かない (段 2 プランと段 3 両レンズが一致して過剰と判定)。
  再測手段は `output/insights/2026-08-03_t328-devwave-docs-externalize/t282-residue-measurement.md`
  base: 5952a6daf1308e481b7d8a7534ee571fc9e9ed499cc86f28e9a2a61eab3bca3f

### 更新

- [T-328] **P1・ユーザー再裁定要 (前回裁定の前提が不成立)**: 外出しは実装しなかった。D94 却下案 (a) が
  同じ scope を「読了削減 0 で総量予算と checker 改修だけ増える」として却下済みで、
  dev-wave の読み込み契約が leaf 節単位である以上その実測は今も成立する。
  択 = (a) 上限据え置きのまま**陳腐化節の削除**で空ける (D94 決定 2 の routing、削除はユーザー裁定)、
  (b) **+2,000 bytes の予算引き上げ**と明示し新 D で D94 却下案 (a) を supersede してから外出しする、
  (c) **[T-313] を先に実装する**。**推奨は (c)** — [T-313]「byte 予算を常時読量 gate へ置換」は
  既にユーザー裁定済み・実装待ちであり、上限を上げず、ファイル分割をしないので D94 と衝突せず、
  レンズ A が指摘した「読量が増える」を正面から測る gate になる。
  (b) を採る場合でも、条件 dispatch の発火条件逐語検査・前置きの dispatch 到達性・節 ID の全族一意性・
  consumer 閉包 (`SKILL.md` / `docs/README.md` / 自己改善 routing / `LIVING_DOCS`)・
  failures の逆方向 pointer の是正がすべて scope に入る
  base: 35f99f4e06273849642c006fc0e959f41327f7ae771c6cfe8735e0ae5fc019f4
- [T-264] **P3・(a) の stale 判定を撤回**: 段 1 brief が (a)「実装子 prompt に最初から
  『テスト実走は親』と書く」を `DW-O05` で充足済みと判定したのは誤りである。`DW-O05` の発火条件は
  「read-only codex に相談・レビューさせる直前」で、workspace-write の実装子には渡らない。
  (a) は未充足のまま残る。(c)「予算 gate 対象では変異を byte 中立に」は `DW-M01` の単一理由性で
  部分的に充足済みで、真に足りないのは `tools/mutation_harness.py` の byte 長検査という機械 gate。
  統合先の枠は [T-328] の裁定に依存する
  base: ef835903f0d744bf1004a90b3e4f42d1ab4197e4c74458f7b47522422a05aa12

### 新規

- {{T:dispatch-condition-verbatim-gate}} **P1・新規 (本エントリ、段 3 A-3 / B-2)**:
  条件 dispatch 表の**発火条件の逐語**と列所有を `check_docs` が検査していない。path・節 ID・
  最遅期限・row 数・allowlist を保ったまま、条件 09 の発火条件を「可能性が判明」から
  「変更すると決定」へ狭めても緑のまま通る。D110 決定 3 は provenance 側で
  「発火条件の逐語不一致」を独立 finding にしており (`tools/check_docs.py:1761-1837,2873-2940`)、
  同じ歯を dev-wave 側へ移植できる。**外出しの採否と独立に成立する既存の穴**
- {{T:reference-preamble-unreachable}} **P2・新規 (本エントリ、段 3 A-5 / B-3)**:
  登録 reference の H1 と最初の必須 H2 の間に置いた規範 prose は、予算にも H2 検査にも
  三面一致にも掛からないが、入口が exact 節を読む経路からは**到達できない**。
  現に `docs/dev-wave/operations.md` と `docs/dev-wave/mutation.md` の前置きが
  この位置にあり、「操作の直前に該当節を読み停止条件を迂回しない」等の義務を担っている
- {{T:land-without-check-receipt}} **P1・新規 (本エントリ、段 3 A-8)**:
  `tools/dev_wave_land.py` は LandRequest に test / check の receipt を要求せず、
  spool fold が no-op なら `check_docs` を呼ばずに ff-only land する。
  standalone `check_docs` と全走を省いた tip でも land が成立しうる。
  択 = (a) land を「外部 receipt を信頼する非安全境界」と明記する、
  (b) 独立した pre-land check または検証 receipt を LandRequest へ束縛する
- {{T:supervisor-dwctx-unwired}} **P3・新規 (本エントリ、段 3 B-6)**:
  入口は外部 supervisor 自身へ「最初の `claude -p` spawn 前に `DW-CTX` を読む」と課すが、
  `tools/dev_waves/daemon.py` / `worker.py` に読取処理は無く、prompt を組み立てるだけである。
  現在 fake-only なので runtime blocked。台帳には「無人継続まで閉じた」と書かない
- {{T:qsub-interpreter-contract}} **P3・新規 (本エントリ、実測。マシン固有部分は本 wave で解消)**:
  生 `qsub` から計算ノードで pytest を走らせる経路に interpreter 契約が無く、
  既定 `python3` が 3.10 未満のため偽赤が出る ({{F:raw-qsub-interpreter-false-red}})。
  **マシン固有事実 (既定 `python3` の版・shim の要否・`-o`/`-e` の落ち先) は段 8 で
  `docs/pegasus-runbook.md` §3 へ書いた** — 横断 docs にマシン密結合を持ち込まない規律に従い、
  ここが正しい正本である。残るのは「親が計算ノードで pytest を走らせる直前に正規経路を使う」
  という**環境非依存の手順**を `DW-O18` 側へ足すかで、**その枠は [T-328] の裁定に依存する**
