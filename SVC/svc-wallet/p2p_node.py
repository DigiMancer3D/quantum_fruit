import asyncio
import json
import time

class SVC_P2PNode:
    def __init__(self):
        self.writers = []
        self.server = None
        self.on_receive_coin = None
        self.on_ack_received = None
        self.port = 8000

    async def start(self):
        base_port = 8000
        for attempt in range(9):
            test_port = base_port + attempt
            try:
                self.port = test_port
                self.server = await asyncio.start_server(self.handle_connection, '0.0.0.0', self.port)
                print(f"✅ Mesh started on port {self.port}")
                await self.server.serve_forever()
                return
            except OSError:
                print(f"Port {test_port} full, trying next...")
        raise RuntimeError("No available port")

    async def handle_connection(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"New peer connected from {addr}")
        # FIXED: always register incoming connections
        if writer not in self.writers:
            self.writers.append(writer)
        await self._reader_loop(reader, writer)

    async def connect_to_peer(self, target_port):
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', target_port)
            addr = writer.get_extra_info('peername')
            print(f"✅ Connected to peer on port {target_port}")
            self.writers.append(writer)
            asyncio.create_task(self._reader_loop(reader, writer))
            return True
        except Exception as e:
            print(f"Failed to connect to {target_port}: {e}")
            return False

    async def _reader_loop(self, reader, writer):
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                message = json.loads(data.decode())
                if message.get("type") == "coin-transfer" and self.on_receive_coin:
                    print("✅ Received coin message from peer")
                    self.on_receive_coin(message["coin_data"], message["receiver"])
                elif message.get("type") == "coin-ack" and self.on_ack_received:
                    print("✅ Received ACK from peer")
                    self.on_ack_received(message.get("receiver"))
        except Exception as e:
            print(f"Reader error: {e}")
        finally:
            writer.close()

    async def broadcast_coin(self, coin_data, receiver_address):
        message = {
            "type": "coin-transfer",
            "coin_data": coin_data,
            "receiver": receiver_address,
            "timestamp": time.time()
        }
        sent = 0
        for p in range(8000, 8051):
            if p == self.port: continue
            try:
                reader, writer = await asyncio.open_connection('127.0.0.1', p)
                writer.write((json.dumps(message) + "\n").encode())
                await writer.drain()
                writer.close()
                sent += 1
            except:
                pass
        print(f"Coin broadcasted to {sent} peer(s)")

    def send_ack(self, receiver_address):
        """Synchronous version - works from Tkinter thread"""
        if not hasattr(self, 'writers') or not self.writers:
            print("No writers for ACK")
            return
        message = {
            "type": "coin-ack",
            "receiver": receiver_address,
            "timestamp": time.time()
        }
        sent = 0
        for writer in list(self.writers):
            try:
                writer.write((json.dumps(message) + "\n").encode())
                # drain is non-blocking here (fire-and-forget)
                sent += 1
            except:
                if writer in self.writers:
                    self.writers.remove(writer)
        if sent > 0:
            print(f"ACK sent back to sender (to {sent} peer(s))")
