"""Exercise actual panel-zone code with mocked actors; never manipulate Shell."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Node is required for the JS harness')
class PanelZoneTests(unittest.TestCase):
    def test_geometry_menus_lifecycle_and_bounded_updates(self):
        result = subprocess.run(['node', '--input-type=module', '-'], input=HARNESS,
                                cwd=ROOT, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


HARNESS = r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
const logic = await import('data:text/javascript;base64,' + Buffer.from(fs.readFileSync('panel-zones-extension/zoneLogic.js')).toString('base64'));
const policy = await import('data:text/javascript;base64,' + Buffer.from(fs.readFileSync('panel-zones-extension/windowPolicy.js')).toString('base64'));
const bounds = [{left:0,right:100},{left:700,right:1100},{left:1600,right:1920}];
assert.equal(logic.hoveredZone(bounds, 10, 0, 0, 32), 0);
assert.equal(logic.hoveredZone(bounds, 800, 20, 0, 32), 1);
assert.equal(logic.hoveredZone(bounds, 1900, 31, 0, 32), 2);
assert.equal(logic.hoveredZone(bounds, 350, 0, 0, 32), -1);
assert.equal(logic.hoveredZone(bounds, 800, 33, 0, 32), -1);
assert.equal(logic.hoveredZone([{left:-100,right:0}], -50, 101, 100, 32), 0);
assert.deepEqual(logic.visibleZones(3, 2, -1, false), [false,false,true]);
assert.deepEqual(logic.visibleZones(3, -1, 1, false), [false,true,false]);
assert.deepEqual(logic.visibleZones(3, -1, -1, true), [true,true,true]);
assert.deepEqual(logic.visibleZones(3, -1, -1, false, 0), [true,false,false]);
let next = 1;
class Actor {
    constructor(left=0,width=100) { this.left=left;this.width=width;this.height=32;this.opacity=255;this.translation_y=0;this.style='original';this.signals=new Map(); }
    connect(name,fn) { const id=next++;this.signals.set(id,[name,fn]);return id; }
    disconnect(id) { assert(this.signals.delete(id)); }
    get has_clip() { return !!this.clip; }
    get_clip() { return this.clip; }
    set_clip(...clip) { this.clip=clip; }
    remove_clip() { this.clip=null; }
    get_style() { return this.style; }
    set_style(style) { this.style=style; }
    contains(actor) { return actor?.parent === this; }
    get_transformed_position() { return [this.left,this.translation_y]; }
    remove_all_transitions() {}
}
function metaWindow(overrides={}) {
    return Object.assign(new Actor(), {minimized:false, maximized_horizontally:true,
        maximized_vertically:true, get_monitor:()=>0, showing_on_its_workspace:()=>true, located_on_workspace:()=>true,
        is_fullscreen:()=>false}, overrides);
}
const maxWindow=metaWindow();
assert(policy.shouldAutohide([maxWindow],0));
for (const changes of [{maximized_horizontally:false}, {maximized_vertically:false},
    {minimized:true}, {get_monitor:()=>1}, {showing_on_its_workspace:()=>false}, {located_on_workspace:()=>false}])
    assert.equal(policy.shouldAutohide([metaWindow(changes)],0),false);
assert.equal(policy.shouldAutohide([],0),false);
assert(policy.shouldAutohide([metaWindow({maximized_horizontally:false,maximized_vertically:false,is_fullscreen:()=>true})],0));
let windows=[maxWindow];
const left=new Actor(0,100), center=new Actor(700,400), right=new Actor(1600,320);
const panel=new Actor();
Object.assign(panel,{_leftBox:left,_centerBox:center,_rightBox:right,menuManager:{activeMenu:null}});
const overview=new Actor();overview.visible=false;
const layout=new Actor();layout.primaryMonitor={y:0};layout.primaryIndex=0;layout.panelBox=new Actor();
let focus=null;
const stage=new Actor();stage.get_key_focus=()=>focus;
const tracker=new Actor();
let pointer=[1900,0];
const timers=new Map();
const GLib={PRIORITY_DEFAULT:0,SOURCE_REMOVE:false,timeout_add(_priority,delay,fn) {const id=next++;timers.set(id,{delay,fn});return id;},source_remove(id) {assert(timers.delete(id));}};
const Main={panel,overview,layoutManager:layout,modalCount:0};
const workspaceManager=new Actor();workspaceManager.get_active_workspace=()=>({});
const global={get_window_actors:()=>windows.map(window=>({get_meta_window:()=>window})),display:new Actor(),workspace_manager:workspaceManager,backend:{get_cursor_tracker:()=>tracker},stage,get_pointer:()=>pointer};
const source=fs.readFileSync('panel-zones-extension/extension.js','utf8')
 .replace(/^import .*;\n/gm,'')
 .replace('export default class PanelZones extends Extension','return class PanelZones extends Extension');
const Class=new Function('GLib','Main','global','Extension','hoveredZone','visibleZones','shouldAutohide',source)(GLib,Main,global,class {},logic.hoveredZone,logic.visibleZones,policy.shouldAutohide);
const extension=new Class();extension.enable();
assert.equal(left.opacity,0);assert.equal(center.opacity,0);assert.equal(right.opacity,255);
assert(right.translation_y===0 && left.translation_y < -32);
assert.deepEqual(left.clip,[0,0,0,0]);assert.equal(right.clip,null);
maxWindow.maximized_horizontally=false;maxWindow.maximized_vertically=false;pointer=[350,400];extension._sync();
for(const actor of [left,center,right]) assert.equal(actor.opacity,255,'without maximized windows every zone stays visible');
maxWindow.maximized_horizontally=true;maxWindow.maximized_vertically=true;
pointer=[800,1];extension._sync();
assert.equal(center.opacity,255);assert.equal(right.opacity,0);
Main.panel.menuManager.activeMenu={sourceActor:{parent:center}};
pointer=[800,200];extension._sync();
assert.equal(center.opacity,255,'open menu pins owner');
Main.panel.menuManager.activeMenu=null;
pointer=[350,5];extension._sync();
assert(extension._hideTimer,'leaving creates one delayed hide');
const hideTimer=extension._hideTimer;
extension._sync();assert.equal(extension._hideTimer,hideTimer);
// Returning to a zone cancels delayed hiding, without flashing other groups.
pointer=[5,1];extension._sync();assert.equal(left.opacity,255);assert.equal(extension._hideTimer,0);
for(let i=0;i<1000;i++) extension._queue();
assert(timers.size <= 1,'motion events coalesce into one timer');
extension.disable();
assert.equal(timers.size,0);
assert.equal(panel.style,'original');
for(const actor of [left,center,right]) {assert.equal(actor.style,'original');assert.equal(actor.opacity,255);assert.equal(actor.translation_y,0);assert.equal(actor.signals.size,0);assert.equal(actor.clip,null);}
assert.equal(maxWindow.signals.size,0);assert.equal(tracker.signals.size,0);assert.equal(stage.signals.size,0);
tracker.connect=()=>{throw new Error('injected registration failure');};
assert.throws(()=>new Class().enable(), /injected registration failure/);
assert.equal(panel.style,'original');
for(const actor of [left,center,right]) {assert.equal(actor.style,'original');assert.equal(actor.opacity,255);}
'''


if __name__ == '__main__':
    unittest.main()
