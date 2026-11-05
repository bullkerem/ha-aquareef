import ast, asyncio, logging, time, unittest
from datetime import datetime
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

root=Path(__file__).resolve().parents[1]/'custom_components/aquareef'
for p in root.glob('*.py'):
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
tree=ast.parse((root/'coordinator.py').read_text(encoding='utf-8'))
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
methods=[n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name in ('async_send_tcp_raw','_async_sync_hardware','_async_periodic_tick')]
class HAError(Exception): pass
ns=dict(asyncio=asyncio,time=time,datetime=datetime,dt_util=SimpleNamespace(now=lambda:datetime(2026,11,5,10,0)),_LOGGER=logging.getLogger('test'),HomeAssistantError=HAError,CHANNEL_ORDER=['red','green','royal_blue','blue','white','uv','mint','cyan','violet'])
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='TestCoordinator',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[])),'extracted','exec'),ns)

class TransportTests(unittest.IsolatedAsyncioTestCase):
    def make(self):
        c=ns['TestCoordinator']();c._socket_lock=asyncio.Lock();c._last_tcp_close_ts=0
        c.host='test';c.port=8899;c.is_on=True;c.master_brightness=255
        c.channels={k:50 for k in ns['CHANNEL_ORDER']};c._last_sent_payload=b'';c._manual_mode_sent=False
        c.data={'is_on':False,'channels':{k:0 for k in ns['CHANNEL_ORDER']}}
        c._get_current_state=lambda:{};c.async_set_updated_data=Mock()
        return c
    async def test_connect_failure_propagates_and_rolls_back(self):
        c=self.make()
        with patch.object(asyncio,'open_connection',AsyncMock(side_effect=TimeoutError())):
            with self.assertRaisesRegex(HAError,'TimeoutError'):
                await c._async_sync_hardware(True)
        self.assertFalse(c.is_on);self.assertFalse(c._tcp_connected)
        self.assertEqual(c._last_sent_payload,b'')
    async def test_drain_failure_closes_socket(self):
        c=self.make(); w=Mock();w.drain=AsyncMock(side_effect=ConnectionResetError());w.wait_closed=AsyncMock()
        with patch.object(asyncio,'open_connection',AsyncMock(return_value=(Mock(),w))):
            with self.assertRaises(ConnectionResetError):await c.async_send_tcp_raw(b'm')
        w.close.assert_called_once();self.assertFalse(c._tcp_connected)
    async def test_frame_encoding_and_no_ack(self):
        c=self.make();r=Mock();r.read=AsyncMock(side_effect=TimeoutError());w=Mock();w.drain=AsyncMock();w.wait_closed=AsyncMock()
        with patch.object(asyncio,'open_connection',AsyncMock(return_value=(r,w))):
            await c._async_sync_hardware(True)
        self.assertEqual(w.write.call_args.args[0],b'm'+bytes.fromhex('07d0')*9+b'\0')
        self.assertEqual(w.write.call_args_list[0].args[0],b'o'*20)
        self.assertEqual(w.write.call_count,2)
        self.assertTrue(c._tcp_connected);self.assertEqual(c._last_tcp_response,'')
        self.assertEqual(c._last_sent_channels,c.channels)
    async def test_off_frame(self):
        c=self.make();c.is_on=False;c.async_send_tcp_raw=AsyncMock(return_value=b'')
        await c._async_sync_hardware(True)
        self.assertEqual(c.async_send_tcp_raw.call_args.args[0],b'm'+b'\0'*19)
    async def test_small_simulation_steps_reach_transport(self):
        c=self.make();c.simulation_enabled=True;c.schedule_enabled=False
        c.cloud_enabled=False;c._sim_preview_until_ts=0
        c._last_sim_synced_phase='dawn';c._last_sim_hw_sync_ts=time.time()
        c.channels={k:11 for k in ns['CHANNEL_ORDER']}
        c._last_sent_channels={k:10 for k in ns['CHANNEL_ORDER']}
        c.compute_simulation_channels=lambda minute:({k:12 for k in ns['CHANNEL_ORDER']},'dawn')
        c._async_sync_hardware=AsyncMock()
        await c._async_periodic_tick(None)
        c._async_sync_hardware.assert_awaited_once()

if __name__=='__main__':unittest.main(verbosity=2)
