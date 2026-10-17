"""Exercise actual island controller with actors/DBus mocked, never a live Shell."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Node required for the JS harness')
class PanelZoneTests(unittest.TestCase):
    def test_clock_playback_hover_menus_and_cleanup(self):
        result = subprocess.run(['node', '--input-type=module', '-'], input=HARNESS,
                                cwd=ROOT, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


HARNESS = r'''
import fs from 'node:fs';
import assert from 'node:assert/strict';
const logic=await import('data:text/javascript;base64,'+Buffer.from(fs.readFileSync('panel-zones-extension/zoneLogic.js')).toString('base64'));
assert.equal(logic.hoveredZone([{left:0,right:100},{left:700,right:1100}],50,2,0,32),0);
assert.equal(logic.hoveredZone([{left:0,right:100},{left:700,right:1100}],350,2,0,32),-1);
assert.equal(logic.hoveredZone([{left:-100,right:0}],-50,101,100,32),0);
let next=1;
class Actor {
 constructor(left=0,width=100){Object.assign(this,{left,width,height:32,opacity:255,translation_y:0,visible:true,style:'original',signals:new Map(),children:[],parent:null,y:0});}
 connect(name,fn){const id=next++;this.signals.set(id,[name,fn]);return id;}
 disconnect(id){assert(this.signals.delete(id));}
 get has_clip(){return !!this.clip;}
 get_clip(){return this.clip;}
 set_clip(...clip){this.clip=clip;}
 remove_clip(){this.clip=null;}
 get_style(){return this.style;}
 set_style(style){this.style=style;}
 contains(actor){while(actor){if(actor===this)return true;actor=actor.parent;}return false;}
 get_transformed_position(){return [this.left,this.translation_y];}
 get_parent(){return this.parent;}
 get_children(){return this.children;}
 add(actor){actor.parent=this;this.children.push(actor);}
 show(){this.visible=true;}
}
const left=new Actor(0,100),center=new Actor(700,400),right=new Actor(1600,320);
const media=new Actor(),clock=new Actor(),extra=new Actor();
center.add(media);center.add(clock);center.add(extra);
media.playerProxy={playbackStatus:'Paused'};
const panel=new Actor();Object.assign(panel,{_leftBox:left,_centerBox:center,_rightBox:right,statusArea:{dateMenu:clock,'Media Controls':media},menuManager:{activeMenu:null}});
const overview=new Actor();overview.visible=false;
const layout=new Actor();Object.assign(layout,{primaryMonitor:{y:0,inFullscreen:false},panelBox:new Actor(),removeChrome:()=>{},addChrome:(_actor,options)=>{layout.options=options;}});
const stage=new Actor();let focus=null;stage.get_key_focus=()=>focus;
const tracker=new Actor();let pointer=[350,400];
let disables=0,enables=0;
const global={backend:{get_cursor_tracker:()=>tracker},stage,get_pointer:()=>pointer,display:new Actor(),compositor:{disable_unredirect:()=>disables++,enable_unredirect:()=>enables++}};
const Main={panel,overview,layoutManager:layout,modalCount:0};
const timers=new Map();
const GLib={PRIORITY_DEFAULT:0,SOURCE_REMOVE:false,timeout_add(_priority,delay,fn){const id=next++;timers.set(id,{delay,fn});return id;},source_remove(id){assert(timers.delete(id));}};
function tick(id){const timer=timers.get(id);assert(timer);timers.delete(id);timer.fn();}
let statusCallback=null,subscription=null;
const Gio={DBusSignalFlags:{NONE:0},DBus:{session:{signal_subscribe(...args){statusCallback=args.at(-1);subscription=next++;return subscription;},signal_unsubscribe(id){assert.equal(id,subscription);subscription=null;}}}};
const source=fs.readFileSync('panel-zones-extension/extension.js','utf8').replace(/^import .*;\n/gm,'').replace('export default class PanelZones extends Extension','return class PanelZones extends Extension');
const Type=new Function('Gio','GLib','Main','global','Extension','hoveredZone',source)(Gio,GLib,Main,global,class {},logic.hoveredZone);
const extension=new Type();extension.enable();
assert.equal(left.opacity,0);assert.equal(right.opacity,0);assert.equal(center.opacity,255);
assert.equal(clock.visible,true);assert.equal(media.visible,false);assert.equal(extra.visible,false);
assert(center.style.includes('background-color: transparent'));
assert.equal(layout.options.affectsStruts,false);assert.equal(layout.options.trackFullscreen,true);
assert.equal(disables,1,'persistent clock acquires compositing with no fullscreen window');
assert.deepEqual(left.clip,[0,0,0,0]);
// Metadata storms must not queue UI work or player lookups.
for(let i=0;i<1000;i++)statusCallback(null,null,null,null,null,{deep_unpack:()=>['player',{Metadata:{}},[]]});
assert.equal(timers.size,0);
media.playerProxy.playbackStatus='Playing';
for(let i=0;i<1000;i++)statusCallback(null,null,null,null,null,{deep_unpack:()=>['player',{PlaybackStatus:{}},[]]});
assert.equal(timers.size,1);tick(extension._timer);
assert.equal(clock.visible,true);assert.equal(media.visible,true);assert.equal(extra.visible,false);
assert.equal(left.opacity,0);assert.equal(right.opacity,0);
media.playerProxy.playbackStatus='Paused';extension._sync();assert.equal(media.visible,false);
pointer=[1800,1];extension._sync();assert.equal(right.opacity,255);assert.equal(left.opacity,0);assert.equal(clock.visible,true);
pointer=[50,1];extension._sync();assert.equal(left.opacity,255);
const hideRight=extension._groups[2].hideTimer;assert(hideRight);tick(hideRight);assert.equal(right.opacity,0);
// Hovering center or an open media menu reveals paused controls for resuming.
pointer=[800,1];extension._sync();assert(media.visible);assert(extra.visible);
pointer=[350,400];panel.menuManager.activeMenu={sourceActor:media};extension._sync();assert(media.visible);assert(clock.visible);
panel.menuManager.activeMenu=null;focus=clock;extension._sync();assert.equal(media.visible,false,'clock focus must not keep paused media visible');
focus=media;extension._sync();assert(media.visible,'keyboard media focus stays accessible');
focus=null;extension._sync();assert.equal(media.visible,false);
media.playerProxy={get playbackStatus(){throw new Error('player closed');}};extension._sync();assert(clock.visible);
// Removing/disabling Media Controls leaves a visible clock and no stale pill.
delete panel.statusArea['Media Controls'];extension._sync();assert(clock.visible);assert.equal(media.visible,false);
layout.primaryMonitor.inFullscreen=true;pointer=[50,1];extension._sync();extension._sync();
assert.equal(enables,1,'fullscreen releases compositing once');
for(const actor of [left,center,right]) assert.equal(actor.opacity,0,'fullscreen hides all islands even when hovering');
assert(extension._groups.every(group=>!group.hideTimer));
layout.primaryMonitor.inFullscreen=false;pointer=[350,400];extension._sync();
assert.equal(center.opacity,255,'leaving fullscreen restores persistent clock');
assert.equal(disables,2,'normal/maximized mode reacquires compositing');
for(let i=0;i<1000;i++)extension._queue();
assert(timers.size<=3,'one motion timer plus at most two per-side hide timers');
extension.disable();assert.equal(timers.size,0);assert.equal(subscription,null);
assert.equal(disables,2);assert.equal(enables,2,'disable balances all acquired compositing holds');
assert.equal(panel.style,'original');assert.equal(layout.panelBox.style,'original');
assert.equal(layout.options.affectsStruts,true);assert.equal(layout.options.trackFullscreen,true);
for(const actor of [left,center,right,media,clock,extra]){assert.equal(actor.style,'original');assert.equal(actor.opacity,255);assert.equal(actor.visible,true);assert.equal(actor.signals.size,0);}
assert.equal(tracker.signals.size,0);assert.equal(stage.signals.size,0);
// A partially failed enable still releases chrome/styles/signals.
tracker.connect=()=>{throw new Error('injected signal failure');};
assert.throws(()=>new Type().enable(),/injected signal failure/);
assert.equal(panel.style,'original');assert.equal(layout.options.trackFullscreen,true);
'''


if __name__ == '__main__':
    unittest.main()
