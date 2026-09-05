# Mini Novels

短編小説と連載小説のための静かな読書室です。[公開サイト](https://m-simplifier.github.io/mini-novels/)

作品の目次から初回・最新話を選び、文字サイズ・書体・配色を調整して読めます。読書位置はブラウザ内に保存し、同じブラウザで続きから再開できます。本文と作品間の移動はJavaScriptなしでも利用できます。

## 使い方

1. 現行版は `stories/` に、初期版アーカイブは `archive/initial/` に Markdown を置く
2. `python3 scripts/build_site.py` を実行する
3. `site/index.html` をブラウザで開く

ローカルでサーバーを立てて見る場合:

```sh
python3 -m http.server 8000 --directory site
```

その後、`http://localhost:8000` を開いてください。

## ホットリロード

Markdown を書きながらプレビューしたいときは、開発サーバーを使います。

```sh
python3 scripts/dev_server.py --port 8000
```

その後、`http://127.0.0.1:8000` を開いてください。
`stories/*.md`, `archive/initial/*.md`, `scripts/*.py`, `web/*`, `content/*.json` のいずれかを保存すると自動で再ビルドされ、ブラウザもリロードされます。
Linux ではファイルシステムイベントで監視し、対応していない環境では polling にフォールバックします。
強制的に polling を使う場合は `--watch-mode poll` を付けてください。

## GitHub Pages

`main` への push ごとに、`.github/workflows/deploy-pages.yml` が `python3 scripts/build_site.py` を実行し、生成した `site/` を GitHub Pages へ公開します。

最初の一回だけ、リポジトリ側で GitHub Pages を有効にする必要があります。有効化後は、`main` に push すれば自動で更新されます。

## 原稿とサイトの構成

- `stories/`: 現行版のMarkdown原稿
- `archive/initial/`: 改稿前の原稿
- `content/catalog.json`: ネタバレを避けた作品紹介、ジャンル、連載目次のURL
- `scripts/manuscripts.py`: 原稿の解析と連載のグループ化
- `scripts/build_site.py`: HTML、作品目次、サイトマップの生成
- `web/`: CSS、読書機能、アイコンの編集元
- `site/`: 公開用の生成物。直接編集せず、ビルドで更新します

Python 3.10以上の標準ライブラリだけで生成できます。連載はfront matterの `series` と `episode` で同じ作品にまとめます。`（前編／中編／後編）` 形式の題名も全編をまとめます。次話を原稿フォルダへ追加すると、目次と前後移動が更新されます。紹介のない新作も原稿のメタデータか冒頭を使って掲載します。

現行版と初期版の既存URL、`section-*` の章アンカーは保持しています。文字数は空白を除いて数え、読了時間は毎分700字を目安にします。読書位置は段落と段落内の割合で保存するため、画面幅や文字サイズが変わっても同じ箇所へ戻れます。

## 読書データと外部通信

読書履歴と設定は `mini-novels:reading:v1` / `mini-novels:settings:v1` としてlocalStorageに保存します。サーバーへの送信や端末間同期、アクセス解析はありません。保存を拒否された場合も、本文とそのページ内の表示設定は動作します。書体のみGoogle Fontsを利用し、未接続時はシステム書体にフォールバックします。

## 検証

```sh
python3 -m unittest discover -s tests -v
```

全原稿の掲載、本文と章アンカーの保持、全ローカルリンク、連載への次話追加、完結表示、404の復帰先を検証します。GitHub Pagesの公開前にも実行します。

実ブラウザの回帰確認にはPlaywrightを使います。ビルド後にHTTPサーバーを起動し、Playwrightをインストールした環境で実行してください。

```sh
node tests/reader.cjs
```

既定の接続先は `http://127.0.0.1:8765/`。`MINI_TEST_URL` で変更できます。Chromiumの既存実行ファイルを使う場合は `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` を指定します。検索、保存・再開、表示設定、キーボード、各画面幅、JavaScript無効、ストレージ拒否時を確認します。

## Markdownの対応範囲

- `stories/*.md` を現行版の一覧ページと個別ページに変換します
- `archive/initial/*.md` を初期版アーカイブの一覧ページと個別ページに変換します
- 本文の `#`, `##`, 段落、箇条書き、`inline code` を拾います
- `##` 見出しから目次を作ります
- 文字数とだいたいの読了時間を表示します
- 開発サーバーでは自動再ビルドとホットリロードが使えます
