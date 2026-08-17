# 段 4 裁定 — [T-1279]

親 (izanagi dev-wave manager) / 2026-08-17 09:20 JST

段 3 の敵対相談は省いた。ユーザー裁定が「版の権威をどこに置くかの敵対検証は不要」と明示しており、
DW-C00 の軽量版に該当する。段 6 の敵対レビューは受理集合に触れうるため省かない。

## 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A | 親の P1 (lock pin を git HEAD より先に見る) は official 値を変えうる | **real** | 採用 = P1 を撤回 |
| B | 8c 探索の lock は必ず v2 (authority 付き) | **real** | 採用 (P2 を支持) |
| C | 呼び手側で直す案は build_accepted_report / CLI / 直接 render の省略経路を取り残す | **real** | 採用 (P3 を支持) |
| D | `Path(__file__)` 起点の生成器 repo HEAD は packaging で無関係な HEAD を拾いうる | **real** | 採用 = 生成器 HEAD fallback を作らない |
| E | `test_p3_autonomous_workload_trial.py:2368` の `_git_head` monkeypatch は新 fallback を迂回し回帰を隠す | **real** | 採用 = 除去して実値検査へ差し替える |

### A の根拠 (親が独立に確認)

`_git_head` は「campaign 置き場の git HEAD」を返すが、`generated_from_head` が答えるべきは
「この report を生成したコードの版」である。両者はたまたま一致していただけで、意味が違う。
lock の `contract_loader_commit` は **lock 作成時**の HEAD であり、再生成時の現在 HEAD とは
一般に異なる。したがって lock-first は repo 内 v2 campaign の値を変える = official 経路の
挙動変更にあたる。撤回する。

なお段 2 子は「repo 内の tracked campaign.lock 32 件のうち v2 は 0 件」と報告した。
現存する official 成果物に限れば値は構造的に不変だが、裁定は現物ではなく**入力一般**で取る。

## プラン v2 (確定)

`orchestrator/campaign/layer3_report.py` の中だけで閉じる。

1. 新 private helper `_resolve_generated_from_head(campaign_dir, decoded_lock, generated_from_head)`
   を `_git_head` の直後に置く。解決順は
   1. 明示引数が `None` でなければ**無変更で返す** (既存挙動)。
   2. `_git_head(campaign_dir)` を現行どおり呼び、成功したらその値を返す。
   3. 失敗し、かつ `campaign_dir` が生成器 source repo (`_DEFAULT_OUTPUT_ROOT.parent`) の**内側**
      なら、元の `Layer3ReportError` を再送出する (official 経路の受理集合を 1 mm も広げない)。
   4. source repo の外側で `decoded_lock.authority is not None` なら、検証済み hex40
      `authority.contract_loader_commit` を返す。
   5. authority の無い v1 なら元の `Layer3ReportError` を再送出する。
2. `layer3_report.py:511` の ternary を helper 呼び出しへ置き換える。`decoded_lock` は 444 行で
   既に得ている。**新しい読み取り経路・検証層・gate・schema 変更は作らない。**
3. `_git_head` / `build_report` / `build_accepted_report` / `render` / `main` の signature と
   返り値構造は変えない。

### 不採用にした案と理由

- 呼び手 (`_finalize_build_cell_admission`) へ引数を足す: 所見 C。同じ穴の他入口が残る。
- `Path(__file__)` 起点の生成器 HEAD fallback: 所見 D。無関係 repo の HEAD を静かに拾う経路を
  作るのは、値の意味を曖昧にする方向であり裁定の「だいたいでよい」の範囲を超えて悪化する。
- 明示引数への hex 検査追加: 既存 API は `"fixed"` を受理しており、これは厳密化にあたる。裁定で
  不要と確定済み。scope 外。

## scope 外に送る real 所見

なし。段 2 の所見はすべて本 wave 内で処理できる。

## 変異事前登録 (DW-M01)

対象 file は `orchestrator/campaign/layer3_report.py` 単独。各変異は「新 helper の解決順」という
単一の層にだけ当たり、前後に同じ入力を拒否する層は無い (schema は string としか縛らず、
completeness の hex 要求は hex40 を返す限り発火しない)。

| ID | 変異内容 (production) | 期待 | 落ちるべき test node (完全集合は段 6 fix 後に再導出) |
|---|---|---|---|
| M-1 | helper 呼び出しを **wave 前の実コードの形** `generated_from_head if generated_from_head is not None else _git_head(campaign_dir)` へ戻す | KILLED | 新規 repo 外 v2 test + 8c e2e test |
| M-2 | 解決順 2 と 4 を入れ替え (lock pin を git HEAD より先に見る) | KILLED | 新規 git-backed 優先順 test |
| M-3 | source repo 内外の分岐を落とし、repo 内の git 失敗でも authority へ退避する | KILLED | 新規 official 不変 (負例) test |
| M-4 | `contract_loader_commit` の代わりに `environment_contract_sha256` (hex64) を返す | KILLED | 新規 repo 外 v2 test (完全一致検査) |
| M-5 | v1 + repo 外で `"0" * 40` へ退避する | KILLED | 新規 v1 fail-closed test |
| M-6 | 明示引数を無視して常に解決順 2 以降へ進む | KILLED | 新規 明示値優先 test |

正例 (承認外の過剰拒否を検出する): 既存の official 経路 test 群
(`test_layer3_report.py` の `generated_from_head="fixed"` を渡す全 call) が無変異で緑のままである
こと。受理集合を縮小していないことの証拠として登録する。

M-4 について: hex64 も `_GIT_OBJECT_ID_RE` を満たすため completeness gate では kill されない。
**完全一致検査を新規 test に必ず入れる**こと (DW-M03 の単一理由性)。

## 成果物影響 (DW-G05 再確認)

これを実装しないと 8c 探索の build cell が毎回 `AutonomousTrialError` で倒れ、certified 選択も
層 3 材料レポートも 0 件になる。実装後、探索 campaign の `meta.generated_from_head` は
lock が束縛する hex40 pin になり、official campaign の同 field は不変。

## 裁定 inbox の再走査

段 4 直前に worklog 末尾 (エントリ 622) と `docs/handoff/` を再確認した。[T-1279] に関する
wave 開始後の更新は無い (2026-08-17 09:20 JST)。
