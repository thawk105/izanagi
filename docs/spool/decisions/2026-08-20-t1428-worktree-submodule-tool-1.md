---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: t1428-worktree-submodule-tool
seq: 1
---

## {{D:worktree-submodule-init-tool}}. worktree submodule 初期化を専用スクリプトへ集約する

**決定:** worktree 再作成時に `git submodule update --init` が file transport 既定禁止で
必ず失敗する問題を、手順書 (`docs/dev-wave/operations.md` の DW-O08/DW-O20) の文言修正では
なく、`tools/dev_wave_submodule_init.py` という専用スクリプトの新設で解消する。既存の
`tools/dev_waves/git_state.py::update_submodules_no_fetch()` (daemon.py が既に本番運用) を
再利用し、正しい flag (`-c protocol.file.allow=always ... --init --recursive`) を複製しない。
`docs/dev-wave/core.md` の DW-C01 (DW-O08/DW-O20 に優先する権威節) の submodule bullet を、
このスクリプト呼び出しへの短い pointer へ置換する。

**理由:**
- 手作業の git コマンド構築 (flag の失念・誤記) が F320 の実際の失敗経路であり、1コマンドの
  固定スクリプトへ置き換えることでこの失敗モードを構造的に無くせる。
- `docs/dev-wave/operations.md` 側は過去の同種修正試行が byte 予算 (1000 bytes/節) の壁で
  頓挫していた ({{F:submodule-nonlocal-url-false-reject}} 参照)。docs 文言修正を主たる
  解決手段にしないことで、この壁を回避する。
- EnterWorktree (Claude Code harness 組み込み) 自体は本 repo の改変対象外であり、
  「手作業の完全な自動排除」ではなく「手作業の失敗モードの排除」がこの wave の現実的な scope
  であると裁定した。

**却下した選択肢:**
- `docs/dev-wave/operations.md` (DW-O08/DW-O20) の文言だけを是正する — byte 予算の壁で過去に
  頓挫済みであり、かつ手作業自体は残る。
- `tools/check_wave_startup.py` (観測専用の既存 checker) 自体に修復ロジックを混ぜる —
  同 checker 自身の docstring が「修復操作は行わない」と明記しており、checker/mutator の
  分離という既存設計を壊す。

## {{D:submodule-url-resolved-fallback}}. submodule ローカル判定は宣言と解決済み URL の両方を見る

**決定:** `update_submodules_no_fetch()` の pre-flight local 判定を、`.gitmodules` の宣言 URL
だけでなく、`git config --get submodule.<name>.url` で得られる解決済み URL (override 込み) も
考慮する対称判定へ拡張する。解決済み URL が取得できればそれを正本とし、取得できなければ
(override 無し) 宣言 URL にフォールバックする。

**理由:**
- 本 repo の実際の submodule 構成 (`external/ccbench` は `.gitmodules` 宣言が remote だが
  実行環境の `.git/config` で local override 済み) で、宣言だけを見る従来の判定は
  git が実際に使う URL と乖離しており、正当な local 操作を誤って拒否していた
  ({{F:submodule-nonlocal-url-false-reject}} 参照)。
- 解決済み URL は git 自身が submodule 操作で実際に使う値であり、これを判定基準に含めることは
  「意味論的に正しい」方向の修正である (単なる緩和ではない)。
- 悪用には対象 repo の `.git/config` への書込み権限が要り、これは `-c
  protocol.file.allow=always` を手動で付けて実行できる権限と同水準であるためユーザーが
  許容範囲と裁定した。

**却下した選択肢:**
- `tools/dev_wave_submodule_init.py` 側だけで pre-flight を薄く迂回する — `update_submodules_no_fetch`
  を daemon.py 等と共有する以上、同じ環境不整合が他 consumer にも将来再発しうるため、
  共有関数側の修正を優先した。
- pre-flight 検査自体を削除する — `.gitmodules` の宣言と乖離した任意の remote URL を無検査で
  通すことになり、既存の防御水準を後退させる。

## {{D:registered-worktree-chroot-boundary}}. worktree 身元検証は common_dir/worktrees/ chroot までとする

**決定:** 新設した `resolve_registered_worktree()` の worktree 身元検証は、candidate の
実際の gitdir が `<common_dir>/worktrees/` 配下に実在することまでを保証する
(段6 敵対レビュー2本が独立発見した stale registry 偽装への対応、
{{F:worktree-registry-spoofed-gitdir}} 参照)。**完全な TOCTOU 耐性、および
「別の実在・登録済み worktree の gitdir を指す偽装」への対策は、この wave では意図的に
実施しない。**

**理由:**
- 検証後から実行までの間に候補ディレクトリが差し替えられる TOCTOU は、本 repo の姉妹関数
  (`create_exact_worktree` 等) も同種の防御を持たず、AI が単発で操作するローカル CLI という
  脅威モデルでは過剰投資と判断した。
- 「別の実在 worktree への偽装」は、悪用に対象 path への書込み権限が要り、結果も repo 内の
  正当な worktree への誤操作に留まる。fix 3巡上限 (DW-O16) に達したため、本 wave では
  対応しないと裁定した。
- 本 wave 以前は worktree 身元検証が皆無だった (どんな path でも無条件に操作されていた) ため、
  上記の残存ギャップを含めても厳密な改善である。

**却下した選択肢:**
- 残存ギャップまで塞ぐ4巡目の fix — DW-O16 の3巡上限を超え、収穫逓減 (段6で新しい懸念が
  出るたびに fix を重ねる) に陥るリスクがあった。
