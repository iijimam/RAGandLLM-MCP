# RAG ＋ 生成 AI であそぼう！の MCP サーバのコード

[RAG + 生成AIであそぼう！](https://intersystems-dc.connpass.com/event/364272/)のウェビナーで使用した MCP サーバー側コードです。

※ REST API 側のコードは https://github.com/Intersystems-jp/RAGandLLM-Asobo にあります。

※ 参考にしたページ：https://qiita.com/Maki-HamarukiLab/items/2f3230d5293beff2ca46

## 含まれるコンポーネント

### ツール

この MCP サーバに含まれるツールは以下の通りです。

- upload_file

  魚の画像ファイルをUploadすると、魚名と魚IDが返ります。

  応答JSON例
  ```
  {
    "FishID": "f025",
    "FishName": "シーバス"
  }
  ```

- get_recipe

  レシピ生成を依頼できます。
  
  upload_file 実行時の応答とユーザの好みの情報や料理経験が入力情報で必要です。

  POST 要求の Body に指定している実際の JSON は以下の通りです。
  ```
  {
    "FishID": "f025",
    "FishName": "シーバス",
    "UserInput": "地元料理でフライパン1つで作れるレシピ"
  }
  ```  

- register_choka

  釣った魚の釣果を登録できます。

  upload_file で得られた魚名(FishName)と魚ID(FishID)を使用します。

  POST 要求の Body に指定している実際の JSON は以下の通りです。

  ```
  {
    "FishID": "f025",
    "FishName": "シーバス",
    "FishSize": "50",
    "FishCount": 2
  }
  ```


## Quickstart

### Install

#### Claude Desktop の開発者用設定

- On MacOS

  `~/Library/Application\ Support/Claude/claude_desktop_config.json`

- On Windows:

  `%APPDATA%/Claude/claude_desktop_config.json`


#### 設定内容

Claude desktop の ファイル>設定>開発者 を開き「設定を編集」をクリックし設定用JSONに以下指定します。

```
"mcpServers": {
  "RAGandLLM-MCP": {
    "command": "uv",
    "args": [
      "--directory",
      "C:\\WorkSpace\\MCPTest\\RAGandLLM-MCP",
      "run",
      "RAGandLLM-MCP"
    ]
  }
}
```

