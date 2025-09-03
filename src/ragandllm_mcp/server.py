import asyncio

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
import httpx
import json
import logging

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("RAGandLLM-MCP")
server = Server("RAGandLLM-MCP")

#呼び出すREST APIのエンドポイント(WSGI利用)
API_BASE_URL = "https://localhost:9993/fish"

#魚の画像Upload
async def upload_file(filename: str):
    file = {'fish': open(filename, 'rb')}
    async with httpx.AsyncClient(timeout=60.0,verify=False) as client:
        response = await client.post(
            f"{API_BASE_URL}/upload",files=file
        )
        response.raise_for_status()
        data = response.json()
        return data

#釣果登録
async def register_choka(fish_id: str, fish_name: str, fish_size: str,fish_count:int) -> str:
    headers={
        "Content-Type":"application/json;charset=utf-8"
    }
    # 送信するJSONボディを組み立て
    body = {
        "FishID": fish_id,
        "FishName": fish_name,
        "Size": fish_size,
        "FishCount": fish_count,
    }
    async with httpx.AsyncClient(timeout=80.0,verify=False) as client:
        response = await client.post(
            f"{API_BASE_URL}/choka",
            headers=headers,
            json=body
        )
        response.raise_for_status()
        data = response.json()
        return data

#OpenAI利用時(/recipe2)／Ollama利用時(/recipe)
async def get_recipe(user_input: str, fish_id:str, fish_name: str) -> str:
    headers={
        "Content-Type":"application/json;charset=utf-8"
    }
    # 送信するJSONボディを組み立て
    body = {
        "UserInput": user_input,
        "FishID": fish_id,
        "FishName": fish_name
    }
    async with httpx.AsyncClient(timeout=80.0,verify=False) as client:
        response = await client.post(
            f"{API_BASE_URL}/recipe2",
            headers=headers,
            json=body
        )
        response.raise_for_status()
        data = response.json()
        return data

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="upload_file",
            description="魚の画像を渡すと魚名が返ります。補足情報として魚IDも返ります。",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "アップロードする魚画像ファイル名フルパス（例: c:\temp\fish.jpg）で指定します。応答はJSONで返送され、FishID、FishName、が返ります。"
                    }
                },
                "required": ["filename"]
            }
        ),
        types.Tool(
            name="get_recipe",
            description="ユーザプロンプトと前回取得した魚名、魚IDを元にレシピ生成",
            inputSchema={
                "type": "object",
                "properties": {
                    "UserInput": {
                        "type": "string",
                        "description": "ユーザのレシピに対する希望。例：夏バテ防止レシピ"
                    },
                    "FishID": {
                        "type": "string",
                        "description": "魚の画像アップロード後に得られた魚ID"
                    },
                    "FishName": {
                        "type": "string",
                        "description": "魚の画像アップロード後に得られた魚の名称"
                    }
                },
                "required": ["UserInput","FishID","FishName"]
            }
        ),
        types.Tool(
            name="register_choka",
            description="釣果登録が行えます",
            inputSchema={
                "type": "object",
                "properties": {
                    "FishID": {
                        "type": "string",
                        "description": "upload_fileの応答JSONにあるFishIDを使用する。upload_fileを事前に実行していいない場合はユーザによる指定が必要"
                    },
                    "FishName": {
                        "type": "string",
                        "description": "upload_fileの応答JSONにあるFishNameを使用する。upload_fileを事前に実行していいない場合はユーザによる指定が必要"
                    },
                    "FishSize": {
                        "type": "string",
                        "description": "釣果登録時、魚の体長をセンチメートルで指定する"
                    },
                    "FishCount": {
                        "type": "integer",
                        "description": "釣果登録時、釣った魚の数を指定する。"
                    }
                },
                "required": ["FishID","FishName","FishSize","FishCount"]
            }
        )

    ]

# この関数の戻り値にMCPクライアント側に表示したいメッセージを書く
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "upload_file":
    
        if not isinstance(arguments, dict):
            raise ValueError("Invalid forecast arguments")
        
        file=arguments["filename"]
        try:
            answer= await upload_file(file)
            print(answer)
            logger.info(f"answer is : {answer}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(answer,ensure_ascii=False, indent=2)
                )
            ]
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            return [
                types.TextContent(
                    type="text",
                    text=f"エラーが発生しました(upload): {json.dumps(error_details, ensure_ascii=False, indent=2)}"
                )
            ]
        except httpx.HTTPError as e:
            logger.error(f"IRIS API error: {str(e)}")
            return [
            types.TextContent(
                type="text",
                text=f"エラーが発生しました(upload): {str(e)}"
            )
            ]

    elif name == "get_recipe":
    
        if not isinstance(arguments, dict):
            raise ValueError("Invalid forecast arguments")
        
        userinput=arguments["UserInput"]
        fish_id=arguments["FishID"]
        fish_name=arguments["FishName"]
        try:
            answer= await get_recipe(userinput,fish_id,fish_name)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(answer,ensure_ascii=False, indent=2)
                    #text=f"🎉 IRIS接続成功！\n📥 応答:：{msg}"
                )
            ]
        
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            return [
                types.TextContent(
                    type="text",
                    text=f"エラーが発生しました(recipe): {json.dumps(error_details, ensure_ascii=False, indent=2)}"
                )
            ]
        except httpx.HTTPError as e:
            logger.error(f"IRIS API error: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"エラーが発生しました(recipe): {str(e)}"
                )
            ]

    elif name == "register_choka":
    
        if not isinstance(arguments, dict):
            raise ValueError("Invalid forecast arguments")
        
        fish_id=arguments["FishID"]
        fish_name=arguments["FishName"]
        fish_size=arguments["FishSize"]
        fish_count=arguments["FishCount"]
        try:
            answer= await register_choka(fish_id,fish_name,fish_size,fish_count)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(answer,ensure_ascii=False, indent=2)
                    #text=f"🎉 IRIS接続成功！\n📥 応答:：{msg}"
                )
            ]
        
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            return [
                types.TextContent(
                    type="text",
                    text=f"エラーが発生しました(recipe): {json.dumps(error_details, ensure_ascii=False, indent=2)}"
                )
            ]
        except httpx.HTTPError as e:
            logger.error(f"IRIS API error: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"エラーが発生しました(recipe): {str(e)}"
                )
            ]


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="RAGandLLM-MCP",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )