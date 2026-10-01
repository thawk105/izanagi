# 撤去を促す Stop hook の ff-only 直後の誤検出の修正 (md_6、[T-2951]・[T-2957]、F1081)

2026-10-01、branch `worktree-cleanup-stop-hook-ffonly`。実装は Codex author (gpt-6-astra・ultra)、親は Claude (統合・裁定)。

## 何が起きていたか

`tools/dev_wave_cleanup_stop_hook.py` は、linked worktree の branch が作成点 (reflog の最古項) から前進し、HEAD が `refs/heads/main` の祖先なら
「land 済みの可能性、撤去せよ」と終了を 1 回止める。背景 job の dev-wave は開始時に DW-O20 の `merge --ff-only main` で main に揃えるので、
自分の commit が 0 でも branch が前進して main の祖先になり、turn を終えるたびに誤って止まっていた (md_34 で 3 回、md_37 で 6 回、F1081)。

実物再現 (`raw/repro-before.log`、使い捨て repo に変更前の hook script を通した): 遅れた起点から branch を切り `merge --ff-only main` しただけの木で block、
commit して main へ ff-only land した木でも block (後者は正しい)。

## 何を直したか

免除 (block しない) を次の全部が成り立つ木だけにした。それ以外は従来の判定のまま。

1. branch の reflog の最古項の subject が `branch: Created from ` で始まる (作成項が残っている)。
2. それ以外の全項の subject が `merge main: Fast-forward` か `merge refs/heads/main: Fast-forward` と完全一致する。
3. その各項の OID を、`refs/heads/main` の reflog がその項の時刻以前 (≤) に指していた。
4. reflog の行は LF だけで割り、空 subject は空として扱う (区切りの欠落を fail-open にしない)。main の reflog が読めない・解析できないなら免除しない。

変更後の実物再現 (`raw/repro-after-fix1.log`): ff-only 直後の木は通り、land 済みの木は従来どおり block。

段 5 の最初の実装は 2 と最古項の除外だけだった。段 6 の敵対レビュー 2 本 (`verbatim/review-a.md`・`review-b.md`) が、land 済みの木で促しが消える反例を
4 種示した (作成項が期限切れで最古項が commit になる、U+2028 を含む subject を `splitlines()` が割る、`.strip()` が最古項の空 subject の区切りを消す、
tag `main` や `GIT_REFLOG_ACTION` で同じ subject を作れる)。fix で 1・3・4 を足した (`verbatim/ruling-stage6.md`)。

## 確かめたこと

- 焦点走 (計算ノード、`test_hooks.py -k "cleanup_stop or settings_json"`): 段 5 の差分で 19 passed (request 40717.nqsv)、fix 後 30 passed
  (cleanup_stop 28 ケース + settings_json 2)。
- 変異 (独立 clone、対象 commit `70af9ee82`、runner は `run_tests.py --force-dispatch orchestrator/tests/test_hooks.py`、`mutation/`):
  - probe (全件 SURVIVED 期待で観測 node を集める): baseline 緑。m0 (コメントだけ) と m8 が SURVIVED、他 11 本が落ちた。
  - **m8 の erratum**: m8 は「OID 直後の区切りが無い行を fail-open にする」位置に置いたが、fix 後の書式 (`OID selector subject`) では最古行の
    末尾空白が消えても OID 直後の空白は残るので、注入が欠陥の発火経路に届かず SURVIVED になった (焦点再レビュー C が事前に指摘)。
    「branch の reflog で subject 前の区切りが欠けた行を fail-open にする」位置へ再照準した m8b を足した。初回結果は台帳に残してある。
  - final (12 変異): **12/12 登録どおり** (KILLED 11、m0 SURVIVED、MISMATCH 0)。
  - m8b: probe で `test_cleanup_stop_blocks_landed_oldest_empty_subject` 1 件だけが落ち、その期待で走らせた final も KILLED 1/1 (baseline 緑)。

| 変異 | 何を壊すか | 落ちた node 数 |
|---|---|---|
| m1 | 免除を常に通す | 12 |
| m2 | 免除を常に無効にする | 9 |
| m3 / m3+m9 | subject を `: Fast-forward` の末尾一致に広げる (単独 / main 時刻照合も外す) | 1 / 3 |
| m4 / m4+m9 | 最新項だけを見る (単独 / main 時刻照合も外す) | 1 / 3 |
| m5 | 最古項 (作成項) も ff 判定に含める | 9 |
| m6 | 作成項の要求を外す | 1 |
| m7 | LF 分割を `splitlines()` に戻す | 1 |
| m8b | subject 前の区切りが欠けた行を fail-open にする | 1 |
| m9 | main の reflog 時刻照合を外す | 2 |
| m10 | 時刻比較を `<` にする | 6 |

m10 で落ちる 6 件のうち 3 件は段 5 で足した実時計の test で、main の前進と wave の ff が同じ秒に記録されることが通常であることを示す
(`≤` が要る理由)。この 3 件は秒の境界をまたぐと m10 の下で緑になりうる (本走では 6 件とも落ちた)。

## 確かめていないこと・既知の限界

- 焦点再レビュー C (`verbatim/review-c-focus.md`) が残りの反例 5 件を示した。いずれも親が scope 外と裁定した (`verbatim/ruling-stage6-round2.md`):
  - main の巻き戻し + 同名 tag、`GIT_COMMITTER_DATE` による記録時刻の逆転、`GIT_REFLOG_ACTION=branch` の偽装 commit + 作成項の削除で、
    land 済みの木でも免除されうる。どれも git の記録の改変が要る。旧 hook も reflog の削除や `branch -f` には元々負ける (hooks/README.md hook 5 の既知の限界)。
  - main の reflog が期限切れだと ff だけの木で従来の誤検出が残る (安全側)。
  - main reflog の読み取りが時間切れになると祖先判定の予算が無くなり fail-open で通る。この経路に入るのは作成後の全項が ff main の木だけ。
- 直したのは `merge --ff-only main` (と `refs/heads/main`) の誤検出だけ。sha 指定の ff・`pull --ff-only`・`reset --hard main`・`-m` 付きの ff は従来どおり促しが出る。
- 実際の dev-wave session の Stop event で hook が黙ることは観測していない (使い捨て repo の再現と test だけ)。
- main reflog の読み取り所要は 3,732 項で 0.15 秒の 1 点だけ測った。
- `hooks/README.md` hook 5 の「判定」と「既知の限界」の文言は古いまま。`hooks/` は guard_write の自己保護 (D427) で AI が直接書けず所有外なので、持ち越し項目にした。

## 資料

- `verbatim/`: 段 1 brief、段 4・段 6 の裁定、敵対レビュー A・B と焦点再レビュー C の全文、使い捨て script の逐語。
- `raw/`: 実物再現 (変更前・fix 後)、reflog 時刻と tag `main` の probe、実 repo の branch reflog の観察 (12:00 JST)。
- `mutation/`: spec (probe・final・m8b の probe と final)、台帳 (gz)。
