# [T-574] historical resolver の production 配線 — 逐語と裁定パッケージ

契約世代を進めても publish 済み成果物を再検証できるようにするため、artifact に記録された
`contract_sha256` から世代を解決する resolver を read-only 再検証の consumer へ配線した wave の
一次資料。branch `worktree-dev-wave-t574-historical-resolver`。

## 何をしたか

`launch_validate` は **live 実走の admission と read-only 再検証の共用入口**だった (親が実測、
`parent-measured.md` §3)。そのまま historical 化すると新規実走の受理集合まで広がるため、入口を分けた。

- `launch_validate` は current 束縛のまま、受理集合を 1 bit も変えない。
- `reverify_published_freeze` を新設。記録 hash から世代を **artifact 1 件につき 1 回だけ**解決し、
  同一 contract を journal / run_cmd / result / occurrence の全 edge へ必須引数で通す。
  戻り値は `LaunchValidatedFreeze` と別型の `ReverifiedFreeze`。
- oracle report の再検証呼び出しだけを新入口へ移し、`_receipt_expectations` を resolver 必須にした。
- 未知 hash・非一意・cross-env・recorded と違う entry を返す resolver・解決世代の calibration
  欠落 / hash 不一致は、いずれも current への fallback なしで fail-closed。

## 保証しないこと (名前の縮小)

**この wave は `versioned predicate dispatch` を実装していない。その語を成果物で使わない。**
正当な後継世代が変えられるのは calibration の path/sha だけなので (`is_valid_successor`)、
`clocks_per_us` / `numactl` / `attestation_mode` は世代間で必ず同値になる。したがって
「解決した世代の値を使う実装」と「current を引く実装」は正当な世代では観測的に区別できない。
区別できない保証を台帳に書かないという D196 の規律に従い、保証を
**「記録 hash からの世代解決」と「解決世代の calibration 選択」**に限定した。

さらに `ReverifiedFreeze` の型分離は**偽造耐性を主張しない**。`LaunchValidatedFreeze` は封印
されていない素の frozen dataclass であり (実測)、効くのは自分たちの consumer が黙って広がらない
ことだけである。真の防壁は「driver が historical 経路をそもそも呼ばない」ことにある。

## ファイル

