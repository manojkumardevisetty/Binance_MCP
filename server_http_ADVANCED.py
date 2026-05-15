#!/usr/bin/env python3
import json, logging, os
from typing import Optional
import jwt
from binance.client import Client
from binance.exceptions import BinanceAPIException
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TESTNET = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET", "MUST_BE_REPLACED")
USERS_DB = "/opt/binance-mcp/data/users.json"

app = FastAPI()

def load_users():
    try:
        with open(USERS_DB) as f:
            return json.load(f)
    except:
        return {}

def verify_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"]).get("sub")
    except:
        return None

def get_user_client(username):
    users = load_users()
    user = users.get(username, {})
    api_key = user.get("binance_api_key")
    api_secret = user.get("binance_api_secret")
    if not api_key or not api_secret:
        return None
    return Client(api_key, api_secret, testnet=TESTNET)

@app.post("/messages")
async def messages(request: Request, authorization: Optional[str] = Header(None)):
    if not authorization:
        return JSONResponse({"error": "Missing auth"}, 401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse({"error": "Invalid"}, 401)
    username = verify_jwt(parts[1])
    if not username:
        return JSONResponse({"error": "Invalid token"}, 401)
    try:
        body = await request.json()
    except:
        return JSONResponse({"error": "Bad JSON"}, 400)
    method = body.get("method")
    logger.info(f"[{username}] {method}")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": body.get("id"), "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "binance-futures", "version": "1.0"}}}
    if method == "tools/list":
        tools = [
            {"name": "get_account_info", "description": "Get balance, positions, leverage", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            {"name": "get_mark_price", "description": "Get current mark price", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_24h_stats", "description": "24h volume, high, low, change %", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_funding_rate", "description": "Perpetual funding rate", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_open_orders", "description": "List open orders", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": []}},
            {"name": "get_order_history", "description": "Past trades", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "limit": {"type": "number"}}, "required": ["symbol"]}},
            {"name": "get_conditional_orders", "description": "Pending stop/TP orders", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_position_leverage", "description": "Current leverage", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_position_pnl", "description": "Unrealized P&L %", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_liquidation_price", "description": "Liquidation level", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "set_leverage", "description": "Set leverage", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "leverage": {"type": "number"}}, "required": ["symbol", "leverage"]}},
            {"name": "place_market_order", "description": "Market order", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "side": {"type": "string", "enum": ["BUY", "SELL"]}, "quantity": {"type": "number"}, "leverage": {"type": "number"}}, "required": ["symbol", "side", "quantity"]}},
            {"name": "place_limit_order", "description": "Limit order", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "side": {"type": "string", "enum": ["BUY", "SELL"]}, "quantity": {"type": "number"}, "price": {"type": "number"}, "leverage": {"type": "number"}}, "required": ["symbol", "side", "quantity", "price"]}},
            {"name": "batch_orders", "description": "Place multiple orders", "inputSchema": {"type": "object", "properties": {"orders": {"type": "array", "items": {"type": "object"}}}, "required": ["orders"]}},
            {"name": "place_stop_loss", "description": "Stop loss order", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "stop_price": {"type": "number"}}, "required": ["symbol", "stop_price"]}},
            {"name": "place_take_profit", "description": "Take profit order", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "take_profit_price": {"type": "number"}}, "required": ["symbol", "take_profit_price"]}},
            {"name": "place_trailing_stop", "description": "Trailing stop (% callback)", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "callback_rate": {"type": "number"}}, "required": ["symbol", "callback_rate"]}},
            {"name": "modify_order", "description": "Edit limit order price", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "order_id": {"type": "string"}, "new_price": {"type": "number"}}, "required": ["symbol", "order_id", "new_price"]}},
            {"name": "cancel_order", "description": "Cancel order", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "order_id": {"type": "string"}}, "required": ["symbol", "order_id"]}},
            {"name": "cancel_conditional_order", "description": "Cancel by algoId", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "algo_id": {"type": "string"}}, "required": ["symbol", "algo_id"]}},
            {"name": "cancel_all_conditional_orders", "description": "Cancel all conditionals", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "close_position", "description": "Close & cancel all", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
            {"name": "get_safety_status", "description": "Safety limits", "inputSchema": {"type": "object", "properties": {}, "required": []}},
        ]
        return {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": tools}}
    if method == "tools/call":
        name = body.get("params", {}).get("name")
        args = body.get("params", {}).get("arguments", {})
        client = get_user_client(username)
        if not client:
            result = "ERROR: Credentials"
        else:
            try:
                if name == "get_account_info":
                    acct = client.futures_account()
                    balance = acct.get('totalWalletBalance', 'N/A')
                    available = acct.get('availableBalance', 'N/A')
                    positions = [p for p in acct.get('positions', []) if float(p.get('positionAmt', 0)) != 0]
                    pos_str = '\n'.join([f"  {p['symbol']}: {p['positionAmt']} ({p['leverage']}x) | PnL: {p['unrealizedProfit']} USDT" for p in positions]) if positions else "None"
                    result = f"Balance: {balance} USDT\nAvailable: {available} USDT\nPositions:\n{pos_str}"
                elif name == "get_mark_price":
                    symbol = args.get("symbol", "BTCUSDT").upper()
                    data = client.futures_mark_price(symbol=symbol)
                    result = f"{symbol}: {data['markPrice']}"
                elif name == "get_24h_stats":
                    symbol = args.get("symbol", "BTCUSDT").upper()
                    try:
                        stats = client.futures_ticker(symbol=symbol)
                        result = f"24H: {symbol}\nVol: {stats['volume']}\nHigh: {stats['highPrice']}\nLow: {stats['lowPrice']}\nChange: {stats['priceChangePercent']}%"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "get_funding_rate":
                    symbol = args.get("symbol", "BTCUSDT").upper()
                    try:
                        rate = client.futures_funding_rate(symbol=symbol)
                        current = rate[0] if isinstance(rate, list) else rate
                        result = f"Funding {symbol}:\nRate: {float(current.get('fundingRate', 0)) * 100:.4f}%\nTime: {current.get('fundingTime')}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "get_open_orders":
                    symbol = args.get("symbol")
                    if symbol:
                        orders = client.futures_get_open_orders(symbol=symbol.upper())
                        result = f"Open: {len(orders)}\n" + "\n".join([f"{o['type']}: ID {o['orderId']}, {o['side']} {o['origQty']} @ {o.get('price', 'MKT')}" for o in orders[:5]])
                    else:
                        orders = client.futures_get_open_orders()
                        result = f"Total: {len(orders)}"
                elif name == "get_order_history":
                    symbol = args.get("symbol", "").upper()
                    limit = int(args.get("limit", 10))
                    try:
                        trades = client.futures_account_trades(symbol=symbol, limit=limit)
                        if not trades:
                            result = f"No trades for {symbol}"
                        else:
                            result = f"TRADES ({len(trades)}):\n"
                            for t in trades[-5:]:
                                result += f"Side: {t['side']}, Qty: {t['qty']}, Price: {t['price']}, PnL: {t.get('realizedPnl')} USDT\n"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "get_conditional_orders":
                    symbol = args.get("symbol", "").upper()
                    try:
                        response = client._request_futures_api('get', 'openOrders', True, symbol=symbol)
                        all_orders = response if isinstance(response, list) else [response]
                        conditional = [o for o in all_orders if o.get('type') in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']]
                        if conditional:
                            result = f"CONDITIONAL: {len(conditional)}\n" + "\n".join([f"{o['type']}: AlgoID {o.get('algoId')}, Stop {o.get('stopPrice')}" for o in conditional])
                        else:
                            result = f"None"
                    except:
                        result = f"Use AlgoIDs from place responses"
                elif name == "get_position_leverage":
                    symbol = args.get("symbol", "").upper()
                    try:
                        positions = client.futures_position_information(symbol=symbol)
                        result = f"Leverage: {positions[0]['leverage']}x" if positions and float(positions[0]['positionAmt']) != 0 else "No position"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "get_position_pnl":
                    symbol = args.get("symbol", "").upper()
                    try:
                        positions = client.futures_position_information(symbol=symbol)
                        if positions and float(positions[0]['positionAmt']) != 0:
                            p = positions[0]
                            unrealized = float(p.get('unrealizedProfit', 0))
                            mark_price = float(p.get('markPrice', 0))
                            amt = float(p.get('positionAmt', 0))
                            pnl_pct = (unrealized / (abs(amt) * mark_price * float(p.get('leverage', 1)))) * 100 if mark_price else 0
                            result = f"P&L {symbol}:\nUSDT: {unrealized:.2f}\n%: {pnl_pct:.2f}%"
                        else:
                            result = "No position"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "get_liquidation_price":
                    symbol = args.get("symbol", "").upper()
                    try:
                        positions = client.futures_position_information(symbol=symbol)
                        if positions and float(positions[0]['positionAmt']) != 0:
                            p = positions[0]
                            result = f"Liq {symbol}:\nPrice: {p.get('liquidationPrice')}\nCurrent: {p.get('markPrice')}"
                        else:
                            result = "No position"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "set_leverage":
                    symbol = args.get("symbol", "").upper()
                    leverage = int(args.get("leverage", 1))
                    try:
                        client.futures_change_leverage(symbol=symbol, leverage=leverage)
                        result = f"✅ {symbol} = {leverage}x"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "place_market_order":
                    symbol = args.get("symbol", "").upper()
                    side = args.get("side")
                    quantity = float(args.get("quantity"))
                    leverage = args.get("leverage")
                    try:
                        if leverage:
                            client.futures_change_leverage(symbol=symbol, leverage=int(leverage))
                        order = client.futures_create_order(symbol=symbol, side=side, type="MARKET", quantity=quantity)
                        result = f"✅ {symbol} {side} {quantity}\nID: {order.get('orderId')}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "place_limit_order":
                    symbol = args.get("symbol", "").upper()
                    side = args.get("side")
                    quantity = float(args.get("quantity"))
                    price = float(args.get("price"))
                    leverage = args.get("leverage")
                    try:
                        if leverage:
                            client.futures_change_leverage(symbol=symbol, leverage=int(leverage))
                        order = client.futures_create_order(symbol=symbol, side=side, type="LIMIT", timeInForce="GTC", quantity=quantity, price=price)
                        result = f"✅ LIMIT {symbol} @ {price}\nID: {order.get('orderId')}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "batch_orders":
                    orders_list = args.get("orders", [])
                    try:
                        results = []
                        for o in orders_list:
                            try:
                                symbol = o.get("symbol", "").upper()
                                side = o.get("side")
                                order_type = o.get("type", "MARKET").upper()
                                quantity = float(o.get("quantity"))
                                if order_type == "LIMIT":
                                    price = float(o.get("price"))
                                    order = client.futures_create_order(symbol=symbol, side=side, type=order_type, timeInForce="GTC", quantity=quantity, price=price)
                                else:
                                    order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
                                results.append(f"✅ {symbol}")
                            except Exception as e:
                                results.append(f"❌ {o.get('symbol', '?')}")
                        result = f"BATCH ({len(orders_list)}):\n" + "\n".join(results)
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "place_stop_loss":
                    symbol = args.get("symbol", "").upper()
                    stop_price = float(args.get("stop_price"))
                    try:
                        positions = client.futures_position_information(symbol=symbol)
                        if not positions or float(positions[0]['positionAmt']) == 0:
                            result = "ERROR: No position"
                        else:
                            qty = abs(float(positions[0]['positionAmt']))
                            side = "SELL" if float(positions[0]['positionAmt']) > 0 else "BUY"
                            order = client.futures_create_order(symbol=symbol, side=side, type="STOP_MARKET", stopPrice=stop_price, quantity=qty, timeInForce="GTC")
                            algo_id = order.get('algoId')
                            result = f"✅ STOP {symbol} @ {stop_price}\nAlgoID: {algo_id}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "place_take_profit":
                    symbol = args.get("symbol", "").upper()
                    tp_price = float(args.get("take_profit_price"))
                    try:
                        positions = client.futures_position_information(symbol=symbol)
                        if not positions or float(positions[0]['positionAmt']) == 0:
                            result = "ERROR: No position"
                        else:
                            qty = abs(float(positions[0]['positionAmt']))
                            side = "SELL" if float(positions[0]['positionAmt']) > 0 else "BUY"
                            order = client.futures_create_order(symbol=symbol, side=side, type="TAKE_PROFIT_MARKET", stopPrice=tp_price, quantity=qty, timeInForce="GTC")
                            algo_id = order.get('algoId')
                            result = f"✅ TP {symbol} @ {tp_price}\nAlgoID: {algo_id}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "place_trailing_stop":
                    symbol = args.get("symbol", "").upper()
                    callback_rate = float(args.get("callback_rate")) / 100
                    try:
                        positions = client.futures_position_information(symbol=symbol)
                        if not positions or float(positions[0]['positionAmt']) == 0:
                            result = "ERROR: No position"
                        else:
                            qty = abs(float(positions[0]['positionAmt']))
                            side = "SELL" if float(positions[0]['positionAmt']) > 0 else "BUY"
                            order = client.futures_create_order(symbol=symbol, side=side, type="TRAILING_STOP_MARKET", callbackRate=callback_rate, quantity=qty, timeInForce="GTC")
                            algo_id = order.get('algoId')
                            result = f"✅ TRAIL {symbol} @ {callback_rate*100:.2f}%\nAlgoID: {algo_id}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "modify_order":
                    symbol = args.get("symbol", "").upper()
                    order_id = args.get("order_id")
                    new_price = float(args.get("new_price"))
                    try:
                        orders = client.futures_get_open_orders(symbol=symbol)
                        original = next((o for o in orders if o['orderId'] == int(order_id)), None)
                        if original:
                            client.futures_cancel_order(symbol=symbol, orderId=int(order_id))
                            new_order = client.futures_create_order(symbol=symbol, side=original['side'], type="LIMIT", timeInForce="GTC", quantity=float(original['origQty']), price=new_price)
                            result = f"✅ MODIFIED\nOld: {order_id}\nNew: {new_order.get('orderId')}\nPrice: {new_price}"
                        else:
                            result = f"ERROR: Order not found"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "cancel_order":
                    symbol = args.get("symbol", "").upper()
                    order_id = args.get("order_id")
                    try:
                        client.futures_cancel_order(symbol=symbol, orderId=int(order_id))
                        result = f"✅ Cancelled {order_id}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "cancel_conditional_order":
                    symbol = args.get("symbol", "").upper()
                    algo_id = args.get("algo_id")
                    try:
                        client._request_futures_api('delete', 'openOrders', True, symbol=symbol, algoId=int(algo_id))
                        result = f"✅ Cancelled {algo_id}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "cancel_all_conditional_orders":
                    symbol = args.get("symbol", "").upper()
                    try:
                        try:
                            response = client._request_futures_api('get', 'openOrders', True, symbol=symbol)
                            all_orders = response if isinstance(response, list) else [response]
                            conditional = [o for o in all_orders if o.get('type') in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']]
                        except:
                            conditional = []
                        if not conditional:
                            result = f"None"
                        else:
                            cancelled = 0
                            for o in conditional:
                                try:
                                    algo_id = o.get('algoId')
                                    if algo_id:
                                        client._request_futures_api('delete', 'openOrders', True, symbol=symbol, algoId=int(algo_id))
                                        cancelled += 1
                                except:
                                    pass
                            result = f"✅ Cancelled {cancelled}/{len(conditional)}"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "close_position":
                    symbol = args.get("symbol", "").upper()
                    try:
                        try:
                            orders = client.futures_get_open_orders(symbol=symbol)
                            for o in orders:
                                try:
                                    client.futures_cancel_order(symbol=symbol, orderId=o['orderId'])
                                except:
                                    pass
                        except:
                            pass
                        positions = client.futures_position_information(symbol=symbol)
                        amt = float(positions[0]['positionAmt']) if positions else 0
                        if amt == 0:
                            result = "No position"
                        else:
                            side = "SELL" if amt > 0 else "BUY"
                            order = client.futures_create_order(symbol=symbol, side=side, type="MARKET", quantity=abs(amt), reduceOnly=True)
                            result = f"✅ CLOSED"
                    except Exception as e:
                        result = f"ERROR: {str(e)}"
                elif name == "get_safety_status":
                    result = f"DRY_RUN={DRY_RUN}\nTESTNET={TESTNET}"
                else:
                    result = f"Unknown: {name}"
            except Exception as e:
                logger.exception(f"Error: {name}")
                result = f"ERROR: {str(e)}"
        return {"jsonrpc": "2.0", "id": body.get("id"), "result": {"content": [{"type": "text", "text": result}]}}
    return {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32601, "message": "Method not found"}}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8765))
    host = os.getenv("HOST", "127.0.0.1")
    logger.info(f"Starting on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
