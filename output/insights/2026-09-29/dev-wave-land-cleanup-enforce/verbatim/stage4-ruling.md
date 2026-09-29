# 段 4 裁定 — dev-wave-land-cleanup-enforce (2026-09-29)

入力: brief-stage1.md、plan-out.md (段 2)、consult-A-out.md (正しさ、must-fix 4)、consult-B-out.md (過剰)。
裁定 inbox の再走査: ListAgents で同主題の稼働 wave 無し (「cleanup branches」session は /cleanup-branches の本走で、command 本文を編集しない契約)。

## 所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| plan P1 完全 archive (全 entry 目録・index 生 bytes・stash・submodule admin 保存・空 repo verify) | B が過剰と指摘、real (実測原因と対応しない) | 不採用。既存退避 (patch・tar・history.bundle・再読照合) を再利用 |
| plan P2 journal・段階別再開 | real (現行は木削除後 receipt 前に再入不能) だが頻度未実測 | 後送 (insight に backlog 記録)。P2 の前進許容で実測 4 件の主因を消し、残る partial を測る |
| A#1 per-worktree ref (`refs/worktree/*`) の commit が bundle から漏れる | real | 採用 (簡易): 退避経路では admin dir 配下の ref / pseudo-ref (`refs/`、`logs/refs/`、ORIG_HEAD 等の operation marker は既存検査) が main 非到達 commit を指すなら拒否 |
| A#2 旧 manifest の path 再利用・land 前の呼出し | 一部 real | 採用: 退避経路は「manifest の wave_worktree が現存し、その HEAD が `refs/heads/main` の祖先」のときだけ。不在・非祖先・判定不能は現行どおり rc=20。作成世代の識別は D2163 の既知限界のまま (退避経路でも内容は bundle・tar に残り損失にならない。生きた使用は占有検査が拒否) |
| A#3 tip 照合と `-D` の競合 | real | 採用: 子 branch 削除を期待 old OID 付きの compare-and-delete (`git update-ref -d refs/heads/<b> <oid>`) にする。統合済み経路も同じ関数を通す |
| A#4 証拠 dir の保管期間 | real (手順側) | 採用: DW-O28 に「`<D>` は job 終了で消えない場所」。tool 側の新検査はしない (機体固有 path を持ち込まない) |
| A#5 Stop hook の偽陽性 (main の ff 取込だけ) と見逃し (main に戻った session) | real | 採用 (軽量 hook を維持): reason は「land 済みの可能性」と弱め、未 land なら 1 行で終えてよいと書く。回収率は主張しない。実測: 撤去せず終えた 2 件のうち 1 件 (vhash-related-work) は終了時 cwd が wave 木、1 件は main に戻っていた |
| A#6 変異の帰属 (reflog 中間 entry、同時変異で緑) | real | 採用: reflog-only commit の fixture は「commit → reset で branch から外す」形 (既存 `test_remove_child_rejects_unreachable_reflog_history` と同型)、tar 検査は独立に作った期待 file 集合と展開結果で照合 |
| B: P3 を後送し land 案内を優先 | refuted (部分) | ユーザーの訴えは文字どおり「land して掃除せず終了する」。終了時の再促しは依頼の核心。land tool の出力変更は 6,487 行・JSON 出力の consumer を持つため不採用 |
| B: fix は同じ木と**同じ branch** を再利用 | real | 採用 (DW-S05-A) |
| A: P2 は proof 時 tip の祖先性で統合証明を壊さない | 採用。receipt に proof 時 main tip を残す (既存 field があれば流用) |

## plan v2 (実装単位は 1 つ、wave 木で直接 = F873 の恒久対応、子木を作らない)

1. `tools/dev_wave_cleanup.py` (remove-child)
   - 統合証明 (`_assert_child_integration`) が不成立のとき、次を全部満たせば退避経路 (`integration_basis="archived-unintegrated"`) へ進む。満たさなければ現行どおり rc=20 (理由文は現行を保ちつつ満たさなかった条件を足す):
     (a) manifest の `wave_worktree` が現存し、その HEAD が `refs/heads/main` の祖先
     (b) HEAD reflog・branch reflog・HEAD・branch tip の全 commit が、main・子 branch tip・他の既存 branch (現行 `_assert_child_history` の規則) のどれかから到達可能。子 branch tip からだけ到達可能な commit は history.bundle に入る (bundle は現行どおり `<branch> ^main`)。detached 子で HEAD が main 非祖先なら拒否 (bundle を作れない)
     (c) admin dir 配下の per-worktree ref が main 非到達 commit を指さない
     (d) 既存の占有・index・変換・submodule・dirty 退避の検査を全部通る (緩めない)
   - 退避経路では dirty の patch・tar と history.bundle の作成・再読照合・`git bundle verify` を統合済み経路と同じく必須にし、失敗は現行どおり撤去せず停止。
   - P2: `:1580` と `:1933` の `main tip == proof.main_tip` を「proof.main_tip が現 main の祖先」へ。判定不能・非祖先 (巻戻し・分岐) は現行の拒否。owned path の tree 比較は proof 時 tip のまま。
   - 子 branch 削除は compare-and-delete (`update-ref -d <ref> <old>`)。`_validate_git_argv` の許可形を最小追加。
   - receipt (`removed.json`) の `integration_basis` に新値。stderr 1 行に basis を出す (stdout の既存形は変えない)。