| file | 内容 |
|---|---|
| `parent-measured.md` | **親が自分で実走した事実だけ**。射程の限定を含む。まずここを読む |
| (probe 逐語) | 段 1 前提実測の計器は `parent-measured.md` §1 の code block に埋め込んである。親 (Claude) が書いた Python を実行可能ファイルとして repo へ置くと `docs/ai-provenance.md` の Codex `role=author` 必須契約に抵触するため |
| `brief.md` | 段 1 brief。**3 点が段 4 で訂正されている** (下記) |
| `s2-plan.md` | 段 2 codex プラン (骨子は段 4 で差し替え) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 2 レンズ逐語 |
| `s4-adjudication.md` | **段 4 裁定 (実装の正本)** |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-reviewR1.md` / `s6-reviewR2.md` | 段 6 敵対レビュー 2 本逐語 |
| `s6-fix-ruling.md` | 段 6 fix 裁定 |
| `s6-fix.md` | 段 6 fix 子の報告 |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 run 2 (採用) |
| `mutation-spec-run1-erratum.json` / `mutation-ledger-run1-erratum.json` | 変異 run 1 (erratum、消さずに残す) |

## 段 1 brief の誤り 3 点 (段 4 で訂正済み)

1. C1〜C3 を「read-only 再検証」と分類したのは誤り。`launch_validate` は live 実走 admission と
   共用である。
2. DW-O09 の「旧 hash pin は 0 件」は偽。`env_contract.py` には publish 済み歴史 pin が
   path key と role 名 key の双方に存在する (本 wave は同 file を変更しない)。
3. probe の射程は 2 leaf の counterfactual であり、「selector まで含めて全部落ちる」は
   D196 の文言の引き写しだった。

## ユーザー裁定待ちの択一 (実装していない real 所見)

| # | 択一 | 重さ | 根拠 |
|---|---|---|---|
| R1 | **記録 hash を世代選択の権威にしてよいか。** (a) 登録済み registry に限定される現状を受容し「非偽造」を主張しない / (b) 活性化 record を先に実装する (D196 の順序を覆す) / (c) 外部 trust root を導入する | **重** | resolver が証明するのは形式・登録・一意性・env 一致だけで、「その世代が artifact 作成時に active だった」ことは証明しない。fuse が 1 世代を強制する間は発火しない |
| R2 | **silo `verify-result` は歴史 proof verifier か current 互換 verifier か。** (a) 歴史 verifier として resolver を配線 / (b) current 互換検査と明示し「全 certified 成果物を再検証可能」から除外 | **重** | 記録 hash を current と比較する第 5 の層。**今日すでに `driver` binding で赤**であり、意味が曖昧なまま残っている |
| R3 | **世代更新を跨いだ resume を失ってよいか。** (a) current-only resume を正式仕様として availability loss を受容し回帰試験で固定 / (b) recorded contract を resume 実行辺まで伝播する別 scope を起こす | **重** | `linux-baremetal` は `allow_resume=True`。「pegasus は `allow_resume=False` だから実害なし」という親の一般化は段 3 の両レンズが否定した |
| R4 | **真の versioned predicate dispatch を別途起こすか。** | 中 | 正当な世代遷移で観測差を作れる遷移規則と generation-aware dispatcher が要る。現 successor 規則では作れない |
| R5 | **historical calibration bytes の保存契約を作るか。** | 中 | 今は「欠落なら fail-closed」で閉じるが、旧 path の削除を禁じる契約はない |
| R6 | **oracle report の `repo_root` 分裂を直すか。** `_receipt_expectations` は module 定数 `ROOT`、CLI は `--repo-root` を受ける | 小 | 既存欠陥で世代解決とは独立 |
| R7 | **宣言済みだが不正な `run_contract` を legacy と見なす既存挙動を直すか。** (a) field があるのに `env_tag` / `contract_sha256` が欠落・空・非文字列なら manifest-global error にする (受理集合の縮小) / (b) 既存挙動を正式仕様として明記し回帰試験で固定 | 中 | 本 wave 以前から同一の分岐。contract / calibration / execution receipt の束縛なしに row が `completed` へ到達しうる |

R1〜R3 が骨格を決める。とくに R1 は [T-529] (活性化権限) の前提そのものである。

## 段 8 (自己改善) の結果

候補 2 件を裁定した。

- **候補 A (見送り、予算)**: worktree 隔離された背景 job では、`DW-O01` が示す 1 行の codex 起動形を
  そのまま Bash へ渡すと harness が複合 command として拒否するため、launcher script を Write して
  起動する。本 wave でも段 3 の完了確認で実際に拒否され 1 往復を失った。
  `docs/dev-wave/operations.md` への追記が自然な行き先だが、`docs/dev-wave/**` の合計は
  **25,187 / 25,200 bytes** で**残り 13 bytes** しかなく、1 行 (約 80 bytes) が入らない。
  **同じ理由での見送りはこれで 3 例目**である。
- **候補 B (実施)**: 段 1 の前提実測で親が書いた probe の `.py` を insights へ凍結したところ、
  provenance の実装面 Codex `role=author` 契約に抵触した。これは既存 F75 と同型で、
  F75 の恒久対応 (逐語を code block へ埋め込む) がそのまま解になった。失敗台帳へ**再発**として送り、
  F75 の判別条件を「段 6 で harness を書く前」から「親が実行可能ファイルを書くとき常に」へ広げた。
  dev-wave reference は変更しない (予算外の台帳で閉じたため)。

| # | 択一 | 根拠 |
|---|---|---|
| R8 | **dev-wave reference の予算飽和をどうするか。** (a) 陳腐化した節をユーザー裁定で削って空ける / (b) 現状維持で候補を insights に貯め続ける | 残り 13 bytes。3 wave 連続で改善が入らず、同じ候補が繰り返し記録だけされている。**上限引き上げは既裁定で提案しない**。dev-wave 系の外出しも既裁定で禁じられている (読み込みが leaf 節単位で削減 0) |