2. 新 hook `hooks/guard_dev_wave_cleanup_stop.py` + `.claude/settings.json` の `Stop` 配線
   - `stop_hook_active` true・payload 不正・cwd 不在・git 外・primary checkout (git-dir == common-dir)・detached・bare・submodule は通す。
   - 現 branch の reflog 最古 entry の new SHA を作成点とし、(作成点 != HEAD) かつ HEAD が `refs/heads/main` の祖先のときだけ block。reflog 不在・曖昧・git 失敗・timeout (各呼出し 2 秒、全体 5 秒以内) は通す。
   - block は stdout に `{"decision":"block","reason":...}`。reason (日本語): この worktree の branch は local main に land 済みの可能性がある。DW-O28 に従い子木と wave 木を撤去する。撤去できない・未 land・撤去中なら、その旨と残置 path を 1 行書いて終えてよい。
   - 許可と内部失敗は exit 0・出力なし。
3. `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py`: 親が commit した新 DW-O28 本文に `DEV_WAVE_DW_O28_SECTION_LITERAL`・`_SYNTHETIC_DW_O28_SECTION`・byte 数 assert を追随。新 D/F 番号は DW-O28 に書かない (fixture placeholder 不要)。
4. docs (親が先に commit): DW-O28 (997 bytes 以内に圧縮)、DW-S05-A (fix は同じ木と branch を再利用、補助・計測・probe 木も作成時に manifest 登録)、hooks/README.md (Stop hook の節)。

## 既存テスト期待値の変更許可 (これ以外は変えない)
- `test_remove_child_rejects_unintegrated_author_commit`、`test_remove_child_empty_owned_paths_requires_ancestry`: fixture の wave が main 祖先なら退避撤去が成功する正例へ置き換え、同じ入力で wave 木が main 非祖先のときの rc=20 負例を別テストで残す。
- `test_remove_child_main_advance_during_removal_is_partial`: main の fast-forward は完走する正例へ置き換え、main の巻戻し・分岐は rc=20/30 の負例を別テストで残す。
- `test_hooks.py` の settings 配線 test が hook 種別を閉集合で固定しているなら、Stop の追加だけ許す。

## 規模上限
tool 差分 250 行以内、hook 120 行以内、テストは各 300 行以内。超えたら差し戻す。テスト全体 5 分上限を守る (新テストは tmp git repo で 1 本 数秒以内)。

## 補遺 (段 5 の実装子報告を受けて、2026-09-29)
- Stop hook の置き場を `tools/dev_wave_cleanup_stop_hook.py` に変える。`hooks/` は guard_write の「hook 実行面」自己保護で AI の直接書き込みが拒否され、
  変更は D427 の別 worktree 経路 (有効化前 base の第 2 worktree + merge、F266 の着地形) を要する。本 hook は何も拒否しない注意喚起で、
  AI が書き換えても防壁は弱まらない。`hooks/` を防壁専用に保ち、D427 の拒否した「hooks/ の中身を script 越しに書く迂回」には当たらない。段 6 の敵対レビューで攻撃させる。
- 実装子が特定した「`branch -D` 呼出しを固定する既存テスト 2 本」は、compare-and-delete の argv へ追随させることを許す (受理・拒否の意味は変えず、呼出し形の pin だけを直す)。
- docs 予算 (L1.5 9,696) 超過 27 bytes は DW-S05-A の圧縮で解消 (親)。

## 変異の事前登録 (実装後に単一理由性を確認し、成り立たないものは登録から外して理由を記す)
| ID | 変異 | 殺すべき test |
|---|---|---|
| M1 | 退避経路の (a) wave 祖先条件を常に真 | wave 非祖先で rc=20 の負例 |
| M2 | (b) の reflog 到達性検査を退避経路で省く | reflog-only commit の拒否 (既存 unreachable test) |
| M3 | (c) per-worktree ref 検査を省く | `refs/worktree/keep` だけが指す commit の拒否 |
| M4 | detached 非祖先子を退避経路で受理 | detached 非祖先の拒否 |
| M5 | 退避経路で bundle 作成/verify を省く | 退避撤去後に bundle から子 commit を復元できる正例 |
| M6 | P2 の祖先判定を常に真 | main 巻戻し/分岐の拒否 |
| M7 | P2 を等値比較へ戻す | main ff で完走する正例 |
| M8 | compare-and-delete の old OID を外す (無条件削除) | 削除直前に branch が動いたら削除しない負例 |
| M9 | hook が stop_hook_active を無視 | 再 Stop は通す test |
| M10 | hook の (作成点 != HEAD) を外す | commit 0 件の wave は通す test |
| M11 | hook の main 祖先判定を外す | 未 land (main 非祖先) は通す test |
| M12 | settings の Stop 配線を外す | 配線 test |
